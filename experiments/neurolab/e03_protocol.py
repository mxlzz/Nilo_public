"""E03 pre-registered experiment runner: 20 seeds and frozen baseline.

All A→D0/B→D1 labels live HERE, never in plasticity.py. Neurons only
see numeric stimuli; after their choice, the evaluator sends +1 or -1.
The evaluation never updates weights.
"""
from __future__ import annotations

import json
import random
import statistics
from typing import Mapping

from .plasticity import PlasticLearner, PlasticState

ORIGINAL = {"A": "D0", "B": "D1"}
REVERSED = {"A": "D1", "B": "D0"}


def sequence(seed: int, *, n_per_class: int, salt: int) -> tuple[str, ...]:
    events = ["A"] * n_per_class + ["B"] * n_per_class
    random.Random(seed + salt).shuffle(events)
    return tuple(events)


def encode(signal: str) -> tuple[int, int]:
    if signal == "A":
        return 255, 0
    if signal == "B":
        return 0, 255
    raise ValueError("estímulo desconocido")


def train(
    learner: PlasticLearner, state: PlasticState, events: tuple[str, ...],
    expected: Mapping[str, str], *, learning: bool
) -> PlasticState:
    for event in events:
        trial = learner.respond(state, encode(event))
        reward = 1 if trial.action == expected[event] else -1
        state = learner.update(state, trial, reward, learning=learning)
    return state


def evaluate(
    learner: PlasticLearner, state: PlasticState, events: tuple[str, ...],
    expected: Mapping[str, str]
) -> float:
    correct = sum(
        learner.respond(state, encode(event)).action == expected[event]
        for event in events
    )
    return correct / len(events)


def experiment_for_seed(seed: int) -> dict:
    trained = PlasticLearner(seed, rate=16)
    frozen = PlasticLearner(seed, rate=16)
    state_t = trained.initial()
    state_f = frozen.initial()
    learn_data = sequence(seed, n_per_class=50, salt=1000)  # total 100
    holdout = sequence(seed, n_per_class=40, salt=2000)  # total 80, sin refuerzo
    state_t = train(trained, state_t, learn_data, ORIGINAL, learning=True)
    state_f = train(frozen, state_f, learn_data, ORIGINAL, learning=False)
    original_accuracy = evaluate(trained, state_t, holdout, ORIGINAL)
    frozen_accuracy = evaluate(frozen, state_f, holdout, ORIGINAL)
    inversion = sequence(seed, n_per_class=80, salt=3000)  # total 160
    state_t = train(trained, state_t, inversion, REVERSED, learning=True)
    reversal_holdout = sequence(seed, n_per_class=40, salt=4000)
    reversed_accuracy = evaluate(trained, state_t, reversal_holdout, REVERSED)
    return {
        "seed": seed,
        "before": list(trained.initial_weights),
        "after_train": original_accuracy,
        "frozen": frozen_accuracy,
        "after_reversal": reversed_accuracy,
        "weights_reversed": list(state_t.weights),
        "weights_frozen": list(state_f.weights),
        "events_train": len(learn_data),
        "events_reversal": len(inversion)
    }


def run_all() -> dict:
    seeds = [experiment_for_seed(seed) for seed in range(20)]
    winners = sum(x["after_train"] >= 0.9 for x in seeds)
    reversers = sum(x["after_reversal"] >= 0.9 for x in seeds)
    delta = statistics.mean(x["after_train"] - x["frozen"] for x in seeds)
    result = {
        "protocol": "E03_PRE_REGISTRO v1",
        "neuron_model": "NeuroLab experimental, not C1 historical",
        "n_seeds": len(seeds),
        "passed": winners >= 18 and reversers >= 18 and delta >= 0.30,
        "seeds_train_at_least_0_9": winners,
        "seeds_reversal_at_least_0_9": reversers,
        "mean_train": statistics.mean(x["after_train"] for x in seeds),
        "mean_frozen": statistics.mean(x["frozen"] for x in seeds),
        "mean_delta": delta,
        "mean_reversed": statistics.mean(x["after_reversal"] for x in seeds),
        "per_seed": seeds,
    }
    return result


def main() -> None:
    result = run_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit("E03 pre-registered acceptance gate NOT met")


if __name__ == "__main__":
    main()
