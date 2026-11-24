"""E06: contextual XOR with pair concepts vs fixed memory/singleton baselines."""
from __future__ import annotations

import json
import random
import statistics

from .concepts import ConceptLearner, ConceptWeights


PATTERNS = ((0, 2), (0, 3), (1, 2), (1, 3))
TARGET = {(0, 2): "D0", (0, 3): "D1", (1, 2): "D1", (1, 3): "D0"}


def encode(pattern: tuple[int, int], context: int) -> tuple[int, ...]:
    if pattern not in PATTERNS or context not in (0, 1) or isinstance(context, bool):
        raise ValueError("patrón o contexto inválido")
    bits = [0] * 5
    bits[pattern[0]] = 1
    bits[pattern[1]] = 1
    bits[4] = context
    return tuple(bits)


def sequence(seed: int, *, context: int, repetitions: int, salt: int) -> tuple[tuple[int, int], ...]:
    patterns = list(PATTERNS) * repetitions
    random.Random(seed + salt).shuffle(patterns)
    return tuple(patterns)


def train(
    learner: ConceptLearner, state: ConceptWeights,
    patterns: tuple[tuple[int, int], ...], *, context: int, learn: bool
) -> ConceptWeights:
    for pattern in patterns:
        choice = learner.respond(state, encode(pattern, context))
        reward = +1 if choice.action == TARGET[pattern] else -1
        state = learner.update(state, choice, reward, learn=learn)
    return state


def evaluate(learner: ConceptLearner, state: ConceptWeights,
             patterns: tuple[tuple[int, int], ...], *, context: int) -> float:
    correct = sum(learner.respond(state, encode(pattern, context)).action == TARGET[pattern]
                  for pattern in patterns)
    return correct / len(patterns)


def memory_baseline(train_patterns: tuple[tuple[int, int], ...],
                    test_patterns: tuple[tuple[int, int], ...]) -> float:
    memory = {encode(p, 0): TARGET[p] for p in train_patterns}
    return sum(memory.get(encode(p, 1), "D0") == TARGET[p]
               for p in test_patterns) / len(test_patterns)


def run_seed(seed: int) -> dict:
    data = sequence(seed, context=0, repetitions=30, salt=6000)
    holdout = sequence(seed, context=1, repetitions=20, salt=7000)
    concept, singleton, frozen = (
        ConceptLearner(seed, mode="pair"),
        ConceptLearner(seed, mode="singleton"),
        ConceptLearner(seed, mode="pair"),
    )
    cp = train(concept, concept.initial(), data, context=0, learn=True)
    sp = train(singleton, singleton.initial(), data, context=0, learn=True)
    fp = train(frozen, frozen.initial(), data, context=0, learn=False)
    return {
        "seed": seed,
        "concept": evaluate(concept, cp, holdout, context=1),
        "singleton": evaluate(singleton, sp, holdout, context=1),
        "frozen": evaluate(frozen, fp, holdout, context=1),
        "exact_memory": memory_baseline(data, holdout),
        "pairs": {str(pattern): concept.respond(cp, encode(pattern,1)).action
                  for pattern in PATTERNS},
        "weights": [list(x) for x in cp.edges],
    }


def run_all() -> dict:
    runs = [run_seed(seed) for seed in range(20)]
    n_success = sum(x["concept"] >= 0.90 for x in runs)
    adv_memory = statistics.mean(x["concept"] - x["exact_memory"] for x in runs)
    adv_single = statistics.mean(x["concept"] - x["singleton"] for x in runs)
    return {
        "protocol": "E06_PRE_REGISTRO v1",
        "scope": "fixed pair detectors, context-invariance only, not learned concepts",
        "n_seeds": len(runs),
        "at_least_90_percent": n_success,
        "avg_concept": statistics.mean(x["concept"] for x in runs),
        "avg_singleton": statistics.mean(x["singleton"] for x in runs),
        "avg_frozen": statistics.mean(x["frozen"] for x in runs),
        "avg_exact_memory": statistics.mean(x["exact_memory"] for x in runs),
        "advantage_vs_singleton": adv_single,
        "advantage_vs_memory": adv_memory,
        "passed": n_success >= 18 and adv_memory >= .20 and adv_single >= .15,
        "per_seed": runs,
    }


def main() -> None:
    result = run_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit("E06 preregistered gate NOT met")


if __name__ == "__main__":
    main()
