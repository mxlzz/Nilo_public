"""H40: actual Landlab terrain epochs; same live sphere throughout.
Native H31 mesh + H39 rebuild only static collider; no global time mapping.
"""
import hashlib
import json
import pathlib
import sys
import tempfile
import numpy as np
import pybullet as p
import xarray as xr
from importlib.metadata import version
import probe_e5_h31_owner_contract as c
import probe_e4_h30_worldengine_bullet as mesh
import probe_h37_sequential_bullet_contact as h37

SEEDS=(7321,8128)
PATCH={7321:(10,10),8128:(10,16)}
EXPECTED={
    (7321,.1):"33f352be6a90001f331f8ff97dde4fb12dcd044c02008a3bbcca61bba0b30d0b",
    (7321,0.):"28d3aacfa5a3daf589964c91892e100cd133bfd85a1e2df2511e8717b9430760",
    (8128,.1):"b97a8af673b509330e4a95423da371aaeac623530c3cbba12a243ceb3b48d5c6",
    (8128,0.):"2a86b57667f5c2c554094c18117e74e4058c1f2868c68ce1320b97ebc76b8d02",
}
BLOCK=720
MOTION=("body_position_m_nominal","body_velocity_m_nominal_per_s",
        "body_orientation_xyzw","body_angular_velocity_rad_s")

def height(patch,x,y):
    a,b,z,d=patch[0,0],patch[0,1],patch[1,1],patch[1,0]
    u,v=x/c.DX,y/c.DX
    return float((1-u)*a+(u-v)*b+v*z if u>=v else (1-v)*a+u*z+(v-u)*d)

def terrain(owner,seed):
    y,x=PATCH[seed]
    return c.topography(owner)[y:y+2,x:x+2].copy()

def native(cid,body):
    pos,q=p.getBasePositionAndOrientation(body,physicsClientId=cid)
    vel,omega=p.getBaseVelocity(body,physicsClientId=cid)
    return np.array([*pos,*vel,*q,*omega],dtype=np.float64)

def joint(soil,state,seed,steps):
    out=soil.copy(deep=True)
    out.attrs.update(body_status="released",body_release_count=1,
        patch_y=PATCH[seed][0],patch_x=PATCH[seed][1],bullet_t_s=steps*c.BULLET_DT)
    for key,v in zip(MOTION,(state[:3],state[3:6],state[6:10],state[10:13])):
        out[key].values[0]=v
    validate_joint(out,soil,seed,steps)
    return out

def validate_joint(ds,soil,seed,steps):
    if set(ds.data_vars)!=c.FIELDS_ALL or set(ds.attrs)!=set(soil.attrs):
        raise ValueError("Unknown/duplicate stock or metadata")
    if set(ds.coords)!=set(soil.coords) or any(not np.array_equal(ds[k].values,soil[k].values) for k in soil.coords):
        raise ValueError("Altered coordinates/identity")
    for key in c.FIELDS_ALL:
        if ds[key].dims!=soil[key].dims or ds[key].attrs!=soil[key].attrs:
            raise ValueError("Altered material/pose field contract")
    for key in c.FIELDS_SOIL|{"body_mass_kg"}:
        if not np.array_equal(ds[key].values,soil[key].values):
            raise ValueError("Matter altered independently of solver")
    attrs=dict(soil.attrs)
    attrs.update(body_status="released",body_release_count=1,
        patch_y=PATCH[seed][0],patch_x=PATCH[seed][1],bullet_t_s=steps*c.BULLET_DT)
    if any(ds.attrs[k]!=v for k,v in attrs.items()):
        raise ValueError("Incorrect source/clock/transition state")
    if steps not in (720,1440,2160) or int(ds.attrs["landlab_step"]) not in (0,3,6):
        raise ValueError("Invalid epoch")
    if any(not np.isfinite(ds[k].values).all() for k in MOTION):
        raise ValueError("Nonfinite kinematics")
    if abs(np.linalg.norm(ds[MOTION[2]].values[0])-1.)>1e-4:
        raise ValueError("Invalid orientation")
    total=float(ds.soil_mass_kg.sum())+float(ds.attrs["exported_soil_kg"])+float(ds.body_mass_kg.sum())
    if abs(total-(c.MASS0+c.BODY_MASS))>.09216:
        raise ValueError("Material budget")
    return total

def get_contact(cid,body,ground):
    points=p.getContactPoints(bodyA=body,bodyB=ground,physicsClientId=cid)
    return (sum(float(v[9]) for v in points if v[9]>1e-5),
            min([float(v[8]) for v in points]+[0.]))

