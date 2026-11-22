"""H12: longitudinal 3D sand settling with pinned upstream GeoMPM.

No locally coded constitutive physics. Preregistered conditions:
WORLD_RESEARCH/ETAPA_1_H12_PROTOCOLO_REPOSO_MPM.md
"""
from __future__ import annotations
import hashlib
import json
import platform
import time

import numpy as np
import torch
import xarray as xr

from probe_e1_h11_upstream_mpm3d import (
    original_solver, validate_owner, hash_owner, UPSTREAM_SHA
)

DOMAIN = (0.80, 0.80, 0.36)
DX = 0.025
LO = (0.30, 0.30, 0.075)
HI = (0.45, 0.45, 0.225)
TIMES = (0.0, 0.4, 0.8, 1.2)
T_END = 1.2


def make_case(provider, g, phi):
    sim = provider.GeoMPM(
        domain=DOMAIN, dx=DX,
        gravity=(0.0, 0.0, g), floor="friction", walls="slip",
        wall_friction=0.5, dtype=torch.float64,
    )
    count = sim.add_body(
        provider.box(LO, HI),
        provider.Sand(E=20000.0, nu=0.3, rho=1600.0, friction_deg=phi),
        ppc=1, name="A"
    )
    masses = sim.m.detach().cpu().numpy().copy()
    owner = xr.Dataset(
        {"mass_kg": (("particle_id",),masses,
          {"units":"kg","meaning":"canonical material inventory; upstream sim mass only physics cache"})},
        coords={"particle_id":np.arange(count,dtype=np.int32)},
        attrs={"schema_version":1,"material":"A","upstream_sha":UPSTREAM_SHA},
    )
    total = validate_owner(owner, masses)
    owner_digest = hash_owner(owner)
    start = time.perf_counter()
    frames = sim.run(t_end=T_END,save_every=0.4,out=None)
    elapsed = time.perf_counter()-start
    if len(frames)!=len(TIMES):
        raise ValueError("Unexpected number of temporal observations")
    for t, f in zip(TIMES,frames):
        if abs(float(f["time"])-t)>1e-7:
            raise ValueError("Time/snapshot mismatch")
    if not np.array_equal(sim.m.detach().cpu().numpy(),masses):
        raise ValueError("Upstream solver changed particle material mass")
    if hash_owner(owner)!=owner_digest:
        raise ValueError("Owner inventory changed without ledger")
    for f in frames:
        if not all(np.isfinite(f[k]).all() for k in ("position","velocity","volume","stress")):
            raise ValueError("Nonfinite material field")
        if np.any(f["volume"]<=0):
            raise ValueError("Nonpositive material point volume")
    out=[]
    for f in frames:
        x=np.asarray(f["position"])
        v=np.asarray(f["velocity"])
        q=np.quantile(x,[.01,.99],axis=0)
        bounds_xy = (
            (x[:,0] <= 2.5*DX) | (x[:,0] >= DOMAIN[0]-2.5*DX)
            | (x[:,1] <= 2.5*DX) | (x[:,1] >= DOMAIN[1]-2.5*DX)
        )
        clamp = np.isclose(x[:,2],1.5*DX,rtol=0,atol=1e-10)
        out.append({
            "time_s":float(f["time"]),
            "centroid_m":np.average(x,weights=masses,axis=0).tolist(),
            "max_speed_m_s":float(np.linalg.norm(v,axis=1).max()),
            "q01_xyz_m":q[0].tolist(),
            "q99_xyz_m":q[1].tolist(),
            "particle_count_xy_boundary_band":int(bounds_xy.sum()),
            "floor_position_clamp_fraction":float(clamp.mean()),
            "q_vertical_span_m":float(q[1,2]-q[0,2]),
        })
    return {
        "owner":owner,
        "frames":frames,
        "observations":out,
        "total_mass_kg":total,
        "n_particles":count,
        "owner_sha256":owner_digest,
        "wall_clock_s":elapsed,
        "gravity_m_s2":g,
        "sand_phi_deg":phi,
    }


