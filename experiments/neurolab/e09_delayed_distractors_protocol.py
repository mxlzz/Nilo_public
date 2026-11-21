"""E09.02g.10b — delayed single-reward attribution with distractors.

PRE-REGISTERED: docs/neurolab/E09_02G_10B_DEMORA_DISTRACTORES_PRE_REGISTRO.md
No changes to C1ContextBrain, C1 rules, IG or existing tests.
"""
from __future__ import annotations

import json
import random
import statistics

from .c1_context_brain import C1ContextBrain, ContextBrainState
from .e09_context_protocol import (
    ZERO, REWARD, PUNISHMENT, MAPPING_A, MAPPING_B, tabular_step_choice,
)
from .e09_intrinsic_gate import InternalCreditState, step_intrinsic

SEEDS = tuple(range(120, 160))
MODES = ("C", "IG", "F", "Q")
TRAIN_REPEATS = 10
HOLDOUT_REPEATS = 6
TARGET_TICKS = 4
DELAYS = (1, 2, 3)


def trials(seed: int, salt: int, repeats: int) -> tuple[tuple[int, int], ...]:
    if type(repeats) is not int or repeats <= 0:
        raise ValueError("repeats must be a positive integer")
    seq = [(c, d) for c in (0, 1) for d in DELAYS for _ in range(repeats)]
    random.Random(seed + salt).shuffle(seq)
    return tuple(seq)


def _step(
    brain: C1ContextBrain,
    state: ContextBrainState | InternalCreditState,
    mode: str,
    context: int,
    pulse: tuple[int, int, int, int],
    *,
    learn: bool,
) -> tuple[ContextBrainState | InternalCreditState, str | None, bool]:
    if mode == "IG":
        if not isinstance(state, InternalCreditState):
            raise TypeError("IG requires InternalCreditState")
        if learn:
            result = step_intrinsic(brain, state, context, pulse)
            return result.after, result.neural.action, result.suppressed
        trace = brain.step(state.brain, context, ZERO, learn=False)
        return InternalCreditState(
            trace.after, trace.old_concepts if trace.action is not None else None,
        ), trace.action, False
    if mode not in ("C", "F") or not isinstance(state, ContextBrainState):
        raise ValueError("invalid neural arm")
    trace = brain.step(state, context, pulse if learn else ZERO,
                       learn=learn and mode == "C")
    return trace.after, trace.action, False


def neural_phase(
    brain: C1ContextBrain,
    state: ContextBrainState | InternalCreditState,
    seq: tuple[tuple[int, int], ...],
    mapping: tuple[str, str],
    mode: str,
    *,
    learn: bool,
) -> tuple[ContextBrainState | InternalCreditState, dict]:
    """One scored target decision, distractor run, then one reward arrival.

    The evaluator sees mapping only AFTER the scored choice. The neural brain
    never receives reward provenance, target label, or trial boundaries.
    """
    correct = {d: 0 for d in DELAYS}
    counts = {d: 0 for d in DELAYS}
    by_context = [0, 0]
    by_context_counts = [0, 0]
    sent = suppressed = missing_actions = 0
    total_ticks = 0
    for target, delay in seq:
        distractor = 1 - target
        action = None
        for _ in range(TARGET_TICKS):
            state, action, _ = _step(brain, state, mode, target, ZERO, learn=learn)
            total_ticks += 1
        ok = int(action == mapping[target])
        correct[delay] += ok
        counts[delay] += 1
        by_context[target] += ok
        by_context_counts[target] += 1
        missing_actions += int(action is None)
        for _ in range(delay):
            state, _, _ = _step(brain, state, mode, distractor, ZERO, learn=learn)
            total_ticks += 1
        pulse = ZERO if action is None else (REWARD if ok else PUNISHMENT)
        if learn and pulse != ZERO:
            sent += 1
        state, _, filtered = _step(
            brain, state, mode, distractor, pulse if learn else ZERO, learn=learn,
        )
        suppressed += int(filtered)
        total_ticks += 1
    if mode == "F" and learn:
        raise AssertionError("F always uses frozen synapses; learn flag is only environment signal")
    return state, {
        "overall": sum(correct.values()) / len(seq),
        "by_delay": {str(d): correct[d] / counts[d] for d in DELAYS},
        "by_context": [by_context[c] / by_context_counts[c] for c in (0, 1)],
        "target_choices": len(seq),
        "target_missing": missing_actions,
        "delivered_nonzero_pulses": sent if learn else 0,
        "suppressed_nonzero_pulses": suppressed if learn else 0,
        "neural_ticks": total_ticks,
    }


