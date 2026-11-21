"""E09.02g.7: observational, tick-level causal provenance ledger.

Pre-registration: docs/neurolab/E09_02G_07_CREDITO_CAUSAL_PRE_REGISTRO.md
No modification to C1ContextBrain or the original E09g5 experiment.
This measures misalignment, not proof of erroneous reward attribution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .c1_context_brain import C1ContextBrain, ContextBrainState
from .e09_context_protocol import (
    BLOCK_TICKS, TRAIN_BLOCKS, ZERO, REWARD, PUNISHMENT,
    MAPPING_A, MAPPING_B, blocks, train_brain,
)


def source_of(concepts: tuple[int, int]) -> int | None:
    active = [i for i, v in enumerate(concepts) if v > 0]
    return active[0] if len(active) == 1 else None


def ledger_train(
    brain: C1ContextBrain, state: ContextBrainState,
    pending: tuple[int, int, int, int],
    previous: dict | None, schedule: tuple[int, ...],
    mapping: tuple[str, str], phase: str,
) -> tuple[ContextBrainState, tuple[int, int, int, int], dict | None, list[dict]]:
    records: list[dict] = []
    for block_index, context in enumerate(schedule):
        if block_index == 0:
            boundary = "initial"
        else:
            boundary = "switch" if schedule[block_index-1] != context else "repeated"
        for position in range(BLOCK_TICKS):
            before = state
            old_pulse = pending
            tr = brain.step(state, context, pending, learn=True)
            sent = source_of(tr.old_concepts)
            acted = None if previous is None else previous["decision_source"]
            attributable = old_pulse != ZERO and sent is not None and acted is not None
            mismatch = (sent != acted) if attributable else None
            changed = []
            for i, (a, b) in enumerate(zip(before.dendrites, tr.after.dendrites)):
                stw = b.dendrite.stw - a.dendrite.stw
                ltw = b.dendrite.ltw - a.dendrite.ltw
                if stw or ltw:
                    changed.append([i, stw, ltw])
            record = {
                "phase": phase,
                "block": block_index,
                "position": position,
                "boundary": boundary,
                "sensory_context": context,
                "previous_action": previous["action"] if previous else None,
                "previous_action_sensory": previous["sensory_context"] if previous else None,
                "previous_action_decision_source": acted,
                "plasticity_source": sent,
                "pulse": "reward" if old_pulse == REWARD else
                         "punishment" if old_pulse == PUNISHMENT else "zero",
                "comparable": attributable,
                "source_mismatch": mismatch,
                "stw_ltw_changes": changed,
            }
            records.append(record)
            if tr.action is None:
                pending = ZERO
            else:
                pending = REWARD if tr.action == mapping[context] else PUNISHMENT
            previous = {
                "action": tr.action,
                "sensory_context": context,
                "decision_source": sent,
            }
            state = tr.after
    return state, pending, previous, records


def run_seed(seed: int) -> dict:
    brain = C1ContextBrain(seed)
    schedule_a = blocks(seed, 10000, TRAIN_BLOCKS)
    schedule_b = blocks(seed, 20000, TRAIN_BLOCKS)
    observed_state = brain.initial()
    reference_state = brain.initial()
    observed_pulse = reference_pulse = ZERO
    previous = None
    rows = {}
    for phase, schedule, mapping in (
        ("first", schedule_a, MAPPING_A),
        ("reversed", schedule_b, MAPPING_B),
    ):
        observed_state, observed_pulse, previous, rows[phase] = ledger_train(
            brain, observed_state, observed_pulse, previous,
            schedule, mapping, phase,
        )
        reference_state, reference_pulse = train_brain(
            brain, reference_state, reference_pulse, schedule, mapping, learn=True,
        )
        if observed_state != reference_state or observed_pulse != reference_pulse:
            raise AssertionError(f"seed={seed} {phase}: ledger changed E09g5 training")
    return {"seed": seed, "first": rows["first"], "reversed": rows["reversed"]}


def _empty() -> dict:
    return {"ticks": 0, "pulses": 0, "comparable": 0,
            "unknown_source_pulses": 0, "discordant": 0,
            "discordant_with_stw_change": 0, "discordant_with_ltw_change": 0}


def summarize(rows: list[dict]) -> dict:
    result = {}
    for rec in rows:
        phase = rec["phase"]
        boundary = rec["boundary"]
        position = str(rec["position"]) if rec["position"] < 3 else "3plus"
        key = f"{phase}/{boundary}/{position}"
        entry = result.setdefault(key, _empty())
        entry["ticks"] += 1
        if rec["pulse"] == "zero":
            continue
        entry["pulses"] += 1
        if not rec["comparable"]:
            entry["unknown_source_pulses"] += 1
            continue
        entry["comparable"] += 1
        if rec["source_mismatch"]:
            entry["discordant"] += 1
            if any(change[1] != 0 for change in rec["stw_ltw_changes"]):
                entry["discordant_with_stw_change"] += 1
            if any(change[2] != 0 for change in rec["stw_ltw_changes"]):
                entry["discordant_with_ltw_change"] += 1
    return result


def run_all() -> dict:
    seeds = [run_seed(seed) for seed in range(20)]
    events = [event for row in seeds for phase in ("first", "reversed")
              for event in row[phase]]
    summary = summarize(events)
    total = _empty()
    for entry in summary.values():
        for k in total:
            total[k] += entry[k]
    return {
        "protocol": "E09_02G_07_CREDITO_CAUSAL_PRE_REGISTRO-v1",
        "observational": True,
        "n_seeds": 20,
        "n_ticks_per_seed": 2 * TRAIN_BLOCKS * BLOCK_TICKS,
        "total": total,
        "by_phase_boundary_position": summary,
        "per_seed": seeds,
        "warning": "Alignment mismatch is not a proof that a STW change was caused by that pulse.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_all()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "protocol": result["protocol"],
        "n_seeds": result["n_seeds"],
        "total": result["total"],
        "by_phase_boundary_position": result["by_phase_boundary_position"],
        "warning": result["warning"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
