"""E09.02g.5: two-context associative learning in six C1-derived units.

32 shuffled, balanced blocks of eight ticks per training phase; 16
blocks per holdout; 20 preregistered seeds. External evaluator knows
S0→D0/S1→D1, then reverses both. No correct labels in C1ContextBrain.

Controls:
1. Same neural circuit with all dendrites frozen.
2. Same neural circuit blinded to sensory context.
3. Simple tabular 2×2 Q associative memory, including an explicit
   previous (context, action) for precise delayed causal credit.
   This tabular control is intentionally better informed about the
   causal provenance of feedback, so it is NOT a matched brain model.

A scientific failure is reported as data, not swallowed or tuned away.
"""
from __future__ import annotations

from dataclasses import asdict
import argparse
import json
import random
import statistics

from .c1_context_brain import C1ContextBrain, ContextBrainState

ZERO=(0,0,0,0)
REWARD=(255,0,0,0)
PUNISHMENT=(0,255,0,0)
MAPPING_A=("D0","D1")
MAPPING_B=("D1","D0")
TRAIN_BLOCKS=32
TEST_BLOCKS=16
BLOCK_TICKS=8


def blocks(seed:int,salt:int,n_blocks:int)->tuple[int,...]:
    if n_blocks%2 or n_blocks<2:
        raise ValueError("se necesitan bloques balanceados")
    arrangement=[0]*(n_blocks//2)+[1]*(n_blocks//2)
    random.Random(seed+salt).shuffle(arrangement)
    return tuple(arrangement)


def train_brain(
    brain:C1ContextBrain, state:ContextBrainState,
    pending:tuple[int,int,int,int], seq:tuple[int,...],
    mapping:tuple[str,str], *, learn:bool,
)->tuple[ContextBrainState,tuple[int,int,int,int]]:
    for context in seq:
        for _ in range(BLOCK_TICKS):
            trace=brain.step(state,context,pending,learn=learn)
            if trace.action is None:
                pending=ZERO
            else:
                pending=REWARD if trace.action==mapping[context] else PUNISHMENT
            state=trace.after
    return state,pending


def evaluate_brain(
    brain:C1ContextBrain, state:ContextBrainState,
    seq:tuple[int,...], mapping:tuple[str,str],
)->dict:
    totals=[0,0]
    correct=[0,0]
    stable_totals=[0,0]
    stable_correct=[0,0]
    early_correct=0
    current=state
    for context in seq:
        for within in range(BLOCK_TICKS):
            tr=brain.step(current,context,ZERO,learn=False)
            current=tr.after
            valid=tr.action==mapping[context]
            totals[context]+=1
            correct[context]+=int(valid)
            if within>=2:
                stable_totals[context]+=1
                stable_correct[context]+=int(valid)
            else:
                early_correct+=int(valid)
    total=sum(totals)
    steady_total=sum(stable_totals)
    return {
        "overall":sum(correct)/total,
        "steady":sum(stable_correct)/steady_total,
        "early":early_correct/(total-steady_total),
        "overall_by_context":[correct[i]/totals[i] for i in (0,1)],
        "steady_by_context":[
            stable_correct[i]/stable_totals[i] for i in (0,1)
        ],
        "total_ticks":total,"steady_ticks":steady_total,
    }


def tabular_step_choice(
    q:list[list[float]], context:int, *, seed:int, tick:int,
    explore:bool,
)->str:
    rng=random.Random(seed*3_000_000+tick+991)
    if explore and rng.random()<.10:
        index=rng.randrange(2)
    elif q[context][0]>q[context][1]:
        index=0
    elif q[context][1]>q[context][0]:
        index=1
    else:
        index=rng.randrange(2)
    return "D0" if index==0 else "D1"


def train_tabular(
    q:list[list[float]],
    pending:tuple[int,int,int]|None,
    seq:tuple[int,...],
    mapping:tuple[str,str],
    *,seed:int,tick:int,
)->tuple[list[list[float]],tuple[int,int,int]|None,int]:
    for context in seq:
        for _ in range(BLOCK_TICKS):
            tick+=1
            if pending is not None:
                prior_context,prior_action,prior_reward=pending
                old=q[prior_context][prior_action]
                q[prior_context][prior_action]=old+.2*(prior_reward-old)
            action=tabular_step_choice(q,context,seed=seed,tick=tick,explore=True)
            action_id=0 if action=="D0" else 1
            reward=1 if action==mapping[context] else -1
            # The baseline remembers the action and sensory context
            # that caused the incoming feedback; the brain does NOT.
            pending=(context,action_id,reward)
    return q,pending,tick


def evaluate_tabular(
    q:list[list[float]],seq:tuple[int,...],
    mapping:tuple[str,str], *,seed:int,start_tick:int,
)->dict:
    totals=[0,0]
    correct=[0,0]
    stable_correct=[0,0]
    early_correct=0
    tick=start_tick
    for context in seq:
        for within in range(BLOCK_TICKS):
            tick+=1
            action=tabular_step_choice(q,context,seed=seed,tick=tick,explore=False)
            ok=int(action==mapping[context])
            totals[context]+=1
            correct[context]+=ok
            if within>=2:
                stable_correct[context]+=ok
            else:
                early_correct+=ok
    all_ticks=sum(totals)
    stable_count=len(seq)*(BLOCK_TICKS-2)
    return {
        "overall":sum(correct)/all_ticks,
        "steady":sum(stable_correct)/stable_count,
        "early":early_correct/(all_ticks-stable_count),
        "overall_by_context":[correct[i]/totals[i] for i in (0,1)],
        "steady_by_context":[
            stable_correct[i]/(totals[i]*(BLOCK_TICKS-2)/BLOCK_TICKS)
            for i in (0,1)
        ],
        "total_ticks":all_ticks,"steady_ticks":stable_count,
    }


def _state_snapshot(s:ContextBrainState)->dict:
    return {
        "tick":s.tick,
        "neuron_states":list(s.neuron_states),
        "neuron_outputs":list(s.neuron_outputs),
        "concept_outputs":list(s.concept_outputs),
        "synapses":[asdict(d) for d in s.dendrites],
    }


def run_seed(seed:int)->dict:
    schedule_a=blocks(seed,10000,TRAIN_BLOCKS)
    schedule_b=blocks(seed,20000,TRAIN_BLOCKS)
    holdout_a=blocks(seed,30000,TEST_BLOCKS)
    holdout_b=blocks(seed,40000,TEST_BLOCKS)

    neural=C1ContextBrain(seed)
    frozen=C1ContextBrain(seed)
    blind=C1ContextBrain(seed,blind=True)
    state,pulse=train_brain(neural,neural.initial(),ZERO,schedule_a,
                            MAPPING_A,learn=True)
    frozen_state,frozen_pulse=train_brain(frozen,frozen.initial(),ZERO,
                                          schedule_a,MAPPING_A,learn=False)
    blind_state,blind_pulse=train_brain(blind,blind.initial(),ZERO,
                                        schedule_a,MAPPING_A,learn=True)
    phase1=evaluate_brain(neural,state,holdout_a,MAPPING_A)
    frozen_phase1=evaluate_brain(frozen,frozen_state,holdout_a,MAPPING_A)
    blind_phase1=evaluate_brain(blind,blind_state,holdout_a,MAPPING_A)
    first_state=_state_snapshot(state)

    state,pulse=train_brain(neural,state,pulse,schedule_b,MAPPING_B,learn=True)
    frozen_state,frozen_pulse=train_brain(frozen,frozen_state,frozen_pulse,
                                          schedule_b,MAPPING_B,learn=False)
    blind_state,blind_pulse=train_brain(blind,blind_state,blind_pulse,
                                        schedule_b,MAPPING_B,learn=True)
    phase2=evaluate_brain(neural,state,holdout_b,MAPPING_B)
    frozen_phase2=evaluate_brain(frozen,frozen_state,holdout_b,MAPPING_B)
    blind_phase2=evaluate_brain(blind,blind_state,holdout_b,MAPPING_B)

    table=[[0.0,0.0],[0.0,0.0]]
    table,table_pending,table_tick=train_tabular(
        table,None,schedule_a,MAPPING_A,seed=seed,tick=0)
    table1=evaluate_tabular(table,holdout_a,MAPPING_A,seed=seed,start_tick=table_tick)
    table_at_first=[list(x) for x in table]
    table,table_pending,table_tick=train_tabular(
        table,table_pending,schedule_b,MAPPING_B,seed=seed,tick=table_tick)
    table2=evaluate_tabular(table,holdout_b,MAPPING_B,seed=seed,start_tick=table_tick)

    return {
        "seed":seed,
        "schedule_blocks_a":list(schedule_a),
        "schedule_blocks_b":list(schedule_b),
        "neural_first":phase1,"neural_reversed":phase2,
        "frozen_first":frozen_phase1,"frozen_reversed":frozen_phase2,
        "blind_first":blind_phase1,"blind_reversed":blind_phase2,
        "tabular_first":table1,"tabular_reversed":table2,
        "tabular_q_after_first":table_at_first,
        "tabular_q_after_reverse":[list(x) for x in table],
        "neural_after_first":first_state,
        "neural_after_reversal":_state_snapshot(state),
    }


def run_all()->dict:
    results=[run_seed(seed) for seed in range(20)]
    good_both=sum(
        r["neural_first"]["steady"]>=.90
        and r["neural_reversed"]["steady"]>=.90 for r in results
    )
    mean=lambda model,when:statistics.mean(r[model+"_"+when]["steady"] for r in results)
    advantage_frozen=mean("neural","first")-mean("frozen","first")
    advantage_blind=mean("neural","first")-mean("blind","first")
    gate=good_both>=18 and advantage_frozen>=.25 and advantage_blind>=.20
    return {
        "protocol":"E09_02G_05_DOS_CONCEPTOS_PRE_REGISTRO-v1",
        "n_seeds":20,
        "train_ticks_per_phase":TRAIN_BLOCKS*BLOCK_TICKS,
        "holdout_ticks_per_phase":TEST_BLOCKS*BLOCK_TICKS,
        "n_units":6,"n_plastic_dendrites":8,
        "mean_steady":{
            label:{phase:mean(label,phase) for phase in ("first","reversed")}
            for label in ("neural","frozen","blind","tabular")
        },
        "mean_overall":{
            label:{phase:statistics.mean(
                r[label+"_"+phase]["overall"] for r in results)
                for phase in ("first","reversed")}
            for label in ("neural","frozen","blind","tabular")
        },
        "good_both":good_both,
        "advantage_first_vs_frozen":advantage_frozen,
        "advantage_first_vs_blind":advantage_blind,
        "passed":gate,
        "per_seed":results,
        "limitations":"Concept detectors prewired; tabular has explicit causal provenance; external feedback",
    }


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--strict",action="store_true")
    args=parser.parse_args()
    result=run_all()
    print(json.dumps(result,indent=2,sort_keys=True))
    if args.strict and not result["passed"]:
        raise SystemExit("E09g5 gate not met; preserve as negative evidence")


if __name__=="__main__":
    main()