def gates(a,b,c,r):
    fail=[]
    def check(name,ok):
        if not ok: fail.append(name)
    obs=a["observations"]
    final=obs[-1]
    prev=obs[-2]
    check("same_mass_across_conditions",a["owner_sha256"]==b["owner_sha256"]==c["owner_sha256"]==r["owner_sha256"]
          and a["total_mass_kg"]==b["total_mass_kg"]==c["total_mass_kg"]==r["total_mass_kg"])
    check("grain_count",10<=a["n_particles"]<=1000 and
          a["n_particles"]==b["n_particles"]==c["n_particles"]==r["n_particles"])
    check("gravity_centroid_drop",obs[0]["centroid_m"][2]-final["centroid_m"][2]>0.05)
    b0,bf=b["frames"][0],b["frames"][-1]
    check("zero_gravity_position",np.max(np.abs(b0["position"]-bf["position"]))<1e-8)
    check("zero_gravity_velocity",np.max(np.abs(bf["velocity"]))<1e-8)
    check("lateral_boundary_free",final["particle_count_xy_boundary_band"]==0)
    check("rest_speed",final["max_speed_m_s"]<0.05)
    bound_deltas={}
    for axis in (0,1):
        for qname in ("q01_xyz_m","q99_xyz_m"):
            delta=abs(prev[qname][axis]-final[qname][axis])
            bound_deltas[f"{qname}[{axis}]"]=delta
            check(f"shape_stable_{qname}_{axis}",delta<0.005)
    dz=abs(prev["q99_xyz_m"][2]-final["q99_xyz_m"][2])
    bound_deltas["q99_z"]=dz
    check("shape_stable_q99_z",dz<0.005)
    check("z_span_exceeds_dx",final["q_vertical_span_m"]>DX)
    check("floor_clamp_fraction_low",final["floor_position_clamp_fraction"]<=0.5)
    exact=True
    for fr,rf in zip(a["frames"],r["frames"]):
        for k in ("position","velocity"):
            exact=exact and np.array_equal(fr[k],rf[k])
    check("deterministic_replay",exact)
    material_delta=float(np.mean(np.abs(a["frames"][-1]["position"]-
                                        c["frames"][-1]["position"])))
    return fail,{"relative_sand_friction_position_L1_mean_m":material_delta,
                 "late_shape_quantile_deltas_m":bound_deltas,
                 "replay_exact":exact,
                 "rest_speed_threshold_m_s":0.05,
                 "late_shape_threshold_m":0.005,
                 "measured_stability_accepted":not fail}


def main():
    torch.set_num_threads(1)
    provider=original_solver()
    a=make_case(provider,-9.81,30.0)
    b=make_case(provider,0.0,30.0)
    c=make_case(provider,-9.81,0.0)
    replay=make_case(provider,-9.81,30.0)
    failures,analysis=gates(a,b,c,replay)
    def report_case(d):
        return {k:v for k,v in d.items() if k not in ("frames","owner")}
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"E1 H12 settling of 3D MPM with wide xy boundaries",
        "upstream":"PINNeAPPle-Labs/PINNeAPPle",
        "upstream_commit":UPSTREAM_SHA,
        "python":platform.python_version(),
        "torch":torch.__version__,"xarray":xr.__version__,
        "domain_m":DOMAIN,"dx_m":DX,
        "initial_block_lo_m":LO,"initial_block_hi_m":HI,
        "active_phi30":report_case(a),"no_gravity_phi30":report_case(b),
        "active_phi0":report_case(c),
        "analysis":analysis,
        "failed_preregistered_gates":failures,
        "limitations":"Longitudinal 1.2s only, no geological calibration, no benchmark against 3D physical data, no Landlab/ROI coupling, no full solver restart, no open-ended emergence."
    },sort_keys=True),flush=True)
    if failures:
        raise AssertionError("H12 preregistered physical gates failed: "+", ".join(failures))


if __name__=="__main__":
    main()
