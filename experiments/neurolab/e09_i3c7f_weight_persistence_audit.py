"""I3c.7f: immutable 20-seed post-hoc STW/LTW/strength retention audit.

PREREG: docs/neurolab/E09_02I_I3C7F_PERSISTENCIA_PESOS_PRE_REGISTRO.md
No new brain calls, genes, chemical changes, new learning or new seeds.
This is NOT a confirmatory statistical test of G05. The source traces
were inspected BEFORE design and are a development cohort.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import statistics

EXPECTED_SEEDS = tuple(range(1600,1620))
EXPECTED_PER_SEED_SHA256 = (
    "311b387817b4f0d645cf191df99ae701641c11e9329758fe64f1f71701af8f8e"
)
ORIGINAL_JSON_SHA256 = (
    "193ef109e214d33b9779611f1757d3bf23781755d38a0212778ed4269748752c"
)
MODES = ("D0","D16","M0","M16","FD","FM")
PHASES = ("first","reversed")
READOUTS = ("frozen","active_no_new_reward")
QUARTERS = ((1,32),(33,64),(65,96),(97,128))
GEN_SIGNAL_THRESHOLD = 5


def _digest(obj):
    return sha256(json.dumps(
        obj,sort_keys=True,separators=(",",":")
    ).encode("utf-8")).hexdigest()


def validate_source(data):
    if not isinstance(data,dict) or data.get("protocol")!="NL-EXP-I3c7e-v1":
        raise AssertionError("source is not the registered I3c7e original")
    if (data.get("seeds")!=list(EXPECTED_SEEDS)
            or data.get("n_seeds")!=20
            or data.get("modes")!=list(MODES)
            or data.get("phases")!=list(PHASES)
            or data.get("readouts")!=list(READOUTS)
            or data.get("holdout_ticks_per_readout")!=128
            or data.get("gates",{}).get("G05")!="OPEN"):
        raise AssertionError("experiment contract or cohort changed")
    rows=data.get("per_seed")
    if not isinstance(rows,list) or len(rows)!=20:
        raise AssertionError("not all original 20 seeds present")
    if [r["seed"] for r in rows]!=list(EXPECTED_SEEDS):
        raise AssertionError("seed coordinates changed or reordered")
    aggregate=_digest(rows)
    if aggregate!=EXPECTED_PER_SEED_SHA256:
        raise AssertionError("20 seed trajectories changed: original hash mismatch")
    for row in rows:
        seed=row["seed"]
        if _digest(row)!=data.get("per_seed_sha256",{}).get(str(seed)):
            raise AssertionError(f"individual seed changed: {seed}")
        if not row.get("initial_sha256"):
            raise AssertionError("missing common initial checkpoint")
        for phase in PHASES:
            p=row[phase]
            if not (p["golden_e09g5_neural_equal"]
                     and p["golden_e09g5_frozen_metrics_equal"]):
                raise AssertionError("D0 original E09g.5 parity lost")
            if len(p["train_blocks"])!=32 or len(p["holdout_blocks"])!=16:
                raise AssertionError("phase schedule changed")
            if set(p["arms"])!=set(MODES):
                raise AssertionError("factorial arms missing")
            for mode in MODES:
                a=p["arms"][mode]
                if set(a["readouts"])!=set(READOUTS):
                    raise AssertionError("missing a readout mode")
                for readout in READOUTS:
                    read=a["readouts"][readout]
                    frames=read.get("frames")
                    if (read["n_ticks"]!=128 or len(frames)!=128
                            or read["new_feedback_events"]!=0):
                        raise AssertionError("active/frozen holdout introduced feedback")
                    start=a["training"]["final_neural"]["tick"]+1
                    if [f.get("tick") for f in frames]!=list(range(start,start+128)):
                        raise AssertionError("holdout logical tick drift")
                    for i,f in enumerate(frames):
                        if (f["within_block"]!=i%8 or
                            f["external_feedback_created"] is not False or
                            f["context"] not in (0,1) or
                            f["correct"] not in (0,1) or
                            len(f["strengths"])!=8 or len(f["stw"])!=8 or
                            len(f["ltw"])!=8 or len(f["chem_input"])!=4):
                            raise AssertionError("invalid frame schema")
                        if not (
                            0<=f["n_live"]<=8
                            and f["n_live"]==sum(s>0 for s in f["strengths"])
                            and f["n_live_stw_ge5"]==sum(
                               s>0 and w>=GEN_SIGNAL_THRESHOLD
                               for s,w in zip(f["strengths"],f["stw"])
                            )
                            and f["n_live_ltw_positive"]==sum(
                               s>0 and w>0
                               for s,w in zip(f["strengths"],f["ltw"])
                            )
                        ):
                            raise AssertionError("original live STW/LTW counts inconsistent")
                    total=sum(f["correct"] for f in frames)/128
                    steady=sum(f["correct"] for f in frames
                               if f["within_block"]>=2)/96
                    if (total!=read["overall"] or steady!=read["steady"]):
                        raise AssertionError("raw frame scores disagree with original holdout")
    return rows,aggregate


def _first_or_none(frames,predicate):
    return next((i for i,f in enumerate(frames,1) if predicate(f)),None)


def _one_seed_window(frames,start,end):
    part=frames[start-1:end]
    if len(part)!=32:
        raise AssertionError("fixed 32-tick analysis window required")
    counts=Counter(f["context"] for f in part)
    correct=Counter(f["context"] for f in part if f["correct"])
    if sum(counts.values())!=32:
        raise AssertionError("missing context in split")
    return {
        "n_ticks":32,
        "correct":sum(f["correct"] for f in part),
        "accuracy":sum(f["correct"] for f in part)/32,
        "context_n":{str(c):counts[c] for c in (0,1)},
        "context_correct":{str(c):correct[c] for c in (0,1)},
        "mean_live":sum(f["n_live"] for f in part)/32,
        "mean_live_stw_ge5":sum(f["n_live_stw_ge5"] for f in part)/32,
        "mean_live_ltw_positive":sum(
            f["n_live_ltw_positive"] for f in part
        )/32,
        "pct_frames_no_live":sum(f["n_live"]==0 for f in part)/32,
        "pct_frames_no_live_functional_stw":sum(
            f["n_live_stw_ge5"]==0 for f in part
        )/32,
        "pct_frames_no_live_ltw":sum(
            f["n_live_ltw_positive"]==0 for f in part
        )/32,
        "mean_stw_among_live_slots":(
            sum(w for f in part for s,w in zip(f["strengths"],f["stw"])
                if s>0)/
            max(1,sum(f["n_live"] for f in part))
        ),
        "mean_ltw_among_live_slots":(
            sum(w for f in part for s,w in zip(f["strengths"],f["ltw"])
                if s>0)/
            max(1,sum(f["n_live"] for f in part))
        ),
    }


def summarize(data):
    rows,hash20=validate_source(data)
    out={
        "protocol":"NL-AUDIT-I3c7f-v1",
        "source":"I3c7e same original 20 development seeds, post hoc, NOT new holdout",
        "source_per_seed_sha256":hash20,
        "seeds":list(EXPECTED_SEEDS),
        "n_holdout_frames":20*2*6*2*128,
        "genetic_c1_context_stw_threshold":GEN_SIGNAL_THRESHOLD,
        "quarter_windows":[list(x) for x in QUARTERS],
        "by_phase_mode_readout":{},
        "selected_illustrative_seed_traces":{},
        "G05_G09_G00H":"OPEN",
    }
    for phase in PHASES:
        out["by_phase_mode_readout"][phase]={}
        for mode in MODES:
            out["by_phase_mode_readout"][phase][mode]={}
            for readout in READOUTS:
                fragments=[]
                fullframes=[]
                survival=[]
                chems=[[],[]]
                last_live=[]
                for row in rows:
                    r=row[phase]["arms"][mode]["readouts"][readout]
                    frames=r["frames"]
                    fullframes.extend(frames)
                    last_live.append(frames[-1]["n_live"])
                    for c in (0,1):
                        chems[c].append(sum(f["chem_input"][c] for f in frames))
                    survival.append({
                        "seed":row["seed"],
                        "first_no_live":_first_or_none(
                            frames,lambda f:f["n_live"]==0
                        ),
                        "first_no_live_stw_ge5":_first_or_none(
                            frames,lambda f:f["n_live_stw_ge5"]==0
                        ),
                        "first_no_live_ltw_positive":_first_or_none(
                            frames,lambda f:f["n_live_ltw_positive"]==0
                        ),
                        "fraction_of_128_ticks_without_live":sum(
                            f["n_live"]==0 for f in frames
                        )/128,
                        "fraction_of_128_ticks_without_live_stw_ge5":sum(
                            f["n_live_stw_ge5"]==0 for f in frames
                        )/128,
                        "fraction_of_128_ticks_without_live_ltw":sum(
                            f["n_live_ltw_positive"]==0 for f in frames
                        )/128,
                        "end_n_live":frames[-1]["n_live"],
                        "end_n_live_stw_ge5":frames[-1]["n_live_stw_ge5"],
                        "end_n_live_ltw_positive":frames[-1]["n_live_ltw_positive"],
                    })
                    fragments.append(frames)
                windows=[]
                for a,b in QUARTERS:
                    per_seed=[_one_seed_window(frames,a,b) for frames in fragments]
                    correct_by_context={str(c):sum(
                        r["context_correct"][str(c)] for r in per_seed
                    ) for c in (0,1)}
                    count_by_context={str(c):sum(
                        r["context_n"][str(c)] for r in per_seed
                    ) for c in (0,1)}
                    windows.append({
                        "ticks":[a,b],
                        "n_ticks":len(per_seed)*32,
                        "accuracy":sum(r["correct"] for r in per_seed)/
                                   (len(per_seed)*32),
                        "n_by_context":count_by_context,
                        "accuracy_by_context":{
                            str(c):(
                                correct_by_context[str(c)]/
                                count_by_context[str(c)]
                                if count_by_context[str(c)] else None
                            ) for c in (0,1)
                        },
                        "mean_live":statistics.mean(r["mean_live"] for r in per_seed),
                        "mean_live_stw_ge5":statistics.mean(
                            r["mean_live_stw_ge5"] for r in per_seed
                        ),
                        "mean_live_ltw_positive":statistics.mean(
                            r["mean_live_ltw_positive"] for r in per_seed
                        ),
                        "fraction_frames_no_live":statistics.mean(
                            r["pct_frames_no_live"] for r in per_seed
                        ),
                        "fraction_frames_no_live_functional_stw":statistics.mean(
                            r["pct_frames_no_live_functional_stw"] for r in per_seed
                        ),
                        "fraction_frames_no_live_ltw":statistics.mean(
                            r["pct_frames_no_live_ltw"] for r in per_seed
                        ),
                        "mean_stw_among_live_slots_per_seed":statistics.mean(
                            r["mean_stw_among_live_slots"] for r in per_seed
                        ),
                        "mean_ltw_among_live_slots_per_seed":statistics.mean(
                            r["mean_ltw_among_live_slots"] for r in per_seed
                        ),
                    })
                for i,window in enumerate(windows):
                    start,end=QUARTERS[i]
                    if window["n_ticks"]!=640:
                        raise AssertionError("not all seed frames included")
                    if sum(window["n_by_context"].values())!=640:
                        raise AssertionError("context balance accounting broken")
                original=statistics.mean(
                    row[phase]["arms"][mode]["readouts"][readout]["overall"]
                    for row in rows
                )
                # The same rational accuracy may accumulate with different
                # floating-point order: compare within machine precision,
                # never alter original counts or cohorts.
                if abs(sum(w["accuracy"] for w in windows)/4-original)>1e-12:
                    raise AssertionError("original overall accuracy mismatch")
                out["by_phase_mode_readout"][phase][mode][readout]={
                    "n_seeds":20,
                    "n_ticks":20*128,
                    "original_mean_overall":original,
                    "original_mean_steady":statistics.mean(
                        row[phase]["arms"][mode]["readouts"][readout]["steady"]
                        for row in rows
                    ),
                    "chem_auc_mean":[statistics.mean(chems[0]),
                                     statistics.mean(chems[1])],
                    "n_seeds_all_strength_zero_at_end":sum(x==0 for x in last_live),
                    "n_seeds_eight_strength_positive_at_end":sum(x==8 for x in last_live),
                    "windows":windows,
                    "per_seed_fates":survival,
                }
    return out


def audit_file(path:Path):
    raw=path.read_bytes()
    data=json.loads(raw)
    result=summarize(data)
    digest=sha256(raw).hexdigest()
    result["source_json_sha256"]=digest
    result["source_full_json_matches_first_success"]=(
        digest==ORIGINAL_JSON_SHA256
    )
    # Corrected CI can differ only in aggregate CI fields, not per-seed
    # dataset. validate_source() already enforces original neural SHA.
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True,type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    result=audit_file(args.input)
    payload=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(payload,encoding="utf-8")
    print(json.dumps({
        "protocol":result["protocol"],"n_holdout_frames":result["n_holdout_frames"],
        "per_seed_sha256":result["source_per_seed_sha256"],
        "inversion_M0_active_windows":result["by_phase_mode_readout"]["reversed"][
            "M0"]["active_no_new_reward"]["windows"],
        "inversion_M16_active_windows":result["by_phase_mode_readout"]["reversed"][
            "M16"]["active_no_new_reward"]["windows"],
        "G05_G09_G00H":result["G05_G09_G00H"],
    },sort_keys=True))
