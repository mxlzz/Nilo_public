"""P0-B: joint checkpoints after the first actual terrain replacement."""
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import numpy as np
import pybullet as p
import xarray as xr
import probe_h40_live_body_soil_epochs as h40
import probe_h37_sequential_bullet_contact as h37
import probe_e5_h31_owner_contract as c
import probe_e4_h30_worldengine_bullet as mesh
import p0a_world_runner as a

MID=1440
END=2160
BLOCK=720

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def file_sha(path):return sha_bytes(path.read_bytes())
def read_owner(path):
    with xr.open_dataset(path,engine="scipy") as f:return f.load()
def dump(path,data):path.write_text(json.dumps(data,sort_keys=True,indent=2,default=h37.np_scalar))
def project(joint,raw,seed,k):
    soil=c.augment(c.soil_only(joint),seed,c.SOURCES[seed],k)
    for key in ("landlab_step","landlab_t_bench"):
        soil.attrs[key]=joint.attrs[key]
    c.validate(soil,raw,seed,k)
    h40.validate_joint(joint,soil,seed,MID)
    return soil

def save_bundle(folder,joint,stream,trace,cid,body,ground,seed,k,abort=False):
    stage=folder.with_name(folder.name+".staging")
    stage.mkdir()
    try:
        joint.to_netcdf(stage/"owner.nc",engine="scipy")
        if c.hash_owner(read_owner(stage/"owner.nc"))!=c.hash_owner(joint):raise ValueError("Checkpoint NetCDF")
        p.saveBullet(str(stage/"native.bullet"),physicsClientId=cid)
        (stage/"prefix.bin").write_bytes(np.asarray(trace,dtype=np.float64).tobytes())
        if len(trace)!=MID:raise ValueError("Prefix length")
        meta={"seed":seed,"K":k,"mid":MID,"soil_step":3,"body_id":body,"ground_id":ground,
             "initial_patch":h40.terrain(stream.cache[0],seed).tolist(),
             "current_patch":h40.terrain(stream.cache[1],seed).tolist(),
             "owner_sha":c.hash_owner(joint),"soil_sha":c.hash_owner(stream.cache[1]),
             "contact":h40.get_contact(cid,body,ground),"prefix_sha":file_sha(stage/"prefix.bin"),
             "files":{f:file_sha(stage/f) for f in ("owner.nc","native.bullet","prefix.bin")}}
        dump(stage/"manifest.json",meta)
        if abort:return False
        stage.replace(folder)
        return True
    finally:
        if stage.exists():shutil.rmtree(stage)

def produce_case(rawpath,python,raw,seed,k,folder):
    trace=[]; ids={}; gates=[]
    step_original=p.stepSimulation; joint_original=h40.joint
    def gate(name,ok):
        if not ok:gates.append(name)
    with tempfile.TemporaryDirectory() as private:
        stream=a.OnDemand(python,rawpath,raw,seed,k,private)
        def step(*args,**kwargs):
            ans=step_original(*args,**kwargs)
            cid=kwargs["physicsClientId"]
            if not ids:
                ids.update(cid=cid,body=next(i for i in (p.getBodyUniqueId(j,physicsClientId=cid) for j in range(p.getNumBodies(physicsClientId=cid))) if p.getDynamicsInfo(i,-1,physicsClientId=cid)[0]==c.BODY_MASS))
            trace.append(h40.native(cid,ids["body"]))
            return ans
        def joint(soil,state,s,steps):
            out=stream.publish(soil,state,s,steps,joint_original)
            if steps==MID:
                cid=ids["cid"]; body=ids["body"]
                ground=next(i for i in (p.getBodyUniqueId(j,physicsClientId=cid) for j in range(p.getNumBodies(physicsClientId=cid))) if i!=body)
                gate("mid_support",h40.get_contact(cid,body,ground)[0]>0)
                gate("mid_projection",c.hash_owner(project(out,raw,seed,k))==c.hash_owner(soil))
                gate("mid_reference",c.hash_owner(out)==a.REFERENCE[seed,k][1][1])
                gate("abort_not_visible",not save_bundle(folder,out,stream,trace,cid,body,ground,seed,k,True) and not folder.exists())
                gate("checkpoint_published",save_bundle(folder,out,stream,trace,cid,body,ground,seed,k))
            return out
        p.stepSimulation=step; h40.joint=joint
        try:result=h40.run(stream,seed,k)
        finally:p.stepSimulation=step_original; h40.joint=joint_original
        gate("reference_history",result["history_sha"]==a.REFERENCE[seed,k][0]==sha_bytes(np.asarray(trace).tobytes()))
        gate("reference_owners",tuple(c.hash_owner(x) for x in stream.joints)==a.REFERENCE[seed,k][1])
        gate("reference_events",[e["event"] for e in stream.events]==a.ORDER)
        gates.extend(result["failed"])
        return {"seed":seed,"K":k,"history_sha":result["history_sha"],"final_contact":[result["epochs"][-1]["end_force_N"],result["epochs"][-1]["end_contact_distance_nominal_m"]],"failed":gates}

