"""E09.02g.3 preregistered C1 continuous-clock 5-node experiment.

Two tie policies: historically grounded first-index WTA and laboratory
random-tie control. 20 seeds each; initial 60 ticks, reversed 120 ticks,
80-step non-learning holdouts. Reward/Punishment chemical pulses arrive
ONE TICK AFTER the action; this delay is a LAB abstraction, not a
complete C1 biochemical simulation.
"""
from __future__ import annotations

import argparse
import json
import statistics

from .c1_continuous_brain import C1ContinuousBrain,ContinuousBrainState


ZERO=(0,0,0,0)


def train(brain:C1ContinuousBrain,state:ContinuousBrainState,
          incoming:tuple[int,int,int,int],target:str,n:int,
          *,learn:bool=True)->tuple[ContinuousBrainState,tuple[int,int,int,int]]:
    for _ in range(n):
        trace=brain.step(state,incoming,learn=learn)
        # External evaluator only; brain receives chemicals, not target.
        if trace.action is None:
            incoming=ZERO
        else:
            incoming=(255,0,0,0) if trace.action==target else (0,255,0,0)
        state=trace.after
    return state,incoming


def evaluate(brain:C1ContinuousBrain,state:ContinuousBrainState,
             target:str,n:int=80)->float:
    correct=0
    spectator=state
    for _ in range(n):
        trace=brain.step(spectator,ZERO,learn=False)
        correct+=int(trace.action==target)
        spectator=trace.after
    return correct/n


def snapshot(state:ContinuousBrainState)->dict:
    return {
        "tick":state.tick,
        "neuron_states":list(state.neuron_states),
        "neuron_outputs":list(state.neuron_outputs),
        "concept_output":state.concept_output,
        "synapses":[{
            "susceptibility":d.dendrite.susceptibility,
            "stw":d.dendrite.stw,
            "ltw":d.dendrite.ltw,
            "strength":d.strength,
        } for d in state.dendrites],
    }


def run_seed(seed:int,tie_mode:str)->dict:
    brain=C1ContinuousBrain(seed,tie_mode=tie_mode)
    frozen=C1ContinuousBrain(seed,tie_mode=tie_mode)
    learned,pulse=train(brain,brain.initial(),ZERO,"D0",60)
    control,_=train(frozen,frozen.initial(),ZERO,"D0",60,learn=False)
    learned_acc=evaluate(brain,learned,"D0")
    frozen_acc=evaluate(frozen,control,"D0")
    after_first=snapshot(learned)
    learned,pulse=train(brain,learned,pulse,"D1",120)
    after_second=snapshot(learned)
    return {
        "seed":seed,
        "train":learned_acc,
        "frozen":frozen_acc,
        "reversal":evaluate(brain,learned,"D1"),
        "after_train":after_first,
        "after_reversal":after_second,
    }


def run_all()->dict:
    conditions={}
    for mode in ("first_index","random_tie"):
        rows=[run_seed(seed,mode) for seed in range(20)]
        good1=sum(x["train"]>=.90 for x in rows)
        good2=sum(x["reversal"]>=.90 for x in rows)
        advantage=statistics.mean(x["train"]-x["frozen"] for x in rows)
        conditions[mode]={
            "mean_train":statistics.mean(x["train"] for x in rows),
            "mean_frozen":statistics.mean(x["frozen"] for x in rows),
            "mean_reversal":statistics.mean(x["reversal"] for x in rows),
            "good_train":good1,
            "good_reversal":good2,
            "advantage_vs_frozen":advantage,
            "passed":good1>=18 and good2>=18 and advantage>=.30,
            "per_seed":rows,
        }
    return {
        "protocol":"E09_02G_03_RELOJ_CONTINUO_PRE_REGISTRO-v1",
        "conditions":conditions,
        "seeds_per_condition":20,
        "initial_ticks":60,"reversal_ticks":120,"holdout_ticks":80,
        "at_least_one_gate_passed":any(x["passed"] for x in conditions.values()),
        "scope":"five units, prior Concept/Decision WTA outputs, persistent neuron STATE; externally delayed chemicals",
    }


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--strict",action="store_true")
    args=parser.parse_args()
    data=run_all()
    print(json.dumps(data,indent=2,sort_keys=True))
    if args.strict and not data["at_least_one_gate_passed"]:
        raise SystemExit("E09g3 no scientific gate met; result retained")


if __name__=="__main__":
    main()
