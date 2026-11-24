"""P0-D: source-fed granular matter, live erosion, independent observation and restart."""
import hashlib
import json
import pathlib
import resource
import shutil
import sys
import tempfile
import time
import numpy as np
import pybullet as p
import xarray as xr
import probe_e5_h31_owner_contract as c
import probe_e3_h24_granular_pile as h24
import probe_e3_h26_gravity_feed as h26
import probe_e6_h35_granular_midfeed_restart as h35
import probe_h40_live_body_soil_epochs as h40
import probe_h41_aggregate_transit as h41
import probe_h42_directional_cover as h42
import probe_h37_sequential_bullet_contact as h37
import p0b_joint_restart as b
import p0b_profile_restart as profile
import p0c_extended_world as pc

N,R,M=h26.N,h26.R,h26.M
MID=3
BLOCK=720
EXTRA={"grain_state","grain_mass_kg","grain_radius_m_nominal","source_id","release_step","native_id","grain_reservoir_kg"}
ATTRS={"p0d_seed","p0d_formation_steps","p0d_bullet_steps","p0d_epoch","p0d_plan_sha","p0d_geometry"}
REQ=pc.require

def setup(soil,seed):
    old=h35.SEED
    h35.SEED=h41.GRAIN_SEEDS[seed]
    try:state=h35.setup()
    finally:h35.SEED=old
    cid=state["cid"]
    p.removeBody(state["floor"],physicsClientId=cid)
    patch=h40.terrain(soil,seed)
    ground=h41.make_ground(cid,patch);state["floor"]=ground
    shift=np.array([*h41.CENTER,h40.height(patch,*h41.CENTER)])
    state["plan"]=[(int(i),np.asarray(xyz)+shift) for i,xyz in state["plan"]]
    return state,patch

def replace(state,patch):
    cid=state["cid"];ids=state["ids"]
    before=h41.snap(cid,ids)
    p.removeBody(state["floor"],physicsClientId=cid)
    ground=h41.make_ground(cid,patch);state["floor"]=ground
    for i in ids:p.changeDynamics(i,-1,activationState=p.ACTIVATION_STATE_WAKE_UP,physicsClientId=cid)
    REQ(np.array_equal(before,h41.snap(cid,ids)) and identities(state),"grain identity changed at collider replacement")

def identities(state):
    cid=state["cid"];ids=state["ids"]
    return len(ids)==N and len(set(ids))==N and set(ids)|{state["floor"]}=={p.getBodyUniqueId(j,physicsClientId=cid) for j in range(p.getNumBodies(physicsClientId=cid))} and all(p.getDynamicsInfo(i,-1,physicsClientId=cid)[0]==M for i in ids)

def live_check(state):
    q=h41.snap(state["cid"],state["ids"])
    REQ(np.isfinite(q).all() and np.all((q[:,:2]>2)&(q[:,:2]<98)),"live grain outside patch or invalid pose")
    return q

def integrity(state):
    REQ(identities(state) and h41.valid_bodies(state["cid"],state["ids"],state["floor"],np.full(N,R)),"native grain integrity")

def hash_owner(ds,soil):
    h=hashlib.sha256(c.hash_owner(soil).encode())
    for name in sorted(EXTRA):
        h.update(name.encode()+ds[name].values.tobytes()+json.dumps(ds[name].attrs,sort_keys=True).encode())
    h.update(json.dumps({key:c.normal(ds.attrs[key]) for key in sorted(ATTRS)},sort_keys=True).encode())
    return h.hexdigest()

def extract_soil(ds):
    soil=ds.drop_vars(list(EXTRA)).drop_dims(["grain","motion"])
    soil.attrs={k:v for k,v in ds.attrs.items() if k not in ATTRS}
    return soil