def train_tabular_q(
    q: list[list[float]], seq: tuple[tuple[int, int], ...],
    mapping: tuple[str, str], *, seed: int, choice_tick: int,
) -> tuple[list[list[float]], int, dict]:
    updates = 0
    causal_provenance = []
    elapsed = 0
    delivery_ticks = []
    for target, delay in seq:
        # Four target ticks precede the scored choice. The Q policy acts
        # only once and does not process intervening sensory stimuli.
        elapsed += TARGET_TICKS
        action_at = elapsed
        choice_tick += 1
        action = tabular_step_choice(q, target, seed=seed, tick=choice_tick, explore=True)
        action_index = 0 if action == "D0" else 1
        stored = (target, action_index)
        reward = 1 if action == mapping[target] else -1
        # Hold the causal (context, action) token throughout the distractor
        # interval. Apply learning ONLY at the later feedback-arrival tick.
        elapsed += delay
        elapsed += 1
        received_at = elapsed
        if received_at - action_at != delay + 1:
            raise AssertionError("incorrect Q feedback delay")
        source_target, source_action = stored
        prior = q[source_target][source_action]
        q[source_target][source_action] = prior + .2 * (reward - prior)
        updates += 1
        delivery_ticks.append((action_at, received_at))
        causal_provenance.append((target, delay, source_target, source_action, reward))
    return q, choice_tick, {
        "updates": updates,
        "causal_provenance": causal_provenance,
        "delivery_ticks": delivery_ticks,
        "emulated_ticks": elapsed,
    }


