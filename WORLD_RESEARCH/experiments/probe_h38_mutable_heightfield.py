"""H38: native Bullet heightfield updates under an already active rigid body.
Controlled material withdrawal, NOT an erosion solver. Protocol preregistered.
"""
import hashlib
import json
import pathlib
import tempfile
from importlib.metadata import version

import numpy as np
import pybullet as p
import xarray as xr

N=9
DX=.5
RHO=1200.
AREA=DX**2
MASS=2.
RADIUS=.25
DT=1/240
BLOCK=480
B0=np.full((N,N),.5)
B0[0,0]=0.
B0[-1,-1]=2.
S0=np.zeros((N,N))
S0[2:7,2:7]=.5*RHO*AREA
TOTAL=3752.
FIELDS=("soil_kg","bedrock_m","body_mass_kg","position_m","velocity_mps",
        "orientation_xyzw","angular_velocity_rad_s")
UNITS=("kg","m","kg","m","m/s","1","rad/s")

def scalar(v):
    if isinstance(v,np.generic):return v.item()
    raise TypeError(type(v).__name__)

def terrain(soil):
    return B0+soil/(RHO*AREA)

def native(cid,body):
    pos,q=p.getBasePositionAndOrientation(body,physicsClientId=cid)
    vel,omega=p.getBaseVelocity(body,physicsClientId=cid)
    return np.array([*pos,*vel,*q,*omega],dtype=np.float64)

def owner(soil,out,state,step,mode):
    return xr.Dataset({
        "soil_kg":(("y","x"),soil.copy(),{"units":"kg"}),
        "bedrock_m":(("y","x"),B0.copy(),{"units":"m"}),
        "body_mass_kg":(("body",),[MASS],{"units":"kg"}),
        "position_m":(("body","xyz"),state[None,:3],{"units":"m"}),
        "velocity_mps":(("body","xyz"),state[None,3:6],{"units":"m/s"}),
        "orientation_xyzw":(("body","quat"),state[None,6:10],{"units":"1"}),
        "angular_velocity_rad_s":(("body","xyz"),state[None,10:13],{"units":"rad/s"}),
    },coords={"y":np.arange(N,dtype=np.int32),"x":np.arange(N,dtype=np.int32),
              "body":np.array([0],dtype=np.int32),"xyz":["x","y","z"],
              "quat":["x","y","z","w"]},
       attrs={"step":int(step),"time_s":step*DT,"exported_kg":float(out),
              "mode":mode,"schema_version":1,"density_kg_m3":RHO,
              "node_area_m2":AREA})

def validate(ds,step,mode):
    if set(ds.data_vars)!=set(FIELDS) or any(ds[k].attrs.get("units")!=u for k,u in zip(FIELDS,UNITS)):
        raise ValueError("Wrong inventory schema or units")
    if ds.attrs["step"]!=step or ds.attrs["time_s"]!=step*DT or ds.attrs["mode"]!=mode:
        raise ValueError("Wrong clock or scenario")
    soil=ds.soil_kg.values
    if soil.shape!=(N,N) or not np.isfinite(soil).all() or (soil<0).any() or (soil[S0==0]!=0).any():
        raise ValueError("Invalid soil")
    if not np.array_equal(ds.bedrock_m.values,B0) or not np.array_equal(ds.body_mass_kg.values,[MASS]):
        raise ValueError("Altered geometry or body mass")
    out=float(ds.attrs["exported_kg"])
    if out<0 or not np.isfinite(out) or abs(float(soil.sum())+out+MASS-TOTAL)>1e-9:
        raise ValueError("Material ledger invalid")
    if any(not np.isfinite(ds[k].values).all() for k in FIELDS[3:]):
        raise ValueError("Invalid pose")
    if abs(np.linalg.norm(ds.orientation_xyzw.values[0])-1)>1e-4:
        raise ValueError("Invalid orientation")
    return float(soil.sum())+out+MASS

