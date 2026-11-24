"""NR01.04-A: PURE, preregistered descriptive analysis of development worlds.

No model imports, no experiment execution, no confirmation seeds.
See docs/neurolab/NR01_04A_PREREGISTRO_DESARROLLO_20261122.md
"""
from __future__ import annotations

from collections import Counter
import math
import random
import statistics

SEEDS = tuple(range(23000, 23020))
GRID = (("raw", None), ("knn", None), ("kmeans", 4),
        ("kmeans", 8), ("kmeans", 16),
        ("art", .60), ("art", .80), ("art", .90))
BOOTSTRAP_REPS = 5000
BOOTSTRAP_SEED = 918277


def arm_id(row):
    return (row["kind"], row.get("parameter"))


def _score(a, b):
    return (.5 * a["original"]["checkpoints"]["32"]["accuracy"]
            + .25 * b["B1"]["checkpoints"]["32"]["accuracy"]
            + .25 * b["B2"]["checkpoints"]["32"]["accuracy"])


def _percentile(values, frac):
    values = sorted(values)
    loc = frac * (len(values) - 1)
    low = int(loc)
    high = min(low + 1, len(values) - 1)
    return values[low] + (loc - low) * (values[high] - values[low])


def bootstrap_ci(deltas):
    if len(deltas) != len(SEEDS):
        raise ValueError("bootstrap requires 20 paired world deltas")
    randomizer = random.Random(BOOTSTRAP_SEED)
    samples = [statistics.fmean(deltas[randomizer.randrange(len(deltas))]
                               for _ in range(len(deltas)))
               for _ in range(BOOTSTRAP_REPS)]
    return [_percentile(samples, .025), _percentile(samples, .975)]


def _metrics(a, b):
    return {"A32": a["original"]["checkpoints"]["32"]["accuracy"],
            "A_reversal32": a["reversed"]["checkpoints"]["32"]["accuracy"],
            "B1_32": b["B1"]["checkpoints"]["32"]["accuracy"],
            "B2_32": b["B2"]["checkpoints"]["32"]["accuracy"]}


def _state_bytes(a, b):
    return (.5 * a["original"]["checkpoints"]["32"]["state_bytes"]
            + .25 * b["B1"]["checkpoints"]["32"]["state_bytes"]
            + .25 * b["B2"]["checkpoints"]["32"]["state_bytes"])


def _acquisition_cpu(a, b):
    return a["acquisition_cpu_ns"] + b["acquisition_cpu_ns"]


def _check_exposures(rows):
    for seed in SEEDS:
        for family in ("A", "B"):
            group = [r for r in rows if r["world_seed"] == seed and r["family"] == family]
            for field in ("unlabelled_sha256", "test_sha256"):
                if len(set(x[field] for x in group)) != 1:
                    raise AssertionError(f"observation exposure differs {seed}/{family}/{field}")
            for phase in (("original", "reversed") if family == "A" else ("B1", "B2")):
                eligible = [r[phase]["feedback_observations_sha256"]
                            for r in group if not r["over_budget"]]
                if eligible and len(set(eligible)) != 1:
                    raise AssertionError(f"feedback exposure differs {seed}/{family}/{phase}")


def summarize(rows):
    """Reject missing worlds/errors; never select on incomplete/ART-valid subset."""
    expected = {(seed, family, kind, parameter)
                for seed in SEEDS for family in ("A", "B")
                for kind, parameter in GRID}
    observed = [(r["world_seed"], r["family"], r["kind"], r["parameter"]) for r in rows]
    if len(observed) != len(expected) or set(observed) != expected:
        raise ValueError("development matrix must have exactly 20x2x8 unique conditions")
    if len(set(observed)) != len(observed):
        raise ValueError("duplicate development condition")
    if any(r.get("error") or r["status"] == "ERROR" for r in rows):
        raise ValueError("development has exceptions; preserve raw evidence, do not rank")
    _check_exposures(rows)

    by_id = {(r["world_seed"], r["family"], arm_id(r)): r for r in rows}
    report = {"worlds": len(SEEDS), "conditions": len(rows), "bootstrap_reps": BOOTSTRAP_REPS,
              "bootstrap_seed": BOOTSTRAP_SEED, "candidates": {}, "eligibility": {}}
    eligible = {}
    for key in GRID:
        pairs = [(by_id[seed, "A", key], by_id[seed, "B", key]) for seed in SEEDS]
        excluded_A = sum(bool(a["over_budget"]) for a, b in pairs)
        excluded_B = sum(bool(b["over_budget"]) for a, b in pairs)
        full = not (excluded_A or excluded_B)
        name = f"{key[0]}:{key[1]}"
        report["eligibility"][name] = {
            "full_20_worlds": full, "over_budget_A": excluded_A,
            "over_budget_B": excluded_B,
            "observed_category_counts_A": [a.get("encoder_categories") for a,b in pairs],
            "observed_category_counts_B": [b.get("encoder_categories") for a,b in pairs],
        }
        if not full:
            report["candidates"][name] = {"eligible": False, "reason": "category budget"}
            continue
        per_world = [_score(a, b) for a, b in pairs]
        phases = [_metrics(a,b) for a,b in pairs]
        eligible[name] = per_world
        report["candidates"][name] = {
            "eligible": True,
            "mean_score": statistics.fmean(per_world),
            "median_score": statistics.median(per_world),
            "mean_by_phase": {p: statistics.fmean(x[p] for x in phases)
                              for p in ("A32","A_reversal32","B1_32","B2_32")},
            "mean_state_bytes_checkpoint32": statistics.fmean(_state_bytes(a,b) for a,b in pairs),
            "mean_acquisition_cpu_ns_AplusB": statistics.fmean(_acquisition_cpu(a,b) for a,b in pairs),
            "per_world_score": per_world,
        }

    baseline_names = ("raw:None", "knn:None")
    if any(name not in eligible for name in baseline_names):
        raise AssertionError("missing valid simple control")
    best = sorted(baseline_names, key=lambda n:
                  (-report["candidates"][n]["mean_score"],
                   report["candidates"][n]["mean_state_bytes_checkpoint32"],
                   0 if n == "raw:None" else 1))[0]
    report["selected_simple_baseline"] = best
    report["comparisons"] = {}
    base = eligible[best]
    for name, per_world in eligible.items():
        if name in baseline_names:
            continue
        diffs = [x-y for x,y in zip(per_world,base)]
        candidate = report["candidates"][name]
        b_ph = report["candidates"][best]["mean_by_phase"]
        c_ph = candidate["mean_by_phase"]
        gain_A = c_ph["A32"] - b_ph["A32"]
        gain_B = .5*(c_ph["B1_32"]-b_ph["B1_32"]) + .5*(c_ph["B2_32"]-b_ph["B2_32"])
        ci = bootstrap_ci(diffs)
        report["comparisons"][name] = {
            "mean_advantage": statistics.fmean(diffs),
            "median_advantage": statistics.median(diffs),
            "bootstrap95": ci,
            "better_worlds": sum(d>1e-12 for d in diffs),
            "worse_worlds": sum(d< -1e-12 for d in diffs),
            "tied_worlds": sum(abs(d)<=1e-12 for d in diffs),
            "family_A_gain": gain_A, "family_B_gain": gain_B,
            "preliminary_statistical_signal": bool(statistics.fmean(diffs)>=.05
                                                  and ci[0]>0 and gain_A>0 and gain_B>0),
            "ablation_done": False,
            "confirmation_authorized": False,
        }

    report["decision"] = (
        "Development-only. No confirmation without a practical, paired, "
        "causally ablated advantage and frozen NR01.05 protocol."
    )
    return report
