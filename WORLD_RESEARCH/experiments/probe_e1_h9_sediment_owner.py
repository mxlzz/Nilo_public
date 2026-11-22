"""E1/H9: native Landlab sediment transport publishes to one xarray mass owner.

Not a new physical law or a reusable world engine. This scoped experiment
compares an active SPACE run to a zero-erodibility control with per-step
material ledger checks. See preregistered ETAPA_1_H9_PROTOCOLO_SEDIMENTO_OWNER.md.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import tempfile

import landlab
import numpy as np
import xarray as xr
from landlab import RasterModelGrid
from landlab.components import PriorityFloodFlowRouter, SpaceLargeScaleEroder

SHAPE = (16, 16)
SPACING_M = 10.0
AREA_M2 = SPACING_M**2
DENSITY_KG_M3 = 1200.0  # abstract A, NOT a natural-material calibration
STEPS = 12
DT = 0.2
K_ACTIVE = 0.10


def checksum(ds):
    return hashlib.sha256(
        np.ascontiguousarray(ds["soil_mass_kg"].values).tobytes()
        + np.ascontiguousarray(ds["bedrock_elevation_m"].values).tobytes()
        + repr(float(ds.attrs["exported_soil_kg"])).encode("ascii")
    ).hexdigest()


def validate(ds, baseline_kg):
    if set(ds.data_vars) != {"soil_mass_kg", "bedrock_elevation_m", "is_core_node"}:
        raise ValueError("Unexpected material owner fields")
    if tuple(ds["soil_mass_kg"].dims) != ("y", "x"):
        raise ValueError("Unexpected owner dimensions")
    if ds.sizes.get("x") != SHAPE[1] or ds.sizes.get("y") != SHAPE[0]:
        raise ValueError("Unexpected owner shape")
    if ds["soil_mass_kg"].attrs.get("units") != "kg":
        raise ValueError("Unknown owner mass units")
    if ds["bedrock_elevation_m"].attrs.get("units") != "m":
        raise ValueError("Bedrock units invalid")
    if ds.attrs.get("schema_version") != 1 or ds.attrs.get("density_kg_m3") != DENSITY_KG_M3:
        raise ValueError("Unrecognized schema or conversion density")
    if ds.attrs.get("node_cell_area_m2") != AREA_M2:
        raise ValueError("Grid cell area changed")
    owner = ds["soil_mass_kg"].values
    bedrock = ds["bedrock_elevation_m"].values
    mask = ds["is_core_node"].values.astype(bool)
    ref = np.zeros(SHAPE, dtype=bool)
    ref[1:-1, 1:-1] = True
    if not np.array_equal(mask, ref):
        raise ValueError("Invalid core node mask")
    if not np.isfinite(owner).all() or not np.isfinite(bedrock).all():
        raise ValueError("Nonfinite state")
    if np.any(owner < 0.0) or np.any(owner[~mask] != 0.0):
        raise ValueError("Invalid mass or material at non-owned boundary")
    cumulative = float(ds.attrs.get("exported_soil_kg", np.nan))
    if not np.isfinite(cumulative) or cumulative < 0.0:
        raise ValueError("Invalid outgoing sediment ledger")
    if ds.attrs.get("initial_soil_kg") != float(baseline_kg):
        raise ValueError("Unrecognized initial material balance")
    stored = float(np.sum(owner))
    residual = stored + cumulative - baseline_kg
    tolerance = max(1e-4, 1e-8 * baseline_kg)
    if abs(residual) > tolerance:
        raise ValueError(f"Unaccounted material source/sink: residual={residual}, tol={tolerance}")
    return {"stored_kg": stored, "export_kg": cumulative,
            "residual_kg": residual, "tolerance_kg": tolerance}


def topography(ds):
    mass = ds["soil_mass_kg"].values
    depth = mass / (DENSITY_KG_M3 * AREA_M2)
    return ds["bedrock_elevation_m"].values + depth


def make_scene(k_sed):
    grid = RasterModelGrid(SHAPE, xy_spacing=SPACING_M)
    x, y = grid.node_x, grid.node_y
    bedrock = 0.042*y + 0.021*x + 0.016*np.sin(x*.024 + y*.025)
    initial_soil_depth = np.where(y < 50.0, 0.0, 0.6)
    # Core nodes are material cells; boundary nodes are geometric conditions.
    core = np.zeros(grid.number_of_nodes, dtype=bool)
    core[grid.core_nodes] = True
    initial_soil_depth[~core] = 0.0
    grid.at_node["bedrock__elevation"] = bedrock.copy()
    grid.at_node["soil__depth"] = initial_soil_depth.copy()
    grid.at_node["topographic__elevation"] = bedrock.copy() + initial_soil_depth
    grid.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True, left_is_closed=True,
        right_is_closed=True, top_is_closed=True
    )
    grid.set_watershed_boundary_condition_outlet_id(
        0, grid.at_node["topographic__elevation"], -9999.0
    )
    flow = PriorityFloodFlowRouter(grid, flow_metric="D8", suppress_out=True)
    space = SpaceLargeScaleEroder(
        grid, K_sed=k_sed, K_br=0.0, F_f=0.0, phi=0.0,
        H_star=1.0, v_s=3.0, m_sp=.5, n_sp=1.0,
        sp_crit_sed=0, sp_crit_br=0
    )
    mass = (initial_soil_depth * DENSITY_KG_M3 * AREA_M2).reshape(SHAPE)
    baseline = float(mass.sum())
    owner = xr.Dataset(
        {
            "soil_mass_kg": (("y", "x"), mass,
                             {"units": "kg", "meaning": "authoritative mobile solid mass"}),
            "bedrock_elevation_m": (("y", "x"), bedrock.reshape(SHAPE),
                                     {"units": "m", "meaning": "fixed nonmobile geometry"}),
            "is_core_node": (("y", "x"), core.reshape(SHAPE).astype(np.int8),
                              {"meaning": "1 = physical sediment owner cell"}),
        },
        coords={"y": np.arange(SHAPE[0], dtype=np.int32),
                "x": np.arange(SHAPE[1], dtype=np.int32)},
        attrs={
            "schema_version": 1,
            "density_kg_m3": DENSITY_KG_M3,
            "node_cell_area_m2": AREA_M2,
            "initial_soil_kg": baseline,
            "exported_soil_kg": 0.0,
            "description": "Landlab fields are temporary solver views, never a second ledger",
        }
    )
    validate(owner, baseline)
    return grid, flow, space, owner


def advance_native_step(grid, flow, space, owner, baseline):
    # Solver view comes from owner on EVERY step, never the reverse.
    depth = owner["soil_mass_kg"].values.ravel() / (DENSITY_KG_M3 * AREA_M2)
    np.copyto(grid.at_node["soil__depth"], depth)
    np.copyto(grid.at_node["topographic__elevation"],
              owner["bedrock_elevation_m"].values.ravel() + depth)
    flow.run_one_step()
    suspended_m3, bedload_m3 = space.run_one_step(DT)
    if not np.isfinite([suspended_m3, bedload_m3]).all():
        raise ValueError("Nonfinite outlet measurement")
    if suspended_m3 < 0 or bedload_m3 < 0:
        raise ValueError("Negative sediment export")
    raw_depth = grid.at_node["soil__depth"]
    if not np.isfinite(raw_depth).all() or np.any(raw_depth < 0):
        raise ValueError("Invalid new sediment depth from native solver")
    candidate = owner.copy(deep=True)
    result_mass = raw_depth.reshape(SHAPE) * DENSITY_KG_M3 * AREA_M2
    candidate["soil_mass_kg"].values[:] = result_mass
    candidate.attrs["exported_soil_kg"] = (
        float(owner.attrs["exported_soil_kg"]) +
        float(suspended_m3 + bedload_m3) * DENSITY_KG_M3
    )
    metrics = validate(candidate, baseline)  # before publication
    return candidate, metrics


def execute(k_sed):
    grid, flow, space, owner = make_scene(k_sed)
    baseline = float(owner.attrs["initial_soil_kg"])
    original = owner["soil_mass_kg"].values.copy()
    flux_erosion_steps = flux_deposition_steps = 0
    last = None
    for _ in range(STEPS):
        candidate, last = advance_native_step(grid, flow, space, owner, baseline)
        erosion = grid.at_node["sediment__erosion_flux"][grid.core_nodes]
        deposition = grid.at_node["sediment__deposition_flux"][grid.core_nodes]
        flux_erosion_steps += int(np.any(erosion > 1e-15))
        flux_deposition_steps += int(np.any(deposition > 1e-15))
        owner = candidate  # publish only after validating whole candidate
    mask = owner["is_core_node"].values.astype(bool)
    increase = int(np.count_nonzero((owner["soil_mass_kg"].values - original)[mask] > 1e-6))
    assert last is not None
    return {
        "owner": owner, "original": original,
        "initial_mass_kg": baseline,
        "net_gain_node_count": increase,
        "erosion_steps": flux_erosion_steps,
        "deposition_steps": flux_deposition_steps,
        "mass_ledger": last,
        "height_change_max_m": float(np.max(np.abs(topography(owner) -
                         (owner["bedrock_elevation_m"].values +
                          original/(DENSITY_KG_M3*AREA_M2))))),
    }


def negative_cases(good):
    original_sha = checksum(good)
    baseline = float(good.attrs["initial_soil_kg"])
    cases = {}
    def try_reject(name, mutate):
        bad = good.copy(deep=True)
        mutate(bad)
        try:
            validate(bad, baseline)
        except ValueError:
            cases[name] = True
        else:
            raise AssertionError(f"Invalid candidate accepted: {name}")
        assert checksum(good) == original_sha, "Rejected candidate mutated committed owner"
    try_reject("unaccounted_source", lambda x: x["soil_mass_kg"].values.__setitem__((7,7), x["soil_mass_kg"].values[7,7]+1))
    try_reject("negative_mass", lambda x: x["soil_mass_kg"].values.__setitem__((7,7), -1.0))
    try_reject("invalid_units", lambda x: x["soil_mass_kg"].attrs.__setitem__("units", "g"))
    try_reject("boundary_material", lambda x: x["soil_mass_kg"].values.__setitem__((0,5), 1.0))
    try_reject("shrinking_outflow", lambda x: x.attrs.__setitem__("exported_soil_kg", -1.0))
    return cases


def main():
    active = execute(K_ACTIVE)
    control = execute(0.0)
    replay = execute(K_ACTIVE)
    a, c, r = (z["owner"] for z in (active, control, replay))
    assert active["net_gain_node_count"] > 0, "No receiving core node gained sediment"
    assert active["erosion_steps"] > 0 and active["deposition_steps"] > 0
    assert active["mass_ledger"]["export_kg"] > 0
    assert active["height_change_max_m"] > 0
    assert control["mass_ledger"]["export_kg"] == 0
    assert control["erosion_steps"] == 0 and control["deposition_steps"] == 0
    assert np.array_equal(c["soil_mass_kg"].values, control["original"])
    assert np.array_equal(a["soil_mass_kg"].values, r["soil_mass_kg"].values)
    assert a.attrs["exported_soil_kg"] == r.attrs["exported_soil_kg"]
    rejected = negative_cases(a)
    with tempfile.TemporaryDirectory(prefix="world_h9_") as folder:
        file = pathlib.Path(folder)/"sediment_owner.nc"
        a.to_netcdf(file, engine="scipy")
        with xr.open_dataset(file, engine="scipy") as fh:
            loaded = fh.load()
        assert np.array_equal(a["soil_mass_kg"].values, loaded["soil_mass_kg"].values)
        assert np.array_equal(topography(a), topography(loaded))
        assert checksum(a) == checksum(loaded)
        assert validate(loaded, active["initial_mass_kg"])
        assert "soil__depth" not in loaded and "topographic__elevation" not in loaded
        size = file.stat().st_size
    print("WORLD_EVAL_JSON " + json.dumps({
        "experiment": "E1 H9 native sediment transport to one owned xarray ledger",
        "python": platform.python_version(),
        "landlab_version": landlab.__version__, "xarray_version": xr.__version__,
        "steps": STEPS, "dt_experimental": DT,
        "shape": SHAPE, "cell_area_m2": AREA_M2,
        "density_kg_m3_abstract": DENSITY_KG_M3,
        "active": {k:v for k,v in active.items() if k not in ("owner","original")},
        "control": {k:v for k,v in control.items() if k not in ("owner","original")},
        "replay_equal": True,
        "negative_candidate_rejections": rejected,
        "netcdf_bytes": size,
        "checkpoint_equal": True,
        "owner_sha256": checksum(a),
        "limitations": "2.5D fluvial sediment, idealized boundary, no 3D granular motion, ROI coupling, energy, calibration, emergence or physical terrain-to-voxel conversion."
    }, sort_keys=True))


if __name__ == "__main__":
    main()
