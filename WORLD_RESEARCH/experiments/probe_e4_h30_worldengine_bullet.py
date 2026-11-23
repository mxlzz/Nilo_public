"""E4/H30: generated triangular terrain patch supports native PyBullet contact.

The same H29 WorldEngine source is used; heights are only nominal meters.
No gravity/contact law is implemented locally. The geologic patch is a
static boundary, not a world engine or proof of coupled sediment dynamics.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import platform
import tempfile
import sys
from importlib.metadata import version

import numpy as np
import pybullet as p
import xarray as xr

SEEDS=(7321,8128)
UPSTREAM_SHA="3b9113ecfad884cab4b32081d138a15e6262ada8"
SOURCE_HASH={
    7321:"495e97c24477e68e0cffcab8f485481630d4425d31a01442c7ad1cbb0daa170d",
    8128:"d03e423f93b3c26ac097fba54e303c6322131f0b7fec0afb21d15e4c52e40781"
}
DX=100.
SPHERE_R=.5
SPHERE_M=2.
DT=1./240.
STEPS=720
X_TRIAL=40.
Y_TRIAL=30.
MIN_PATCH_HEIGHT_RANGE=.05

def digest_raw(a):
    return hashlib.sha256(np.ascontiguousarray(a,dtype="<f8").tobytes()).hexdigest()

def z_nominal(raw):
    return 50.*(raw-float(raw.min()))/(float(raw.max())-float(raw.min()))

def choose_patch(raw):
    z=z_nominal(raw)
    candidates=[]
    for iy in range(z.shape[0]-1):
        for ix in range(z.shape[1]-1):
            block=z[iy:iy+2,ix:ix+2]
            spread=float(np.ptp(block))
            if spread>=MIN_PATCH_HEIGHT_RANGE:
                candidates.append((spread,iy,ix))
    if not candidates:
        raise ValueError("No nonflat generated patch above preregistered threshold")
    spread,iy,ix=min(candidates)
    patch=np.asarray(z[iy:iy+2,ix:ix+2],dtype=np.float64).copy()
    return patch,(iy,ix),spread

def surface_at_probe(patch):
    return .6*patch[0,0]+.1*patch[0,1]+.3*patch[1,1]

def scene_owner(patch,source_seed,source_sha,index,has_mesh=True,gravity=True):
    nominal=surface_at_probe(patch)
    ds=xr.Dataset({
        "material_mass_kg":(("body",),np.array([SPHERE_M],dtype=np.float64),{"units":"kg"}),
        "position_m":(("body","axis"),np.array([[X_TRIAL,Y_TRIAL,nominal+3.]],dtype=np.float64),{"units":"m_nominal"}),
        "velocity_mps":(("body","axis"),np.zeros((1,3),dtype=np.float64),{"units":"m_nominal/s"}),
        "terrain_height_m_nominal":(("v","u"),patch.copy(),{"units":"m_nominal","role":"static geologic sample only"}),
    },coords={"body":np.array([0],dtype=np.int32),"axis":["x","y","z"],
              "v":np.array([0,1],dtype=np.int32),"u":np.array([0,1],dtype=np.int32)},
    attrs={
        "schema_version":1,"source":"WorldEngine",
        "source_seed":int(source_seed),"source_sha256":str(source_sha),
        "source_revision":UPSTREAM_SHA,"patch_row":int(index[0]),"patch_col":int(index[1]),
        "source_height_units":"arbitrary","terrain_height_units":"m_nominal",
        "horizontal_dx_m_nominal":DX,"body_radius_m_nominal":SPHERE_R,
        "body_mass_kg":SPHERE_M,
        "has_mesh":int(bool(has_mesh)),"gravity":int(bool(gravity)),
        "time_s":0.,"physical_geometry":"static 2-triangle WorldEngine core patch",
    })
    validate(ds,patch,source_seed,source_sha,index,has_mesh,gravity)
    return ds

def validate(ds,patch,source_seed,source_sha,index,has_mesh,gravity):
    if set(ds.data_vars)!={"material_mass_kg","position_m","velocity_mps","terrain_height_m_nominal"}:
        raise ValueError("Extra or missing material/terrain field")
    if (ds["material_mass_kg"].dims!=("body",)
        or ds["position_m"].dims!=("body","axis")
        or ds["velocity_mps"].dims!=("body","axis")
        or ds["terrain_height_m_nominal"].dims!=("v","u")):
        raise ValueError("Unexpected topology")
    if (ds.coords["body"].values.tolist()!=[0]
        or ds.coords["axis"].values.tolist()!=["x","y","z"]
        or ds.coords["v"].values.tolist()!=[0,1]
        or ds.coords["u"].values.tolist()!=[0,1]):
        raise ValueError("Identity or axes changed")
    for name,units in (("material_mass_kg","kg"),("position_m","m_nominal"),
                      ("velocity_mps","m_nominal/s"),("terrain_height_m_nominal","m_nominal")):
        if ds[name].attrs.get("units")!=units:
            raise ValueError("Invalid unit "+name)
    expected={
        "schema_version":1,"source":"WorldEngine","source_seed":int(source_seed),
        "source_sha256":source_sha,"source_revision":UPSTREAM_SHA,
        "patch_row":int(index[0]),"patch_col":int(index[1]),
        "source_height_units":"arbitrary","terrain_height_units":"m_nominal",
        "horizontal_dx_m_nominal":DX,"body_radius_m_nominal":SPHERE_R,
        "body_mass_kg":SPHERE_M,"has_mesh":int(bool(has_mesh)),
        "gravity":int(bool(gravity)),
        "physical_geometry":"static 2-triangle WorldEngine core patch",
    }
    if any(ds.attrs.get(k)!=v for k,v in expected.items()):
        raise ValueError("Generated geometry source or physical contract changed")
    if set(ds.attrs)!=set(expected)|{"time_s"} or ds.attrs["time_s"] not in (0.,STEPS*DT):
        raise ValueError("Unexpected owner state time")
    if not np.array_equal(ds["terrain_height_m_nominal"].values,patch):
        raise ValueError("Static generated bedrock altered")
    m=ds["material_mass_kg"].values
    pos=ds["position_m"].values
    vel=ds["velocity_mps"].values
    if (not np.isfinite(m).all() or not np.isfinite(pos).all() or
        not np.isfinite(vel).all() or not np.array_equal(m,np.array([SPHERE_M]))):
        raise ValueError("Mass not conserved or pose nonfinite")
    return True

def owner_hash(ds):
    h=hashlib.sha256()
    for name in ("material_mass_kg","position_m","velocity_mps","terrain_height_m_nominal"):
        h.update(name.encode())
        h.update(ds[name].values.tobytes())
        h.update(ds[name].attrs["units"].encode())
    h.update(json.dumps({k:(v.item() if isinstance(v,np.generic) else v)
                         for k,v in ds.attrs.items()},sort_keys=True).encode())
    return h.hexdigest()

def mesh_vertices(patch):
    a,b,c,d=float(patch[0,0]),float(patch[0,1]),float(patch[1,1]),float(patch[1,0])
    return [[0.,0.,a],[DX,0.,b],[DX,DX,c],[0.,DX,d]]

def simulate(patch,source_seed,source_sha,index,gravity=True,has_mesh=True):
    owner=scene_owner(patch,source_seed,source_sha,index,has_mesh,gravity)
    p0=owner["position_m"].values[0].copy()
    z_expected=float(surface_at_probe(patch))
    cid=p.connect(p.DIRECT)
    positive=0
    worst_contact_distance=0.
    ray_height=None
    try:
        p.setPhysicsEngineParameter(
            fixedTimeStep=DT,numSolverIterations=60,physicsClientId=cid)
        p.setGravity(0.,0.,-9.81 if gravity else 0.,physicsClientId=cid)
        terrain=None
        if has_mesh:
            shape=p.createCollisionShape(p.GEOM_MESH,
                    vertices=mesh_vertices(patch),
                    indices=[0,1,2,0,2,3],
                    flags=p.GEOM_FORCE_CONCAVE_TRIMESH,
                    physicsClientId=cid)
            terrain=p.createMultiBody(baseMass=0.,baseCollisionShapeIndex=shape,
                                      physicsClientId=cid)
            p.changeDynamics(terrain,-1,lateralFriction=.8,
                             restitution=0.,physicsClientId=cid)
            ray=p.rayTest([X_TRIAL,Y_TRIAL,z_expected+10.],
                          [X_TRIAL,Y_TRIAL,z_expected-10.],physicsClientId=cid)[0]
            if ray[0]!=terrain:
                raise ValueError("Ray did not hit static generated terrain mesh")
            ray_height=float(ray[3][2])
        sphere_shape=p.createCollisionShape(p.GEOM_SPHERE,radius=SPHERE_R,physicsClientId=cid)
        body=p.createMultiBody(baseMass=SPHERE_M,
                               baseCollisionShapeIndex=sphere_shape,
                               basePosition=p0.tolist(),physicsClientId=cid)
        p.changeDynamics(body,-1,lateralFriction=.8,
                         restitution=0.,physicsClientId=cid)
        for _ in range(STEPS):
            p.stepSimulation(physicsClientId=cid)
            for contact in p.getContactPoints(physicsClientId=cid):
                if terrain is not None and set((contact[1],contact[2]))==set((body,terrain)):
                    if float(contact[9])>1e-5:
                        positive+=1
                    worst_contact_distance=min(worst_contact_distance,float(contact[8]))
        final_pos,_=p.getBasePositionAndOrientation(body,physicsClientId=cid)
        vel,_=p.getBaseVelocity(body,physicsClientId=cid)
    finally:
        p.disconnect(physicsClientId=cid)

    candidate=owner.copy(deep=True)
    candidate["position_m"].values[0]=np.asarray(final_pos,dtype=np.float64)
    candidate["velocity_mps"].values[0]=np.asarray(vel,dtype=np.float64)
    candidate.attrs["time_s"]=STEPS*DT
    validate(candidate,patch,source_seed,source_sha,index,has_mesh,gravity)
    owner["position_m"].values[:]=candidate["position_m"].values
    owner["velocity_mps"].values[:]=candidate["velocity_mps"].values
    owner.attrs["time_s"]=STEPS*DT
    validate(owner,patch,source_seed,source_sha,index,has_mesh,gravity)
    if owner_hash(owner)!=owner_hash(candidate):
        raise ValueError("Published result not equal validated candidate")
    xyz=owner["position_m"].values[0]
    return {
        "owner":owner,"seed":source_seed,"patch_index":list(index),
        "patch_heights_m_nominal":patch.tolist(),
        "patch_range_m_nominal":float(np.ptp(patch)),
        "source_sha256":source_sha,"gravity":bool(gravity),
        "has_mesh":bool(has_mesh),
        "expected_triangle_ray_height_m_nominal":z_expected,
        "ray_height_m_nominal":ray_height,
        "ray_vertical_error_m_nominal":abs(ray_height-z_expected) if ray_height is not None else None,
        "descent_m_nominal":float(p0[2]-xyz[2]),
        "final_position_m_nominal":xyz.tolist(),
        "final_speed_m_nominal_per_s":float(np.linalg.norm(owner["velocity_mps"].values[0])),
        "positive_contact_events":positive,
        "worst_contact_distance_m_nominal":worst_contact_distance,
        "owner_sha256":owner_hash(owner),
    }

def corruptions(owner,patch,index,seed,source_sha):
    original=owner_hash(owner)
    result={}
    def reject(name,mutate):
        c=owner.copy(deep=True)
        mutate(c)
        try:validate(c,patch,seed,source_sha,index,True,True)
        except ValueError:result[name]=True
        else:raise AssertionError("Invalid owner accepted "+name)
        assert owner_hash(owner)==original
    reject("mass_plus_1kg",lambda d:d["material_mass_kg"].values.__setitem__(0,SPHERE_M+1))
    reject("negative_mass",lambda d:d["material_mass_kg"].values.__setitem__(0,-1))
    reject("wrong_units",lambda d:d["terrain_height_m_nominal"].attrs.__setitem__("units","cm"))
    reject("change_bedrock",lambda d:d["terrain_height_m_nominal"].values.__setitem__((0,0),d["terrain_height_m_nominal"].values[0,0]+1))
    reject("wrong_source_hash",lambda d:d.attrs.__setitem__("source_sha256","invalid"))
    reject("body_id_changed",lambda d:d.coords.__setitem__("body",np.array([7])))
    reject("duplicate_mass_stock",lambda d:d.__setitem__("extra_mass_kg",xr.DataArray(np.ones(1),dims=("body",))))
    return result

def main(input_file):
    with np.load(input_file,allow_pickle=False) as fd:
        raw={7321:np.asarray(fd["elevation_seed_7321"],dtype="<f8").copy(),
             8128:np.asarray(fd["elevation_seed_8128"],dtype="<f8").copy()}
        producer_sha=[str(x) for x in fd["source_sha256"]]
        source_upstream=str(fd["worldengine_revision"][0])
    failures=[]
    def gate(name,ok):
        if not ok:failures.append(name)
    gate("matching_generator_source",source_upstream==UPSTREAM_SHA and
         all(digest_raw(raw[seed])==SOURCE_HASH[seed] and
             producer_sha[i]==SOURCE_HASH[seed] for i,seed in enumerate(SEEDS)))
    cases={}
    for seed in SEEDS:
        patch,index,spread=choose_patch(raw[seed])
        results={
            "gravity":simulate(patch,seed,SOURCE_HASH[seed],index,True,True),
            "no_gravity":simulate(patch,seed,SOURCE_HASH[seed],index,False,True),
            "no_mesh":simulate(patch,seed,SOURCE_HASH[seed],index,True,False),
        }
        cases[seed]=(patch,index,results)
        active=results["gravity"]
        nog=results["no_gravity"]
        absent=results["no_mesh"]
        gate(f"{seed}_nonflat_patch",spread>=MIN_PATCH_HEIGHT_RANGE)
        gate(f"{seed}_correct_native_triangle_height",
             active["ray_vertical_error_m_nominal"] is not None
             and active["ray_vertical_error_m_nominal"]<.001)
        gate(f"{seed}_real_gravity_contact",active["positive_contact_events"]>0
             and active["descent_m_nominal"]>=1.
             and active["worst_contact_distance_m_nominal"]>=-.05
             and 0<=active["final_position_m_nominal"][0]<=DX
             and 0<=active["final_position_m_nominal"][1]<=DX
             and active["final_position_m_nominal"][2]>=float(patch.min())-1.)
        gate(f"{seed}_g0_no_motion",abs(nog["descent_m_nominal"])<1e-8
             and nog["final_speed_m_nominal_per_s"]<1e-8
             and nog["positive_contact_events"]==0)
        gate(f"{seed}_absence_of_mesh_no_contact",absent["positive_contact_events"]==0
             and absent["descent_m_nominal"]>5.)
    patch,index,metrics=cases[7321]
    replay=simulate(patch,7321,SOURCE_HASH[7321],index,True,True)
    gate("seed7321_replay_exact",np.array_equal(
        metrics["gravity"]["owner"]["position_m"].values,
        replay["owner"]["position_m"].values)
        and np.array_equal(metrics["gravity"]["owner"]["velocity_mps"].values,
                           replay["owner"]["velocity_mps"].values)
        and metrics["gravity"]["owner_sha256"]==replay["owner_sha256"]
        and metrics["gravity"]["positive_contact_events"]==replay["positive_contact_events"]
        and metrics["gravity"]["ray_height_m_nominal"]==replay["ray_height_m_nominal"])
    bad=corruptions(metrics["gravity"]["owner"],patch,index,7321,SOURCE_HASH[7321])
    with tempfile.TemporaryDirectory(prefix="world_h30_") as td:
        path=pathlib.Path(td)/"local_terrain_body.nc"
        metrics["gravity"]["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:
            restored=f.load()
        validate(restored,patch,7321,SOURCE_HASH[7321],index,True,True)
        gate("checkpoint_exact",owner_hash(restored)==metrics["gravity"]["owner_sha256"])
        size=path.stat().st_size
    def public(res):
        return {k:v for k,v in res.items() if k!="owner"}
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"E4 H30 WorldEngine triangular local surface with native Bullet contact",
        "pybullet":version("pybullet"),"python":platform.python_version(),
        "numpy":np.__version__,"xarray":xr.__version__,
        "source_upstream_SHA":source_upstream,"nominal_height_units":"m_nominal, NOT calibrated geology",
        "seed_7321":{k:public(v) for k,v in cases[7321][2].items()},
        "seed_8128":{k:public(v) for k,v in cases[8128][2].items()},
        "negative_owner_candidates":bad,"replay_exact":True,
        "checkpoint_bytes":size,"failed_preregistered_gates":failures,
        "limitations":"2-triangle flat-subset ROI from procedural sample centers, not full arbitrary terrain collision, no continuous material owner joint with Landlab sediment, no geophysical meter calibration."
    },sort_keys=True),flush=True)
    if failures:
        raise AssertionError("H30 preregistered gates failed: "+", ".join(failures))

if __name__=="__main__":
    main(sys.argv[1])
