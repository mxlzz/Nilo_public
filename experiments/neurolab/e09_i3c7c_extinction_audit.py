"""I3c.7c: post-hoc forensic replay of I3c7b raw, hash-locked branch traces.

PREREG: docs/neurolab/E09_02I_I3C7C_EXTINCION_PRE_REGISTRO.md
The 80 episodes have ALREADY BEEN INSPECTED. Not a blinded holdout.
No new data, controller, neural rule or tunable parameter.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

EXPECTED_SHA256="2660ba63b866abfff469d754ff88cab8941b215b1078a652ddc52dfca0cce8a6"
EXPECTED_SEEDS=tuple(range(1500,1520))
MODES=("N","M","C","F")
TIMES=(7,8,9,10,11,16,128)
READOUT_TIMES=(7,9,16,128)
FRAME_KEYS={
    "tick","chem_read","chem_from_pool","class_type_inputs","scores",
    "action","effects","pre_strength_positive","post_strength_positive",
    "post_live_stw","post_ltw",
}


def _sha_row(row):
    data=json.dumps(row,sort_keys=True,separators=(",",":")).encode("utf-8")
    return sha256(data).hexdigest()


def _validate(data,*,full):
    if (not isinstance(data,dict) or data.get("protocol")!="NL-EXP-I3c7b-v1"
            or data.get("gates",{}).get("G05")!="OPEN"
            or data.get("gates",{}).get("sensitivity")!="DESCRIPTIVE_ONLY"):
        raise AssertionError("not a frozen I3c7b diagnostic artifact")
    rows=data.get("per_seed")
    seeds=data.get("seeds")
    if (not isinstance(rows,list) or not rows
            or not isinstance(seeds,list)
            or any(type(seed) is not int for seed in seeds)
            or len(set(seeds))!=len(seeds)
            or any(seed not in EXPECTED_SEEDS for seed in seeds)
            or seeds!=[row.get("seed") for row in rows]):
        raise AssertionError("development seed subset/count invalid")
    if full and seeds!=list(EXPECTED_SEEDS):
        raise AssertionError("full original 20-seed cohort required")
    if (data.get("n_physical_trunks")!=2*len(rows)
            or data.get("n_mapping_coordinates")!=4*len(rows)
            or data.get("n_branches")!=16*len(rows)
            or len(data.get("per_seed_sha256",{}))!=len(rows)):
        raise AssertionError("coordinate or branch counts drifted")
    all_eps=[]
    for row in rows:
        seed=row["seed"]
        if _sha_row(row)!=data["per_seed_sha256"].get(str(seed)):
            raise AssertionError(f"complete per-seed SHA mismatch: {seed}")
        eps=row.get("episodes")
        if (not isinstance(eps,list) or len(eps)!=4
                or {(e.get("target"),e.get("mapping")) for e in eps}
                   !={(t,m) for t in (0,1) for m in ("A","B")}):
            raise AssertionError("expected four balanced mapping coordinates")
        for target in (0,1):
            a,b=(e for e in eps if e["target"]==target)
            if (a["trunk_sha256"]!=b["trunk_sha256"]
                    or a["original_action"]!=b["original_action"]):
                raise AssertionError("evaluator leaked into common trunk")
        for ep in eps:
            if (ep["seed"]!=seed
                    or set(ep["arms"])!=set(MODES)
                    or ep["original_action"] not in ("D0","D1")):
                raise AssertionError("episode schema/action inconsistent")
            arms=ep["arms"]
            for a,b in (("N","C"),("M","F")):
                if (arms[a]["chemical_trajectory_sha256"]
                    !=arms[b]["chemical_trajectory_sha256"]):
                    raise AssertionError("chemical arm paths not paired")
            for mode in MODES:
                arm=arms[mode]
                frames=arm.get("frames")
                if (not isinstance(frames,list) or len(frames)!=124
                        or [f.get("tick") for f in frames]!=list(range(5,129))
                        or set(arm.get("readouts",{}))!={"7","9","16","128"}):
                    raise AssertionError("missing tick, frame or readout")
                for f in frames:
                    if (set(f)!=FRAME_KEYS or type(f["post_strength_positive"]) is not int
                            or not 0<=f["post_strength_positive"]<=8
                            or len(f["post_live_stw"])!=8
                            or len(f["post_ltw"])!=8
                            or len(f["effects"])!=8
                            or len(f["class_type_inputs"])!=2
                            or any(len(x)!=2 for x in f["class_type_inputs"])
                            or len(f["scores"])!=2
                            or len(f["chem_read"])!=4
                            or len(f["chem_from_pool"])!=4):
                        raise AssertionError("invalid neural trace fields")
                    if (sum(x is not None for x in f["post_live_stw"])
                            !=f["post_strength_positive"]):
                        raise AssertionError("live STW mask not equal live strength")
            all_eps.append(ep)
    if full and (data["initial_none_actions"]!=0
                 or data["initial_correct"]!=40):
        raise AssertionError("initial decisions/signs changed")
    return all_eps


def summarize(data,*,full=False):
    episodes=_validate(data,full=full)
    n=len(episodes)
    observed={"protocol":"NL-AUDIT-I3c7c-v1",
              "source_protocol":"NL-EXP-I3c7b-v1",
              "study":"post hoc already-inspected replay; not new holdout",
              "n_seeds":len(data["seeds"]),
              "n_mapping_coordinates":n,
              "n_branches":n*len(MODES),
              "timeline":{},
              "readout_transitions":{},
              "synaptic_effect_by_source":{},
              "initial_signs":dict(Counter(
                  str(ep["initial_correct"]) for ep in episodes
              )),
              "per_seed_original_hashes_verified":True}
    for mode in MODES:
        frames_by_time={
            str(t):[ep["arms"][mode]["frames"][t-5] for ep in episodes]
            for t in TIMES
        }
        observed["timeline"][mode]={}
        for tick in TIMES:
            frames=frames_by_time[str(tick)]
            neutral=[ep["arms"]["N"]["frames"][tick-5] for ep in episodes]
            observed["timeline"][mode][str(tick)]={
                "n":n,
                "all_eight_strength_zero":sum(
                    f["post_strength_positive"]==0 for f in frames
                ),
                "mean_strength_positive":sum(
                    f["post_strength_positive"] for f in frames
                )/n,
                "any_live_stw_positive":sum(
                    any(x is not None and x>0 for x in f["post_live_stw"])
                    for f in frames
                ),
                "any_live_stw_at_least5":sum(
                    any(x is not None and x>=5 for x in f["post_live_stw"])
                    for f in frames
                ),
                "any_type_positive_pre_tick":sum(
                    any(x>0 for cl in f["class_type_inputs"] for x in cl)
                    for f in frames
                ),
                "score_different_from_neutral_pre_tick":sum(
                    f["scores"]!=z["scores"] for f,z in zip(frames,neutral)
                ),
                "any_post_ltw_positive":sum(
                    any(x>0 for x in f["post_ltw"]) for f in frames
                ),
            }
        observed["readout_transitions"][mode]={}
        for t in READOUT_TIMES:
            transitions=Counter(
                (ep["arms"]["N"]["readouts"][str(t)]["correct"],
                 ep["arms"][mode]["readouts"][str(t)]["correct"])
                for ep in episodes
            )
            obs={
                "n":n,
                "neutral_wrong_to_wrong":transitions[(0,0)],
                "neutral_wrong_to_right":transitions[(0,1)],
                "neutral_right_to_wrong":transitions[(1,0)],
                "neutral_right_to_right":transitions[(1,1)],
                "accuracy":(
                    transitions[(0,1)]+transitions[(1,1)]
                )/n,
                "accuracy_delta_vs_neutral":(
                    transitions[(0,1)]-transitions[(1,0)]
                )/n,
                "different_action_count":sum(
                    ep["arms"][mode]["readouts"][str(t)]["action"]
                    !=ep["arms"]["N"]["readouts"][str(t)]["action"]
                    for ep in episodes
                ),
            }
            if sum(transitions.values())!=n:
                raise AssertionError("disappeared holdout event")
            if obs["accuracy"]!=data["summary"][mode]["readout_accuracy"][str(t)]:
                raise AssertionError("raw readout vs prior summary inconsistent")
            if obs["different_action_count"]!=data["summary"][mode][
                    "readout_action_changed_vs_N"][str(t)]:
                raise AssertionError("raw choice vs original action counts inconsistent")
            observed["readout_transitions"][mode][str(t)]=obs
        target=0
        distractor=0
        for ep in episodes:
            for frame in ep["arms"][mode]["frames"]:
                for i,e in enumerate(frame["effects"]):
                    if (i%4)//2==ep["target"]:
                        target+=e
                    else:
                        distractor+=e
        if (target!=data["summary"][mode]["effect_target_total"]
                or distractor!=data["summary"][mode]["effect_distractor_total"]):
            raise AssertionError("increment count differs from source trace")
        observed["synaptic_effect_by_source"][mode]={
            "target_total":target,"distractor_total":distractor,
            "all_effect":target+distractor,
        }
    if full:
        C=observed["timeline"]["C"]
        M=observed["timeline"]["M"]
        if (C["7"]["any_live_stw_at_least5"]!=60
                or C["9"]["any_live_stw_at_least5"]!=60
                or C["10"]["all_eight_strength_zero"]!=80
                or C["11"]["any_type_positive_pre_tick"]!=0
                or C["8"]["score_different_from_neutral_pre_tick"]!=36
                or M["7"]["any_live_stw_at_least5"]!=0
                or observed["readout_transitions"]["C"]["9"][
                    "neutral_wrong_to_right"]!=20
                or observed["readout_transitions"]["C"]["9"][
                    "neutral_right_to_wrong"]!=2
                or observed["readout_transitions"]["C"]["16"][
                    "accuracy_delta_vs_neutral"]!=0):
            raise AssertionError("original post hoc finding did not reproduce")
    observed["conclusion"]=(
        "Direct255 produces short-lived real STW/type/choice effects; the full "
        "original microbrain N/C/M loses all 8 contacts in tick10, erasing "
        "STW and eliminating later behavioral advantage. C also credits "
        "distractor sources: this is not verified causal-credit learning."
    )
    observed["G05_G09_G00H"]="OPEN"
    return observed


def inspect_file(path:Path):
    raw=path.read_bytes()
    original=sha256(raw).hexdigest()
    if original!=EXPECTED_SHA256:
        raise ValueError("not the SHA-locked complete original I3c7b JSON")
    data=json.loads(raw)
    result=summarize(data,full=True)
    result["source_original_json_sha256"]=original
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    result=inspect_file(args.input)
    output=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(output,encoding="utf-8")
    print(output,end="")


if __name__=="__main__":
    main()
