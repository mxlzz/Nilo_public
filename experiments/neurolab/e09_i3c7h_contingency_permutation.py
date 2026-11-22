"""NeuroLab I3c.7h — preregistered contingency degradation, not C1 credit proof.

Docs: E09_02I_I3C7H_CONTINGENCIA_PERMUTADA_PRE_REGISTRO.md
B: own-action M0; Y: exact B event tape; F: frozen weights, B event tape;
P: B tape reward valences shuffled within context, preserving every event
slot and sign counts/context, but NOT chemical chronology.
Theorem: B and Y MUST remain identical in deterministic fixed-brain C1.
Original C1ContextBrain, genes, chemical runtime, dose and rate untouched.
"""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import argparse
import json
import random
import statistics

from .c1_context_brain import C1ContextBrain
from .e09_context_protocol import (
    MAPPING_A, MAPPING_B, BLOCK_TICKS, blocks,
)
from .e09_coupled_brain import initial_coupled
from .e09_i3_metabolic_protocol import (
    PRECURSOR_DOSE, selected_genes, add_environment_precursors,
)
from .e09_i3c7e_loss_factorial import (
    ArmState, _advance, run_phase, _neural_snapshot,
)

PROTOCOL="NL-EXP-I3c7h-v1"
SEEDS=tuple(range(1800,1820))
RESERVED_CONFIRMATION=tuple(range(1400,1420))
MODES=("B","Y","P","F")
PHASES=(("first",10000,30000,MAPPING_A),
        ("reversed",20000,40000,MAPPING_B))
PHASE_TRAIN_BLOCKS=32
HOLDOUT_BLOCKS=16
READOUTS=("frozen","active_no_new_reward")
PERMUTATION_SEED=60520
BOOTSTRAP_REPS=2000
BOOTSTRAP_SEED=60520
EFFECTIVE_MANIPULATION_FRACTION=.10
MIN_SEEDS_EFFECTIVE=16


def digest(obj):
    return sha256(json.dumps(
        obj,sort_keys=True,separators=(",",":")
    ).encode("utf-8")).hexdigest()


def event_tape_from_original(training):
    """Only the REAL evaluator's post-action sign, not a predicted label."""
    frames=training["frames"]
    tape=tuple(
        (bool(f["correct"]) if f["external_feedback_created"] else None)
        for f in frames
    )
    if len(tape)!=PHASE_TRAIN_BLOCKS*BLOCK_TICKS:
        raise AssertionError("original full post-action feedback schedule missing")
    if sum(x is not None for x in tape)!=training["new_feedback_events"]:
        raise AssertionError("original feedback events differ from tape")
    return tape


def context_stratified_permutation(tape,contexts,seed,phase_index):
    """One and only one frozen random permutation per seed, phase, context.

    Only delivered True/False are shuffled. None positions stay fixed.
    Counts of positive and negative outcomes by context are unchanged.
    """
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside preregistered development cohort")
    if phase_index not in (0,1):
        raise ValueError("invalid preregistered phase index")
    if len(tape)!=len(contexts) or len(tape)!=256:
        raise ValueError("full 256 tick context/tape length required")
    if any(type(x) not in (bool,type(None)) for x in tape):
        raise TypeError("feedback tape only True/False/None")
    if any(x not in (0,1) for x in contexts):
        raise ValueError("context must be binary")
    rng=random.Random(PERMUTATION_SEED+1000*seed+phase_index)
    result=list(tape)
    for context in (0,1):
        positions=[
            t for t,(x,c) in enumerate(zip(tape,contexts))
            if c==context and x is not None
        ]
        signs=[tape[t] for t in positions]
        rng.shuffle(signs)
        for t,x in zip(positions,signs):
            result[t]=x
    result=tuple(result)
    for context in (0,1):
        for valence in (True,False,None):
            old=sum(x is valence and c==context
                    for x,c in zip(tape,contexts))
            new=sum(x is valence and c==context
                    for x,c in zip(result,contexts))
            if old!=new:
                raise AssertionError("event/valence/context counts changed")
    if any((a is None)!=(b is None) for a,b in zip(tape,result)):
        raise AssertionError("reward timing or None position changed")
    return result


