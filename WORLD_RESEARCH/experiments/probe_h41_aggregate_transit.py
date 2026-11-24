"""H41: horizontal transit across a gravity-fed aggregate after H40 terrain changes.
See the preregistered H41 protocol. Native Bullet, no custom contact laws.
"""
import hashlib
import json
import pathlib
import sys
import numpy as np
import pybullet as p
import xarray as xr
import probe_h40_live_body_soil_epochs as h40
import probe_h37_sequential_bullet_contact as h37
import probe_e5_h31_owner_contract as c
import probe_e4_h30_worldengine_bullet as mesh
import probe_e3_h24_granular_pile as h24
import probe_e3_h26_gravity_feed as h26
import probe_e6_h35_granular_midfeed_restart as h35

GRAIN_SEEDS={7321:20261122,8128:20261123}
CENTER=np.array([40.,30.])
PROBE_R=.15
PROBE_M=.10
BLOCK=720
TRIAL=1440
STOCK=h26.N*h26.M

def load_soils(rawpath,folder):
    raw=h37.read_raw(rawpath)
    root=pathlib.Path(folder)
    manifest=json.loads((root/"manifest.json").read_text())
    out={}
    for seed in h40.SEEDS:
        for k in (0.,.1):
            name=h37.CASES[(seed,k)]
            states=[]
            for step,tag,key in ((0,"initial","initial_sha256"),(3,"checkpoint","mid_sha256"),(6,"baseline","baseline_sha256")):
                with xr.open_dataset(root/f"{name}_{tag}.nc",engine="scipy") as f:
                    ds=f.load()
                c.validate(ds,raw[seed],seed,k)
                if c.hash_owner(ds)!=manifest["cases"][name][key] or int(ds.attrs["landlab_step"])!=step:
                    raise ValueError("H40 input altered")
                states.append(ds)
            if c.hash_owner(states[-1])!=h40.EXPECTED[(seed,k)]:
                raise ValueError("H37 historical soil changed")
            if k==0 and any(not np.array_equal(s.soil_mass_kg.values,states[0].soil_mass_kg.values) or s.attrs["exported_soil_kg"]!=0. for s in states):
                raise ValueError("K0 changed soil")
            out[seed,k]=states
    return out

def make_ground(cid,patch):
    shape=p.createCollisionShape(p.GEOM_MESH,vertices=mesh.mesh_vertices(patch),
        indices=[0,1,2,0,2,3],flags=p.GEOM_FORCE_CONCAVE_TRIMESH,physicsClientId=cid)
    ground=p.createMultiBody(baseMass=0.,baseCollisionShapeIndex=shape,physicsClientId=cid)
    p.changeDynamics(ground,-1,lateralFriction=.8,restitution=0.,physicsClientId=cid)
    return ground

def snap(cid,ids):
    return np.asarray([h40.native(cid,i) for i in ids],dtype=np.float64).reshape(-1,13)

def digest(*arrays):
    h=hashlib.sha256()
    for a in arrays:
        h.update(np.asarray(a).tobytes())
    return h.hexdigest()

def aggregate(cid,ids,ground,patch):
    if not ids:
        return {"component":0,"high":0,"max_speed":0.}
    q=snap(cid,ids)
    high=sum(row[2]-h40.height(patch,row[0],row[1])>.26 for row in q)
    component,_,_=h24.contact_sizes(p.getContactPoints(physicsClientId=cid),ids,ground)
    return {"component":int(component),"high":int(high),"max_speed":float(np.linalg.norm(q[:,3:6],axis=1).max())}

def valid_bodies(cid,ids,ground,radii):
    if not ids:return True
    q=snap(cid,ids)
    if not np.isfinite(q).all() or not np.all((q[:,:2]>2)&(q[:,:2]<98)):
        return False
    if any(abs(np.linalg.norm(row[6:10])-1.)>1e-4 for row in q):
        return False
    pairs=np.linalg.norm(q[:,None,:3]-q[None,:,:3],axis=2)-radii[:,None]-radii[None,:]
    np.fill_diagonal(pairs,np.inf)
    if np.min(pairs)<-.02:return False
    for i in ids:
        near=p.getClosestPoints(i,ground,distance=.02,physicsClientId=cid)
        if any(float(x[8])<-.02 for x in near):return False
    return True

