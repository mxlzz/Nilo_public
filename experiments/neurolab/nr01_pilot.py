"""NR01.03-DP preregistered single DEVELOPMENT-seed pilot.

Only world 23000 is allowed here; no historical or confirmation seeds.
The runner consumes the pre-existing harness without changing model rules.
"""
from __future__ import annotations

from collections import Counter
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

from .nr01_harness import run_world

WORLD_SEED = 23000
GRID = (("raw", None), ("knn", None),
        ("kmeans", 4), ("kmeans", 8), ("kmeans", 16),
        ("art", .60), ("art", .80), ("art", .90))
OUTDIR = Path("metrics")
FINAL = OUTDIR / "nr01_dev_pilot_23000.json"
PROGRESS = OUTDIR / "nr01_dev_pilot_23000_progress.jsonl"


def _primary(row):
    if row.get("over_budget") or row.get("error"):
        return None
    if row["family"] == "A":
        return {"A32": row["original"]["checkpoints"]["32"]["accuracy"],
                "A_reversal32": row["reversed"]["checkpoints"]["32"]["accuracy"]}
    return {"B1_32": row["B1"]["checkpoints"]["32"]["accuracy"],
            "B2_32": row["B2"]["checkpoints"]["32"]["accuracy"]}


def run_pilot():
    # Keep seeds hardcoded in this unit. The full development experiment
    # needs a separate preregistered workflow, not a CLI switch.
    if WORLD_SEED != 23000:
        raise AssertionError("this pilot can only use preregistered seed23000")
    OUTDIR.mkdir(exist_ok=True)
    PROGRESS.write_text("", encoding="utf-8")
    rows = []
    errors = []
    checks = {}

    with PROGRESS.open("a", encoding="utf-8") as log:
        for family in ("A", "B"):
            for kind, parameter in GRID:
                key = f"{family}:{kind}:{parameter}"
                try:
                    row = run_world(family, WORLD_SEED, kind, parameter)
                    if row["world_seed"] != WORLD_SEED or row["family"] != family:
                        raise AssertionError("wrong experiment identity")
                    for what in ("unlabelled_sha256", "test_sha256"):
                        reference = checks.setdefault((family, what), row[what])
                        if reference != row[what]:
                            raise AssertionError(f"exposure mismatch {what}: {key}")
                    if not row.get("over_budget"):
                        phases = ("original", "reversed") if family == "A" else ("B1", "B2")
                        for phase in phases:
                            info = row[phase]
                            what = f"feedback:{phase}"
                            reference = checks.setdefault((family, what), info["feedback_observations_sha256"])
                            if reference != info["feedback_observations_sha256"]:
                                raise AssertionError(f"feedback tape mismatch: {key}:{phase}")
                            if info["test_observations_sha256"] != row["test_sha256"]:
                                raise AssertionError(f"test tape mismatch: {key}:{phase}")
                    row["primary_32"] = _primary(row)
                except Exception as exc:
                    row = {"family": family, "kind": kind, "parameter": parameter,
                           "world_seed": WORLD_SEED, "status": "ERROR",
                           "error": f"{type(exc).__name__}: {str(exc)[:500]}"}
                    errors.append(key)
                rows.append(row)
                log.write(json.dumps({"key": key, "status": row["status"],
                                      "primary_32": row.get("primary_32"),
                                      "categories": row.get("encoder_categories"),
                                      "error": row.get("error")},
                                     sort_keys=True, allow_nan=False) + "\n")
                log.flush()

    counts = Counter(row["status"] for row in rows)
    report = {
        "protocol": "NR01.03-DP-pre-registered-development-pilot-v1",
        "science_inference": False,
        "world_seed": WORLD_SEED,
        "forbidden_confirmation_seeds_used": False,
        "families": ["A", "B"],
        "conditions_expected": 16, "conditions_observed": len(rows),
        "software": {"python": platform.python_version(),
                     "artlib": importlib.metadata.version("artlib"),
                     "scikit_learn": importlib.metadata.version("scikit-learn")},
        "runner": platform.platform(),
        "status_counts": dict(counts),
        "exposure_sha256": {f"{family}:{what}": value
                            for (family, what), value in sorted(checks.items())},
        "results": rows,
        "exceptions": errors,
    }
    FINAL.write_text(json.dumps(report, indent=2, sort_keys=True,
                                allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"protocol": report["protocol"],
                      "conditions": len(rows),
                      "counts": dict(counts),
                      "exceptions": errors,
                      "results": [{"family": r["family"], "kind": r["kind"],
                                   "parameter": r["parameter"], "status": r["status"],
                                   "primary_32": r.get("primary_32"),
                                   "categories": r.get("encoder_categories")}
                                  for r in rows]}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(run_pilot())
