"""I3c.5e: fixed numeric oracles explaining I3c.5d zero behavioral delta.

PREREGISTRATION: docs/neurolab/E09_02I_I3C5E_PUERTA_SENAL_PRE_REGISTRO.md.
Post hoc numeric read-only study. No changes to model, gene, feedback or samples.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from .c1_runtime_math import dendrite_signal
from .c1_dendrite_tick import DendriteRates, DendriteState, transition
from .c1_strength import StrengthState, update_strength
from .c1_context_brain import C1ContextBrain, ContextBrainState
from .c1_synapse_integrated import C1SynapseState

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT / "docs/neurolab/resultados/e09i3c5d_resumen_y_hashes.json"
ORIGINAL_JSON_SHA="b6a97ae5ae765d55330b122050c60b29ffcb9eb95080efa5af5ed5df37658192"
STW_RATE=80
LTW_RATE=128
STRENGTH_GAIN_RATE=3
STRENGTH_LOSE_RATE=5


def reference_fixture():
    record=json.loads(FIXTURE.read_text(encoding="utf-8"))
    if (record["protocol"]!="NL-EXP-I3c5d-v1"
            or record["original_full_json_sha256"]!=ORIGINAL_JSON_SHA
            or record["n_seeds"]!=20
            or record["n_mapping_coordinates"]!=80
            or record["n_branches"]!=240
            or set(record["per_seed_sha256"])!={str(i) for i in range(1300,1320)}
            or any(len(x)!=64 for x in record["per_seed_sha256"].values())):
        raise AssertionError("I3c5d evidence fixture not frozen or incomplete")
    if (record["positive_effect_cases"]!={"N":0,"D0":16,"D3":48}
            or record["effect_by_source"]["D0"]!={"target":16,"distractor":0}
            or record["effect_by_source"]["D3"]!={"target":16,"distractor":44}
            or record["max_effect_per_synapse_per_tick"]!=1
            or record["readout_action_changes_vs_N"]!={
                "D0":{"9":0,"16":0,"128":0},
                "D3":{"9":0,"16":0,"128":0},
            }
            or record["max_snapshot_stw_all_branches"]!=0):
        raise AssertionError("original observed mechanics changed")
    return record


def _probe_decision_score(weight,source_output):
    if type(weight) is not int or not 0<=weight<=255:
        raise ValueError("strength weight must be byte")
    brain=C1ContextBrain(1500)
    initial=brain.initial()
    syn=list(initial.dendrites)
    syn[0]=C1SynapseState(DendriteState(stw=weight),2)
    state=ContextBrainState(
        tuple(syn),neuron_states=(80,80),neuron_outputs=(0,0),
        concept_outputs=(source_output,0),tick=4,
    )
    trace=brain.step(state,0,(0,0,0,0),learn=False)
    if trace.after.dendrites!=state.dendrites:
        raise AssertionError("test readout changed neural weights")
    return trace.scores


def evaluate_gate():
    evidence=reference_fixture()
    # Exactly matches the existing one-hot Concept detector in C1ContextBrain:
    # source=255, gene/program weight=128, attenuation=255.
    concept=dendrite_signal((255,), (128,),attenuation=255).and_value
    strength_classes=[
        dendrite_signal((concept,), (stw,), attenuation=128).type_value
        for stw in range(256)
    ]
    minimal=next((w for w,val in enumerate(strength_classes) if val>0),None)
    if minimal is None:
        raise AssertionError("no STW could propagate into Decision")
    if (concept!=126 or minimal!=5
            or any(strength_classes[w]>0 for w in range(minimal))):
        raise AssertionError("input type arithmetic diverged from oracles")
    scores={
        str(weight):_probe_decision_score(weight,concept)
        for weight in (0,1,minimal)
    }
    if scores["0"]!=scores["1"]:
        raise AssertionError("unit STW unexpectedly changed neural scores")
    if scores[str(minimal)][0]<=scores["0"][0]:
        raise AssertionError("the empirically discovered gate did not alter score")

    # A unit effect can exist NUMERICALLY, but relax(rate=80, tick7) can
    # erase it in the SAME tick. Compare tick6 (not a relax mask boundary).
    rate=DendriteRates(48,STW_RATE,LTW_RATE)
    early=transition(
        DendriteState(),rates=rate,tick=7,
        susceptibility_rule_output=255,reinforcement_rule_output=64,
    )
    before_gate=transition(
        DendriteState(),rates=rate,tick=6,
        susceptibility_rule_output=255,reinforcement_rule_output=64,
    )
    if early.reinforcement_effect!=1 or early.stw_after_reinforcement!=1:
        raise AssertionError("artificial one-unit effect not reproduced")
    if early.stw_after_relaxation!=0 or before_gate.stw_after_relaxation!=1:
        raise AssertionError("quantized STW relaxation mismatch")

    # Tick10 loss branch; the same original strength1/STW1 cannot survive
    # if lose-rule positive and no gain. This is a *synthetic isolated oracle*.
    limited=StrengthState(DendriteState(susceptibility=4,stw=1,ltw=0),1)
    loss_tick=update_strength(
        limited,tick=10,gain_rate=STRENGTH_GAIN_RATE,
        gain_rule_output=0,lose_rate=STRENGTH_LOSE_RATE,
        lose_rule_output=1,
    )
    control_tick=update_strength(
        limited,tick=9,gain_rate=STRENGTH_GAIN_RATE,
        gain_rule_output=0,lose_rate=STRENGTH_LOSE_RATE,
        lose_rule_output=1,
    )
    if (not loss_tick.lost_connection or loss_tick.after.strength!=0
            or loss_tick.after.dendrite.stw!=0
            or control_tick.lost_connection
            or control_tick.after.dendrite.stw!=1):
        raise AssertionError("original strength loss/reset contract changed")

    return {
        "protocol":"NL-EXP-I3c5e-v1",
        "study_type":"post hoc read-only numeric oracles; not new learning run",
        "original_i3c5d_json_sha256":evidence["original_full_json_sha256"],
        "original_20_seed_hashes_verified":True,
        "original_n_branches":evidence["n_branches"],
        "original_readout_action_changes":evidence["readout_action_changes_vs_N"],
        "original_positive_effect_cases":evidence["positive_effect_cases"],
        "original_positive_effect_ticks":evidence["positive_effect_tick"],
        "original_max_effect_per_synapse_per_tick":evidence[
            "max_effect_per_synapse_per_tick"
        ],
        "concept_source_output":concept,
        "min_positive_decision_class_signal_stw":minimal,
        "signal_for_stw_0":strength_classes[0],
        "signal_for_stw_1":strength_classes[1],
        "signal_for_stw_threshold":strength_classes[minimal],
        "score_fixture_no_learning":scores,
        "synthetic_effect_stw1_tick6":{
            "numeric_effect":before_gate.reinforcement_effect,
            "before_relax":before_gate.stw_after_reinforcement,
            "after_relax":before_gate.stw_after_relaxation,
        },
        "synthetic_effect_stw1_tick7":{
            "numeric_effect":early.reinforcement_effect,
            "before_relax":early.stw_after_reinforcement,
            "after_relax":early.stw_after_relaxation,
        },
        "synthetic_strength1_tick9":{
            "lost_connection":control_tick.lost_connection,
            "strength":control_tick.after.strength,
            "stw":control_tick.after.dendrite.stw,
        },
        "synthetic_strength1_tick10":{
            "lost_connection":loss_tick.lost_connection,
            "strength":loss_tick.after.strength,
            "stw":loss_tick.after.dendrite.stw,
        },
        "interpretation":"Under unchanged N numeric rules, observed unit reinforcement cannot reach Decision class input. Tick7 relax and tick10 disconnection are additional erasure mechanisms consistent with observed I3c5d. Not a new causal learning trial.",
        "G05_G09_G00H":"OPEN",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    data=evaluate_gate()
    blob=json.dumps(data,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(blob,encoding="utf-8")
    print(blob,end="")


if __name__=="__main__":
    main()
