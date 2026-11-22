"""Etapa2 H17: Bullet rigid contact updates a single xarray kinematic owner.

Preregistered H17 protocol exists before this file.
Physics is Bullet/PyBullet 3.2.7, not reimplemented here.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import tempfile

import numpy as np
import pybullet as p
import xarray as xr

DT=1./240.
STEPS=720
SAMPLE_EVERY=60
MATERIALS=("A","B")
XYZ=("x","y","z")
MASS=np.array([2.,8.],dtype=np.float64)
EXTENTS=np.full((2,3),.5,dtype=np.float64)
FLAGS=np.array([0,1],dtype=np.int32)
G=-9.81
START_A=np.array([0.,0.,2.],dtype=np.float64)
ZERO3=np.zeros(3,dtype=np.float64)


def normal(v):
    if isinstance(v,np.generic):
        return v.item()
    return v


def sha(ds):
    digest=hashlib.sha256()
    for name in ("material_mass_kg","position_m","velocity_mps","half_extent_m","fixed_flag"):
        x=ds[name]
        digest.update(name.encode())
        digest.update(x.values.tobytes())
        digest.update(str(x.attrs.get("units")).encode())
    digest.update(json.dumps({
        "body":[str(x) for x in ds.coords["body"].values.tolist()],
        "coord":[str(x) for x in ds.coords["coord"].values.tolist()],
        "attrs":{k:normal(v) for k,v in ds.attrs.items()}
    },sort_keys=True).encode())
    return digest.hexdigest()


def obstacle_xyz(placement):
    if placement=="free":
        return np.array([2.5,0.,.5],dtype=np.float64)
    if placement=="blocked":
        return np.array([0.,0.,.5],dtype=np.float64)
    raise ValueError("Not a preregistered obstacle arrangement")


def initial_owner(placement):
    coords=np.stack([START_A,obstacle_xyz(placement)])
    ds=xr.Dataset({
        "material_mass_kg":(("body",),MASS.copy(),{"units":"kg","role":"sole material inventory"}),
        "position_m":(("body","coord"),coords,{"units":"m","role":"authoritative kinematics"}),
        "velocity_mps":(("body","coord"),np.zeros((2,3),dtype=np.float64),
                      {"units":"m/s","role":"authoritative kinematics"}),
        "half_extent_m":(("body","coord"),EXTENTS.copy(),{"units":"m","role":"geometry only"}),
        "fixed_flag":(("body",),FLAGS.copy(),{"units":"1","role":"constraint flag"}),
    },coords={"body":np.array(MATERIALS,dtype="U1"),"coord":np.array(XYZ,dtype="U1")},
      attrs={"schema_version":1,"placement":placement,"time_s":0.,
             "ground_boundary_z_m":0.,"external_mass_kg":0.,"gravity_reference_m_s2":G})
    validate(ds,placement)
    return ds


def validate(ds,placement):
    expected={"material_mass_kg","position_m","velocity_mps","half_extent_m","fixed_flag"}
    if set(ds.data_vars)!=expected:
        raise ValueError("Unexpected material or kinematic stock")
    if [str(v) for v in ds.coords["body"].values.tolist()]!=list(MATERIALS) or [str(v) for v in ds.coords["coord"].values.tolist()]!=list(XYZ):
        raise ValueError("Body identity or axis names changed")
    if ds["material_mass_kg"].dims!=("body",) or any(ds[k].dims!=("body","coord") for k in ["position_m","velocity_mps","half_extent_m"]):
        raise ValueError("Wrong kinematic topology")
    if ds["fixed_flag"].dims!=("body",):
        raise ValueError("Wrong constraint shape")
    for field,unit in (("material_mass_kg","kg"),("position_m","m"),("velocity_mps","m/s"),("half_extent_m","m"),("fixed_flag","1")):
        if ds[field].attrs.get("units")!=unit:
            raise ValueError("Wrong physical unit: "+field)
    if ds.attrs.get("schema_version")!=1 or ds.attrs.get("placement")!=placement or ds.attrs.get("external_mass_kg")!=0. or ds.attrs.get("ground_boundary_z_m")!=0. or ds.attrs.get("gravity_reference_m_s2")!=G:
        raise ValueError("Unexpected scene identity / mass ledger")
    if ds.attrs.get("time_s") not in (0.,STEPS*DT):
        raise ValueError("Unexpected physical time in owner")
    m=ds["material_mass_kg"].values
    x=ds["position_m"].values
    v=ds["velocity_mps"].values
    half=ds["half_extent_m"].values
    fix=ds["fixed_flag"].values
    if not (np.isfinite(m).all() and np.isfinite(x).all() and np.isfinite(v).all() and np.isfinite(half).all()):
        raise ValueError("NaN or infinite physical state")
    if not np.array_equal(m,MASS) or float(m.sum())!=10.:
        raise ValueError("Mass source/sink or negative mass")
    if not np.array_equal(half,EXTENTS) or not np.array_equal(fix,FLAGS):
        raise ValueError("Material volume or fixed constraint modified")
    if not np.array_equal(x[1],obstacle_xyz(placement)) or not np.array_equal(v[1],ZERO3):
        raise ValueError("Static material B moved")
    sep=np.abs(x[0]-x[1])
    overlap=np.maximum(0.,half[0]+half[1]-sep)
    if np.all(overlap>.02):
        raise ValueError("Material volumes interpenetrate")
    if np.max(np.abs(x[0,:2]))>.15:
        raise ValueError("Mobile A left initial vertical corridor")
    if x[0,2]-.5<-.02:
        raise ValueError("Mobile body penetrated ground excessively")
    if np.max(np.abs(x[0]))>10. or np.max(np.abs(v[0]))>50.:
        raise ValueError("Unbounded mobile body state")
    return {"mass_kg":float(m.sum()),"volume_m3":float(np.prod(2*half[0])+np.prod(2*half[1]))}


def solve(placement,gravity):
    initial=initial_owner(placement)
    old_sha=sha(initial)
    cid=p.connect(p.DIRECT)
    samples=[]
    max_ground_force=0.
    max_block_force=0.
    pos_B=initial["position_m"].values[1].copy()
    try:
        p.setPhysicsEngineParameter(deterministicOverlappingPairs=1,physicsClientId=cid)
        p.setTimeStep(DT,physicsClientId=cid)
        p.setGravity(0.,0.,gravity,physicsClientId=cid)
        floor_geom=p.createCollisionShape(p.GEOM_PLANE,planeNormal=[0.,0.,1.],physicsClientId=cid)
        floor=p.createMultiBody(baseMass=0,baseCollisionShapeIndex=floor_geom,basePosition=[0,0,0],physicsClientId=cid)
        boxshape=p.createCollisionShape(p.GEOM_BOX,halfExtents=[.5,.5,.5],physicsClientId=cid)
        mobile=p.createMultiBody(baseMass=float(initial["material_mass_kg"].values[0]),
                  baseCollisionShapeIndex=boxshape,basePosition=START_A.tolist(),physicsClientId=cid)
        fixed=p.createMultiBody(baseMass=0,baseCollisionShapeIndex=boxshape,basePosition=pos_B.tolist(),physicsClientId=cid)
        for body in (floor,mobile,fixed):
            p.changeDynamics(body,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
        for step in range(1,STEPS+1):
            p.stepSimulation(physicsClientId=cid)
            for cont in p.getContactPoints(bodyA=mobile,bodyB=floor,physicsClientId=cid):
                max_ground_force=max(max_ground_force,float(cont[9]))
            for cont in p.getContactPoints(bodyA=mobile,bodyB=fixed,physicsClientId=cid):
                max_block_force=max(max_block_force,float(cont[9]))
            if step%SAMPLE_EVERY==0:
                xyz,ori=p.getBasePositionAndOrientation(mobile,physicsClientId=cid)
                linear,angular=p.getBaseVelocity(mobile,physicsClientId=cid)
                if not np.allclose(np.asarray(ori),[0.,0.,0.,1.],rtol=0.,atol=.01):
                    raise ValueError("Body rotated but orientation is not in minimal owner")
                samples.append({
                    "step":step,
                    "position_m":list(xyz),"velocity_mps":list(linear),
                    "angular_velocity_rad_s":list(angular),
                })
        Bfinal,ori_B=p.getBasePositionAndOrientation(fixed,physicsClientId=cid)
        if not np.array_equal(np.asarray(Bfinal),pos_B):
            raise AssertionError("Fixed collider B moved")
    finally:
        p.disconnect(physicsClientId=cid)

    # The Bullet state is transient; never a second canonical stock.
    candidate=initial.copy(deep=True)
    candidate["position_m"].values[0]=np.asarray(samples[-1]["position_m"])
    candidate["velocity_mps"].values[0]=np.asarray(samples[-1]["velocity_mps"])
    candidate.attrs["time_s"]=STEPS*DT
    validate(candidate,placement)
    # Single-writer commit into existing owner arrays (no stale separate copy).
    np.copyto(initial["position_m"].values,candidate["position_m"].values)
    np.copyto(initial["velocity_mps"].values,candidate["velocity_mps"].values)
    initial.attrs["time_s"]=STEPS*DT
    validate(initial,placement)
    if sha(initial)!=sha(candidate):
        raise AssertionError("Kinematic commit not identical to validated candidate")
    return {
        "owner":initial,"samples":samples,
        "placement":placement,"gravity_m_s2":gravity,
        "initial_center_z_m":float(START_A[2]),
        "final_center_z_m":float(initial["position_m"].values[0,2]),
        "net_descent_m":float(START_A[2]-initial["position_m"].values[0,2]),
        "final_speed_m_s":float(np.linalg.norm(initial["velocity_mps"].values[0])),
        "max_ground_contact_force_N":max_ground_force,
        "max_block_contact_force_N":max_block_force,
        "material_mass_kg":float(initial["material_mass_kg"].sum()),
        "volume_m3":float(validate(initial,placement)["volume_m3"]),
        "initial_owner_sha256":old_sha,
        "final_owner_sha256":sha(initial)
    }


def reject_changes(owner):
    placement=owner.attrs["placement"]
    digest=sha(owner)
    flags={}
    def reject(name,patch):
        b=owner.copy(deep=True)
        patch(b)
        try:
            validate(b,placement)
        except ValueError:
            flags[name]=True
        else:
            raise AssertionError("Invalid physical state accepted: "+name)
        if sha(owner)!=digest:
            raise AssertionError("Good owner altered on rejecting candidate")
    reject("mass_plus_one",lambda d:d["material_mass_kg"].values.__setitem__(0,3.))
    reject("mass_negative",lambda d:d["material_mass_kg"].values.__setitem__(1,-8.))
    reject("wrong_length_units",lambda d:d["position_m"].attrs.__setitem__("units","cm"))
    reject("changed_identity",lambda d:d.coords.__setitem__("body",np.array(["C","B"])))
    reject("static_block_displaced",lambda d:d["position_m"].values.__setitem__((1,0),5.))
    reject("overlapped_solids",lambda d:d["position_m"].values.__setitem__((0,slice(None)),d["position_m"].values[1].copy()))
    reject("wrong_velocity_units",lambda d:d["velocity_mps"].attrs.__setitem__("units","km/h"))
    reject("fixed_flag_swapped",lambda d:d["fixed_flag"].values.__setitem__(0,1))
    reject("extra_velocity_stock",lambda d:d.__setitem__("velocity_copy",xr.DataArray(np.zeros((2,3)),dims=("body","coord"))))
    return flags


def main():
    free=solve("free",G)
    blocked=solve("blocked",G)
    g0=solve("free",0.)
    replay=solve("free",G)
    errors=[]
    def check(name,condition):
        if not condition: errors.append(name)
    check("free_fall_observed",free["net_descent_m"]>1.2 and .45<free["final_center_z_m"]<.6)
    check("blocked_support_observed",.3<blocked["net_descent_m"]<.7 and 1.45<blocked["final_center_z_m"]<1.6)
    check("free_falls_more",free["net_descent_m"]-blocked["net_descent_m"]>.8)
    check("ground_contact_positive",free["max_ground_contact_force_N"]>0.)
    check("obstacle_contact_positive",blocked["max_block_contact_force_N"]>0.)
    check("g0_unchanged_position",abs(g0["final_center_z_m"]-START_A[2])<1e-8 and
          np.max(np.abs(g0["owner"]["position_m"].values[0]-START_A))<1e-8)
    check("g0_zero_velocity_force",g0["final_speed_m_s"]<1e-8 and
          g0["max_ground_contact_force_N"]==0. and g0["max_block_contact_force_N"]==0.)
    check("all_mass_kept",all(v["material_mass_kg"]==10. and v["volume_m3"]==2. for v in (free,blocked,g0,replay)))
    check("bit_identical_replay",np.array_equal(free["owner"]["position_m"].values,replay["owner"]["position_m"].values)
          and np.array_equal(free["owner"]["velocity_mps"].values,replay["owner"]["velocity_mps"].values)
          and free["samples"]==replay["samples"])
    rejected=reject_changes(free["owner"])
    rejected.update({f"blocked_{k}":v for k,v in reject_changes(blocked["owner"]).items()})
    with tempfile.TemporaryDirectory(prefix="world_h17_") as td:
        f=pathlib.Path(td)/"kinematic_owner.nc"
        free["owner"].to_netcdf(f,engine="scipy")
        with xr.open_dataset(f,engine="scipy") as inp:
            loaded=inp.load()
        validate(loaded,"free")
        check("checkpoint_exact",sha(loaded)==sha(free["owner"])
              and np.array_equal(loaded["position_m"].values,free["owner"]["position_m"].values)
              and np.array_equal(loaded["velocity_mps"].values,free["owner"]["velocity_mps"].values))
        snapshot_bytes=f.stat().st_size
    def public(d):
        return {k:v for k,v in d.items() if k not in ("owner","samples")}
    report={
        "experiment":"E2 H17 stateful rigid gravity with free vs blocked volume",
        "python":platform.python_version(),"pybullet":p.__version__ if hasattr(p,"__version__") else "3.2.7 pinned CI",
        "numpy":np.__version__,"xarray":xr.__version__,
        "physical_step_s":DT,"nsteps":STEPS,"sample_every":SAMPLE_EVERY,
        "free":public(free),"blocked":public(blocked),"no_gravity":public(g0),
        "exact_replay":True,"negative_cases_rejected":rejected,
        "netcdf_bytes":snapshot_bytes,
        "preregistered_gates_failed":errors,
        "limitations":"Prescribed ground and fixed obstacle, ideal rigid cubes no orientation changes, no thermomechanical energy ledger or geometric emergence; checkpoint contains kinematic owner, not Bullet contact solver internals."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if errors:
        raise AssertionError("H17 physical gates failed: "+", ".join(errors))


if __name__=="__main__":
    main()
