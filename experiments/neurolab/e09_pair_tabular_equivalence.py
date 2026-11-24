"""E09.05-TAB1: independent exact comparator for the restricted E06 domain.

PRE-REGISTRATION: docs/neurolab/E09_05_TAB1_EQUIVALENCIA_PRE_REGISTRO.md
No new neural rules, seeds, C1 changes or privileged evaluator labels.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import random

from .concepts import ConceptLearner, ConceptWeights
from .e06_protocol import PATTERNS, TARGET, encode, sequence


@dataclass(frozen=True)
class PairTableState:
    weights: tuple[tuple[int, int], ...]
    trials: int = 0


@dataclass(frozen=True)
class PairTableDecision:
    row: int
    scores: tuple[int, int]
    action: str
    trial: int


class IndependentPairTable:
    """Same observed *pair*, not full 5-bit memorization or future target."""

    def __init__(self, seed: int, rate: int = 16) -> None:
        if type(seed) is not int or seed < 0 or rate != 16:
            raise ValueError("contract: positive seed and fixed rate 16")
        rng = random.Random(seed)
        self.initial_state = PairTableState(tuple(
            (rng.randint(40, 220), rng.randint(40, 220))
            for _ in range(4)
        ))
        self.rate = rate

    @staticmethod
    def _row(bits: tuple[int, ...]) -> int:
        if not isinstance(bits, tuple) or len(bits) != 5 or any(
            type(b) is not int or b not in (0, 1) for b in bits
        ):
            raise ValueError("five binary inputs required")
        # The E06 domain: exactly one A feature, one B feature.
        if bits[0] + bits[1] != 1 or bits[2] + bits[3] != 1:
            raise ValueError("outside E06 paired-input domain")
        # Independent tabular feature extractor: C (bits[4]) is irrelevant.
        return (0 if bits[0] else 2) + (0 if bits[2] else 1)

    def respond(self, state: PairTableState, bits: tuple[int, ...]) -> PairTableDecision:
        row = self._row(bits)
        scores = state.weights[row]
        action = "D0" if scores[0] >= scores[1] else "D1"
        return PairTableDecision(row, scores, action, state.trials)

    def update(self, state: PairTableState, choice: PairTableDecision,
               reward: int) -> PairTableState:
        if type(reward) is not int or reward not in (-1, +1):
            raise ValueError("reward +/-1 required")
        if choice.trial != state.trials:
            raise ValueError("stale table decision")
        rows = [list(x) for x in state.weights]
        action_col = 0 if choice.action == "D0" else 1
        old = rows[choice.row][action_col]
        rows[choice.row][action_col] = max(0, min(255, old + reward * self.rate))
        return PairTableState(tuple(tuple(x) for x in rows), state.trials + 1)


def check_entire_e06_domain(concept: ConceptLearner, cs: ConceptWeights,
                            table: IndependentPairTable, ts: PairTableState) -> int:
    """All 8 legal 5-bit observations, including nuisance-bit contrast."""
    if cs.edges != ts.weights or cs.trials != ts.trials:
        raise AssertionError("paired state mismatch")
    comparisons = 0
    for pair in PATTERNS:
        for context in (0, 1):
            x = encode(pair, context)
            c = concept.respond(cs, x)
            t = table.respond(ts, x)
            if len(c.active) != 1 or c.active[0] != t.row:
                raise AssertionError("detector mismatch")
            if c.scores != t.scores or c.action != t.action or c.trial != t.trial:
                raise AssertionError("action or score mismatch")
            comparisons += 1
    return comparisons


def run_seed(seed: int) -> dict:
    concept = ConceptLearner(seed, mode="pair", rate=16)
    table = IndependentPairTable(seed, rate=16)
    cs = concept.initial()
    ts = table.initial_state
    comparisons = check_entire_e06_domain(concept, cs, table, ts)
    updates = 0
    holdout_comparisons = 0

    # Original E06 training: exactly 4*30=120 events and same targets as source.
    for pair in sequence(seed, context=0, repetitions=30, salt=6000):
        x = encode(pair, 0)
        c = concept.respond(cs, x)
        t = table.respond(ts, x)
        if c.action != t.action or c.scores != t.scores:
            raise AssertionError("training decision mismatch")
        reward = +1 if c.action == TARGET[pair] else -1
        cs = concept.update(cs, c, reward)
        ts = table.update(ts, t, reward)
        updates += 1
        comparisons += check_entire_e06_domain(concept, cs, table, ts)

    # Original E06 holdout: 4*20=80 events, no rewards and no state changes.
    for pair in sequence(seed, context=1, repetitions=20, salt=7000):
        x = encode(pair, 1)
        c = concept.respond(cs, x)
        t = table.respond(ts, x)
        if c.action != t.action or c.scores != t.scores:
            raise AssertionError("holdout mismatch")
        holdout_comparisons += 1

    # Additional diagnostic using the same development seed: inverse target,
    # 120 online steps without state reset, nuisance context alternates.
    for k, pair in enumerate(sequence(seed, context=0, repetitions=30, salt=8100)):
        x = encode(pair, k % 2)
        c = concept.respond(cs, x)
        t = table.respond(ts, x)
        if c.action != t.action or c.scores != t.scores:
            raise AssertionError("reversal decision mismatch")
        reversed_target = "D1" if TARGET[pair] == "D0" else "D0"
        reward = +1 if c.action == reversed_target else -1
        cs = concept.update(cs, c, reward)
        ts = table.update(ts, t, reward)
        updates += 1
        comparisons += check_entire_e06_domain(concept, cs, table, ts)

    comparisons += check_entire_e06_domain(concept, cs, table, ts)
    if cs.edges != ts.weights or cs.trials != ts.trials:
        raise AssertionError("final-state mismatch")
    return {
        "seed": seed,
        "equal": True,
        "domain_comparisons": comparisons,
        "original_holdout_comparisons": holdout_comparisons,
        "learning_updates": updates,
        "final_trials": cs.trials,
        "final_weights": [list(row) for row in cs.edges],
    }


def run_all() -> dict:
    rows = [run_seed(seed) for seed in range(20)]
    return {
        "protocol": "E09.05-TAB1-v1",
        "scope": "exact E06 legal pairs; fixed features, same parameter/update rule",
        "source": "E09_05_TAB1_EQUIVALENCIA_PRE_REGISTRO.md",
        "seeds": list(range(20)),
        "n_seeds": len(rows),
        "all_equal": all(r["equal"] for r in rows),
        "domain_comparisons": sum(r["domain_comparisons"] for r in rows),
        "original_holdout_comparisons": sum(r["original_holdout_comparisons"] for r in rows),
        "learning_updates": sum(r["learning_updates"] for r in rows),
        "discrepancies": 0,
        "per_seed": rows,
        "out_of_domain": "excluded by contract, not proven equivalent",
        "historical_fidelity": False,
        "confirmatory_cohort_used": False,
    }


def main() -> None:
    d = run_all()
    if not d["all_equal"] or d["discrepancies"]:
        raise SystemExit("E09.05-TAB1 exact identity FAILED")
    print(json.dumps(d, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