def validate(ds,soil,raw,seed,k,epoch):
    c.validate(soil,raw,seed,k,max_step=pc.HORIZON)
    REQ(set(ds.data_vars)==c.FIELDS_ALL|EXTRA and set(ds.attrs)==set(soil.attrs)|ATTRS,"owner schema")
    REQ(set(ds.coords)==set(soil.coords)|{"grain","motion"} and np.array_equal(ds.grain.values,np.arange(N)) and np.array_equal(ds.motion.values,np.arange(13)),"owner coordinates")
    REQ(c.hash_owner(extract_soil(ds))==c.hash_owner(soil),"soil/reserved stock changed")
    REQ(ds.attrs["p0d_seed"]==h41.GRAIN_SEEDS[seed] and ds.attrs["p0d_geometry"]=="nominal" and ds.attrs["p0d_epoch"]==epoch and soil.attrs["landlab_step"]==3*epoch,"owner epoch")
    form=int(ds.attrs["p0d_formation_steps"]);steps=int(ds.attrs["p0d_bullet_steps"])
    REQ(0<form<=h26.MAX_STEPS and steps==form+epoch*BLOCK,"mechanical clock")
    REQ(ds.grain_state.dims==("grain","motion") and all(ds[v].dims==("grain",) for v in EXTRA-{"grain_state","grain_reservoir_kg"}) and ds.grain_reservoir_kg.ndim==0,"grain dimensions")
    REQ(ds.grain_mass_kg.attrs=={"units":"kg"} and ds.grain_reservoir_kg.attrs=={"units":"kg"} and ds.grain_radius_m_nominal.attrs=={"units":"m_nominal"},"grain units")
    REQ(np.array_equal(ds.grain_mass_kg.values,np.full(N,M)) and np.array_equal(ds.grain_radius_m_nominal.values,np.full(N,R)) and float(ds.grain_reservoir_kg)==0.,"grain inventory")
    REQ(sorted(ds.source_id.values.tolist())==list(range(N)) and len(set(ds.native_id.values.tolist()))==N,"grain identity")
    rel=ds.release_step.values
    REQ(np.all(rel>0) and np.all(np.diff(rel)>0) and rel[-1]<=form,"release history")
    q=ds.grain_state.values
    REQ(np.isfinite(q).all() and np.all((q[:,:2]>2)&(q[:,:2]<98)) and np.all(np.abs(np.linalg.norm(q[:,6:10],axis=1)-1.)<1e-4),"grain pose")
    total=float(soil.soil_mass_kg.sum())+float(soil.attrs["exported_soil_kg"])+float(soil.body_mass_kg.sum())+float(ds.grain_mass_kg.sum())+float(ds.grain_reservoir_kg)
    REQ(abs(total-(c.MASS0+c.BODY_MASS+N*M))<=.09216,"world material balance")
    return total

def snapshot(soil,state,raw,seed,k,epoch,form,plan_sha):
    ds=soil.copy(deep=True).assign_coords(grain=np.arange(N,dtype=np.int32),motion=np.arange(13,dtype=np.int32))
    ds["grain_state"]=(("grain","motion"),h41.snap(state["cid"],state["ids"]))
    ds["grain_mass_kg"]=(("grain",),np.full(N,M),{"units":"kg"})
    ds["grain_radius_m_nominal"]=(("grain",),np.full(N,R),{"units":"m_nominal"})
    ds["source_id"]=(("grain",),np.asarray([sid for _,sid in state["release"]],dtype=np.int32))
    ds["release_step"]=(("grain",),np.asarray([step for step,_ in state["release"]],dtype=np.int32))
    ds["native_id"]=(("grain",),np.asarray(state["ids"],dtype=np.int32))
    ds["grain_reservoir_kg"]=xr.DataArray(0.,attrs={"units":"kg"})
    ds.attrs.update(p0d_seed=h41.GRAIN_SEEDS[seed],p0d_formation_steps=form,p0d_bullet_steps=form+epoch*BLOCK,p0d_epoch=epoch,p0d_plan_sha=plan_sha,p0d_geometry="nominal")
    validate(ds,soil,raw,seed,k,epoch)
    return ds

