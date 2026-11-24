"""E09.02g.6: preregistered 2x2 holdout-only interventions.

See docs/neurolab/E09_02G_06_ABLACIONES_TEMPORALES_PRE_REGISTRO.md.
The original E09g.5 training and C1ContextBrain are untouched.
These manipulations are artificial diagnostic oracles, NOT C1 emulation,
new learning capabilities or repairs to the failed E09g.5 gate.
"""
from __future__ import annotations

from dataclasses import replace
import json
import statistics

from .c1_context_brain import C1ContextBrain, ContextBrainState
from .e09_context_protocol import (
    BLOCK_TICKS, TRAIN_BLOCKS, TEST_BLOCKS, ZERO,
    MAPPING_A, MAPPING_B, blocks, train_brain, evaluate_brain,
)

MODES = ("C", "N", "W", "NW")
BASELINE_FAILED = (0, 2, 3, 4, 8, 16, 17, 19)


def _intervene(state: ContextBrainState, context: int, mode: str) -> ContextBrainState:
    if mode not in MODES:
        raise ValueError("invalid intervention mode")
    if mode == "C":
        return state
    adjustments = {}
    if "N" in mode:
        adjustments.update(neuron_states=(80, 80), neuron_outputs=(0, 0))
    if "W" in mode:
        adjustments["concept_outputs"] = (126, 0) if context == 0 else (0, 126)
    modified = replace(state, **adjustments)
    if modified.dendrites != state.dendrites or modified.tick != state.tick:
        raise AssertionError("intervention altered synapses or clock")
    return modified


def evaluate_variant(
    brain: C1ContextBrain,
    state: ContextBrainState,
    schedule: tuple[int, ...],
    mapping: tuple[str, str],
    mode: str,
) -> dict:
    if mode not in MODES:
        raise ValueError("invalid mode")
    current = state
    positions = [0] * BLOCK_TICKS
    correct_by_position = [0] * BLOCK_TICKS
    by_context = [0, 0]
    correct_by_context = [0, 0]
    for context in schedule:
        current = _intervene(current, context, mode)
        for position in range(BLOCK_TICKS):
            tr = brain.step(current, context, ZERO, learn=False)
            current = tr.after
            ok = int(tr.action == mapping[context])
            positions[position] += 1
            correct_by_position[position] += ok
            by_context[context] += 1
            correct_by_context[context] += ok
    n = len(schedule)
    accuracy = [correct_by_position[i] / positions[i] for i in range(BLOCK_TICKS)]
    return {
        "overall": sum(correct_by_position) / (n * BLOCK_TICKS),
        "early": sum(correct_by_position[:2]) / (2 * n),
        "steady": sum(correct_by_position[2:]) / (6 * n),
        "by_position": accuracy,
        "by_context": [correct_by_context[i] / by_context[i] for i in (0, 1)],
    }


def run_seed(seed: int) -> dict:
    brain = C1ContextBrain(seed)
    sa = blocks(seed, 10000, TRAIN_BLOCKS)
    sb = blocks(seed, 20000, TRAIN_BLOCKS)
    ha = blocks(seed, 30000, TEST_BLOCKS)
    hb = blocks(seed, 40000, TEST_BLOCKS)

    state, pending = train_brain(brain, brain.initial(), ZERO, sa, MAPPING_A, learn=True)
    first = {mode: evaluate_variant(brain, state, ha, MAPPING_A, mode) for mode in MODES}
    expected_a = evaluate_brain(brain, state, ha, MAPPING_A)
    if any(abs(first["C"][k] - expected_a[k]) > 1e-12
           for k in ("steady", "early", "overall")):
        raise AssertionError("control C diverged from the frozen E09g.5 phase A")

    state, pending = train_brain(brain, state, pending, sb, MAPPING_B, learn=True)
    second = {mode: evaluate_variant(brain, state, hb, MAPPING_B, mode) for mode in MODES}
    expected_b = evaluate_brain(brain, state, hb, MAPPING_B)
    if any(abs(second["C"][k] - expected_b[k]) > 1e-12
           for k in ("steady", "early", "overall")):
        raise AssertionError("control C diverged from the frozen E09g.5 phase B")

    return {
        "seed": seed,
        "original_joint_pass": first["C"]["steady"] >= .90 and second["C"]["steady"] >= .90,
        "first": first,
        "reversed": second,
    }


def run_all() -> dict:
    rows = [run_seed(seed) for seed in range(20)]
    gate_count = sum(x["original_joint_pass"] for x in rows)
    failed = tuple(x["seed"] for x in rows if not x["original_joint_pass"])
    if gate_count != 12 or failed != BASELINE_FAILED:
        raise AssertionError("E09g.5 failure set not reproduced; g6 analysis invalid")
    means = {}
    contrasts = {}
    for phase in ("first", "reversed"):
        means[phase] = {}
        contrasts[phase] = {}
        for mode in MODES:
            means[phase][mode] = {
                metric: statistics.mean(row[phase][mode][metric] for row in rows)
                for metric in ("overall", "early", "steady")
            }
            means[phase][mode]["by_position"] = [
                statistics.mean(row[phase][mode]["by_position"][pos] for row in rows)
                for pos in range(BLOCK_TICKS)
            ]
            if mode == "C":
                continue
            delta = lambda r: r[phase][mode]["steady"] - r[phase]["C"]["steady"]
            contrasts[phase][mode] = {
                "mean_delta_steady": statistics.mean(delta(r) for r in rows),
                "delta_steady_by_seed": [delta(r) for r in rows],
                "original_failed_seeds_with_gain_ge_0_10": [
                    r["seed"] for r in rows if r["seed"] in BASELINE_FAILED
                    and delta(r) >= 0.10
                ],
            }
    return {
        "protocol": "E09_02G_06_ABLACIONES_TEMPORALES_PRE_REGISTRO-v1",
        "scope": "holdout-only artificial interventions; does not fix g5 or G05",
        "n_seeds": len(rows),
        "original_g5_good_both": gate_count,
        "original_g5_failing_seeds": list(failed),
        "mean": means,
        "paired_contrasts": contrasts,
        "per_seed": rows,
    }


def main() -> None:
    print(json.dumps(run_all(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
