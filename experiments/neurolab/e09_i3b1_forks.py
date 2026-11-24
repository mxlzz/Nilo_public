"""E09.02i-I3b.1: paired one-pulse chemical counterfactuals, N line only.

PRE-REGISTERED: docs/neurolab/E09_02I_I3B1_RAMAS_QUIMICAS_PRE_REGISTRO.md.
A shared trained-without-reward trunk is forked into N,E1,L1,E4,L4;
same causal action and external precursor, different delivery time or
artificial neural CHEM gain.  No change to C1ContextBrain or C1 genes.

This is a mechanistic one-pulse study, NOT autonomous learning or
historical C1 gain. Rates=40, dose=80, genes reused from I3.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
import argparse
import json
import random
import statistics

from .c1_context_brain import C1ContextBrain
from .c1_synapse_integrated import (
    C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)
from .e09_chemical_bridge import chemical_bridge_tick
from .e09_coupled_brain import CoupledState, initial_coupled
from .e09_context_protocol import MAPPING_A, MAPPING_B
from .e09_i3_metabolic_protocol import (
    PRECURSOR_DOSE, RATES, selected_genes, add_environment_precursors,
    metabolic_step,
)
from .e09_pool_decay import decay_pool

SEEDS = tuple(range(300,320))
DELAYS = (1,2,3)
MAPS = (("A",MAPPING_A),("B",MAPPING_B))
MODES = ("N","E1","L1","E4","L4")
GAIN = {"N":1,"E1":1,"L1":1,"E4":4,"L4":4}
WARMUP = (0,)*8+(1,)*8+(0,)*8+(1,)*8
TARGET_TICKS = 4
EXTRA_DISTRACTOR_TICKS = 8
READOUT_TICKS = 4
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 60513


def _counters() -> dict:
    return {
        "effect_total":0,"effect_candidate":0,
        "effect_target_source":0,"effect_distractor_source":0,
        "positive_effect_events":0,"synapse_samples":0,
        "max_effect":0,"max_neural_chem":0,
    }


def witness_step(brain, state, context, receptors, reactions, *,
                 gain=1, learn=True, selected_action=None,
                 target=None, counters=None):
    """Same chemistry as I3; only CHEM0/1 input scaled if gain=4.

    The existing synapse update verifies every instrumented transition;
    a modification to C1ContextBrain would cause the assertion to fail.
    """
    if gain not in (1,4):
        raise ValueError("only preregistered gains 1 or 4")
    if counters is not None and (target not in (0,1) or
                                 selected_action not in ("D0","D1",None)):
        raise ValueError("target/action for witness required")
    old=state.brain
    unscaled=state.chemistry.decision_chem
    applied=(min(255,unscaled[0]*gain),min(255,unscaled[1]*gain),
             unscaled[2],unscaled[3])
    if counters is not None and learn:
        expected=[]
        winner_id=0 if selected_action=="D0" else (
            1 if selected_action=="D1" else -1)
        for index,syn in enumerate(old.dendrites):
            owner=index//4
            source=(index%4)//2
            inhibitory=bool(index%2)
            gene=(DECISION_INHIBITORY_GENE if inhibitory
                  else DECISION_EXCITATORY_GENE)
            inp=C1SynapticInput(
                source_output=old.concept_outputs[source],
                owner_state=old.neuron_states[owner],
                owner_output=old.neuron_outputs[owner],
                chemicals=applied,
            )
            witness=update_c1_synapse(syn,gene,inp,tick=old.tick+1)
            expected.append(witness.after)
            val=witness.numeric.reinforcement_effect
            counters["effect_total"]+=val
            counters["effect_target_source"]+=val if source==target else 0
            counters["effect_distractor_source"]+=val if source!=target else 0
            counters["effect_candidate"]+=val if (
                source==target and owner==winner_id) else 0
            counters["positive_effect_events"]+=int(val>0)
            counters["synapse_samples"]+=1
            counters["max_effect"]=max(counters["max_effect"],val)
            counters["max_neural_chem"]=max(
                counters["max_neural_chem"],applied[0],applied[1])
    bt=brain.step(old,context,applied,learn=learn)
    if counters is not None and learn and tuple(expected)!=bt.after.dendrites:
        raise AssertionError("witness dendrites not equal to real neural step")
    ct=chemical_bridge_tick(state.chemistry,(),receptors,reactions)
    new_pool=decay_pool(ct.after.pool,RATES,state.chemistry.tick)
    result=CoupledState(bt.after,replace(ct.after,pool=new_pool))
    return result,bt.action


def common_trunk(brain,target,receptors,reactions):
    state=initial_coupled(brain,receptors)
    for context in WARMUP+(target,)*TARGET_TICKS:
        state,action=witness_step(
            brain,state,context,receptors,reactions,
        )
    return state,action


def source_memory_distance(state,control,target,action):
    """Absolute STW/LTW distance from no-precursor branch at SAME tick."""
    winner=0 if action=="D0" else 1 if action=="D1" else -1
    sums={"stw_candidate":0,"stw_target_source":0,"stw_distractor_source":0,
          "ltw_candidate":0,"ltw_target_source":0,"ltw_distractor_source":0}
    for index,(s,c) in enumerate(zip(state.brain.dendrites,control.brain.dendrites)):
        owner=index//4
        source=(index%4)//2
        for key in ("stw","ltw"):
            delta=abs(getattr(s.dendrite,key)-getattr(c.dendrite,key))
            sums[key+("_target_source" if source==target
                      else "_distractor_source")]+=delta
            if source==target and owner==winner:
                sums[key+"_candidate"]+=delta
    return sums


def run_episode(seed,target,delay,which_mapping,receptors=None,reactions=None):
    """Five branches of ONE reference decision; maps only affect feedback sign."""
    if type(seed) is not int or seed<0 or target not in (0,1) or delay not in DELAYS:
        raise ValueError("invalid episode parameters")
    if which_mapping not in ("A","B"):
        raise ValueError("unknown evaluation mapping")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    mapping=MAPPING_A if which_mapping=="A" else MAPPING_B
    brain=C1ContextBrain(seed)
    trunk,action=common_trunk(brain,target,receptors,reactions)
    good=None if action is None else action==mapping[target]
    branches={}
    full_chem={}
    states={}
    horizon=delay+1+EXTRA_DISTRACTOR_TICKS

    for mode in MODES:
        state=trunk
        stats=_counters()
        injection_index=(0 if mode.startswith("E")
                         else delay if mode.startswith("L") else None)
        delivered=0
        chem_states=[]
        for index in range(horizon):
            if injection_index is not None and index==injection_index and good is not None:
                state=add_environment_precursors(state,correct=good)
                delivered+=1
            state,_=witness_step(
                brain,state,1-target,receptors,reactions,
                gain=GAIN[mode],selected_action=action,target=target,
                counters=stats,
            )
            chem_states.append(state.chemistry)
        states[mode]=state
        full_chem[mode]=tuple(chem_states)
        total=stats["effect_total"]
        stats["fraction_target_source"]=(stats["effect_target_source"]/total
                                          if total>0 else None)
        stats["injected_at_post_target_tick"]=injection_index if good is not None else None
        stats["delivered_events"]=delivered
        stats["final_pool_selected"]={
            str(id_):state.chemistry.pool[id_] for id_ in (17,33,1,49,50,51)
        }
        stats["end_tick"]=state.brain.tick
        # Readout has no learning and no new environmental feedback.
        for _ in range(READOUT_TICKS):
            state,last_action=witness_step(
                brain,state,target,receptors,reactions,
                gain=GAIN[mode],learn=False,
            )
        stats["final_readout_action"]=last_action
        stats["final_readout_correct"]=int(last_action==mapping[target])
        branches[mode]=stats

    # Crucial: the upstream biochemical trajectory is independent of
    # artificial neuronal gain at fixed delivery time. Compare FULL states.
    if full_chem["E1"]!=full_chem["E4"] or full_chem["L1"]!=full_chem["L4"]:
        raise AssertionError("neural gain illegally altered upstream chemistry")
    for mode in MODES:
        branches[mode].update(source_memory_distance(
            states[mode],states["N"],target,action
        ))
    if good is None:
        if any(branches[mode]["delivered_events"] for mode in MODES):
            raise AssertionError("no-action episode received feedback")
    else:
        if branches["N"]["delivered_events"]!=0 or any(
                branches[m]["delivered_events"]!=1 for m in MODES[1:]):
            raise AssertionError("bad number of precursor events")
    assert all(branches[m]["end_tick"]==trunk.brain.tick+horizon
               for m in MODES)
    return {
        "seed":seed,"target":target,"delay":delay,
        "mapping":which_mapping,"reference_action":action,
        "reference_correct":good,
        "reference_tick":trunk.brain.tick,"horizon":horizon,
        "branches":branches,
        "chemical_trajectories_matched_for_gain":True,
    }


def _percentile(sorted_data,percent):
    index=(len(sorted_data)-1)*percent
    low=int(index)
    high=min(low+1,len(sorted_data)-1)
    return sorted_data[low]+(sorted_data[high]-sorted_data[low])*(index-low)


def paired_bootstrap(episodes,mode_a,mode_b,metric,*,seed=BOOTSTRAP_SEED,
                     replicas=BOOTSTRAP_REPS):
    """Seed-clustered paired estimates; omitted undefined ratios stay missing."""
    by_seed={}
    for ep in episodes:
        a=ep["branches"][mode_a][metric]
        b=ep["branches"][mode_b][metric]
        if a is not None and b is not None:
            by_seed.setdefault(ep["seed"],[]).append(a-b)
    per_seed={key:statistics.mean(values) for key,values in by_seed.items()}
    seed_means=list(per_seed.values())
    if not seed_means:
        return {"paired_episodes":0,"n_seeds":0,"mean":None,"ci95":None}
    rng=random.Random(seed)
    sampled=[]
    for _ in range(replicas):
        sample=[seed_means[rng.randrange(len(seed_means))]
                for _ in seed_means]
        sampled.append(statistics.mean(sample))
    sampled.sort()
    return {
        "paired_episodes":sum(len(x) for x in by_seed.values()),
        "n_seeds":len(seed_means),
        "mean":statistics.mean(seed_means),
        "ci95":[_percentile(sampled,0.025),_percentile(sampled,0.975)],
        "per_seed":{str(key):per_seed[key] for key in sorted(per_seed)},
    }


def run_all(seeds=SEEDS):
    if not isinstance(seeds,tuple) or not seeds or any(
            type(seed) is not int or seed<0 for seed in seeds):
        raise ValueError("nonempty tuple of nonnegative seeds required")
    receptors,reactions=selected_genes()
    rows=[
        run_episode(seed,target,delay,label,receptors,reactions)
        for seed in seeds for target in (0,1) for delay in DELAYS
        for label,_mapping in MAPS
    ]
    contrasts={
        "gain_early_effect_candidate_E4_minus_E1":
            paired_bootstrap(rows,"E4","E1","effect_candidate"),
        "gain_late_effect_candidate_L4_minus_L1":
            paired_bootstrap(rows,"L4","L1","effect_candidate"),
        "gain_early_stw_candidate_E4_minus_E1":
            paired_bootstrap(rows,"E4","E1","stw_candidate"),
        "gain_late_stw_candidate_L4_minus_L1":
            paired_bootstrap(rows,"L4","L1","stw_candidate"),
        "timing_gain1_target_fraction_E1_minus_L1":
            paired_bootstrap(rows,"E1","L1","fraction_target_source"),
        "timing_gain4_target_fraction_E4_minus_L4":
            paired_bootstrap(rows,"E4","L4","fraction_target_source"),
        "timing_gain1_candidate_effect_E1_minus_L1":
            paired_bootstrap(rows,"E1","L1","effect_candidate"),
        "timing_gain4_candidate_effect_E4_minus_L4":
            paired_bootstrap(rows,"E4","L4","effect_candidate"),
    }
    return {
        "protocol":"E09_02I_I3B1_RAMAS_QUIMICAS_PRE_REGISTRO-v1",
        "study_type":"paired mechanistic one-pulse N, not learning benchmark",
        "seeds":list(seeds),
        "episode_count":len(rows),
        "n_units":6,"n_dendrites":8,
        "rates_synthetic":40,"dose":PRECURSOR_DOSE,
        "modes":list(MODES),"warmup_ticks":len(WARMUP),
        "target_ticks":TARGET_TICKS,
        "post_arrival_distractor_ticks":EXTRA_DISTRACTOR_TICKS,
        "readout_ticks":READOUT_TICKS,
        "bootstrap_replicates":BOOTSTRAP_REPS,
        "bootstrap_seed":BOOTSTRAP_SEED,
        "missing_reference_actions":sum(ep["reference_action"] is None
                                        for ep in rows),
        "signs":{
            "correct":sum(ep["reference_correct"] is True for ep in rows),
            "incorrect":sum(ep["reference_correct"] is False for ep in rows),
            "none":sum(ep["reference_correct"] is None for ep in rows),
        },
        "contrasts":contrasts,
        "per_episode":rows,
        "gate_wiring":"PASS: witness and full upstream chemistry equality asserted",
        "gate_behavioral_G05_G09":"NOT EVALUATED; I3 remains negative",
        "limitations":(
            "Artificial gain4, synthetic rate40, single event and short readout, "
            "no historical dose, rate or automatic neural emitter mapping; "
            "candidate source/decision classification is not causal proof."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    payload=json.dumps(run_all(),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(payload,encoding="utf-8")
    print(payload,end="")


if __name__=="__main__":
    main()
