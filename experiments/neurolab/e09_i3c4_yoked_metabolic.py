"""NeuroLab E09.02i-I3c.4: preregistered B/Y/P/F four-synapse chemical trial.

BEFORE CODE:
 docs/neurolab/E09_02I_I3C4_QUIMICA_APAREADA_PRE_REGISTRO.md

B: own feedback, plastic, no migration.
Y: B-YOKED feedback, plastic, Type1 migration.
P: own feedback, plastic, Type1 migration (on-policy confounded).
F: B-YOKED feedback, frozen, no migration.

All four use identical four-slot initial brain, original GEN reactions /
receptors from I3, synthetic rate40 and dose80. Y/F MUST have a full
identical chemical state after EVERY tick to B, despite differing actions.
No goal/target/correct label enters the neuron step or migration function.
This is N-LINE exploratory, not proven historical C1 or G05/G09.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
import argparse
import hashlib
import json
import random
import statistics

from .c1_context_brain import C1ContextBrain
from .e09_chemical_bridge import (
    ChemicalBridgeState, initial_bridge, chemical_bridge_tick,
)
from .e09_pool_decay import decay_pool
from .e09_i3_metabolic_protocol import (
    RATES, PRECURSOR_DOSE, DELAYS, TRAIN_REPEATS,
    HOLDOUT_REPEATS, TARGET_TICKS, selected_genes,
)
from .e09_context_protocol import MAPPING_A, MAPPING_B
from .e09_delayed_distractors_protocol import trials
from .e09_i3b1_forks import paired_bootstrap
from .e09_i3c3_dynamic_context import (
    DynamicContextBrain, DynamicBrainState, SOURCE_POINTERS,
)

SEEDS=tuple(range(900,920))
MODES=("B","Y","P","F")
TAPE_LENGTH=16384
BOOTSTRAP_REPS=2000
BOOTSTRAP_SEED=60513


@dataclass(frozen=True)
class DynamicChemState:
    brain:DynamicBrainState
    chemistry:ChemicalBridgeState

    def __post_init__(self):
        if not isinstance(self.brain,DynamicBrainState):
            raise TypeError("expected dynamic four-synapse brain")
        if not isinstance(self.chemistry,ChemicalBridgeState):
            raise TypeError("expected chemical bridge")
        if self.brain.tick!=self.chemistry.tick:
            raise ValueError("misaligned chemical and brain logical ticks")


def explicit_wiring(seed):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside independent preregistered cohort")
    return ((0x1000,0x2000,0x2000,0x1000) if seed%2==0
            else (0x2000,0x1000,0x1000,0x2000))


def migration_tape(seed):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("invalid cohort seed")
    rng=random.Random(910000+seed)
    return tuple(rng.randrange(32768) for _ in range(TAPE_LENGTH))


def start(brain,receptors,wiring,draws):
    return DynamicChemState(
        brain.initial(wiring=wiring,random_draws=draws),
        initial_bridge(receptors),
    )


def coupled_step(brain,state,context,receptors,reactions,*,learn):
    """I3 order: brain reads OLD CHEM; chemical tick; decay chemical pool."""
    if not isinstance(state,DynamicChemState):
        raise TypeError("DynamicChemState required")
    bt=brain.step(
        state.brain,context,state.chemistry.decision_chem,learn=learn,
    )
    ct=chemical_bridge_tick(
        state.chemistry,(),receptors,reactions,
    )
    pool=decay_pool(ct.after.pool,RATES,state.chemistry.tick)
    after=DynamicChemState(
        bt.after,replace(ct.after,pool=pool),
    )
    return after,bt.action,bt


def add_environment_precursors(state,correct,*,dose=PRECURSOR_DOSE):
    """Same exogenous substrate rule as I3, typed to DynamicChemState."""
    if not isinstance(state,DynamicChemState) or type(correct) is not bool:
        raise TypeError("dynamic state + boolean outcome required")
    if type(dose) is not int or not 0<=dose<=255:
        raise ValueError("byte precursor dose required")
    additions=((33,dose),(1,dose)) if correct else ((17,dose),)
    pool=list(state.chemistry.pool)
    for chem,n in additions:
        pool[chem]=min(255,pool[chem]+n)
    return DynamicChemState(
        state.brain,replace(state.chemistry,pool=tuple(pool))
    )


def _core(s):
    """Neural state WITHOUT migration random cursor."""
    x=s.brain
    return (x.links,x.neuron_states,x.neuron_outputs,x.concept_outputs)


def _chemical_bytes(state):
    c=state.chemistry
    if c.ports:
        raise AssertionError("I3c4 does not supply neural emitter ports")
    return (c.tick.to_bytes(8,"little")+
            bytes(c.pool)+bytes(c.decision_chem)+bytes(c.concept_chem))


def run_phase(
    brain,state,seq,mapping,receptors,reactions,*,mode,
    feedback_reference=None,expected_chemistry=None,
    train=True,
):
    """Train or holdout with optionally fixed/yoked exogenous feedback.

    A feedback_reference tuple holds B's outcome for every target trial.
    None means no injection, even if this brain emitted an action.
    """
    if mode not in MODES:
        raise ValueError("unknown preregistered arm")
    if mode in ("Y","F") and train and feedback_reference is None:
        raise ValueError("yoked arms require B feedback events")
    if feedback_reference is not None and len(feedback_reference)!=len(seq):
        raise ValueError("feedback tape length mismatch")
    if expected_chemistry is not None and not isinstance(expected_chemistry,tuple):
        raise TypeError("full chemical witness tuple required")
    frozen=state.brain.links
    cursor_before=state.brain.random_tape.cursor
    tally=Counter()
    action_counts=Counter()
    sums={d:0 for d in DELAYS}
    n={d:0 for d in DELAYS}
    by_context=[0,0]
    context_n=[0,0]
    lost_at_end=0
    missing=0
    delivered=0
    events=[]
    chem_states=[]
    cores=[]
    acceptance_flags=[]
    cumulative_digest=hashlib.sha256()
    old_ptrs=tuple(link.source_pointer for link in state.brain.links)
    ref_cursor=0

    def advanced(context):
        nonlocal state,ref_cursor
        previous=state
        state,action,trace=coupled_step(
            brain,state,context,receptors,reactions,learn=(train and mode!="F"),
        )
        if len(state.brain.links)!=4:
            raise AssertionError("dynamic contact count changed")
        reasons=[e.reason for e in trace.migration]
        tally.update(reasons)
        moved=any(e.migrated for e in trace.migration)
        acceptance_flags.append(moved)
        if (tuple(link.source_pointer for link in state.brain.links)
                !=tuple(link.source_pointer for link in previous.brain.links))!=moved:
            raise AssertionError("pointer transition lacks accepted Type1 witness")
        if (mode in ("B","F") or not train) and (
                trace.migration or state.brain.random_tape.cursor!=
                    previous.brain.random_tape.cursor):
            raise AssertionError("frozen/disabled arm consumed migration RNG")
        if expected_chemistry is not None:
            if ref_cursor>=len(expected_chemistry):
                raise AssertionError("reference chemistry shorter than execution")
            if state.chemistry!=expected_chemistry[ref_cursor]:
                raise AssertionError(
                    f"{mode} chemistry deviated from B at tick {state.brain.tick}")
        chem_states.append(state.chemistry)
        cumulative_digest.update(_chemical_bytes(state))
        cores.append(_core(state))
        ref_cursor+=1
        return action

    for i,(target,delay) in enumerate(seq):
        chosen=None
        for _ in range(TARGET_TICKS):
            chosen=advanced(target)
        correct=chosen==mapping[target]
        missing+=int(chosen is None)
        n[delay]+=1
        sums[delay]+=int(correct)
        context_n[target]+=1
        by_context[target]+=int(correct)
        action_counts.update((chosen if chosen is not None else "None",))
        for _ in range(delay):
            advanced(1-target)
        outcome=(None if chosen is None else bool(correct))
        if feedback_reference is not None:
            outcome=feedback_reference[i]
        if train and outcome is not None:
            state=add_environment_precursors(state,outcome)
            delivered+=1
        events.append(outcome if train else None)
        advanced(1-target)

    if expected_chemistry is not None and ref_cursor!=len(expected_chemistry):
        raise AssertionError("reference chemistry longer than execution")
    if not train:
        if state.brain.links!=frozen or state.brain.random_tape.cursor!=cursor_before:
            raise AssertionError("holdout changed weights, source or RNG")
    lost_at_end=sum(link.synapse.strength==0 for link in state.brain.links)
    if mode in ("B","F") and (
        tuple(link.source_pointer for link in state.brain.links)!=old_ptrs):
        raise AssertionError("control altered fixed Concept source pointers")
    accuracy=sum(sums.values())/len(seq)
    return state,{
        "overall":accuracy,
        "by_delay":{str(d):sums[d]/n[d] for d in DELAYS},
        "by_context":[by_context[c]/context_n[c] for c in (0,1)],
        "target_choices":len(seq),
        "target_missing":missing,
        "feedback_deliveries":delivered,
        "feedback_events":events,
        "action_counts":dict(sorted(action_counts.items())),
        "migration_reasons":dict(sorted(tally.items())),
        "migration_acceptances":sum(acceptance_flags),
        "exhausted_final":lost_at_end,
        "random_cursor":state.brain.random_tape.cursor,
        "wiring_final":[hex(link.source_pointer) for link in state.brain.links],
        "chem_trajectory_sha256":cumulative_digest.hexdigest(),
        "ticked_steps":ref_cursor,
    },tuple(chem_states),tuple(cores),tuple(acceptance_flags)


def _assert_neural_equal_before_first_migration(reference,intervened,flags,history):
    """Assert no B vs Y divergence before an accepted Type1 transition."""
    if not (len(reference)==len(intervened)==len(flags)):
        raise AssertionError("mismatched B/Y neural trace lengths")
    for before,after,moved in zip(reference,intervened,flags):
        if not history["ever_accepted"] and not moved and before!=after:
            raise AssertionError("Y neural path diverged before accepted migration")
        history["ever_accepted"]|=moved


def run_seed(seed):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside frozen cohort")
    receptors,reactions=selected_genes()
    draws=migration_tape(seed)
    wiring=explicit_wiring(seed)
    brains={
        "B":DynamicContextBrain(seed,migration_enabled=False),
        "Y":DynamicContextBrain(seed,migration_enabled=True),
        "P":DynamicContextBrain(seed,migration_enabled=True),
        "F":DynamicContextBrain(seed,migration_enabled=False),
    }
    states={m:start(b,receptors,wiring,draws) for m,b in brains.items()}
    initial=states["B"].chemistry
    if any(states[m].chemistry!=initial for m in MODES):
        raise AssertionError("not identical chemical origins")
    freeze_links=states["F"].brain.links
    history={"ever_accepted":False}
    record={"seed":seed,"initial_wiring":[hex(x) for x in wiring]}
    for phase,salt_train,salt_test,mapping in (
        ("first",50000,70000,MAPPING_A),
        ("reversed",60000,80000,MAPPING_B),
    ):
        training=trials(seed,salt_train,TRAIN_REPEATS)
        holdout=trials(seed,salt_test,HOLDOUT_REPEATS)
        score_train={}
        score_holdout={}

        states["B"],score_train["B"],chem_B,core_B,accept_B=run_phase(
            brains["B"],states["B"],training,mapping,receptors,reactions,
            mode="B",train=True,
        )
        tape_B=tuple(score_train["B"]["feedback_events"])
        states["Y"],score_train["Y"],chem_Y,core_Y,accept_Y=run_phase(
            brains["Y"],states["Y"],training,mapping,receptors,reactions,
            mode="Y",feedback_reference=tape_B,
            expected_chemistry=chem_B,train=True,
        )
        states["F"],score_train["F"],chem_F,core_F,accept_F=run_phase(
            brains["F"],states["F"],training,mapping,receptors,reactions,
            mode="F",feedback_reference=tape_B,
            expected_chemistry=chem_B,train=True,
        )
        states["P"],score_train["P"],chem_P,core_P,accept_P=run_phase(
            brains["P"],states["P"],training,mapping,receptors,reactions,
            mode="P",train=True,
        )
        _assert_neural_equal_before_first_migration(
            core_B,core_Y,accept_Y,history,
        )
        if states["F"].brain.links!=freeze_links:
            raise AssertionError("frozen F changed C1 synaptic state")
        if not (
            score_train["B"]["chem_trajectory_sha256"]==
            score_train["Y"]["chem_trajectory_sha256"]==
            score_train["F"]["chem_trajectory_sha256"]
        ):
            raise AssertionError("B Y F training chemistry mismatch")

        chem_H_B=None
        core_H_B=None
        for mode in MODES:
            _after,score,chem,core,flags=run_phase(
                brains[mode],states[mode],holdout,mapping,
                receptors,reactions,mode=mode,train=False,
                expected_chemistry=chem_H_B if mode in ("Y","F") else None,
            )
            score_holdout[mode]=score
            if mode=="B":
                chem_H_B=chem
                core_H_B=core
            if mode=="Y":
                _assert_neural_equal_before_first_migration(
                    core_H_B,core,flags,history,
                )
        if not (
            score_holdout["B"]["chem_trajectory_sha256"]==
            score_holdout["Y"]["chem_trajectory_sha256"]==
            score_holdout["F"]["chem_trajectory_sha256"]
        ):
            raise AssertionError("B Y F holdout chemistry mismatch")

        record[phase]={
            "train":score_train,
            "holdout":score_holdout,
            "B_Y_F_identical_chemical_every_tick":True,
            "n_train_trials":len(training),
            "n_holdout_trials":len(holdout),
        }
    record["any_Y_migration_accepted"]=history["ever_accepted"]
    return record


def run_all(seeds=SEEDS):
    if not isinstance(seeds,tuple) or not seeds or any(
            type(s) is not int or s not in SEEDS for s in seeds
    ) or len(set(seeds))!=len(seeds):
        raise ValueError("independent unique preregistered seed subset required")
    rows=[run_seed(seed) for seed in seeds]
    means={
        phase:{
            m:statistics.mean(row[phase]["holdout"][m]["overall"] for row in rows)
            for m in MODES
        } for phase in ("first","reversed")
    }
    contrasts={}
    for phase in ("first","reversed"):
        view=[
            {"seed":row["seed"],"branches":{
                mode:{"accuracy":row[phase]["holdout"][mode]["overall"]}
                for mode in MODES
            }} for row in rows
        ]
        contrasts[phase]={
            "Y_minus_B":paired_bootstrap(view,"Y","B","accuracy",
                                        seed=BOOTSTRAP_SEED,replicas=BOOTSTRAP_REPS),
            "B_minus_F":paired_bootstrap(view,"B","F","accuracy",
                                        seed=BOOTSTRAP_SEED,replicas=BOOTSTRAP_REPS),
            "P_minus_B":paired_bootstrap(view,"P","B","accuracy",
                                        seed=BOOTSTRAP_SEED,replicas=BOOTSTRAP_REPS),
        }
    accepted={
        mode:sum(row[phase]["train"][mode]["migration_acceptances"]
                 for row in rows for phase in ("first","reversed"))
        for mode in MODES
    }
    return {
        "protocol":"E09_02I_I3C4_QUIMICA_APAREADA_PRE_REGISTRO-v1",
        "study_type":"paired synthetic chemistry N; not historical C1 or G05",
        "seeds":list(seeds),
        "n_seeds":len(seeds),
        "n_units":6,"n_contacts":4,
        "n_train_trials_per_phase":60,
        "n_holdout_trials_per_phase":36,
        "rates_synthetic_per_chemical":40,
        "precursor_dose_synthetic":80,
        "reactions":[57,71,111,112],
        "modes":list(MODES),
        "migration_rng":"Python local Random(910000+seed), 16384 raw draws; not CRT",
        "mean_holdout_accuracy":means,
        "migration_acceptances":accepted,
        "seeds_with_Y_migration":sum(row["any_Y_migration_accepted"] for row in rows),
        "contrasts":contrasts,
        "all_B_Y_F_chemical_trajectories_identical":True,
        "all_pre_migration_neural_paths_identical":True,
        "gate_wiring":"PASS if no assertions; Y-B difference is not guaranteed",
        "gate_G05_G09":"NOT EVALUATED; I3 general learning remains negative",
        "per_seed":rows,
        "limitations":"Y receives B-derived foreign choices/reward, P is on-policy and may diverge chemically; synthetic decay40/dose80/migration config and no automatic emitters. Do not infer autonomous learning or C1 fidelity.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    blob=json.dumps(run_all(),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(blob,encoding="utf-8")
    print(blob,end="")


if __name__=="__main__":
    main()
