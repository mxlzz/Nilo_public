"""H11: use pinned upstream 3D MPM, not locally implemented physical laws.

Refer to ETAPA_1_H11_PROTOCOLO_MPM_3D.md (preregistered before code).
Upstream is loaded from temporary checkout, with no dependency on its UI.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import pathlib
import platform
import sys
import tempfile
import time

import numpy as np
import torch
import xarray as xr

UPSTREAM_SHA = "c8a6e3dce5daedd10903cc68f7f3a062c42b8bc4"
DOMAIN = (0.60, 0.24, 0.36)
BOX_LO = (0.075, 0.075, 0.075)
BOX_HI = (0.225, 0.150, 0.225)
GRID_DX = 0.025
T_END = 0.25


def original_solver():
    path = os.environ.get("PINNEAPPLE_GEO_MPM_PATH")
    if not path or not pathlib.Path(path).is_file():
        raise RuntimeError("Expected a pinned original upstream geo_mpm.py path; never replace with own solver")
    spec = importlib.util.spec_from_file_location("pinned_upstream_geo_mpm", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load native upstream MPM")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def hash_owner(ds):
    return hashlib.sha256(
        ds["mass_kg"].values.tobytes()
        + ds.coords["particle_id"].values.tobytes()
    ).hexdigest()


def validate_owner(ds, expected_mass):
    if set(ds.data_vars) != {"mass_kg"}:
        raise ValueError("Not a single-owner inventory")
    if tuple(ds["mass_kg"].dims) != ("particle_id",):
        raise ValueError("Invalid owner dimensions")
    if ds["mass_kg"].attrs.get("units") != "kg" or ds.attrs.get("schema_version") != 1:
        raise ValueError("Invalid material units/schema")
    mass = np.asarray(ds["mass_kg"].values)
    ids = np.asarray(ds.coords["particle_id"].values)
    if len(mass) < 10 or len(mass) > 1000:
        raise ValueError("Unexpected particle count")
    if not np.array_equal(ids, np.arange(len(mass))):
        raise ValueError("Particle ID mismatch")
    if not np.isfinite(mass).all() or np.any(mass <= 0):
        raise ValueError("Invalid particle mass")
    if not np.array_equal(mass, expected_mass):
        raise ValueError("Unaccounted material source or sink")
    return float(mass.sum())


def negative_cases(owner):
    original = hash_owner(owner)
    mass = owner["mass_kg"].values.copy()
    rejected = {}
    def reject(name, mutate):
        invalid = owner.copy(deep=True)
        mutate(invalid)
        try:
            validate_owner(invalid, mass)
        except ValueError:
            rejected[name] = True
        else:
            raise AssertionError("Invalid material candidate accepted: " + name)
        assert hash_owner(owner) == original
    reject("source_plus_1kg", lambda ds: ds["mass_kg"].values.__setitem__(0, ds["mass_kg"].values[0]+1.0))
    reject("negative_mass", lambda ds: ds["mass_kg"].values.__setitem__(0, -0.1))
    reject("wrong_mass_units", lambda ds: ds["mass_kg"].attrs.__setitem__("units", "g"))
    reject("invalid_particle_id", lambda ds: ds.coords.__setitem__(
        "particle_id", np.r_[999, np.arange(1, ds.sizes["particle_id"])]
    ))
    return rejected


def run_case(solver_module, gravity, angle):
    sim = solver_module.GeoMPM(
        domain=DOMAIN, dx=GRID_DX, gravity=(0.,0.,gravity),
        floor="friction", walls="slip", wall_friction=0.5,
        dtype=torch.float64
    )
    n = sim.add_body(
        solver_module.box(BOX_LO, BOX_HI),
        solver_module.Sand(friction_deg=angle, E=20000.0, nu=0.3, rho=1600.0),
        ppc=1, name="A",
    )
    if not 10 <= n <= 1000 or len(sim.x.shape)!=2 or sim.x.shape[1]!=3:
        raise ValueError("Scene is not an actual small 3D MPM setup")
    initial_mass = sim.m.detach().cpu().numpy().copy()
    owner = xr.Dataset(
        data_vars={
            "mass_kg": (("particle_id",), initial_mass,
                       {"units":"kg","meaning":"sole material inventory of MPM particles"})
        },
        coords={"particle_id":np.arange(n, dtype=np.int32)},
        attrs={"schema_version":1, "material":"A", "upstream_sha":UPSTREAM_SHA}
    )
    valid_mass = validate_owner(owner, initial_mass)
    before = hash_owner(owner)
    init=sim.frame(0.0)
    started=time.perf_counter()
    frames=sim.run(t_end=T_END, save_every=T_END, out=None)
    wall_seconds=time.perf_counter()-started
    if len(frames)<2 or abs(float(frames[-1]["time"])-T_END)>1e-7:
        raise AssertionError("Upstream did not produce requested physical interval")
    final=frames[-1]
    x0,x1=np.asarray(init["position"]),np.asarray(final["position"])
    v0,v1=np.asarray(init["velocity"]),np.asarray(final["velocity"])
    vol=np.asarray(final["volume"])
    f_mass=sim.m.detach().cpu().numpy()
    if not (np.isfinite(x1).all() and np.isfinite(v1).all()
            and np.isfinite(vol).all() and np.all(vol>0)):
        raise ValueError("Nonfinite or nonpositive 3D material state")
    if not np.allclose(f_mass, initial_mass, rtol=1e-12, atol=0.0):
        raise AssertionError("Solver changed material point mass")
    assert np.array_equal(owner["mass_kg"].values, initial_mass)
    assert hash_owner(owner)==before
    assert valid_mass>0
    centroid_before=np.average(x0,weights=initial_mass,axis=0)
    centroid_after=np.average(x1,weights=initial_mass,axis=0)
    with tempfile.TemporaryDirectory(prefix="world_h11_") as tmp:
        path=pathlib.Path(tmp)/"owner.nc"
        owner.to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:
            loaded=f.load()
        assert validate_owner(loaded,initial_mass)==valid_mass
        assert hash_owner(loaded)==before
        snapshot_exact=True
    return {
        "owner":owner, "initial":init, "final":final,
        "particle_count":n, "total_mass_kg":valid_mass,
        "mass_per_particle_exact":True,
        "owner_sha256":before, "snapshot_exact":snapshot_exact,
        "initial_centroid_m":centroid_before.tolist(),
        "final_centroid_m":centroid_after.tolist(),
        "center_of_mass_z_drop_m":float(centroid_before[2]-centroid_after[2]),
        "max_position_displacement_m":float(np.max(np.abs(x1-x0))),
        "longitudinal_max_change_m":float(np.max(np.abs(x1[:,0]-x0[:,0]))),
        "runout_x99_m":float(np.quantile(x1[:,0],.99)),
        "width_x99_minus_x01_m":float(np.quantile(x1[:,0],.99)-np.quantile(x1[:,0],.01)),
        "vertical_height_m":float(x1[:,2].max()-x1[:,2].min()),
        "peak_speed_m_s":float(np.linalg.norm(v1,axis=1).max()),
        "mean_speed_m_s":float(np.linalg.norm(v1,axis=1).mean()),
        "wall_seconds":wall_seconds,
        "end_time_s":float(final["time"])
    }


def main():
    torch.set_num_threads(1)
    module=original_solver()
    a=run_case(module,-9.81,30.0)
    b=run_case(module,0.,30.0)
    c=run_case(module,-9.81,0.0)
    replay=run_case(module,-9.81,30.0)
    assert a["center_of_mass_z_drop_m"]>0.015, "No gravitational deformation"
    assert a["longitudinal_max_change_m"]>0.005, "No lateral deformation"
    assert b["max_position_displacement_m"]<1e-8, "Zero gravity scene moved"
    assert b["peak_speed_m_s"]<1e-8, "Nonzero motion with zero gravity"
    friction_l1=float(np.mean(np.abs(a["final"]["position"]-c["final"]["position"])))
    assert friction_l1>0.002, "No measurable material friction sensitivity"
    assert np.array_equal(a["final"]["position"],replay["final"]["position"]), "Position replay differs"
    assert np.array_equal(a["final"]["velocity"],replay["final"]["velocity"]), "Velocity replay differs"
    assert np.array_equal(a["owner"]["mass_kg"].values,replay["owner"]["mass_kg"].values)
    rejected=negative_cases(a["owner"])
    if not all([a["snapshot_exact"],b["snapshot_exact"],c["snapshot_exact"],replay["snapshot_exact"]]):
        raise AssertionError("Owner snapshot mismatch")

    def public(case):
        return {k:v for k,v in case.items() if k not in ("owner","initial","final")}
    report={
        "experiment":"E1 H11 3D MPM plastic sand from pinned upstream; no new physical law",
        "upstream_repository":"PINNeAPPle-Labs/PINNeAPPle",
        "upstream_sha":UPSTREAM_SHA,"python":platform.python_version(),
        "torch":torch.__version__,"xarray":xr.__version__,
        "upstream_material":"Sand/Drucker-Prager","density_kg_m3":1600.,
        "young_modulus_Pa":20000.,"dt":"upstream automatic CFL",
        "grid_dx_m":GRID_DX,"domain_m":DOMAIN,
        "active_30deg":public(a),"zero_gravity_30deg":public(b),
        "active_0deg":public(c),
        "friction_mean_l1_position_diff_m":friction_l1,
        "replay_exact_same_cpu":True,
        "invalid_owner_candidates_rejected":rejected,
        "limitations":"Isolated tiny 3D MPM, no calibrated 3D soil benchmark, no demonstrated final rest, no mixed materials, cavitation or coupling with Landlab/ROI, no energy conservation test."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
