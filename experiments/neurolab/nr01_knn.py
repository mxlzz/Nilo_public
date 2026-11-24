"""NR01.03-C: bounded raw-observation 1-NN baseline, no external labels.

Canonical spec: docs/neurolab/NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md
This file does not import the generator, evaluator, ART or KMeans.
Scientific development and confirmation cohorts are NOT run here.
"""
from __future__ import annotations

import json
import math

_ACTIONS = ("D0", "D1")


def _vector(x):
    if type(x) is not tuple or len(x) != 16:
        raise ValueError("expected tuple of 16 observed scalar features")
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
           for v in x):
        raise ValueError("observations must be finite [0,1] reals")
    return tuple(float(v) for v in x)


class CaseMemory16:
    """One nearest neighbour, capacity 16, oldest wins exact-distance ties.

    A case is learned *only* from the action and its subsequent ±1 reward.
    Test calls choose() never mutate memory; no hidden latent feature is stored.
    """

    CAPACITY = 16

    def __init__(self):
        self.cases = []  # insertion order: oldest first; (16D tuple, action)

    def choose(self, x):
        observed = _vector(x)
        if not self.cases:
            return "D0"
        # min(key=...) keeps the earliest case on equal distance. Do NOT
        # compare (distance, action) tuples: that would break the tie rule.
        _prior, action = min(
            self.cases,
            key=lambda case: math.fsum(
                (a - b) ** 2 for a, b in zip(observed, case[0])
            ),
        )
        return action

    def apply_reward(self, x, chosen_action, reward):
        observed = _vector(x)
        if chosen_action not in _ACTIONS or type(reward) is not int or reward not in (-1, 1):
            raise ValueError("invalid action or feedback")
        if chosen_action != self.choose(observed):
            raise ValueError("feedback action inconsistent with current choice")
        correct = chosen_action if reward == 1 else (
            "D1" if chosen_action == "D0" else "D0"
        )
        self.cases.append((observed, correct))
        if len(self.cases) > self.CAPACITY:
            self.cases.pop(0)

    def snapshot(self):
        return json.dumps(
            {"schema": "nr01-1nn16-v1",
             "capacity": self.CAPACITY,
             "cases": self.cases},
            allow_nan=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    @classmethod
    def restore(cls, data):
        record = json.loads(data)
        if type(record) is not dict or set(record) != {"schema", "capacity", "cases"}:
            raise ValueError("invalid snapshot structure")
        if record["schema"] != "nr01-1nn16-v1" or record["capacity"] != cls.CAPACITY:
            raise ValueError("invalid snapshot version or capacity")
        if type(record["cases"]) is not list or len(record["cases"]) > cls.CAPACITY:
            raise ValueError("invalid case count")
        model = cls()
        for case in record["cases"]:
            if type(case) is not list or len(case) != 2 or case[1] not in _ACTIONS:
                raise ValueError("invalid stored case")
            if type(case[0]) is not list:
                raise ValueError("invalid observation record")
            model.cases.append((_vector(tuple(case[0])), case[1]))
        return model
