"""E3 H26: preregistered gradually fed, unconfined 3D granular-pile experiment.

Only native PyBullet3.2.7 physics, H24's contact/friction and owner checks.
Pre-registered: ETAPA_3_H26_PROTOCOLO_DEPOSITO_GRADUAL.md.
All 125 grains exist in a source inventory from t0; no simulated bodies
exist until their individually checked release. We do not present future
feed locations as physical positions.
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
M=h24.M
R=h24.R
DT=h24.DT
G=h24.G
MAX_RELEASE_STEP=10200
MAX_STEP=12000
POST=(1200,1800)
LOOKAHEAD=36
CLEARANCE=1.04*(2*R)
SEEDS=(h24.SEED1,h24.SEED2)


def feed_plan(seed):
    rng=np.random.default_rng(seed)
    polar=rng.random((N,2))
    radii=.17*np.sqrt(polar[:,0])
    angles=2*np.pi*polar[:,1]
    xyz=np.zeros((N,3),dtype=np.float64)
    xyz[:,0]=radii*np.cos(angles)
    xyz[:,1]=radii*np.sin(angles)
    xyz[:,2]=1.50
    return xyz


def final_owner(seed,friction,positions,velocities,omega,quaternions,step):
    # Canonical inventory is complete before feeding; there are no
    # fictional world positions for grains still in the feed reservoir.
    values={
        "material_mass_kg":(("grain",),np.full(N,M),{"units":"kg","role":"one material inventory"}),
        "radius_m":(("grain",),np.full(N,R),{"units":"m","role":"sphere geometry"}),
        "position_m":(("grain","xyz"),positions,{"units":"m"}),
        "velocity_mps":(("grain","xyz"),velocities,{"units":"m/s"}),
        "angular_velocity_rad_s":(("grain","xyz"),omega,{"units":"rad/s"}),
        "orientation_xyzw":(("grain","quat"),quaternions,{"units":"1"}),
    }
    owner=xr.Dataset(values,coords={"grain":np.arange(N,dtype=np.int32),
                        "xyz":["x","y","z"],"quat":["x","y","z","w"]},
            attrs={"schema_version":1,"seed":int(seed),"friction":int(bool(friction)),
                  "gravity":1,"time_s":step*DT,
                  "boundary":"infinite ground plane; no lateral walls"})
    h24.STEPS=step
    h24.check(owner,seed,friction,True)
    return owner


def run(seed,friction):
    xyz=feed_plan(seed)
    order=list(range(N))
    bodies={}
    emitted=[]
    samples={}
    source_mass_initial=N*M
    cid=p.connect(p.DIRECT)
    if cid<0:
        raise RuntimeError("Bullet DIRECT unavailable")
    slide,roll,spin=h24.ACTIVE if friction else h24.NO_FRICTION
    last_release=None
    final_step=None
    min_clearance_at_release=float("inf")
    max_mass_ledger_error=0.0
    try:
        p.setPhysicsEngineParameter(fixedTimeStep=DT,numSolverIterations=60,
            deterministicOverlappingPairs=1,physicsClientId=cid)
        p.setGravity(0,0,G,physicsClientId=cid)
        floor_shape=p.createCollisionShape(p.GEOM_PLANE,planeNormal=[0,0,1],physicsClientId=cid)
        floor=p.createMultiBody(baseMass=0,baseCollisionShapeIndex=floor_shape,physicsClientId=cid)
        p.changeDynamics(floor,-1,lateralFriction=slide,restitution=0,physicsClientId=cid)
        shape=p.createCollisionShape(p.GEOM_SPHERE,radius=R,physicsClientId=cid)
        for step in range(1,MAX_STEP+1):
            if last_release is None and step%4==0 and step<=MAX_RELEASE_STEP and order:
                # Check the native physical positions of all released grains.
                live=np.asarray([p.getBasePositionAndOrientation(b,physicsClientId=cid)[0]
                       for b in bodies.values()],dtype=np.float64).reshape((-1,3))
                best=None
                best_gap=float("inf")
                for j in range(min(LOOKAHEAD,len(order))):
                    index=order[j]
                    if len(live):
                        gap=float(np.min(np.linalg.norm(live-xyz[index],axis=1)))
                    else:
                        gap=float("inf")
                    if gap>CLEARANCE:
                        best=(j,index)
                        best_gap=gap
                        break
                if best is not None:
                    j,index=best
                    order[0],order[j]=order[j],order[0]
                    order.pop(0)
                    body=p.createMultiBody(baseMass=M,baseCollisionShapeIndex=shape,
                          basePosition=xyz[index].tolist(),baseOrientation=[0,0,0,1],
                          physicsClientId=cid)
                    p.resetBaseVelocity(body,linearVelocity=[0,0,0],
                         angularVelocity=[0,0,0],physicsClientId=cid)
                    p.changeDynamics(body,-1,lateralFriction=slide,rollingFriction=roll,
                         spinningFriction=spin,restitution=0,
                         linearDamping=.02,angularDamping=.02,physicsClientId=cid)
                    bodies[index]=body
                    emitted.append({"grain_id":index,"step":step})
                    min_clearance_at_release=min(min_clearance_at_release,best_gap)
                    if not order:
                        last_release=step
            balance_error=abs((len(order)+len(bodies))*M-source_mass_initial)
            max_mass_ledger_error=max(max_mass_ledger_error,balance_error)
            if len(order)+len(bodies)!=N or balance_error>1e-12:
                raise ValueError("Source and released material out of balance")
            p.stepSimulation(physicsClientId=cid)
            if last_release is not None:
                offset=step-last_release
                if offset in POST:
                    if len(bodies)!=N:
                        raise RuntimeError("Incomplete physical feed at post-release sample")
                    ordered=[bodies[i] for i in range(N)]
                    samples[offset]=h24.collect(ordered,cid)
                if offset==POST[-1]:
                    final_step=step
                    break
        if last_release is None or last_release>MAX_RELEASE_STEP or final_step is None:
            print("WORLD_EVAL_JSON "+json.dumps({
                "experiment":"E3 H26 gradual feed",
                "failed_preregistered_gates":["source_did_not_empty_in_time"],
                "seed":seed,"friction":friction,
                "released_grains":len(bodies),
                "source_remaining":len(order),
                "last_release_step":last_release,
                "max_step":MAX_STEP
            }),flush=True)
            raise ValueError("H26 feed did not complete by preregistered limit")
        ids=[bodies[i] for i in range(N)]
        component,grain_contacts,floor_contacts=h24.contact_sizes(
            p.getContactPoints(physicsClientId=cid),ids,floor)
    finally:
        p.disconnect(physicsClientId=cid)
    last=samples[POST[-1]]
    owner=final_owner(seed,friction,last["position_m"],
        last["velocity_mps"],last["angular_velocity_rad_s"],
        last["orientation_xyzw"],final_step)
    previous=samples[POST[0]]["position_m"]
    pos=last["position_m"]
    speed=np.linalg.norm(last["velocity_mps"],axis=1)
    return {
        "owner":owner,"samples":samples,"release_sequence":emitted,
        "seed":seed,"friction":friction,"released_count":len(bodies),
        "last_release_step":last_release,"end_step":final_step,
        "release_first_step":emitted[0]["step"],
        "min_release_clearance_m":min_clearance_at_release,
        "max_source_ledger_residual_kg":max_mass_ledger_error,
        "mass_kg":h24.check(owner,seed,friction,True),
        "top_height_m":float(np.max(pos[:,2]+R)),
        "grains_high":int(np.count_nonzero(pos[:,2]>.26)),
        "largest_contact_component":int(component),
        "grain_contacts":int(grain_contacts),
        "floor_contacts":int(floor_contacts),
        "radial_p90_m":float(np.quantile(np.linalg.norm(pos[:,:2],axis=1),.90)),
        "median_late_displacement_m":float(np.median(np.linalg.norm(pos-previous,axis=1))),
        "p90_final_speed_m_s":float(np.quantile(speed,.90)),
        "sha256":h24.state_sha(owner)
    }


def main():
    a=run(SEEDS[0],True)
    b=run(SEEDS[1],True)
    zero=run(SEEDS[0],False)
    replay=run(SEEDS[0],True)
    failed=[]
    def gate(name,ok):
        if not ok:
            failed.append(name)
    cases=(a,b,zero,replay)
    gate("all_grains_released",all(x["released_count"]==N
              and x["last_release_step"]<=MAX_RELEASE_STEP
              and x["end_step"]-x["last_release_step"]==1800
              and x["max_source_ledger_residual_kg"]<1e-12
              and x["min_release_clearance_m"]>CLEARANCE for x in cases))
    gate("material_stock_unchanged",all(x["mass_kg"]==N*M for x in cases))
    for key,c in (("active_seed1",a),("active_seed2",b)):
        gate(key+"_significant_pile",c["top_height_m"]>.36 and
             c["grains_high"]>=30)
        gate(key+"_supported_component",c["largest_contact_component"]>=45
             and c["grain_contacts"]>0 and c["floor_contacts"]>0)
        gate(key+"_natural_settling",c["median_late_displacement_m"]<.025
             and c["p90_final_speed_m_s"]<.08)
    gate("friction_increases_height",a["top_height_m"]>=zero["top_height_m"]+.08)
    gate("friction_restricts_spread",a["radial_p90_m"]<=zero["radial_p90_m"]-.06)
    gate("friction_connects",a["largest_contact_component"]>=zero["largest_contact_component"]+10)
    gate("independent_seed_different_geometry",
         np.max(np.abs(a["owner"]["position_m"].values-b["owner"]["position_m"].values))>.01)
    gate("exact_replay",a["release_sequence"]==replay["release_sequence"] and
         a["last_release_step"]==replay["last_release_step"] and
         all(np.array_equal(a["owner"][field].values,replay["owner"][field].values)
             for field in ("position_m","velocity_mps","angular_velocity_rad_s","orientation_xyzw"))
         and all(np.array_equal(a["samples"][offset][field],replay["samples"][offset][field])
             for offset in POST for field in a["samples"][offset]))
    # The old validator uses a fixed number of steps in metadata.
    h24.STEPS=a["end_step"]
    rejected=h24.bad_states(a["owner"])
    with tempfile.TemporaryDirectory(prefix="world_h26_") as td:
        path=pathlib.Path(td)/"granular_feed_owner.nc"
        a["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as fd:
            restored=fd.load()
        h24.check(restored,a["seed"],True,True)
        gate("owner_NetCDF_sha",h24.state_sha(restored)==a["sha256"])
        snapshot_size=path.stat().st_size
    def public(x):
        return {k:v for k,v in x.items() if k not in ("owner","samples","release_sequence")}
    result={
        "experiment":"E3 H26 gradual nonoverlapping feed of rigid grains on unconfined ground",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "n_grains":N,"radius_m":R,"per_grain_kg":M,"total_kg":N*M,
        "release_check_interval_steps":4,"lookahead":LOOKAHEAD,
        "clearance_m":CLEARANCE,
        "active_seed1":public(a),"active_seed2":public(b),
        "zero_friction":public(zero),
        "release_sequence_sha256_active":hashlib.sha256(json.dumps(a["release_sequence"],sort_keys=True).encode()).hexdigest(),
        "rejected_invalid_owner_states":rejected,
        "replay_exact":True,
        "NetCDF_bytes":snapshot_size,
        "failed_preregistered_gates":failed,
        "limitations":"Source grain reservoir is accounted by ID/amount but has no finite physical geometry or checkpoint mid-feed; published owner only at fully fed end. No 3D deformable soil, no cohesion or calibrated sand."
    }
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True),flush=True)
    if failed:
        raise AssertionError("H26 preregistered gates failed: "+", ".join(failed))


if __name__=="__main__":
    main()
