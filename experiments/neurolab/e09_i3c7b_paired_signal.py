"""I3c.7b: same-decision sensitivity of C1 microbrain to direct vs metabolic feedback.

PRE-REGISTERED BEFORE CODE:
 docs/neurolab/E09_02I_I3C7B_CONTRASTE_SENAL_PRE_REGISTRO.md

Four arms share a single *unreinforced* decision at tick4:
N normal unreinforced, M chemical precursor80 (tick5), C single direct255
neural pulse (tick7), F same full chemical trajectory as M but frozen.
These are NOT matched feedback magnitudes, and NOT G05 learning proof.
No changes to original neural, genetic, receptor, reaction or migration code.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import random
import statistics

from .c1_context_brain import C1ContextBrain
from .c1_runtime_math import (
    RuleInputs, evaluate as evaluate_rule, neuron_output,
    dendrite_signal, DECISION_RULE,
)
from .c1_synapse_integrated import (
    C1SynapticInput, DECISION_EXCITATORY_GENE,
    DECISION_INHIBITORY_GENE, update_c1_synapse,
)
from .e09_context_protocol import (
    MAPPING_A, MAPPING_B, REWARD, PUNISHMENT,
)
from .e09_coupled_brain import CoupledState, initial_coupled
from .e09_i3_metabolic_protocol import (
    RATES, PRECURSOR_DOSE, selected_genes, add_environment_precursors,
)
from .e09_i3b1_forks import witness_step
from .e09_chemical_bridge import chemical_bridge_tick
from .e09_pool_decay import decay_pool

SEEDS = tuple(range(1500,1520))
RESERVED_CONFIRMATION_SEEDS = tuple(range(1400,1420))
TARGETS = (0,1)
MAPS = {"A":MAPPING_A,"B":MAPPING_B}
MODES = ("N","M","C","F")
TRUNK_TICK = 4
END_TICK = 128
CHEMICAL_PRECURSOR_TICK = 5
DIRECT_NEURAL_PULSE_TICK = 7
READOUT_TICKS = (7,9,16,128)
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 60517


def _digest(data):
    return sha256(json.dumps(
        data,sort_keys=True,separators=(",",":")
    ).encode("utf-8")).hexdigest()


def initial_trunk(seed,target,receptors,reactions):
    if type(seed) is not int or seed not in SEEDS or target not in TARGETS:
        raise ValueError("seed or target not in I3c7b development cohort")
    brain=C1ContextBrain(seed)
    state=initial_coupled(brain,receptors)
    action=None
    for _ in range(TRUNK_TICK):
        state,action=witness_step(
            brain,state,target,receptors,reactions,gain=1,learn=True,
        )
    if (state.brain.tick!=TRUNK_TICK or state.chemistry.tick!=TRUNK_TICK
        or len(state.brain.dendrites)!=8
        or sum(s.strength>0 for s in state.brain.dendrites)!=8):
        raise AssertionError("pre-feedback trunk must have eight active dendrites")
    return brain,state,action


def _class_inputs_and_scores(neural):
    values=[]
    scores=[]
    for owner in (0,1):
        exc=tuple(neural.dendrites[(owner*2+src)*2].dendrite.stw
                  for src in (0,1))
        inh=tuple(neural.dendrites[(owner*2+src)*2+1].dendrite.stw
                  for src in (0,1))
        type0=dendrite_signal(
            neural.concept_outputs,exc,attenuation=128
        ).type_value
        type1=dendrite_signal(
            neural.concept_outputs,inh,attenuation=128
        ).type_value
        values.append((type0,type1))
        scores.append(neuron_output(evaluate_rule(
            DECISION_RULE,RuleInputs(
                state=neural.neuron_states[owner],
                type0=type0,type1=type1,
            )),0))
    return values,scores


def _numeric_oracle(old,chemicals):
    predicted=[]
    effects=[]
    for i,syn in enumerate(old.dendrites):
        gene=(DECISION_INHIBITORY_GENE if i%2
              else DECISION_EXCITATORY_GENE)
        tr=update_c1_synapse(
            syn,gene,C1SynapticInput(
                source_output=old.concept_outputs[(i%4)//2],
                owner_state=old.neuron_states[i//4],
                owner_output=old.neuron_outputs[i//4],
                chemicals=chemicals,
            ),tick=old.tick+1,
        )
        predicted.append(tr.after)
        effects.append(tr.numeric.reinforcement_effect)
    return tuple(predicted),tuple(effects)


def _readout(brain,state,target,mapping,receptors,reactions):
    frozen=state.brain.dendrites
    sample=state
    action=None
    for _ in range(4):
        sample,action=witness_step(
            brain,sample,target,receptors,reactions,gain=1,learn=False,
        )
    if sample.brain.dendrites!=frozen:
        raise AssertionError("frozen readout changed dendrite state")
    return {"action":action,"correct":int(action==mapping[target])}


def _run_branch(brain,trunk,action,target,mapping,mode,receptors,reactions):
    if mode not in MODES:
        raise ValueError("unknown I3c7b branch")
    correct=(None if action is None else bool(action==mapping[target]))
    neural_pulse=(REWARD if correct else PUNISHMENT) if correct is not None else None
    state=trunk
    frames=[]
    readouts={}
    delivered=0
    total_effect=[0]*8
    chem_auc=[0,0]
    strength_positive_stw_at_least5_max=0
    max_live_stw=0
    first_input_positive_tick=None
    first_type_positive_tick=None
    chem_hash=sha256()
    frozen_dendrites=trunk.brain.dendrites
    chem_checkpoints={}
    for index in range(END_TICK-TRUNK_TICK):
        tick=TRUNK_TICK+index+1
        if mode in ("M","F") and tick==CHEMICAL_PRECURSOR_TICK:
            if correct is not None:
                state=add_environment_precursors(
                    state,correct=correct,dose=PRECURSOR_DOSE,
                )
                delivered+=1
        old=state
        read_chem=old.chemistry.decision_chem
        effective=(
            neural_pulse if mode=="C" and tick==DIRECT_NEURAL_PULSE_TICK
            and neural_pulse is not None else read_chem
        )
        if mode=="C" and tick==DIRECT_NEURAL_PULSE_TICK and neural_pulse is not None:
            delivered+=1
        types,expected_scores=_class_inputs_and_scores(old.brain)
        if first_type_positive_tick is None and any(x>0 for row in types for x in row):
            first_type_positive_tick=tick
        predicted,effects=_numeric_oracle(old.brain,effective)
        trial=brain.step(old.brain,1-target,effective,learn=(mode!="F"))
        if trial.scores!=tuple(expected_scores):
            raise AssertionError("score and original Decision SVRule disagree")
        if mode=="F":
            if trial.after.dendrites!=old.brain.dendrites:
                raise AssertionError("frozen branch updated weights")
            actual_effects=(0,)*8
        else:
            if trial.after.dendrites!=predicted:
                raise AssertionError("independent per-slot C1 gene numeric oracle mismatch")
            actual_effects=effects
        for i,x in enumerate(actual_effects):
            total_effect[i]+=x
        if mode!="C":
            state,next_action=witness_step(
                brain,old,1-target,receptors,reactions,
                gain=1,learn=(mode!="F"),
            )
            if state.brain!=trial.after or next_action!=trial.action:
                raise AssertionError("original witness_step disagrees with numeric oracle")
        else:
            ct=chemical_bridge_tick(old.chemistry,(),receptors,reactions)
            pool=decay_pool(ct.after.pool,RATES,old.chemistry.tick)
            state=CoupledState(trial.after,replace(ct.after,pool=pool))
        if state.brain.tick!=tick or state.chemistry.tick!=tick:
            raise AssertionError("misaligned neural and chemical tick")
        if mode=="F" and state.brain.dendrites!=frozen_dendrites:
            raise AssertionError("F dendrites drifted after tick4")
        if first_input_positive_tick is None and (effective[0]>0 or effective[1]>0):
            first_input_positive_tick=tick
        for c in range(2):
            chem_auc[c]+=effective[c]
        live=sum(s.strength>0 and s.dendrite.stw>=5
                 for s in state.brain.dendrites)
        strength_positive_stw_at_least5_max=max(
            strength_positive_stw_at_least5_max,live
        )
        max_live_stw=max(max_live_stw,max(
            (s.dendrite.stw for s in state.brain.dendrites if s.strength>0),
            default=0,
        ))
        chem_hash.update(json.dumps(
            asdict(state.chemistry),sort_keys=True,separators=(",",":")
        ).encode("utf-8"))
        if tick in READOUT_TICKS:
            readouts[str(tick)]=_readout(
                brain,state,target,mapping,receptors,reactions,
            )
            chem_checkpoints[str(tick)]={
                "chemical_sha256":_digest(asdict(state.chemistry)),
                "dendrite_sha256":_digest([
                    asdict(s) for s in state.brain.dendrites
                ]),
            }
        frames.append({
            "tick":tick,
            "chem_read":list(effective),
            "chem_from_pool":list(read_chem),
            "class_type_inputs":[list(x) for x in types],
            "scores":list(trial.scores),
            "action":trial.action,
            "effects":list(actual_effects),
            "pre_strength_positive":sum(s.strength>0 for s in old.brain.dendrites),
            "post_strength_positive":sum(
                s.strength>0 for s in state.brain.dendrites
            ),
            "post_live_stw":[s.dendrite.stw if s.strength>0 else None
                             for s in state.brain.dendrites],
            "post_ltw":[s.dendrite.ltw for s in state.brain.dendrites],
        })
    if len(frames)!=124 or len(readouts)!=4:
        raise AssertionError("missing preregistered timing points")
    expected_deliveries=int(mode in ("M","C","F") and action is not None)
    if delivered!=expected_deliveries:
        raise AssertionError("incorrect reward cardinality")
    target_effect=sum(x for i,x in enumerate(total_effect)
                      if (i%4)//2==target)
    distractor_effect=sum(total_effect)-target_effect
    return {
        "mode":mode,
        "delivered":delivered,
        "first_positive_neural_chem_tick":first_input_positive_tick,
        "first_positive_decision_type_tick":first_type_positive_tick,
        "total_effect":sum(total_effect),
        "target_effect":target_effect,
        "distractor_effect":distractor_effect,
        "effect_by_slot":total_effect,
        "chem_auc":chem_auc,
        "max_live_stw":max_live_stw,
        "max_positive_strength_stw_at_least5":strength_positive_stw_at_least5_max,
        "end_strength_positive":sum(
            s.strength>0 for s in state.brain.dendrites
        ),
        "end_ltw_positive_live":sum(
            s.strength>0 and s.dendrite.ltw>0 for s in state.brain.dendrites
        ),
        "chemical_trajectory_sha256":chem_hash.hexdigest(),
        "chem_checkpoints":chem_checkpoints,
        "readouts":readouts,
        "frames":frames,
    }


def run_episode(seed,target,mapping_name,receptors=None,reactions=None):
    if type(seed) is not int or seed not in SEEDS or target not in TARGETS:
        raise ValueError("cohort seed/target invalid")
    if mapping_name not in MAPS:
        raise ValueError("mapping name A/B required")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    brain,trunk,action=initial_trunk(seed,target,receptors,reactions)
    h=_digest({
        "brain":brain.checkpoint(trunk.brain),
        "chemistry":asdict(trunk.chemistry),
    })
    arms={
        m:_run_branch(
            brain,trunk,action,target,MAPS[mapping_name],m,
            receptors,reactions,
        ) for m in MODES
    }
    for a,b in (("M","F"),("N","C")):
        if arms[a]["chemical_trajectory_sha256"]!=arms[b]["chemical_trajectory_sha256"]:
            raise AssertionError(f"{a}/{b} upstream chemistry not perfectly paired")
        for tick in READOUT_TICKS:
            if (arms[a]["chem_checkpoints"][str(tick)]["chemical_sha256"]
                !=arms[b]["chem_checkpoints"][str(tick)]["chemical_sha256"]):
                raise AssertionError("mismatched chemical snapshots")
    for mode in MODES:
        arms[mode]["different_readout_actions_vs_N"]={
            str(t):int(arms[mode]["readouts"][str(t)]["action"]
                       !=arms["N"]["readouts"][str(t)]["action"])
            for t in READOUT_TICKS
        }
        arms[mode]["different_score_ticks_vs_N"]=sum(
            frame["scores"] != control["scores"]
            for frame,control in zip(arms[mode]["frames"],arms["N"]["frames"])
        )
        arms[mode]["different_type_ticks_vs_N"]=sum(
            frame["class_type_inputs"]!=control["class_type_inputs"]
            for frame,control in zip(arms[mode]["frames"],arms["N"]["frames"])
        )
        arms[mode]["first_score_difference_tick"]=next(
            (f["tick"] for f,n in zip(
                arms[mode]["frames"],arms["N"]["frames"]
            ) if f["scores"]!=n["scores"]),None
        )
    return {
        "seed":seed,"target":target,"mapping":mapping_name,
        "trunk_sha256":h,"original_action":action,
        "initial_correct":None if action is None else
           bool(action==MAPS[mapping_name][target]),
        "arms":arms,
    }


def run_seed(seed,receptors=None,reactions=None):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed not in preregistered development cohort")
    if receptors is None or reactions is None:
        receptors,reactions=selected_genes()
    episodes=[
        run_episode(seed,target,label,receptors,reactions)
        for target in TARGETS for label in ("A","B")
    ]
    for target in TARGETS:
        a,b=[ep for ep in episodes if ep["target"]==target]
        if a["trunk_sha256"]!=b["trunk_sha256"] or a["original_action"]!=b["original_action"]:
            raise AssertionError("mapping leaked to pre-feedback trunk or decision")
    return {"seed":seed,"episodes":episodes}


def _cluster_ci(rows,a,b,metric):
    # Same four correlated mapping/context coordinates per original seed.
    values=[]
    for row in rows:
        diffs=[]
        for ep in row["episodes"]:
            x,y=ep["arms"][a][metric],ep["arms"][b][metric]
            if x is not None and y is not None:
                diffs.append(x-y)
        if diffs:
            values.append(statistics.mean(diffs))
    if not values:
        return {"n_seeds":0,"mean":None,"ci95":None}
    rng=random.Random(BOOTSTRAP_SEED)
    draws=sorted(
        statistics.mean(rng.choice(values) for _ in values)
        for _ in range(BOOTSTRAP_REPS)
    )
    return {
        "n_seeds":len(values),
        "mean":statistics.mean(values),
        "ci95":[draws[int(0.025*BOOTSTRAP_REPS)],
                draws[int(0.975*BOOTSTRAP_REPS)-1]],
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds,tuple) or not seeds
            or any(type(x) is not int or x not in SEEDS for x in seeds)
            or len(set(seeds))!=len(seeds)):
        raise ValueError("only a unique subset of frozen development seeds permitted")
    receptors,reactions=selected_genes()
    rows=[run_seed(seed,receptors,reactions) for seed in seeds]
    episodes=[ep for row in rows for ep in row["episodes"]]
    summaries={}
    for mode in MODES:
        arms=[ep["arms"][mode] for ep in episodes]
        summaries[mode]={
            "n_branches":len(arms),
            "delivered":sum(a["delivered"] for a in arms),
            "first_chem_positive_ticks":{
                str(t):sum(a["first_positive_neural_chem_tick"]==t
                           for a in arms)
                for t in (7,8,9,None)
            },
            "effect_total":sum(a["total_effect"] for a in arms),
            "effect_target_total":sum(a["target_effect"] for a in arms),
            "effect_distractor_total":sum(a["distractor_effect"] for a in arms),
            "branches_with_effect":sum(a["total_effect"]>0 for a in arms),
            "branches_with_live_stw_at_least5":sum(
                a["max_positive_strength_stw_at_least5"]>0 for a in arms
            ),
            "branches_with_type_change_vs_N":sum(
                a["different_type_ticks_vs_N"]>0 for a in arms
            ),
            "branches_with_score_change_vs_N":sum(
                a["different_score_ticks_vs_N"]>0 for a in arms
            ),
            "chemical_auc_mean":[
                statistics.mean(a["chem_auc"][c] for a in arms)
                for c in (0,1)
            ],
            "readout_accuracy":{
                str(t):statistics.mean(
                    a["readouts"][str(t)]["correct"] for a in arms
                ) for t in READOUT_TICKS
            },
            "readout_action_changed_vs_N":{
                str(t):sum(a["different_readout_actions_vs_N"][str(t)]
                          for a in arms)
                for t in READOUT_TICKS
            },
            "live_ltw_tick128":sum(a["end_ltw_positive_live"] for a in arms),
            "mean_strength_positive_tick128":statistics.mean(
                a["end_strength_positive"] for a in arms
            ),
        }
    # Add flattened preregistered readout metrics for seed-cluster inference.
    for ep in episodes:
        for mode in MODES:
            arm=ep["arms"][mode]
            for tick in READOUT_TICKS:
                arm[f"readout_{tick}_correct"]=arm["readouts"][str(tick)]["correct"]
                arm[f"readout_{tick}_action_changed_vs_N"]=arm[
                    "different_readout_actions_vs_N"][str(tick)]
    contrast={}
    for a,b in (("C","N"),("M","N"),("C","M"),("M","F")):
        contrast[f"{a}_minus_{b}"]={
            metric:_cluster_ci(rows,a,b,metric)
            for metric in ("total_effect","different_type_ticks_vs_N",
                           "different_score_ticks_vs_N")+
                          tuple(f"readout_{t}_correct" for t in READOUT_TICKS)
        }
    return {
        "protocol":"NL-EXP-I3c7b-v1",
        "study":"one decision and pulse; mechanistic sensitivity only",
        "seeds":list(seeds),
        "n_physical_trunks":2*len(seeds),
        "n_mapping_coordinates":4*len(seeds),
        "n_branches":16*len(seeds),
        "modes":list(MODES),
        "trunk_tick":TRUNK_TICK,
        "end_tick":END_TICK,
        "direct_pulse_tick":DIRECT_NEURAL_PULSE_TICK,
        "precursor_tick":CHEMICAL_PRECURSOR_TICK,
        "synthetic_chemical_dose":PRECURSOR_DOSE,
        "synthetic_pool_rate":RATES[0],
        "readout_ticks":list(READOUT_TICKS),
        "initial_none_actions":sum(
            ep["original_action"] is None for ep in episodes
        ),
        "initial_correct":sum(
            ep["initial_correct"] is True for ep in episodes
        ),
        "summary":summaries,
        "paired_contrasts":contrast,
        "per_seed_sha256":{str(row["seed"]):_digest(row) for row in rows},
        "per_seed":rows,
        "comparison_limits":"C direct255 one tick at7; M precursor80 at5 produces lower, longer CHEM exposure. Their amplitude and biochemical histories are NOT matched. F is frozen and retains strength; its readout is not a perfect behavioral control. No target/label is passed to neural update.",
        "gates":{"software":"PASS if all assertions",
                 "sensitivity":"DESCRIPTIVE_ONLY",
                 "G05":"OPEN","G09":"OPEN","G00H":"OPEN"},
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    result=run_all()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(
            json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",
            encoding="utf-8",
        )
    print(json.dumps({
        k:result[k] for k in (
            "protocol","seeds","n_physical_trunks","n_mapping_coordinates",
            "n_branches","initial_none_actions","initial_correct",
            "summary","paired_contrasts","per_seed_sha256","gates"
        )
    },sort_keys=True))


if __name__=="__main__":
    main()