def verify_bundle(folder,raw,seed,k):
    meta=json.loads((folder/"manifest.json").read_text())
    if (meta["seed"],meta["K"],meta["mid"],meta["soil_step"])!=(seed,k,MID,3):raise ValueError("Manifest identity")
    for name in ("owner.nc","native.bullet","prefix.bin"):
        if file_sha(folder/name)!=meta["files"][name]:raise ValueError("File digest "+name)
    joint=read_owner(folder/"owner.nc")
    soil=project(joint,raw,seed,k)
    if c.hash_owner(joint)!=meta["owner_sha"] or meta["owner_sha"]!=a.REFERENCE[seed,k][1][1] or c.hash_owner(soil)!=meta["soil_sha"]:raise ValueError("Owner digest")
    prefix=(folder/"prefix.bin").read_bytes()
    if len(prefix)!=MID*13*8 or sha_bytes(prefix)!=meta["prefix_sha"]:raise ValueError("Prefix bytes")
    state=np.r_[joint[h40.MOTION[0]].values[0],joint[h40.MOTION[1]].values[0],joint[h40.MOTION[2]].values[0],joint[h40.MOTION[3]].values[0]]
    if not np.array_equal(np.frombuffer(prefix,dtype=np.float64).reshape(MID,13)[-1],state):raise ValueError("Prefix endpoint")
    initial=h40.terrain(c.augment(c.soil_only(joint),seed,c.SOURCES[seed],k),seed)
    # Original initial patch has initial uniform core soil thickness (one metre).
    initial_owner=c.augment(c.soil_only(joint),seed,c.SOURCES[seed],k)
    initial_owner["soil_mass_kg"].values[:]=np.where(initial_owner["is_core_node"].values!=0,c.RHO*c.AREA*1.,0.)
    initial=h40.terrain(initial_owner,seed)
    if not np.array_equal(initial,np.asarray(meta["initial_patch"])) or not np.array_equal(h40.terrain(soil,seed),np.asarray(meta["current_patch"])):raise ValueError("Collider recipe")
    return meta,joint,soil,prefix,state