def owner(soil,grain_state,source_ids,probe_state,mode,steps):
    ds=soil.copy(deep=True)
    live=len(source_ids)
    ds=ds.assign_coords(h41_grain=np.arange(h26.N,dtype=np.int32),h41_motion=np.arange(13,dtype=np.int32))
    state=np.zeros((h26.N,13),dtype=np.float64)
    mass=np.zeros(h26.N,dtype=np.float64)
    if live:
        state[np.asarray(source_ids)]=grain_state
        mass[np.asarray(source_ids)]=h26.M
    ds["h41_grain_state"]=(("h41_grain","h41_motion"),state)
    ds["h41_grain_mass_kg"]=(("h41_grain",),mass,{"units":"kg"})
    ds["h41_probe_state"]=(("h41_motion",),probe_state)
    ds["h41_probe_mass_kg"]=xr.DataArray(PROBE_M,attrs={"units":"kg"})
    ds["h41_grain_reservoir_kg"]=xr.DataArray(float(STOCK-live*h26.M),attrs={"units":"kg"})
    ds.attrs.update(h41_mode=mode,h41_bullet_steps=int(steps),h41_geometry_units="nominal")
    validate_owner(ds,soil,mode,steps)
    return ds

def validate_owner(ds,soil,mode,steps):
    extra={"h41_grain_state","h41_grain_mass_kg","h41_probe_state","h41_probe_mass_kg","h41_grain_reservoir_kg"}
    if set(ds.data_vars)!=set(soil.data_vars)|extra:raise ValueError("Stock schema")
    for k in soil.variables:
        if not ds[k].identical(soil[k]):raise ValueError("H40 soil or reserved body modified")
    attrs=dict(soil.attrs)
    attrs.update(h41_mode=mode,h41_bullet_steps=int(steps),h41_geometry_units="nominal")
    if dict(ds.attrs)!=attrs:raise ValueError("Clock or mode")
    expected=np.full(h26.N,h26.M if mode!="terrain" else 0.)
    if not np.array_equal(ds.h41_grain_mass_kg.values,expected):raise ValueError("Grain mass")
    if abs(float(ds.h41_grain_mass_kg.sum())+float(ds.h41_grain_reservoir_kg)-STOCK)>1e-12:raise ValueError("Grain source ledger")
    if float(ds.h41_probe_mass_kg)!=PROBE_M:raise ValueError("Probe mass")
    if not np.isfinite(ds.h41_grain_state.values).all() or not np.isfinite(ds.h41_probe_state.values).all():raise ValueError("Kinematics")
    if mode=="terrain" and np.any(ds.h41_grain_state.values):raise ValueError("Reservoir poses")

def owner_hash(ds,soil):
    return digest(np.frombuffer(c.hash_owner(soil).encode(),dtype=np.uint8),ds.h41_grain_mass_kg.values,
        ds.h41_grain_state.values,ds.h41_probe_state.values,ds.h41_probe_mass_kg.values,
        ds.h41_grain_reservoir_kg.values,np.frombuffer(str(ds.attrs["h41_bullet_steps"]).encode(),dtype=np.uint8))

