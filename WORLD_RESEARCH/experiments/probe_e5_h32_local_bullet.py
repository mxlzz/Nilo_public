"""E5 H32 stage 2 Python3.11: downstream native Bullet contact on local-K terrains.

Reuses exact vetted H31 native Bullet contact routine; H32 owner K_sed field
is a physical parameter, not a second material inventory. Source and
body remain in the same canonical NetCDF checkpoint across both runtimes.
"""
from __future__ import annotations

import json
import pathlib
import platform
import sys
from importlib.metadata import version

import numpy as np
import pybullet
import xarray as xr

import probe_e4_h30_worldengine_bullet as b4
import probe_e5_h31_owner_contract as c
import probe_e5_h31_bullet_stage as h31bullet
import probe_e5_h32_local_contract as local

def load_owner(path,raw,seed,index,mode,receiver_sha,expected_sha):
    with xr.open_dataset(path,engine="scipy") as f:
        ds=f.load()
    local.validate(ds,raw,seed,index,mode,receiver_sha)
    if local.hash_owner(ds)!=expected_sha:
        raise ValueError("H32 native Landlab checkpoint failed owner hash")
    if ds.attrs["body_status"]!="reservoir" or ds.attrs["landlab_step"]!=c.TIMESTEPS:
        raise ValueError("Landlab did not complete soil with unreleased body")
    return ds

def output_bullet(h32owner,raw,seed,index,mode,receiver_sha,control_patch):
    core=local.original_projection(h32owner)
    solved=h31bullet.contact_from_owner(
        core,raw,seed,c.K_ACTIVE,index,control_patch)
    candidate=h32owner.copy(deep=True)
    for name in ("body_position_m_nominal",
                 "body_velocity_m_nominal_per_s","body_orientation_xyzw",
                 "body_angular_velocity_rad_s"):
        candidate[name].values[:]=solved["owner"][name].values
    for name in ("body_status","body_release_count","patch_y","patch_x",
                 "bullet_t_s"):
        candidate.attrs[name]=solved["owner"].attrs[name]
    local.validate(candidate,raw,seed,index,mode,receiver_sha)
    if (not np.array_equal(candidate[local.LOCAL_FIELD].values,
                           h32owner[local.LOCAL_FIELD].values) or
        not np.array_equal(candidate["soil_mass_kg"].values,
                           h32owner["soil_mass_kg"].values)):
        raise ValueError("Rigid contact changed soil or local physical property")
    return {
        "owner":candidate,
        "final_joint_sha256":local.hash_owner(candidate),
        **{k:v for k,v in solved.items() if k!="owner"}
    }

def choose_patch_again(before,after,local_center,downstream):
    banned=local.target_patch_coords(local_center)
    route=set(int(i) for i in downstream)
    chosen=[]
    for y in range(1,16):
        for x in range(1,32):
            nodes={(y,x),(y,x+1),(y+1,x),(y+1,x+1)}
            if nodes&banned:continue
            if not {i*c.SHAPE[1]+j for i,j in nodes}&route:
                continue
            a=before[y:y+2,x:x+2]
            b=after[y:y+2,x:x+2]
            delta=float(.6*(b[0,0]-a[0,0])+
                        .1*(b[0,1]-a[0,1])+
                        .3*(b[1,1]-a[1,1]))
            chosen.append((-abs(delta),y,x,delta))
    if not chosen:
        raise ValueError("No downstream target exists independent of Bullet")
    _,y,x,d=min(chosen)
    return (y,x),float(d)

def reject_corruption(owner,raw,seed,index,mode,receiver_sha):
    start=local.hash_owner(owner)
    flags={}
    def reject(label,patch):
        ds=owner.copy(deep=True)
        patch(ds)
        try:local.validate(ds,raw,seed,index,mode,receiver_sha)
        except ValueError:flags[label]=True
        else:raise AssertionError("Invalid joint H32 owner accepted "+label)
        if local.hash_owner(owner)!=start:
            raise AssertionError("Rejected test corrupted true owner")
    reject("unaccounted_soil_1kg",lambda ds:ds["soil_mass_kg"].values.__setitem__((2,2),ds["soil_mass_kg"].values[2,2]+1))
    reject("negative_material",lambda ds:ds["soil_mass_kg"].values.__setitem__((2,2),-1.))
    reject("changed_body_mass",lambda ds:ds["body_mass_kg"].values.__setitem__(0,3.))
    reject("changed_K_outside_patch",lambda ds:ds[local.LOCAL_FIELD].values.__setitem__((1,1),0.))
    reject("negative_K_in_patch",lambda ds:ds[local.LOCAL_FIELD].values.__setitem__((index[0],index[1]),-1.))
    reject("changed_K_target_metadata",lambda ds:ds.attrs.__setitem__("erodibility_target_x",index[1]+1))
    reject("bad_soil_units",lambda ds:ds["soil_mass_kg"].attrs.__setitem__("units","g"))
    reject("source_sha_corrupt",lambda ds:ds.attrs.__setitem__("source_hash_sha256","bad"))
    reject("duplicated_mass_stock",lambda ds:ds.__setitem__("second_body_mass",xr.DataArray(np.ones(1),dims=("body",))))
    reject("negative_export",lambda ds:ds.attrs.__setitem__("exported_soil_kg",-1.))
    return flags

