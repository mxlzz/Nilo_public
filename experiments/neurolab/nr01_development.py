"""NR01.04-A fixed 20-world development cohort. NEVER confirmation.

See preregistered design in docs/neurolab/NR01_04A_PREREGISTRO_DESARROLLO_20261122.md
"""
from __future__ import annotations
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import time

from .nr01_dev_analysis import SEEDS, GRID, summarize
from .nr01_harness import run_world

OUTDIR = Path("metrics")
FINAL = OUTDIR / "nr01_development_23000_23019.json"
PARTIAL = OUTDIR / "nr01_development_23000_23019.jsonl"

# Replayed pilot primary metrics, copied from the immutable GitHub Actions
# stdout at https://github.com/mxlzz/Nilo_public/actions/runs/45049410694
PILOT_CHECKPOINTS = {
    ("A", "raw", None): ("original", 1.0, "reversed", 0.5),
    ("A", "knn", None): ("original", 1.0, "reversed", 1.0),
    ("A", "kmeans", 4): ("original", 1.0, "reversed", .25),
    ("A", "kmeans", 8): ("original", .9875, "reversed", 0.0),
    ("A", "kmeans", 16): ("original", 1.0, "reversed", .31875),
    ("B", "raw", None): ("B1", 2/3, "B2", 2/3),
    ("B", "knn", None): ("B1", .5, "B2", 11/12),
    ("B", "kmeans", 4): ("B1", 2/3, "B2", 107/120),
    ("B", "kmeans", 8): ("B1", 53/120, "B2", 107/120),
    ("B", "kmeans", 16): ("B1", 73/120, "B2", 2/3),
}
PILOT_ART_COUNTS = {
    ("A", .60): 29, ("A", .80): 58, ("A", .90): 119,
    ("B", .60): 26, ("B", .80): 139, ("B", .90): 167,
}


def replay_check(row):
    if row["world_seed"] != 23000:
        return
    family, kind, param = row["family"], row["kind"], row["parameter"]
    if kind == "art":
        expected = PILOT_ART_COUNTS[(family, param)]
        if not row["over_budget"] or row["encoder_categories"] != expected:
            raise AssertionError(f"pilot ART budget replay mismatch {family}/{param}")
    else:
        p1, v1, p2, v2 = PILOT_CHECKPOINTS[(family, kind, param)]
        actual1 = row[p1]["checkpoints"]["32"]["accuracy"]
        actual2 = row[p2]["checkpoints"]["32"]["accuracy"]
        if abs(actual1 - v1)>1e-12 or abs(actual2-v2)>1e-12:
            raise AssertionError(f"pilot replay mismatch {family}/{kind}/{param}:"
                                 f" expected {(v1,v2)}, got {(actual1,actual2)}")


def main():
    OUTDIR.mkdir(exist_ok=True)
    PARTIAL.write_text("", encoding="utf-8")
    if SEEDS != tuple(range(23000, 23020)) or len(GRID) != 8:
        raise RuntimeError("NR01 preregistered development cohort changed")
    results = []
    errors = []
    start_ns = time.process_time_ns()
    with PARTIAL.open("a", encoding="utf-8") as log:
        for seed in SEEDS:
            for family in ("A", "B"):
                for kind, param in GRID:
                    key = f"{seed}/{family}/{kind}/{param}"
                    try:
                        row = run_world(family, seed, kind, param)
                        replay_check(row)
                    except Exception as exc:
                        errors.append(key)
                        row = {"world_seed": seed, "family": family, "kind": kind,
                               "parameter": param, "status": "ERROR",
                               "error": f"{type(exc).__name__}: {str(exc)[:500]}"}
                    results.append(row)
                    log.write(json.dumps(row, allow_nan=False, sort_keys=True) + "\n")
                    log.flush()
            summary = Counter(r["status"] for r in results if r["world_seed"]==seed)
            print(json.dumps({"development_seed_completed": seed,
                              "world_conditions": dict(summary),
                              "cumulative_errors": len(errors)},
                             sort_keys=True), flush=True)
    try:
        analysis = summarize(results) if not errors else {
            "blocked": "exception in an arm; do not rank partial world matrix",
            "errors": errors}
    except Exception as exc:
        errors.append("aggregate")
        analysis = {"blocked": "analysis invariant failure",
                    "exception": f"{type(exc).__name__}: {str(exc)[:500]}"}
    report = {"protocol": "NR01.04-A-20-development-worlds-v1",
              "used_seeds": list(SEEDS),
              "confirmation_or_historical_seeds_used": False,
              "conditions_expected": len(SEEDS)*2*len(GRID),
              "conditions_observed": len(results),
              "library_versions": {
                  "artlib": importlib.metadata.version("artlib"),
                  "scikit_learn": importlib.metadata.version("scikit-learn"),
                  "python": platform.python_version()},
              "platform": platform.platform(),
              "elapsed_process_cpu_ns": time.process_time_ns()-start_ns,
              "exceptions": errors,
              "status_counts": dict(Counter(r["status"] for r in results)),
              "analysis": analysis,
              "rows": results}
    FINAL.write_text(json.dumps(report, sort_keys=True, indent=2,
                                allow_nan=False) + "\n", encoding="utf-8")
    digest = hashlib.sha256(FINAL.read_bytes()).hexdigest()
    print(json.dumps({
        "development_summary": True, "json_sha256": digest,
        "conditions": report["conditions_observed"],
        "exceptions": errors,
        "counts": report["status_counts"],
        "selected_simple_baseline": analysis.get("selected_simple_baseline"),
        "candidates": {name: {
            "eligible": body.get("eligible"), "mean_score": body.get("mean_score"),
            "mean_state_bytes": body.get("mean_state_bytes_checkpoint32"),
        } for name, body in analysis.get("candidates", {}).items()},
        "eligibility": {name: {
            "A": body["over_budget_A"], "B": body["over_budget_B"]
        } for name, body in analysis.get("eligibility", {}).items()},
        "comparisons": analysis.get("comparisons", {}),
        "science_confirmation": "NOT EXECUTED",
    }, sort_keys=True), flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
