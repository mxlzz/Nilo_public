"""E09.02i-I3b.2: observed LTW gate at tick128 (N mechanistic, not C1 real time).

PREREGISTERED before code: docs/neurolab/E09_02I_I3B2_VENTANA_LTW_PRE_REGISTRO.md
Reuses I3b1's exact C1ContextBrain + chemistry adapter and artificially
rescaled CHEM0/1. Baseline tick124, dose once at tick125 versus tick128.
No modification to original C1 brain, genes, weights, dose or decay rates.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import argparse
import json

from .c1_context_brain import C1ContextBrain
from .c1_synapse_integrated import (
    C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)
from .e09_coupled_brain import initial_coupled
from .e09_context_protocol import MAPPING_A, MAPPING_B
from .e09_i3_metabolic_protocol import (
    PRECURSOR_DOSE, add_environment_precursors, selected_genes,
)
from .e09_i3b1_forks import (
    MODES, GAIN, DELAYS, witness_step, paired_bootstrap,
)

SEEDS=tuple(range(400,420))
TARGETS=(0,1)
MAPPINGS=(("A",MAPPING_A),("B",MAPPING_B))
DELAY=3
PREP_TICKS=120
TARGET_TICKS=4
POST_TICKS=DELAY+1+8
READOUT_TICKS=4
BASE_TICK=PREP_TICKS+TARGET_TICKS
LTW_GATE_TICK=128
END_TICK=BASE_TICK+POST_TICKS


def _synapse_inspection(before,context,gain,target_action):
    """Independent observer over old state, using existing C1 synapse code."""
    state=before.brain
    chem=before.chemistry.decision_chem
    applied=(min(255,chem[0]*gain),min(255,chem[1]*gain),chem[2],chem[3])
    events=[]
    expected=[]
    for i,syn in enumerate(state.dendrites):
        owner=i//4
        source=(i%4)//2
        gene=(DECISION_INHIBITORY_GENE if i%2 else DECISION_EXCITATORY_GENE)
        result=update_c1_synapse(
            syn,gene,
            C1SynapticInput(
                source_output=state.concept_outputs[source],
                owner_state=state.neuron_states[owner],
                owner_output=state.neuron_outputs[owner],
                chemicals=applied,
            ),tick=state.tick+1,
        )
        expected.append(result.after)
        events.append(result.numeric.reinforcement_effect)
    return applied,events,tuple(expected)


def _tick_recorded(brain,state,context,receptors,reactions,*,gain,phase):
    old=state
    applied,effects,witness=_synapse_inspection(old,context,gain,None)
    new,action=witness_step(
        brain,state,context,receptors,reactions,gain=gain
    )
    if witness!=new.brain.dendrites:
        raise AssertionError("recorded synapse witness disagrees with neural step")
    record={
        "tick":new.brain.tick,
        "input_context":context,
        "phase":phase,
        "read_chem_raw":list(old.chemistry.decision_chem),
        "read_chem_applied":list(applied),
        "reinforcement_effect_per_dendrite":effects,
        "pre_susceptibility":[s.dendrite.susceptibility for s in old.brain.dendrites],
        "pre_STW":[s.dendrite.stw for s in old.brain.dendrites],
        "post_STW":[s.dendrite.stw for s in new.brain.dendrites],
        "pre_LTW":[s.dendrite.ltw for s in old.brain.dendrites],
        "post_LTW":[s.dendrite.ltw for s in new.brain.dendrites],
        "pool_after_selected":{
            str(c):new.chemistry.pool[c] for c in (1,17,33,49,50,51)
        },
    }
    return new,action,record


def _distances(target_state,neutral_state,target,reference_action,prefix):
    winner=0 if reference_action=="D0" else (
        1 if reference_action=="D1" else -1)
    out={}
    for weight in ("stw","ltw"):
        deltas=[
            abs(getattr(a.dendrite,weight)-getattr(b.dendrite,weight))
            for a,b in zip(target_state.brain.dendrites,
                           neutral_state.brain.dendrites)
        ]
        out[prefix+"_"+weight+"_sum_abs"]=sum(deltas)
        out[prefix+"_"+weight+"_changed"]=sum(v>0 for v in deltas)
        out[prefix+"_"+weight+"_candidate_abs"]=sum(
            x for i,x in enumerate(deltas)
            if (i%4)//2==target and i//4==winner)
        out[prefix+"_"+weight+"_target_source_abs"]=sum(
            x for i,x in enumerate(deltas) if (i%4)//2==target)
        out[prefix+"_"+weight+"_distractor_source_abs"]=sum(
            x for i,x in enumerate(deltas) if (i%4)//2!=target)
    return out


def run_episode(seed,target,mapping_name,receptors=None,reactions=None):
    if type(seed) is not int or seed<0 or target not in TARGETS or (
            mapping_name not in ("A","B")):
        raise ValueError("invalid I3b2 episode coordinates")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    mapping=MAPPING_A if mapping_name=="A" else MAPPING_B
    brain=C1ContextBrain(seed)
    state=initial_coupled(brain,receptors)
    preparation=tuple((i//8)%2 for i in range(PREP_TICKS))
    for context in preparation+(target,)*TARGET_TICKS:
        state,reference_action=witness_step(
            brain,state,context,receptors,reactions,
        )
    if state.brain.tick!=BASE_TICK:
        raise AssertionError("LTW gate experimental timebase drift")
    correct=None if reference_action is None else (
        reference_action==mapping[target])
    results={}
    chemistry={}
    snapshots={}
    for mode in MODES:
        current=state
        gained=GAIN[mode]
        injection_index=0 if mode.startswith("E") else (
            DELAY if mode.startswith("L") else None)
        n_injected=0
        traces=[]
        ch=[]
        milestone={}
        for i in range(POST_TICKS):
            if injection_index is not None and i==injection_index and correct is not None:
                current=add_environment_precursors(current,correct=correct)
                n_injected+=1
            current,_,record=_tick_recorded(
                brain,current,1-target,receptors,reactions,
                gain=gained,phase="post-target",
            )
            traces.append(record)
            ch.append(current.chemistry)
            if current.brain.tick in (127,LTW_GATE_TICK,END_TICK):
                milestone[current.brain.tick]=current
        if not set((127,128,136)).issubset(milestone):
            raise AssertionError("missing preregistered LTW snapshots")
        snapshots[mode]=milestone
        chemistry[mode]=tuple(ch)
        readout=None
        for _ in range(READOUT_TICKS):
            current,readout=witness_step(
                brain,current,target,receptors,reactions,
                gain=gained,learn=False,
            )
        results[mode]={
            "gain":gained,
            "event_absolute_tick":(
                BASE_TICK+injection_index+1
                if injection_index is not None and correct is not None else None
            ),
            "delivered_events":n_injected,
            "trace_ticks_125_136":traces,
            "readout_action":readout,
            "readout_correct":int(readout==mapping[target]),
        }

    if chemistry["E1"]!=chemistry["E4"] or chemistry["L1"]!=chemistry["L4"]:
        raise AssertionError("gain contaminated upstream chemical trajectory")
    if any(
        results[mode]["delivered_events"]!=(
            0 if mode=="N" or correct is None else 1)
        for mode in MODES
    ):
        raise AssertionError("incorrect number of precursor events")

    for mode in MODES:
        for tick,label in ((127,"tick127"),(128,"tick128"),(136,"tick136")):
            results[mode].update(_distances(
                snapshots[mode][tick],snapshots["N"][tick],
                target,reference_action,label,
            ))
        # The original C1 rate=128 forbids any LTW updates before tick128
        # after the last previous multiple of 128 (the setup starts at t0).
        if results[mode]["tick127_ltw_sum_abs"]!=0:
            raise AssertionError("pre-gate LTW diverged before tick128")
    return {
        "seed":seed,"target":target,"mapping":mapping_name,
        "reference_action":reference_action,
        "reference_correct":correct,
        "base_tick":BASE_TICK,"first_eligible_ltw_tick":128,
        "modes":results,"upstream_chem_same_at_fixed_timing":True,
        "last_measured_plastic_tick":END_TICK,
        "last_readout_tick":END_TICK+READOUT_TICKS,
    }


def run_all(seeds=SEEDS):
    if not isinstance(seeds,tuple) or not seeds or any(
            type(s) is not int or s<0 for s in seeds):
        raise ValueError("nonempty seed tuple needed")
    receptors,reactions=selected_genes()
    rows=[
        run_episode(seed,target,name,receptors,reactions)
        for seed in seeds for target in TARGETS for name,_ in MAPPINGS
    ]
    # pair bootstrap expects "branches", but this protocol calls them "modes";
    # transfer numerical estimates only, leaving each original observation unchanged.
    view=[
        {"seed":ep["seed"],"branches":ep["modes"]}
        for ep in rows
    ]
    contrasts={
        "gate128_ltw_E4_minus_L4":paired_bootstrap(
            view,"E4","L4","tick128_ltw_sum_abs"
        ),
        "gate128_ltw_E1_minus_L1":paired_bootstrap(
            view,"E1","L1","tick128_ltw_sum_abs"
        ),
        "gate128_ltw_E4_minus_N":paired_bootstrap(
            view,"E4","N","tick128_ltw_sum_abs"
        ),
        "gate128_stw_E4_minus_L4":paired_bootstrap(
            view,"E4","L4","tick128_stw_sum_abs"
        ),
        "end136_ltw_E4_minus_L4":paired_bootstrap(
            view,"E4","L4","tick136_ltw_sum_abs"
        ),
        "readout_E4_minus_N":paired_bootstrap(
            view,"E4","N","readout_correct"
        ),
    }
    return {
        "protocol":"E09_02I_I3B2_VENTANA_LTW_PRE_REGISTRO-v1",
        "study_type":"phase-gated one-pulse synaptic consolidation N diagnostic",
        "seeds":list(seeds),"episode_count":len(rows),
        "distractor_delay":DELAY,"base_tick":BASE_TICK,
        "early_injection_tick":125,"late_injection_tick":128,
        "ltw_first_boundary_tick":128,"after_tick":END_TICK,
        "readout_end_tick":END_TICK+READOUT_TICKS,
        "rates_synthetic":40,"dose":PRECURSOR_DOSE,
        "means_by_mode":{
            mode:{
                label:sum(ep["modes"][mode][label] for ep in rows)/len(rows)
                for label in (
                    "tick128_ltw_sum_abs","tick128_ltw_changed",
                    "tick128_stw_sum_abs",
                    "tick136_ltw_sum_abs","readout_correct")
            } for mode in MODES
        },
        "counts":{
            "correct_reference":sum(ep["reference_correct"] is True for ep in rows),
            "incorrect_reference":sum(ep["reference_correct"] is False for ep in rows),
            "missing_reference":sum(ep["reference_correct"] is None for ep in rows),
        },
        "contrasts":contrasts,
        "per_episode":rows,
        "gate_wiring":"PASS: 5 branches, same trunk, single precursor and chemical matching",
        "gate_behavioral_G05_G09":"NOT EVALUATED; I3 remains negative",
        "limitations":(
            "Tick128 is a logical phase intervention, not a real-time frequency; "
            "artificial gain4, synthetic chemistry rates40 and one-pulse window "
            "do not establish historical C1 fidelity or lasting learned behavior."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    document=json.dumps(run_all(),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(document,encoding="utf-8")
    print(document,end="")


if __name__=="__main__":
    main()