def _run_external_tape(brain,state,seq,mapping,source,mode,
                       receptors,reactions):
    """Advance using the ORIGINAL 8-synapse C1/chemical functions.

    mode Y/P have plasticity; F is frozen during *training* only.
    source is a tape of external precursor signs; it never goes to brain.
    """
    if mode not in ("B","Y","P","F"):
        raise ValueError("unknown experimental arm")
    contexts=tuple(c for block in seq for c in (block,)*BLOCK_TICKS)
    if len(contexts)!=len(source) or len(contexts)!=256:
        raise AssertionError("one sign slot per original experimental tick")
    traces=[]
    chemistry=[]
    neural=[]
    actions=[]
    correct=[]
    tally={"effect":0,"gain":0,"lose":0,"lost_connection":0}
    initial_weights=state.coupled.brain.dendrites
    for tick,(context,reward) in enumerate(zip(contexts,source)):
        old=state
        state,action,chem,weights=_advance(
            brain,state,context,"M0",receptors,reactions,
            learn=mode!="F",
        )
        if (mode=="F" and
                state.coupled.brain.dendrites!=initial_weights):
            raise AssertionError("F did not keep dendrites frozen")
        was_correct=(action==mapping[context])
        if reward is not None:
            state=ArmState(
                add_environment_precursors(
                    state.coupled,correct=reward,dose=PRECURSOR_DOSE,
                ),
            )
        if state.coupled.brain.tick!=old.coupled.brain.tick+1:
            raise AssertionError("neural clock not advanced exactly once")
        for key in tally:
            tally[key]+=weights[key]
        snapshot=_neural_snapshot(state.coupled.brain)
        chemical_snapshot=digest(asdict(state.coupled.chemistry))
        neural_snapshot=digest(asdict(state.coupled.brain))
        chemistry.append(chemical_snapshot)
        neural.append(neural_snapshot)
        actions.append(action)
        correct.append(int(was_correct))
        traces.append({
            "tick":state.coupled.brain.tick,
            "context":context,
            "within_block":tick%BLOCK_TICKS,
            "action":action,
            "correct":int(was_correct),
            "evaluator_valence":reward,
            "reward_correct_for_own_action":(
                None if reward is None else int(reward==was_correct)
            ),
            "chem_input":list(chem),
            "chemical_after_injection_sha256":chemical_snapshot,
            "neural_after_step_sha256":neural_snapshot,
            "n_live":snapshot["n_live"],
            "n_live_stw_ge5":snapshot["n_live_stw_ge5"],
            "n_live_ltw_positive":snapshot["n_live_ltw_positive"],
            "strengths":snapshot["strengths"],
            "stw":snapshot["stw"],
            "ltw":snapshot["ltw"],
            "effect":weights["effect"],
            "loss":weights["lose"],
        })
    n_steady=sum(t["within_block"]>=2 for t in traces)
    if n_steady!=192:
        raise AssertionError("changed predeclared steady sample definition")
    return state,{
        "n_ticks":len(contexts),
        "n_deliveries":sum(x is not None for x in source),
        "n_positive":sum(x is True for x in source),
        "n_negative":sum(x is False for x in source),
        "accuracy_overall":sum(correct)/len(correct),
        "accuracy_steady":sum(
            t["correct"] for t in traces if t["within_block"]>=2
        )/n_steady,
        "positive_correct_to_own_choice":sum(
            t["reward_correct_for_own_action"]==1 for t in traces
        ),
        "fraction_reward_matching_own_outcome":(
            sum(t["reward_correct_for_own_action"]==1 for t in traces)/
            max(1,sum(x is not None for x in source))
        ),
        "n_none_actions":sum(a is None for a in actions),
        "chemical_auc":[sum(t["chem_input"][i] for t in traces)
                        for i in range(4)],
        "synapse_events":tally,
        "end_weights":_neural_snapshot(state.coupled.brain),
        "frames":traces,
        "chemistry_after_each_tick_sha256":chemistry,
        "neural_after_each_tick_sha256":neural,
        "end_state_sha256":digest(asdict(state.coupled)),
    }


