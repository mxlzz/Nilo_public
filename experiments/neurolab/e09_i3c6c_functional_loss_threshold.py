"""I3c.6c: functional strength-loss threshold after original C1 two-stage chemistry.

PRE-REG: docs/neurolab/E09_02I_I3C6C_UMBRAL_ATROFIA_PRE_REGISTRO.md
This is read-only numeric behavior of existing C1 emitter/receptor/synapse rules.
Not a new brain, controller, dose, learning result or whole-C1 equivalence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .e09_i3c6b_feedback_threshold import (
    EMITTER_GENES, RECEPTOR_IDS, authentic_receptors, capacities,
)
from .e09_historical_emitter import emitter_tick
from .e09_historical_receptor import receptor_value
from .c1_dendrite_tick import DendriteState
from .c1_synapse_integrated import (
    C1SynapseState, C1SynapticInput,
    DECISION_EXCITATORY_GENE, DECISION_INHIBITORY_GENE,
    update_c1_synapse,
)

LOCUS_VALUES=tuple(range(33))
GENES=(DECISION_EXCITATORY_GENE,DECISION_INHIBITORY_GENE)


def evaluate():
    receptors=authentic_receptors()
    response={}
    for emitter,idx,gene,channel in zip(
        EMITTER_GENES,RECEPTOR_IDS,GENES,(2,3)
    ):
        rows=[]
        rec=receptors[idx]
        for x in LOCUS_VALUES:
            event=emitter_tick(
                emitter,tuple(0 for _ in range(256)),x,0
            )
            chem=receptor_value(rec,event.pool)
            if chem is None:
                raise AssertionError("expected C1 original inverted receptor")
            chems=[0,0,0,0]
            chems[channel]=chem
            output=update_c1_synapse(
                C1SynapseState(DendriteState(),4),
                gene,
                C1SynapticInput(
                    source_output=0,owner_state=80,owner_output=0,
                    chemicals=tuple(chems),
                ),tick=5,
            )
            if output.lose_strength_rule_output!=chem:
                raise AssertionError("original C1 CHEM loss rule mismatch")
            expected=4-int(chem>0)
            if output.after.strength!=expected:
                raise AssertionError("original C1 loss tick mismatch")
            rows.append({
                "locus":x,"chemical_from_emitter":event.pool[emitter.chemical],
                "decision_chem_value":chem,
                "lose_rule_output":output.lose_strength_rule_output,
                "strength_before":4,"strength_after_tick5":output.after.strength,
                "loss_inhibited":output.after.strength==4,
            })
        first_chemical=next((x["locus"] for x in rows
                             if x["decision_chem_value"]<16),None)
        first_loss=next((x["locus"] for x in rows
                         if x["loss_inhibited"]),None)
        if first_chemical!=3 or first_loss!=18:
            raise AssertionError(
                f"critical original thresholds mismatch {first_chemical}/{first_loss}"
            )
        response[str(emitter.gene_index)]={
            "emitter":emitter.gene_index,
            "receptor":idx,
            "channel":channel,
            "chemical_id":emitter.chemical,
            "first_receptor_change":first_chemical,
            "first_strength_loss_inhibition":first_loss,
            "curve":rows,
        }
    counts=capacities()
    if (counts["fixed_eight_synapses"]["max_class_loose"]!=2
            or counts["dynamic_four_synapses"]["max_class_loose"]!=1):
        raise AssertionError("reduced topology changed")
    return {
        "protocol":"NL-EXP-I3c6c-v1",
        "study_type":"isolated genuine-gene numeric response; not full game or learning",
        "pairs":response,
        "functional_antiatrophy_locus_threshold":18,
        "receptor_change_locus_threshold":3,
        "reduced_class_capacities":counts,
        "historical_decision_class_capacity":128,
        "conclusion":"An original chemical receptor shift at loose count3 (CHEM16->15) still triggers exactly the same strength loss at tick5; preventing the loss requires CHEM=0, first achieved at locus18 in this isolated zero-pool path. Even increasing reduced Decision class capacity from2 to3 would not inhibit atrophy; 18 is only a necessary capacity bound, not sufficient to guarantee runtime feedback.",
        "limitations":"Single emitter, receptor, zero pool and synthetic isolated dendrite with initial strength4. Other C1 chemical sources/scheduling not excluded; no demonstration of behavior, memory or autonomy.",
        "G05_G09_G00H":"OPEN",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=evaluate()
    raw=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw,encoding="utf-8")
    print(raw,end="")


if __name__=="__main__":
    main()