def ground_for(cid,patch):
    shape=p.createCollisionShape(p.GEOM_MESH,vertices=mesh.mesh_vertices(patch),indices=[0,1,2,0,2,3],flags=p.GEOM_FORCE_CONCAVE_TRIMESH,physicsClientId=cid)
    ground=p.createMultiBody(baseMass=0.,baseCollisionShapeIndex=shape,physicsClientId=cid)
    p.changeDynamics(ground,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
    return ground

def consume_case(rawpath,python,raw,seed,k,folder,reference,outdir):
    failed=[]
    def gate(name,ok):
        if not ok:failed.append(name)
    meta,joint,soil,prefix,expected=verify_bundle(folder,raw,seed,k)
    bad=joint.copy(deep=True);bad["body_mass_kg"].values[0]+=1.
    try:project(bad,raw,seed,k)
    except ValueError:pass
    else:failed.append("invalid_owner_accepted")
    with tempfile.TemporaryDirectory() as tmp:
        corrupt=pathlib.Path(tmp)/"corrupt";shutil.copytree(folder,corrupt)
        b=bytearray((corrupt/"native.bullet").read_bytes());b[-1]^=1;(corrupt/"native.bullet").write_bytes(b)
        try:verify_bundle(corrupt,raw,seed,k)
        except ValueError:pass
        else:failed.append("invalid_cache_accepted")
    cid=p.connect(p.DIRECT)
    try:
        p.setPhysicsEngineParameter(fixedTimeStep=c.BULLET_DT,numSolverIterations=60,deterministicOverlappingPairs=1,physicsClientId=cid)
        p.setGravity(0,0,-9.81,physicsClientId=cid)
        initial=np.asarray(meta["initial_patch"]);patch=np.asarray(meta["current_patch"])
        ground=ground_for(cid,initial)
        shape=p.createCollisionShape(p.GEOM_SPHERE,radius=c.BODY_RADIUS,physicsClientId=cid)
        body=p.createMultiBody(c.BODY_MASS,shape,basePosition=[40.,30.,h40.height(initial,40.,30.)+3.],physicsClientId=cid)
        p.changeDynamics(body,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
        p.removeBody(ground,physicsClientId=cid);ground=ground_for(cid,patch)
        p.changeDynamics(body,-1,activationState=p.ACTIVATION_STATE_WAKE_UP,physicsClientId=cid)
        gate("recipe_ids",(body,ground)==(meta["body_id"],meta["ground_id"]))
        try:p.restoreState(fileName=str(folder/"native.bullet"),physicsClientId=cid)
        except Exception as e:
            return {"seed":seed,"K":k,"failed":failed+["native_restore_exception"],"error":str(e)}
        restored=h40.native(cid,body)
        gate("exact_restored_pose",np.array_equal(restored,expected))
        gate("restored_mass",p.getDynamicsInfo(body,-1,physicsClientId=cid)[0]==c.BODY_MASS)
        gate("restored_contact",list(h40.get_contact(cid,body,ground))==meta["contact"])
        if failed:return {"seed":seed,"K":k,"failed":failed,"pose_delta":(restored-expected).tolist()}
        with tempfile.TemporaryDirectory() as tmp:
            stream=a.OnDemand(python,rawpath,raw,seed,k,tmp)
            # Existing prefix is supplied only as the validated previous soil;
            # no calls to initialize or advance the past.
            stream.cache=[None,soil];stream.events=[{"event":"FIN1440"}]
            soil.to_netcdf(pathlib.Path(tmp)/"soil_3.nc",engine="scipy")
            next_soil=stream[2]
            gate("only_remaining_soil",len(stream.events)==2 and stream.events[1]["from"]==4 and stream.events[1]["to"]==6)
        before=h40.native(cid,body)
        old_force,old_dist=h40.get_contact(cid,body,ground)
        new_patch=h40.terrain(next_soil,seed)
        dz=h40.height(new_patch,*before[:2])-h40.height(patch,*before[:2])
        p.removeBody(ground,physicsClientId=cid);ground=ground_for(cid,new_patch)
        p.changeDynamics(body,-1,activationState=p.ACTIVATION_STATE_WAKE_UP,physicsClientId=cid)
        gate("same_body",np.array_equal(before,h40.native(cid,body)) and p.getNumBodies(physicsClientId=cid)==2)
        near=p.getClosestPoints(body,ground,distance=2.,physicsClientId=cid)
        closest=min([float(q[8]) for q in near],default=2.)
        gate("prior_contact",old_force>0 and old_dist>=-.05)
        gate("initial_penetration",closest>=-.05)
        gate("within_patch_before",all(2.<x<98. for x in before[:2]))
        gate("terrain_change",(dz<-.003 and closest>.001) if k else (dz==0. and abs(closest)<.05))
        rayz=h40.height(new_patch,70.,70.)
        hit=p.rayTest([70.,70.,rayz+10],[70.,70.,rayz-10],physicsClientId=cid)[0]
        gate("terrain_ray",hit[0]==ground and abs(hit[3][2]-rayz)<.001)
        trace=[];worst=0.;first={}
        for j in range(1,BLOCK+1):
            p.stepSimulation(physicsClientId=cid)
            state=h40.native(cid,body)
            trace.append(state)
            force,dist=h40.get_contact(cid,body,ground);worst=min(worst,dist)
            if j==1:
                first={"force":force,"dvz":float(state[5]-before[5])}
                if k:gate("native_gravity_gap",force==0. and -.055<first["dvz"]<-.025)
        state=trace[-1];force,dist=h40.get_contact(cid,body,ground)
        final=h40.joint(next_soil,state,seed,END)
        gate("remaining_steps",len(trace)==BLOCK)
        full=sha_bytes(prefix+np.asarray(trace,dtype=np.float64).tobytes())
        gate("history_exact",full==a.REFERENCE[seed,k][0])
        gate("final_owner_exact",c.hash_owner(final)==a.REFERENCE[seed,k][1][-1])
        gate("final_soil_exact",c.hash_owner(next_soil)==h40.EXPECTED[seed,k])
        gate("final_contacts_exact",[force,dist]==reference["final_contact"])
        gate("support_and_patch",force>0 and worst>=-.05 and all(2.<x<98. for x in state[:2]))
        gate("material_export",float(next_soil.attrs["exported_soil_kg"])>float(soil.attrs["exported_soil_kg"]) if k else float(next_soil.attrs["exported_soil_kg"])==0.)
        target=outdir/f"{seed}_{k}.nc"
        final.to_netcdf(target,engine="scipy")
        back=read_owner(target);h40.validate_joint(back,next_soil,seed,END)
        gate("final_roundtrip",c.hash_owner(back)==c.hash_owner(final))
        gate("checkpoint_unchanged",file_sha(folder/"owner.nc")==meta["files"]["owner.nc"] and file_sha(folder/"native.bullet")==meta["files"]["native.bullet"])
        return {"seed":seed,"K":k,"failed":failed,"history_sha":full,"final_sha":c.hash_owner(final),"first":first,"final_contact":[force,dist],"terrain_delta":dz,"remaining_steps":len(trace),"provider_event":stream.events[-1]}
    finally:p.disconnect(physicsClientId=cid)

def main(mode,rawpath,python,folder,*output):
    raw=h37.read_raw(rawpath);root=pathlib.Path(folder)
    cases={};failed=[]
    if mode=="produce":root.mkdir(parents=True,exist_ok=False)
    else:
        out=pathlib.Path(output[0]);out.mkdir(parents=True,exist_ok=False)
        ref=json.loads((root/"result.json").read_text())
        if ref["failed_preregistered_gates"]:raise ValueError("Producer failed")
    for seed in h40.SEEDS:
        for k in (0.,.1):
            key=f"{seed}_{k}"
            if mode=="produce":rec=produce_case(rawpath,python,raw[seed],seed,k,root/key)
            else:rec=consume_case(rawpath,python,raw[seed],seed,k,root/key,ref["cases"][key],out)
            cases[key]=rec;failed.extend(key+"_"+v for v in rec["failed"])
            print("WORLD_CASE_JSON "+json.dumps(rec,sort_keys=True,default=h37.np_scalar),flush=True)
    data={"experiment":"P0-B","mode":mode,"cases":cases,"failed_preregistered_gates":failed}
    dump((root if mode=="produce" else out)/"result.json",data)
    print("WORLD_EVAL_JSON "+json.dumps(data,sort_keys=True,default=h37.np_scalar),flush=True)
    if failed:raise AssertionError("P0-B "+str(failed))

if __name__=="__main__":main(*sys.argv[1:])
