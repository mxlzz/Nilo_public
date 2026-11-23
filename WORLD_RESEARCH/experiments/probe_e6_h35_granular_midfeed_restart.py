"""E6 H35: cross-process mid-feed continuation of ORIGINAL H26 granular world.

This instrument reuses native PyBullet only and original H26's seed/physics/
feed rules. Records source queue, released material IDs and Bullet solver state.
Preregistered before code: ETAPA_6_H35_PROTOCOLO_RESTART_FUENTE_GRANULAR.md.
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

import probe_e3_h24_granular_pile as h24
import probe_e3_h26_gravity_feed as h26

MID=1200
SEED=h24.SEED1
ORIGINAL_SHA="ac1dd51b214ede889328a672237a07a850ba7e183b0fa4ed4ffbf73b4e223697"
VARS=("material_mass_kg","radius_m","released_source_id",
      "release_step","pending_source_id","position_m",
      "velocity_mps","angular_velocity_rad_s","orientation_xyzw")
MOTION=("position_m","velocity_mps","angular_velocity_rad_s","orientation_xyzw")
N=h26.N
R=h26.R
M=h26.M
DT=h26.DT
ATTR_FIXED={"schema_version":1,"seed":SEED,"grain_count":N,
            "grain_radius_m":R,"grain_mass_kg":M,
            "source_radius_m":h26.OUTLET_RADIUS,
            "outlet_z_m":h26.OUTLET_Z,"feed_check_every":h26.CHECK_EVERY,
            "feed_lookahead":h26.LOOKAHEAD,
            "spawn_separation_m":h26.MIN_SPAWN_SEPARATION,
            "physics":"H26 PyBullet ACTIVE friction with open ground"}
UNITS={"material_mass_kg":"kg","radius_m":"m","released_source_id":"1",
       "release_step":"step","pending_source_id":"1","position_m":"m",
       "velocity_mps":"m/s","angular_velocity_rad_s":"rad/s",
       "orientation_xyzw":"1"}

def source_positions():
    return {int(i):np.asarray(pos,dtype=np.float64)
            for i,pos in h26.feed_plan(SEED)}

def setup():
    cid=p.connect(p.DIRECT)
    if cid<0:
        raise RuntimeError("Native Bullet DIRECT unavailable")
    p.setPhysicsEngineParameter(fixedTimeStep=DT,numSolverIterations=60,
       deterministicOverlappingPairs=1,physicsClientId=cid)
    p.setGravity(0,0,h26.GRAVITY,physicsClientId=cid)
    floor_shape=p.createCollisionShape(p.GEOM_PLANE,planeNormal=[0,0,1],
                                       physicsClientId=cid)
    floor=p.createMultiBody(baseMass=0,baseCollisionShapeIndex=floor_shape,
                            physicsClientId=cid)
    p.changeDynamics(floor,-1,lateralFriction=h24.ACTIVE[0],
                     restitution=0.,physicsClientId=cid)
    shape=p.createCollisionShape(p.GEOM_SPHERE,radius=R,physicsClientId=cid)
    return {"cid":cid,"floor":floor,"shape":shape,
            "ids":[],"plan":h26.feed_plan(SEED),"release":[],
            "last_release":None,"max_ledger_error_kg":0.,"samples":{}}

def add_grain(state,source_id,pos):
    cid=state["cid"]
    body=p.createMultiBody(baseMass=M,baseCollisionShapeIndex=state["shape"],
                     basePosition=np.asarray(pos).tolist(),physicsClientId=cid)
    slide,roll,spin=h24.ACTIVE
    p.changeDynamics(body,-1,lateralFriction=slide,
       rollingFriction=roll,spinningFriction=spin,restitution=0.,
       linearDamping=.02,angularDamping=.02,physicsClientId=cid)
    state["ids"].append(body)

def step_scene(state,step):
    cid=state["cid"]
    if step%h26.CHECK_EVERY==0 and state["plan"] and state["last_release"] is None:
        selected=None
        for i in range(min(h26.LOOKAHEAD,len(state["plan"]))):
            _source_id,source_pos=state["plan"][i]
            clear=True
            for body in state["ids"]:
                xyz=p.getBasePositionAndOrientation(body,physicsClientId=cid)[0]
                if np.linalg.norm(np.asarray(xyz)-source_pos)<=h26.MIN_SPAWN_SEPARATION:
                    clear=False
                    break
            if clear:
                selected=i
                break
        if selected is not None:
            sid,pos=state["plan"].pop(selected)
            add_grain(state,sid,pos)
            state["release"].append((step,int(sid)))
            if not state["plan"]:
                state["last_release"]=step
    released_kg=float(len(state["ids"])*M)
    source_kg=float((N-len(state["ids"]))*M)
    residual=abs(released_kg+source_kg-N*M)
    state["max_ledger_error_kg"]=max(state["max_ledger_error_kg"],residual)
    if len(state["ids"])+len(state["plan"])!=N or residual>1e-12:
        raise ValueError("A physical grain was created/removed while releasing")
    if state["last_release"] is None and step>=h26.MAX_FEED_STEP:
        raise ValueError("Feed not empty at preregistered end")
    p.stepSimulation(physicsClientId=cid)
    if state["last_release"] is not None:
        offset=step-state["last_release"]
        if offset in h26.SAMPLES_AFTER:
            state["samples"][offset]=h24.collect(state["ids"],cid)
        if offset==h26.POST_RELEASE:
            return True
    return False

def snapshot_owner(state,step):
    k=len(state["ids"])
    if not(0<k<=N):
        raise ValueError("Checkpoint requires at least one emitted grain")
    d={}
    pending=np.full(N,-1,dtype=np.int32)
    source=np.full(N,-1,dtype=np.int32)
    time=np.zeros(N,dtype=np.int32)
    pending[:N-k]=[int(item[0]) for item in state["plan"]]
    source[:k]=[int(sid) for _step,sid in state["release"]]
    time[:k]=[int(st) for st,_sid in state["release"]]
    current=h24.collect(state["ids"],state["cid"])
    for name in MOTION:
        shape=(N,4) if name=="orientation_xyzw" else (N,3)
        a=np.full(shape,np.nan,dtype=np.float64)
        a[:k]=current[name]
        dims=("spawn_rank","quat") if name=="orientation_xyzw" else ("spawn_rank","xyz")
        d[name]=(dims,a,{"units":UNITS[name]})
    d.update({
        "material_mass_kg":(("spawn_rank",),np.full(N,M),{"units":"kg"}),
        "radius_m":(("spawn_rank",),np.full(N,R),{"units":"m"}),
        "released_source_id":(("spawn_rank",),source,{"units":"1"}),
        "release_step":(("spawn_rank",),time,{"units":"step"}),
        "pending_source_id":(("queue_slot",),pending,{"units":"1"}),
    })
    attrs=dict(ATTR_FIXED)
    attrs.update({"step":int(step),"time_s":step*DT,"released_count":int(k),
                  "last_release_step":int(state["last_release"] or -1),
                  "is_feeding":int(state["last_release"] is None)})
    owner=xr.Dataset(d,coords={
        "spawn_rank":np.arange(N,dtype=np.int32),
        "queue_slot":np.arange(N,dtype=np.int32),
        "xyz":["x","y","z"],"quat":["x","y","z","w"],
    },attrs=attrs)
    validate(owner)
    return owner

def validate(ds):
    if set(ds.data_vars)!=set(VARS) or set(ds.attrs)!=set(ATTR_FIXED)|{
        "step","time_s","released_count","last_release_step","is_feeding"}:
        raise ValueError("Unexpected or duplicate material/physical stock")
    if any(ds.attrs.get(k)!=v for k,v in ATTR_FIXED.items()):
        raise ValueError("Scenario or feed parameters corrupted")
    if ds.coords["spawn_rank"].values.tolist()!=list(range(N)) or ds.coords["queue_slot"].values.tolist()!=list(range(N)) or ds.coords["xyz"].values.tolist()!=["x","y","z"] or ds.coords["quat"].values.tolist()!=["x","y","z","w"]:
        raise ValueError("Source/target identities changed")
    dims={
        "material_mass_kg":("spawn_rank",),"radius_m":("spawn_rank",),
        "released_source_id":("spawn_rank",),"release_step":("spawn_rank",),
        "pending_source_id":("queue_slot",),
        "position_m":("spawn_rank","xyz"),
        "velocity_mps":("spawn_rank","xyz"),
        "angular_velocity_rad_s":("spawn_rank","xyz"),
        "orientation_xyzw":("spawn_rank","quat"),
    }
    if any(ds[name].dims!=d or ds[name].attrs.get("units")!=UNITS[name]
           for name,d in dims.items()):
        raise ValueError("Wrong fields units or axis topology")
    if (not np.array_equal(ds["material_mass_kg"].values,np.full(N,M))
        or not np.array_equal(ds["radius_m"].values,np.full(N,R))):
        raise ValueError("Mass or geometry created/destroyed")
    k=int(ds.attrs["released_count"])
    step=int(ds.attrs["step"])
    if not(0<=k<=N and MID<=step<=h26.MAX_STEPS and ds.attrs["time_s"]==step*DT):
        raise ValueError("Feed progress corrupted")
    src=ds["released_source_id"].values
    times=ds["release_step"].values
    pending=ds["pending_source_id"].values
    if (not np.array_equal(src[k:],np.full(N-k,-1)) or
        not np.array_equal(times[k:],np.zeros(N-k,dtype=int)) or
        not np.array_equal(pending[N-k:],np.full(k,-1))):
        raise ValueError("A pending/source sentinel was replaced")
    released=[int(x) for x in src[:k]]
    queue=[int(x) for x in pending[:N-k]]
    if len(set(released+queue))!=N or set(released+queue)!=set(range(N)):
        raise ValueError("Source identities were lost or duplicated")
    expected=[i for i,_pos in h26.feed_plan(SEED) if i not in set(released)]
    if queue!=expected:
        raise ValueError("Pending source queue order mutated")
    if np.any(times[:k]<=0) or np.any(times[:k]>step) or (
            k>1 and np.any(np.diff(times[:k])<0)):
        raise ValueError("Release history not monotonic or within time")
    last=int(ds.attrs["last_release_step"])
    if k==N:
        if ds.attrs["is_feeding"]!=0 or last!=int(times[k-1]):
            raise ValueError("Source emptied but feed status invalid")
    elif last!=-1 or ds.attrs["is_feeding"]!=1:
        raise ValueError("Early source completion claimed")
    material=float(ds["material_mass_kg"].values.sum())
    if material!=N*M or abs(k*M+(N-k)*M-material)>1e-12:
        raise ValueError("Mass balance source+released failed")
    for name in MOTION:
        v=ds[name].values
        if not np.isfinite(v[:k]).all() or not np.isnan(v[k:]).all():
            raise ValueError("Live pose invalid or phantom pose for pending source")
    q=ds["orientation_xyzw"].values[:k]
    if k and np.max(np.abs(np.linalg.norm(q,axis=1)-1.))>1e-4:
        raise ValueError("Live quaternion invalid")
    pos=ds["position_m"].values[:k]
    if k and np.min(pos[:,2])<R-.02:
        raise ValueError("Live grain under floor")
    if k>1:
        dist=np.linalg.norm(pos[:,None,:]-pos[None,:,:],axis=2)
        np.fill_diagonal(dist,np.inf)
        if np.min(dist)<2*R-.02:
            raise ValueError("Grains overlap beyond contact tolerance")
    return {"released":k,"source":N-k,"inventory_kg":material,
            "source_kg":(N-k)*M,"live_kg":k*M}

def hash_owner(owner):
    h=hashlib.sha256()
    for name in VARS:
        a=owner[name]
        h.update(name.encode()+a.values.tobytes()+a.attrs["units"].encode())
    h.update(json.dumps({k:(v.item() if isinstance(v,np.generic) else v)
                         for k,v in owner.attrs.items()},sort_keys=True).encode())
    for key in ("spawn_rank","queue_slot","xyz","quat"):
        h.update(repr(owner.coords[key].values.tolist()).encode())
    return h.hexdigest()

def h26_final_owner(state,step):
    # Preserve ORIGINAL H26's meaning of grain identity: BODY RELEASE ORDER.
    h24.STEPS=step
    owner=h24.owner_for(SEED,True,True)
    end=state["samples"][h26.POST_RELEASE]
    for name in MOTION:
        np.copyto(owner[name].values,end[name])
    owner.attrs["time_s"]=step*DT
    h24.check(owner,SEED,True,True)
    return owner

def check_pile(state):
    ids=state["ids"]
    size,grain,floor=h24.contact_sizes(
        p.getContactPoints(physicsClientId=state["cid"]),ids,state["floor"])
    end=state["samples"][1800]
    before=state["samples"][1200]
    pos=end["position_m"]
    motion=np.linalg.norm(pos-before["position_m"],axis=1)
    speed=np.linalg.norm(end["velocity_mps"],axis=1)
    return {
        "height_m":float(np.max(pos[:,2]+R)),
        "grains_above_0_26m":int(np.count_nonzero(pos[:,2]>.26)),
        "largest_force_contact_component":int(size),
        "grain_positive_contacts":int(grain),
        "floor_positive_contacts":int(floor),
        "median_late_displacement_m":float(np.median(motion)),
        "p90_speed_m_s":float(np.quantile(speed,.9)),
    }

def run_to_end(state,begin_step):
    end_step=None
    for step in range(begin_step,h26.MAX_STEPS+1):
        if step_scene(state,step):
            end_step=step
            break
    if end_step is None or len(state["ids"])!=N:
        raise ValueError("H26 source never completed or no valid rest window")
    if set(state["samples"])!=set(h26.SAMPLES_AFTER):
        raise ValueError("Required H26 post-release samples missing")
    return end_step

def bad_states(owner):
    key=hash_owner(owner)
    errors={}
    def reject(name,mutate):
        candidate=owner.copy(deep=True)
        mutate(candidate)
        try:validate(candidate)
        except ValueError:errors[name]=True
        else:raise AssertionError("Invalid source owner accepted: "+name)
        if hash_owner(owner)!=key:
            raise AssertionError("Corrupted authoritative H35 owner")
    k=int(owner.attrs["released_count"])
    reject("invented_material",lambda d:d["material_mass_kg"].values.__setitem__(0,M+1))
    reject("negative_material",lambda d:d["material_mass_kg"].values.__setitem__(0,-.02))
    reject("unit_cm",lambda d:d["position_m"].attrs.__setitem__("units","cm"))
    reject("duplicate_released_source_id",lambda d:d["released_source_id"].values.__setitem__(1,d["released_source_id"].values[0]))
    reject("changed_source_queue",lambda d:d["pending_source_id"].values.__setitem__(0,d["released_source_id"].values[0]))
    reject("changed_released_count",lambda d:d.attrs.__setitem__("released_count",k-1))
    reject("phantom_pending_pose",lambda d:d["position_m"].values.__setitem__((k,0),1.))
    reject("invalid_live_quaternion",lambda d:d["orientation_xyzw"].values.__setitem__((0,3),2.))
    reject("clock_corrupted",lambda d:d.attrs.__setitem__("step",MID+1))
    reject("second_mass_stock",lambda d:d.__setitem__("extra_mass",xr.DataArray(np.zeros(N),dims=("spawn_rank",))))
    return errors

def producer(folder):
    out=pathlib.Path(folder);out.mkdir(parents=True,exist_ok=True)
    reference=h26.main_scene(SEED,True)
    if reference["owner_sha"]!=ORIGINAL_SHA or reference["total_step"]!=3688:
        raise AssertionError("Unmodified upstream H26 original baseline differs from published result")
    state=setup()
    try:
        for step in range(1,MID+1):
            if step_scene(state,step):
                raise ValueError("Unexpected completion before midpoint")
        checkpoint=snapshot_owner(state,MID)
        stats=validate(checkpoint)
        if not(0<stats["released"]<N):
            raise AssertionError("Mid-feed checkpoint not between empty and full")
        mid=out/"owner_midfeed_step1200.nc"
        checkpoint.to_netcdf(mid,engine="scipy")
        with xr.open_dataset(mid,engine="scipy") as f:
            back=f.load()
        validate(back)
        if hash_owner(back)!=hash_owner(checkpoint):
            raise AssertionError("NetCDF checkpoint owner hash changed")
        cache=out/"native_midfeed_step1200.bullet"
        p.saveBullet(str(cache),physicsClientId=state["cid"])
        if not cache.exists() or cache.stat().st_size<100:
            raise ValueError("Native Bullet mid-feed solver cache missing")
        mid_contacts=h24.contact_sizes(p.getContactPoints(physicsClientId=state["cid"]),
                                state["ids"],state["floor"])
        rejected=bad_states(checkpoint)
        end_step=run_to_end(state,MID+1)
        final_h26=h26_final_owner(state,end_step)
        final_h35=snapshot_owner(state,end_step)
        final_metrics=check_pile(state)
    finally:
        p.disconnect(physicsClientId=state["cid"])
    expected_release=reference["release"]
    if (state["release"]!=expected_release or
        h24.state_sha(final_h26)!=reference["owner_sha"] or
        any(not np.array_equal(state["samples"][t][name],reference["snapshots"][t][name])
            for t in h26.SAMPLES_AFTER for name in MOTION)):
        print("WORLD_EVAL_JSON "+json.dumps({
            "experiment":"H35 producer","failed_preregistered_gates":["original_H26_trajectory_not_reproduced"],
            "reference_SHA":reference["owner_sha"],
            "instrumented_SHA":h24.state_sha(final_h26),
            "same_release_sequence":state["release"]==expected_release
        },sort_keys=True),flush=True)
        raise AssertionError("H35 recorder changed original H26 dynamics")
    end=out/"owner_h26_final.nc"
    final_h26.to_netcdf(end,engine="scipy")
    with xr.open_dataset(end,engine="scipy") as f:
        loaded=f.load()
    h24.STEPS=end_step
    h24.check(loaded,SEED,True,True)
    if h24.state_sha(loaded)!=ORIGINAL_SHA:
        raise ValueError("Original H26 final state NetCDF invalid")
    current=out/"owner_with_source_ids_final.nc"
    final_h35.to_netcdf(current,engine="scipy")
    with xr.open_dataset(current,engine="scipy") as f:
        again=f.load()
    if hash_owner(again)!=hash_owner(final_h35):
        raise ValueError("Final H35 source/kinematic owner not preserved")
    manifest={
        "experiment":"E6 H35 producer with full source and Bullet cache mid-feed",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "seed":SEED,"checkpoint_step":MID,
        "mid_source_grains":stats["source"],
        "mid_live_grains":stats["released"],
        "mid_inventory_kg":stats["inventory_kg"],
        "checkpoint_owner_sha256":hash_owner(checkpoint),
        "checkpoint_bullet_sha256":hashlib.sha256(cache.read_bytes()).hexdigest(),
        "checkpoint_bullet_bytes":cache.stat().st_size,
        "mid_force_contact_size":int(mid_contacts[0]),
        "expected_final_step":end_step,
        "expected_last_release_step":int(state["last_release"]),
        "expected_H26_sha256":ORIGINAL_SHA,
        "expected_H35_sha256":hash_owner(final_h35),
        "reference_release_sha256":reference["release_sequence_sha"],
        "release_sequence_sha256":hashlib.sha256(np.asarray(state["release"],dtype=np.int64).tobytes()).hexdigest(),
        "max_source_plus_bodies_mass_residual_kg":state["max_ledger_error_kg"],
        "final_pile":final_metrics,"rejected_checkpoint_candidates":rejected,
        "failed_preregistered_gates":[]
    }
    if manifest["reference_release_sha256"]!=manifest["release_sequence_sha256"]:
        raise AssertionError("H26 identity release ledger not consistent")
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("WORLD_EVAL_JSON "+json.dumps(manifest,sort_keys=True),flush=True)

def consumer(folder):
    out=pathlib.Path(folder)
    manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    with xr.open_dataset(out/"owner_midfeed_step1200.nc",engine="scipy") as f:
        mid=f.load()
    with xr.open_dataset(out/"owner_h26_final.nc",engine="scipy") as f:
        expected_h26=f.load()
    with xr.open_dataset(out/"owner_with_source_ids_final.nc",engine="scipy") as f:
        expected_h35=f.load()
    validate(mid)
    validate(expected_h35)
    if hash_owner(mid)!=manifest["checkpoint_owner_sha256"]:
        raise ValueError("H35 midpoint owner SHA changed")
    cached=(out/"native_midfeed_step1200.bullet").read_bytes()
    if len(cached)!=manifest["checkpoint_bullet_bytes"] or hashlib.sha256(cached).hexdigest()!=manifest["checkpoint_bullet_sha256"]:
        raise ValueError("Native Bullet cache corrupted before restore")
    corrupt=bytearray(cached)
    corrupt[-1]^=1
    if hashlib.sha256(corrupt).hexdigest()==manifest["checkpoint_bullet_sha256"]:
        raise ValueError("Invalid native cache passed digest control")
    count=int(mid.attrs["released_count"])
    source=source_positions()
    state=setup()
    state["plan"]=[(int(sid),source[int(sid)]) for sid in
                   mid["pending_source_id"].values[:N-count]]
    state["release"]=[(int(st),int(sid)) for st,sid in zip(
        mid["release_step"].values[:count],
        mid["released_source_id"].values[:count])]
    state["last_release"]=None
    try:
        for _step,sid in state["release"]:
            add_grain(state,sid,source[sid])
        if len(state["ids"])!=count:
            raise ValueError("Restored body ID count mismatch")
        try:
            p.restoreState(fileName=str(out/"native_midfeed_step1200.bullet"),
                           physicsClientId=state["cid"])
        except Exception as ex:
            print("WORLD_EVAL_JSON "+json.dumps({
                "experiment":"E6 H35","failed_preregistered_gates":["native_midfeed_restore_exception"],
                "error_type":type(ex).__name__,"message":str(ex),
                "released_grains":count
            },sort_keys=True),flush=True)
            raise
        restored=h24.collect(state["ids"],state["cid"])
        restore_identical=all(np.array_equal(
            restored[name],mid[name].values[:count]) for name in MOTION)
        if not restore_identical:
            print("WORLD_EVAL_JSON "+json.dumps({
                "experiment":"E6 H35","failed_preregistered_gates":["not_bit_exact_midfeed_restore"],
                "restored_grains":count
            },sort_keys=True),flush=True)
            raise AssertionError("Native Bullet mid-feed cache not restored exactly")
        end_step=run_to_end(state,MID+1)
        final_h26=h26_final_owner(state,end_step)
        final_h35=snapshot_owner(state,end_step)
        final_metrics=check_pile(state)
    finally:
        p.disconnect(physicsClientId=state["cid"])

    failed=[]
    def gate(name,ok):
        if not ok:failed.append(name)
    same_order=(manifest["release_sequence_sha256"]==
           hashlib.sha256(np.asarray(state["release"],dtype=np.int64).tobytes()).hexdigest())
    gate("restore_midpoint_native_bit_exact",restore_identical)
    gate("feed_history_bit_exact",same_order and
         int(state["last_release"])==manifest["expected_last_release_step"])
    gate("expected_step_exact",end_step==manifest["expected_final_step"]==3688)
    gate("same_material_ledger",state["max_ledger_error_kg"]<1e-12)
    gate("same_final_original_H26",h24.state_sha(final_h26)==ORIGINAL_SHA and
         all(np.array_equal(final_h26[name].values,expected_h26[name].values)
             for name in h24.state_sha.__globals__.get("FIELDS",())
             if name in expected_h26.data_vars))
    gate("same_final_extended_owner",hash_owner(final_h35)==manifest["expected_H35_sha256"]
         and all(np.array_equal(final_h35[name].values,expected_h35[name].values,
                                equal_nan=True) for name in MOTION))
    gate("physical_pile_still_supported",final_metrics["height_m"]>.36 and
         final_metrics["grains_above_0_26m"]>=30 and
         final_metrics["largest_force_contact_component"]>=45 and
         final_metrics["grain_positive_contacts"]>0 and
         final_metrics["floor_positive_contacts"]>0 and
         final_metrics["median_late_displacement_m"]<.025 and
         final_metrics["p90_speed_m_s"]<.08)
    gate("source_identity_partition_valid",validate(final_h35)["source"]==0
         and validate(final_h35)["released"]==125)
    report={
        "experiment":"E6 H35 full mid-feed source+contact restart in a new runner",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "checkpoint_step":MID,"resume_started_step":MID+1,
        "restarted_live_grains":count,"restarted_source_grains":N-count,
        "ended_step":end_step,"last_release_step":int(state["last_release"]),
        "native_solver_cache_bytes":len(cached),
        "native_cache_corruption_rejected":True,
        "midpoint_restore_bit_identical":restore_identical,
        "release_order_exact":same_order,
        "final_h26_SHA256":h24.state_sha(final_h26),
        "final_h35_SHA256":hash_owner(final_h35),
        "expected_H26_SHA256":ORIGINAL_SHA,
        "final_pile":final_metrics,
        "max_source_ledger_error_kg":state["max_ledger_error_kg"],
        "failed_preregistered_gates":failed,
        "limitations":"One seed, same Bullet version and CPU runner, source positions regenerated by seed. No common synchronized soil/time or climate; stored .bullet solver cache is not a second material inventory."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if failed:
        raise AssertionError("H35 preregistered mid-feed gates failed: "+", ".join(failed))

if __name__=="__main__":
    if len(sys.argv)!=3 or sys.argv[1] not in ("producer","consumer"):
        raise SystemExit("Usage: producer|consumer folder")
    globals()[sys.argv[1]](sys.argv[2])
