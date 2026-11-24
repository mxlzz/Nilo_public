"""I3c.7g: preregistered minimal LTW consolidation horizon feasibility.

PRE-REGISTERED BEFORE CODE:
 docs/neurolab/E09_02I_I3C7G_HORIZONTE_CONSOLIDACION_PRE_REGISTRO.md

Short reversed phase: 32 blocks*8 ticks (LTW B gates384/512).
Long reversed phase: same exact first32 blocks +48 balanced blocks
(LTW B gates384/512/640/768/896). No C1 neural/chemical rate changes.
Long arms have EXTRA PRACTICE and reward: no pure causal LTW isolation.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import random
import statistics

from .c1_context_brain import C1ContextBrain
from .e09_context_protocol import (
    blocks, train_brain, evaluate_brain,
    MAPPING_A, MAPPING_B, ZERO,
)
from .e09_coupled_brain import initial_coupled
from .e09_i3_metabolic_protocol import selected_genes
from .e09_i3c7e_loss_factorial import ArmState, run_phase, READOUTS

SEEDS=tuple(range(1700,1720))
CONFIRMATION_SEEDS=tuple(range(1400,1420))
MODES=("M0","M16","D0","FM")
PHASE_A_BLOCKS=32
PHASE_B_SHORT_BLOCKS=32
PHASE_B_EXT_BLOCKS=48
PHASE_B_LONG_BLOCKS=80
TICKS_PER_BLOCK=8
HOLDOUT_BLOCKS=16
LTW_RATE=128
SIGNAL_STW_THRESHOLD=5
BOOTSTRAP_REPS=2000
BOOTSTRAP_SEED=60519


def _hash(obj):
    return sha256(json.dumps(
        obj,sort_keys=True,separators=(",",":")
    ).encode("utf-8")).hexdigest()


def sequences(seed):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside preregistered I3c7g development cohort")
    a=blocks(seed,10000,PHASE_A_BLOCKS)
    a_hold=blocks(seed,30000,HOLDOUT_BLOCKS)
    short=blocks(seed,20000,PHASE_B_SHORT_BLOCKS)
    extension=blocks(seed,24000,PHASE_B_EXT_BLOCKS)
    long=short+extension
    b_hold=blocks(seed,40000,HOLDOUT_BLOCKS)
    if (len(long)!=80 or long[:len(short)]!=short or
            short.count(0)!=short.count(1)!=0 or
            extension.count(0)!=extension.count(1)!=0 or
            long.count(0)!=long.count(1)!=0 or
            len(a)!=32 or len(b_hold)!=16):
        raise AssertionError("nested balanced input schedule mismatch")
    return a,a_hold,short,extension,long,b_hold


def _end_weights(state):
    brain=state.coupled.brain
    return {
        "tick":brain.tick,
        "strengths":[s.strength for s in brain.dendrites],
        "stws":[s.dendrite.stw for s in brain.dendrites],
        "ltws":[s.dendrite.ltw for s in brain.dendrites],
        "n_live":sum(s.strength>0 for s in brain.dendrites),
        "n_live_stw_ge5":sum(
            s.strength>0 and s.dendrite.stw>=SIGNAL_STW_THRESHOLD
            for s in brain.dendrites
        ),
        "n_live_ltw_ge5":sum(
            s.strength>0 and s.dendrite.ltw>=SIGNAL_STW_THRESHOLD
            for s in brain.dendrites
        ),
        "n_live_ltw_positive":sum(
            s.strength>0 and s.dendrite.ltw>0 for s in brain.dendrites
        ),
    }


def _two_readouts(brain,state,seq,mapping,mode,receptors,reactions):
    answer={}
    original_sha=_hash(asdict(state))
    for r in READOUTS:
        derived,metrics=run_phase(
            brain,state,seq,mapping,mode,receptors,reactions,
            training=False,readout=r,
        )
        if derived.coupled.brain.tick!=state.coupled.brain.tick+128:
            raise AssertionError("holdout length changed")
        if metrics["new_feedback_events"]!=0:
            raise AssertionError("holdout received NEW evaluator feedback")
        if r=="frozen" and derived.coupled.brain.dendrites!=state.coupled.brain.dendrites:
            raise AssertionError("frozen evaluator altered weights")
        if _hash(asdict(state))!=original_sha:
            raise AssertionError("readout mutated original training state")
        answer[r]=metrics
    return answer


def _combine_training(prefix,extension):
    """Never pretend this independent extension is a new model."""
    frames=prefix["frames"]+extension["frames"]
    if (len(frames)!=640 or frames[0]["tick"]!=257 or
            frames[-1]["tick"]!=896):
        raise AssertionError("long inverted training did not continue short prefix")
    overall=sum(f["correct"] for f in frames)/len(frames)
    steady=sum(f["correct"] for f in frames if f["within_block"]>=2)/(
        len(frames)*6/8
    )
    auc=[prefix["chemical_input_auc"][i]+extension["chemical_input_auc"][i]
         for i in range(4)]
    effects={k:prefix["synapse_events"][k]+extension["synapse_events"][k]
             for k in prefix["synapse_events"]}
    return {
        "n_ticks":len(frames),
        "overall":overall,
        "steady":steady,
        "feedback_events":(
            prefix["new_feedback_events"]+extension["new_feedback_events"]
        ),
        "chemical_input_auc":auc,
        "loss_gain_events":effects,
        "pool_saturation_ticks":(
            prefix["pool_saturation_ticks"]+extension["pool_saturation_ticks"]
        ),
        "n_context0":sum(f["context"]==0 for f in frames),
        "n_context1":sum(f["context"]==1 for f in frames),
        "frames":frames,
    }


def run_seed(seed,receptors=None,reactions=None):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside I3c7g development cohort")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    brain=C1ContextBrain(seed)
    a,a_hold,b_short,b_ext,b_long,b_hold=sequences(seed)
    # For each algorithm the two B horizons share the *same* A checkpoint,
    # and the long B literally continues the stored short B state.
    answers={}
    golden=brain.initial()
    pending=ZERO
    golden,pending=train_brain(brain,golden,pending,a,MAPPING_A,learn=True)
    golden_first_eval=evaluate_brain(brain,golden,a_hold,MAPPING_A)
    for mode in MODES:
        initial=ArmState(initial_coupled(brain,receptors))
        after_a,a_stats=run_phase(
            brain,initial,a,MAPPING_A,mode,receptors,reactions,
            training=True,
        )
        a_readouts=_two_readouts(
            brain,after_a,a_hold,MAPPING_A,mode,receptors,reactions,
        )
        a_sha=_hash(asdict(after_a))
        if mode=="D0":
            if after_a.coupled.brain!=golden or after_a.pending!=pending:
                raise AssertionError("D0 A state not identical to original E09g5")
            for key in ("steady","overall","steady_by_context","overall_by_context"):
                if a_readouts["frozen"][key]!=golden_first_eval[key]:
                    raise AssertionError("D0 A frozen readout not E09g5")
        after_short,short_stats=run_phase(
            brain,after_a,b_short,MAPPING_B,mode,receptors,reactions,
            training=True,
        )
        prefix_sha=_hash(asdict(after_short))
        if after_short.coupled.brain.tick!=512 or after_a.coupled.brain.tick!=256:
            raise AssertionError("original prefix clock changed")
        if mode=="D0":
            golden_b,pending_b=train_brain(
                brain,golden,pending,b_short,MAPPING_B,learn=True
            )
            if after_short.coupled.brain!=golden_b or after_short.pending!=pending_b:
                raise AssertionError("D0 short B state not identical to E09g5")
            gold_b_eval=evaluate_brain(brain,golden_b,b_hold,MAPPING_B)
        short_end=_end_weights(after_short)
        if any(ltw>4 for ltw in short_end["ltws"]):
            raise AssertionError("short fixed GEN LTW exceeds four tick opportunities")
        short_readouts=_two_readouts(
            brain,after_short,b_hold,MAPPING_B,mode,receptors,reactions,
        )
        if mode=="D0":
            for key in ("steady","overall","steady_by_context","overall_by_context"):
                if short_readouts["frozen"][key]!=gold_b_eval[key]:
                    raise AssertionError("D0 short B frozen readout not E09g5")
        after_long,extra_stats=run_phase(
            brain,after_short,b_ext,MAPPING_B,mode,receptors,reactions,
            training=True,
        )
        if _hash(asdict(after_short))!=prefix_sha:
            raise AssertionError("long extension mutated saved short checkpoint")
        if _hash(asdict(after_a))!=a_sha:
            raise AssertionError("B training mutated A reference checkpoint")
        if after_long.coupled.brain.tick!=896:
            raise AssertionError("long B missed fifth post-reversal LTW gate")
        long_end=_end_weights(after_long)
        if any(ltw>7 for ltw in long_end["ltws"]):
            raise AssertionError("original LTW rate128 maximum seven global gates")
        long_readouts=_two_readouts(
            brain,after_long,b_hold,MAPPING_B,mode,receptors,reactions,
        )
        long_stats=_combine_training(short_stats,extra_stats)
        if long_stats["feedback_events"]<short_stats["new_feedback_events"]:
            raise AssertionError("long exposure smaller than short")
        if mode=="FM":
            if any(x["ltws"]!=[0]*8 for x in (short_end,long_end)):
                raise AssertionError("frozen FM acquired LTW")
        answers[mode]={
            "first":{
                "after_training_sha256":a_sha,
                "training":a_stats,
                "readouts":a_readouts,
                "end_weights":_end_weights(after_a),
            },
            "short":{
                "after_training_sha256":prefix_sha,
                "training":short_stats,
                "readouts":short_readouts,
                "end_weights":short_end,
            },
            "long":{
                "initial_short_prefix_sha256":prefix_sha,
                "training":long_stats,
                "readouts":long_readouts,
                "end_weights":long_end,
            },
        }
    return {
        "seed":seed,
        "source_sequence_a":list(a),
        "source_sequence_b_short":list(b_short),
        "source_sequence_b_extension":list(b_ext),
        "source_sequence_b_long":list(b_long),
        "source_holdout_b":list(b_hold),
        "modes":answers,
        "D0_e09g5_exact_reference":True,
    }


def _ci(rows,mode,kind,metric="steady"):
    vals=[
        row["modes"][mode]["long"]["readouts"][kind][metric]
        -row["modes"][mode]["short"]["readouts"][kind][metric]
        for row in rows
    ]
    rng=random.Random(BOOTSTRAP_SEED)
    draws=sorted(statistics.mean(rng.choice(vals) for _ in vals)
                 for _ in range(BOOTSTRAP_REPS))
    return {
        "mean":statistics.mean(vals),
        "n_seeds":len(vals),
        "ci95":[draws[int(0.025*BOOTSTRAP_REPS)],
                draws[int(0.975*BOOTSTRAP_REPS)-1]],
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds,tuple) or not seeds or
            len(set(seeds))!=len(seeds) or
            any(type(s) is not int or s not in SEEDS for s in seeds)):
        raise ValueError("only unique subset of preregistered development seeds")
    receptors,reactions=selected_genes()
    rows=[run_seed(seed,receptors,reactions) for seed in seeds]
    summary={}
    for mode in MODES:
        summary[mode]={}
        for when in ("short","long"):
            summary[mode][when]={
                "n_seeds":len(rows),
                "ltw_at_least5_before_holdout_total":sum(
                    row["modes"][mode][when]["end_weights"]["n_live_ltw_ge5"]
                    for row in rows
                ),
                "seeds_with_functional_ltw_before_holdout":sum(
                    row["modes"][mode][when]["end_weights"]["n_live_ltw_ge5"]>0
                    for row in rows
                ),
                "mean_live_before_holdout":statistics.mean(
                    row["modes"][mode][when]["end_weights"]["n_live"]
                    for row in rows
                ),
                "mean_new_feedback_events":statistics.mean(
                    row["modes"][mode][when]["training"].get(
                        "feedback_events",
                        row["modes"][mode][when]["training"].get(
                            "new_feedback_events",0,
                        ),
                    ) for row in rows
                ),
                "readouts":{
                    read:{
                        "mean_steady":statistics.mean(
                            row["modes"][mode][when]["readouts"][read]["steady"]
                            for row in rows
                        ),
                        "mean_overall":statistics.mean(
                            row["modes"][mode][when]["readouts"][read]["overall"]
                            for row in rows
                        ),
                        "n_seed_steady_ge90":sum(
                            row["modes"][mode][when]["readouts"][read]["steady"]>=.9
                            for row in rows
                        ),
                    } for read in READOUTS
                },
            }
    contrasts={
        mode:{
            read:_ci(rows,mode,read)
            for read in READOUTS
        } for mode in MODES
    }
    m0=contrasts["M0"]["active_no_new_reward"]
    feasibility=(
        m0["mean"]>=.10 and m0["ci95"][0]>0
        and summary["M0"]["long"]["ltw_at_least5_before_holdout_total"]>0
    )
    return {
        "protocol":"NL-EXP-I3c7g-v1",
        "study":"longer reversal practice constrained by original LTW rate128; not causal isolated LTW effect",
        "seeds":list(seeds),
        "n_seeds":len(seeds),
        "modes":list(MODES),
        "phaseA_ticks":256,
        "phaseB_short_ticks":256,
        "phaseB_long_ticks":640,
        "post_reversal_LTW_gates":{"short":[384,512],
                                    "long":[384,512,640,768,896]},
        "same_short_prefix_in_long":True,
        "same_holdout_sequences":True,
        "summary":summary,
        "paired_long_minus_short":contrasts,
        "exploratory_feasibility_M0":feasibility,
        "original_direct_gene_protocol_exact_short_reference":True,
        "original_quantization_threshold":SIGNAL_STW_THRESHOLD,
        "per_seed_sha256":{str(r["seed"]):_hash(r) for r in rows},
        "per_seed":rows,
        "limitations":"Extra practice/rewards/exposure in long arm. Even if LTW5 appears, cannot attribute performance solely to consolidation; loss0 synthetic not historical and no Norn/full chemistry. Q privileged excluded.",
        "gates":{"software":"PASS if all assertions",
                 "G05":"OPEN","G09":"OPEN","G00H":"OPEN"},
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    out=run_all()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(
            json.dumps(out,sort_keys=True,separators=(",",":"))+"\n",
            encoding="utf-8",
        )
    print(json.dumps({k:out[k] for k in (
        "protocol","seeds","n_seeds","phaseB_short_ticks",
        "phaseB_long_ticks","summary","paired_long_minus_short",
        "exploratory_feasibility_M0","per_seed_sha256","gates"
    )},sort_keys=True))


if __name__=="__main__":
    main()
