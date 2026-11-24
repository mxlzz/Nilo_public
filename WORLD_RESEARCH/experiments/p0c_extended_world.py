"""P0-C: finite extended world with checkpoint beyond the historical horizon."""
import hashlib
import json
import pathlib
import resource
import shutil
import subprocess
import sys
import tempfile
import time
import numpy as np
import pybullet as p
import probe_e5_h31_owner_contract as c
import probe_h40_live_body_soil_epochs as h40
import probe_h37_sequential_bullet_contact as h37
import p0b_joint_restart as b
import p0b_profile_restart as profile

HORIZON=18
BLOCK=720
MID_EPOCH=3
WORKER=pathlib.Path(__file__).with_name("p0c_landlab_worker.py")
REF={
(7321,0.):("b72798b4faa32c8c2ad912479e411ea010e9378994e4b92748858e8026b80ea0",["5899e70ea69d4ac1da274a2020f52a3155e19cc18ded3d15efad53cf694cd7ed","4d0b35e0c30abb9d4ace38046535fea4bf3c0e5200e11a2074c05a0c0fef38f0","2bb7fe3a72c4805d81fe920f85cc1f940a72bcb48a79cd3c90ba653a69a696a8"]),
(7321,.1):("763fc0afab3f7afaa2c23bca2d3a3a523f14c72f48d59380a64962019e70d3b4",["ef5cffa37f621af94b90137c809ced3a2dd4d7c1be410a8f3f21cda79cd01f02","56407817aa9c27304d70da49698cb87e390bcf260cc7bbe35b8db3ac54b09422","f14c93a36c55428f7573d8dd0fe6eb47c21a20a3a27677326270d0b80ad7ed69"]),
(8128,0.):("f4fe53c9fa67074e95cb93c25b0bab9446bd48eefc338cbdd6ccb85cbc2a9197",["9b206cbfe0eadbdff16d317b7ec08e6ed64966328bb7c75a0a09efa5a3b901c2","f7db34f7b449ae80e8ff54231599dfb05e4ac920dc2a657cc5dbb2c956f092fe","d3afc98df991a5da3554f09a5c857fa8788f25db4635deda71688524e5e956af"]),
(8128,.1):("7c844185286eb2e9c1e7c52ba4f68d710089d8304b77e23000354bcd2b624f15",["ec2e2d1352bec21895d443b3a70767ec1046c1db82e56ba52e698171654c0a4b","34828e7f87c14c5bef85cd019cf46d8698c41a4d09aaf8f4ff13b05da680c996","467bd72a62ecc3d12ab963ba62ad51365f5b72d97a1288a2e9d0ce3531f4546d"])
}

def require(ok,name):
    if not ok:raise ValueError(name)
def motion(ds):
    return np.concatenate([ds[key].values[0] for key in h40.MOTION])
def project(joint,raw,seed,k):
    soil=c.augment(c.soil_only(joint),seed,c.SOURCES[seed],k)
    for key in ("landlab_step","landlab_t_bench"):soil.attrs[key]=joint.attrs[key]
    c.validate(soil,raw,seed,k,max_step=HORIZON)
    return soil

def validate_joint(joint,soil,raw,seed,k,epoch):
    c.validate(soil,raw,seed,k,max_step=HORIZON)
    require(int(soil.attrs["landlab_step"])==3*epoch,"soil epoch")
    require(set(joint.data_vars)==c.FIELDS_ALL and set(joint.attrs)==set(soil.attrs),"joint stock schema")
    require(set(joint.coords)==set(soil.coords) and all(np.array_equal(joint[v].values,soil[v].values) for v in soil.coords),"joint identity")
    attrs=dict(soil.attrs)
    attrs.update(body_status="released",body_release_count=1,patch_y=h40.PATCH[seed][0],patch_x=h40.PATCH[seed][1],bullet_t_s=(epoch+1)*BLOCK*c.BULLET_DT)
    require(all(joint.attrs[key]==value for key,value in attrs.items()),"joint clocks or attrs")
    for key in c.FIELDS_ALL:
        require(joint[key].dims==soil[key].dims and joint[key].attrs==soil[key].attrs,"joint field contract")
    for key in c.FIELDS_SOIL|{"body_mass_kg"}:
        require(np.array_equal(joint[key].values,soil[key].values),"joint stock changed")
    state=motion(joint)
    require(np.isfinite(state).all() and abs(np.linalg.norm(state[6:10])-1.)<1e-4,"invalid pose")
    require(all(2.<x<98. for x in state[:2]),"body escaped patch")
    residual=float(joint.soil_mass_kg.sum())+float(joint.attrs["exported_soil_kg"])+float(joint.body_mass_kg.sum())-(c.MASS0+c.BODY_MASS)
    require(abs(residual)<=.09216,"material budget")
    return residual

