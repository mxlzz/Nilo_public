"""I3c.7e prereg: reward pathway (direct/metabolic) x atrophy (off/nominal16).

PRE-REGISTERED BEFORE CODE:
 docs/neurolab/E09_02I_I3C7E_FACTORIAL_PERDIDA_REFUERZO_PRE_REGISTRO.md

Four plastic arms D0/D16/M0/M16 and frozen FD/FM from same C1ContextBrain
and preexisting E09g5 sensory sequences. A/B reversal and twin readouts:
learn=False frozen, and learn=True without NEW external feedback.
Direct255 and metabolic precursor80 are NOT equal-amplitude interventions.
Loss0 is explicitly a SYNTHETIC ABLATION, never a C1 historical claim.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import random
import statistics

from .c1_context_brain import C1ContextBrain, ContextBrainState
from .c1_synapse_integrated import (
    C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)
from .e09_context_protocol import (
    ZERO, REWARD, PUNISHMENT, MAPPING_A, MAPPING_B,
    blocks, train_brain, evaluate_brain,
    TRAIN_BLOCKS, TEST_BLOCKS, BLOCK_TICKS,
)
from .e09_coupled_brain import CoupledState, initial_coupled
from .e09_i3_metabolic_protocol import (
    RATES, PRECURSOR_DOSE, selected_genes, add_environment_precursors,
)
from .e09_chemical_bridge import chemical_bridge_tick
from .e09_pool_decay import decay_pool

SEEDS=tuple(range(1600,1620))
UNUSED_CONFIRMATION_SEEDS=tuple(range(1400,1420))
MODES=("D0","D16","M0","M16","FD","FM")
# via, nominal_loss_flag, plastic_in_training
SPECS={
    "D0":("D",False,True),
    "D16":("D",True,True),
    "M0":("M",False,True),
    "M16":("M",True,True),
    "FD":("D",True,False),
    "FM":("M",True,False),
}
PHASES=(
    ("first",10000,30000,MAPPING_A),
    ("reversed",20000,40000,MAPPING_B),
)
READOUTS=("frozen","active_no_new_reward")
BOOTSTRAP_REPS=2000
BOOTSTRAP_SEED=60518
EXPECTED_NOMINAL=(0,0,16,16)


def _sha(obj):
    return sha256(json.dumps(
        obj,sort_keys=True,separators=(",",":")
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ArmState:
    coupled: CoupledState
    pending: tuple[int,int,int,int] = ZERO

    def __post_init__(self):
        if not isinstance(self.coupled,CoupledState):
            raise TypeError("exact coupled brain+chemical typed state required")
        if not isinstance(self.pending,tuple) or len(self.pending)!=4:
            raise ValueError("direct pulse must have 4 chemicals")
        if any(type(x) is not int or not 0<=x<=255 for x in self.pending):
            raise ValueError("pending pulse byte range")


def _input_neural(state,mode):
    via,loss_nominal,_=SPECS[mode]
    base=(state.pending if via=="D"
          else state.coupled.chemistry.decision_chem)
    return (base[0],base[1],base[2],base[3]) if loss_nominal else (
        base[0],base[1],0,0
    )


def _witness(old,chem,tick):
    expected=[]
    tally={"effect":0,"gain":0,"lose":0,"lost_connection":0}
    for i,syn in enumerate(old.dendrites):
        gene=(DECISION_INHIBITORY_GENE if i%2
              else DECISION_EXCITATORY_GENE)
        tr=update_c1_synapse(
            syn,gene,C1SynapticInput(
                source_output=old.concept_outputs[(i%4)//2],
                owner_state=old.neuron_states[i//4],
                owner_output=old.neuron_outputs[i//4],
                chemicals=chem,
            ),tick=tick,
        )
        expected.append(tr.after)
        tally["effect"]+=tr.numeric.reinforcement_effect
        tally["gain"]+=int(tr.strength.did_gain)
        tally["lose"]+=int(tr.strength.did_lose)
        tally["lost_connection"]+=int(tr.strength.lost_connection)
    return tuple(expected),tally


def _neural_snapshot(state:ContextBrainState):
    return {
        "tick":state.tick,
        "strengths":[s.strength for s in state.dendrites],
        "stw":[s.dendrite.stw for s in state.dendrites],
        "ltw":[s.dendrite.ltw for s in state.dendrites],
        "n_live":sum(s.strength>0 for s in state.dendrites),
        "n_live_stw_ge5":sum(s.strength>0 and s.dendrite.stw>=5
                             for s in state.dendrites),
        "n_live_ltw_positive":sum(s.strength>0 and s.dendrite.ltw>0
                                  for s in state.dendrites),
    }


def _advance(brain,state,context,mode,receptors,reactions,*,learn):
    if mode not in SPECS:
        raise ValueError("undefined protocol arm")
    chem=_input_neural(state,mode)
    old=state.coupled
    tick=old.brain.tick+1
    before_synapses=old.brain.dendrites
    predicted,wt=_witness(old.brain,chem,tick)
    bt=brain.step(old.brain,context,chem,learn=learn)
    if learn and bt.after.dendrites!=predicted:
        raise AssertionError("per-dendrite original gene update diverges from brain")
    if not learn and bt.after.dendrites!=before_synapses:
        raise AssertionError("frozen readout/training updated synapses")
    ct=chemical_bridge_tick(old.chemistry,(),receptors,reactions)
    new_pool=decay_pool(ct.after.pool,RATES,old.chemistry.tick)
    after=CoupledState(bt.after,replace(ct.after,pool=new_pool))
    if after.brain.tick!=after.chemistry.tick:
        raise AssertionError("chemical/neural clocks diverged")
    if not learn:
        wt={"effect":0,"gain":0,"lose":0,"lost_connection":0}
    return ArmState(after,state.pending),bt.action,chem,wt


def run_phase(brain,state,seq,mapping,mode,receptors,reactions,*,training,readout=None):
    """TRAIN creates on-policy feedback after choice. HOLDOUT never creates new."""
    if mode not in SPECS:
        raise ValueError("unknown arm")
    if readout not in (None,*READOUTS) or (training!=(readout is None)):
        raise ValueError("readout must be None iff training")
    via,_,plastic_training=SPECS[mode]
    effective_learning=(
        plastic_training if training else (readout=="active_no_new_reward")
    )
    if not training:
        # Direct residual pending reward from last training tick must NEVER
        # enter a no-new-reward evaluation, even if phase2 will later use it.
        state=ArmState(state.coupled,ZERO)
    initial_neural=state.coupled.brain.dendrites
    context_correct=[0,0]
    context_total=[0,0]
    steady_correct=[0,0]
    steady_total=[0,0]
    missing=0
    delivered=0
    sum_chem=[0,0,0,0]
    sums={"effect":0,"gain":0,"lose":0,"lost_connection":0}
    peaks_pool={str(k):0 for k in (17,33,1,49,50,51,53,70)}
    saturated_ticks=0
    frames=[]
    for context in seq:
        for within in range(BLOCK_TICKS):
            old=state
            state,action,chem,wt=_advance(
                brain,state,context,mode,receptors,reactions,
                learn=effective_learning,
            )
            if state.coupled.brain.dendrites!=old.coupled.brain.dendrites and not effective_learning:
                raise AssertionError("learn=False strength/STW/LTW mutation")
            if action is None:
                missing+=1
            choice_correct=(action==mapping[context])
            context_correct[context]+=int(choice_correct)
            context_total[context]+=1
            if within>=2:
                steady_correct[context]+=int(choice_correct)
                steady_total[context]+=1
            for k in sums:
                sums[k]+=wt[k]
            for i in range(4):
                sum_chem[i]+=chem[i]
            pool=state.coupled.chemistry.pool
            for cid in peaks_pool:
                peaks_pool[cid]=max(peaks_pool[cid],pool[int(cid)])
            saturated_ticks+=int(any(pool[c]==255 for c in (17,33,1,49,50,51)))
            # External evaluator sees truth AFTER the scored choice. No label,
            # target or reward history enters the brain through any other path.
            delivered_now=False
            if training:
                if via=="D":
                    pulse=ZERO if action is None else (
                        REWARD if choice_correct else PUNISHMENT
                    )
                    state=ArmState(state.coupled,pulse)
                    delivered_now=action is not None
                else:
                    if action is not None:
                        state=ArmState(
                            add_environment_precursors(
                                state.coupled,correct=choice_correct,
                                dose=PRECURSOR_DOSE,
                            ),ZERO,
                        )
                        delivered_now=True
            delivered+=int(delivered_now)
            snap=_neural_snapshot(state.coupled.brain)
            frames.append({
                "tick":state.coupled.brain.tick,
                "context":context,
                "within_block":within,
                "action":action,
                "correct":int(choice_correct),
                "chem_input":list(chem),
                "external_feedback_created":delivered_now,
                "effect":wt["effect"],
                "gain":wt["gain"],
                "lose":wt["lose"],
                "lost_connection":wt["lost_connection"],
                "n_live":snap["n_live"],
                "n_live_stw_ge5":snap["n_live_stw_ge5"],
                "n_live_ltw_positive":snap["n_live_ltw_positive"],
                "strengths":snap["strengths"],
                "stw":snap["stw"],
                "ltw":snap["ltw"],
            })
    if not frames:
        raise AssertionError("empty trial segment")
    if training and via=="D":
        # The current reward is only sent to the NEXT tick, not this one.
        if delivered!=len(frames)-missing:
            raise AssertionError("direct reward schedule cardinality drift")
    if training and via=="M" and delivered!=len(frames)-missing:
        raise AssertionError("precursor schedule cardinality drift")
    if not training and delivered!=0:
        raise AssertionError("holdout generated forbidden external feedback")
    if not effective_learning and state.coupled.brain.dendrites!=initial_neural:
        raise AssertionError("frozen readout/arm mutation")
    full_count=len(frames)
    steady_count=sum(steady_total)
    stats={
        "readout":readout if not training else "training",
        "n_ticks":full_count,
        "context_correct":context_correct,
        "context_total":context_total,
        "steady_correct":steady_correct,
        "steady_total":steady_total,
        "overall":sum(context_correct)/full_count,
        "steady":sum(steady_correct)/steady_count,
        "overall_by_context":[context_correct[c]/context_total[c] for c in (0,1)],
        "steady_by_context":[steady_correct[c]/steady_total[c] for c in (0,1)],
        "missing_actions":missing,
        "new_feedback_events":delivered,
        "chemical_input_auc":sum_chem,
        "chem_pool_peaks":peaks_pool,
        "pool_saturation_ticks":saturated_ticks,
        "synapse_events":sums,
        "final_neural":_neural_snapshot(state.coupled.brain),
        "final_chem_sha256":_sha(asdict(state.coupled.chemistry)),
        "frames":frames,
    }
    return state,stats


def run_seed(seed,receptors=None,reactions=None):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside frozen independent development cohort")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    states={}
    brain=C1ContextBrain(seed)
    for mode in MODES:
        states[mode]=ArmState(initial_coupled(brain,receptors))
    if len({_sha(asdict(x.coupled)) for x in states.values()})!=1:
        raise AssertionError("factorial arms did not share initial state")
    initial_sha=_sha(asdict(states["D0"].coupled))
    golden_state=brain.initial()
    golden_pending=ZERO
    phases={}
    for phase,train_salt,test_salt,mapping in PHASES:
        train_seq=blocks(seed,train_salt,TRAIN_BLOCKS)
        test_seq=blocks(seed,test_salt,TEST_BLOCKS)
        phase_out={}
        for mode in MODES:
            state,training=run_phase(
                brain,states[mode],train_seq,mapping,mode,receptors,reactions,
                training=True,
            )
            states[mode]=state
            readouts={}
            for readout in READOUTS:
                evaluated,info=run_phase(
                    brain,state,test_seq,mapping,mode,receptors,reactions,
                    training=False,readout=readout,
                )
                if evaluated.coupled.brain.tick!=state.coupled.brain.tick+128:
                    raise AssertionError("holdout consumed incorrect ticks")
                if readout=="frozen" and (
                     evaluated.coupled.brain.dendrites!=state.coupled.brain.dendrites
                ):
                    raise AssertionError("frozen readout altered training weights")
                readouts[readout]=info
            phase_out[mode]={"training":training,"readouts":readouts}
        # Gold standard for D0: the very same E09g.5 direct-feedback
        # training and frozen readout. This is checked at *both* phases.
        golden_state,golden_pending=train_brain(
            brain,golden_state,golden_pending,train_seq,mapping,learn=True,
        )
        if (states["D0"].coupled.brain!=golden_state
                or states["D0"].pending!=golden_pending):
            raise AssertionError(f"D0 deviates from original E09g5 {phase} state")
        golden_readout=evaluate_brain(
            brain,golden_state,test_seq,mapping,
        )
        for key in ("overall","steady","overall_by_context","steady_by_context"):
            if phase_out["D0"]["readouts"]["frozen"][key]!=golden_readout[key]:
                raise AssertionError(f"D0 fails original E09g5 {key} in {phase}")
        phases[phase]={
            "mapping":list(mapping),
            "train_blocks":list(train_seq),
            "holdout_blocks":list(test_seq),
            "arms":phase_out,
            "golden_e09g5_neural_equal":True,
            "golden_e09g5_frozen_metrics_equal":True,
        }
    return {"seed":seed,"initial_sha256":initial_sha,**phases}


def _paired_ci(rows,phase,readout,a,b,metric="steady"):
    vals=[]
    for row in rows:
        vals.append(
            row[phase]["arms"][a]["readouts"][readout][metric]
            -row[phase]["arms"][b]["readouts"][readout][metric]
        )
    if not vals:
        return {"mean":None,"ci95":None,"n_seeds":0}
    rng=random.Random(BOOTSTRAP_SEED)
    draws=sorted(statistics.mean(
        rng.choice(vals) for _ in vals
    ) for _ in range(BOOTSTRAP_REPS))
    return {
        "mean":statistics.mean(vals),
        "ci95":[draws[int(0.025*BOOTSTRAP_REPS)],
                draws[int(0.975*BOOTSTRAP_REPS)-1]],
        "n_seeds":len(vals),
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds,tuple) or not seeds
            or len(set(seeds))!=len(seeds)
            or any(type(s) is not int or s not in SEEDS for s in seeds)):
        raise ValueError("only frozen unique development seeds allowed")
    receptors,reactions=selected_genes()
    result=[run_seed(s,receptors,reactions) for s in seeds]
    summary={}
    contrasts={}
    for phase in ("first","reversed"):
        summary[phase]={}
        contrasts[phase]={}
        for mode in MODES:
            summary[phase][mode]={
                readout:{
                    "mean_steady":statistics.mean(
                        row[phase]["arms"][mode]["readouts"][readout]["steady"]
                        for row in result
                    ),
                    "mean_overall":statistics.mean(
                        row[phase]["arms"][mode]["readouts"][readout]["overall"]
                        for row in result
                    ),
                    "mean_end_live":statistics.mean(
                        row[phase]["arms"][mode]["readouts"][readout][
                            "final_neural"]["n_live"]
                        for row in result
                    ),
                    "mean_end_ltw_positive_live":statistics.mean(
                        row[phase]["arms"][mode]["readouts"][readout][
                            "final_neural"]["n_live_ltw_positive"]
                        for row in result
                    ),
                } for readout in READOUTS
            }
            summary[phase][mode]["training"]={
                "mean_steady":statistics.mean(
                    row[phase]["arms"][mode]["training"]["steady"] for row in result
                ),
                "mean_end_live":statistics.mean(
                    row[phase]["arms"][mode]["training"]["final_neural"]["n_live"]
                    for row in result
                ),
                "mean_feedback_events":statistics.mean(
                    row[phase]["arms"][mode]["training"]["new_feedback_events"]
                    for row in result
                ),
                "mean_pool_saturation_ticks":statistics.mean(
                    row[phase]["arms"][mode]["training"]["pool_saturation_ticks"]
                    for row in result
                ),
            }
        for a,b in (("D0","D16"),("M0","M16"),
                    ("D0","M0"),("D16","M16"),
                    ("D16","FD"),("M16","FM")):
            contrasts[phase][f"{a}_minus_{b}"]={
                readout:_paired_ci(result,phase,readout,a,b)
                for readout in READOUTS
            }
        contrasts[phase]["frozen_minus_active_within_each_mode"]={
            mode:{
                "n_seeds":len(result),
                "mean":statistics.mean(
                    row[phase]["arms"][mode]["readouts"]["frozen"]["steady"]
                    -row[phase]["arms"][mode]["readouts"][
                        "active_no_new_reward"]["steady"]
                    for row in result
                ),
            } for mode in MODES
        }
    return {
        "protocol":"NL-EXP-I3c7e-v1",
        "study":"repeated feedback factorial, exploratory development not G05",
        "seeds":list(seeds),
        "n_seeds":len(seeds),
        "modes":list(MODES),
        "phases":["first","reversed"],
        "train_ticks_per_phase":TRAIN_BLOCKS*BLOCK_TICKS,
        "holdout_ticks_per_readout":TEST_BLOCKS*BLOCK_TICKS,
        "readouts":list(READOUTS),
        "original_direct_gene_protocol_exact_match":True,
        "synthetic_loss0_caveat":"CHEM2/3 masked only for neural input, not historical C1 adaptation",
        "equal_dose_caveat":"Direct one-tick255 and chemical precursor80 via reaction are NOT equivalent magnitude or delay; signs are on-policy",
        "no_new_feedback_during_holdout":True,
        "summary":summary,
        "paired_contrasts":contrasts,
        "per_seed_sha256":{str(row["seed"]):_sha(row) for row in result},
        "per_seed":result,
        "gates":{"software":"PASS if assertions hold",
                 "G05":"OPEN","G09":"OPEN","G00H":"OPEN"},
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    data=run_all()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(
            json.dumps(data,sort_keys=True,separators=(",",":"))+"\n",
            encoding="utf-8",
        )
    print(json.dumps({
        k:data[k] for k in (
            "protocol","seeds","n_seeds","train_ticks_per_phase",
            "holdout_ticks_per_readout","summary","paired_contrasts",
            "per_seed_sha256","gates",
        )
    },sort_keys=True))


if __name__=="__main__":
    main()