def _holdout(brain,state,seq,mapping,receptors,reactions):
    answer={}
    before=digest(asdict(state))
    for kind in READOUTS:
        _,metrics=run_phase(
            brain,state,seq,mapping,"M0",receptors,reactions,
            training=False,readout=kind,
        )
        if metrics["new_feedback_events"]!=0:
            raise AssertionError("unexpected reward in holdout")
        if digest(asdict(state))!=before:
            raise AssertionError("holdout contaminated training continuation")
        answer[kind]=metrics
    return answer


def run_seed(seed,receptors=None,reactions=None):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("invalid preregistered seed")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    brain=C1ContextBrain(seed)
    states={
        mode:ArmState(initial_coupled(brain,receptors))
        for mode in MODES
    }
    if len({digest(asdict(s.coupled)) for s in states.values()})!=1:
        raise AssertionError("four arms have different initial chemistry/neurons")
    initial_sha=digest(asdict(states["B"].coupled))
    phases={}
    for phase_index,(phase,salt_train,salt_holdout,mapping) in enumerate(PHASES):
        seq=blocks(seed,salt_train,PHASE_TRAIN_BLOCKS)
        test=blocks(seed,salt_holdout,HOLDOUT_BLOCKS)
        contexts=tuple(c for block in seq for c in (block,)*BLOCK_TICKS)
        initial_B=states["B"]
        reference_B,reference_metrics=run_phase(
            brain,initial_B,seq,mapping,"M0",receptors,reactions,
            training=True,
        )
        tape_B=event_tape_from_original(reference_metrics)
        tape_P=context_stratified_permutation(
            tape_B,contexts,seed,phase_index,
        )
        tape_by_mode={"B":tape_B,"Y":tape_B,"P":tape_P,"F":tape_B}
        training={}
        for mode in MODES:
            states[mode],training[mode]=_run_external_tape(
                brain,states[mode],seq,mapping,tape_by_mode[mode],
                mode,receptors,reactions,
            )
        if states["B"].coupled!=reference_B.coupled:
            raise AssertionError("B replay differs from I3c7e M0 original final state")
        for i,(r,b) in enumerate(zip(
            reference_metrics["frames"],training["B"]["frames"]
        )):
            if (r["tick"]!=b["tick"] or r["action"]!=b["action"]
                    or r["chem_input"]!=b["chem_input"]
                    or r["correct"]!=b["correct"]
                    or r["strengths"]!=b["strengths"]
                    or r["stw"]!=b["stw"] or r["ltw"]!=b["ltw"]):
                raise AssertionError(f"B replay differs from original at frame {i}")
        if states["Y"].coupled!=states["B"].coupled:
            raise AssertionError("Y not deterministic identity of B after exact replay")
        for mode in ("Y","F"):
            if (training["B"]["chemistry_after_each_tick_sha256"]
                !=training[mode]["chemistry_after_each_tick_sha256"]):
                raise AssertionError(f"B/{mode} chemistry diverged under exact tape")
        if (training["B"]["neural_after_each_tick_sha256"]
            !=training["Y"]["neural_after_each_tick_sha256"]):
            raise AssertionError("B/Y neuronal trajectories differ despite identical inputs")
        if any(a!=b for a,b in zip(
            (t["action"] for t in training["B"]["frames"]),
            (t["action"] for t in training["Y"]["frames"]),
        )):
            raise AssertionError("B/Y policy divergence impossible under same state")
        if (training["F"]["end_weights"]["strengths"]!=[2]*8
                or training["F"]["end_weights"]["stw"]!=[0]*8
                or training["F"]["end_weights"]["ltw"]!=[0]*8):
            raise AssertionError("negative control F acquired plasticity")
        mismatch=sum(a!=b for a,b in zip(tape_B,tape_P))
        n_delivered=sum(x is not None for x in tape_B)
        if mismatch%2:
            raise AssertionError("valence-permutation differences must be even")
        if any((a is None)!=(b is None) for a,b in zip(tape_B,tape_P)):
            raise AssertionError("reward event positions differ")
        for context in (0,1):
            for sign in (True,False,None):
                b=sum(x is sign and c==context
                      for x,c in zip(tape_B,contexts))
                p=sum(x is sign and c==context
                      for x,c in zip(tape_P,contexts))
                if b!=p:
                    raise AssertionError("permutation altered context-stratified reward budget")
        readouts={
            mode:_holdout(
                brain,states[mode],test,mapping,receptors,reactions
            ) for mode in MODES
        }
        if readouts["B"]!=readouts["Y"]:
            raise AssertionError("B/Y holdout must remain exactly identical")
        phases[phase]={
            "mapping":list(mapping),
            "training_blocks":list(seq),
            "holdout_blocks":list(test),
            "b_tape":list(tape_B),
            "p_tape":list(tape_P),
            "permutation_seed":PERMUTATION_SEED+1000*seed+phase_index,
            "n_reward_sign_changes":mismatch,
            "fraction_sign_changes":mismatch/max(1,n_delivered),
            "manipulation_effective":mismatch/max(1,n_delivered)>=EFFECTIVE_MANIPULATION_FRACTION,
            "action_disagreement_B_P":sum(
                a["action"]!=b["action"]
                for a,b in zip(training["B"]["frames"],training["P"]["frames"])
            ),
            "B_Y_F_chemical_each_tick_equal":True,
            "B_Y_neural_each_tick_equal":True,
            "B_exact_I3c7e_M0_reference":True,
            "training":training,
            "readouts":readouts,
        }
    return {"seed":seed,"initial_sha256":initial_sha,"phases":phases}


