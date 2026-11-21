"""E09g10c: exploratory per-synapse eligibility counterfactual at feedback.

Preregistration: docs/neurolab/E09_02G_10C_SUSCEPTIBILIDAD_PRE_REGISTRO.md.
Replays frozen g10b C schedule; zero-chemical counterfactual is discarded.
Never modifies the neuron, learning rules, schedules or targets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

from .c1_context_brain import C1ContextBrain
from .e09_context_protocol import ZERO, REWARD, PUNISHMENT, MAPPING_A, MAPPING_B
from .e09_delayed_distractors_protocol import (
    SEEDS, TRAIN_REPEATS, TARGET_TICKS, trials, neural_phase,
)


def _syn_index(owner: int, source: int, inhibitory: int) -> int:
    return (owner * 2 + source) * 2 + inhibitory


def _counterfactual_event(
    brain: C1ContextBrain, state, target: int, delay: int,
    selected_action: str | None, pulse,
    *, seed: int, phase: str,
):
    """Two one-tick continuations from SAME state, only chemical differs."""
    before = state
    real = brain.step(before, 1-target, pulse, learn=True)
    no_pulse = brain.step(before, 1-target, ZERO, learn=True)
    event = {
        "seed": seed, "phase": phase,
        "target": target, "delay": delay,
        "chosen_action": selected_action,
        "pulse": "reward" if pulse == REWARD else (
            "punishment" if pulse == PUNISHMENT else "zero"
        ),
    }
    if selected_action is None:
        event.update({"sus_target": None, "sus_distractor": None,
                      "delta_target": None, "delta_distractor": None,
                      "delta_other_owner": None})
        return real.after, event
    owner = 0 if selected_action == "D0" else 1
    cls = 0 if pulse == REWARD else 1
    target_id = _syn_index(owner, target, cls)
    distractor_id = _syn_index(owner, 1-target, cls)
    other_ids = [_syn_index(1-owner, src, cls) for src in (0,1)]
    difference = lambda index: (
        real.after.dendrites[index].dendrite.stw
        - no_pulse.after.dendrites[index].dendrite.stw
    )
    event.update({
        "sus_target": before.dendrites[target_id].dendrite.susceptibility,
        "sus_distractor": before.dendrites[distractor_id].dendrite.susceptibility,
        "delta_target": difference(target_id),
        "delta_distractor": difference(distractor_id),
        "delta_other_owner": sum(difference(i) for i in other_ids),
    })
    return real.after, event


def trace_seed(seed: int) -> dict:
    brain = C1ContextBrain(seed)
    state = brain.initial()
    ref_state = brain.initial()
    events = []
    per_phase_training_accuracy = {}
    for phase, salt, mapping in (
        ("first", 50000, MAPPING_A),
        ("reversed", 60000, MAPPING_B),
    ):
        seq = trials(seed, salt, TRAIN_REPEATS)
        scored_correct = 0
        for target, delay in seq:
            action = None
            for _ in range(TARGET_TICKS):
                step = brain.step(state, target, ZERO, learn=True)
                state, action = step.after, step.action
            scored_correct += int(action == mapping[target])
            for _ in range(delay):
                state = brain.step(state, 1-target, ZERO, learn=True).after
            pulse = ZERO if action is None else (
                REWARD if action == mapping[target] else PUNISHMENT
            )
            state, event = _counterfactual_event(
                brain, state, target, delay, action, pulse,
                seed=seed, phase=phase,
            )
            events.append(event)
        ref_state, reference_metrics = neural_phase(
            brain, ref_state, seq, mapping, "C", learn=True,
        )
        if state != ref_state or reference_metrics["overall"] != scored_correct / len(seq):
            raise AssertionError(f"seed={seed}, phase={phase}: replay differs from g10b C")
        per_phase_training_accuracy[phase] = reference_metrics["overall"]
    return {
        "seed": seed,
        "training_accuracy": per_phase_training_accuracy,
        "events": events,
    }


def _aggregate(rows: list[dict]) -> dict:
    results = {}
    for phase in ("first", "reversed"):
        results[phase] = {}
        for delay in (1,2,3):
            selected = [
                event for row in rows for event in row["events"]
                if event["phase"] == phase and event["delay"] == delay
                and event["pulse"] != "zero"
            ]
            missing = sum(
                1 for row in rows for event in row["events"]
                if event["phase"] == phase and event["delay"] == delay
                and event["pulse"] == "zero"
            )
            if not selected:
                raise AssertionError("no pulses: cannot estimate eligibility")
            n = len(selected)
            results[phase][str(delay)] = {
                "pulses": n, "missing_pulses": missing,
                "mean_sus_target_before": statistics.mean(x["sus_target"] for x in selected),
                "mean_sus_distractor_before": statistics.mean(x["sus_distractor"] for x in selected),
                "fraction_sus_target_positive": sum(x["sus_target"] > 0 for x in selected)/n,
                "fraction_sus_distractor_positive": sum(x["sus_distractor"] > 0 for x in selected)/n,
                "mean_pulse_effect_target_STW": statistics.mean(x["delta_target"] for x in selected),
                "mean_pulse_effect_distractor_STW": statistics.mean(x["delta_distractor"] for x in selected),
                "mean_pulse_effect_other_owner_STW_sum": statistics.mean(x["delta_other_owner"] for x in selected),
                "fraction_target_STW_affected": sum(x["delta_target"] != 0 for x in selected)/n,
                "fraction_distractor_STW_affected": sum(x["delta_distractor"] != 0 for x in selected)/n,
                "fraction_other_owner_STW_affected": sum(x["delta_other_owner"] != 0 for x in selected)/n,
            }
    return results


def run_all() -> dict:
    rows = [trace_seed(seed) for seed in SEEDS]
    events = sum(len(x["events"]) for x in rows)
    if len(rows) != 40 or events != 40 * 2 * 60:
        raise AssertionError("cohort or event count changed")
    aggregate = _aggregate(rows)
    return {
        "protocol": "E09_02G_10C_SUSCEPTIBILIDAD_PRE_REGISTRO-v1",
        "classification": "EXPLORATORY post-hoc mechanism audit, not OOS confirmation",
        "n_seeds": len(rows), "n_events": events,
        "aggregate": aggregate, "per_seed": rows,
        "warning": "One-tick chemical counterfactual does not measure future behavioral causation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_all()
    if args.output is not None:
        args.output.write_text(json.dumps(result, sort_keys=True, separators=(",",":")),
                               encoding="utf-8")
    print(json.dumps({
        "protocol": result["protocol"],
        "classification": result["classification"],
        "n_seeds": result["n_seeds"], "n_events": result["n_events"],
        "aggregate": result["aggregate"],
        "warning": result["warning"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
