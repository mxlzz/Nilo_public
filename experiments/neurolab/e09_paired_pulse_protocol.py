"""E09.02g.8: paired, externally scheduled omission of chemistry pulses.

Prespecification:
docs/neurolab/E09_02G_08_PULSOS_PAREADOS_PRE_REGISTRO.md.
This is an interventional DIAGNOSTIC, not a new C1 neural rule.
E09g5 source files and thresholds remain unchanged.
"""
from __future__ import annotations

import json
import statistics

from .c1_context_brain import C1ContextBrain, ContextBrainState
from .e09_context_protocol import (
    ZERO, REWARD, PUNISHMENT, TRAIN_BLOCKS, TEST_BLOCKS, BLOCK_TICKS,
    MAPPING_A, MAPPING_B, blocks, train_brain, evaluate_brain,
)

MODES = ("C", "G", "S")
TARGET_MEAN_FIRST = 0.9671875
TARGET_MEAN_REVERSED = 0.9302083333333333


def train_variant(
    brain: C1ContextBrain,
    state: ContextBrainState,
    pending: tuple[int, int, int, int],
    previous_context: int | None,
    schedule: tuple[int, ...],
    mapping: tuple[str, str],
    *,
    mode: str,
) -> tuple[ContextBrainState, tuple[int, int, int, int], int | None, dict]:
    if mode not in MODES:
        raise ValueError("mode debe ser C, G o S")
    scheduled = 0
    effective = 0
    for context in schedule:
        changed = previous_context is not None and context != previous_context
        for pos in range(BLOCK_TICKS):
            suppress = changed and ((mode == "G" and pos == 1)
                                    or (mode == "S" and pos == 2))
            pulse = ZERO if suppress else pending
            if suppress:
                scheduled += 1
                effective += int(pending != ZERO)
            tr = brain.step(state, context, pulse, learn=True)
            if tr.action is None:
                pending = ZERO
            else:
                pending = REWARD if tr.action == mapping[context] else PUNISHMENT
            state = tr.after
        previous_context = context
    return state, pending, previous_context, {
        "scheduled_omissions": scheduled,
        "nonzero_omissions": effective,
    }


def run_seed(seed: int) -> dict:
    brains = {mode: C1ContextBrain(seed) for mode in MODES}
    states = {mode: brains[mode].initial() for mode in MODES}
    pending = {mode: ZERO for mode in MODES}
    last_context = {mode: None for mode in MODES}
    records = {}
    for phase, salt, holdout_salt, mapping in (
        ("first", 10000, 30000, MAPPING_A),
        ("reversed", 20000, 40000, MAPPING_B),
    ):
        sequence = blocks(seed, salt, TRAIN_BLOCKS)
        holdout = blocks(seed, holdout_salt, TEST_BLOCKS)
        records[phase] = {}
        for mode in MODES:
            current, pulse, last, suppressed = train_variant(
                brains[mode], states[mode], pending[mode],
                last_context[mode], sequence, mapping, mode=mode,
            )
            states[mode] = current
            pending[mode] = pulse
            last_context[mode] = last
            metrics = evaluate_brain(brains[mode], current, holdout, mapping)
            records[phase][mode] = {**metrics, **suppressed}
        # The original E09g5 training function is an independent
        # oracle for the unmodified control (including carried pulse).
        # Per-seed state equality is asserted in the separate tests.
    return {"seed": seed, **records}


def run_all() -> dict:
    rows = [run_seed(seed) for seed in range(20)]
    means = {}
    gates = {}
    deltas = {}
    counts = {}
    for phase in ("first", "reversed"):
        means[phase] = {mode: {
            metric: statistics.mean(row[phase][mode][metric] for row in rows)
            for metric in ("steady", "early", "overall")
        } for mode in MODES}
        counts[phase] = {mode: {
            k: sum(row[phase][mode][k] for row in rows)
            for k in ("scheduled_omissions", "nonzero_omissions")
        } for mode in MODES}
        deltas[phase] = {
            "G_minus_C": [r[phase]["G"]["steady"] - r[phase]["C"]["steady"] for r in rows],
            "S_minus_C": [r[phase]["S"]["steady"] - r[phase]["C"]["steady"] for r in rows],
            "G_minus_S": [r[phase]["G"]["steady"] - r[phase]["S"]["steady"] for r in rows],
        }
    for mode in MODES:
        gates[mode] = sum(
            r["first"][mode]["steady"] >= .90
            and r["reversed"][mode]["steady"] >= .90 for r in rows
        )
    if (gates["C"] != 12
        or abs(means["first"]["C"]["steady"] - TARGET_MEAN_FIRST) > 1e-12
        or abs(means["reversed"]["C"]["steady"] - TARGET_MEAN_REVERSED) > 1e-12):
        raise AssertionError("control diverged from the frozen E09g5 baseline")
    for phase in ("first", "reversed"):
        for k in ("scheduled_omissions", "nonzero_omissions"):
            if counts[phase]["G"][k] != counts[phase]["S"][k]:
                raise AssertionError("unequal pulse omissions G/S")
    delta_b = statistics.mean(deltas["reversed"]["G_minus_S"])
    delta_a = statistics.mean(deltas["first"]["G_minus_S"])
    return {
        "protocol": "E09_02G_08_PULSOS_PAREADOS_PRE_REGISTRO-v1",
        "n_seeds": 20,
        "means": means,
        "g5_like_joint_steady_ge_0_90": gates,
        "suppression_counts": counts,
        "paired_steady_deltas": deltas,
        "primary_practical_indicator": {
            "B_G_minus_S": delta_b,
            "A_G_minus_S": delta_a,
            "criterion": "B >= +0.03 and A >= -0.02",
            "met": delta_b >= .03 and delta_a >= -.02,
        },
        "per_seed": rows,
        "limitations": "G/S externally know context transitions; not autonomous causal memory",
    }


def main() -> None:
    print(json.dumps(run_all(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
