"""E5 H31 stage 2/2: PyBullet reads the exact Landlab material owner.

Python 3.11 intentionally never imports Landlab. It receives the canonical
xarray NetCDF checkpoint from Python 3.13 Landlab and publishes native
Bullet contact outcomes to the SAME logical owner after validation.
Preregistered H31 thresholds unchanged; no bidirectional feedback claimed.
"""
from __future__ import annotations

import json
import pathlib
import platform
import sys
import tempfile
from importlib.metadata import version

import numpy as np
import pybullet as p
import xarray as xr

import probe_e4_h30_worldengine_bullet as bullet4
import probe_e5_h31_owner_contract as c

def load_owner(path,raw,seed,k,expected_sha):
    with xr.open_dataset(path,engine="scipy") as opened:
        owner=opened.load()
    c.validate(owner,raw,seed,k)
    actual=c.hash_owner(owner)
    if actual!=expected_sha:
        raise ValueError("Canonical owner differs from Landlab stage hash")
    if owner.attrs["body_status"]!="reservoir":
        raise ValueError("Body material must remain in reservoir at handoff")
    if owner.attrs["landlab_step"]!=c.TIMESTEPS:
        raise ValueError("Landlab phase incomplete")
    return owner

def contact_from_owner(owner,raw,seed,k,index,before_patch):
    """Native Bullet solve on derived triangles, no second soil mass stock."""
    c.validate(owner,raw,seed,k)
    zfield=c.topography(owner)
    patch=zfield[index[0]:index[0]+2,index[1]:index[1]+2].copy()
    z_expected=float(bullet4.surface_at_probe(patch))
    start_z=float(bullet4.surface_at_probe(before_patch)+3.)
    release=np.array([40.,30.,start_z],dtype=np.float64)
    first=None
    contacts=0
    worst=0.
    cid=p.connect(p.DIRECT)
    try:
        p.setPhysicsEngineParameter(fixedTimeStep=c.BULLET_DT,
                                    numSolverIterations=60,physicsClientId=cid)
        p.setGravity(0.,0.,-9.81,physicsClientId=cid)
        shape=p.createCollisionShape(
            p.GEOM_MESH,
            vertices=bullet4.mesh_vertices(patch),
            indices=[0,1,2,0,2,3],
            flags=p.GEOM_FORCE_CONCAVE_TRIMESH,physicsClientId=cid)
        terrain=p.createMultiBody(baseMass=0.,
                                  baseCollisionShapeIndex=shape,
                                  physicsClientId=cid)
        p.changeDynamics(terrain,-1,lateralFriction=.8,restitution=0.,
                         physicsClientId=cid)
        ray=p.rayTest([40.,30.,z_expected+10.],
                      [40.,30.,z_expected-10.],physicsClientId=cid)[0]
        if ray[0]!=terrain:
            raise ValueError("No Bullet ray hit on actual owner-derived surface")
        sphere=p.createCollisionShape(p.GEOM_SPHERE,radius=c.BODY_RADIUS,
                                      physicsClientId=cid)
        body=p.createMultiBody(baseMass=c.BODY_MASS,
                               baseCollisionShapeIndex=sphere,
                               basePosition=release.tolist(),
                               physicsClientId=cid)
        p.changeDynamics(body,-1,lateralFriction=.8,restitution=0.,
                         physicsClientId=cid)
        for step in range(1,c.BULLET_STEPS+1):
            p.stepSimulation(physicsClientId=cid)
            for cp in p.getContactPoints(physicsClientId=cid):
                if (set((cp[1],cp[2]))==set((body,terrain))
                    and float(cp[9])>1e-5):
                    contacts+=1
                    worst=min(worst,float(cp[8]))
                    if first is None:
                        terrain_xyz=cp[5] if cp[1]==terrain else cp[6]
                        first={
                            "step":step,
                            "terrain_xyz_m_nominal":[float(x) for x in terrain_xyz],
                            "normal_force_N":float(cp[9]),
                        }
        final_pos,final_quat=p.getBasePositionAndOrientation(body,physicsClientId=cid)
        velocity,omega=p.getBaseVelocity(body,physicsClientId=cid)
    finally:
        p.disconnect(physicsClientId=cid)

    candidate=owner.copy(deep=True)
    candidate.attrs["body_status"]="released"
    candidate.attrs["body_release_count"]=1
    candidate.attrs["patch_y"]=int(index[0])
    candidate.attrs["patch_x"]=int(index[1])
    candidate.attrs["bullet_t_s"]=c.BULLET_STEPS*c.BULLET_DT
    candidate["body_position_m_nominal"].values[0]=np.asarray(final_pos)
    candidate["body_velocity_m_nominal_per_s"].values[0]=np.asarray(velocity)
    candidate["body_orientation_xyzw"].values[0]=np.asarray(final_quat)
    candidate["body_angular_velocity_rad_s"].values[0]=np.asarray(omega)
    c.validate(candidate,raw,seed,k)
    # Publication: candidate validated in the same canonical Dataset schema,
    # and input from Landlab remains immutable and is separately hashed.
    if not np.array_equal(candidate["soil_mass_kg"].values,owner["soil_mass_kg"].values):
        raise ValueError("Bullet changed Landlab material mass")
    return {
        "owner":candidate,
        "seed":seed,"K_sed":k,"patch_index":list(index),
        "release_xyz_m_nominal":release.tolist(),
        "expected_ray_z_m_nominal":z_expected,
        "actual_ray_z_m_nominal":float(ray[3][2]),
        "ray_error_m_nominal":abs(float(ray[3][2])-z_expected),
        "first_positive_contact":first,
        "contact_events":contacts,
        "worst_contact_distance_m_nominal":worst,
        "final_position_xyz_m_nominal":[float(x) for x in final_pos],
        "final_velocity_xyz_m_nominal_per_s":[float(x) for x in velocity],
        "final_joint_owner_sha":c.hash_owner(candidate),
    }

