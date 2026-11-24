"""E09.02i-I3a retrospective read-only synapse diagnostic.

Replays the exact I3 metabolic M training arm. The existing C1 synapse
interpreter is evaluated observationally on OLD brain/chemistry snapshots,
then compared against every dendrite actually produced by C1ContextBrain.
No original learner, parameters, seeds or feedback code is modified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .c1_context_brain import C1ContextBrain
from .c1_synapse_integrated import (
    C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)
from .e09_coupled_brain import CoupledState,initial_coupled
from .e09_context_protocol import MAPPING_A,MAPPING_B
from .e09_delayed_distractors_protocol import trials
from .e09_i3_metabolic_protocol import (
    SEEDS,LAB_RATE,PRECURSOR_DOSE,TRAIN_REPEATS,TARGET_TICKS,
    selected_genes,metabolic_step,metabolic_phase,
    add_environment_precursors,
)

FIELDS=(
    "synapse_samples","chem_positive","susceptibility_positive",
    "chem_and_suscept_positive","effect_positive","stw_increased",
    "stw_changed","ltw_changed","source_nonzero","owner_output_nonzero",
)


def new_counters()->dict:
    return {**{x:0 for x in FIELDS},
            "max_chem":0,"max_susceptibility":0,"max_effect":0,
            "max_source_output":0,"max_owner_output":0,
            "by_class":{
                "excitatory":{"samples":0,"chem_positive":0,"effect_positive":0},
                "inhibitory":{"samples":0,"chem_positive":0,"effect_positive":0},
            }}


def observed_step(brain,state,context,receptors,reactions,counters):
    if not isinstance(state,CoupledState):
        raise TypeError("CoupledState required")
    initial=state.brain
    chem=state.chemistry.decision_chem
    predictions=[]
    for i,syn in enumerate(initial.dendrites):
        owner=i//4
        source=(i%4)//2
        inhibitory=i%2==1
        genotype=(DECISION_INHIBITORY_GENE if inhibitory
                  else DECISION_EXCITATORY_GENE)
        value=chem[1 if inhibitory else 0]
        source_output=initial.concept_outputs[source]
        owner_output=initial.neuron_outputs[owner]
        witness=update_c1_synapse(
            syn,genotype,
            C1SynapticInput(
                source_output=source_output,
                owner_state=initial.neuron_states[owner],
                owner_output=owner_output,
                chemicals=chem,
            ),
            tick=initial.tick+1,
        )
        predictions.append(witness.after)
        effect=witness.numeric.reinforcement_effect
        bc=counters["by_class"]["inhibitory" if inhibitory else "excitatory"]
        counters["synapse_samples"]+=1
        bc["samples"]+=1
        counters["chem_positive"]+=int(value>0)
        bc["chem_positive"]+=int(value>0)
        counters["susceptibility_positive"]+=int(syn.dendrite.susceptibility>0)
        counters["chem_and_suscept_positive"]+=int(
            value>0 and syn.dendrite.susceptibility>0)
        counters["effect_positive"]+=int(effect>0)
        bc["effect_positive"]+=int(effect>0)
        counters["stw_increased"]+=int(
            witness.after.dendrite.stw > syn.dendrite.stw)
        counters["stw_changed"]+=int(
            witness.after.dendrite.stw != syn.dendrite.stw)
        counters["ltw_changed"]+=int(
            witness.after.dendrite.ltw != syn.dendrite.ltw)
        counters["source_nonzero"]+=int(source_output>0)
        counters["owner_output_nonzero"]+=int(owner_output>0)
        counters["max_chem"]=max(counters["max_chem"],value)
        counters["max_susceptibility"]=max(
            counters["max_susceptibility"],syn.dendrite.susceptibility)
        counters["max_effect"]=max(counters["max_effect"],effect)
        counters["max_source_output"]=max(
            counters["max_source_output"],source_output)
        counters["max_owner_output"]=max(
            counters["max_owner_output"],owner_output)
    advanced,action,trace=metabolic_step(
        brain,state,context,receptors,reactions,plasticity=True)
    if tuple(predictions)!=advanced.brain.dendrites:
        raise AssertionError(
            "read-only synapse witness disagrees with actual C1ContextBrain")
    if trace.brain_trace.before!=initial:
        raise AssertionError("brain's pre-tick input differs from witness")
    return advanced,action


def observe_phase(brain,state,seq,mapping,receptors,reactions):
    counts=new_counters()
    choices_missing=feedback_events=0
    for target,delay in seq:
        choice=None
        for _ in range(TARGET_TICKS):
            state,choice=observed_step(
                brain,state,target,receptors,reactions,counts)
        choices_missing+=int(choice is None)
        for _ in range(delay):
            state,_=observed_step(
                brain,state,1-target,receptors,reactions,counts)
        if choice is not None:
            state=add_environment_precursors(
                state,correct=bool(choice==mapping[target]))
            feedback_events+=1
        state,_=observed_step(
            brain,state,1-target,receptors,reactions,counts)
    counts["missing_target_choices"]=choices_missing
    counts["delivered_precursors"]=feedback_events
    counts["brain_ticks"]=state.brain.tick
    return state,counts


def run_seed(seed:int)->dict:
    receptors,reactions=selected_genes()
    brain=C1ContextBrain(seed)
    state=initial_coupled(brain,receptors)
    answer={"seed":seed}
    for label,salt,mapping in (
        ("first",50000,MAPPING_A),
        ("reversed",60000,MAPPING_B),
    ):
        seq=trials(seed,salt,TRAIN_REPEATS)
        reference,_=metabolic_phase(
            brain,state,seq,mapping,receptors,reactions,
            feedback=True,plasticity=True,
        )
        current,counts=observe_phase(
            brain,state,seq,mapping,receptors,reactions)
        if current!=reference:
            raise AssertionError(
                f"observational replay diverged from I3 M in phase {label}")
        answer[label]=counts
        state=current
    return answer


def run_all(seeds:tuple[int,...]=SEEDS)->dict:
    if (not isinstance(seeds,tuple) or not seeds or any(
            type(x) is not int or x<0 for x in seeds)):
        raise ValueError("nonempty tuple of nonnegative seed ints")
    rows=[run_seed(seed) for seed in seeds]
    totals={}
    for phase in ("first","reversed"):
        total={field:sum(r[phase][field] for r in rows) for field in FIELDS}
        total["missing_target_choices"]=sum(
            r[phase]["missing_target_choices"] for r in rows)
        total["delivered_precursors"]=sum(
            r[phase]["delivered_precursors"] for r in rows)
        for field in ("max_chem","max_susceptibility","max_effect",
                      "max_source_output","max_owner_output"):
            total[field]=max(r[phase][field] for r in rows)
        total["by_class"]={
            label:{
                key:sum(r[phase]["by_class"][label][key] for r in rows)
                for key in ("samples","chem_positive","effect_positive")
            } for label in ("excitatory","inhibitory")
        }
        totals[phase]=total
    return {
        "protocol":"E09_02I_I3A_DIAGNOSTICO_POSTHOC_PRE_REGISTRO-v1",
        "status":"retrospective observational, not new holdout",
        "seeds":list(seeds),
        "rates_lab":LAB_RATE,
        "precursor_dose":PRECURSOR_DOSE,
        "totals":totals,
        "per_seed":rows,
        "replay_equivalence":"all 8 synapses each tick and final phase state",
        "scientific_gate":"not evaluated; I3 remains negative",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    doc=json.dumps(run_all(),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(doc,encoding="utf-8")
    print(doc,end="")


if __name__=="__main__":
    main()