def digest(ds):
    h=hashlib.sha256()
    for k in FIELDS:
        h.update(k.encode()+ds[k].values.tobytes()+ds[k].attrs["units"].encode())
    h.update(json.dumps(ds.attrs,sort_keys=True,default=scalar).encode())
    for k in ("y","x","body","xyz","quat"):
        h.update(repr(ds.coords[k].values.tolist()).encode())
    return h.hexdigest()

def contacts(cid,body,ground):
    c=p.getContactPoints(bodyA=body,bodyB=ground,physicsClientId=cid)
    return (sum(float(x[9]) for x in c if x[9]>1e-5),
            min([float(x[8]) for x in c]+[0.]))

def cast(cid,ground):
    h=p.rayTest([.5,0.,3.],[.5,0.,-1.],physicsClientId=cid)[0]
    return {"hits_ground":h[0]==ground,"z":float(h[3][2])}

def run(mode):
    soil=S0.copy()
    exported=0.
    cid=p.connect(p.DIRECT)
    try:
        p.setPhysicsEngineParameter(fixedTimeStep=DT,numSolverIterations=60,
                                     deterministicOverlappingPairs=1,physicsClientId=cid)
        p.setGravity(0,0,-9.81,physicsClientId=cid)
        def shape_update(s,previous=None):
            kw={} if previous is None else {"replaceHeightfieldIndex":previous}
            return p.createCollisionShape(p.GEOM_HEIGHTFIELD,
                    meshScale=[DX,DX,1.],heightfieldData=terrain(s).ravel().tolist(),
                    numHeightfieldRows=N,numHeightfieldColumns=N,
                    physicsClientId=cid,**kw)
        shape=shape_update(soil)
        ground=p.createMultiBody(0,shape,basePosition=[0,0,1.],physicsClientId=cid)
        sp=p.createCollisionShape(p.GEOM_SPHERE,radius=RADIUS,physicsClientId=cid)
        body=p.createMultiBody(MASS,sp,basePosition=[0,0,1.6],physicsClientId=cid)
        for b in (ground,body):
            p.changeDynamics(b,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
        hist=hashlib.sha256()
        trace=[]
        epochs=[]
        def sample():
            state=native(cid,body)
            force,dist=contacts(cid,body,ground)
            return {"z":float(state[2]),"vz":float(state[5]),
                    "speed":float(np.linalg.norm(state[3:6])),
                    "xy":float(np.linalg.norm(state[:2])),
                    "normal_force":force,"contact_distance":dist,
                    "ray":cast(cid,ground)}
        worst=0.
        for step in range(1,3*BLOCK+1):
            p.stepSimulation(physicsClientId=cid)
            hist.update(native(cid,body).tobytes())
            _,dist=contacts(cid,body,ground)
            worst=min(worst,dist)
            if step in (BLOCK+1,2*BLOCK+1):
                epochs[-1]["first_step"]=sample()
                epochs[-1]["delta_vz"]=epochs[-1]["first_step"]["vz"]-epochs[-1]["pre"]["vz"]
            if step%BLOCK==0:
                trace.append(sample())
                if step==3*BLOCK:break
                before=native(cid,body)
                count=p.getNumBodies(physicsClientId=cid)
                if mode=="active":
                    old=soil.copy()
                    soil[2:7,2:7]-=.1*RHO*AREA
                    exported+=float((old-soil).sum())
                returned=shape
                if mode!="static":
                    returned=shape_update(soil,shape)
                after=native(cid,body)
                ds=owner(soil,exported,after,step,mode)
                validate(ds,step,mode)
                epochs.append({"step":step,"pre":trace[-1],"ray_after":cast(cid,ground),
                    "unchanged_body":bool(np.array_equal(before,after)),
                    "same_shape_and_ids":bool(returned==shape and count==p.getNumBodies(physicsClientId=cid)==2
                         and p.getBodyUniqueId(0,physicsClientId=cid)==ground
                         and p.getBodyUniqueId(1,physicsClientId=cid)==body),
                    "material_total_kg":validate(ds,step,mode),
                    "exported_kg":exported,
                    "bounds_unchanged":float(terrain(soil).min())==0. and float(terrain(soil).max())==2.})
        final=owner(soil,exported,native(cid,body),3*BLOCK,mode)
        validate(final,3*BLOCK,mode)
        return {"mode":mode,"samples":trace,"epochs":epochs,
                "worst_penetration_m":-worst,"exported_kg":exported,
                "owner":final,"sha":digest(final),"history_sha":hist.hexdigest()}
    finally:
        p.disconnect(physicsClientId=cid)

def negatives(ds):
    results={}
    def reject(name,mutate):
        other=ds.copy(deep=True)
        mutate(other)
        try:validate(other,1440,"active")
        except ValueError:results[name]=True
        else:raise AssertionError("Invalid owner accepted: "+name)
    reject("created_mass",lambda d:d.soil_kg.values.__setitem__((4,4),d.soil_kg.values[4,4]+1))
    reject("negative_mass",lambda d:d.soil_kg.values.__setitem__((4,4),-1))
    reject("wrong_units",lambda d:d.soil_kg.attrs.__setitem__("units","g"))
    reject("duplicate_stock",lambda d:d.__setitem__("other_mass",d.soil_kg.copy()))
    reject("wrong_clock",lambda d:d.attrs.__setitem__("step",1))
    return results

def main():
    a=run("active")
    s=run("sham")
    n=run("static")
    r=run("active")
    fail=[]
    def gate(name,ok):
        if not ok:fail.append(name)
    for x in (a,s,n,r):
        mode=x["mode"]
        for j,sample in enumerate(x["samples"]):
            target=1.-(.1*j if mode=="active" else 0.)
            gate(mode+str(j)+"_ray",sample["ray"]["hits_ground"] and abs(sample["ray"]["z"]-target)<.001)
            gate(mode+str(j)+"_support",abs(sample["z"]-(target+RADIUS))<.003
                 and sample["speed"]<.01 and sample["normal_force"]>0 and sample["xy"]<.01)
        for j,e in enumerate(x["epochs"]):
            target=1.-(.1*(j+1) if mode=="active" else 0.)
            gate(mode+str(j)+"_same_native_body",e["unchanged_body"] and e["same_shape_and_ids"])
            gate(mode+str(j)+"_updated_ray",e["ray_after"]["hits_ground"] and abs(e["ray_after"]["z"]-target)<.001)
            gate(mode+str(j)+"_bounds",e["bounds_unchanged"])
            if mode=="active":
                gate("active"+str(j)+"_gravity_gap",-.045<e["delta_vz"]<-.035
                     and e["first_step"]["normal_force"]==0.)
        gate(mode+"_penetration",x["worst_penetration_m"]<=.005)
        gate(mode+"_stock",x["exported_kg"]==(1500. if mode=="active" else 0.))
    gate("exact_active_replay",a["sha"]==r["sha"] and a["history_sha"]==r["history_sha"]
         and a["epochs"]==r["epochs"] and a["samples"]==r["samples"])
    rejected=negatives(a["owner"])
    with tempfile.TemporaryDirectory() as t:
        path=pathlib.Path(t)/"owner.nc"
        a["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:back=f.load()
        validate(back,1440,"active")
        gate("netcdf_exact",digest(back)==a["sha"])
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"H38 native mutable heightfield under live body",
        "pybullet":version("pybullet"),"numpy":np.__version__,"xarray":xr.__version__,
        "cases":[{k:v for k,v in x.items() if k!="owner"} for x in (a,s,n)],
        "rejected":rejected,"failed_preregistered_gates":fail,
        "limitations":"Prescribed two withdrawals, fixed min/max, no native erosion or feedback, no integrated environmental clock."
    },sort_keys=True,default=scalar),flush=True)
    if fail:raise AssertionError("H38 failed: "+", ".join(fail))

if __name__=="__main__":main()