def observe(ds,soil,state,patch):
    before=hash_owner(ds,soil);q=h41.snap(state["cid"],state["ids"])
    values=[]
    for _ in range(2):
        obs=h42.Observer(patch)
        try:values.append(obs.measure(ds.grain_state.values[:,:3].copy()))
        finally:obs.close()
    REQ(values[0]==values[1] and not any(values[0]["terrain_hits"]),"observer reproducibility or terrain occlusion")
    REQ(hash_owner(ds,soil)==before and np.array_equal(q,h41.snap(state["cid"],state["ids"])),"observer modified live owner")
    return values[0]

def save(folder,ds,soil,state,recipe,history):
    stage=folder.with_name(folder.name+".staging");stage.mkdir()
    try:
        ds.to_netcdf(stage/"owner.nc",engine="scipy")
        p.saveBullet(str(stage/"native.bullet"),physicsClientId=state["cid"])
        meta={"profile":profile.PROFILE,"owner_sha":hash_owner(ds,soil),"recipe":recipe,
              "history":history,"floor":state["floor"],"files":{name:b.file_sha(stage/name) for name in ("owner.nc","native.bullet")}}
        b.dump(stage/"manifest.json",meta)
        stage.replace(folder)
    finally:
        if stage.exists():shutil.rmtree(stage)

def verify(folder,raw,seed,k):
    meta=json.loads((folder/"manifest.json").read_text());profile.verify_profile(meta)
    for name in ("owner.nc","native.bullet"):REQ(b.file_sha(folder/name)==meta["files"][name],"checkpoint digest "+name)
    ds=b.read_owner(folder/"owner.nc");soil=extract_soil(ds)
    validate(ds,soil,raw,seed,k,MID)
    REQ(hash_owner(ds,soil)==meta["owner_sha"],"checkpoint owner digest")
    recipe=np.asarray(meta["recipe"])
    REQ(recipe.shape==(MID+1,2,2) and np.isfinite(recipe).all() and np.array_equal(recipe[-1],h40.terrain(soil,seed)),"checkpoint recipe")
    REQ(len(meta["history"])==MID+1,"checkpoint trajectory count")
    return meta,ds,soil

def trace_step(h,state,step):
    q=live_check(state)
    h.update(np.asarray([step,len(q)],dtype=np.int64).tobytes())
    h.update(np.asarray([sid for _,sid in state["release"]],dtype=np.int32).tobytes())
    h.update(q.tobytes())

