"""E09.05-TAB2: exact independent tabular control for original reset E03.

Prerecorded: docs/neurolab/E09_05_TAB2_E03_PRE_REGISTRO.md
Legal observations are ONLY A=(255,0) and B=(0,255), reset every 3 ticks.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import random

from .plasticity import PlasticLearner, PlasticState
from .e03_protocol import ORIGINAL, REVERSED, encode, sequence


@dataclass(frozen=True)
class BinaryTableState:
    weights: tuple[int, int, int, int]
    trials: int = 0


@dataclass(frozen=True)
class BinaryChoice:
    row: int
    scores: tuple[int, int]
    action: str | None
    trial: int


class IndependentBinaryTable:
    """Four adjustable weights, two stimuli and two actions, no evaluator labels."""

    def __init__(self, seed: int, rate: int = 16) -> None:
        if type(seed) is not int or seed < 0 or rate != 16:
            raise ValueError("fixed seed and rate=16 required")
        rng = random.Random(seed)
        self.initial_state = BinaryTableState(tuple(rng.randint(40, 220) for _ in range(4)))
        self.rate = rate

    @staticmethod
    def _row(stimulus: tuple[int, int]) -> int:
        if stimulus == (255, 0):
            return 0
        if stimulus == (0, 255):
            return 1
        raise ValueError("input outside reset E03 legal domain")

    def respond(self, state: BinaryTableState,
                stimulus: tuple[int, int]) -> BinaryChoice:
        row = self._row(stimulus)
        scores = state.weights[2*row], state.weights[2*row+1]
        m = max(scores)
        action = None if m == 0 else ("D0" if scores[0] >= scores[1] else "D1")
        return BinaryChoice(row, scores, action, state.trials)

    def update(self, state: BinaryTableState,
               choice: BinaryChoice, reward: int) -> BinaryTableState:
        if type(reward) is not int or reward not in (-1, +1):
            raise ValueError("reward must be +/-1")
        if choice.trial != state.trials:
            raise ValueError("stale tabular choice")
        weights = list(state.weights)
        if choice.action is not None:
            i = 2*choice.row + (0 if choice.action == "D0" else 1)
            weights[i] = max(0, min(255, weights[i] + reward * self.rate))
        return BinaryTableState(tuple(weights), state.trials+1)


def check_full_legal_domain(learner: PlasticLearner, ls: PlasticState,
                            table: IndependentBinaryTable,
                            ts: BinaryTableState) -> int:
    if ls.weights != ts.weights or ls.trials != ts.trials:
        raise AssertionError("E03 vs table state mismatch")
    for row, stimulus in enumerate(((255, 0), (0, 255))):
        x = learner.respond(ls, stimulus)
        y = table.respond(ts, stimulus)
        cs = tuple(v for _, v in x.scores)
        expected_concept = "C0" if row == 0 else "C1"
        if x.active_concepts != (expected_concept,):
            raise AssertionError("three-tick unit mapping failed")
        if x.action != y.action or cs != y.scores:
            raise AssertionError("E03 vs table decision mismatch")
    return 2


def run_seed(seed: int) -> dict:
    learner = PlasticLearner(seed, rate=16)
    table = IndependentBinaryTable(seed, rate=16)
    ls, ts = learner.initial(), table.initial_state
    comparisons = check_full_legal_domain(learner, ls, table, ts)
    updates = 0
    holdouts = 0

    def verify_holdout(events) -> int:
        n = 0
        for event in events:
            stimulus = encode(event)
            x, y = learner.respond(ls, stimulus), table.respond(ts, stimulus)
            if x.action != y.action or tuple(v for _, v in x.scores) != y.scores:
                raise AssertionError("holdout disagreement")
            n += 1
        return n

    for event in sequence(seed, n_per_class=50, salt=1000):
        stimulus = encode(event)
        x, y = learner.respond(ls, stimulus), table.respond(ts, stimulus)
        if x.action != y.action or tuple(v for _, v in x.scores) != y.scores:
            raise AssertionError("training disagreement")
        reward = +1 if x.action == ORIGINAL[event] else -1
        ls = learner.update(ls, x, reward)
        ts = table.update(ts, y, reward)
        updates += 1
        comparisons += check_full_legal_domain(learner, ls, table, ts)

    holdouts += verify_holdout(sequence(seed, n_per_class=40, salt=2000))

    for event in sequence(seed, n_per_class=80, salt=3000):
        stimulus = encode(event)
        x, y = learner.respond(ls, stimulus), table.respond(ts, stimulus)
        if x.action != y.action or tuple(v for _, v in x.scores) != y.scores:
            raise AssertionError("reversal disagreement")
        reward = +1 if x.action == REVERSED[event] else -1
        ls = learner.update(ls, x, reward)
        ts = table.update(ts, y, reward)
        updates += 1
        comparisons += check_full_legal_domain(learner, ls, table, ts)

    holdouts += verify_holdout(sequence(seed, n_per_class=40, salt=4000))
    comparisons += check_full_legal_domain(learner, ls, table, ts)
    if ls.weights != ts.weights or ls.trials != ts.trials:
        raise AssertionError("final state difference")

    return {
        "seed": seed,
        "equal": True,
        "exhaustive_two_input_comparisons": comparisons,
        "original_holdout_comparisons": holdouts,
        "online_updates": updates,
        "final_trials": ls.trials,
        "final_weights": list(ls.weights),
    }


def run_all() -> dict:
    rows = [run_seed(i) for i in range(20)]
    return {
        "protocol": "E09.05-TAB2-v1",
        "scope": "original E03 exact 255/0 inputs, reset 3-tick brain only",
        "source": "E09_05_TAB2_E03_PRE_REGISTRO.md",
        "seeds": list(range(20)),
        "n_seeds": len(rows),
        "all_equal": all(r["equal"] for r in rows),
        "two_input_comparisons": sum(r["exhaustive_two_input_comparisons"] for r in rows),
        "holdout_comparisons": sum(r["original_holdout_comparisons"] for r in rows),
        "online_updates": sum(r["online_updates"] for r in rows),
        "discrepancies": 0,
        "per_seed": rows,
        "outside_exact_original_protocol": "not tested nor claimed",
        "confirmatory_cohort_used": False,
    }


def main() -> None:
    d = run_all()
    if not d["all_equal"] or d["discrepancies"]:
        raise SystemExit("E09 TAB2 identity FAILED")
    print(json.dumps(d, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
