"""I3c.5b: read-only audit of strength=0 in NeuroLab, NOT a C1 history proof.

Preregistered at docs/neurolab/E09_02I_I3C5B_STRENGTH0_PRE_REGISTRO.md.
Does not modify class_signal, synapse, migration or winner-takes-all.
Original Creatures.exe is not bundled; historical gate cannot close here.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from .c1_dendrite_tick import DendriteState
from .c1_synapse_integrated import (
    C1SynapseState, C1SynapticInput, DECISION_EXCITATORY_GENE,
    update_c1_synapse,
)
from .e09_i3c3_dynamic_context import (
    DynamicContextBrain, class_signal,
)

WIRES = (0x1000, 0x2000, 0x2000, 0x1000)
EXE_SHA256 = "548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7"


def audit():
    brain = DynamicContextBrain(1500, migration_enabled=False)
    base = brain.initial(wiring=WIRES)
    active_syn = C1SynapseState(
        DendriteState(susceptibility=0, stw=255, ltw=0), 0,
    )
    empty_syn = C1SynapseState(DendriteState(), 0)
    active = replace(
        base, links=(
            replace(base.links[0], synapse=active_syn),
            *base.links[1:],
        ), concept_outputs=(255, 0),
    )
    empty = replace(
        active, links=(
            replace(active.links[0], synapse=empty_syn),
            *active.links[1:],
        ),
    )
    signal_on = class_signal(active.concept_outputs, active.links[0])
    signal_zero = class_signal(empty.concept_outputs, empty.links[0])
    tick_on = brain.step(active, 0, (0, 0, 0, 0), learn=False)
    tick_zero = brain.step(empty, 0, (0, 0, 0, 0), learn=False)
    if tick_on.after.links != active.links or tick_zero.after.links != empty.links:
        raise AssertionError("read-only observation updated synapses")
    if tick_on.class_signals[0] != signal_on or tick_zero.class_signals[0] != signal_zero:
        raise AssertionError("class_signal does not match actual WTA input")
    if active.links[0].synapse.strength != 0:
        raise AssertionError("test fixture is not exhausted")

    exhausted = C1SynapseState(
        DendriteState(susceptibility=255, stw=0, ltw=0), 0,
    )
    transition = update_c1_synapse(
        exhausted, DECISION_EXCITATORY_GENE,
        C1SynapticInput(
            source_output=255,
            owner_state=200,
            owner_output=255,
            chemicals=(255, 0, 0, 0),
        ), tick=1,
    )
    return {
        "protocol": "NL-EXP-I3c5b-v1",
        "model": "NeuroLab N-line; no original C1 EXE in CI",
        "source_exe_sha256_from_prior_static_report": EXE_SHA256,
        "source_pointer": WIRES[0],
        "input_context_output": 255,
        "strength_before_signal": 0,
        "stw_before_signal": 255,
        "signal_at_strength0_with_stw255": signal_on,
        "signal_at_strength0_with_stw0": signal_zero,
        "class_signal_propagates_to_WTA_input": (
            tick_on.class_signals[0] == signal_on
        ),
        "model_strength0_transmits_signal": signal_on > signal_zero,
        "decision_score_strength0_stw255": tick_on.scores[0],
        "decision_score_strength0_stw0": tick_zero.scores[0],
        "numerical_synapse_strength_before": exhausted.strength,
        "numerical_synapse_strength_after_tick1": transition.after.strength,
        "numerical_synapse_stw_before": exhausted.dendrite.stw,
        "numerical_synapse_stw_after_tick1": transition.after.dendrite.stw,
        "numeric_reinforcement_effect_tick1": transition.numeric.reinforcement_effect,
        "numerical_weight_changed_while_exhausted": (
            transition.after.strength == 0 and
            transition.after.dendrite.stw != exhausted.dendrite.stw
        ),
        "historical_strength0_input_gate": "NOT VERIFIED — requires original EXE loop audit",
        "G05_G09_G00H": "OPEN",
        "limitations": (
            "Shows Python reduction behavior only. No claim about x86 loop when "
            "source strength=0, candidate migration, or whole-game behavior."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = audit()
    blob = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(blob, encoding="utf-8")
    print(blob, end="")


if __name__ == "__main__":
    main()
