"""NeuroLab I3c.7i: causal local STW lesions at hash-verified old checkpoints.

PRE-REGISTERED after prior I3c7h outcome, before any lesions:
 docs/neurolab/E09_02I_I3C7I_ABLACION_LOCAL_PRE_REGISTRO.md

Pure diagnostics: SAME original C1ContextBrain, same original 20 seeds;
no new learning, genes, neurons, metabolic tuning or migration. A single
slot's STW is zeroed in a cloned checkpoint for a 8-tick frozen readout.
A local action change indicates necessity of THAT input in THAT state,
NOT causal assignment of historical feedback to that synapse.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import argparse
import json
import random
import statistics

from .c1_context_brain import C1ContextBrain, ContextBrainState
from .e09_context_protocol import (
    ZERO, MAPPING_A, MAPPING_B, blocks, BLOCK_TICKS,
)
from .e09_coupled_brain import initial_coupled
from .e09_i3_metabolic_protocol import selected_genes
from .e09_i3c7e_loss_factorial import ArmState,run_phase
from .e09_i3c7h_contingency_permutation import (
    SEEDS,MODES as SOURCE_MODES,digest,
    run_seed as original_run_seed, event_tape_from_original,
    context_stratified_permutation, _run_external_tape,
)

PROTOCOL="NL-AUDIT-I3c7i-v1"
EVALUATED_MODES=("B","P")
PHASES=(("first",10000,MAPPING_A),("reversed",20000,MAPPING_B))
PROBE_CONTEXTS=(0,1)
PROBE_TICKS=8
STEADY_START_INDEX=2
N_SLOTS=8
MIN_ALL_ZERO_EFFECTIVE_SEEDS=12
MIN_B_INVERTED_BASELINE_ACCURACY=.65
BOOTSTRAP_REPS=2000
BOOTSTRAP_SEED=60521
MANIFEST_PATH=(
    Path(__file__).resolve().parents[2]/
    "docs/neurolab/resultados/e09i3c7h_resumen_y_hashes.json"
)
EXPECTED_SOURCE_JSON_SHA256=(
    "d723c4a590c0428e13b175c39cd9028c69ed5b714d000f46ada61717eebe925e"
)


def load_original_manifest():
    data=json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if (data.get("protocol")!="NL-EXP-I3c7h-v1"
            or data.get("full_json_sha256")!=EXPECTED_SOURCE_JSON_SHA256
            or data.get("seeds")!=list(SEEDS)
            or len(data.get("per_seed_sha256",{}))!=20):
        raise AssertionError("original I3c7h manifest missing or changed")
    for s in SEEDS:
        h=data["per_seed_sha256"].get(str(s))
        if not isinstance(h,str) or len(h)!=64:
            raise AssertionError("incomplete prior per-seed source SHA")
    return data


def checkpoint_replay(seed,original=None):
    """Reconstruct B/P only from existing source runner, no new mechanism."""
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("unknown I3c7h development seed")
    if original is None:
        original=original_run_seed(seed)
    if original.get("seed")!=seed:
        raise AssertionError("original seed ID mismatch")
    receptors,reactions=selected_genes()
    brain=C1ContextBrain(seed)
    states={m:ArmState(initial_coupled(brain,receptors)) for m in EVALUATED_MODES}
    checkpoints={}
    for i,(phase,salt,mapping) in enumerate(PHASES):
        seq=blocks(seed,salt,32)
        reference,metrics=run_phase(
            brain,states["B"],seq,mapping,"M0",receptors,reactions,
            training=True,
        )
        tape=event_tape_from_original(metrics)
        contexts=tuple(c for block in seq for c in (block,)*BLOCK_TICKS)
        p_tape=context_stratified_permutation(tape,contexts,seed,i)
        p_state,p_observed=_run_external_tape(
            brain,states["P"],seq,mapping,p_tape,"P",receptors,reactions,
        )
        states["B"]=reference
        states["P"]=p_state
        checkpoint_modes={}
        for mode in EVALUATED_MODES:
            state=states[mode]
            expected=original["phases"][phase]["training"][mode][
                "end_state_sha256"]
            actual=digest(asdict(state.coupled))
            if actual!=expected:
                raise AssertionError(
                    f"checkpoint SHA not original for seed{seed}/{phase}/{mode}"
                )
            checkpoint_modes[mode]=state.coupled.brain
        if len(checkpoint_modes["B"].dendrites)!=N_SLOTS:
            raise AssertionError("original typed C1 eight-slot topology changed")
        if (p_observed["end_state_sha256"]
            !=original["phases"][phase]["training"]["P"][
                "end_state_sha256"]):
            raise AssertionError("original P replay does not match")
        checkpoints[phase]=checkpoint_modes
    return brain,checkpoints


def clone_stw_mask(state,indices):
    if not isinstance(state,ContextBrainState):
        raise TypeError("typed C1 neural state required")
    indices=tuple(indices)
    if (len(set(indices))!=len(indices)
            or any(type(i) is not int or i not in range(N_SLOTS) for i in indices)):
        raise ValueError("only unique existing C1 slot indices allowed")
    original=state.dendrites
    out=tuple(
        replace(s,dendrite=replace(
            s.dendrite,stw=(0 if i in indices else s.dendrite.stw),
        )) for i,s in enumerate(original)
    )
    changed=replace(state,dendrites=out)
    if (changed.neuron_states!=state.neuron_states
            or changed.neuron_outputs!=state.neuron_outputs
            or changed.concept_outputs!=state.concept_outputs
            or changed.tick!=state.tick
            or any(a.strength!=b.strength
                   or a.dendrite.ltw!=b.dendrite.ltw
                   or a.dendrite.susceptibility!=b.dendrite.susceptibility
                   for a,b in zip(original,out))):
        raise AssertionError("intervention changed other neuronal quantities")
    return changed


def microprobe(brain,state,context):
    if not isinstance(brain,C1ContextBrain):
        raise TypeError("C1ContextBrain required")
    if context not in PROBE_CONTEXTS:
        raise ValueError("one of two fixed contexts required")
    original_weights=state.dendrites
    current=state
    trajectory=[]
    for t in range(PROBE_TICKS):
        step=brain.step(current,context,ZERO,learn=False)
        if step.after.dendrites!=original_weights:
            raise AssertionError("diagnostic probe modified its weights")
        if t==0:
            # Under learn=False, chemistry cannot change Decision scores
            # and no synaptic rules are evaluated. Original source oracle.
            high=brain.step(current,context,(255,255,255,255),learn=False)
            if (step.action!=high.action or step.scores!=high.scores
                    or step.after!=high.after):
                raise AssertionError("frozen assay responds to chemical route")
        trajectory.append({
            "step":t+1,
            "action":step.action,
            "scores":list(step.scores),
        })
        current=step.after
    return trajectory


def slot_classification(slot,context,mapping):
    if type(slot) is not int or slot not in range(N_SLOTS):
        raise ValueError("known slot0..7 required")
    owner=slot//4
    source=(slot%4)//2
    cls="inhibitory" if slot%2 else "excitatory"
    desired_owner=0 if mapping[context]=="D0" else 1
    aligned=(source==context and (
        (cls=="excitatory" and owner==desired_owner)
        or (cls=="inhibitory" and owner!=desired_owner)
    ))
    return {
        "owner":owner,"source":source,"class":cls,
        "aligned_to_current_mapping":aligned,
    }


def _comparison(reference,altered,mapping,context):
    if len(reference)!=PROBE_TICKS or len(altered)!=PROBE_TICKS:
        raise AssertionError("probe length must be identical")
    stats={
        "action_changed_steady":0,
        "score_changed_steady":0,
        "lost_correct_steady":0,
        "gained_correct_steady":0,
        "base_correct_steady":0,
        "altered_correct_steady":0,
    }
    for old,new in zip(reference[STEADY_START_INDEX:],
                       altered[STEADY_START_INDEX:]):
        base_correct=old["action"]==mapping[context]
        new_correct=new["action"]==mapping[context]
        stats["action_changed_steady"]+=int(old["action"]!=new["action"])
        stats["score_changed_steady"]+=int(old["scores"]!=new["scores"])
        stats["lost_correct_steady"]+=int(base_correct and not new_correct)
        stats["gained_correct_steady"]+=int(not base_correct and new_correct)
        stats["base_correct_steady"]+=int(base_correct)
        stats["altered_correct_steady"]+=int(new_correct)
    if stats["base_correct_steady"]-stats["altered_correct_steady"]!=(
        stats["lost_correct_steady"]-stats["gained_correct_steady"]
    ):
        raise AssertionError("score/error directions inconsistent")
    return stats


def one_checkpoint_context(brain,state,context,mapping):
    original_hash=digest(asdict(state))
    reference=microprobe(brain,state,context)
    sham=microprobe(brain,clone_stw_mask(state,()),context)
    if reference!=sham:
        raise AssertionError("sham ablation changed original trajectory")
    all_zero=microprobe(brain,clone_stw_mask(state,range(N_SLOTS)),context)
    all_zero_stats=_comparison(reference,all_zero,mapping,context)
    lesions=[]
    for index in range(N_SLOTS):
        syn=state.dendrites[index]
        ablated=microprobe(
            brain,clone_stw_mask(state,(index,)),context,
        )
        comparison=_comparison(reference,ablated,mapping,context)
        if syn.dendrite.stw==0 and (
            comparison["action_changed_steady"] or
            comparison["score_changed_steady"] or
            ablated!=reference
        ):
            raise AssertionError("ablation of already-zero STW invented an effect")
        lesions.append({
            "slot":index,
            "original_stw":syn.dendrite.stw,
            "original_ltw":syn.dendrite.ltw,
            "original_strength":syn.strength,
            **slot_classification(index,context,mapping),
            **comparison,
            "probe":ablated,
        })
    if digest(asdict(state))!=original_hash:
        raise AssertionError("diagnostic clones altered original checkpoint")
    return {
        "context":context,
        "initial_neural_sha256":original_hash,
        "reference":reference,
        "sham_identical":True,
        "all_zero":all_zero,
        "all_zero_vs_reference":all_zero_stats,
        "lesions":lesions,
    }


def _summarize_mode_checkpoint(observations):
    probe_points=sum(
        len(ob["reference"])-STEADY_START_INDEX for ob in observations
    )
    if probe_points!=12:
        raise AssertionError("exactly 2 contexts ×6 steady choices required")
    lesion_count=sum(len(x["lesions"]) for x in observations)
    if lesion_count!=16:
        raise AssertionError("all slots/context tested")
    lesion_ticks=lesion_count*(PROBE_TICKS-STEADY_START_INDEX)
    changed=sum(s["action_changed_steady"] for ob in observations
                for s in ob["lesions"])
    lost=sum(s["lost_correct_steady"] for ob in observations
             for s in ob["lesions"])
    gained=sum(s["gained_correct_steady"] for ob in observations
               for s in ob["lesions"])
    summary={
        "n_probe_steady_ticks":probe_points,
        "n_lesions":lesion_count,
        "n_lesion_steady_ticks":lesion_ticks,
        "reference_steady_correct":sum(
            ob["all_zero_vs_reference"]["base_correct_steady"]
            for ob in observations
        ),
        "all_zero_action_changed_steady":sum(
            ob["all_zero_vs_reference"]["action_changed_steady"]
            for ob in observations
        ),
        "single_lesion_action_change_rate":changed/lesion_ticks,
        "single_lesion_lost_correct_rate":lost/lesion_ticks,
        "single_lesion_gained_correct_rate":gained/lesion_ticks,
        "single_lesion_net_lost_correct_rate":(lost-gained)/lesion_ticks,
        "n_lesions_with_any_action_change":sum(
            s["action_changed_steady"]>0 for ob in observations
            for s in ob["lesions"]
        ),
        "per_alignment":{},
    }
    for aligned in (True,False):
        ls=[s for ob in observations for s in ob["lesions"]
            if s["aligned_to_current_mapping"] is aligned]
        n=len(ls)*(PROBE_TICKS-STEADY_START_INDEX)
        summary["per_alignment"][str(aligned)]={
            "n_lesions":len(ls),
            "action_change_rate":sum(
                s["action_changed_steady"] for s in ls
            )/n,
            "net_lost_correct_rate":sum(
                s["lost_correct_steady"]-s["gained_correct_steady"]
                for s in ls
            )/n,
        }
    return summary


def run_seed(seed,manifest=None):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("only the old 20-seed development cohort allowed")
    if manifest is None:
        manifest=load_original_manifest()
    original=original_run_seed(seed)
    actual=digest(original)
    if actual!=manifest["per_seed_sha256"][str(seed)]:
        raise AssertionError("original I3c7h raw per-seed SHA mismatch")
    brain,checkpoints=checkpoint_replay(seed,original)
    phases={}
    for phase,_,mapping in PHASES:
        modes={}
        for mode in EVALUATED_MODES:
            state=checkpoints[phase][mode]
            observations=[
                one_checkpoint_context(brain,state,c,mapping)
                for c in PROBE_CONTEXTS
            ]
            modes[mode]={
                "observations":observations,
                "summary":_summarize_mode_checkpoint(observations),
            }
        phases[phase]=modes
    return {
        "seed":seed,
        "verified_original_I3c7h_sha256":actual,
        "phases":phases,
    }


def _paired_ci(rows,phase,metric):
    diffs=[
        row["phases"][phase]["B"]["summary"][metric]
        -row["phases"][phase]["P"]["summary"][metric]
        for row in rows
    ]
    rng=random.Random(BOOTSTRAP_SEED)
    draws=sorted(
        statistics.mean(rng.choice(diffs) for _ in diffs)
        for _ in range(BOOTSTRAP_REPS)
    )
    return {
        "n_seeds":len(rows),
        "mean":statistics.mean(diffs),
        "ci95":[draws[int(0.025*BOOTSTRAP_REPS)],
                draws[int(0.975*BOOTSTRAP_REPS)-1]],
    }


def _paired_ci_by_alignment(rows,phase,group,metric):
    """Same original paired seed-cluster bootstrap for BOTH structural groups.

    Descriptive grouping was specified before lesions, but this output
    aggregator was added after first data inspection. No reranking/selection.
    """
    vals=[
        row["phases"][phase]["B"]["summary"]["per_alignment"][group][metric]
        -row["phases"][phase]["P"]["summary"]["per_alignment"][group][metric]
        for row in rows
    ]
    rng=random.Random(BOOTSTRAP_SEED)
    draws=sorted(
        statistics.mean(rng.choice(vals) for _ in vals)
        for _ in range(BOOTSTRAP_REPS)
    )
    return {
        "n_seeds":len(vals),
        "mean":statistics.mean(vals),
        "ci95":[draws[int(0.025*BOOTSTRAP_REPS)],
                draws[int(0.975*BOOTSTRAP_REPS)-1]],
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds,tuple) or not seeds
            or len(set(seeds))!=len(seeds)
            or any(type(s) is not int or s not in SEEDS for s in seeds)):
        raise ValueError("cannot consume any additional or duplicate cohort")
    manifest=load_original_manifest()
    rows=[run_seed(seed,manifest) for seed in seeds]
    summary={}
    contrast={}
    for phase in ("first","reversed"):
        summary[phase]={}
        for mode in EVALUATED_MODES:
            obs=[r["phases"][phase][mode]["summary"] for r in rows]
            summary[phase][mode]={
                "n_seeds":len(rows),
                "baseline_steady_accuracy":statistics.mean(
                    x["reference_steady_correct"]/12 for x in obs
                ),
                "n_seed_all_zero_changes_action":sum(
                    x["all_zero_action_changed_steady"]>0 for x in obs
                ),
                "mean_single_lesion_action_change_rate":statistics.mean(
                    x["single_lesion_action_change_rate"] for x in obs
                ),
                "mean_net_lost_correct_rate":statistics.mean(
                    x["single_lesion_net_lost_correct_rate"] for x in obs
                ),
                "mean_lesions_with_action_change":statistics.mean(
                    x["n_lesions_with_any_action_change"] for x in obs
                ),
            }
        contrast[phase]={
            m:_paired_ci(rows,phase,m)
            for m in (
                "single_lesion_action_change_rate",
                "single_lesion_net_lost_correct_rate",
            )
        }
    alignment_contrasts={
        phase:{
            group:{
                metric:_paired_ci_by_alignment(rows,phase,group,metric)
                for metric in ("action_change_rate","net_lost_correct_rate")
            } for group in ("True","False")
        } for phase in ("first","reversed")
    }
    for phase in ("first","reversed"):
        for mode in EVALUATED_MODES:
            summary[phase][mode]["by_alignment"]={
                group:{
                    metric:statistics.mean(
                        row["phases"][phase][mode]["summary"][
                            "per_alignment"][group][metric]
                        for row in rows
                    )
                    for metric in ("action_change_rate","net_lost_correct_rate")
                } for group in ("True","False")
            }
    if len(rows)==20:
        gate_allzero=(summary["reversed"]["B"][
            "n_seed_all_zero_changes_action"]>=MIN_ALL_ZERO_EFFECTIVE_SEEDS)
        gate_baseline=(summary["reversed"]["B"][
            "baseline_steady_accuracy"]>=MIN_B_INVERTED_BASELINE_ACCURACY)
    else:
        gate_allzero=gate_baseline=None
    return {
        "protocol":PROTOCOL,
        "source":"same 20 I3c7h development seeds; original per-seed and checkpoint SHA verified",
        "n_seeds":len(rows),
        "seeds":list(seeds),
        "n_modes":2,
        "n_phases":2,
        "n_contexts":2,
        "n_single_lesions_per_context":8,
        "n_microblocks":len(rows)*2*2*2*10,
        "n_single_lesion_microblocks":len(rows)*2*2*2*8,
        "n_total_probe_steps":len(rows)*2*2*2*10*PROBE_TICKS,
        "summary":summary,
        "paired_B_minus_P":contrast,
        "paired_B_minus_P_by_alignment":alignment_contrasts,
        "analysis_amendment":"Structural alignment seed-cluster aggregate added after original data were inspected; per_seed neural/probe data unchanged.",
        "gate_allzero_effective":gate_allzero,
        "gate_baseline_informative":gate_baseline,
        "per_seed_sha256":{str(r["seed"]):digest(r) for r in rows},
        "per_seed":rows,
        "limitations":"Intervention zeros STW for one checkpoint/readout, not the learned gene or structural strength; causal necessity LOCAL to state/action only, with possible redundancy. Full source I3c7h outcomes already known. This is not proof that past reward was credited correctly or that C1 organism is emulated.",
        "gates":{"software":"PASS if all assertions",
                 "G05":"OPEN","G09":"OPEN","G00H":"OPEN"},
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=run_all()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(
            json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",
            encoding="utf-8",
        )
    print(json.dumps({
        k:result[k] for k in (
            "protocol","n_seeds","seeds","n_microblocks",
            "n_single_lesion_microblocks","n_total_probe_steps",
            "summary","paired_B_minus_P",
            "paired_B_minus_P_by_alignment","gate_allzero_effective",
            "gate_baseline_informative","per_seed_sha256","gates",
        )
    },sort_keys=True))


if __name__=="__main__":
    main()
