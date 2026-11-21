"""E09.02i-I3b.2a: posthoc, noninterfering synapse strength-loss witness.

Preregistered AFTER I3b2 data but BEFORE this code:
 docs/neurolab/E09_02I_I3B2A_FORTALEZA_PRE_REGISTRO.md

Replays identical 80 episodes and compares every eight-synapse update/tick
against unmodified C1ContextBrain AND full recorded I3b2 per-tick traces.
This is an observational attribution of vanished LTW inside our reduced
model; NOT a full historical C1 dendrite migration implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import defaultdict

from .c1_context_brain import C1ContextBrain
from .c1_synapse_integrated import (
    C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)
from .e09_coupled_brain import initial_coupled
from .e09_context_protocol import MAPPING_A, MAPPING_B
from .e09_i3_metabolic_protocol import selected_genes, add_environment_precursors
from .e09_i3b1_forks import MODES, GAIN, witness_step
from .e09_i3b2_ltw_window import (
    SEEDS, TARGETS, MAPPINGS, DELAY, PREP_TICKS,
    TARGET_TICKS, BASE_TICK, POST_TICKS, END_TICK, run_episode,
)

GATE=128


def classify_ltw_change(*,old:int,numeric:int,final:int,
                        lost_connection:bool,tick:int)->dict:
    """Falsify unexplained change outside LTW gate; account for atrophy reset."""
    if any(type(v) is not int or not 0<=v<=255 for v in (old,numeric,final)):
        raise ValueError("LTW byte state required")
    if type(tick) is not int or tick<0 or type(lost_connection) is not bool:
        raise ValueError("tick and lost_connection typed required")
    if tick%GATE!=0 and numeric!=old:
        raise AssertionError("LTW numeric changed outside update gate")
    if lost_connection:
        if final!=0:
            raise AssertionError("loss of connection did not reset LTW to zero")
        if final>numeric:
            raise AssertionError("reset cannot gain LTW")
    elif final!=numeric:
        raise AssertionError("LTW changed after numeric phase without connection loss")
    return {
        "ltw_cleared_by_strength_units":numeric-final if lost_connection else 0,
        "ltw_lost_positive":int(lost_connection and numeric>0),
        "numeric_ltw_changed":int(numeric!=old),
        "post_numeric_ltw_changed":int(final!=numeric),
    }


def synapse_witness(brain,state,context,receptors,reactions,gain):
    """One step, checking each original C1 strength/synapse trace."""
    applied=state.chemistry.decision_chem
    applied=(min(255,applied[0]*gain),min(255,applied[1]*gain),
             applied[2],applied[3])
    before=state.brain
    predictions=[]
    events=[]
    for index,syn in enumerate(before.dendrites):
        owner=index//4
        source=(index%4)//2
        genotype=(DECISION_INHIBITORY_GENE if index%2
                  else DECISION_EXCITATORY_GENE)
        traced=update_c1_synapse(
            syn,genotype,C1SynapticInput(
                source_output=before.concept_outputs[source],
                owner_state=before.neuron_states[owner],
                owner_output=before.neuron_outputs[owner],
                chemicals=applied,
            ),tick=before.tick+1,
        )
        classified=classify_ltw_change(
            old=syn.dendrite.ltw,
            numeric=traced.numeric.after.ltw,
            final=traced.after.dendrite.ltw,
            lost_connection=traced.strength.lost_connection,
            tick=before.tick+1,
        )
        predictions.append(traced.after)
        events.append({
            "synapse_index":index,"owner":owner,"source":source,
            "class":"inh" if index%2 else "exc",
            "strength_before":syn.strength,
            "strength_after":traced.after.strength,
            "did_gain":traced.strength.did_gain,
            "did_lose":traced.strength.did_lose,
            "lost_connection":traced.strength.lost_connection,
            "ltw_before":syn.dendrite.ltw,
            "ltw_numeric":traced.numeric.after.ltw,
            "ltw_final":traced.after.dendrite.ltw,
            "stw_before":syn.dendrite.stw,
            "stw_after":traced.after.dendrite.stw,
            "reinforcement_effect":traced.numeric.reinforcement_effect,
            **classified,
        })
    next_state,action=witness_step(
        brain,state,context,receptors,reactions,gain=gain,
    )
    if tuple(predictions)!=next_state.brain.dendrites:
        raise AssertionError("strength witness diverged from original brain")
    return next_state,action,applied,events


def replay_episode(seed,target,mapping_name,receptors=None,reactions=None):
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    source=run_episode(seed,target,mapping_name,receptors,reactions)
    mapping=MAPPING_A if mapping_name=="A" else MAPPING_B
    brain=C1ContextBrain(seed)
    state=initial_coupled(brain,receptors)
    preparation=tuple((i//8)%2 for i in range(PREP_TICKS))
    for context in preparation+(target,)*TARGET_TICKS:
        state,action=witness_step(
            brain,state,context,receptors,reactions,
        )
    if state.brain.tick!=BASE_TICK or action!=source["reference_action"]:
        raise AssertionError("I3b2a trunk differs from frozen I3b2")

    truth=None if action is None else action==mapping[target]
    outcome={}
    for mode in MODES:
        current=state
        injection=(0 if mode.startswith("E")
                   else DELAY if mode.startswith("L") else None)
        ticks=[]
        for index in range(POST_TICKS):
            if injection is not None and index==injection and truth is not None:
                current=add_environment_precursors(current,correct=truth)
            current,_action,applied,events=synapse_witness(
                brain,current,1-target,receptors,reactions,GAIN[mode])
            original=source["modes"][mode]["trace_ticks_125_136"][index]
            # These literal fields must reproduce exactly the prior data.
            if not (
                original["tick"]==current.brain.tick
                and original["read_chem_applied"]==list(applied)
                and original["reinforcement_effect_per_dendrite"]==
                    [e["reinforcement_effect"] for e in events]
                and original["pre_LTW"]==[e["ltw_before"] for e in events]
                and original["post_LTW"]==[e["ltw_final"] for e in events]
                and original["post_STW"]==[e["stw_after"] for e in events]
            ):
                raise AssertionError("I3b2a re-run NOT identical to I3b2 trace")
            ticks.append({
                "tick":current.brain.tick,
                "strength_lost":sum(e["lost_connection"] for e in events),
                "strength_gains":sum(e["did_gain"] for e in events),
                "strength_losses":sum(e["did_lose"] for e in events),
                "ltw_reset_event_count":sum(e["ltw_lost_positive"] for e in events),
                "ltw_reset_units":sum(e["ltw_cleared_by_strength_units"]
                                      for e in events),
                "all_synapses":events,
            })
        if current.brain.tick!=END_TICK:
            raise AssertionError("last tick shifted")
        outcome[mode]={
            "strength_lost":sum(t["strength_lost"] for t in ticks),
            "ltw_reset_event_count":sum(t["ltw_reset_event_count"] for t in ticks),
            "ltw_reset_units":sum(t["ltw_reset_units"] for t in ticks),
            "ltw_reset_units_129_to_136":sum(
                t["ltw_reset_units"] for t in ticks if 129<=t["tick"]<=136
            ),
            "ltw_gate_units_128":sum(
                (e["ltw_numeric"]-e["ltw_before"])
                for t in ticks if t["tick"]==128 for e in t["all_synapses"]
            ),
            "ltw_final_128":sum(
                e["ltw_final"] for t in ticks if t["tick"]==128
                for e in t["all_synapses"]
            ),
            "ltw_final_136":sum(
                e["ltw_final"] for t in ticks if t["tick"]==136
                for e in t["all_synapses"]
            ),
            "ticks":ticks,
        }
        if outcome[mode]["ltw_final_128"]-outcome[mode]["ltw_final_136"] != (
                outcome[mode]["ltw_reset_units_129_to_136"]):
            raise AssertionError("LTW reduction 128→136 not explained by strength resets")

    return {
        "seed":seed,"target":target,"mapping":mapping_name,
        "original_I3b2_action":source["reference_action"],
        "original_I3b2_sign":source["reference_correct"],
        "modes":outcome,
        "reproduced_all_original_brain_transitions":True,
    }


def run_all(seeds=SEEDS):
    if not isinstance(seeds,tuple) or not seeds:
        raise ValueError("nonempty cohort required")
    rs,rx=selected_genes()
    rows=[
        replay_episode(seed,target,name,rs,rx)
        for seed in seeds for target in TARGETS for name,_ in MAPPINGS
    ]
    by_mode={}
    for mode in MODES:
        total={
            label:sum(row["modes"][mode][label] for row in rows)
            for label in ("strength_lost","ltw_reset_event_count",
                          "ltw_reset_units","ltw_reset_units_129_to_136",
                          "ltw_gate_units_128","ltw_final_128","ltw_final_136")
        }
        total["by_tick"]={
            str(tick):{
                k:sum(
                    next(t[k] for t in row["modes"][mode]["ticks"]
                         if t["tick"]==tick)
                    for row in rows
                ) for k in ("strength_lost","ltw_reset_event_count",
                            "ltw_reset_units")
            } for tick in range(125,137)
        }
        by_mode[mode]=total
    return {
        "protocol":"E09_02I_I3B2A_FORTALEZA_PRE_REGISTRO-v1",
        "type":"posthoc observational audit of earlier I3b2 seeds",
        "seeds":list(seeds),"episode_count":len(rows),
        "gate":"WITNESS verified original state+trace; not learning proof",
        "all_absent_gate_drops_accounted":True,
        "totals":by_mode,"per_episode":rows,
        "limitations":(
            "Only reduced C1ContextBrain; historical dendrite migration "
            "is not integrated. Reuse of I3b2 cohort is diagnostic, "
            "not independent confirmatory evidence."
        )
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    out=json.dumps(run_all(),indent=2,sort_keys=True)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(out,encoding="utf-8")
    print(out,end="")


if __name__=="__main__":
    main()
