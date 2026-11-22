"""E3 H24: registered unconfined granular-pile test with PyBullet 3.2.7.

No new contact physics or artificial resting placement. Existing Bullet
calculates friction and rigid contacts; xarray is canonical owner of mass
and terminal poses/velocities. See ETAPA_3_H24_PROTOCOLO_PILA_GRANULAR.md.
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
import pybullet as bullet
import xarray as xr

N=125
R=.075
M=.025
DT=1/240.
STEPS=1600
G=-9.81
SAMPLES=(1200,1600)
ACTIVE=(1.5,.15,.10)
NO_FRICTION=(0.,0.,0.)
SEED1=20261122
SEED2=20261123

def initial_positions(seed):
    rng=np.random.default_rng(seed)
    out=[]
    for k in range(5):
        for i in range(5):
            for j in range(5):
                noise=rng.uniform(-.008,.008,size=3)
                out.append([-.36+.18*i+noise[0],
                            -.36+.18*j+noise[1],
                            .78+.22*k+noise[2]])
    xyz=np.asarray(out,dtype=np.float64)
    assert xyz.shape==(N,3)
    gap=np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=-1)
    np.fill_diagonal(gap,np.inf)
    assert np.min(gap)>2*R+.005, "Initial grain overlap"
    return xyz

def owner_for(seed,friction=True,gravity=True):
    data={
        "material_mass_kg":(("grain",),np.full(N,M),{"units":"kg","role":"one material inventory"}),
        "radius_m":(("grain",),np.full(N,R),{"units":"m","role":"sphere geometry"}),
        "position_m":(("grain","xyz"),initial_positions(seed),{"units":"m"}),
        "velocity_mps":(("grain","xyz"),np.zeros((N,3)),{"units":"m/s"}),
        "angular_velocity_rad_s":(("grain","xyz"),np.zeros((N,3)),{"units":"rad/s"}),
        "orientation_xyzw":(("grain","quat"),np.tile([0.,0.,0.,1.],(N,1)),{"units":"1"})
    }
    return xr.Dataset(data,coords={"grain":np.arange(N,dtype=np.int32),
            "xyz":["x","y","z"],"quat":["x","y","z","w"]},
            attrs={"schema_version":1,"seed":int(seed),"friction":int(bool(friction)),
                   "gravity":int(bool(gravity)),"time_s":0.,
                   "boundary":"infinite ground plane; no lateral walls"})

def check(ds,seed,friction,gravity):
    fields={"material_mass_kg","radius_m","position_m","velocity_mps",
            "angular_velocity_rad_s","orientation_xyzw"}
    if set(ds.data_vars)!=fields:raise ValueError("Unexpected/doubled material or pose stock")
    if ds["material_mass_kg"].dims!=("grain",) or ds["radius_m"].dims!=("grain",):
        raise ValueError("Wrong material dimensions")
    for name in ("position_m","velocity_mps","angular_velocity_rad_s"):
        if ds[name].dims!=("grain","xyz") or ds[name].shape!=(N,3):
            raise ValueError("Wrong kinematic dimensions")
    if ds["orientation_xyzw"].dims!=("grain","quat") or ds["orientation_xyzw"].shape!=(N,4):
        raise ValueError("Wrong quaternion dimensions")
    if ds.coords["grain"].values.tolist()!=list(range(N)) or (
        ds.coords["xyz"].values.tolist()!=["x","y","z"]
        or ds.coords["quat"].values.tolist()!=["x","y","z","w"]
    ):raise ValueError("Identity or axis changed")
    for f,u in (("material_mass_kg","kg"),("radius_m","m"),("position_m","m"),
                ("velocity_mps","m/s"),("angular_velocity_rad_s","rad/s"),
                ("orientation_xyzw","1")):
        if ds[f].attrs.get("units")!=u:raise ValueError("Invalid physical unit "+f)
    expected={"schema_version":1,"seed":seed,"friction":int(bool(friction)),
              "gravity":int(bool(gravity)),
              "boundary":"infinite ground plane; no lateral walls"}
    if any(ds.attrs.get(k)!=v for k,v in expected.items()) or ds.attrs.get("time_s") not in (0.,STEPS*DT):
        raise ValueError("Changed trial identity or time")
    mass=ds["material_mass_kg"].values
    radii=ds["radius_m"].values
    xyz=ds["position_m"].values
    vel=ds["velocity_mps"].values
    omega=ds["angular_velocity_rad_s"].values
    quat=ds["orientation_xyzw"].values
    if not all(np.isfinite(q).all() for q in (mass,radii,xyz,vel,omega,quat)):
        raise ValueError("Nonfinite material/kinematic state")
    if not np.array_equal(mass,np.full(N,M)) or float(mass.sum())!=N*M:
        raise ValueError("Mass created or lost")
    if not np.array_equal(radii,np.full(N,R)):
        raise ValueError("Radius altered")
    if np.max(np.abs(np.linalg.norm(quat,axis=1)-1.))>1e-4:
        raise ValueError("Invalid orientation")
    sep=np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=-1)
    np.fill_diagonal(sep,np.inf)
    if np.min(sep)<2*R-.02:
        raise ValueError("Grain overlap exceeds contact tolerance")
    if gravity and np.min(xyz[:,2])<R-.02:
        raise ValueError("Ground penetration")
    return float(mass.sum())

def state_sha(ds):
    h=hashlib.sha256()
    for f in ("material_mass_kg","radius_m","position_m","velocity_mps",
              "angular_velocity_rad_s","orientation_xyzw"):
        a=ds[f]
        h.update(f.encode()+a.values.tobytes()+a.attrs["units"].encode())
    metadata={k:(v.item() if isinstance(v,np.generic) else v) for k,v in ds.attrs.items()}
    h.update(json.dumps(metadata,sort_keys=True).encode())
    for name in ("grain","xyz","quat"):
        h.update(repr(ds.coords[name].values.tolist()).encode())
    return h.hexdigest()

def collect(ids,cid):
    states=[]
    for body in ids:
        pos,quat=bullet.getBasePositionAndOrientation(body,physicsClientId=cid)
        vel,omega=bullet.getBaseVelocity(body,physicsClientId=cid)
        states.append((pos,vel,omega,quat))
    return {
        "position_m":np.array([x[0] for x in states],dtype=np.float64),
        "velocity_mps":np.array([x[1] for x in states],dtype=np.float64),
        "angular_velocity_rad_s":np.array([x[2] for x in states],dtype=np.float64),
        "orientation_xyzw":np.array([x[3] for x in states],dtype=np.float64)
    }

def contact_sizes(points,ids,floor):
    mapping={body:i for i,body in enumerate(ids)}
    parent=list(range(N))
    def root(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    grain_contacts=0
    floor_contacts=0
    for c in points:
        if float(c[9])<=1e-5:continue
        a,b=c[1],c[2]
        if a in mapping and b in mapping:
            ia,ib=root(mapping[a]),root(mapping[b])
            if ia!=ib:parent[ia]=ib
            grain_contacts+=1
        elif floor is not None and ((a==floor and b in mapping) or (b==floor and a in mapping)):
            floor_contacts+=1
    sizes={}
    for i in range(N):
        rt=root(i)
        sizes[rt]=sizes.get(rt,0)+1
    return max(sizes.values()),grain_contacts,floor_contacts

def execute(seed,friction=True,gravity=True):
    owner=owner_for(seed,friction,gravity)
    check(owner,seed,friction,gravity)
    original_sha=state_sha(owner)
    start=owner["position_m"].values.copy()
    cid=bullet.connect(bullet.DIRECT)
    samples={}
    try:
        bullet.setPhysicsEngineParameter(
            fixedTimeStep=DT,numSolverIterations=60,
            deterministicOverlappingPairs=1,physicsClientId=cid)
        bullet.setGravity(0.,0.,G if gravity else 0.,physicsClientId=cid)
        plane=bullet.createCollisionShape(bullet.GEOM_PLANE,
                           planeNormal=[0,0,1],physicsClientId=cid)
        floor=bullet.createMultiBody(baseMass=0,
                 baseCollisionShapeIndex=plane,physicsClientId=cid)
        slide,rolling,spinning=ACTIVE if friction else NO_FRICTION
        bullet.changeDynamics(floor,-1,lateralFriction=slide,
                 restitution=0.,physicsClientId=cid)
        shape=bullet.createCollisionShape(bullet.GEOM_SPHERE,radius=R,physicsClientId=cid)
        bodies=[]
        for pos in start:
            body=bullet.createMultiBody(baseMass=M,
                   baseCollisionShapeIndex=shape,
                   basePosition=pos.tolist(),physicsClientId=cid)
            bullet.changeDynamics(body,-1,lateralFriction=slide,
                   rollingFriction=rolling,spinningFriction=spinning,
                   restitution=0.,linearDamping=.02,angularDamping=.02,
                   physicsClientId=cid)
            bodies.append(body)
        for step in range(1,STEPS+1):
            bullet.stepSimulation(physicsClientId=cid)
            if step in SAMPLES:
                samples[step]=collect(bodies,cid)
        connected,contacts,floor_contacts=contact_sizes(
                   bullet.getContactPoints(physicsClientId=cid),bodies,floor)
    finally:
        bullet.disconnect(physicsClientId=cid)
    candidate=owner.copy(deep=True)
    for name,arr in samples[STEPS].items():
        candidate[name].values[:]=arr
    candidate.attrs["time_s"]=STEPS*DT
    check(candidate,seed,friction,gravity)
    for name in samples[STEPS]:
        np.copyto(owner[name].values,candidate[name].values)
    owner.attrs["time_s"]=STEPS*DT
    check(owner,seed,friction,gravity)
    if state_sha(owner)!=state_sha(candidate):
        raise ValueError("Published state differs from validated candidate")
    final=samples[STEPS]
    pos=final["position_m"]
    motion=np.linalg.norm(pos-samples[1200]["position_m"],axis=1)
    speed=np.linalg.norm(final["velocity_mps"],axis=1)
    return {
        "owner":owner,"samples":samples,"seed":seed,"friction":bool(friction),
        "gravity":bool(gravity),"initial_sha":original_sha,
        "final_sha":state_sha(owner),
        "mass_kg":check(owner,seed,friction,gravity),
        "max_top_height_m":float(np.max(pos[:,2]+R)),
        "grains_above_first_layer":int(np.count_nonzero(pos[:,2]>.26)),
        "mean_descent_m":float(np.mean(start[:,2]-pos[:,2])),
        "radial_p90_m":float(np.quantile(np.linalg.norm(pos[:,:2],axis=1),.9)),
        "median_late_displacement_m":float(np.median(motion)),
        "p90_speed_m_s":float(np.quantile(speed,.9)),
        "largest_force_contact_component":int(connected),
        "grain_positive_contact_count":int(contacts),
        "floor_positive_contact_count":int(floor_contacts),
        "max_initial_final_position_change_m":float(np.max(np.abs(pos-start))),
    }

def bad_states(owner):
    digest=state_sha(owner)
    seed=int(owner.attrs["seed"])
    friction=bool(owner.attrs["friction"])
    gravity=bool(owner.attrs["gravity"])
    rejected={}
    def reject(key,patch):
        other=owner.copy(deep=True)
        patch(other)
        try:check(other,seed,friction,gravity)
        except ValueError:rejected[key]=True
        else:raise AssertionError("Invalid owner accepted "+key)
        assert state_sha(owner)==digest
    reject("mass_plus1",lambda d:d["material_mass_kg"].values.__setitem__(0,M+1))
    reject("negative_mass",lambda d:d["material_mass_kg"].values.__setitem__(1,-1.))
    reject("wrong_units",lambda d:d["position_m"].attrs.__setitem__("units","cm"))
    reject("radius_altered",lambda d:d["radius_m"].values.__setitem__(0,.2))
    reject("invalid_grain_id",lambda d:d.coords.__setitem__("grain",np.arange(N)+1))
    reject("overlap_two_grains",lambda d:d["position_m"].values.__setitem__((1,slice(None)),d["position_m"].values[0].copy()))
    reject("invalid_quaternion",lambda d:d["orientation_xyzw"].values.__setitem__((0,3),2.))
    reject("extra_mass_stock",lambda d:d.__setitem__("mass_duplicate",xr.DataArray(np.ones(N),dims=("grain",))))
    return rejected

def main():
    a=execute(SEED1,True,True)
    b=execute(SEED2,True,True)
    free=execute(SEED1,False,True)
    nog=execute(SEED1,True,False)
    replay=execute(SEED1,True,True)
    fail=[]
    def gate(key,passed):
        if not passed:fail.append(key)
    gate("invariants",all(q["mass_kg"]==N*M for q in (a,b,free,nog,replay)))
    gate("3d_heap_both_seeds",all(q["max_top_height_m"]>.36 and
         q["grains_above_first_layer"]>=30 and q["mean_descent_m"]>.15 for q in (a,b)))
    gate("contact_support_both_seeds",all(q["grain_positive_contact_count"]>0 and
         q["floor_positive_contact_count"]>0 and
         q["largest_force_contact_component"]>=45 for q in (a,b)))
    gate("friction_contact_graph",a["largest_force_contact_component"]>=
         free["largest_force_contact_component"]+10)
    gate("friction_causes_height",a["max_top_height_m"]>=free["max_top_height_m"]+.08)
    gate("friction_restricts_spread",a["radial_p90_m"]<=free["radial_p90_m"]-.06)
    gate("late_settling_both_seeds",all(q["median_late_displacement_m"]<.025 and
         q["p90_speed_m_s"]<.08 for q in (a,b)))
    gate("zero_gravity_immobile",nog["max_initial_final_position_change_m"]<1e-8 and
         nog["p90_speed_m_s"]<1e-8)
    gate("different_seed_geometry",np.max(np.abs(a["owner"]["position_m"].values-
                                   b["owner"]["position_m"].values))>.01)
    gate("exact_replay",all(np.array_equal(
        a["owner"][k].values,replay["owner"][k].values)
        for k in ("position_m","velocity_mps","angular_velocity_rad_s","orientation_xyzw"))
        and all(all(np.array_equal(a["samples"][step][k],replay["samples"][step][k])
        for k in a["samples"][step]) for step in SAMPLES))
    rejected=bad_states(a["owner"])
    with tempfile.TemporaryDirectory(prefix="world_h24_") as td:
        p=pathlib.Path(td)/"granular_owner.nc"
        a["owner"].to_netcdf(p,engine="scipy")
        with xr.open_dataset(p,engine="scipy") as fd:loaded=fd.load()
        check(loaded,SEED1,True,True)
        gate("owner_checkpoint_exact",state_sha(loaded)==a["final_sha"])
        size=p.stat().st_size
    def info(q):
        return {k:v for k,v in q.items() if k not in ("owner","samples")}
    report={
        "experiment":"E3 H24 unconfined friction-dependent 3D granular pile",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "grains":N,"grain_radius_m":R,"grain_mass_kg":M,
        "physical_steps":STEPS,"dt_s":DT,
        "active_seed1":info(a),"active_seed2":info(b),
        "zero_friction":info(free),"zero_gravity":info(nog),
        "rejected_bad_states":rejected,"replay_exact":True,
        "checkpoint_bytes":size,"preregistered_gates_failed":fail,
        "limitations":"Abstract uniform rigid spheres, no material cohesive strength, no 3D voxel soil, no calibrated geotechnics, no thermal/mechanical energy conversion. Initial feed is regular jittered lattice and floor is an external boundary."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if fail:raise AssertionError("H24 gates failed: "+", ".join(fail))

if __name__=="__main__":
    main()