def make_joint(soil,state,raw,seed,k,epoch):
    out=soil.copy(deep=True)
    out.attrs.update(body_status="released",body_release_count=1,patch_y=h40.PATCH[seed][0],patch_x=h40.PATCH[seed][1],bullet_t_s=(epoch+1)*BLOCK*c.BULLET_DT)
    for key,value in zip(h40.MOTION,(state[:3],state[3:6],state[6:10],state[10:13])):
        out[key].values[0]=value
    validate_joint(out,soil,raw,seed,k,epoch)
    return out

def request(python,rawpath,raw,seed,k,folder,epoch,old):
    target=epoch*3; dest=folder/f"soil_{target}.nc"
    require(not dest.exists(),"duplicate soil request")
    prev="-" if epoch==0 else str(folder/f"soil_{target-3}.nc")
    require((old is None)==(epoch==0),"missing predecessor")
    if old is not None:require(int(old.attrs["landlab_step"])==target-3,"wrong predecessor epoch")
    proc=subprocess.run([python,str(WORKER),rawpath,str(seed),str(k),prev,str(target),str(dest)],capture_output=True,text=True)
    if proc.returncode:raise RuntimeError(proc.stdout+"\n"+proc.stderr)
    event=json.loads(next(line.split("P0C_SOIL_JSON ",1)[1] for line in proc.stdout.splitlines() if line.startswith("P0C_SOIL_JSON ")))
    soil=b.read_owner(dest);c.validate(soil,raw,seed,k,max_step=HORIZON)
    require(event["seed"]==seed and event["K"]==k and event["to"]==target and event["from"]==(None if epoch==0 else target-2) and event["input_sha"]==(None if old is None else c.hash_owner(old)) and event["output_sha"]==c.hash_owner(soil),"worker event mismatch")
    return soil,event

