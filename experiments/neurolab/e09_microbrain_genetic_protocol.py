"""E09.02g.2: four preregistered 5-neuron WTA/chemical feedback trials.

All contingencies remain in THIS evaluator, never inside the brain:
D0 is rewarded for 60 trials; then D1 is rewarded for 120 trials.
Holdouts contain no synaptic updates. 20 seeds per condition, frozen
controls, same trial counts as the previous E09e experiment.

A scientific gate may fail without being a software error; JSON records
pass/fail explicitly and --strict makes the process exit nonzero.
"""
from __future__ import annotations

import argparse
import json
import statistics

from .c1_microbrain_genetic import MicroBrainState, MicroC1Brain


CONDITIONS=(
    ("post_wta_gated","first_index"),
    ("post_wta_gated","random_tie"),
    ("pre_wta_all","first_index"),
    ("pre_wta_all","random_tie"),
)


def train(brain:MicroC1Brain,state:MicroBrainState,
          target:str,n:int,*,learn:bool=True)->MicroBrainState:
    for _ in range(n):
        choice=brain.respond(state)
        pulse=(255,0,0,0) if choice.action==target else (0,255,0,0)
        state=brain.feedback(state,choice,pulse,learn=learn).after
    return state


def evaluate(brain:MicroC1Brain,state:MicroBrainState,target:str,n:int=80)->float:
    correct=0
    spectator=state
    for _ in range(n):
        choice=brain.respond(spectator)
        correct+=int(choice.action==target)
        spectator=MicroBrainState(spectator.dendrites,spectator.trials+1)
    return correct/n


def _snapshot(state:MicroBrainState)->list[dict]:
    return [
        {
            "susceptibility":syn.dendrite.susceptibility,
            "stw":syn.dendrite.stw,
            "ltw":syn.dendrite.ltw,
            "strength":syn.strength,
        } for syn in state.dendrites
    ]


def run_seed(seed:int,timing:str,tie_mode:str)->dict:
    brain=MicroC1Brain(seed,timing=timing,tie_mode=tie_mode)
    frozen=MicroC1Brain(seed,timing=timing,tie_mode=tie_mode)
    learned=train(brain,brain.initial(),"D0",60)
    control=train(frozen,frozen.initial(),"D0",60,learn=False)
    phase1=evaluate(brain,learned,"D0")
    frozen_phase1=evaluate(frozen,control,"D0")
    after_train=_snapshot(learned)
    learned=train(brain,learned,"D1",120)
    phase2=evaluate(brain,learned,"D1")
    return {
        "seed":seed,"train":phase1,"frozen":frozen_phase1,
        "reversal":phase2,
        "after_train":after_train,
        "after_reversal":_snapshot(learned),
    }


def run_all()->dict:
    output={}
    for timing,tie_mode in CONDITIONS:
        rows=[run_seed(seed,timing,tie_mode) for seed in range(20)]
        good_train=sum(row["train"]>=0.90 for row in rows)
        good_reverse=sum(row["reversal"]>=0.90 for row in rows)
        advantage=statistics.mean(row["train"]-row["frozen"] for row in rows)
        mean_train=statistics.mean(row["train"] for row in rows)
        mean_rev=statistics.mean(row["reversal"] for row in rows)
        mean_frozen=statistics.mean(row["frozen"] for row in rows)
        output[f"{timing}/{tie_mode}"]={
            "timing":timing,"tie_mode":tie_mode,
            "mean_train":mean_train,
            "mean_reversal":mean_rev,
            "mean_frozen":mean_frozen,
            "seeds_train_at_least_90pct":good_train,
            "seeds_reversal_at_least_90pct":good_reverse,
            "advantage_vs_frozen":advantage,
            "passed":good_train>=18 and good_reverse>=18 and advantage>=.30,
            "per_seed":rows,
        }
    return {
        "protocol":"E09_02G_02_MICRORED_PRE_REGISTRO-v1",
        "seeds_per_condition":20,
        "training_episodes":60,
        "reversal_episodes":120,
        "holdout_episodes_per_phase":80,
        "conditions":output,
        "at_least_one_gate_passed":any(x["passed"] for x in output.values()),
        "scope":"5 synthetic units, historical arithmetic and dendritic genetics; simplified timing/feedback",
    }


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--strict",action="store_true",
                        help="exit nonzero when no scientific condition passes")
    args=parser.parse_args()
    outcome=run_all()
    print(json.dumps(outcome,indent=2,sort_keys=True))
    if args.strict and not outcome["at_least_one_gate_passed"]:
        raise SystemExit("E09g.2 all preregistered gates failed")


if __name__=="__main__":
    main()
