"""E09.02e preregistered 20-seed twin-weight reversal experiment."""
from __future__ import annotations

import json
import statistics

from .c1_twinsynapse_brain import TwinBrainLearner, TwinBrainState


def train(model:TwinBrainLearner,state:TwinBrainState,target:str,n:int,*,learn:bool=True)->TwinBrainState:
    for _ in range(n):
        tr=model.respond(state)
        reward=+1 if tr.chosen==target else -1
        state=model.feedback(state,tr,reward,learn=learn)
    return state


def evaluate(model:TwinBrainLearner,state:TwinBrainState,target:str,n:int=80)->float:
    score=0
    current=state
    for _ in range(n):
        tr=model.respond(current)
        score+=int(tr.chosen==target)
        current=TwinBrainState(current.synapses,current.trials+1)
    return score/n


def run_seed(seed:int)->dict:
    model=TwinBrainLearner(seed)
    control=TwinBrainLearner(seed)
    s=train(model,model.initial(),"D0",60)
    frozen=train(control,control.initial(),"D0",60,learn=False)
    train_acc=evaluate(model,s,"D0")
    frozen_acc=evaluate(control,frozen,"D0")
    before=[{"stw":d.stw,"ltw":d.ltw} for d in s.synapses]
    s=train(model,s,"D1",120)
    reverse_acc=evaluate(model,s,"D1")
    after=[{"stw":d.stw,"ltw":d.ltw} for d in s.synapses]
    return {"seed":seed,"train":train_acc,"frozen":frozen_acc,
            "reversal":reverse_acc,
            "synapses_before_reversal":before,
            "synapses_after_reversal":after}


def run_all()->dict:
    seeds=[run_seed(i) for i in range(20)]
    n_train=sum(x["train"]>=.90 for x in seeds)
    n_rev=sum(x["reversal"]>=.90 for x in seeds)
    advantage=statistics.mean(x["train"]-x["frozen"] for x in seeds)
    passed=n_train>=18 and n_rev>=18 and advantage>=.30 and n_rev>6
    return {
        "protocol":"E09_02E_STW_LTW_PRE_REGISTRO-v1",
        "seeds":20,
        "mean_train":statistics.mean(x["train"] for x in seeds),
        "mean_frozen":statistics.mean(x["frozen"] for x in seeds),
        "mean_reversal":statistics.mean(x["reversal"] for x in seeds),
        "success_train_seeds":n_train,
        "success_reversal_seeds":n_rev,
        "advantage_over_frozen":advantage,
        "better_than_greedy_6_seeds":n_rev>6,
        "passed":passed,
        "per_seed":seeds,
        "model":"NeuroLab E04 twin rates + C1 genomic neuron rules; NOT C1 engine kinetics",
    }


def main()->None:
    outcome=run_all()
    print(json.dumps(outcome,indent=2,sort_keys=True))
    if not outcome["passed"]:
        raise SystemExit("E09.02e preregistered STW/LTW gate failed")


if __name__=="__main__":
    main()