def run(soils,seed,k):
    cid=p.connect(p.DIRECT)
    fail=[]
    def gate(name,ok):
        if not ok:fail.append(name)
    def create_ground(patch):
        shape=p.createCollisionShape(p.GEOM_MESH,vertices=mesh.mesh_vertices(patch),
            indices=[0,1,2,0,2,3],flags=p.GEOM_FORCE_CONCAVE_TRIMESH,physicsClientId=cid)
        g=p.createMultiBody(baseMass=0.,baseCollisionShapeIndex=shape,physicsClientId=cid)
        p.changeDynamics(g,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
        return g
    def ray(ground,patch):
        expected=height(patch,70.,70.)
        hit=p.rayTest([70.,70.,expected+10.],[70.,70.,expected-10.],physicsClientId=cid)[0]
        return {"terrain":hit[0]==ground,"expected_z":expected,"ray_z":float(hit[3][2])}
    def check_ray(name,ground,patch):
        v=ray(ground,patch)
        gate(name,v["terrain"] and abs(v["ray_z"]-v["expected_z"])<.001)
        return v
    history=hashlib.sha256()
    prefix=None
    events=[]
    checkpoints=[]
    worst=0.
    try:
        p.setPhysicsEngineParameter(fixedTimeStep=c.BULLET_DT,numSolverIterations=60,
            deterministicOverlappingPairs=1,physicsClientId=cid)
        p.setGravity(0,0,-9.81,physicsClientId=cid)
        patch=terrain(soils[0],seed)
        ground=create_ground(patch)
        shape=p.createCollisionShape(p.GEOM_SPHERE,radius=c.BODY_RADIUS,physicsClientId=cid)
        body=p.createMultiBody(c.BODY_MASS,shape,basePosition=[40.,30.,height(patch,40.,30.)+3.],
                physicsClientId=cid)
        p.changeDynamics(body,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
        check_ray("initial_ray",ground,patch)
        initial_export=float(soils[0].attrs["exported_soil_kg"])
        for epoch,soil in enumerate(soils):
            t=epoch*BLOCK
            if epoch:
                before=native(cid,body)
                old_force,old_dist=get_contact(cid,body,ground)
                new_patch=terrain(soil,seed)
                dz=height(new_patch,before[0],before[1])-height(patch,before[0],before[1])
                old_ground=ground
                p.removeBody(ground,physicsClientId=cid)
                ground=create_ground(new_patch)
                p.changeDynamics(body,-1,activationState=p.ACTIVATION_STATE_WAKE_UP,physicsClientId=cid)
                after=native(cid,body)
                same=bool(np.array_equal(before,after) and p.getNumBodies(physicsClientId=cid)==2
                      and {p.getBodyUniqueId(i,physicsClientId=cid) for i in range(2)}=={ground,body}
                      and p.getDynamicsInfo(body,-1,physicsClientId=cid)[0]==c.BODY_MASS)
                near=p.getClosestPoints(body,ground,distance=2.,physicsClientId=cid)
                closest=min([float(q[8]) for q in near],default=2.)
                gate(f"{epoch}_prior_contact",old_force>0 and old_dist>=-.05)
                gate(f"{epoch}_same_body",same)
                gate(f"{epoch}_within_patch",all(2.<x<98. for x in before[:2]))
                gate(f"{epoch}_no_initial_penetration",closest>=-.05)
                if k:
                    gate(f"{epoch}_erosional_lowering",dz<-.003 and closest>.001)
                else:
                    gate(f"{epoch}_sham_no_height_change",dz==0. and abs(closest)<.05)
                event={"epoch":epoch,"before_body":before.tolist(),"body_preserved":same,
                    "body_id":body,"terrain_ids":[old_ground,ground],
                    "surface_delta_nominal_m":dz,"new_closest_distance_nominal_m":closest,
                    "old_contact_force_N":old_force,
                    "ray":check_ray(f"{epoch}_ray",ground,new_patch)}
                patch=new_patch
                events.append(event)
            for j in range(1,BLOCK+1):
                p.stepSimulation(physicsClientId=cid)
                state=native(cid,body)
                history.update(state.tobytes())
                force,dist=get_contact(cid,body,ground)
                worst=min(worst,dist)
                if j==1 and epoch:
                    dv=float(state[5]-before[5])
                    event.update(first_step_force_N=force,delta_vz_nominal_mps=dv)
                    if k:gate(f"{epoch}_native_gravity_gap",force==0. and -.055<dv<-.025)
            if epoch==0:prefix=history.hexdigest()
            state=native(cid,body)
            force,dist=get_contact(cid,body,ground)
            gate(f"{epoch}_end_contact",force>0 and dist>=-.05)
            gate(f"{epoch}_end_within_patch",all(2.<x<98. for x in state[:2]))
            out=joint(soil,state,seed,t+BLOCK)
            total=validate_joint(out,soil,seed,t+BLOCK)
            export=float(soil.attrs["exported_soil_kg"])
            if epoch:
                gate(f"{epoch}_material_export",export>initial_export if k else export==0.)
            initial_export=export
            checkpoints.append({"landlab_step":int(soil.attrs["landlab_step"]),
                "landlab_t_bench":float(soil.attrs["landlab_t_bench"]),
                "bullet_t_s":float(out.attrs["bullet_t_s"]),
                "owner_sha":c.hash_owner(out),"exported_kg":export,
                "material_total_kg":total,"end_pose":state.tolist(),
                "end_force_N":force,"end_contact_distance_nominal_m":dist})
        gate("contact_penetration_bound",worst>=-.05)
        return {"seed":seed,"K_sed":k,"prefix_sha":prefix,"history_sha":history.hexdigest(),
                "events":events,"epochs":checkpoints,"failed":fail,
                "worst_distance_nominal_m":worst,"owner":out}
    finally:
        p.disconnect(physicsClientId=cid)

def corruptions(owner,soil,seed):
    checks={}
    def reject(n,f):
        v=owner.copy(deep=True);f(v)
        try:validate_joint(v,soil,seed,2160)
        except ValueError:checks[n]=True
        else:raise AssertionError("Corruption accepted "+n)
    reject("extra_stock",lambda v:v.__setitem__("duplicate_soil",v.soil_mass_kg.copy()))
    reject("created_soil",lambda v:v.soil_mass_kg.values.__setitem__((2,2),v.soil_mass_kg.values[2,2]+1))
    reject("body_mass",lambda v:v.body_mass_kg.values.__setitem__(0,3.))
    reject("body_id",lambda v:v.coords.__setitem__("body",np.array([9],dtype=np.int32)))
    reject("wrong_clock",lambda v:v.attrs.__setitem__("bullet_t_s",3.))
    return checks

def main(rawpath,folder):
    raw=h37.read_raw(rawpath)
    root=pathlib.Path(folder)
    manifest=json.loads((root/"manifest.json").read_text())
    cases={}
    soils={}
    for seed in SEEDS:
        for k in (0.,.1):
            name=h37.CASES[(seed,k)]
            d=manifest["cases"][name]
            states=[]
            for step,tag,hashkey in ((0,"initial","initial_sha256"),(3,"checkpoint","mid_sha256"),(6,"baseline","baseline_sha256")):
                with xr.open_dataset(root/f"{name}_{tag}.nc",engine="scipy") as f:ds=f.load()
                c.validate(ds,raw[seed],seed,k)
                if c.hash_owner(ds)!=d[hashkey] or int(ds.attrs["landlab_step"])!=step:
                    raise ValueError("Altered input owner")
                states.append(ds)
            if c.hash_owner(states[2])!=EXPECTED[(seed,k)]:
                raise ValueError("H37 historical soil changed")
            if k==0 and any(not np.array_equal(s.soil_mass_kg.values,states[0].soil_mass_kg.values) or s.attrs["exported_soil_kg"]!=0. for s in states):
                raise ValueError("K0 changed soil")
            soils[(seed,k)]=states
            cases[(seed,k)]=run(states,seed,k)
    replay=run(soils[(7321,.1)],7321,.1)
    failed=[f"{seed}_{k}_{v}" for (seed,k),x in cases.items() for v in x["failed"]]
    for seed in SEEDS:
        a,b=cases[(seed,.1)],cases[(seed,0.)]
        if a["prefix_sha"]!=b["prefix_sha"]:failed.append(f"{seed}_same_prefix")
        if np.linalg.norm(a["owner"][MOTION[0]].values-b["owner"][MOTION[0]].values)<.01:
            failed.append(f"{seed}_different_final_pos")
    a=cases[(7321,.1)]
    if a["history_sha"]!=replay["history_sha"] or a["events"]!=replay["events"] or a["epochs"]!=replay["epochs"]:
        failed.append("replay_exact")
    result={"experiment":"H40 actual soil epochs under same live body","pybullet":version("pybullet"),
        "cases":{f"{s}_{k}":{x:y for x,y in v.items() if x!="owner"} for (s,k),v in cases.items()},
        "failed_preregistered_gates":failed,
        "limitations":"Sequential unilateral nominal geometry; separate clocks; soil independent of body; no bidirectional feedback or coupled restart."}
    print("WORLD_PHYSICAL_JSON "+json.dumps(result,sort_keys=True,default=h37.np_scalar),flush=True)
    for (seed,k),v in cases.items():
        with tempfile.TemporaryDirectory() as td:
            path=pathlib.Path(td)/"owner.nc"
            v["owner"].to_netcdf(path,engine="scipy")
            with xr.open_dataset(path,engine="scipy") as f:back=f.load()
            validate_joint(back,soils[(seed,k)][2],seed,2160)
            if c.hash_owner(back)!=c.hash_owner(v["owner"]):failed.append(f"{seed}_{k}_netcdf")
    result["corruptions_rejected"]=corruptions(a["owner"],soils[(7321,.1)][2],7321)
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True,default=h37.np_scalar),flush=True)
    if failed:raise AssertionError("H40 failed: "+str(failed))
if __name__=="__main__":main(*sys.argv[1:])