def reject_invalid(owner,raw,seed,k):
    original_sha=c.hash_owner(owner)
    results={}
    def attempt(label,change):
        trial=owner.copy(deep=True)
        change(trial)
        try:
            c.validate(trial,raw,seed,k)
        except ValueError:
            results[label]=True
        else:
            raise AssertionError("Joint owner incorrectly accepted "+label)
        if c.hash_owner(owner)!=original_sha:
            raise AssertionError("Good owner changed on rejection")
    attempt("plus_1kg_soil_without_source",lambda d:d["soil_mass_kg"].values.__setitem__((2,2),d["soil_mass_kg"].values[2,2]+1.))
    attempt("negative_soil_mass",lambda d:d["soil_mass_kg"].values.__setitem__((2,2),-1.))
    attempt("wrong_body_mass",lambda d:d["body_mass_kg"].values.__setitem__(0,3.))
    attempt("wrong_body_position_unit",lambda d:d["body_position_m_nominal"].attrs.__setitem__("units","cm"))
    attempt("modified_bedrock",lambda d:d["bedrock_elevation_m"].values.__setitem__((2,2),d["bedrock_elevation_m"].values[2,2]+1.))
    attempt("wrong_source_hash",lambda d:d.attrs.__setitem__("source_hash_sha256","tampered"))
    attempt("wrong_body_id",lambda d:d.coords.__setitem__("body",np.array([9],dtype=np.int32)))
    attempt("duplicate_mass_stock",lambda d:d.__setitem__("other_mass_kg",xr.DataArray(np.ones(1),dims=("body",))))
    attempt("negative_export",lambda d:d.attrs.__setitem__("exported_soil_kg",-1.))
    return results