def run(rawpath,python,raw,seed,k,folder,out,soil_refs,resume=False,observer=True):
    start=time.monotonic();state=None;old=None;recipe=[];history=[];epochs=[];requests=[]
    try:
        with tempfile.TemporaryDirectory() as tmp:
            private=pathlib.Path(tmp)
            if resume:
                meta,ds,old=verify(folder,raw,seed,k)
                bad=ds.copy(deep=True);bad.grain_mass_kg.values[0]+=1.
                try:validate(bad,old,raw,seed,k,MID)
                except ValueError:pass
                else:raise ValueError("invented grain accepted")
                with tempfile.TemporaryDirectory() as ct:
                    copy=pathlib.Path(ct)/"corrupt";shutil.copytree(folder,copy)
                    binary=bytearray((copy/"native.bullet").read_bytes());binary[-1]^=1;(copy/"native.bullet").write_bytes(binary)
                    try:verify(copy,raw,seed,k)
                    except ValueError:pass
                    else:raise ValueError("bad cache accepted")
                # Reconstruct initial geometry from raw bedrock + original uniform soil;
                # this is a derived recipe, not execution of the prefix.
                initial=old.copy(deep=True)
                mask=initial.is_core_node.values!=0
                initial.soil_mass_kg.values[:]=np.where(mask,c.MASS0/int(mask.sum()),0.)
                state,patch=setup(initial,seed)
                recipe=meta["recipe"];history=list(meta["history"])
                REQ(np.array_equal(patch,np.asarray(recipe[0])),"initial recipe")
                plan={sid:xyz for sid,xyz in state["plan"]}
                plan_sha=h41.digest(np.asarray([xyz for _,xyz in state["plan"]]))
                REQ(plan_sha==ds.attrs["p0d_plan_sha"],"source recipe")
                state["release"]=list(zip(ds.release_step.values.tolist(),ds.source_id.values.tolist()))
                for _,sid in state["release"]:h35.add_grain(state,sid,plan[sid])
                state["plan"]=[];state["last_release"]=state["release"][-1][0]
                for vertices in recipe[1:]:replace(state,np.asarray(vertices))
                REQ(state["ids"]==ds.native_id.values.tolist() and state["floor"]==meta["floor"],"native recipe IDs")
                p.restoreState(fileName=str(folder/"native.bullet"),physicsClientId=state["cid"])
                REQ(np.array_equal(h41.snap(state["cid"],state["ids"]),ds.grain_state.values),"native restored grain state")
                integrity(state)
                old.to_netcdf(private/"soil_9.nc",engine="scipy")
                form=int(ds.attrs["p0d_formation_steps"]);patch=np.asarray(recipe[-1]);first=MID+1
            else:first=0
            for epoch in range(first,pc.HORIZON//3+1):
                soil,event=pc.request(python,rawpath,raw,seed,k,private,epoch,old);requests.append(event)
                REQ(c.hash_owner(soil)==soil_refs[epoch],"P0-C soil reference mismatch")
                try:pc.request(python,rawpath,raw,seed,k,private,epoch,old)
                except ValueError:pass
                else:raise ValueError("duplicate soil request accepted")
                newpatch=h40.terrain(soil,seed);recipe.append(newpatch.tolist())
                h=hashlib.sha256()
                if epoch==0:
                    state,patch=setup(soil,seed)
                    plan_sha=h41.digest(np.asarray([xyz for _,xyz in state["plan"]]))
                    for step in range(1,h26.MAX_STEPS+1):
                        done=h35.step_scene(state,step);trace_step(h,state,step)
                        if done:break
                    else:raise ValueError("feed timeout")
                    form=step
                    REQ(not state["plan"] and state["max_ledger_error_kg"]<=1e-12,"feed ledger")
                else:
                    integrity(state);replace(state,newpatch);integrity(state)
                    for step in range(1,BLOCK+1):
                        p.stepSimulation(physicsClientId=state["cid"]);trace_step(h,state,form+(epoch-1)*BLOCK+step)
                    if k:REQ(float(soil.attrs["exported_soil_kg"])>float(old.attrs["exported_soil_kg"]) and not np.array_equal(soil.soil_mass_kg.values,old.soil_mass_kg.values),"erosion stopped")
                    else:REQ(float(soil.attrs["exported_soil_kg"])==0. and np.array_equal(soil.soil_mass_kg.values,old.soil_mass_kg.values),"K0 changed")
                patch=newpatch;integrity(state)
                cid=state["cid"];z=h40.height(patch,70.,70.);hit=p.rayTest([70.,70.,z+10],[70.,70.,z-10],physicsClientId=cid)[0]
                REQ(hit[0]==state["floor"] and abs(hit[3][2]-z)<.001,"terrain ray")
                ds=snapshot(soil,state,raw,seed,k,epoch,form,plan_sha)
                sha=hash_owner(ds,soil);history.append(h.hexdigest())
                observation=observe(ds,soil,state,patch) if observer else None
                rec={"epoch":epoch,"steps":form+epoch*BLOCK,"owner_sha":sha,"soil_sha":c.hash_owner(soil),
                     "trace_sha":history[-1],"aggregate":h41.aggregate(cid,state["ids"],state["floor"],patch),"observation":observation}
                if out is not None:
                    path=out/f"epoch_{epoch}.nc";ds.to_netcdf(path,engine="scipy")
                    back=b.read_owner(path);validate(back,soil,raw,seed,k,epoch)
                    REQ(hash_owner(back,soil)==sha,"owner roundtrip")
                epochs.append(rec)
                print("P0D_EPOCH_JSON "+json.dumps({"seed":seed,"K":k,**rec},sort_keys=True),flush=True)
                if not resume and observer and epoch==MID:save(folder,ds,soil,state,recipe,history)
                old=soil
            if resume:REQ(all(b.file_sha(folder/name)==digest for name,digest in meta["files"].items()),"checkpoint changed")
            REQ([e["to"] for e in requests]==list(range(first*3,pc.HORIZON+1,3)),"request order")
            return {"epochs":epochs,"history":history,"formation_steps":form,"new_bullet_steps":sum(BLOCK if e["epoch"] else form for e in epochs),"requests":requests,"wall_seconds":time.monotonic()-start,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"child_peak_rss_kib":resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}
    finally:
        if state is not None:p.disconnect(physicsClientId=state["cid"])

def main(mode,rawpath,python,folder,outdir,reference=None):
    profile.runtime(python);profile.runtime(sys.executable)
    root=pathlib.Path(folder);out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=False)
    raw=h37.read_raw(rawpath);resume=mode=="consume"
    if resume:
        baseline=json.loads((root/"reference.json").read_text());refs=baseline["soil_refs"]
    else:
        root.mkdir(parents=True,exist_ok=False)
        ref=json.loads(pathlib.Path(reference).read_text())
        REQ(not ref["failed_preregistered_gates"] and ref["experiment"]=="P0-C","P0-C reference invalid")
        refs={key:[e["soil_sha"] for e in value["epochs"]] for key,value in ref["cases"].items()}
    records={};fail=[]
    for seed in h40.SEEDS:
        for k in (0.,.1):
            key=f"{seed}_{k}";target=out/key;target.mkdir()
            try:
                rec=run(rawpath,python,raw[seed],seed,k,root/key,target,refs[key],resume)
                if resume:
                    expected=baseline["cases"][key]
                    REQ(rec["history"]==expected["history"] and rec["epochs"]==expected["epochs"][MID+1:] and rec["requests"]==expected["requests"][MID+1:],"granular restart diverged")
                    REQ(rec["new_bullet_steps"]==2160,"unexpected replay")
                records[key]=rec
            except Exception as e:
                fail.append(key+": "+str(e));records[key]={"error":str(e)}
                print("P0D_FAILURE_JSON "+json.dumps({"case":key,"error":str(e)}),flush=True)
    if not resume and not fail:
        for seed in h40.SEEDS:
            if records[f"{seed}_0.0"]["history"][0]!=records[f"{seed}_0.1"]["history"][0]:fail.append(f"{seed}: formation prefix")
        try:
            replay=run(rawpath,python,raw[7321],7321,.1,root/"unused",None,refs["7321_0.1"],False,False)
            expected=records["7321_0.1"]
            REQ(replay["history"]==expected["history"] and [{k:v for k,v in e.items() if k!="observation"} for e in expected["epochs"]]==[{k:v for k,v in e.items() if k!="observation"} for e in replay["epochs"]],"observer affected dynamics")
        except Exception as e:fail.append("observer replay: "+str(e))
        if not fail:b.dump(root/"reference.json",{"soil_refs":refs,"cases":records})
    data={"experiment":"P0-D","mode":mode,"cases":records,"failed_preregistered_gates":fail}
    b.dump(out/"result.json",data)
    print("WORLD_EVAL_JSON "+json.dumps(data,sort_keys=True,default=h37.np_scalar),flush=True)
    if fail:raise AssertionError(str(fail))

if __name__=="__main__":main(*sys.argv[1:])
