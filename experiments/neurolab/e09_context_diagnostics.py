"""E09.02g.5a EXPLORATORY diagnosis after observing g5 failure.

This is NOT preregistered confirmatory evidence. It does not change
C1ContextBrain, training episodes, weights, chemistry, or thresholds.
It instruments holdout ticks to locate context-switch timing and
persistent choice errors. Its sole purpose is to guide a FUTURE,
separately preregistered experiment.
"""
from __future__ import annotations

import json
import statistics

from .c1_context_brain import C1ContextBrain, ContextBrainState
from .e09_context_protocol import (
    BLOCK_TICKS,TRAIN_BLOCKS,TEST_BLOCKS,ZERO,
    MAPPING_A,MAPPING_B,blocks,train_brain,evaluate_brain,
)


def inspect_holdout(
    brain:C1ContextBrain, state:ContextBrainState,
    schedule:tuple[int,...],mapping:tuple[str,str],
    *,include_trace:bool=False,
)->dict:
    current=state
    ticks=[]
    first_of_switched=[]
    first_of_repeated=[]
    for block_index,context in enumerate(schedule):
        switched=block_index>0 and context!=schedule[block_index-1]
        for position in range(BLOCK_TICKS):
            sample=brain.step(current,context,ZERO,learn=False)
            current=sample.after
            correct=sample.action==mapping[context]
            ticks.append({
                "block":block_index,
                "position":position,
                "context":context,
                "changed_context":switched,
                "correct":correct,
                "action":sample.action,
                "old_concepts":list(sample.old_concepts),
                "scores":list(sample.scores),
                "old_decisions":list(sample.old_decisions),
                "new_concepts":list(sample.after.concept_outputs),
                "new_decisions":list(sample.after.neuron_outputs),
            })
            if position==0 and block_index>0:
                (first_of_switched if switched else first_of_repeated).append(int(correct))
    per_position=[]
    for position in range(BLOCK_TICKS):
        sub=[x for x in ticks if x["position"]==position]
        per_position.append(sum(x["correct"] for x in sub)/len(sub))
    overall=sum(x["correct"] for x in ticks)/len(ticks)
    steady=sum(x["correct"] for x in ticks if x["position"]>=2)/(len(schedule)*6)
    switched_blocks=[
        i for i in range(1,len(schedule)) if schedule[i]!=schedule[i-1]
    ]
    return {
        "overall":overall,
        "steady":steady,
        "position_accuracy":per_position,
        "context_switches":len(switched_blocks),
        "first_tick_after_switch_accuracy":(
            sum(first_of_switched)/len(first_of_switched)
            if first_of_switched else None
        ),
        "first_tick_after_repeated_block_accuracy":(
            sum(first_of_repeated)/len(first_of_repeated)
            if first_of_repeated else None
        ),
        "blocks":len(schedule),
        "context_accuracy":{
            str(i):sum(x["correct"] for x in ticks if x["context"]==i)/(
                len([x for x in ticks if x["context"]==i])
            ) for i in (0,1)
        },
        **({"trace":ticks} if include_trace else {}),
    }


def run_seed_diagnostic(seed:int,*,include_trace:bool=False)->dict:
    brain=C1ContextBrain(seed)
    sa=blocks(seed,10000,TRAIN_BLOCKS)
    sb=blocks(seed,20000,TRAIN_BLOCKS)
    ha=blocks(seed,30000,TEST_BLOCKS)
    hb=blocks(seed,40000,TEST_BLOCKS)
    state,pending=train_brain(brain,brain.initial(),ZERO,sa,MAPPING_A,learn=True)
    first=inspect_holdout(brain,state,ha,MAPPING_A,include_trace=include_trace)
    reference_a=evaluate_brain(brain,state,ha,MAPPING_A)
    if abs(first["steady"]-reference_a["steady"])>1e-12:
        raise AssertionError("diagnóstico no coincide con gate preregistrada fase A")
    state,pending=train_brain(brain,state,pending,sb,MAPPING_B,learn=True)
    reversed_=inspect_holdout(brain,state,hb,MAPPING_B,include_trace=include_trace)
    reference_b=evaluate_brain(brain,state,hb,MAPPING_B)
    if abs(reversed_["steady"]-reference_b["steady"])>1e-12:
        raise AssertionError("diagnóstico no coincide con gate preregistrada fase B")
    return {
        "seed":seed,
        "failed_joint_gate":first["steady"]<.90 or reversed_["steady"]<.90,
        "first":first,
        "reversed":reversed_,
    }


def run_all()->dict:
    # For examples, record traces in selected failing seeds found in g5.
    # Selection is EXPLICITLY post-hoc; numerical claims rely on all 20.
    examples=(2,16)
    rows=[run_seed_diagnostic(seed,include_trace=seed in examples)
          for seed in range(20)]
    aggregated={}
    for phase in ("first","reversed"):
        data=[row[phase] for row in rows]
        aggregated[phase]={
            "mean_overall":statistics.mean(d["overall"] for d in data),
            "mean_steady":statistics.mean(d["steady"] for d in data),
            "mean_by_position":[statistics.mean(
                d["position_accuracy"][pos] for d in data
            ) for pos in range(BLOCK_TICKS)],
            "mean_first_tick_after_switch":statistics.mean(
                d["first_tick_after_switch_accuracy"] for d in data
                if d["first_tick_after_switch_accuracy"] is not None
            ),
            "mean_first_tick_repeated_block":statistics.mean(
                d["first_tick_after_repeated_block_accuracy"] for d in data
                if d["first_tick_after_repeated_block_accuracy"] is not None
            ),
        }
    return {
        "label":"EXPLORATORY POST-HOC (not preregistered)",
        "source":"E09g.5 frozen experimental configuration",
        "n_seeds":20,
        "failing_seeds":[x["seed"] for x in rows if x["failed_joint_gate"]],
        "aggregate":aggregated,
        "per_seed":rows,
        "interpretation_warning":"Do not use this to change E09g5 thresholds or claim a confirmatory mechanism.",
    }


def main()->None:
    print(json.dumps(run_all(),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