def _paired_ci(rows,phase,a,b,readout="active_no_new_reward",
               metric="steady"):
    values=[
        row["phases"][phase]["readouts"][a][readout][metric]
        -row["phases"][phase]["readouts"][b][readout][metric]
        for row in rows
    ]
    rng=random.Random(BOOTSTRAP_SEED)
    draws=sorted(statistics.mean(rng.choice(values) for _ in values)
                 for _ in range(BOOTSTRAP_REPS))
    return {
        "n_seeds":len(values),
        "mean":statistics.mean(values),
        "ci95":[draws[int(BOOTSTRAP_REPS*.025)],
                draws[int(BOOTSTRAP_REPS*.975)-1]],
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds,tuple) or not seeds
            or len(set(seeds))!=len(seeds)
            or any(type(s) is not int or s not in SEEDS for s in seeds)):
        raise ValueError("only unique preregistered development seeds")
    receptors,reactions=selected_genes()
    rows=[run_seed(seed,receptors,reactions) for seed in seeds]
    summary={}
    contrasts={}
    for phase in ("first","reversed"):
        summary[phase]={}
        for mode in MODES:
            summary[phase][mode]={
                readout:{
                    "mean_steady":statistics.mean(
                        row["phases"][phase]["readouts"][mode][readout]["steady"]
                        for row in rows
                    ),
                    "mean_overall":statistics.mean(
                        row["phases"][phase]["readouts"][mode][readout]["overall"]
                        for row in rows
                    ),
                    "n_steady_ge90":sum(
                        row["phases"][phase]["readouts"][mode][readout]["steady"]>=.90
                        for row in rows
                    ),
                } for readout in READOUTS
            }
            summary[phase][mode]["mean_chemical_auc"]=[
                statistics.mean(
                    row["phases"][phase]["training"][mode]["chemical_auc"][i]
                    for row in rows
                ) for i in (0,1)
            ]
            summary[phase][mode]["mean_own_feedback_agreement"]=statistics.mean(
                row["phases"][phase]["training"][mode][
                    "fraction_reward_matching_own_outcome"
                ] for row in rows
            )
        summary[phase]["permutation"]={
            "effective_seeds":sum(
                row["phases"][phase]["manipulation_effective"] for row in rows
            ),
            "mean_fraction_sign_changes":statistics.mean(
                row["phases"][phase]["fraction_sign_changes"]
                for row in rows
            ),
            "mean_action_disagreement_B_P":statistics.mean(
                row["phases"][phase]["action_disagreement_B_P"]
                for row in rows
            ),
        }
        contrasts[phase]={
            "B_minus_P":{
                readout:_paired_ci(rows,phase,"B","P",readout)
                for readout in READOUTS
            },
            "B_minus_F":{
                readout:_paired_ci(rows,phase,"B","F",readout)
                for readout in READOUTS
            },
            "B_minus_Y":{
                readout:_paired_ci(rows,phase,"B","Y",readout)
                for readout in READOUTS
            },
        }
    informative=sum(
        any(row["phases"][p]["manipulation_effective"]
            for p in ("first","reversed")) for row in rows
    )
    if len(rows)==20:
        usable=informative>=MIN_SEEDS_EFFECTIVE
    else:
        usable=None
    p=contrasts["reversed"]["B_minus_P"]["active_no_new_reward"]
    b=summary["reversed"]["B"]["active_no_new_reward"]["mean_steady"]
    bf=contrasts["reversed"]["B_minus_F"]["active_no_new_reward"]["mean"]
    interest=(usable is True and p["mean"]>=.10
              and p["ci95"][0]>0 and b>=.75 and bf>=.10)
    return {
        "protocol":PROTOCOL,
        "cohort":list(seeds),
        "n_seeds":len(rows),
        "modes":list(MODES),
        "feedback_dose":PRECURSOR_DOSE,
        "permutation_rng_seed_rule":"60520+1000*seed+phase_index, shuffle within each context",
        "original_C1_M0_training_exact_replay":True,
        "B_Y_neural_and_chemical_identity_each_tick":True,
        "B_Y_F_identical_full_chemistry_each_tick":True,
        "P_reward_count_and_valence_by_context_equal_B":True,
        "P_chemistry_not_matched_tickwise":True,
        "n_seeds_with_effective_permutation_in_either_phase":informative,
        "effective_gate_at_least16_of20":usable,
        "summary":summary,
        "paired_contrasts":contrasts,
        "precommitted_interest_gate":interest,
        "per_seed_sha256":{str(row["seed"]):digest(row) for row in rows},
        "per_seed":rows,
        "limitations":"B vs Y identical is a mathematical software control, NOT contingency. P permutes signs within-context but changes chemical kinetics; feedback tape derived from B own policy and P may accidentally receive contingent signs. Source-specific synapse credit is NOT proven. M0 loss suppression synthetic, not historical C1. F active readout unfreezes plasticity.",
        "gates":{"software":"PASS if assertions",
                 "G05":"OPEN","G09":"OPEN","G00H":"OPEN"},
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    data=run_all()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(
            json.dumps(data,sort_keys=True,separators=(",",":"))+"\n",
            encoding="utf-8",
        )
    print(json.dumps({k:data[k] for k in (
        "protocol","cohort","n_seeds",
        "n_seeds_with_effective_permutation_in_either_phase",
        "effective_gate_at_least16_of20",
        "summary","paired_contrasts","precommitted_interest_gate",
        "per_seed_sha256","gates"
    )},sort_keys=True))


if __name__=="__main__":
    main()
