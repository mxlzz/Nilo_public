"""E2/H18: slope-gradient ablation using the EXISTING H9 Landlab sediment solver.

No new sediment-transport physics. This test only changes the initial
bedrock gradient and checks the existing xarray material owner ledger.
Pre-registered in ETAPA_2_H18_PROTOCOLO_GRADIENTE_SEDIMENTO.md.
"""
from __future__ import annotations

import json
import pathlib
import platform
import tempfile

import landlab
import numpy as np
import xarray as xr

import probe_e1_h9_sediment_owner as h9


def average_gradient(z):
    dzdy,dzdx=np.gradient(np.asarray(z),h9.SPACING_M)
    return float(np.mean(np.hypot(dzdx[1:-1,1:-1],dzdy[1:-1,1:-1])))


def run_slope(slope_factor):
    grid,flow,space,owner=h9.make_scene(h9.K_ACTIVE)
    m_initial=owner["soil_mass_kg"].values.copy()
    base_elev=owner["bedrock_elevation_m"].values.copy()
    new_elev=base_elev*float(slope_factor)

    # Only change a geometric input: material inventory, erodibility,
    # rain/discharge model and outlet remain exactly the original H9 scene.
    np.copyto(owner["bedrock_elevation_m"].values,new_elev)
    np.copyto(grid.at_node["bedrock__elevation"],new_elev.ravel())
    np.copyto(grid.at_node["topographic__elevation"],
              h9.topography(owner).ravel())
    baseline=float(owner.attrs["initial_soil_kg"])
    h9.validate(owner,baseline)
    initial_owner_hash=h9.checksum(owner)
    initial_surface=h9.topography(owner).copy()
    initial_gradient=average_gradient(new_elev)
    initial_surface_gradient=average_gradient(initial_surface)
    deposition_steps=0
    erosion_steps=0
    metrics=None
    for step in range(h9.STEPS):
        candidate,metrics=h9.advance_native_step(grid,flow,space,owner,baseline)
        erosion=np.asarray(grid.at_node["sediment__erosion_flux"])[grid.core_nodes]
        deposition=np.asarray(grid.at_node["sediment__deposition_flux"])[grid.core_nodes]
        erosion_steps+=int(np.any(erosion>1e-15))
        deposition_steps+=int(np.any(deposition>1e-15))
        owner=candidate
    assert metrics is not None
    mask=owner["is_core_node"].values.astype(bool)
    delta=owner["soil_mass_kg"].values-m_initial
    return {
        "owner":owner,"initial_mass":m_initial,
        "factor":float(slope_factor),
        "mean_bedrock_gradient":initial_gradient,
        "mean_total_topography_gradient":initial_surface_gradient,
        "initial_sha":initial_owner_hash,
        "final_sha":h9.checksum(owner),
        "mass_initial_kg":baseline,
        "mass_stored_final_kg":float(metrics["stored_kg"]),
        "exported_mass_kg":float(metrics["export_kg"]),
        "mass_balance_error_kg":float(metrics["residual_kg"]),
        "mass_tolerance_kg":float(metrics["tolerance_kg"]),
        "erosion_steps":erosion_steps,
        "deposition_steps":deposition_steps,
        "nodes_with_net_gain":int(np.count_nonzero(delta[mask]>1e-6)),
        "mass_delta_abs_sum_kg":float(np.sum(np.abs(delta[mask]))),
        "topographic_change_max_m":float(np.max(np.abs(h9.topography(owner)-initial_surface))),
    }


def main():
    full=run_slope(1.0)
    half=run_slope(.5)
    half_replay=run_slope(.5)
    k0=h9.execute(0.0)

    failed=[]
    def check(name,flag):
        if not flag:failed.append(name)
    check("same_material_initial",
          np.array_equal(full["initial_mass"],half["initial_mass"]) and
          full["mass_initial_kg"]==half["mass_initial_kg"]==10080000.)
    grad_ratio=half["mean_bedrock_gradient"]/full["mean_bedrock_gradient"]
    check("bedrock_gradient_halved",abs(grad_ratio-.5)<1e-12)
    output_reduction=(full["exported_mass_kg"]-half["exported_mass_kg"])/full["exported_mass_kg"] if full["exported_mass_kg"]>0 else float("nan")
    check("steeper_exports_more_than_five_pct",np.isfinite(output_reduction) and output_reduction>.05)
    check("nonnegative_native_output",full["exported_mass_kg"]>0. and half["exported_mass_kg"]>=0.)
    check("physical_erosion_and_deposition",full["erosion_steps"]>0 and full["deposition_steps"]>0
          and full["nodes_with_net_gain"]>0)
    check("matter_distribution_changed",
          np.count_nonzero(np.abs(full["owner"]["soil_mass_kg"].values-
                                          half["owner"]["soil_mass_kg"].values)>1e-6)>0)
    check("both_mass_balances",all(abs(z["mass_balance_error_kg"])<=z["mass_tolerance_kg"]
                                   for z in (full,half,half_replay)))
    check("zero_erodibility_still_inert",k0["mass_ledger"]["export_kg"]==0
          and np.array_equal(k0["owner"]["soil_mass_kg"].values,k0["original"]))
    check("replay_exact",np.array_equal(half["owner"]["soil_mass_kg"].values,
                                        half_replay["owner"]["soil_mass_kg"].values)
          and half["owner"].attrs["exported_soil_kg"]==half_replay["owner"].attrs["exported_soil_kg"]
          and half["final_sha"]==half_replay["final_sha"])

    rejected=h9.negative_cases(half["owner"])
    with tempfile.TemporaryDirectory(prefix="world_h18_") as td:
        p=pathlib.Path(td)/"slope_owner.nc"
        half["owner"].to_netcdf(p,engine="scipy")
        with xr.open_dataset(p,engine="scipy") as f:
            loaded=f.load()
        h9.validate(loaded,half["mass_initial_kg"])
        check("roundtrip_owner_identical",h9.checksum(loaded)==half["final_sha"]
              and np.array_equal(loaded["soil_mass_kg"].values,half["owner"]["soil_mass_kg"].values)
              and np.array_equal(h9.topography(loaded),h9.topography(half["owner"])))
        checkpoint_bytes=p.stat().st_size
    def display(z):
        return {k:v for k,v in z.items() if k not in ("owner","initial_mass")}
    report={
        "experiment":"E2 H18 vary only bedrock gradient in native Landlab sediment transport",
        "python":platform.python_version(),"landlab":landlab.__version__,
        "numpy":np.__version__,"xarray":xr.__version__,
        "steps":h9.STEPS,"dt":h9.DT,"K_sed":h9.K_ACTIVE,
        "full_gradient":display(full),
        "half_gradient":display(half),
        "gradient_ratio":grad_ratio,
        "export_reduction_fraction":output_reduction,
        "replay_exact":True,
        "zero_K_export_kg":k0["mass_ledger"]["export_kg"],
        "negative_owner_cases_rejected":rejected,
        "netcdf_bytes":checkpoint_bytes,
        "preregistered_gates_failed":failed,
        "limitations":"Idealized 2.5D watershed, soil-depth discontinuity not scaled, no calibrated rainfall/groundwater or 3D granular mechanics. Gradient intervention changes drainage routes if the physical router predicts so."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if failed:
        raise AssertionError("H18 preregistered gradient gates failed: "+", ".join(failed))


if __name__=="__main__":
    main()