def main(rawpath,stage1_dir,stage2_dir):
    target=pathlib.Path(stage2_dir)
    target.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((pathlib.Path(stage1_dir)/"manifest.json").read_text(encoding="utf-8"))
    with np.load(rawpath,allow_pickle=False) as fd:
        upstream=str(fd["worldengine_revision"][0])
        source_hashes=[str(x) for x in fd["source_sha256"]]
        maps={
            7321:np.asarray(fd["elevation_seed_7321"],dtype="<f8").copy(),
            8128:np.asarray(fd["elevation_seed_8128"],dtype="<f8").copy(),
        }
    failures=[]
    def gate(name,ok):
        if not ok:
            failures.append(name)
    gate("matching_upstream_raw",upstream==c.SOURCE_REVISION
         and source_hashes==[c.SOURCES[7321],c.SOURCES[8128]]
         and manifest["source_raw_hashes"]==source_hashes
         and all(c.sha_raw(maps[seed])==c.SOURCES[seed] for seed in maps))
    cases={}
    for seed in (7321,8128):
        records={}
        for k,label in ((c.K_ACTIVE,"active"),(0.,"control")):
            key=f"{seed}_{label}"
            desc=manifest["runs"][key]
            existing=load_owner(pathlib.Path(stage1_dir)/desc["checkpoint_name"],
                                maps[seed],seed,k,desc["final_owner_sha"])
            records[label]=existing
            budget=c.validate(existing,maps[seed],seed,k)
            gate(f"{seed}_{label}_closed_soil_plus_body_ledger",
                 abs(budget["mass_residual_kg"])<=.09216
                 and desc["peak_closed_mass_error_kg"]<=.09216)
        initial=c.topography(records["control"])
        eroded=c.topography(records["active"])
        index,delta=c.select_patch(initial,eroded)
        previous=np.asarray(initial[index[0]:index[0]+2,index[1]:index[1]+2]).copy()
        prior=manifest["patch_selection"][str(seed)]
        gate(f"{seed}_patch_selection_identical_to_Landlab",
             prior["patch_index"]==list(index) and
             prior["delta_z_m_nominal"]==delta)
        gate(f"{seed}_causal_soil_change",abs(delta)>.005
             and manifest["runs"][f"{seed}_active"]["changed_soil_nodes"]>0
             and manifest["runs"][f"{seed}_control"]["changed_soil_nodes"]==0
             and manifest["runs"][f"{seed}_control"]["exported_soil_kg"]==0.)
        active=contact_from_owner(records["active"],maps[seed],seed,
                                  c.K_ACTIVE,index,previous)
        control=contact_from_owner(records["control"],maps[seed],seed,
                                   0.,index,previous)
        cases[seed]={"index":index,"delta":delta,
                     "active":active,"control":control}
        actual_ray_shift=active["actual_ray_z_m_nominal"]-control["actual_ray_z_m_nominal"]
        gate(f"{seed}_rays_derived_exactly_from_single_owner",
             active["ray_error_m_nominal"]<.001
             and control["ray_error_m_nominal"]<.001
             and abs(actual_ray_shift-delta)<.001)
        f1=active["first_positive_contact"]
        f0=control["first_positive_contact"]
        gate(f"{seed}_positive_contact_both",
             f1 is not None and f0 is not None
             and active["contact_events"]>0
             and control["contact_events"]>0
             and active["worst_contact_distance_m_nominal"]>=-.05
             and control["worst_contact_distance_m_nominal"]>=-.05)
        if f1 is not None and f0 is not None:
            contact_shift=(f1["terrain_xyz_m_nominal"][2]-
                           f0["terrain_xyz_m_nominal"][2])
            gate(f"{seed}_force_contact_follows_soil_change",
                 contact_shift*delta>0 and abs(contact_shift)>=.003
                 and abs(contact_shift-delta)<=.03)
        # Record the actual final canonical state of both controlled scenes.
        for label,case in (("active",active),("control",control)):
            fname=target/f"{seed}_{label}_joint_owner.nc"
            case["owner"].to_netcdf(fname,engine="scipy")
            with xr.open_dataset(fname,engine="scipy") as fo:
                restored=fo.load()
            c.validate(restored,maps[seed],seed,c.K_ACTIVE if label=="active" else 0.)
            gate(f"{seed}_{label}_joint_checkpoint",c.hash_owner(restored)==case["final_joint_owner_sha"])
        gate(f"{seed}_same_body_release_position",
             active["release_xyz_m_nominal"]==control["release_xyz_m_nominal"])

    first=cases[7321]
    repeat=contact_from_owner(
        load_owner(
            pathlib.Path(stage1_dir)/manifest["runs"]["7321_active"]["checkpoint_name"],
            maps[7321],7321,c.K_ACTIVE,manifest["runs"]["7321_active"]["final_owner_sha"]),
        maps[7321],7321,c.K_ACTIVE,first["index"],
        c.topography(load_owner(
            pathlib.Path(stage1_dir)/manifest["runs"]["7321_control"]["checkpoint_name"],
            maps[7321],7321,0.,manifest["runs"]["7321_control"]["final_owner_sha"]))[
            first["index"][0]:first["index"][0]+2,first["index"][1]:first["index"][1]+2])
    gate("bit_exact_replay_terrain_body",
         manifest["landlab_replay_seed7321_exact"]
         and repeat["final_joint_owner_sha"]==first["active"]["final_joint_owner_sha"]
         and repeat["first_positive_contact"]==first["active"]["first_positive_contact"]
         and repeat["actual_ray_z_m_nominal"]==first["active"]["actual_ray_z_m_nominal"])
    negatives=reject_invalid(first["active"]["owner"],maps[7321],7321,c.K_ACTIVE)
    def expose(case):
        return {k:v for k,v in case.items() if k!="owner"}
    def expose_seed(seed):
        obj=cases[seed]
        active=obj["active"]
        control=obj["control"]
        f_a=active["first_positive_contact"]
        f_b=control["first_positive_contact"]
        return {
            "seed":seed,
            "patch_index":list(obj["index"]),
            "derived_erosion_height_shift_m_nominal":obj["delta"],
            "ray_height_shift_m_nominal":active["actual_ray_z_m_nominal"]-
                control["actual_ray_z_m_nominal"],
            "first_positive_contact_height_shift_m_nominal":
                f_a["terrain_xyz_m_nominal"][2]-f_b["terrain_xyz_m_nominal"][2]
                if (f_a is not None and f_b is not None) else None,
            "Landlab_active":manifest["runs"][f"{seed}_active"],
            "Landlab_K0":manifest["runs"][f"{seed}_control"],
            "active_bullet":expose(active),"control_bullet":expose(control),
        }
    result={
        "experiment":"E5 H31 one canonical xarray owner across Python3.13 Landlab and Python3.11 Bullet",
        "producer_worldengine_sha":upstream,
        "landlab_python":manifest["python"],"landlab":manifest["landlab"],
        "bullet_python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "physical_scope":"one-way soil erosion -> terrain surface -> native rigid contact",
        "seeds":{str(seed):expose_seed(seed) for seed in (7321,8128)},
        "original_total_mass_soil_plus_body_kg":c.MASS0+c.BODY_MASS,
        "material_clock_landlab_steps":c.TIMESTEPS,
        "body_clock_bullet_steps":c.BULLET_STEPS,
        "two_python_runtimes_one_canonical_checkpoint":True,
        "rejected_invalid_owner_states":negatives,
        "replay_exact":True,
        "preregistered_gates_failed":failures,
        "limitations":"Only sequential one-way coupling; no reaction of body force on sediment; raw heights are nominal units without geophysical calibration; two physical clocks do not form a synchronized world; final source and actor state persisted with no interim Bullet solver state."
    }
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True),flush=True)
    if failures:
        raise AssertionError("H31 preregistered physical gates failed: "+", ".join(failures))

if __name__=="__main__":
    main(sys.argv[1],sys.argv[2],sys.argv[3])
