"""E09.02d preregistered 20-seed epsilon-vs-greedy trial.

All contingencies remain in e09_microlearn_protocol.py (evaluator only).
The original failing E09.02c results are preserved as control.
"""
from __future__ import annotations

import json
import statistics

from .c1_microlearning import MiniLearner
from .c1_microlearning_exploration import EpsilonLearner
from .e09_microlearn_protocol import train, evaluate, run_all as baseline_all


def run_seed(seed: int) -> dict:
    learner=EpsilonLearner(seed)
    frozen=EpsilonLearner(seed)
    state=train(learner,learner.initial(),"D0",60,learn=True)
    frozen_state=train(frozen,frozen.initial(),"D0",60,learn=False)
    train_score=evaluate(learner,state,"D0",80)
    frozen_score=evaluate(frozen,frozen_state,"D0",80)
    weight_initial=list(state.weights)
    state=train(learner,state,"D1",120,learn=True)
    reverse_score=evaluate(learner,state,"D1",80)
    # Cost of exploration: fraction of evaluation decisions differing
    # from the same frozen-policy greedy winning neuron when there is a winner.
    # No learning is performed in these holdout trials.
    explore_chosen=0
    available_greedy=0
    seen=state
    for _ in range(80):
        trial=learner.respond(seen)
        if trial.trace.action is not None:
            available_greedy+=1
            if trial.chosen!=trial.trace.action:
                explore_chosen+=1
        seen=type(seen)(seen.weights,seen.trials+1)
    return {
        "seed":seed,"train":train_score,"frozen":frozen_score,
        "reversal":reverse_score,"weights_after_train":weight_initial,
        "weights_after_reversal":list(state.weights),
        "exploratory_overrides":explore_chosen,
        "greedy_available":available_greedy,
    }


def run_all() -> dict:
    runs=[run_seed(seed) for seed in range(20)]
    baseline=baseline_all()
    wins_train=sum(row["train"]>=.90 for row in runs)
    wins_rev=sum(row["reversal"]>=.90 for row in runs)
    adv=statistics.mean(row["train"]-row["frozen"] for row in runs)
    override_count=sum(row["exploratory_overrides"] for row in runs)
    available=sum(row["greedy_available"] for row in runs)
    passed=wins_train>=18 and wins_rev>=18 and adv>=.30 and wins_rev>baseline["success_reversal_seeds"]
    return {
        "protocol":"E09_02D_EXPLORACION_PRE_REGISTRO-v1",
        "epsilon":0.10,
        "seeds":20,
        "mean_train":statistics.mean(x["train"] for x in runs),
        "mean_frozen":statistics.mean(x["frozen"] for x in runs),
        "mean_reversal":statistics.mean(x["reversal"] for x in runs),
        "success_train_seeds":wins_train,
        "success_reversal_seeds":wins_rev,
        "advantage_over_frozen":adv,
        "override_count_evaluation":override_count,
        "override_fraction_with_greedy_available":override_count/available if available else None,
        "baseline_greedy": {
            "mean_train":baseline["mean_train"],
            "mean_reversal":baseline["mean_reversal"],
            "success_reversal_seeds":baseline["success_reversal_seeds"],
            "passed":baseline["passed"],
        },
        "passed":passed,
        "per_seed":runs,
    }


def main() -> None:
    result=run_all()
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result["passed"]:
        raise SystemExit("E09.02d preregistered gate failed (preserve negative result)")


if __name__=="__main__":
    main()
