"""I3c.4b: preregistered POSTHOC read-only tick128 LTW gate witness.

Same original I3c4 seeds and chemical/genetic rules. Recomputes every
synapse at train ticks divisible by128, compares against actual step,
and verifies immutable per-seed SHA256. No model changes.
See docs/neurolab/E09_02I_I3C4B_GATE128_PRE_REGISTRO.md.
"""
from __future__ import annotations

from hashlib import sha256
from unittest.mock import patch
import argparse
import json

from . import e09_i3c4_yoked_metabolic as original
from .e09_i3c4a_turnover_observer import WitnessBrain,golden_hashes,MODES,PHASES
from .e09_i3c3_dynamic_context import concept_index
from .c1_synapse_integrated import (
    C1SynapticInput,DECISION_EXCITATORY_GENE,DECISION_INHIBITORY_GENE,
    update_c1_synapse,
)

PERIOD=128

class GateWitness(WitnessBrain):
    registry=[]

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.gates={p:[] for p in PHASES}

    def step(self,state,context,chemicals,*,learn=True):
        trace=super().step(state,context,chemicals,learn=learn)
        tick=trace.after.tick
        if not learn or tick%PERIOD:
            return trace
        phase=PHASES[self.phase_index]
        records=[]
        ev_by_slot={(x.owner,x.kind):x for x in trace.migration}
        for i,connection in enumerate(state.links):
            idx=concept_index(connection.source_pointer)
            gene=(DECISION_EXCITATORY_GENE if connection.kind=="exc"
                  else DECISION_INHIBITORY_GENE)
            test=update_c1_synapse(
                connection.synapse,gene,C1SynapticInput(
                    source_output=state.concept_outputs[idx],
                    owner_state=state.neuron_states[connection.owner],
                    owner_output=state.neuron_outputs[connection.owner],
                    chemicals=chemicals,
                ),tick=tick,
            )
            event=ev_by_slot.get((connection.owner,connection.kind))
            after=trace.after.links[i]
            migrated=bool(event and event.migrated)
            if migrated:
                if not (
                    test.after.strength==0
                    and after.source_pointer!=connection.source_pointer
                    and after.synapse.strength==2
                    and after.synapse.dendrite.ltw==0):
                    raise AssertionError("invalid Type1 change at LTW gate")
            elif (after.synapse!=test.after or
                  after.source_pointer!=connection.source_pointer):
                raise AssertionError("read-only C1 synapse gate witness mismatch")
            numeric=test.numeric.after
            erased=numeric.ltw-test.after.dendrite.ltw
            if erased<0 or (erased>0 and not test.strength.lost_connection):
                raise AssertionError("LTW erased without strength reset")
            records.append({
                "slot":i,"owner":connection.owner,
                "class":connection.kind,
                "source_pointer":hex(connection.source_pointer),
                "pre_STW":connection.synapse.dendrite.stw,
                "post_STW":test.after.dendrite.stw,
                "pre_LTW":connection.synapse.dendrite.ltw,
                "numeric_LTW":numeric.ltw,
                "post_strength_LTW":test.after.dendrite.ltw,
                "final_LTW":after.synapse.dendrite.ltw,
                "pre_strength":connection.synapse.strength,
                "post_strength":test.after.strength,
                "source_output":state.concept_outputs[idx],
                "chem0":chemicals[0],"chem1":chemicals[1],
                "susceptibility":numeric.susceptibility,
                "effect":test.numeric.reinforcement_effect,
                "numeric_delta":numeric.ltw-connection.synapse.dendrite.ltw,
                "erased_by_strength":erased,
                "migrated":migrated,
            })
        self.gates[phase].append({
            "tick":tick,"context":context,"rows":records,
        })
        return trace


def observe_seed(seed,golden):
    if type(seed) is not int or seed not in original.SEEDS:
        raise ValueError("seed outside preregistered original cohort")
    GateWitness.registry=[]
    with patch.object(original,"DynamicContextBrain",GateWitness):
        row=original.run_seed(seed)
    digest=sha256(json.dumps(row,sort_keys=True,separators=(",",":"),
                              ensure_ascii=True).encode()).hexdigest()
    if digest!=golden[str(seed)]:
        raise AssertionError("gate observer changed frozen original I3c4 output")
    if tuple(b.mode for b in GateWitness.registry)!=MODES:
        raise AssertionError("observer mode order changed")
    records={}
    fields={
        "positive_STW":lambda r:r["post_STW"]>0,
        "positive_susceptibility":lambda r:r["susceptibility"]>0,
        "positive_effect":lambda r:r["effect"]>0,
        "numeric_LTW_increase":lambda r:r["numeric_delta"]>0,
        "numeric_LTW_decrease":lambda r:r["numeric_delta"]<0,
        "strength_LTW_erasure_units":lambda r:r["erased_by_strength"],
        "post_strength_positive_LTW":lambda r:r["post_strength_LTW"]>0,
        "final_positive_LTW":lambda r:r["final_LTW"]>0,
        "migration_at_gate":lambda r:r["migrated"],
        "strength_zero_before_gate":lambda r:r["pre_strength"]==0,
    }
    for brain in GateWitness.registry:
        records[brain.mode]={}
        for phase in PHASES:
            gates=brain.gates[phase]
            cells=[c for g in gates for c in g["rows"]]
            if any(len(g["rows"])!=4 or g["tick"]%PERIOD for g in gates):
                raise AssertionError("gate slots/clock incorrect")
            d={"gate_ticks":len(gates),"synapse_samples":len(cells)}
            for label,measure in fields.items():
                d[label]=sum(measure(x) for x in cells)
            d["per_gate"]=gates
            records[brain.mode][phase]=d
    if any(records["F"][p]["gate_ticks"] for p in PHASES):
        raise AssertionError("frozen arm contributed consolidation gate")
    return {"seed":seed,"sha_verified":True,"sha256":digest,"modes":records}


def run_all(seeds=original.SEEDS):
    if not isinstance(seeds,tuple) or not seeds or any(
            type(seed) is not int or seed not in original.SEEDS for seed in seeds
    ) or len(set(seeds))!=len(seeds):
        raise ValueError("only unique original seeds allowed")
    gold=golden_hashes()
    rows=[observe_seed(s,gold) for s in seeds]
    totals={}
    for mode in MODES:
        totals[mode]={}
        for phase in PHASES:
            keys=[k for k in rows[0]["modes"][mode][phase] if k!="per_gate"]
            totals[mode][phase]={
                key:sum(row["modes"][mode][phase][key] for row in rows)
                for key in keys
            }
    return {
        "protocol":"E09_02I_I3C4B_GATE128_PRE_REGISTRO-v1",
        "status":"read-only posthoc same 900..919 seeds; not confirmatory",
        "original_workflow_id":44960526007,
        "original_artifact_id":14729775966,
        "seeds":list(seeds),"gate_period":PERIOD,
        "all_original_per_seed_sha_verified":True,
        "totals":totals,"per_seed":rows,
        "G05_G09":"OPEN",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output")
    args=parser.parse_args()
    doc=json.dumps(run_all(),indent=2,sort_keys=True)+"\n"
    if args.output:
        from pathlib import Path
        path=Path(args.output)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(doc,encoding="utf-8")
    print(doc,end="")


if __name__=="__main__":
    main()