def main(rawpath,input_dir,output_dir):
    dest=pathlib.Path(output_dir)
    dest.mkdir(parents=True,exist_ok=True)
    report=json.loads((pathlib.Path(input_dir)/"manifest.json").read_text(encoding="utf-8"))
    with np.load(rawpath,allow_pickle=False) as fd:
        raw={7321:np.asarray(fd["elevation_seed_7321"],dtype="<f8").copy(),
             8128:np.asarray(fd["elevation_seed_8128"],dtype="<f8").copy()}
        sha=[str(h) for h in fd["source_sha256"]]
        revision=str(fd["worldengine_revision"][0])
    failed=[]
    def gate(label,okay):
        if not okay:failed.append(label)
    gate("raw_worldengine_unmodified",
         revision==c.SOURCE_REVISION and sha==[c.SOURCES[7321],c.SOURCES[8128]]
         and all(c.sha_raw(raw[k])==c.SOURCES[k] for k in raw))
    gate("Landlab_local_gate_all_passed",report.get("failed_preregistered_gates",[])==[])
    cases={}
    for seed in (7321,8128):
        desc=report["seeds"][str(seed)]
        initial=desc["initial_flow_selection"]
        target=tuple(initial["target"])
        receiver_sha=initial["receivers_sha256"]
        controls={}
        for mode in ("control","local_off"):
            info=desc["runs"][mode]
            controls[mode]=load_owner(
                pathlib.Path(input_dir)/info["checkpoint"],raw[seed],
                seed,target,mode,receiver_sha,info["sha256"])
        original=local.derived_terrain(controls["control"])
        altered=local.derived_terrain(controls["local_off"])
        patch,delta=choose_patch_again(
            original,altered,target,initial["downstream_nodes_outside_patch"])
        gate(f"{seed}_downstream_selection_replay",
             list(patch)==desc["downstream_patch_index"]
             and abs(delta-desc["downstream_patch_delta_z_m_nominal"])<1e-12)
        gate(f"{seed}_downstream_mass_response",
             desc["max_abs_downstream_material_delta_kg"]>=100.)
        gate(f"{seed}_downstream_terrain_response",abs(delta)>.003)
        before_patch=original[patch[0]:patch[0]+2,patch[1]:patch[1]+2].copy()
        active=output_bullet(controls["local_off"],raw[seed],seed,patch,
                             "local_off",receiver_sha,before_patch)
        control=output_bullet(controls["control"],raw[seed],seed,patch,
                              "control",receiver_sha,before_patch)
        cases[seed]={"active":active,"control":control,
                     "index":patch,"delta_z":delta}
        raydiff=active["actual_ray_z_m_nominal"]-control["actual_ray_z_m_nominal"]
        gate(f"{seed}_ray_tracks_owner_height",
             active["ray_error_m_nominal"]<.001
             and control["ray_error_m_nominal"]<.001
             and abs(raydiff-delta)<.001)
        f_a=active["first_positive_contact"]
        f_c=control["first_positive_contact"]
        gate(f"{seed}_positive_contact_both",
             f_a is not None and f_c is not None
             and active["contact_events"]>0 and control["contact_events"]>0
             and active["worst_contact_distance_m_nominal"]>=-.05
             and control["worst_contact_distance_m_nominal"]>=-.05)
        if f_a is not None and f_c is not None:
            shift=(f_a["terrain_xyz_m_nominal"][2]-f_c["terrain_xyz_m_nominal"][2])
            gate(f"{seed}_local_K_changes_downstream_contact",
                 shift*delta>0 and abs(shift)>=.002
                 and abs(shift-delta)<=.03)
        gate(f"{seed}_same_start_pose",
             active["release_xyz_m_nominal"]==control["release_xyz_m_nominal"])
        for mode,case in (("local_off",active),("control",control)):
            file=dest/f"{seed}_{mode}_joint_owner.nc"
            case["owner"].to_netcdf(file,engine="scipy")
            with xr.open_dataset(file,engine="scipy") as f:loaded=f.load()
            local.validate(loaded,raw[seed],seed,target,mode,receiver_sha)
            gate(f"{seed}_{mode}_checkpoint",
                 local.hash_owner(loaded)==case["final_joint_sha256"])
    first=cases[7321]
    info=report["seeds"]["7321"]
    source=info["initial_flow_selection"]
    t=tuple(source["target"])
    again=load_owner(pathlib.Path(input_dir)/info["runs"]["local_off"]["checkpoint"],
                     raw[7321],7321,t,"local_off",source["receivers_sha256"],
                     info["runs"]["local_off"]["sha256"])
    ctrl=load_owner(pathlib.Path(input_dir)/info["runs"]["control"]["checkpoint"],
                    raw[7321],7321,t,"control",source["receivers_sha256"],
                    info["runs"]["control"]["sha256"])
    idx=first["index"]
    before=local.derived_terrain(ctrl)[idx[0]:idx[0]+2,idx[1]:idx[1]+2].copy()
    replay=output_bullet(again,raw[7321],7321,idx,"local_off",
                         source["receivers_sha256"],before)
    gate("bit_identical_landlab_and_bullet_replay",
         report["replay_exact"] and
         replay["final_joint_sha256"]==first["active"]["final_joint_sha256"]
         and replay["first_positive_contact"]==first["active"]["first_positive_contact"]
         and replay["actual_ray_z_m_nominal"]==first["active"]["actual_ray_z_m_nominal"])
    rejected=reject_corruption(first["active"]["owner"],raw[7321],7321,t,"local_off",source["receivers_sha256"])
    def omit_owner(q):
        return {k:v for k,v in q.items() if k!="owner"}
    def public_case(seed):
        u=cases[seed]
        f_a=u["active"]["first_positive_contact"]
        f_c=u["control"]["first_positive_contact"]
        return {
            "seed":seed,"local_K_target":report["seeds"][str(seed)]["initial_flow_selection"]["target"],
            "downstream_patch_index":list(u["index"]),
            "downstream_terrain_change_m_nominal":u["delta_z"],
            "downstream_max_soil_mass_change_kg":report["seeds"][str(seed)]["max_abs_downstream_material_delta_kg"],
            "ray_height_difference_m_nominal":u["active"]["actual_ray_z_m_nominal"]-
                u["control"]["actual_ray_z_m_nominal"],
            "first_contact_height_difference_m_nominal":
                f_a["terrain_xyz_m_nominal"][2]-f_c["terrain_xyz_m_nominal"][2]
                if f_a is not None and f_c is not None else None,
            "soil_branch_statistics":report["seeds"][str(seed)],
            "active_bullet":omit_owner(u["active"]),
            "control_bullet":omit_owner(u["control"]),
        }
    metrics={
        "experiment":"E5 H32 local K_sed intervention changes downstream soil and rigid contact",
        "python_landlab":report["python"],"landlab":report["landlab"],
        "python_bullet":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "source_worldengine_sha":revision,
        "two_runtime_single_canonical_owner":True,
        "total_soil_and_body_initial_kg":c.MASS0+c.BODY_MASS,
        "local_3_by_3_K_sed_off":True,"global_K_sed_elsewhere":c.K_ACTIVE,
        "seed_7321":public_case(7321),"seed_8128":public_case(8128),
        "rejected_invalid_candidates":rejected,
        "bit_identical_replay":True,
        "failed_preregistered_gates":failed,
        "limitations":"One-way local erodibility parameter intervention, selected on initial native D8 drainage path. Landlab and Bullet remain sequential with distinct clocks and no rigid feedback. Vertical heights are m_nominal, not calibrated geology."
    }
    print("WORLD_EVAL_JSON "+json.dumps(metrics,sort_keys=True),flush=True)
    if failed:raise AssertionError("H32 preregistered downstream gates failed: "+", ".join(failed))

if __name__=="__main__":
    main(sys.argv[1],sys.argv[2],sys.argv[3])
