"""H26: gravity-fed granular pile, upstream PyBullet, no side walls.

The release mechanism prevents initial overlap; all contacts are solved
by PyBullet, not hand-coded. H26 preregistered before this script.
The source material ledger is explicit; full world-state persistence during
feeding is NOT claimed. Final material+pose owner is validated in xarray.
"""
from __future__ import annotations
import hashlib
import json
import math
import pathlib
import platform
import tempfile
from importlib.metadata import version

import numpy as np
import pybullet as p
import xarray as xr

import probe_e3_h24_granular_pile as h24

N=h24.N
R=h24.R
M=h24.M
DT=h24.DT
GRAVITY=h24.G
SEEDS=(h24.SEED1,h24.SEED2)
OUTLET_RADIUS=.17
OUTLET_Z=1.50
CHECK_EVERY=4
LOOKAHEAD=36
MAX_FEED_STEP=10200
POST_RELEASE=1800
MAX_STEPS=12000
SAMPLES_AFTER=(1200,1800)
MIN_SPAWN_SEPARATION=1.04*(2*R)

def feed_plan(seed):
    rng=np.random.default_rng(seed)
    u=rng.random((N,2))
    radii=OUTLET_RADIUS*np.sqrt(u[:,0])
    angles=2*np.pi*u[:,1]
    return [(i,np.array([radii[i]*np.cos(angles[i]),
          radii[i]*np.sin(angles[i]),OUTLET_Z],dtype=np.float64))
          for i in range(N)]

def main_scene(seed, friction):
    plan=feed_plan(seed)
    ids=[]
    release=[]
    states={}
    last_release_step=None
    peak_residual=0.
    slide,rolling,spinning=h24.ACTIVE if friction else h24.NO_FRICTION
    cid=p.connect(p.DIRECT)
    try:
        p.setPhysicsEngineParameter(
            fixedTimeStep=DT,numSolverIterations=60,
            deterministicOverlappingPairs=1,physicsClientId=cid)
        p.setGravity(0,0,GRAVITY,physicsClientId=cid)
        floor_shape=p.createCollisionShape(p.GEOM_PLANE,
                          planeNormal=[0,0,1],physicsClientId=cid)
        floor=p.createMultiBody(baseMass=0,baseCollisionShapeIndex=floor_shape,
                                physicsClientId=cid)
        p.changeDynamics(floor,-1,lateralFriction=slide,restitution=0.,
                         physicsClientId=cid)
        shape=p.createCollisionShape(p.GEOM_SPHERE,radius=R,physicsClientId=cid)
        step_end=None
        for step in range(1,MAX_STEPS+1):
            if step%CHECK_EVERY==0 and plan and last_release_step is None:
                selected=None
                for idx in range(min(LOOKAHEAD,len(plan))):
                    _,pos=plan[idx]
                    safe=True
                    for body in ids:
                        xyz=p.getBasePositionAndOrientation(body,physicsClientId=cid)[0]
                        if np.linalg.norm(np.asarray(xyz)-pos)<=MIN_SPAWN_SEPARATION:
                            safe=False
                            break
                    if safe:
                        selected=idx
                        break
                if selected is not None:
                    origin_id,pos=plan.pop(selected)
                    body=p.createMultiBody(baseMass=M,baseCollisionShapeIndex=shape,
                                basePosition=pos.tolist(),physicsClientId=cid)
                    p.changeDynamics(body,-1,lateralFriction=slide,
                                rollingFriction=rolling,spinningFriction=spinning,
                                restitution=0.,linearDamping=.02,angularDamping=.02,
                                physicsClientId=cid)
                    ids.append(body)
                    release.append((step,int(origin_id)))
                    assert len(ids)<=N
                    if not plan:
                        last_release_step=step
            live_kg=float(len(ids)*M)
            source_kg=float((N-len(ids))*M)
            residual=live_kg+source_kg-N*M
            peak_residual=max(peak_residual,abs(residual))
            if abs(residual)>1e-12:
                raise ValueError("Material source ledger imbalanced")
            if last_release_step is None and step>=MAX_FEED_STEP:
                raise RuntimeError("Not all grains released before preregistered limit")
            p.stepSimulation(physicsClientId=cid)
            if last_release_step is not None:
                offset=step-last_release_step
                if offset in SAMPLES_AFTER:
                    states[offset]=h24.collect(ids,cid)
                if offset==POST_RELEASE:
                    step_end=step
                    break
        if step_end is None or len(ids)!=N:
            raise RuntimeError("Experiment did not finish full feed + rest")
        components,grain_contacts,floor_contacts=h24.contact_sizes(
                   p.getContactPoints(physicsClientId=cid),ids,floor)
    finally:
        p.disconnect(physicsClientId=cid)

    # The returned xarray owner is built only AFTER the source reservoir
    # fully discharges: no claim of a full xarray state during source operation.
    h24.STEPS=step_end
    candidate=h24.owner_for(seed,friction,True)
    for name,value in states[POST_RELEASE].items():
        candidate[name].values[:]=value
    candidate.attrs["time_s"]=step_end*DT
    try:
        h24.check(candidate,seed,friction,True)
    except ValueError as exc:
        print("WORLD_EVAL_JSON "+json.dumps({
            "experiment":"E3 H26","seed":seed,"friction":friction,
            "step":step_end,"failed_preregistered_gates":["nonphysical_final_owner"],
            "message":str(exc)}),flush=True)
        raise
    end=states[POST_RELEASE]
    prior=states[SAMPLES_AFTER[0]]
    pos=end["position_m"]
    movement=np.linalg.norm(pos-prior["position_m"],axis=1)
    speed=np.linalg.norm(end["velocity_mps"],axis=1)
    return {
        "owner":candidate,"snapshots":states,"release":release,
        "seed":seed,"friction":friction,
        "released_grains":len(ids),"release_complete_step":last_release_step,
        "total_step":step_end,"max_source_material_ledger_error_kg":peak_residual,
        "total_mass_kg":h24.check(candidate,seed,friction,True),
        "height_max_m":float(np.max(pos[:,2]+R)),
        "grains_above_026m":int(np.count_nonzero(pos[:,2]>.26)),
        "largest_contact_component":int(components),
        "grain_positive_contacts":int(grain_contacts),
        "floor_positive_contacts":int(floor_contacts),
        "radial_p90_m":float(np.quantile(np.linalg.norm(pos[:,:2],axis=1),.9)),
        "median_late_displacement_m":float(np.median(movement)),
        "p90_final_speed_m_s":float(np.quantile(speed,.9)),
        "release_sequence_sha":hashlib.sha256(
                   np.asarray(release,dtype=np.int64).tobytes()).hexdigest(),
        "owner_sha":h24.state_sha(candidate),
    }

