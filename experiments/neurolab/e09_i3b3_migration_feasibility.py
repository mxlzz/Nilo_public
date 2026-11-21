"""E09.02i-I3b.3: reuse existing C1 migration to audit 6-node feasibility.

PRE-REGISTERED:
 docs/neurolab/E09_02I_I3B3_MIGRACION_VIABILIDAD_PRE_REGISTRO.md

This is a structural EXHAUSTION proof for two sources and two dendrites
per Decision/class. The positive control adds a third source only inside
a synthetic fixture. No migration code, C1ContextBrain or Nilo is edited.
"""
from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path

from .c1_context_brain import C1ContextBrain
from .c1_synapse_integrated import (
    C1SynapseState,DECISION_EXCITATORY_GENE,DECISION_INHIBITORY_GENE,
)
from .c1_migration import (
    SourceNeuron,Dendrite,MigrationConfig,MigrationState,
    RandStream,decision_migrate,
)


def verify_structural_feasibility()->dict:
    model=C1ContextBrain(300).initial()
    if len(model.dendrites)!=8:
        raise AssertionError("unexpected number of microbrain dendrites")
    if (DECISION_EXCITATORY_GENE.migration_type!=1
            or DECISION_INHIBITORY_GENE.migration_type!=1):
        raise AssertionError("Decision class does not have type1 migration")
    attrs={f.name for f in fields(C1SynapseState)}
    if attrs!={"dendrite","strength"}:
        raise AssertionError("microbrain synapse structure changed")

    # 4 groups: Decision0/1 × excitatory/inhibitory.
    # Only two Concept input sources (C0/C1), both already assigned.
    no_free_source=[]
    positive_controls=[]
    for decision in (0,1):
        for cls in ("exc","inh"):
            a=0x1000
            b=0x2000
            third=0x3000
            sources=(SourceNeuron(a),SourceNeuron(b))
            state=MigrationState((
                Dendrite(a,stw=0,ltw=0,strength=0),
                Dendrite(b,stw=20,ltw=5,strength=2),
            ),loose_counter=1)
            synthetic_init=MigrationConfig(
                initial_ltw_min=0,initial_ltw_max=0,
                initial_strength_min=1,initial_strength_max=1,
            )
            for picked in (0,1):
                outcome=decision_migrate(
                    state,sources,synthetic_init,RandStream((picked,)),
                    recipient_output=255,
                )
                if (outcome.migrated or outcome.reason!="duplicate_source"
                        or outcome.state!=state or outcome.random.cursor!=1):
                    raise AssertionError("two-source exhaustive migration impossibility failed")
                no_free_source.append({
                    "decision":decision,"class":cls,
                    "picked_existing_source":hex(sources[picked].pointer),
                    "result":outcome.reason,
                    "migrated":outcome.migrated,
                    "source_pointers_after":[hex(d.source_pointer)
                                             for d in outcome.state.dendrites],
                })

            inactive=decision_migrate(
                state,sources,synthetic_init,RandStream(()),recipient_output=0
            )
            if (inactive.reason!="inactive_recipient" or inactive.migrated
                    or inactive.random.cursor!=0):
                raise AssertionError("inactive recipient control mismatch")

            # POSITIVE CONTROL ONLY: third source available, no longer all
            # candidate pointers are duplicates. This is NOT a changed brain.
            candidates=sources+(SourceNeuron(third),)
            control=decision_migrate(
                state,candidates,synthetic_init,
                RandStream((2,0,0)),recipient_output=255,
            )
            if (not control.migrated or control.reason!="accepted"
                    or control.state.dendrites[0].source_pointer!=third
                    or control.state.loose_counter!=0
                    or control.random.cursor!=3):
                raise AssertionError("existing migration cannot even use unoccupied source")
            positive_controls.append({
                "decision":decision,"class":cls,
                "synthetic_source_count":3,
                "chosen_new_source":hex(third),
                "result":control.reason,
                "migrated":control.migrated,
                "source_pointers_after":[hex(d.source_pointer)
                                         for d in control.state.dendrites],
            })

    return {
        "protocol":"E09_02I_I3B3_MIGRACION_VIABILIDAD_PRE_REGISTRO-v1",
        "basis":"existing c1_migration.decision_migrate and C1ContextBrain topology",
        "n_brain_units":6,
        "n_synapses":len(model.dendrites),
        "n_concept_sources_per_decision_class":2,
        "n_dendrites_per_decision_class":2,
        "migration_type_decision":1,
        "can_migrate_under_current_two_source_topology":False,
        "rejection_cases":no_free_source,
        "positive_control_three_source_synthetic":positive_controls,
        "missing_runtime_source_pointer_field":True,
        "no_neurons_or_synapses_added_to_microbrain":True,
        "gate":"G-I3b3-STRUCT: verified structural inability to migrate with current two-source two-dendrite class",
        "limitations":(
            "A laboratory feasibility proof, not evidence original C1 cannot "
            "migrate. The full C1 Concept lobe has many potential sources, "
            "while reduced C1ContextBrain has only two and no dynamic source "
            "pointer field. Synthetic migration config is not a GEN claim."
        )
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    blob=json.dumps(verify_structural_feasibility(),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(blob,encoding="utf-8")
    print(blob,end="")


if __name__=="__main__":
    main()