def setup(cid,patch):
    p.setPhysicsEngineParameter(fixedTimeStep=c.BULLET_DT,numSolverIterations=60,deterministicOverlappingPairs=1,physicsClientId=cid)
    p.setGravity(0,0,-9.81,physicsClientId=cid)
    ground=b.ground_for(cid,patch)
    shape=p.createCollisionShape(p.GEOM_SPHERE,radius=c.BODY_RADIUS,physicsClientId=cid)
    body=p.createMultiBody(c.BODY_MASS,shape,basePosition=[40.,30.,h40.height(patch,40.,30.)+3.],physicsClientId=cid)
    p.changeDynamics(body,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
    return body,ground
def replace(cid,body,ground,patch):
    p.removeBody(ground,physicsClientId=cid)
    ground=b.ground_for(cid,patch)
    p.changeDynamics(body,-1,activationState=p.ACTIVATION_STATE_WAKE_UP,physicsClientId=cid)
    return ground

def save(folder,joint,prefix,recipe,cid,body,ground,seed,k):
    stage=folder.with_name(folder.name+".staging");stage.mkdir()
    try:
        joint.to_netcdf(stage/"owner.nc",engine="scipy")
        p.saveBullet(str(stage/"native.bullet"),physicsClientId=cid)
        (stage/"prefix.bin").write_bytes(prefix)
        meta={"profile":profile.PROFILE,"seed":seed,"K":k,"epoch":MID_EPOCH,"recipe":recipe,"body":body,"ground":ground,
            "owner_sha":c.hash_owner(joint),"contact":list(h40.get_contact(cid,body,ground)),
            "files":{name:b.file_sha(stage/name) for name in ("owner.nc","native.bullet","prefix.bin")}}
        b.dump(stage/"manifest.json",meta)
        require(c.hash_owner(b.read_owner(stage/"owner.nc"))==meta["owner_sha"],"checkpoint roundtrip")
        stage.replace(folder)
    finally:
        if stage.exists():shutil.rmtree(stage)

def verify(folder,raw,seed,k):
    meta=json.loads((folder/"manifest.json").read_text());profile.verify_profile(meta)
    require((meta["seed"],meta["K"],meta["epoch"])==(seed,k,MID_EPOCH),"checkpoint identity")
    for name in ("owner.nc","native.bullet","prefix.bin"):require(b.file_sha(folder/name)==meta["files"][name],"checkpoint digest "+name)
    joint=b.read_owner(folder/"owner.nc");soil=project(joint,raw,seed,k)
    validate_joint(joint,soil,raw,seed,k,MID_EPOCH)
    prefix=(folder/"prefix.bin").read_bytes()
    require(len(prefix)==(MID_EPOCH+1)*BLOCK*13*8 and np.array_equal(np.frombuffer(prefix,dtype=np.float64).reshape(-1,13)[-1],motion(joint)),"prefix endpoint")
    require(c.hash_owner(joint)==meta["owner_sha"],"owner hash")
    recipe=np.asarray(meta["recipe"])
    require(recipe.shape==(MID_EPOCH+1,2,2) and np.isfinite(recipe).all() and np.array_equal(recipe[-1],h40.terrain(soil,seed)),"collider recipe")
    return meta,joint,soil,prefix,recipe.tolist()

def run(rawpath,python,raw,seed,k,folder,out,resume=False):
    start=time.monotonic();cpu=time.process_time()
    cid=p.connect(p.DIRECT);epochs=[];requests=[];trace=bytearray();recipe=[];old=None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            private=pathlib.Path(tmp)
            if resume:
                meta,joint,old,prefix,recipe=verify(folder,raw,seed,k)
                bad=joint.copy(deep=True);bad["body_mass_kg"].values[0]+=1.
                try:validate_joint(bad,old,raw,seed,k,MID_EPOCH)
                except ValueError:pass
                else:raise ValueError("bad stock accepted")
                with tempfile.TemporaryDirectory() as ct:
                    copy=pathlib.Path(ct)/"corrupt";shutil.copytree(folder,copy)
                    data=bytearray((copy/"native.bullet").read_bytes());data[-1]^=1;(copy/"native.bullet").write_bytes(data)
                    try:verify(copy,raw,seed,k)
                    except ValueError:pass
                    else:raise ValueError("bad cache accepted")
                body,ground=setup(cid,np.asarray(recipe[0]))
                for patch in recipe[1:]:ground=replace(cid,body,ground,np.asarray(patch))
                require((body,ground)==(meta["body"],meta["ground"]),"restored IDs")
                p.restoreState(fileName=str(folder/"native.bullet"),physicsClientId=cid)
                require(np.array_equal(h40.native(cid,body),motion(joint)) and list(h40.get_contact(cid,body,ground))==meta["contact"],"native restore")
                old.to_netcdf(private/"soil_9.nc",engine="scipy")
                trace.extend(prefix);first_epoch=MID_EPOCH+1;patch=np.asarray(recipe[-1])
            else:first_epoch=0
            for epoch in range(first_epoch,HORIZON//3+1):
                soil,event=request(python,rawpath,raw,seed,k,private,epoch,old);requests.append(event)
                newpatch=h40.terrain(soil,seed);recipe.append(newpatch.tolist())
                dz=None;closest=None;first=None
                if epoch==0:body,ground=setup(cid,newpatch)
                else:
                    before=h40.native(cid,body);force,dist=h40.get_contact(cid,body,ground)
                    require(force>0 and dist>=-.05 and all(2.<x<98. for x in before[:2]),"prior support/patch")
                    dz=h40.height(newpatch,*before[:2])-h40.height(patch,*before[:2])
                    ground=replace(cid,body,ground,newpatch)
                    require(np.array_equal(before,h40.native(cid,body)) and p.getNumBodies(physicsClientId=cid)==2 and p.getDynamicsInfo(body,-1,physicsClientId=cid)[0]==c.BODY_MASS,"body identity")
                    closest=min([float(q[8]) for q in p.getClosestPoints(body,ground,distance=2.,physicsClientId=cid)],default=2.)
                    require(closest>=-.05,"initial penetration")
                    if k:
                        require(float(soil.attrs["exported_soil_kg"])>float(old.attrs["exported_soil_kg"]) and not np.array_equal(soil.soil_mass_kg.values,old.soil_mass_kg.values),"active erosion stopped")
                        if epoch<=2:require(dz<-.003 and closest>.001,"H40 early lowering")
                    else:require(dz==0. and abs(closest)<.05 and float(soil.attrs["exported_soil_kg"])==0. and np.array_equal(soil.soil_mass_kg.values,old.soil_mass_kg.values),"K0 changed")
                patch=newpatch
                rayz=h40.height(patch,70.,70.);hit=p.rayTest([70.,70.,rayz+10],[70.,70.,rayz-10],physicsClientId=cid)[0]
                require(hit[0]==ground and abs(hit[3][2]-rayz)<.001,"terrain ray")
                worst=0.
                for j in range(BLOCK):
                    p.stepSimulation(physicsClientId=cid);state=h40.native(cid,body)
                    require(np.isfinite(state).all() and all(2.<x<98. for x in state[:2]),"live body left patch or invalid")
                    trace.extend(state.tobytes())
                    force,dist=h40.get_contact(cid,body,ground);worst=min(worst,dist)
                    require(worst>=-.05,"penetration bound")
                    if j==0 and epoch:
                        first={"force":force,"dvz":float(state[5]-before[5])}
                        if closest>.001:require(force==0. and -.055<first["dvz"]<-.025,"gravity in opened gap")
                require(force>0,"end support")
                joint=make_joint(soil,state,raw,seed,k,epoch);sha=c.hash_owner(joint)
                path=out/f"epoch_{epoch}.nc";joint.to_netcdf(path,engine="scipy")
                back=b.read_owner(path);residual=validate_joint(back,soil,raw,seed,k,epoch)
                require(c.hash_owner(back)==sha,"joint roundtrip")
                rec={"epoch":epoch,"soil_step":3*epoch,"bullet_steps":(epoch+1)*BLOCK,"owner_sha":sha,"soil_sha":c.hash_owner(soil),"history_sha":b.sha_bytes(trace),"contact":[force,dist],"delta":dz,"closest":closest,"first":first,"export_kg":float(soil.attrs["exported_soil_kg"]),"mass_residual_kg":residual,"position":state[:3].tolist()}
                if epoch<=2:
                    require(sha==REF[seed,k][1][epoch],"historical profile owner regression")
                    if epoch==2:require(rec["history_sha"]==REF[seed,k][0],"historical profile history regression")
                epochs.append(rec);print("P0C_EPOCH_JSON "+json.dumps({"seed":seed,"K":k,**rec},sort_keys=True),flush=True)
                if not resume and epoch==MID_EPOCH:save(folder,joint,bytes(trace),recipe,cid,body,ground,seed,k)
                old=soil
            require(len(trace)==7*BLOCK*13*8,"trajectory size")
            if resume:require(all(b.file_sha(folder/name)==meta["files"][name] for name in meta["files"]),"checkpoint modified")
            require([e["to"] for e in requests]==list(range(first_epoch*3,HORIZON+1,3)),"request order")
            return {"seed":seed,"K":k,"epochs":epochs,"requests":requests,"history_sha":b.sha_bytes(trace),"executed_bullet_steps":len(epochs)*BLOCK,"wall_seconds":time.monotonic()-start,"cpu_seconds":time.process_time()-cpu,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"child_peak_rss_kib":resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}
    finally:p.disconnect(physicsClientId=cid)

def main(mode,rawpath,python,checkpoint,results):
    profile.runtime(python);profile.runtime(sys.executable)
    raw=h37.read_raw(rawpath);root=pathlib.Path(checkpoint);out=pathlib.Path(results);out.mkdir(parents=True,exist_ok=False)
    resume=mode=="consume"
    if not resume:root.mkdir(parents=True,exist_ok=False)
    else:refs=json.loads((root/"reference.json").read_text())
    records={};fail=[]
    for seed in h40.SEEDS:
        for k in (0.,.1):
            key=f"{seed}_{k}";target=out/key;target.mkdir()
            try:
                rec=run(rawpath,python,raw[seed],seed,k,root/key,target,resume)
                if resume:
                    ref=refs[key]
                    require(rec["history_sha"]==ref["history_sha"] and rec["epochs"]==ref["epochs"][MID_EPOCH+1:] and rec["requests"]==ref["requests"][MID_EPOCH+1:],"extended restart differs")
                    require(rec["executed_bullet_steps"]==2160,"unexpected replay")
                records[key]=rec
            except Exception as e:
                fail.append(key+": "+str(e));records[key]={"error":str(e)}
                print("P0C_FAILURE_JSON "+json.dumps({"case":key,"error":str(e)}),flush=True)
    if not resume and not fail:
        for seed in h40.SEEDS:
            if records[f"{seed}_0.0"]["epochs"][0]["history_sha"]!=records[f"{seed}_0.1"]["epochs"][0]["history_sha"]:fail.append(f"{seed}: initial prefix differs")
        if not fail:b.dump(root/"reference.json",records)
    data={"experiment":"P0-C","mode":mode,"cases":records,"failed_preregistered_gates":fail}
    b.dump(out/"result.json",data);print("WORLD_EVAL_JSON "+json.dumps(data,sort_keys=True,default=h37.np_scalar),flush=True)
    if fail:raise AssertionError(str(fail))
if __name__=="__main__":main(*sys.argv[1:])
