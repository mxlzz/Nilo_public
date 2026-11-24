"""E09.02g.9: OOS replication of frozen g8 C/G/S arms, seeds 20..99.

Do not change the original E09g8 training, rates, seeds 0..19 or gates.
Pre-registered at docs/neurolab/E09_02G_09_REPLICACION_NUEVAS_SEMILLAS_PRE_REGISTRO.md.
"""
from __future__ import annotations

import json
import random
import statistics

from .e09_paired_pulse_protocol import run_seed, MODES

SEEDS = tuple(range(20, 100))
BOOTSTRAP_REPLICATES = 4000
BOOTSTRAP_SEED = 20261121


def paired_bootstrap_interval(
    deltas: list[float] | tuple[float, ...],
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    if not deltas:
        raise ValueError("no paired differences")
    if type(replicates) is not int or replicates < 100:
        raise ValueError("at least 100 bootstrap replicates required")
    rng = random.Random(seed)
    n = len(deltas)
    estimates = sorted(
        sum(deltas[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(replicates)
    )
    # Fixed percentile-index convention, specified before new results:
    # indices floor(0.025*R) and ceil(0.975*R)-1.
    lo = int(0.025 * replicates)
    hi = int(0.975 * replicates) - 1
    return estimates[lo], estimates[hi]


def _describe(deltas: list[float]) -> dict:
    return {
        "mean": statistics.mean(deltas),
        "median": statistics.median(deltas),
        "minimum": min(deltas),
        "maximum": max(deltas),
        "positive": sum(v > 0 for v in deltas),
        "zero": sum(v == 0 for v in deltas),
        "negative": sum(v < 0 for v in deltas),
        "by_seed": deltas,
    }


def run_all() -> dict:
    rows = [run_seed(seed) for seed in SEEDS]
    if len(rows) != 80 or {row["seed"] for row in rows} != set(SEEDS):
        raise AssertionError("unseen seed partition changed")
    means = {}
    suppression_counts = {}
    for phase in ("first", "reversed"):
        means[phase] = {
            mode: {
                k: statistics.mean(row[phase][mode][k] for row in rows)
                for k in ("steady", "overall", "early")
            }
            for mode in MODES
        }
        suppression_counts[phase] = {
            mode: {
                k: sum(row[phase][mode][k] for row in rows)
                for k in ("scheduled_omissions", "nonzero_omissions")
            }
            for mode in MODES
        }
        for k in ("scheduled_omissions", "nonzero_omissions"):
            if suppression_counts[phase]["G"][k] != suppression_counts[phase]["S"][k]:
                raise AssertionError("G/S received unequal number of omitted pulses")
    per_phase = {}
    for phase in ("first", "reversed"):
        per_phase[phase] = {}
        for pair, (x, y) in {
            "G_minus_S": ("G", "S"),
            "G_minus_C": ("G", "C"),
            "S_minus_C": ("S", "C"),
        }.items():
            per_phase[phase][pair] = _describe([
                row[phase][x]["steady"] - row[phase][y]["steady"]
                for row in rows
            ])
    b_deltas = per_phase["reversed"]["G_minus_S"]["by_seed"]
    ci = paired_bootstrap_interval(b_deltas)
    b_mean = per_phase["reversed"]["G_minus_S"]["mean"]
    a_mean = per_phase["first"]["G_minus_S"]["mean"]
    gates = {
        mode: sum(
            row["first"][mode]["steady"] >= .90
            and row["reversed"][mode]["steady"] >= .90
            for row in rows
        ) for mode in MODES
    }
    return {
        "protocol": "E09_02G_09_REPLICACION_NUEVAS_SEMILLAS_PRE_REGISTRO-v1",
        "seeds": list(SEEDS),
        "n": len(SEEDS),
        "reuses_frozen_g8_runner": True,
        "means": means,
        "suppression_counts": suppression_counts,
        "paired_contrasts": per_phase,
        "bootstrap": {
            "method": "paired percentile, 4000 draws, seed=20261121",
            "B_G_minus_S_95pct_CI": list(ci),
        },
        "directional_support_CI_above_zero": ci[0] > 0,
        "practical_threshold_B_ge_0_03_and_A_ge_minus_0_02":
            b_mean >= .03 and a_mean >= -.02,
        "joint_steady_ge_0_90_by_mode": gates,
        "per_seed": rows,
        "interpretation_warning": "New-seed replication of a laboratory oracle, not a brain-level causal repair.",
    }


def main() -> None:
    print(json.dumps(run_all(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
