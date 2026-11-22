"""H22: preregistered epsilon ablation; reuse unmodified H21 FiPy solver.

H22 varies only the interfacial penalty epsilon of the existing Cahn-Hilliard
equation. The previous failed H21 remains unchanged. CPU-only, no GUI.
"""
from __future__ import annotations
import json
import pathlib
import platform
import tempfile

import fipy
import numpy as np
import xarray as xr

import probe_e3_h21_spinodal_fipy as h21

def run(epsilon, mobility, composition):
    """Run the exact H21 solver equation with a single controlled coefficient."""
    previous = h21.EPSILON
    try:
        h21.EPSILON = epsilon
        return h21.run_case(mobility, composition)
    finally:
        h21.EPSILON = previous

def clean(case):
    return {key: value for key, value in case.items()
            if key not in ("owner", "initial", "snapshots")}

def main():
    active = run(.5, 1., .5)
    baseline = run(1., 1., .5)
    static = run(.5, 0., .5)
    stable = run(.5, 1., .1)
    replay = run(.5, 1., .5)

    results = (active, baseline, static, stable, replay)
    final_phi = h21.fraction(active["owner"])
    active_stats = h21.describe(final_phi)
    base_stats = baseline["final_stats"]
    null = h21.null_conditioned(final_phi > .5)
    early = active["snapshots"][300] > .5
    late = active["snapshots"][400] > .5
    union = np.logical_or(early, late)
    jaccard = (float(np.logical_and(early, late).sum() / union.sum())
               if union.any() else 0.)
    variance_ratio = (active_stats["variance"] / base_stats["variance"]
                      if base_stats["variance"] > 0 else float("nan"))
    no_mobility_change = float(np.max(np.abs(
        h21.fraction(static["owner"]) - static["initial"])))
    fail = []

    def gate(name, ok):
        if not ok:
            fail.append(name)

    gate("material_mass_conserved", all(
        c["peak_mass_A_residual_kg"] < 1e-4
        and abs(c["mass_final_kg"] - 400.) < 1e-9 for c in results))
    gate("strong_segregation_quantiles",
         active_stats["q05"] < .3 and active_stats["q95"] > .7)
    gate("segregation_variance_increases",
         active_stats["variance"] > 2*active["initial_stats"]["variance"])
    gate("both_material_domains", active_stats["n_high"] >= 8
         and active_stats["n_low"] >= 8)
    gate("epsilon_ablation_variance_ratio",
         np.isfinite(variance_ratio) and variance_ratio >= 5.)
    gate("spatial_coherence_exceeds_row_conditioned_null",
         active_stats["same_edge_score"] > null["p95_same_edges"] + .08)
    gate("pattern_persists", jaccard >= .60)
    gate("zero_mobility_no_change", no_mobility_change < 1e-8)
    gate("stable_composition_unsegregated",
         stable["final_stats"]["q95"] < .3 and
         stable["final_stats"]["variance"] <
             1.5*stable["initial_stats"]["variance"])
    gate("replay_bit_identical", np.array_equal(
             active["owner"]["material_mass_kg"].values,
             replay["owner"]["material_mass_kg"].values)
         and np.array_equal(active["snapshots"][300],
                            replay["snapshots"][300])
         and active["owner_hash"] == replay["owner_hash"])

    rejected = h21.reject_candidates(active["owner"])
    with tempfile.TemporaryDirectory(prefix="world_h22_") as temp:
        path = pathlib.Path(temp)/"phase_A_B.nc"
        active["owner"].to_netcdf(path, engine="scipy")
        with xr.open_dataset(path, engine="scipy") as fd:
            restored = fd.load()
        h21.validate(restored)
        gate("checkpoint_identical", h21.digest(restored) ==
             active["owner_hash"] and np.array_equal(
             restored["material_mass_kg"].values,
             active["owner"]["material_mass_kg"].values))
        checkpoint_size = path.stat().st_size

    metrics = {
        "experiment": "E3 H22 preregistered Cahn-Hilliard epsilon sensitivity",
        "python": platform.python_version(),
        "fipy": fipy.__version__, "numpy": np.__version__,
        "xarray": xr.__version__, "seed": h21.SEED,
        "grid": [h21.NY, h21.NX], "nsteps": h21.N_STEPS,
        "epsilon_0_5": clean(active),
        "epsilon_1_H21_reproduction": clean(baseline),
        "mobility_zero": clean(static),
        "mean_0_1_control": clean(stable),
        "variance_ratio": variance_ratio,
        "row_conditioned_null": null,
        "jaccard_step300_step400": jaccard,
        "mobility_zero_max_change": no_mobility_change,
        "rejected_bad_owner_states": rejected,
        "checkpoint_bytes": checkpoint_size,
        "replay_exact": True,
        "preregistered_gates_failed": fail,
        "limitations": "Only dimensionless 2D composition. Not stable 3D objects, mechanics, chemical validation or coupled physical world."
    }
    print("WORLD_EVAL_JSON " + json.dumps(metrics, sort_keys=True), flush=True)
    if fail:
        raise AssertionError("H22 preregistered gates failed: " + ", ".join(fail))

if __name__ == "__main__":
    main()