def no_arrays(obj):
    return {k:v for k,v in obj.items() if k not in ("owner","snapshots","release")}

def main():
    a=main_scene(SEEDS[0],True)
    b=main_scene(SEEDS[1],True)
    mu0=main_scene(SEEDS[0],False)
    replay=main_scene(SEEDS[0],True)
    fail=[]
    def gate(name,ok):
        if not ok:fail.append(name)
    cases=(a,b,mu0,replay)
    gate("all_125_grains_released",all(x["released_grains"]==N
         and x["release_complete_step"]<MAX_FEED_STEP
         and x["total_step"]<=MAX_STEPS for x in cases))
    gate("source_plus_released_mass_conserved",all(x["total_mass_kg"]==N*M
         and x["max_source_material_ledger_error_kg"]<1e-12 for x in cases))
    for name,x in (("seed1",a),("seed2",b)):
        gate(name+"_high_heap",x["height_max_m"]>.36 and
             x["grains_above_026m"]>=30)
        gate(name+"_contact_support",x["grain_positive_contacts"]>0 and
             x["floor_positive_contacts"]>0 and
             x["largest_contact_component"]>=45)
        gate(name+"_settled",x["median_late_displacement_m"]<.025 and
             x["p90_final_speed_m_s"]<.08)
    gate("friction_effect_height",a["height_max_m"]>=mu0["height_max_m"]+.08)
    gate("friction_effect_spread",a["radial_p90_m"]<=mu0["radial_p90_m"]-.06)
    gate("friction_effect_contacts",a["largest_contact_component"]>=
         mu0["largest_contact_component"]+10)
    gate("different_seeds",np.max(np.abs(a["owner"]["position_m"].values-
                                b["owner"]["position_m"].values))>.01)
    gate("replay_release_and_physics",a["release"]==replay["release"]
         and a["owner_sha"]==replay["owner_sha"]
         and all(np.array_equal(a["owner"][k].values,replay["owner"][k].values)
         for k in ("material_mass_kg","position_m","velocity_mps",
                   "orientation_xyzw","angular_velocity_rad_s"))
         and all(all(np.array_equal(a["snapshots"][step][k],
                        replay["snapshots"][step][k]) for k in a["snapshots"][step])
                        for step in SAMPLES_AFTER))
    h24.STEPS=a["total_step"]
    rejected=h24.bad_states(a["owner"])
    with tempfile.TemporaryDirectory(prefix="world_h26_") as td:
        path=pathlib.Path(td)/"fully_released_granular_owner.nc"
        a["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:
            back=f.load()
        h24.check(back,SEEDS[0],True,True)
        gate("owner_restore_sha",h24.state_sha(back)==a["owner_sha"])
        bytes_written=path.stat().st_size
    report={
        "experiment":"E3 H26 controlled nonoverlapping gravity feed to open ground",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "grain_count":N,"radius_m":R,"per_grain_mass_kg":M,
        "outlet_z_m":OUTLET_Z,"outlet_radius_m":OUTLET_RADIUS,
        "min_separation_at_birth_m":MIN_SPAWN_SEPARATION,
        "active_seed1":no_arrays(a),"active_seed2":no_arrays(b),
        "friction_zero":no_arrays(mu0),
        "replay_exact":True,"rejected_invalid_states":rejected,
        "netcdf_bytes":bytes_written,
        "failed_preregistered_gates":fail,
        "limitations":"Slow physical feed is a prescribed boundary condition; upstream DEM is coarse rigid spheres, without natural geological cohesion. During feed the source+material ledger is checked, but only the post-feed state is a persisted xarray owner."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if fail:
        raise AssertionError("H26 preregistered gates failed: "+", ".join(fail))

if __name__=="__main__":
    main()
