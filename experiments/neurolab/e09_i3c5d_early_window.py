"""NeuroLab I3c.5d: fixed-C1 early-feedback timing, with live-strength witness.

PREREGISTERED BEFORE CODE: docs/neurolab/E09_02I_I3C5D_REFUERZO_PRECOZ_PRE_REGISTRO.md
A single decision on tick4, then N/D0/D3 forks, all with identical inputs.
No new neural mechanism, genes, temporal eligibility, gain, migration or tunable rate.
This is an early feasibility probe, NOT a confirmatory G05/G09 success.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import random
import statistics
from pathlib import Path

from .c1_context_brain import C1ContextBrain
from .e09_coupled_brain import initial_coupled
from .e09_i3_metabolic_protocol import selected_genes
from .e09_i3b1_forks import witness_step
from .e09_i3c5a_credit_forks import (
    inspect_synapses, optional_precursor, _distance,
)
from .e09_context_protocol import MAPPING_A, MAPPING_B

SEEDS = tuple(range(1300,1320))
MAPS = {"A": MAPPING_A, "B": MAPPING_B}
TARGETS = (0,1)
MODES = ("N", "D0", "D3")
TRUNK_TICK = 4
END_TICK = 128
SNAPSHOTS = (4,5,6,8,9,10,16,128)
READOUT_TICKS = (9,16,128)
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 60516


def _hash_json(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def shared_trunk(seed, target, receptors, reactions):
    if type(seed) is not int or seed not in SEEDS or target not in TARGETS:
        raise ValueError("invalid seed or target for preregistered cohort")
    brain = C1ContextBrain(seed)
    state = initial_coupled(brain, receptors)
    action = None
    for _ in range(TRUNK_TICK):
        state, action = witness_step(
            brain, state, target, receptors, reactions,
            gain=1, learn=True,
        )
    if state.brain.tick != TRUNK_TICK or state.chemistry.tick != TRUNK_TICK:
        raise AssertionError("tick4 trunk drift")
    return brain, state, action


def _summary_state(state):
    syn = state.brain.dendrites
    return {
        "tick": state.brain.tick,
        "strength_positive":sum(s.strength>0 for s in syn),
        "strength_zero":sum(s.strength==0 for s in syn),
        "stw_positive":sum(s.dendrite.stw>0 for s in syn),
        "ltw_positive":sum(s.dendrite.ltw>0 for s in syn),
        "ltw_positive_with_strength":sum(
            s.strength>0 and s.dendrite.ltw>0 for s in syn
        ),
        "ltw_positive_exhausted":sum(
            s.strength==0 and s.dendrite.ltw>0 for s in syn
        ),
        "strengths":[s.strength for s in syn],
        "stws":[s.dendrite.stw for s in syn],
        "ltws":[s.dendrite.ltw for s in syn],
    }


def _readout(brain, state, target, mapping, receptors, reactions):
    """No state mutation of main learning trace; frozen synapses in clone."""
    after = state
    answer = None
    frozen = state.brain.dendrites
    for _ in range(4):
        after, answer = witness_step(
            brain, after, target, receptors, reactions,
            gain=1, learn=False,
        )
    if after.brain.dendrites != frozen:
        raise AssertionError("holdout readout mutated synapses")
    return {
        "action":answer,
        "correct":int(answer==mapping[target]),
        "end_tick":after.brain.tick,
    }


def _run_branch(brain, initial, action, target, mapping, mode,
                receptors, reactions):
    if mode not in MODES:
        raise ValueError("invalid timing branch")
    injection_index = None if mode=="N" else int(mode[1])
    state=initial
    delivered=0
    frames=[]
    snap={str(TRUNK_TICK):_summary_state(initial)}
    positions={TRUNK_TICK:initial.brain.dendrites}
    readouts={}
    total_effect=[0]*8
    target_effect_active=0
    target_effect_exhausted=0
    distractor_effect_active=0
    distractor_effect_exhausted=0
    candidate_effect_active=0
    candidate_effect_exhausted=0
    per_slot_tick_effects=[]
    chem_auc=[0,0]
    max_chem=[0,0]
    first_chem_positive_tick=None
    first_chem_positive_strength=None
    first_chem_positive_candidate_strength=None
    first_effect_positive_tick=None
    first_effect_positive_strength=None
    chosen_owner=0 if action=="D0" else 1 if action=="D1" else -1
    correct=(None if action is None else bool(action==mapping[target]))

    for offset in range(END_TICK - TRUNK_TICK):
        if offset==injection_index:
            state,n=optional_precursor(state,action,correct)
            delivered+=n
        old=state
        expected,effects,sus=inspect_synapses(old)
        chem=old.chemistry.decision_chem[:2]
        pre=old.brain.dendrites
        eligible=sum(s.strength>0 for s in pre)
        candidate_eligible=sum(
            s.strength>0 for i,s in enumerate(pre)
            if i//4==chosen_owner and (i%4)//2==target
        )
        if first_chem_positive_tick is None and max(chem)>0:
            first_chem_positive_tick=old.brain.tick+1
            first_chem_positive_strength=eligible
            first_chem_positive_candidate_strength=candidate_eligible
        if first_effect_positive_tick is None and any(x>0 for x in effects):
            first_effect_positive_tick=old.brain.tick+1
            first_effect_positive_strength=eligible
        if any(e<0 for e in effects):
            raise AssertionError("negative numerical reinforcement unexpected")
        for c in range(2):
            chem_auc[c]+=chem[c]
            max_chem[c]=max(max_chem[c],chem[c])
        for i,e in enumerate(effects):
            total_effect[i]+=e
            is_target=(i%4)//2==target
            active=pre[i].strength>0
            if is_target and active: target_effect_active+=e
            if is_target and not active: target_effect_exhausted+=e
            if not is_target and active: distractor_effect_active+=e
            if not is_target and not active: distractor_effect_exhausted+=e
            if is_target and i//4==chosen_owner:
                if active: candidate_effect_active+=e
                else: candidate_effect_exhausted+=e
        per_slot_tick_effects.append(list(effects))
        state, _ = witness_step(
            brain,state,1-target,receptors,reactions,
            gain=1,learn=True,
        )
        if state.brain.dendrites!=expected:
            raise AssertionError("independent numeric witness mismatch")
        if state.brain.tick!=TRUNK_TICK+offset+1:
            raise AssertionError("logical clock mismatch")
        if state.brain.tick in SNAPSHOTS:
            snap[str(state.brain.tick)]=_summary_state(state)
            positions[state.brain.tick]=state.brain.dendrites
        if state.brain.tick in READOUT_TICKS:
            readouts[str(state.brain.tick)]=_readout(
                brain,state,target,mapping,receptors,reactions,
            )
        frames.append({
            "tick":state.brain.tick,
            "chem_read":list(chem),
            "pre_strength_positive":eligible,
            "pre_candidate_strength_positive":candidate_eligible,
            "effects":list(effects),
            "sus_positive":sum(x>0 for x in sus),
            "post_strength_positive":sum(s.strength>0
                                         for s in state.brain.dendrites),
        })
    if len(frames)!=124 or not set(map(str,SNAPSHOTS)).issubset(snap):
        raise AssertionError("missing expected comparison windows")
    if delivered!=int(mode!="N" and action is not None):
        raise AssertionError("precursor delivery cardinality incorrect")
    if mode=="N" and (any(x["chem_read"]!=[0,0] for x in frames)
                       or any(any(e>0 for e in x["effects"]) for x in frames)):
        raise AssertionError("neutral arm acquired unexplained chemistry/reward")
    total=sum(total_effect)
    return {
        "mode":mode,
        "injection_tick":TRUNK_TICK+injection_index+1
              if delivered else None,
        "delivered":delivered,
        "chem_auc":chem_auc,
        "max_chem":max_chem,
        "first_chem_positive_tick":first_chem_positive_tick,
        "strength_positive_at_first_chem":first_chem_positive_strength,
        "candidate_strength_positive_at_first_chem":
              first_chem_positive_candidate_strength,
        "first_effect_positive_tick":first_effect_positive_tick,
        "strength_positive_at_first_effect":first_effect_positive_strength,
        "effect_by_slot":total_effect,
        "effect_target_active":target_effect_active,
        "effect_target_exhausted":target_effect_exhausted,
        "effect_distractor_active":distractor_effect_active,
        "effect_distractor_exhausted":distractor_effect_exhausted,
        "effect_candidate_active":candidate_effect_active,
        "effect_candidate_exhausted":candidate_effect_exhausted,
        "target_fraction_raw":(sum(total_effect[i] for i in range(8)
             if (i%4)//2==target)/total if total else None),
        "snapshots":snap,
        "readouts":readouts,
        "frames":frames,
    },positions,per_slot_tick_effects


def run_episode(seed,target,mapping_name,receptors=None,reactions=None):
    if type(seed) is not int or seed not in SEEDS or target not in TARGETS:
        raise ValueError("invalid experimental coordinates")
    if mapping_name not in MAPS:
        raise ValueError("mapping outside preregistered A/B")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    brain,trunk,action=shared_trunk(seed,target,receptors,reactions)
    checkpoint=_hash_json(brain.checkpoint(trunk.brain))
    trunk_snapshot=_summary_state(trunk)
    if trunk_snapshot["strength_positive"]!=8:
        raise AssertionError("tick4 strength-positive availability not met")
    results={}
    synapses={}
    effects={}
    for mode in MODES:
        results[mode],synapses[mode],effects[mode]=_run_branch(
            brain,trunk,action,target,MAPS[mapping_name],mode,
            receptors,reactions,
        )
    for mode in MODES:
        data=results[mode]
        num=data["effect_by_slot"]
        reference=results["N"]["effect_by_slot"]
        attributable=[max(0,x-y) for x,y in zip(num,reference)]
        total=sum(attributable)
        candidate_owner=0 if action=="D0" else 1 if action=="D1" else -1
        target_attributed=sum(
            attributable[i] for i in range(8) if (i%4)//2==target
        )
        candidate_attributed=sum(
            attributable[i] for i in range(8)
            if (i%4)//2==target and i//4==candidate_owner
        )
        data["effect_target_fraction_incremental"]=(
            target_attributed/total if total else None
        )
        data["effect_candidate_fraction_incremental"]=(
            candidate_attributed/total if total else None
        )
        data["effect_incremental_total"]=total
        data["strength_available_when_chem_arrived"]=(
            (data["strength_positive_at_first_chem"]>0)
            if data["strength_positive_at_first_chem"] is not None else None
        )
        data["readout9_correct"]=data["readouts"]["9"]["correct"]
        data["readout16_correct"]=data["readouts"]["16"]["correct"]
        data["readout128_correct"]=data["readouts"]["128"]["correct"]
        data["distances"]={
            str(t):_distance(
                synapses[mode][t],synapses["N"][t],target
            ) for t in SNAPSHOTS if t!=TRUNK_TICK
        }
        # raw observed increments are preserved for full inspection; no post hoc cuts
        data["effect_trace"]=effects[mode]
        if mode=="N" and total:
            raise AssertionError("no-pulse incremental effect must be zero")
    return {
        "seed":seed,
        "target":target,
        "mapping":mapping_name,
        "trunk_checkpoint_sha256":checkpoint,
        "trunk":trunk_snapshot,
        "reference_action":action,
        "reference_correct":None if action is None else
                 bool(action==MAPS[mapping_name][target]),
        "branches":results,
    }


def _paired_ci(rows, mode_a, mode_b, metric):
    by_seed={}
    for row in rows:
        for ep in row["episodes"]:
            a=ep["branches"][mode_a][metric]
            b=ep["branches"][mode_b][metric]
            if a is None or b is None:
                continue
            by_seed.setdefault(row["seed"],[]).append(a-b)
    seed_means=[statistics.mean(by_seed[s]) for s in sorted(by_seed)]
    if not seed_means:
        return {"n_seeds":0,"mean":None,"ci95":None}
    rng=random.Random(BOOTSTRAP_SEED)
    draws=sorted(statistics.mean(
        rng.choice(seed_means) for _ in seed_means
    ) for _ in range(BOOTSTRAP_REPS))
    return {
        "n_seeds":len(seed_means),
        "mean":statistics.mean(seed_means),
        "ci95":[draws[int(0.025*BOOTSTRAP_REPS)],
                draws[int(0.975*BOOTSTRAP_REPS)-1]],
    }


def run_seed(seed,receptors=None,reactions=None):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed outside fixed development cohort")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    episodes=[run_episode(seed,t,name,receptors,reactions)
              for t in TARGETS for name in ("A","B")]
    for target in TARGETS:
        variants=[ep for ep in episodes if ep["target"]==target]
        if variants[0]["trunk_checkpoint_sha256"] != variants[1]["trunk_checkpoint_sha256"]:
            raise AssertionError("mapping altered pre-feedback neural state")
        if variants[0]["reference_action"] != variants[1]["reference_action"]:
            raise AssertionError("evaluator altered decision before feedback")
    return {"seed":seed,"episodes":episodes}


def run_all(seeds=SEEDS):
    if (not isinstance(seeds,tuple) or not seeds
            or len(set(seeds))!=len(seeds)
            or any(type(s) is not int or s not in SEEDS for s in seeds)):
        raise ValueError("unique subset of predefined development seeds needed")
    receptors,reactions=selected_genes()
    rows=[run_seed(s,receptors,reactions) for s in seeds]
    episodes=[ep for row in rows for ep in row["episodes"]]
    means={}
    for mode in MODES:
        xs=[ep["branches"][mode] for ep in episodes]
        available=[v["strength_available_when_chem_arrived"] for v in xs
                   if v["strength_available_when_chem_arrived"] is not None]
        fractions=[v["effect_target_fraction_incremental"] for v in xs
                   if v["effect_target_fraction_incremental"] is not None]
        means[mode]={
            "deliveries":sum(x["delivered"] for x in xs),
            "first_chem_arrivals_with_positive_strength":
                sum(available),
            "first_chem_arrival_count":len(available),
            "fraction_with_strength_at_chem":
                sum(available)/len(available) if available else None,
            "target_fraction_mean":
                statistics.mean(fractions) if fractions else None,
            "target_fraction_n":len(fractions),
            "effect_target_active_total":
                sum(x["effect_target_active"] for x in xs),
            "effect_target_exhausted_total":
                sum(x["effect_target_exhausted"] for x in xs),
            "effect_distractor_active_total":
                sum(x["effect_distractor_active"] for x in xs),
            "effect_distractor_exhausted_total":
                sum(x["effect_distractor_exhausted"] for x in xs),
            "auc_mean":[statistics.mean(x["chem_auc"][i] for x in xs)
                        for i in (0,1)],
            "strength_positive_mean_tick9":
                statistics.mean(x["snapshots"]["9"]["strength_positive"] for x in xs),
            "strength_positive_mean_tick128":
                statistics.mean(x["snapshots"]["128"]["strength_positive"] for x in xs),
            "ltw_positive_with_strength_tick128_total":
                sum(x["snapshots"]["128"]["ltw_positive_with_strength"] for x in xs),
            "readout_accuracy":{
                str(t):statistics.mean(x[f"readout{t}_correct"] for x in xs)
                for t in READOUT_TICKS
            },
        }
    contrasts={
        f"{a}_minus_{b}":{
            f"readout{t}_accuracy":_paired_ci(rows,a,b,f"readout{t}_correct")
            for t in READOUT_TICKS
        } for a,b in (("D0","N"),("D3","N"),("D0","D3"))
    }
    for a,b in (("D0","N"),("D3","N"),("D0","D3")):
        contrasts[f"{a}_minus_{b}"]["target_fraction_incremental"]=_paired_ci(
            rows,a,b,"effect_target_fraction_incremental"
        )
    return {
        "protocol":"NL-EXP-I3c5d-v1",
        "study_type":"single pulse before synaptic exhaustion; diagnostic not G05",
        "seeds":list(seeds),
        "n_unique_trunks":2*len(rows),
        "n_mapping_coordinates":4*len(rows),
        "n_branches":12*len(rows),
        "mapping_labels":list(MAPS),
        "modes":list(MODES),
        "decision_tick":TRUNK_TICK,
        "last_tick":END_TICK,
        "synthetic_dose":80,
        "synthetic_decay_rate":40,
        "no_extra_gain_or_migration":True,
        "missing_initial_actions":sum(
            ep["reference_action"] is None for ep in episodes
        ),
        "reference_correct_counts":dict(Counter(
            str(ep["reference_correct"]) for ep in episodes
        )),
        "summary":means,
        "paired_contrasts":contrasts,
        "per_seed_sha256":{str(row["seed"]):_hash_json(row) for row in rows},
        "gates":{"software":"PASS if all assertions",
                 "G05":"OPEN","G09":"OPEN","G00H":"OPEN"},
        "limitations":"One decision/pulse only; exposure timing differences not isolated from coincidence; holdout readout is not sustained learning or C1 fidelity.",
        "per_seed":rows,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=run_all()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,sort_keys=True,
                          separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in (
        "protocol","seeds","n_unique_trunks","n_mapping_coordinates",
        "n_branches","missing_initial_actions","reference_correct_counts",
        "summary","paired_contrasts","per_seed_sha256","gates"
    )},sort_keys=True))


if __name__=="__main__":
    main()
