"""E7 H36: functional impact response of an untemplated H26 granular heap.

No new contact law, pile geometry, or emergent "barrier" class. Native
PyBullet3.2.7 is run on exactly the same H26 structures, in two seeds and
the no-friction ablation; one identical test sphere is dropped at x=y=0.
Protocol preregistered in ETAPA_7_H36_PROTOCOLO_FUNCION_PILA_IMPACTO.md.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import tempfile
from importlib.metadata import version

import numpy as np
import pybullet as p
import xarray as xr

import probe_e3_h24_granular_pile as h24
import probe_e3_h26_gravity_feed as h26
import probe_e6_h35_granular_midfeed_restart as h35

PROBE_M=.10
PROBE_R=.15
PROBE_INITIAL=np.array([0.,0.,1.6],dtype=np.float64)
N_IMPACT_STEPS=720
SEED1=20261122
SEED2=20261123
REFERENCE={
    (SEED1,True):("ac1dd51b214ede889328a672237a07a850ba7e183b0fa4ed4ffbf73b4e223697",
                  1888,3688,"87cbb189f43aaba194cade2eac5c5c5f34369e9a05fd507ea40a285090aea80c"),
    (SEED2,True):("b364de5794470a7677eed42d5e544fcfbfa0fb282db2dc6cbecf2c651391ab4d",
                  1968,3768,"4d14b3572c89657b69bafe6235213dda2f31ff86743677c5772a267ce6fdb19b"),
    (SEED1,False):("38676dbd23135e9eee45552611b82de05bedbdb7079053d468edc37f42eeacfc",
                   1672,3472,"f529b46ff2f4499acb2feec7f4af339c70afb91a3917a8ae83a23d12cb45e11d"),
}
MOTION=("position_m","velocity_mps","angular_velocity_rad_s","orientation_xyzw")
FIELDS=("material_mass_kg","radius_m","role_code")+MOTION
UNITS={"material_mass_kg":"kg","radius_m":"m","role_code":"1",
       "position_m":"m","velocity_mps":"m/s",
       "angular_velocity_rad_s":"rad/s","orientation_xyzw":"1"}

def combined_owner(grain_snapshot,probe_native,seed,friction,step_h26):
    positions=np.vstack((grain_snapshot["position_m"],
                         np.asarray(probe_native[0],dtype=np.float64)[None,:]))
    linear=np.vstack((grain_snapshot["velocity_mps"],
                      np.asarray(probe_native[2],dtype=np.float64)[None,:]))
    angular=np.vstack((grain_snapshot["angular_velocity_rad_s"],
                       np.asarray(probe_native[3],dtype=np.float64)[None,:]))
    quat=np.vstack((grain_snapshot["orientation_xyzw"],
                    np.asarray(probe_native[1],dtype=np.float64)[None,:]))
    return xr.Dataset({
        "material_mass_kg":(("object",),np.r_[np.full(h26.N,h26.M),PROBE_M],{"units":"kg"}),
        "radius_m":(("object",),np.r_[np.full(h26.N,h26.R),PROBE_R],{"units":"m"}),
        "role_code":(("object",),np.r_[np.zeros(h26.N,dtype=np.int32),1],{"units":"1"}),
        "position_m":(("object","xyz"),positions,{"units":"m"}),
        "velocity_mps":(("object","xyz"),linear,{"units":"m/s"}),
        "angular_velocity_rad_s":(("object","xyz"),angular,{"units":"rad/s"}),
        "orientation_xyzw":(("object","quat"),quat,{"units":"1"}),
    },coords={"object":[f"grain_{i:03d}" for i in range(h26.N)]+["probe"],
              "xyz":["x","y","z"],"quat":["x","y","z","w"]},
    attrs={"schema_version":1,"stage":"impact_complete",
           "seed":int(seed),"friction_on":int(bool(friction)),
           "release_count":h26.N,"h26_final_step":int(step_h26),
           "probe_steps":N_IMPACT_STEPS,
           "total_time_s":(step_h26+N_IMPACT_STEPS)*h26.DT,
           "probe_start_xyz":tuple(PROBE_INITIAL.tolist()),
           "boundary":"open ground, no walls and native Bullet contacts"})
 
def validate(ds,seed,friction,h26_step):
    if set(ds.data_vars)!=set(FIELDS):
        raise ValueError("Second/missing mass inventory")
    if ds.coords["object"].values.tolist()!=[f"grain_{i:03d}" for i in range(h26.N)]+["probe"]:
        raise ValueError("Material identity changed")
    if ds.coords["xyz"].values.tolist()!=["x","y","z"] or ds.coords["quat"].values.tolist()!=["x","y","z","w"]:
        raise ValueError("Geometry axes changed")
    dims={"material_mass_kg":("object",),"radius_m":("object",),
          "role_code":("object",),
          "position_m":("object","xyz"),
          "velocity_mps":("object","xyz"),
          "angular_velocity_rad_s":("object","xyz"),
          "orientation_xyzw":("object","quat")}
    if any(ds[k].dims!=d or ds[k].attrs.get("units")!=UNITS[k]
           for k,d in dims.items()):
        raise ValueError("Unexpected units/dimensions")
    base={"schema_version":1,"stage":"impact_complete",
          "seed":int(seed),"friction_on":int(bool(friction)),
          "release_count":h26.N,"h26_final_step":int(h26_step),
          "probe_steps":N_IMPACT_STEPS,
          "total_time_s":(h26_step+N_IMPACT_STEPS)*h26.DT,
          "probe_start_xyz":tuple(PROBE_INITIAL.tolist()),
          "boundary":"open ground, no walls and native Bullet contacts"}
    if set(ds.attrs)!=set(base) or any(ds.attrs.get(k)!=v for k,v in base.items()):
        raise ValueError("Physical scenario/clock modified")
    m=ds["material_mass_kg"].values
    radii=ds["radius_m"].values
    roles=ds["role_code"].values
    if not np.array_equal(m,np.r_[np.full(h26.N,h26.M),PROBE_M]) or float(m.sum())!=3.225:
        raise ValueError("Material created/destroyed")
    if not np.array_equal(radii,np.r_[np.full(h26.N,h26.R),PROBE_R]) or not np.array_equal(roles,np.r_[np.zeros(h26.N,dtype=np.int32),1]):
        raise ValueError("Body physical role/volume changed")
    for field in MOTION:
        if not np.isfinite(ds[field].values).all():
            raise ValueError("Nonfinite physical state")
    q=ds["orientation_xyzw"].values
    if np.max(np.abs(np.linalg.norm(q,axis=1)-1.))>1e-4:
        raise ValueError("Invalid orientation")
    pos=ds["position_m"].values
    if np.min(pos[:,2]-radii)<-.02:
        raise ValueError("Body penetrated floor")
    sep=np.linalg.norm(pos[:,None,:]-pos[None,:,:],axis=2)
    np.fill_diagonal(sep,np.inf)
    radiisum=radii[:,None]+radii[None,:]
    if np.min(sep-radiisum)<-.02:
        raise ValueError("Nonphysical body overlap")
    return float(m.sum())

def sha(ds):
    h=hashlib.sha256()
    for key in FIELDS:
        a=ds[key]
        h.update(key.encode()+a.values.tobytes()+a.attrs["units"].encode())
    attrs={k:(v.item() if isinstance(v,np.generic) else v) for k,v in ds.attrs.items()}
    h.update(json.dumps(attrs,sort_keys=True).encode())
    for key in ("object","xyz","quat"):
        h.update(repr(ds.coords[key].values.tolist()).encode())
    return h.hexdigest()

def run(seed,friction):
    prior_seed=h35.SEED
    prior_coeff=h24.ACTIVE
    h35.SEED=seed
    h24.ACTIVE=prior_coeff if friction else h24.NO_FRICTION
    state=None
    try:
        state=h35.setup()
        end_step=h35.run_to_end(state,1)
    except:
        if state is not None:
            p.disconnect(physicsClientId=state["cid"])
        raise
    finally:
        h35.SEED=prior_seed
        h24.ACTIVE=prior_coeff

    try:
        h24.STEPS=end_step
        prior=h24.owner_for(seed,friction,True)
        for key in MOTION:
            np.copyto(prior[key].values,state["samples"][1800][key])
        prior.attrs["time_s"]=end_step*h26.DT
        h24.check(prior,seed,friction,True)
        expected_sha,last_release,expected_end,expected_release=REFERENCE[(seed,friction)]
        native_release=hashlib.sha256(np.asarray(state["release"],dtype=np.int64).tobytes()).hexdigest()
        if (h24.state_sha(prior)!=expected_sha or
            state["last_release"]!=last_release or
            end_step!=expected_end or native_release!=expected_release):
            print("WORLD_EVAL_JSON "+json.dumps({
                "experiment":"E7 H36","failed_preregistered_gates":["H26_not_reproduced_before_probe"],
                "seed":seed,"friction":friction,
                "H26_expected_owner_SHA":expected_sha,
                "H26_replayed_owner_SHA":h24.state_sha(prior),
                "release_SHA":native_release
            },sort_keys=True),flush=True)
            raise ValueError("H36 original H26 pre-probe state differs from recorded original")

        cid=state["cid"]
        grain_ids=set(state["ids"])
        points=state["samples"][1800]["position_m"]
        gap=np.min(np.linalg.norm(points-PROBE_INITIAL,axis=1))
        if gap<=h26.R+PROBE_R+.02:
            raise ValueError("Probe initially overlaps existing nonprescribed pile")
        probe_shape=p.createCollisionShape(p.GEOM_SPHERE,radius=PROBE_R,physicsClientId=cid)
        probe=p.createMultiBody(baseMass=PROBE_M,baseCollisionShapeIndex=probe_shape,
                 basePosition=PROBE_INITIAL.tolist(),physicsClientId=cid)
        p.changeDynamics(probe,-1,lateralFriction=.8,restitution=0.,
            linearDamping=.02,angularDamping=.02,physicsClientId=cid)
        events=[]
        peak_grain_force=0.
        max_grain_force_sum=0.
        total_grain_impulse=0.
        early_grain=None
        early_floor=None
        early_any=None
        min_z=float("inf")
        dynamic_history=hashlib.sha256()
        for step in range(1,N_IMPACT_STEPS+1):
            p.stepSimulation(physicsClientId=cid)
            pos,q=p.getBasePositionAndOrientation(probe,physicsClientId=cid)
            linear,omega=p.getBaseVelocity(probe,physicsClientId=cid)
            min_z=min(min_z,float(pos[2]))
            dynamic_history.update(np.asarray([*pos,*q,*linear,*omega],dtype=np.float64).tobytes())
            forces=[]
            for contact in p.getContactPoints(physicsClientId=cid):
                aa,bb=contact[1],contact[2]
                if probe not in (aa,bb) or float(contact[9])<=1e-5:
                    continue
                other=bb if aa==probe else aa
                if other in grain_ids:
                    forces.append(float(contact[9]))
                    if early_grain is None:
                        early_grain={"step":step,"center_z_m":float(pos[2]),"force_N":float(contact[9])}
                elif other==state["floor"] and early_floor is None:
                    early_floor={"step":step,"center_z_m":float(pos[2]),"force_N":float(contact[9])}
                if early_any is None:
                    early_any={"step":step,"center_z_m":float(pos[2]),"kind":"grain" if other in grain_ids else "floor"}
            if forces:
                peak_grain_force=max(peak_grain_force,max(forces))
                max_grain_force_sum=max(max_grain_force_sum,sum(forces))
                total_grain_impulse+=sum(forces)*h26.DT
        grain_state=h24.collect(state["ids"],cid)
        probe_state=(p.getBasePositionAndOrientation(probe,physicsClientId=cid)[0],
                     p.getBasePositionAndOrientation(probe,physicsClientId=cid)[1],
                     p.getBaseVelocity(probe,physicsClientId=cid)[0],
                     p.getBaseVelocity(probe,physicsClientId=cid)[1])
        after=combined_owner(grain_state,probe_state,seed,friction,end_step)
        validate(after,seed,friction,end_step)
        component,grain_contacts,floor_contacts=h24.contact_sizes(
            p.getContactPoints(physicsClientId=cid),state["ids"],state["floor"])
        instrument_velocity=np.linalg.norm(after["velocity_mps"].values[-1])
        same_source=state["release"][:]
        return {
           "owner":after,"prior_owner":prior,"seed":seed,"friction":friction,
           "source_sequence":same_source,"H26_prior_SHA256":h24.state_sha(prior),
           "release_SHA256":native_release,
           "last_release_step":state["last_release"],"H26_end_step":end_step,
           "first_grain_contact":early_grain,
           "first_floor_contact":early_floor,"first_any_positive_contact":early_any,
           "probe_end_center_z_m":float(after["position_m"].values[-1,2]),
           "probe_end_speed_m_s":float(instrument_velocity),
           "probe_min_center_z_m":min_z,
           "probe_grain_contact_peak_force_N":peak_grain_force,
           "probe_total_grain_contact_impulse_N_s":total_grain_impulse,
           "probe_max_total_grain_contact_force_N":max_grain_force_sum,
           "probe_step_history_SHA":dynamic_history.hexdigest(),
           "pile_grains_high_after_probe":int(np.count_nonzero(grain_state["position_m"][:,2]>.26)),
           "pile_largest_force_component_after_probe":int(component),
           "pile_grain_contacts_after_probe":int(grain_contacts),
           "pile_floor_contacts_after_probe":int(floor_contacts),
           "inventory_total_kg":validate(after,seed,friction,end_step),
           "owner_SHA256":sha(after)
        }
    finally:
        p.disconnect(physicsClientId=state["cid"])

def reject_bad_owners(case):
    owner=case["owner"]
    key=sha(owner)
    seed=case["seed"]
    friction=case["friction"]
    end_step=case["H26_end_step"]
    flags={}
    def reject(name,mutate):
        c=owner.copy(deep=True)
        mutate(c)
        try:validate(c,seed,friction,end_step)
        except ValueError:flags[name]=True
        else:raise AssertionError("Invalid functional owner accepted: "+name)
        if sha(owner)!=key:
            raise AssertionError("Rejected state altered original")
    reject("invented_probe_mass",lambda d:d["material_mass_kg"].values.__setitem__(-1,2.))
    reject("negative_grain_mass",lambda d:d["material_mass_kg"].values.__setitem__(0,-1.))
    reject("wrong_units",lambda d:d["position_m"].attrs.__setitem__("units","cm"))
    reject("wrong_probe_identity",lambda d:d.coords.__setitem__("object",[f"grain_{i:03d}" for i in range(h26.N)]+["probe_fake"]))
    reject("wrong_radius",lambda d:d["radius_m"].values.__setitem__(-1,2.))
    reject("invalid_orientation",lambda d:d["orientation_xyzw"].values.__setitem__((0,3),2.))
    reject("body_overlap",lambda d:d["position_m"].values.__setitem__((1,slice(None)),d["position_m"].values[0].copy()))
    reject("extra_material_stock",lambda d:d.__setitem__("mass_copy",xr.DataArray(np.ones(h26.N+1),dims=("object",))))
    reject("time_rewind",lambda d:d.attrs.__setitem__("probe_steps",0))
    return flags

def main():
    a=run(SEED1,True)
    b=run(SEED2,True)
    nofriction=run(SEED1,False)
    replay=run(SEED1,True)
    failed=[]
    def gate(name,flag):
        if not flag:failed.append(name)
    gate("H26_all_original_reproduced",all(
        x["H26_prior_SHA256"]==REFERENCE[(x["seed"],x["friction"])][0]
        for x in (a,b,nofriction,replay)))
    gate("no_friction_monolayer_reproduced",
         nofriction["prior_owner"]["position_m"].values[:,2].max()<.1
         and nofriction["prior_owner"]["position_m"].values[:,2].min()>.055)
    gate("stock_invariant",all(x["inventory_total_kg"]==3.225 for x in (a,b,nofriction,replay)))
    base=nofriction["first_any_positive_contact"]
    for label,c in (("active_seed1",a),("active_seed2",b)):
        grain=c["first_grain_contact"]
        anyhit=c["first_any_positive_contact"]
        gate(label+"_higher_first_contact",grain is not None and
             (c["first_floor_contact"] is None or
              grain["step"]<c["first_floor_contact"]["step"])
             and grain["center_z_m"]>.35 and base is not None
             and anyhit is not None
             and anyhit["center_z_m"]>=base["center_z_m"]+.18)
        gate(label+"_probe_supported_late",c["probe_end_center_z_m"]>.30
             and c["probe_end_speed_m_s"]<.12)
        gate(label+"_granular_structure_survives",c["pile_grains_high_after_probe"]>=25
             and c["pile_largest_force_component_after_probe"]>=45)
    gate("flat_control_probe_on_ground",nofriction["probe_end_center_z_m"]<.22)
    gate("seed_different_geometry",np.max(np.abs(a["owner"]["position_m"].values[:h26.N]-
                                           b["owner"]["position_m"].values[:h26.N]))>.01)
    gate("exact_replay",
         a["source_sequence"]==replay["source_sequence"]
         and a["first_grain_contact"]==replay["first_grain_contact"]
         and a["first_floor_contact"]==replay["first_floor_contact"]
         and a["first_any_positive_contact"]==replay["first_any_positive_contact"]
         and a["probe_step_history_SHA"]==replay["probe_step_history_SHA"]
         and a["owner_SHA256"]==replay["owner_SHA256"]
         and all(np.array_equal(a["owner"][field].values,replay["owner"][field].values)
                 for field in FIELDS))
    rejected=reject_bad_owners(a)
    with tempfile.TemporaryDirectory(prefix="world_h36_") as temp:
        f=pathlib.Path(temp)/"impact_owner.nc"
        a["owner"].to_netcdf(f,engine="scipy")
        with xr.open_dataset(f,engine="scipy") as fd:
            read=fd.load()
        validate(read,SEED1,True,a["H26_end_step"])
        gate("netcdf_owner_exact",sha(read)==a["owner_SHA256"])
        snapshot_bytes=f.stat().st_size
    def expose(c):
        return {k:v for k,v in c.items() if k not in ("owner","prior_owner","source_sequence")}
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"E7 H36 function of native spontaneous frictional heap as projectile support",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "probe_mass_kg":PROBE_M,"probe_radius_m":PROBE_R,
        "probe_start_xyz_m":PROBE_INITIAL.tolist(),
        "probe_steps":N_IMPACT_STEPS,"dt_s":h26.DT,
        "active_seed1":expose(a),"active_seed2":expose(b),
        "zero_friction_control":expose(nofriction),
        "invalid_owners_rejected":rejected,
        "replay_exact":True,"checkpoint_bytes":snapshot_bytes,
        "failed_preregistered_gates":failed,
        "limitations":"One fixed vertical probe, two seeds of coarse spherical grains, no calibrated impact physics, no diversity of ecological functions, no open-ended emergence or integrated world clock."
    },sort_keys=True),flush=True)
    if failed:
        raise AssertionError("H36 preregistered functional gates failed: "+", ".join(failed))

if __name__=="__main__":
    main()