def run(soils,seed,k,mode,matched_steps=None):
    fail=[]
    def gate(name,ok):
        if not ok:fail.append(name)
    old_seed,old_friction=h35.SEED,h24.ACTIVE
    h35.SEED=GRAIN_SEEDS[seed]
    h24.ACTIVE=old_friction if mode=="active" else h24.NO_FRICTION
    state=None
    try:
        state=h35.setup()
        cid=state["cid"]
        p.removeBody(state["floor"],physicsClientId=cid)
        patch=h40.terrain(soils[0],seed)
        ground=make_ground(cid,patch)
        state["floor"]=ground
        shift=np.array([*CENTER,h40.height(patch,*CENTER)])
        state["plan"]=[(i,xyz+shift) for i,xyz in state["plan"]]
        plan_hash=digest(np.asarray([v for _,v in state["plan"]]))
        if mode!="terrain":
            for step in range(1,h26.MAX_STEPS+1):
                if h35.step_scene(state,step):break
            else:raise ValueError("Feed timeout")
            gate("all_grains_released",len(state["ids"])==h26.N and not state["plan"])
        else:
            step=int(matched_steps)
            for _ in range(step):p.stepSimulation(physicsClientId=cid)
        formation_steps=step
        ids=state["ids"]
        source_ids=[sid for _,sid in state["release"]]
        gate("unique_source_ids",sorted(source_ids)==(list(range(h26.N)) if mode!="terrain" else []))
        prefix=digest(snap(cid,ids))
        gate("formation_integrity",valid_bodies(cid,ids,ground,np.full(len(ids),h26.R)))
        events=[]
        for epoch,soil in enumerate(soils[1:],start=1):
            before=snap(cid,ids)
            masses=[p.getDynamicsInfo(i,-1,physicsClientId=cid)[0] for i in ids]
            new_patch=h40.terrain(soil,seed)
            dz=h40.height(new_patch,*CENTER)-h40.height(patch,*CENTER)
            p.removeBody(ground,physicsClientId=cid)
            ground=make_ground(cid,new_patch)
            state["floor"]=ground
            for i in ids:
                p.changeDynamics(i,-1,activationState=p.ACTIVATION_STATE_WAKE_UP,physicsClientId=cid)
            after=snap(cid,ids)
            same=np.array_equal(before,after) and masses==[p.getDynamicsInfo(i,-1,physicsClientId=cid)[0] for i in ids] and set(ids)|{ground}=={p.getBodyUniqueId(j,physicsClientId=cid) for j in range(p.getNumBodies(physicsClientId=cid))}
            gate(f"epoch{epoch}_same_bodies",same)
            gate(f"epoch{epoch}_initial_integrity",valid_bodies(cid,ids,ground,np.full(len(ids),h26.R)))
            for _ in range(BLOCK):p.stepSimulation(physicsClientId=cid)
            patch=new_patch
            gate(f"epoch{epoch}_final_integrity",valid_bodies(cid,ids,ground,np.full(len(ids),h26.R)))
            events.append({"epoch":epoch,"terrain_delta":dz,"same_bodies":bool(same),"aggregate":aggregate(cid,ids,ground,patch)})
        prior=aggregate(cid,ids,ground,patch)
        start=np.array([38.5,30.,h40.height(patch,38.5,30.)+.17])
        grains=snap(cid,ids)
        gate("probe_start_clear",not ids or np.min(np.linalg.norm(grains[:,:3]-start,axis=1))>h26.R+PROBE_R)
        shape=p.createCollisionShape(p.GEOM_SPHERE,radius=PROBE_R,physicsClientId=cid)
        probe=p.createMultiBody(PROBE_M,shape,basePosition=start.tolist(),physicsClientId=cid)
        p.changeDynamics(probe,-1,lateralFriction=.8,restitution=0.,linearDamping=.02,angularDamping=.02,physicsClientId=cid)
        p.resetBaseVelocity(probe,linearVelocity=[2.,0.,0.],angularVelocity=[0.,0.,0.],physicsClientId=cid)
        history=hashlib.sha256()
        first_contact=None
        crossing=None
        max_x=float(start[0])
        for j in range(1,TRIAL+1):
            p.stepSimulation(physicsClientId=cid)
            q=h40.native(cid,probe)
            history.update(q.tobytes())
            max_x=max(max_x,float(q[0]))
            if first_contact is None and any(x[2] in ids and x[9]>1e-5 for x in p.getContactPoints(bodyA=probe,physicsClientId=cid)):
                first_contact=j
            if crossing is None and q[0]>=41.5:crossing=j
        final=aggregate(cid,ids,ground,patch)
        gate("final_integrity",valid_bodies(cid,ids+[probe],ground,np.r_[np.full(len(ids),h26.R),PROBE_R]))
        gate("live_mass",all(p.getDynamicsInfo(i,-1,physicsClientId=cid)[0]==h26.M for i in ids) and p.getDynamicsInfo(probe,-1,physicsClientId=cid)[0]==PROBE_M)
        total_steps=formation_steps+2*BLOCK+TRIAL
        ds=owner(soils[-1],snap(cid,ids),source_ids,h40.native(cid,probe),mode,total_steps)
        return {"seed":seed,"K":k,"mode":mode,"formation_steps":formation_steps,"source_plan_hash":plan_hash,"prefix_sha":prefix,
            "events":events,"before_probe":prior,"after_probe":final,"first_grain_contact":first_contact,"first_crossing":crossing,"max_x":max_x,
            "history_sha":history.hexdigest(),"owner_sha":owner_hash(ds,soils[-1]),"failed":fail,"owner":ds}
    finally:
        h35.SEED=old_seed
        h24.ACTIVE=old_friction
        if state is not None:p.disconnect(physicsClientId=state["cid"])

