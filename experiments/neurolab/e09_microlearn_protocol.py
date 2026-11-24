"""E09.02c: evaluación preregistrada de aprendizaje de preferencia en 5 neuronas."""
from __future__ import annotations
import json
import statistics

from .c1_microlearning import MiniLearner,MiniState

# Solo el EVALUADOR conoce el objetivo; no se pasa al cerebro.
PHASE_A="D0"
PHASE_B="D1"


def train(learner:MiniLearner,state:MiniState,target:str,
          n:int,*,learn:bool=True)->MiniState:
    for _ in range(n):
        trial=learner.respond(state)
        reward=+1 if trial.chosen==target else -1
        state=learner.feedback(state,trial,reward,learn=learn)
    return state


def evaluate(learner:MiniLearner,state:MiniState,target:str,n:int=80)->float:
    correct=0
    seen=state
    for _ in range(n):
        trial=learner.respond(seen)
        correct+=int(trial.chosen==target)
        # Avanza el contador del simulador pero no se administra feedback.
        seen=MiniState(seen.weights,seen.trials+1)
    return correct/n


def run_seed(seed:int)->dict:
    active=MiniLearner(seed)
    frozen=MiniLearner(seed)
    state=active.initial()
    control=frozen.initial()
    state=train(active,state,PHASE_A,60)
    control=train(frozen,control,PHASE_A,60,learn=False)
    accuracy=evaluate(active,state,PHASE_A,80)
    frozen_accuracy=evaluate(frozen,control,PHASE_A,80)
    weights_before=state.weights
    state=train(active,state,PHASE_B,120)
    return {"seed":seed,
            "train":accuracy,
            "frozen":frozen_accuracy,
            "reversal":evaluate(active,state,PHASE_B,80),
            "weights_original":list(weights_before),
            "weights_reversed":list(state.weights)}


def run_all()->dict:
    seeds=[run_seed(i) for i in range(20)]
    n_train=sum(x["train"]>=.90 for x in seeds)
    n_rev=sum(x["reversal"]>=.90 for x in seeds)
    advantage=statistics.mean(x["train"]-x["frozen"] for x in seeds)
    return {
        "protocol":"E09_02C_APRENDIZAJE_PRE_REGISTRO-v1",
        "seeds":20,
        "mean_train":statistics.mean(x["train"] for x in seeds),
        "mean_frozen":statistics.mean(x["frozen"] for x in seeds),
        "mean_reversal":statistics.mean(x["reversal"] for x in seeds),
        "success_train_seeds":n_train,
        "success_reversal_seeds":n_rev,
        "advantage_over_frozen":advantage,
        "passed":n_train>=18 and n_rev>=18 and advantage>=.30,
        "per_seed":seeds,
        "interpretation":"C1-derived rules and own plasticity; no C1 biochemical fidelity",
    }


def main():
    result=run_all()
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result["passed"]:
        raise SystemExit("E09.02c gate not met; retain negative result")


if __name__=="__main__":
    main()
