"""I3c.7k: post-hoc diagnostic STW -> LTW capacity oracle, not C1 learning.

Preregistered (after source outcomes were inspected):
 docs/neurolab/E09_02I_I3C7K_TRANSFERENCIA_CONTENIDO_PRE_REGISTRO.md

Exact replay of 20 original I3c7g development seeds; at the END of
the long reversed training, branch same state to sham S, instant copy
STW->LTW C, and equal-magnitude owner-swapped LTW X. No novel training,
source truth or neural parameters. ACTIVE readouts use existing
C1ContextBrain / I3c7e chemical dynamics with no NEW rewards.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict,replace
from hashlib import sha256
import json
from pathlib import Path
import random
import statistics

from .c1_context_brain import C1ContextBrain
from .e09_coupled_brain import initial_coupled
from .e09_i3_metabolic_protocol import selected_genes
from .e09_i3c7e_loss_factorial import ArmState,run_phase
from .e09_i3c7g_consolidation_horizon import (
    run_seed as original_run_seed,sequences,SEEDS,
)
from .e09_context_protocol import MAPPING_A,MAPPING_B

PROTOCOL="NL-AUDIT-I3c7k-v1"
MODES=("S","C","X")
EXPECTED_SOURCE_PROTOCOL="NL-EXP-I3c7g-v1"
MANIFEST_FILE=(
    Path(__file__).resolve().parents[2]/
    "docs/neurolab/resultados/e09i3c7g_fuente_huellas.json"
)
EXPECTED_SOURCE_SHA=(
    "128e92df48b749c046fb9e1b02fce3beb54f4c8b82ed814b067a7c8d0c215d78"
)
SOURCE_SEEDS=tuple(range(1700,1720))
BOOTSTRAP_REPS=2000
BOOTSTRAP_SEED=60522


def _sha(obj):
    return sha256(json.dumps(
        obj,sort_keys=True,separators=(",",":")
    ).encode("utf-8")).hexdigest()


def load_manifest():
    data=json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    if (data.get("protocol")!=EXPECTED_SOURCE_PROTOCOL
            or data.get("original_full_json_sha256")!=EXPECTED_SOURCE_SHA
            or data.get("original_per_seed_aggregate_sha256")!=
            "9343414af0f29260a0080dd950fbf3dab493633e2550669b999ec1f88e9783fb"
            or set(data.get("per_seed_sha256",{}))!=
            set(str(s) for s in SOURCE_SEEDS)):
        raise AssertionError("source I3c7g manifest changed/incomplete")
    if any(len(data["per_seed_sha256"][str(s)])!=64 for s in SOURCE_SEEDS):
        raise AssertionError("invalid original per-seed fingerprint")
    return data


def copy_weights(state,mode):
    """Change exactly ONE field LTW in eight slots, no changing STW.

    S: original checkpoint,
    C: LTW_i=STW_i, source from the same synapse (unrealistic capacity upper bound),
    X: LTW_i=STW_(i+4 mod8), same STW multiset but other Decision owner.
    """
    if mode not in MODES:
        raise ValueError("only registered S/C/X LTW intervention")
    if not isinstance(state,ArmState):
        raise TypeError("typed ArmState required")
    if mode=="S":
        return state
    before=state.coupled.brain
    stw=tuple(s.dendrite.stw for s in before.dendrites)
    ltw=(stw if mode=="C" else tuple(stw[(i+4)%8] for i in range(8)))
    changed=tuple(
        replace(s,dendrite=replace(s.dendrite,ltw=ltw[i]))
        for i,s in enumerate(before.dendrites)
    )
    new_brain=replace(before,dendrites=changed)
    if (new_brain.tick!=before.tick
            or new_brain.neuron_outputs!=before.neuron_outputs
            or new_brain.neuron_states!=before.neuron_states
            or new_brain.concept_outputs!=before.concept_outputs
            or any(a.strength!=b.strength or
                   a.dendrite.stw!=b.dendrite.stw or
                   a.dendrite.susceptibility!=b.dendrite.susceptibility
                   for a,b in zip(before.dendrites,changed))):
        raise AssertionError("intervention escaped LTW-only")
    result=replace(
        state,coupled=replace(state.coupled,brain=new_brain)
    )
    if (result.coupled.chemistry!=state.coupled.chemistry or
            result.pending!=state.pending):
        raise AssertionError("intervention changed chemistry or reward memory")
    if sorted(s.dendrite.ltw for s in result.coupled.brain.dendrites)!=sorted(stw):
        raise AssertionError("copied LTW distribution differs from original STW")
    return result


def _weights(state):
    return {
        "tick":state.coupled.brain.tick,
        "stw":[s.dendrite.stw for s in state.coupled.brain.dendrites],
        "ltw":[s.dendrite.ltw for s in state.coupled.brain.dendrites],
        "strengths":[s.strength for s in state.coupled.brain.dendrites],
    }


def _rebuild_original_long_m0(seed,source):
    receptors,reactions=selected_genes()
    brain=C1ContextBrain(seed)
    a,_,short,extra,_,holdout=sequences(seed)
    initial=ArmState(initial_coupled(brain,receptors))
    after_a,a_metrics=run_phase(
        brain,initial,a,MAPPING_A,"M0",receptors,reactions,training=True
    )
    after_short,b_short=run_phase(
        brain,after_a,short,MAPPING_B,"M0",receptors,reactions,training=True
    )
    after_long,b_extra=run_phase(
        brain,after_short,extra,MAPPING_B,"M0",receptors,reactions,training=True
    )
    orig=source["modes"]["M0"]
    if (a_metrics["frames"]!=orig["first"]["training"]["frames"]
        or b_short["frames"]+b_extra["frames"]!=orig["long"]["training"]["frames"]
        or after_a.coupled.brain.tick!=256
        or after_short.coupled.brain.tick!=512
        or after_long.coupled.brain.tick!=896):
        raise AssertionError("training observations differ from exact original I3c7g")
    expected=orig["long"]["end_weights"]
    if any(
        a!=expected[k]
        for k,a in (
            ("stws",_weights(after_long)["stw"]),
            ("ltws",_weights(after_long)["ltw"]),
            ("strengths",_weights(after_long)["strengths"]),
        )
    ):
        raise AssertionError("original final synaptic weights changed")
    return brain,after_long,holdout,receptors,reactions


def _readout(brain,state,seq,receptors,reactions,kind):
    old_sha=_sha(asdict(state))
    after,metrics=run_phase(
        brain,state,seq,MAPPING_B,"M0",receptors,reactions,
        training=False,readout=kind,
    )
    if (metrics["n_ticks"]!=128 or metrics["new_feedback_events"]!=0
        or after.coupled.brain.tick!=state.coupled.brain.tick+128
        or _sha(asdict(state))!=old_sha):
        raise AssertionError("readout reward or checkpoint contamination")
    if kind=="frozen" and after.coupled.brain.dendrites!=state.coupled.brain.dendrites:
        raise AssertionError("frozen readout altered dendrites")
    return metrics


def _quarter_metrics(metrics):
    rows=metrics["frames"]
    return [
        sum(f["correct"] for f in rows[i:i+32])/32
        for i in (0,32,64,96)
    ]


def run_seed(seed,manifest=None):
    if type(seed) is not int or seed not in SOURCE_SEEDS:
        raise ValueError("I3c7k accepts only already-consumed development seeds")
    if manifest is None:
        manifest=load_manifest()
    original=original_run_seed(seed)
    origin_hash=_sha(original)
    if origin_hash!=manifest["per_seed_sha256"][str(seed)]:
        raise AssertionError("I3c7g prior source SHA not reproduced")
    brain,state,hold,receptors,reactions=_rebuild_original_long_m0(
        seed,original,
    )
    unchanged=_sha(asdict(state))
    branches={mode:copy_weights(state,mode) for mode in MODES}
    raw_stw=tuple(s.dendrite.stw for s in state.coupled.brain.dendrites)
    if (tuple(s.dendrite.ltw for s in branches["C"].coupled.brain.dendrites)
        !=raw_stw):
        raise AssertionError("LTW perfect copy not equal original STW")
    if (tuple(s.dendrite.ltw for s in branches["X"].coupled.brain.dendrites)
        !=tuple(raw_stw[(i+4)%8] for i in range(8))):
        raise AssertionError("owner-swapped LTW not exactly original STW permutation")
    obs={}
    frozen_actions=[]
    for mode in MODES:
        v=branches[mode]
        active=_readout(brain,v,hold,receptors,reactions,"active_no_new_reward")
        frozen=_readout(brain,v,hold,receptors,reactions,"frozen")
        frozen_actions.append(tuple(
            f["action"] for f in frozen["frames"]
        ))
        obs[mode]={
            "initial":_weights(v),
            "active":{
                "overall":active["overall"],
                "steady":active["steady"],
                "by_context":active["steady_by_context"],
                "quarter_accuracy":_quarter_metrics(active),
                "final_neural":active["final_neural"],
                "chemical_auc":active["chemical_input_auc"],
                "new_feedback_events":active["new_feedback_events"],
                "actions":[f["action"] for f in active["frames"]],
            },
            "frozen":{
                "overall":frozen["overall"],
                "steady":frozen["steady"],
                "by_context":frozen["steady_by_context"],
                "new_feedback_events":frozen["new_feedback_events"],
            },
        }
        if mode=="S":
            historical=original["modes"]["M0"]["long"]["readouts"]
            if active!=historical["active_no_new_reward"] or frozen!=historical["frozen"]:
                raise AssertionError("SHAM readout is not exactly original I3c7g")
    if len(set(frozen_actions))!=1:
        raise AssertionError("LTW-only change had direct readout effect despite learn=False")
    if _sha(asdict(state))!=unchanged:
        raise AssertionError("original training checkpoint mutated across clones")
    return {
        "seed":seed,
        "I3c7g_original_seed_sha256":origin_hash,
        "original_long_checkpoint_sha256":unchanged,
        "frozen_actions_identical_under_all_LTW_variants":True,
        "branches":obs,
    }


def _paired_ci(rows,a,b,metric="steady"):
    values=[
        row["branches"][a]["active"][metric]
        -row["branches"][b]["active"][metric]
        for row in rows
    ]
    randomizer=random.Random(BOOTSTRAP_SEED)
    draws=sorted(
        statistics.mean(randomizer.choice(values) for _ in values)
        for _ in range(BOOTSTRAP_REPS)
    )
    return {
        "n_seeds":len(values),
        "mean":statistics.mean(values),
        "ci95":[draws[int(.025*BOOTSTRAP_REPS)],
                draws[int(.975*BOOTSTRAP_REPS)-1]],
    }


def run_all(seeds=SEEDS):
    if (not isinstance(seeds,tuple) or not seeds
        or len(set(seeds))!=len(seeds)
        or any(type(x) is not int or x not in SOURCE_SEEDS for x in seeds)):
        raise ValueError("only original I3c7g seed subset; no new cohort")
    manifest=load_manifest()
    rows=[run_seed(seed,manifest) for seed in seeds]
    summary={
        mode:{
            "active_steady":statistics.mean(
                row["branches"][mode]["active"]["steady"] for row in rows
            ),
            "active_overall":statistics.mean(
                row["branches"][mode]["active"]["overall"] for row in rows
            ),
            "frozen_steady":statistics.mean(
                row["branches"][mode]["frozen"]["steady"] for row in rows
            ),
            "active_steady_ge90":sum(
                row["branches"][mode]["active"]["steady"]>=.90
                for row in rows
            ),
            "end_live_STW_ge5_mean":statistics.mean(
                row["branches"][mode]["active"]["final_neural"]["n_live_stw_ge5"]
                for row in rows
            ),
            "quarter_accuracy":[statistics.mean(
                row["branches"][mode]["active"]["quarter_accuracy"][q]
                for row in rows
            ) for q in range(4)],
        }
        for mode in MODES
    }
    paired={
        "C_minus_S":_paired_ci(rows,"C","S"),
        "C_minus_X":_paired_ci(rows,"C","X"),
        "S_minus_X":_paired_ci(rows,"S","X"),
    }
    a,b=paired["C_minus_S"],paired["C_minus_X"]
    feasibility=(
        len(rows)==20 and a["mean"]>=.10 and a["ci95"][0]>0
        and b["mean"]>=.10 and b["ci95"][0]>0
    )
    return {
        "protocol":PROTOCOL,
        "source_protocol":EXPECTED_SOURCE_PROTOCOL,
        "analysis_type":"Posthoc capability-oracle intervention, NOT independently confirmatory",
        "seeds":list(seeds),
        "n_seeds":len(rows),
        "modes":list(MODES),
        "source_full_json_sha256":EXPECTED_SOURCE_SHA,
        "STW_original_checkpoint_reused":True,
        "all_frozen_action_traces_identical":True,
        "summary":summary,
        "paired_contrasts":paired,
        "precommitted_capacity_gate":feasibility,
        "per_seed_sha256":{str(row["seed"]):_sha(row) for row in rows},
        "per_seed":rows,
        "limitations":"Perfect instant STW->LTW copying is an artificial microscope/oracle, NOT a learned C1/NeuroLab consolidation mechanism. Swapped LTW equal total but mismatched owner can perturb kinetics. Active outcomes are development only; no G05 gate even with >90% accuracy.",
        "gates":{"software":"PASS if assertions",
                 "G05":"OPEN","G09":"OPEN","G00H":"OPEN"},
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    data=run_all()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(
            json.dumps(data,sort_keys=True,separators=(",",":"))+"\n",
            encoding="utf-8",
        )
    print(json.dumps({
        k:data[k] for k in (
            "protocol","seeds","n_seeds","summary",
            "paired_contrasts","precommitted_capacity_gate",
            "per_seed_sha256","gates",
        )
    },sort_keys=True))


if __name__=="__main__":
    main()