def main(rawpath,folder,outdir):
    soils=load_soils(rawpath,folder)
    out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=True)
    cases={}
    failed=[]
    def gate(name,ok):
        if not ok:failed.append(name)
    for (seed,k),states in soils.items():
        for mode in ("active","ablated","terrain"):
            matched=cases[(seed,k,"active")]["formation_steps"] if mode=="terrain" else None
            case=run(states,seed,k,mode,matched)
            cases[seed,k,mode]=case
            key=f"{seed}_{k}_{mode}"
            failed.extend(key+"_"+v for v in case["failed"])
            ds=case["owner"]
            path=out/(key+".nc")
            ds.to_netcdf(path,engine="scipy")
            with xr.open_dataset(path,engine="scipy") as f:back=f.load()
            steps=int(ds.attrs["h41_bullet_steps"])
            validate_owner(back,states[-1],mode,steps)
            gate(key+"_roundtrip",owner_hash(back,states[-1])==case["owner_sha"])
            bad=ds.copy(deep=True)
            bad.h41_grain_mass_kg.values[0]+=1.
            try:validate_owner(bad,states[-1],mode,steps)
            except ValueError:pass
            else:failed.append(key+"_corruption_accepted")
            print("WORLD_CASE_JSON "+json.dumps({a:b for a,b in case.items() if a!="owner"},sort_keys=True),flush=True)
        a,b,n=(cases[seed,k,m] for m in ("active","ablated","terrain"))
        gate(f"{seed}_{k}_same_plan",a["source_plan_hash"]==b["source_plan_hash"]==n["source_plan_hash"])
        gate(f"{seed}_{k}_instrument",n["first_crossing"] is not None and n["first_crossing"]<=720)
        if k:
            gate(f"{seed}_aggregate",a["before_probe"]["component"]>=45 and a["before_probe"]["high"]>=25 and a["after_probe"]["component"]>=45)
            first=a["first_crossing"]
            gate(f"{seed}_contact",a["first_grain_contact"] is not None and (first is None or a["first_grain_contact"]<first))
            controls=[b["first_crossing"],n["first_crossing"]]
            gate(f"{seed}_functional_delay",all(v is not None for v in controls) and (first is None or first>=max(controls)+120))
    for seed in h40.SEEDS:
        for mode in ("active","ablated"):
            gate(f"{seed}_{mode}_same_prefix",cases[seed,0.,mode]["prefix_sha"]==cases[seed,.1,mode]["prefix_sha"])
    replay=run(soils[7321,.1],7321,.1,"active")
    a=cases[7321,.1,"active"]
    gate("replay",all(replay[key]==a[key] for key in a if key!="owner"))
    result={"experiment":"H41","cases":{str(key):{a:b for a,b in value.items() if a!="owner"} for key,value in cases.items()},"failed_preregistered_gates":failed}
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True))
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True),flush=True)
    if failed:raise AssertionError("H41 gates failed: "+str(failed))

if __name__=="__main__":main(*sys.argv[1:])
