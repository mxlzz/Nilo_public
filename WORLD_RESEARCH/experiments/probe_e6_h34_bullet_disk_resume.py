"""E6/H34: native PyBullet saveBullet/restoreState across two CI runners.

Native Bullet equations only. Disk .bullet is a transient solver cache;
canonical xarray NetCDF stores actual material mass and current kinematics.
Preregistered in ETAPA_6_H34_PROTOCOLO_CHECKPOINT_BULLET.md.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import sys
from importlib.metadata import version

import numpy as np
import pybullet as p
import xarray as xr

DT=1./240.
MID=360
TOTAL=720
MASS=np.array([2.,8.],dtype=np.float64)
EXT=np.full((2,3),.5,dtype=np.float64)
FIXED=np.array([0,1],dtype=np.int32)
A0=np.array([0.,0.,2.])
B0=np.array([0.,0.,.5])
FIELDS=("material_mass_kg","half_extent_m","fixed_flag","position_m",
        "velocity_mps","angular_velocity_rad_s","orientation_xyzw")
STOCKS={
    "material_mass_kg":"kg",
    "half_extent_m":"m",
    "fixed_flag":"1",
    "position_m":"m",
    "velocity_mps":"m/s",
    "angular_velocity_rad_s":"rad/s",
    "orientation_xyzw":"1",
}

def owner_from_native(cid,a,b,step):
    seq=[]
    for body in (a,b):
        pos,orn=p.getBasePositionAndOrientation(body,physicsClientId=cid)
        linear,angular=p.getBaseVelocity(body,physicsClientId=cid)
        seq.append((pos,orn,linear,angular))
    owner=xr.Dataset({
        "material_mass_kg":(("body",),MASS.copy(),{"units":"kg"}),
        "half_extent_m":(("body","xyz"),EXT.copy(),{"units":"m"}),
        "fixed_flag":(("body",),FIXED.copy(),{"units":"1"}),
        "position_m":(("body","xyz"),np.asarray([s[0] for s in seq],dtype=np.float64),{"units":"m"}),
        "velocity_mps":(("body","xyz"),np.asarray([s[2] for s in seq],dtype=np.float64),{"units":"m/s"}),
        "angular_velocity_rad_s":(("body","xyz"),np.asarray([s[3] for s in seq],dtype=np.float64),{"units":"rad/s"}),
        "orientation_xyzw":(("body","quat"),np.asarray([s[1] for s in seq],dtype=np.float64),{"units":"1"}),
    },coords={"body":["A","B"],"xyz":["x","y","z"],"quat":["x","y","z","w"]},
       attrs={"schema_version":1,"step":step,"time_s":step*DT,
              "gravity_z_m_s2":-9.81,"ground_z_m":0.,
              "scene":"blocked H17 cubes; B fixed by Bullet constraint"})
    validate(owner,step)
    return owner

def validate(ds,step):
    if set(ds.data_vars)!=set(FIELDS):
        raise ValueError("Extra/missing inventory or kinematic field")
    if ds.coords["body"].values.tolist()!=["A","B"] or ds.coords["xyz"].values.tolist()!=["x","y","z"] or ds.coords["quat"].values.tolist()!=["x","y","z","w"]:
        raise ValueError("Body or coordinate IDs invalid")
    dims={"material_mass_kg":("body",),"fixed_flag":("body",),
          "half_extent_m":("body","xyz"),
          "position_m":("body","xyz"),
          "velocity_mps":("body","xyz"),
          "angular_velocity_rad_s":("body","xyz"),
          "orientation_xyzw":("body","quat")}
    if any(ds[k].dims!=v or ds[k].attrs.get("units")!=STOCKS[k] for k,v in dims.items()):
        raise ValueError("Invalid dimensions/units")
    base={"schema_version":1,"step":step,"time_s":step*DT,
          "gravity_z_m_s2":-9.81,"ground_z_m":0.,
          "scene":"blocked H17 cubes; B fixed by Bullet constraint"}
    if set(ds.attrs)!=set(base) or any(ds.attrs.get(k)!=v for k,v in base.items()):
        raise ValueError("Checkpoint time or scenario corrupted")
    if not np.array_equal(ds["material_mass_kg"].values,MASS) or float(ds["material_mass_kg"].sum())!=10.:
        raise ValueError("Wrong closed mass")
    if not np.array_equal(ds["fixed_flag"].values,FIXED) or not np.array_equal(ds["half_extent_m"].values,EXT):
        raise ValueError("Changed rigid material geometry")
    for k in ("position_m","velocity_mps","angular_velocity_rad_s","orientation_xyzw"):
        if not np.isfinite(ds[k].values).all():
            raise ValueError("Nonfinite position/velocity/orientation")
    if not np.allclose(ds["position_m"].values[1],B0,rtol=0,atol=1e-12):
        raise ValueError("Fixed body displaced")
    if np.max(np.abs(ds["velocity_mps"].values[1]))>1e-12 or np.max(np.abs(ds["angular_velocity_rad_s"].values[1]))>1e-12:
        raise ValueError("Fixed body moving")
    q=ds["orientation_xyzw"].values
    if np.max(np.abs(np.linalg.norm(q,axis=1)-1.))>1e-4:
        raise ValueError("Quaternion invalid")
    xyz=ds["position_m"].values
    sep=np.abs(xyz[0]-xyz[1])
    if np.all(np.maximum(0.,EXT[0]+EXT[1]-sep)>.02):
        raise ValueError("Body interpenetration")
    if xyz[0,2]-.5<-.02:
        raise ValueError("Mobile body penetrated ground")
    return 10.

def sha_owner(ds):
    h=hashlib.sha256()
    for k in FIELDS:
        a=ds[k]
        h.update(k.encode()+a.values.tobytes()+a.attrs["units"].encode())
    attrs={k:(v.item() if isinstance(v,np.generic) else v)
           for k,v in ds.attrs.items()}
    h.update(json.dumps(attrs,sort_keys=True).encode())
    for k in ("body","xyz","quat"):
        h.update(repr(ds.coords[k].values.tolist()).encode())
    return h.hexdigest()

def setup():
    cid=p.connect(p.DIRECT)
    if cid<0:raise RuntimeError("PyBullet DIRECT failed")
    p.setPhysicsEngineParameter(deterministicOverlappingPairs=1,physicsClientId=cid)
    p.setTimeStep(DT,physicsClientId=cid)
    p.setGravity(0.,0.,-9.81,physicsClientId=cid)
    floorshape=p.createCollisionShape(p.GEOM_PLANE,planeNormal=[0,0,1],physicsClientId=cid)
    floor=p.createMultiBody(baseMass=0,baseCollisionShapeIndex=floorshape,
                            basePosition=[0,0,0],physicsClientId=cid)
    shape=p.createCollisionShape(p.GEOM_BOX,halfExtents=[.5,.5,.5],physicsClientId=cid)
    a=p.createMultiBody(baseMass=2.,baseCollisionShapeIndex=shape,
                        basePosition=A0.tolist(),physicsClientId=cid)
    b=p.createMultiBody(baseMass=0,baseCollisionShapeIndex=shape,
                        basePosition=B0.tolist(),physicsClientId=cid)
    for body in (floor,a,b):
        p.changeDynamics(body,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
    return cid,a,b,floor

def contact_summary(cid,a,b):
    points=p.getContactPoints(bodyA=a,bodyB=b,physicsClientId=cid)
    forces=[float(c[9]) for c in points]
    return {"positive_count":int(sum(v>1e-5 for v in forces)),
            "peak_force_N":float(max(forces) if forces else 0.)}

def one_run(path=None):
    cid,a,b,floor=setup()
    midpoint=None
    contact_mid=None
    try:
        for step in range(1,TOTAL+1):
            p.stepSimulation(physicsClientId=cid)
            if step==MID:
                midpoint=owner_from_native(cid,a,b,step)
                contact_mid=contact_summary(cid,a,b)
                if path is not None:
                    p.saveBullet(str(path),physicsClientId=cid)
        final=owner_from_native(cid,a,b,TOTAL)
        contact_end=contact_summary(cid,a,b)
    finally:
        p.disconnect(physicsClientId=cid)
    return {"checkpoint":midpoint,"final":final,"contact_mid":contact_mid,"contact_final":contact_end}

def corrupted_states(owner):
    initial=sha_owner(owner)
    flags={}
    def reject(name,patch):
        candidate=owner.copy(deep=True)
        patch(candidate)
        try:validate(candidate,MID)
        except ValueError:flags[name]=True
        else:raise AssertionError("Invalid owner passed: "+name)
        if sha_owner(owner)!=initial:
            raise AssertionError("Rejected candidate changed owner")
    reject("mass_created",lambda x:x["material_mass_kg"].values.__setitem__(0,3.))
    reject("negative_mass",lambda x:x["material_mass_kg"].values.__setitem__(0,-2.))
    reject("units_cm",lambda x:x["position_m"].attrs.__setitem__("units","cm"))
    reject("body_id_changed",lambda x:x.coords.__setitem__("body",["C","B"]))
    reject("fixed_B_moved",lambda x:x["position_m"].values.__setitem__((1,0),2.))
    reject("body_overlap",lambda x:x["position_m"].values.__setitem__((0,slice(None)),x["position_m"].values[1].copy()))
    reject("quaternion_invalid",lambda x:x["orientation_xyzw"].values.__setitem__((0,3),2.))
    reject("extra_mass_stock",lambda x:x.__setitem__("mass_copy",xr.DataArray(np.ones(2),dims=("body",))))
    reject("wrong_time",lambda x:x.attrs.__setitem__("step",999))
    return flags

def write_netcdf(owner,path,step):
    validate(owner,step)
    owner.to_netcdf(path,engine="scipy")
    with xr.open_dataset(path,engine="scipy") as f: loaded=f.load()
    validate(loaded,step)
    if sha_owner(loaded)!=sha_owner(owner):
        raise ValueError("NetCDF owner hash mismatch")
    return path.stat().st_size

def producer(outdir):
    out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=True)
    ref=one_run(out/"native_state_at_360.bullet")
    repeated=one_run()
    if not all(np.array_equal(ref["final"][k].values,repeated["final"][k].values)
               for k in FIELDS):
        raise ValueError("Bullet uninterrupted replay failed")
    if (ref["contact_mid"]["positive_count"]<1 or
        ref["contact_final"]["positive_count"]<1):
        raise AssertionError("Rigid body never had positive support")
    initial=ref["checkpoint"]
    midbytes=write_netcdf(initial,out/"owner_step360.nc",MID)
    endbytes=write_netcdf(ref["final"],out/"owner_step720.nc",TOTAL)
    rejected=corrupted_states(initial)
    binary=out/"native_state_at_360.bullet"
    if not binary.exists() or binary.stat().st_size<100:
        raise ValueError("Bullet failed to save a meaningful solver snapshot")
    raw=binary.read_bytes()
    manifest={
        "experiment":"E6 H34 Bullet persistent solver cache + canonical owner",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "checkpoint_step":MID,"final_step":TOTAL,
        "native_binary_SHA256":hashlib.sha256(raw).hexdigest(),
        "native_binary_bytes":len(raw),
        "owner_mid_SHA256":sha_owner(initial),"owner_end_SHA256":sha_owner(ref["final"]),
        "owner_mid_netcdf_bytes":midbytes,
        "owner_end_netcdf_bytes":endbytes,
        "mid_contact":ref["contact_mid"],"end_contact":ref["contact_final"],
        "replay_exact":True,
        "rejected_invalid_candidates":rejected,
        "failed_preregistered_gates":[]
    }
    (out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("WORLD_EVAL_JSON "+json.dumps(manifest,sort_keys=True),flush=True)

def consumer(indir):
    folder=pathlib.Path(indir)
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    with xr.open_dataset(folder/"owner_step360.nc",engine="scipy") as f:owner_mid=f.load()
    with xr.open_dataset(folder/"owner_step720.nc",engine="scipy") as f:owner_final=f.load()
    validate(owner_mid,MID)
    validate(owner_final,TOTAL)
    binary=(folder/"native_state_at_360.bullet").read_bytes()
    failed=[]
    def gate(name,ok):
        if not ok:failed.append(name)
    gate("input_mid_owner_hash",sha_owner(owner_mid)==manifest["owner_mid_SHA256"])
    gate("input_final_owner_hash",sha_owner(owner_final)==manifest["owner_end_SHA256"])
    gate("native_solver_cache_integrity",len(binary)==manifest["native_binary_bytes"]
         and hashlib.sha256(binary).hexdigest()==manifest["native_binary_SHA256"])
    cid,a,b,floor=setup()
    try:
        try:
            p.restoreState(fileName=str(folder/"native_state_at_360.bullet"),
                           physicsClientId=cid)
        except Exception as err:
            print("WORLD_EVAL_JSON "+json.dumps({
                "experiment":"E6 H34", "failed_preregistered_gates":["native_restore_exception"],
                "error_type":type(err).__name__,"error":str(err)
            }),flush=True)
            raise
        restored=owner_from_native(cid,a,b,MID)
        match_mid=all(np.array_equal(restored[k].values,owner_mid[k].values) for k in FIELDS)
        gate("bit_exact_mid_restore",match_mid and sha_owner(restored)==sha_owner(owner_mid))
        for step in range(MID+1,TOTAL+1):
            p.stepSimulation(physicsClientId=cid)
        resumed=owner_from_native(cid,a,b,TOTAL)
        native_contacts=contact_summary(cid,a,b)
    finally:
        p.disconnect(physicsClientId=cid)
    same_final=all(np.array_equal(resumed[k].values,owner_final[k].values)
                   for k in FIELDS)
    gate("bit_exact_final_resume",same_final and sha_owner(resumed)==sha_owner(owner_final))
    gate("support_restored",native_contacts["positive_count"]>0
         and owner_mid["position_m"].values[0,2]>1.45
         and owner_final["position_m"].values[0,2]>1.45)
    gate("contact_force_same",native_contacts==manifest["end_contact"])
    gate("only_remaining_steps",manifest["checkpoint_step"]==360
         and manifest["final_step"]==720)
    result={
        "experiment":"E6 H34 cross-process native saveBullet/restoreState",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "native_binary_bytes":len(binary),
        "mid_checkpoint_kinematics_bit_identical":match_mid,
        "final_kinematics_bit_identical":same_final,
        "checkpoint_sha256":manifest["owner_mid_SHA256"],
        "final_expected_sha256":manifest["owner_end_SHA256"],
        "final_restored_sha256":sha_owner(resumed),
        "support_contact":native_contacts,
        "mid_and_final_native_contact_producer":[manifest["mid_contact"],manifest["end_contact"]],
        "preregistered_gates_failed":failed,
        "limitations":"Two rigid boxes, external fixed plane, same PyBullet version and collision construction. .bullet is solver cache, not independent canonical owner. No source reservoir, soil, feedback or cross-version restart."
    }
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True),flush=True)
    if failed:
        raise AssertionError("H34 preregistered restart gates failed: "+", ".join(failed))

if __name__=="__main__":
    if len(sys.argv)!=3 or sys.argv[1] not in ("producer","consumer"):
        raise SystemExit("Usage: producer|consumer output_dir")
    globals()[sys.argv[1]](sys.argv[2])