def holdout_tabular_q(
    q: list[list[float]], seq: tuple[tuple[int, int], ...],
    mapping: tuple[str, str], *, seed: int, choice_tick: int,
) -> dict:
    scores = {d: 0 for d in DELAYS}
    counts = {d: 0 for d in DELAYS}
    by_context = [0, 0]
    for target, delay in seq:
        choice_tick += 1
        action = tabular_step_choice(q, target, seed=seed, tick=choice_tick, explore=False)
        ok = int(action == mapping[target])
        scores[delay] += ok
        counts[delay] += 1
        by_context[target] += ok
    return {
        "overall": sum(scores.values()) / len(seq),
        "by_delay": {str(d): scores[d] / counts[d] for d in DELAYS},
        "by_context": [by_context[0] / (len(seq)//2), by_context[1] / (len(seq)//2)],
        "target_choices": len(seq),
        "target_missing": 0,
    }


def run_seed(seed: int) -> dict:
    brains = {mode: C1ContextBrain(seed) for mode in ("C", "IG", "F")}
    states = {
        "C": brains["C"].initial(),
        "IG": InternalCreditState(brains["IG"].initial()),
        "F": brains["F"].initial(),
    }
    frozen_original = states["F"].dendrites
    q = [[0.0, 0.0], [0.0, 0.0]]
    q_choice_tick = 0
    phases: dict = {}
    for phase, train_salt, test_salt, mapping in (
        ("first", 50000, 70000, MAPPING_A),
        ("reversed", 60000, 80000, MAPPING_B),
    ):
        training = trials(seed, train_salt, TRAIN_REPEATS)
        testing = trials(seed, test_salt, HOLDOUT_REPEATS)
        metrics = {}
        training_meta = {}
        for mode in ("C", "IG", "F"):
            current = states[mode]
            current, training_metrics = neural_phase(
                brains[mode], current, training, mapping, mode,
                learn=(mode != "F"),
            )
            states[mode] = current
            if mode == "F" and current.dendrites != frozen_original:
                raise AssertionError("frozen brain dendrites changed")
            _, metrics[mode] = neural_phase(
                brains[mode], current, testing, mapping, mode, learn=False,
            )
            training_meta[mode] = {
                "delivered_nonzero_pulses": training_metrics["delivered_nonzero_pulses"],
                "suppressed_nonzero_pulses": training_metrics["suppressed_nonzero_pulses"],
                "neural_ticks": training_metrics["neural_ticks"],
                "training_target_accuracy": training_metrics["overall"],
            }
        q, q_choice_tick, q_training = train_tabular_q(
            q, training, mapping, seed=seed, choice_tick=q_choice_tick,
        )
        metrics["Q"] = holdout_tabular_q(
            q, testing, mapping, seed=seed, choice_tick=q_choice_tick,
        )
        # Q only receives provenance of scored actions, never a label
        # for the contemporaneous distractor.
        if any(c != source for c, _, source, _, _ in q_training["causal_provenance"]):
            raise AssertionError("tabular reward credited to noncausal context")
        if q_training["updates"] != len(training):
            raise AssertionError("missing tabular causal update")
        training_meta["Q"] = {"updates": q_training["updates"]}
        phases[phase] = {
            "holdout": metrics,
            "training": training_meta,
            "training_trials": len(training),
            "holdout_trials": len(testing),
        }
    if states["F"].dendrites != frozen_original:
        raise AssertionError("frozen synapse invariant broken after reversal")
    return {"seed": seed, **phases}


def run_all() -> dict:
    rows = [run_seed(s) for s in SEEDS]
    mean: dict = {}
    by_delay: dict = {}
    for phase in ("first", "reversed"):
        mean[phase] = {
            mode: statistics.mean(row[phase]["holdout"][mode]["overall"] for row in rows)
            for mode in MODES
        }
        by_delay[phase] = {
            mode: {
                str(d): statistics.mean(
                    row[phase]["holdout"][mode]["by_delay"][str(d)] for row in rows
                ) for d in DELAYS
            } for mode in MODES
        }
    joint = {
        mode: sum(
            row["first"]["holdout"][mode]["overall"] >= .90
            and row["reversed"]["holdout"][mode]["overall"] >= .90
            for row in rows
        ) for mode in MODES
    }
    gates = {
        mode: (
            joint[mode] >= 36
            and mean["first"][mode] >= .85
            and mean["reversed"][mode] >= .85
            and all(by_delay[phase][mode][str(d)] >= .70
                    for phase in ("first", "reversed") for d in DELAYS)
        ) for mode in ("C", "IG")
    }
    difference = statistics.mean(
        row["reversed"]["holdout"]["IG"]["overall"]
        - row["reversed"]["holdout"]["C"]["overall"] for row in rows
    )
    q_minus_best_neural = (
        (mean["first"]["Q"] + mean["reversed"]["Q"]) / 2
        - max(
            (mean["first"][mode] + mean["reversed"][mode]) / 2
            for mode in ("C", "IG")
        )
    )
    return {
        "protocol": "E09_02G_10B_DEMORA_DISTRACTORES_PRE_REGISTRO-v1",
        "seeds": list(SEEDS),
        "n_seeds": len(SEEDS),
        "schedule": "4 target ticks + d opposite-context distractors + 1 reward-arrival distractor tick",
        "mean_holdout_target_accuracy": mean,
        "mean_by_delay": by_delay,
        "joint_ge_0_90": joint,
        "neural_robustness_gates": gates,
        "mean_reversed_IG_minus_C": difference,
        "Q_minus_best_neural_average_both_phases": q_minus_best_neural,
        "stop_ad_hoc_neural_expansion": (
            not any(gates.values()) and q_minus_best_neural >= .15
        ),
        "per_seed": rows,
        "limitations": "Q receives explicit causal provenance; C and IG receive only chemical reward",
    }


def main() -> None:
    print(json.dumps(run_all(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
