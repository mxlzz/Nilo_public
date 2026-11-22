"""I3c.6b: read-only, original-gene two-stage Decision anti-atrophy quantization.

PREREG: docs/neurolab/E09_02I_I3C6B_UMBRAL_QUIMICO_PRE_REGISTRO.md.
Uses existing original C1 emitter_tick and receptor_value math, *without*
changing chemistry, genes, neural topology or any learned weights.
It proves only an isolated zero-pool emission/reception path, not whole C1.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .c1_context_brain import C1ContextBrain
from .e09_historical_emitter import Emitter, emitter_tick
from .e09_historical_receptor import Receptor, receptor_value
from .e09_i3c3_dynamic_context import DynamicContextBrain

ROOT=Path(__file__).resolve().parents[2]
GEN_FIXTURE=ROOT / "docs/neurolab/resultados/e09h3_receptores_genoma_original.json"
ORIGINAL_GEN_SHA="e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4"
# These two Emitter tuples are original GEN genes 124/125, confirmed by
# E09_H_05_RESULTADO_EMISORES.md and byte-offset checks of dad1.gen.
EMITTER_GENES=(
    Emitter(124,0,6,1,53,0,1,255,1),
    Emitter(125,0,6,2,70,0,1,255,1),
)
RECEPTOR_IDS=(127,128)
LOCUS_VALUES=tuple(range(17))
WIRES=(0x1000,0x2000,0x2000,0x1000)


def authentic_receptors():
    data=json.loads(GEN_FIXTURE.read_text(encoding="utf-8"))
    if (data.get("genome_sha256")!=ORIGINAL_GEN_SHA
            or data.get("receptor_count")!=43):
        raise AssertionError("receptor GEN fixture mismatch")
    records={}
    for idx in RECEPTOR_IDS:
        gene=Receptor(idx,**data["brain_receptors"][str(idx)])
        if not (gene.organ==gene.lobe*0 and gene.lobe==6
                and gene.locus==15+(idx-127)
                and gene.chemical in (53,70)
                and gene.threshold==0 and gene.nominal==16
                and gene.gain==255 and gene.flags==1):
            raise AssertionError("original Decision inverted receptor has changed")
        records[idx]=gene
    if records[127].chemical!=53 or records[128].chemical!=70:
        raise AssertionError("GEN receptor/emitter mapping mismatch")
    return records


def capacities():
    """Read actual sizes by owner and class; never invent 16/128 for N."""
    fixed=C1ContextBrain(1420).initial()
    sizes={}
    for index,_synapse in enumerate(fixed.dendrites):
        key=(index//4,"inh" if index%2 else "exc")
        sizes[key]=sizes.get(key,0)+1
    dynamic=DynamicContextBrain(1420,migration_enabled=False).initial(wiring=WIRES)
    dynamic_sizes={}
    for link in dynamic.links:
        key=(link.owner,link.kind)
        dynamic_sizes[key]=dynamic_sizes.get(key,0)+1
    if (len(sizes)!=4 or len(dynamic_sizes)!=4
            or len(fixed.dendrites)!=8 or len(dynamic.links)!=4):
        raise AssertionError("unexpected microbrain class topology")
    return {
        "fixed_eight_synapses":{"class_counts":dict(
            sorted((f"D{o}-{kind}",n) for (o,kind),n in sizes.items())),
            "max_class_loose":max(sizes.values()),
            "min_class_loose_capacity":min(sizes.values()),
        },
        "dynamic_four_synapses":{"class_counts":dict(
            sorted((f"D{o}-{kind}",n) for (o,kind),n in dynamic_sizes.items())),
            "max_class_loose":max(dynamic_sizes.values()),
            "min_class_loose_capacity":min(dynamic_sizes.values()),
        },
    }


def audit():
    recs=authentic_receptors()
    rows={}
    for emitter, idx in zip(EMITTER_GENES,RECEPTOR_IDS):
        receptor=recs[idx]
        if (emitter.gene_index != idx-3 or
                emitter.chemical != receptor.chemical or
                emitter.sample_rate!=1 or emitter.flags!=1):
            raise AssertionError("original source/receptor pair mismatch")
        records=[]
        for source in LOCUS_VALUES:
            zero_pool=tuple(0 for _ in range(256))
            event=emitter_tick(emitter,zero_pool,source,tick=0)
            output=receptor_value(receptor,event.pool)
            if output is None:
                raise AssertionError("chemical receptor skipped expected gene")
            expected_emitted=((source*255)>>8) if source else 0
            expected_drop=((expected_emitted*255)>>8) if expected_emitted else 0
            if (event.added_to_pool!=expected_emitted
                    or output!=16-expected_drop
                    or event.pool[emitter.chemical]!=expected_emitted
                    or event.source!=0):
                raise AssertionError("existing C1 emitter/receptor math drift")
            records.append({
                "source_locus":source,
                "emitter_pool_amount":event.pool[emitter.chemical],
                "source_after_emitter":event.source,
                "receptor_value":output,
                "receptor_drop_from_nominal":16-output,
            })
        threshold=next(
            (r["source_locus"] for r in records if r["receptor_drop_from_nominal"]>0),
            None,
        )
        rows[str(emitter.gene_index)]={
            "emitter_gene":emitter.gene_index,
            "receiver_gene":idx,
            "chemical":emitter.chemical,
            "source_locus":emitter.locus,
            "threshold_first_receptor_drop":threshold,
            "samples":records,
        }
    thresholds={v["threshold_first_receptor_drop"] for v in rows.values()}
    if thresholds!={3}:
        raise AssertionError(f"unexpected C1 two-stage quantization {thresholds}")
    size=capacities()
    if not (size["fixed_eight_synapses"]["max_class_loose"]==2
            and size["dynamic_four_synapses"]["max_class_loose"]==1):
        raise AssertionError("microbrain capacities shifted")
    if any(v["max_class_loose"]>=3 for v in size.values()):
        raise AssertionError("capacity no longer smaller than chemical threshold")
    return {
        "protocol":"NL-EXP-I3c6b-v1",
        "study_type":"analytical read-only original C1 chemical functions, not an autonomous learning trial",
        "original_gen_sha256":ORIGINAL_GEN_SHA,
        "locus_values":list(LOCUS_VALUES),
        "pairs":rows,
        "first_locus_count_that_modifies_chem2_or_3":3,
        "topology":size,
        "conclusion":"Even with every connection in one class exhausted, type1 minimum loose counts in N eight/four-synapse models cannot exceed2/1. Original emitter+receptor functions have no antiatrophy chemical effect for source0..2. Isolated endogenous path is silent in these topologies.",
        "limitations":"Only a single zero-pool emitter->receptor path. Does not exclude other chemicals, reactions, emitter sources, neural routes, or whole C1 timing. The C1 original has 128 dendrites per Decision class, so this threshold is not an impossibility for that engine.",
        "gates":{"NUMERIC":"PASS if all assertions", "G05":"OPEN","G09":"OPEN","G00H":"OPEN"},
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=audit()
    data=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(data,encoding="utf-8")
    print(data,end="")


if __name__=="__main__":
    main()
