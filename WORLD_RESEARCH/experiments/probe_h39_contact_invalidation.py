"""H39: wake vs rebuild derived static collider; never recreate active body.
Uses H38 owner and measurements unchanged. H38 stays negative.
"""
from probe_h38_mutable_heightfield import *
def run(mode,method):
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
                previous_shape=shape
                previous_ground=ground
                if mode!="static":
                    if method=="rebuild_static":
                        p.removeBody(ground,physicsClientId=cid)
                        shape=shape_update(soil)
                        ground=p.createMultiBody(0,shape,basePosition=[0,0,1.],physicsClientId=cid)
                        p.changeDynamics(ground,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
                    else:
                        returned=shape_update(soil,shape)
                        if returned!=shape:
                            raise ValueError("In-place update returned a different shape")
                    if method in ("wake","rebuild_static"):
                        p.changeDynamics(body,-1,activationState=p.ACTIVATION_STATE_WAKE_UP,physicsClientId=cid)
                after=native(cid,body)
                ds=owner(soil,exported,after,step,mode)
                validate(ds,step,mode)
                epochs.append({"step":step,"pre":trace[-1],"ray_after":cast(cid,ground),
                    "unchanged_body":bool(np.array_equal(before,after)),
                    "same_dynamic_body":bool(count==p.getNumBodies(physicsClientId=cid)==2
                         and {p.getBodyUniqueId(i,physicsClientId=cid) for i in range(2)}=={ground,body}
                         and p.getDynamicsInfo(body,-1,physicsClientId=cid)[0]==MASS),
                    "terrain_ids":[previous_ground,ground],"shape_ids":[previous_shape,shape],
                    "body_id":body,
                    "material_total_kg":validate(ds,step,mode),
                    "exported_kg":exported,
                    "bounds_unchanged":float(terrain(soil).min())==0. and float(terrain(soil).max())==2.})
        final=owner(soil,exported,native(cid,body),3*BLOCK,mode)
        validate(final,3*BLOCK,mode)
        return {"mode":mode,"method":method,"samples":trace,"epochs":epochs,
                "worst_penetration_m":-worst,"exported_kg":exported,
                "owner":final,"sha":digest(final),"history_sha":hist.hexdigest()}
    finally:
        p.disconnect(physicsClientId=cid)

def metrics(x):
    return {k:v for k,v in x.items() if k!="owner"}

def gates(x,reference):
    fail=[]
    def gate(n,ok):
        if not ok:fail.append(n)
    mode=x["mode"]
    gate("same_pre_intervention",x["samples"][0]==reference["samples"][0])
    for j,s in enumerate(x["samples"]):
        z=1.-(.1*j if mode=="active" else 0.)
        gate(f"{j}_ray",s["ray"]["hits_ground"] and abs(s["ray"]["z"]-z)<.001)
        gate(f"{j}_support",abs(s["z"]-z-RADIUS)<.003 and s["speed"]<.01
             and s["normal_force"]>0 and s["xy"]<.01)
    for j,e in enumerate(x["epochs"]):
        z=1.-(.1*(j+1) if mode=="active" else 0.)
        gate(f"{j}_native_body_preserved",e["unchanged_body"] and e["same_dynamic_body"])
        gate(f"{j}_ray_after",e["ray_after"]["hits_ground"] and abs(e["ray_after"]["z"]-z)<.001)
        gate(f"{j}_bounds",e["bounds_unchanged"])
        if mode=="active":
            gate(f"{j}_gravity_gap",-.045<e["delta_vz"]<-.035 and e["first_step"]["normal_force"]==0.)
    gate("penetration",x["worst_penetration_m"]<=.005)
    gate("ledger",x["exported_kg"]==(1500. if mode=="active" else 0.))
    with tempfile.TemporaryDirectory() as td:
        path=pathlib.Path(td)/"owner.nc"
        x["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:restored=f.load()
        validate(restored,1440,mode)
        gate("netcdf",digest(restored)==x["sha"])
    return fail

def main():
    static=run("static","reference")
    old=run("active","reference")
    reference_ok=(not gates(static,static)
       and old["history_sha"]==static["history_sha"]==
          "6f8778475ea591f25649baaa77640d62434a6479017792b709aa8d57eaf52f39"
       and abs(old["samples"][-1]["z"]-1.25)<.003
       and old["samples"][-1]["normal_force"]>0
       and abs(old["samples"][-1]["ray"]["z"]-.8)<.001)
    result={"experiment":"H39 contact invalidation comparison","pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,"reference_reproduced":reference_ok,
        "reference":metrics(old),"static":metrics(static),"variants":{}}
    accepted=[]
    for method in ("wake","rebuild_static"):
        a=run("active",method)
        sham=run("sham",method)
        r=run("active",method)
        fail=gates(a,static)+["sham_"+v for v in gates(sham,static)]
        if not(a["sha"]==r["sha"] and a["history_sha"]==r["history_sha"]
             and a["epochs"]==r["epochs"] and a["samples"]==r["samples"]):
            fail.append("exact_replay")
        rejected=negatives(a["owner"])
        if not fail:accepted.append(method)
        result["variants"][method]={"active":metrics(a),"sham":metrics(sham),
            "rejected":rejected,"failed_gates":fail,"approved":not fail}
    result["accepted_methods"]=accepted
    result["selected_method"]=accepted[0] if accepted else None
    result["failed_preregistered_gates"]=(
        ([] if reference_ok else ["H38_reference_not_reproduced"])+
        ([] if accepted else ["no_native_method_passed"]))
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True,default=scalar),flush=True)
    if result["failed_preregistered_gates"]:
        raise AssertionError("H39 failed: "+str(result["failed_preregistered_gates"]))

if __name__=="__main__":main()
