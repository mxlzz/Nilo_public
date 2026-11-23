"""E5/H31: one-way causal coupling of Landlab soil erosion to Bullet contact.

One xarray material+rigid actor owner exists from t0. The 2kg rigid actor is
held in a disclosed *reservoir* until its local release after six erosion
steps; soil and actor budgets stay jointly conserved. Landlab and Bullet
are existing upstream physics solvers, never simultaneously authoritative.
Protocol preregistered in ETAPA_5_H31_PROTOCOLO_SUELO_CONTACTO.md.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import sys
import tempfile
from importlib.metadata import version

import landlab
import numpy as np
import pybullet as p
import xarray as xr

import probe_e4_h29_generated_owner_landlab as e4
import probe_e4_h30_worldengine_bullet as bullet4

BODY_MASS=2.
BODY_RADIUS=.5
BODY_AXIS=("x","y","z")
EROSION_STEPS=e4.STEPS
CONTACT_STEPS=720
DT_BULLET=1./240.
BODY_START_XY=(40.,30.)
SOIL_FIELDS={"soil_mass_kg","bedrock_elevation_m","is_core_node"}
BODY_FIELDS={"body_mass_kg","body_position_m_nominal",
             "body_velocity_m_nominal_per_s","body_orientation_xyzw",
             "body_angular_velocity_rad_s"}
ALLOWED=SOIL_FIELDS|BODY_FIELDS

def new_world(raw,seed,source_sha,k):
    base=e4.create(raw,seed,source_sha)
    base["body_mass_kg"]=xr.DataArray([BODY_MASS],dims=("body",),attrs={"units":"kg"})
    base["body_position_m_nominal"]=xr.DataArray(
        [[0.,0.,0.]],dims=("body","axis"),attrs={"units":"m_nominal"})
    base["body_velocity_m_nominal_per_s"]=xr.DataArray(
        [[0.,0.,0.]],dims=("body","axis"),attrs={"units":"m_nominal/s"})
    base["body_orientation_xyzw"]=xr.DataArray(
        [[0.,0.,0.,1.]],dims=("body","quat"),attrs={"units":"1"})
    base["body_angular_velocity_rad_s"]=xr.DataArray(
        [[0.,0.,0.]],dims=("body","axis"),attrs={"units":"rad/s"})
    base=base.assign_coords({"body":np.array([0],dtype=np.int32),
        "axis":np.array(BODY_AXIS),"quat":np.array(["x","y","z","w"])})
    base.attrs.update({
        "body_status":"reservoir","body_release_count":0,
        "body_source_mass_kg":BODY_MASS,"body_radius_m_nominal":BODY_RADIUS,
        "scenario_K_sed":float(k),"landlab_step":0,
        "landlab_t_bench":0.,"bullet_t_s":0.,
        "patch_y":-1,"patch_x":-1,
    })
    return base

def soil_view(owner):
    result=owner[list(SOIL_FIELDS)].copy(deep=False)
    result.attrs={k:v for k,v in owner.attrs.items()
                  if k in ("schema_version","source_generator","source_seed",
                           "source_hash_sha256","source_units",
                           "nominal_elevation_range_m","normalization",
                           "landlab_x_y_offset_m","core_sample_alignment",
                           "horizontal_spacing_m","cell_area_m2","density_kg_m3",
                           "original_soil_kg","exported_soil_kg","soil_material")}
    return result

def validate_joint(owner,raw,seed,sha,k):
    if set(owner.data_vars)!=ALLOWED:
        raise ValueError("Extra/missing material, pose or terrain stock")
    if (owner["body_mass_kg"].dims!=("body",)
        or owner["body_position_m_nominal"].dims!=("body","axis")
        or owner["body_velocity_m_nominal_per_s"].dims!=("body","axis")
        or owner["body_orientation_xyzw"].dims!=("body","quat")
        or owner["body_angular_velocity_rad_s"].dims!=("body","axis")):
        raise ValueError("Invalid rigid body owner shape")
    if (owner.coords["body"].values.tolist()!=[0]
        or owner.coords["axis"].values.tolist()!=list(BODY_AXIS)
        or owner.coords["quat"].values.tolist()!=["x","y","z","w"]):
        raise ValueError("Body identity/axes invalid")
    for field,unit in [
        ("body_mass_kg","kg"),("body_position_m_nominal","m_nominal"),
        ("body_velocity_m_nominal_per_s","m_nominal/s"),
        ("body_orientation_xyzw","1"),
        ("body_angular_velocity_rad_s","rad/s"),
    ]:
        if owner[field].attrs.get("units")!=unit:
            raise ValueError("Invalid body physical unit")
    if (owner.attrs.get("body_source_mass_kg")!=BODY_MASS
        or owner.attrs.get("body_radius_m_nominal")!=BODY_RADIUS
        or owner.attrs.get("scenario_K_sed")!=float(k)):
        raise ValueError("Body source or physical parameters changed")
    m=owner["body_mass_kg"].values
    pos=owner["body_position_m_nominal"].values
    vel=owner["body_velocity_m_nominal_per_s"].values
    quat=owner["body_orientation_xyzw"].values
    spin=owner["body_angular_velocity_rad_s"].values
    if not np.array_equal(m,np.array([BODY_MASS])):
        raise ValueError("Rigid mass created/deleted")
    if not all(np.isfinite(x).all() for x in (pos,vel,quat,spin)):
        raise ValueError("Invalid body motion")
    if abs(np.linalg.norm(quat[0])-1.)>1e-4:
        raise ValueError("Invalid body quaternion")
    status=owner.attrs.get("body_status")
    count=owner.attrs.get("body_release_count")
    if (status,count) not in (("reservoir",0),("released",1)):
        raise ValueError("Invalid release event status")
    if status=="reservoir" and not np.array_equal(pos,np.array([[0.,0.,0.]])):
        raise ValueError("Unreleased body has physical position")
    if owner.attrs.get("landlab_step") not in range(EROSION_STEPS+1):
        raise ValueError("Invalid erosion progress")
    if owner.attrs.get("landlab_t_bench") not in tuple(i*e4.DT for i in range(EROSION_STEPS+1)):
        raise ValueError("Invalid native erosion time")
    if owner.attrs.get("bullet_t_s") not in (0.,CONTACT_STEPS*DT_BULLET):
        raise ValueError("Invalid rigid time")
    iy,ix=int(owner.attrs.get("patch_y",-100)),int(owner.attrs.get("patch_x",-100))
    if status=="reservoir":
        if (iy,ix)!=(-1,-1):
            raise ValueError("Reservoir should not have a terrain patch")
    elif not (1<=iy<=15 and 1<=ix<=31):
        raise ValueError("Released body has invalid patch source")
    soilbudget=e4.validate(soil_view(owner),raw,sha,seed)
    total=soilbudget["remaining_kg"]+soilbudget["exported_kg"]+float(m.sum())
    if abs(total-(e4.MASS0+BODY_MASS))>max(1e-4,1e-10*e4.MASS0):
        raise ValueError("Soil+export+body budget changed")
    return soilbudget

def owner_hash(ds):
    h=hashlib.sha256()
    for field in sorted(ALLOWED):
        h.update(field.encode())
        h.update(ds[field].values.tobytes())
        h.update(ds[field].attrs.get("units","").encode())
    h.update(json.dumps({k:(v.item() if isinstance(v,np.generic) else v)
                         for k,v in ds.attrs.items()},sort_keys=True).encode())
    for name in ("body","axis","quat","y","x"):
        h.update(repr(ds.coords[name].values.tolist()).encode())
    return h.hexdigest()

def erode(raw,seed,sha,k):
    owner=new_world(raw,seed,sha,k)
    validate_joint(owner,raw,seed,sha,k)
    initial=e4.geom(soil_view(owner)).copy()
    grid,flow,space,outlet=e4.setup_scene(soil_view(owner),k)
    peak_error=0.
    for step in range(1,EROSION_STEPS+1):
        soil=soil_view(owner)
        depth=soil["soil_mass_kg"].values.ravel()/(e4.RHO*e4.AREA)
        np.copyto(grid.at_node["soil__depth"],depth)
        np.copyto(grid.at_node["topographic__elevation"],e4.geom(soil).ravel())
        flow.run_one_step()
        suspended,bedload=space.run_one_step(e4.DT)
        if (not np.isfinite([suspended,bedload]).all() or
            suspended<0 or bedload<0):
            raise ValueError("Native sediment flux invalid")
        new_depth=grid.at_node["soil__depth"].reshape(e4.SHAPE)
        if not np.isfinite(new_depth).all() or np.any(new_depth<0):
            raise ValueError("Native Landlab soil depth invalid")
        candidate=owner.copy(deep=True)
        candidate["soil_mass_kg"].values[:]=new_depth*e4.RHO*e4.AREA
        candidate.attrs["exported_soil_kg"]=float(owner.attrs["exported_soil_kg"])+(float(suspended)+float(bedload))*e4.RHO
        candidate.attrs["landlab_step"]=step
        candidate.attrs["landlab_t_bench"]=step*e4.DT
        budget=validate_joint(candidate,raw,seed,sha,k)
        peak_error=max(peak_error,abs(budget["mass_residual_kg"]))
        owner=candidate
    after=e4.geom(soil_view(owner)).copy()
    return {
        "owner":owner,"initial_terrain":initial,
        "final_terrain":after,"outlet_node":outlet,
        "source_seed":seed,"k":k,
        "peak_mass_residual_kg":peak_error,
        "exported_soil_kg":float(owner.attrs["exported_soil_kg"]),
        "changed_soil_cells":int(np.count_nonzero(
            np.abs(owner["soil_mass_kg"].values-new_world(raw,seed,sha,k)["soil_mass_kg"].values)>1e-6))
    }

def select_patch(initial,final):
    candidates=[]
    for iy in range(1,16):
        for ix in range(1,32):
            old=initial[iy:iy+2,ix:ix+2]
            new=final[iy:iy+2,ix:ix+2]
            delta=float(bullet4.surface_at_probe(new)-bullet4.surface_at_probe(old))
            candidates.append((-abs(delta),iy,ix,delta))
    _,iy,ix,delta=min(candidates)
    return (iy,ix),delta

def contact_probe(owner,raw,seed,sha,k,index,patch_before):
    """Bullet scratch reads only authoritative owner-derived surface."""
    patch=e4.geom(soil_view(owner))[index[0]:index[0]+2,index[1]:index[1]+2]
    z_expected=bullet4.surface_at_probe(patch)
    z_start=bullet4.surface_at_probe(patch_before)+3.
    source_pos=np.array([40.,30.,z_start],dtype=np.float64)
    cid=p.connect(p.DIRECT)
    first=None
    positive=0
    worst=0.
    try:
        p.setPhysicsEngineParameter(fixedTimeStep=DT_BULLET,numSolverIterations=60,
                                    physicsClientId=cid)
        p.setGravity(0.,0.,-9.81,physicsClientId=cid)
        mshape=p.createCollisionShape(p.GEOM_MESH,
            vertices=bullet4.mesh_vertices(patch),
            indices=[0,1,2,0,2,3],
            flags=p.GEOM_FORCE_CONCAVE_TRIMESH,physicsClientId=cid)
        terrain=p.createMultiBody(baseMass=0.,baseCollisionShapeIndex=mshape,
                                  physicsClientId=cid)
        p.changeDynamics(terrain,-1,lateralFriction=.8,restitution=0.,
                         physicsClientId=cid)
        ray=p.rayTest([40.,30.,z_expected+10.],
                      [40.,30.,z_expected-10.],physicsClientId=cid)[0]
        if ray[0]!=terrain:
            raise ValueError("Bullet ray did not hit authoritative generated topography")
        sphere=p.createCollisionShape(p.GEOM_SPHERE,radius=BODY_RADIUS,
                                      physicsClientId=cid)
        body=p.createMultiBody(baseMass=BODY_MASS,
                baseCollisionShapeIndex=sphere,basePosition=source_pos.tolist(),
                physicsClientId=cid)
        p.changeDynamics(body,-1,lateralFriction=.8,restitution=0.,
                         physicsClientId=cid)
        for step in range(1,CONTACT_STEPS+1):
            p.stepSimulation(physicsClientId=cid)
            for c in p.getContactPoints(physicsClientId=cid):
                if (set((c[1],c[2]))==set((body,terrain))
                    and float(c[9])>1e-5):
                    positive+=1
                    worst=min(worst,float(c[8]))
                    if first is None:
                        # p.getContactPoints tuple pointOnA index5, pointOnB index6.
                        point_on_terrain=c[5] if c[1]==terrain else c[6]
                        first={"step":step,
                               "terrain_xyz_m_nominal":list(point_on_terrain),
                               "normal_force_N":float(c[9])}
        final_pos,final_quat=p.getBasePositionAndOrientation(body,physicsClientId=cid)
        final_v,final_w=p.getBaseVelocity(body,physicsClientId=cid)
    finally:
        p.disconnect(physicsClientId=cid)
    result=owner.copy(deep=True)
    result.attrs["body_status"]="released"
    result.attrs["body_release_count"]=1
    result.attrs["patch_y"]=int(index[0])
    result.attrs["patch_x"]=int(index[1])
    result.attrs["bullet_t_s"]=CONTACT_STEPS*DT_BULLET
    result["body_position_m_nominal"].values[0]=np.asarray(final_pos)
    result["body_velocity_m_nominal_per_s"].values[0]=np.asarray(final_v)
    result["body_orientation_xyzw"].values[0]=np.asarray(final_quat)
    result["body_angular_velocity_rad_s"].values[0]=np.asarray(final_w)
    validate_joint(result,raw,seed,sha,k)
    return {
        "owner":result,
        "seed":seed,"k":k,"patch_index":list(index),
        "expected_ray_height_m_nominal":float(z_expected),
        "bullet_ray_height_m_nominal":float(ray[3][2]),
        "ray_height_error_m_nominal":float(abs(ray[3][2]-z_expected)),
        "start_position_m_nominal":source_pos.tolist(),
        "first_positive_terrain_contact":first,
        "positive_contact_events":positive,
        "worst_penetration_m_nominal":worst,
        "final_position_m_nominal":list(final_pos),
        "final_velocity_m_nominal_per_s":list(final_v),
        "joint_owner_sha256":owner_hash(result),
    }

def rejected_states(owner,raw,seed,source_sha,k):
    before=owner_hash(owner);flags={}
    def reject(label,change):
        trial=owner.copy(deep=True);change(trial)
        try:validate_joint(trial,raw,seed,source_sha,k)
        except ValueError:flags[label]=True
        else:raise AssertionError("Invalid joint owner accepted: "+label)
        if owner_hash(owner)!=before:
            raise AssertionError("Rejected owner mutation polluted original")
    reject("unaccounted_1kg_soil",lambda d:d["soil_mass_kg"].values.__setitem__((2,2),d["soil_mass_kg"].values[2,2]+1))
    reject("negative_soil",lambda d:d["soil_mass_kg"].values.__setitem__((2,2),-1.))
    reject("body_mass_wrong",lambda d:d["body_mass_kg"].values.__setitem__(0,3.))
    reject("invalid_length_units",lambda d:d["body_position_m_nominal"].attrs.__setitem__("units","cm"))
    reject("bedrock_corrupt",lambda d:d["bedrock_elevation_m"].values.__setitem__((2,2),d["bedrock_elevation_m"].values[2,2]+1.))
    reject("source_sha_corrupt",lambda d:d.attrs.__setitem__("source_hash_sha256","bad"))
    reject("invalid_body_id",lambda d:d.coords.__setitem__("body",np.array([4],dtype=np.int32)))
    reject("extra_mass_stock",lambda d:d.__setitem__("other_mass_kg",xr.DataArray(np.ones(1),dims=("body",))))
    reject("negative_export",lambda d:d.attrs.__setitem__("exported_soil_kg",-1.))
    return flags

def main(input_file):
    with np.load(input_file,allow_pickle=False) as fd:
        raw={
            7321:np.asarray(fd["elevation_seed_7321"],dtype="<f8").copy(),
            8128:np.asarray(fd["elevation_seed_8128"],dtype="<f8").copy()
        }
        sha=[str(x) for x in fd["source_sha256"]]
        upstream=str(fd["worldengine_revision"][0])
    fail=[]
    def gate(name,cond):
        if not cond:fail.append(name)
    gate("source_worldengine_pinned",upstream==bullet4.UPSTREAM_SHA and
         sha==[bullet4.SOURCE_HASH[7321],bullet4.SOURCE_HASH[8128]] and
         all(e4.digest(raw[seed])==bullet4.SOURCE_HASH[seed] for seed in (7321,8128)))
    cases={}
    for seed in (7321,8128):
        source=bullet4.SOURCE_HASH[seed]
        active=erode(raw[seed],seed,source,e4.K_ACTIVE)
        control=erode(raw[seed],seed,source,0.)
        index,delta=select_patch(control["final_terrain"],active["final_terrain"])
        before_patch=control["final_terrain"][index[0]:index[0]+2,index[1]:index[1]+2]
        active_contact=contact_probe(active["owner"],raw[seed],seed,source,
                                      e4.K_ACTIVE,index,before_patch)
        control_contact=contact_probe(control["owner"],raw[seed],seed,source,
                                      0.,index,before_patch)
        cases[seed]={"active_eroded":active,"no_erosion":control,
                     "index":index,"patch_delta_z":delta,
                     "active_contact":active_contact,
                     "control_contact":control_contact}
        ray_delta=(active_contact["bullet_ray_height_m_nominal"]-
                   control_contact["bullet_ray_height_m_nominal"])
        first_a=active_contact["first_positive_terrain_contact"]
        first_b=control_contact["first_positive_terrain_contact"]
        gate(f"{seed}_soil_change",active["changed_soil_cells"]>0
             and control["changed_soil_cells"]==0
             and control["exported_soil_kg"]==0.)
        gate(f"{seed}_closed_joint_ledger",active["peak_mass_residual_kg"]<=.09216
             and control["peak_mass_residual_kg"]<=.09216)
        gate(f"{seed}_erosion_changes_local_patch",abs(delta)>.005)
        gate(f"{seed}_rays_match_derived_ground",
             active_contact["ray_height_error_m_nominal"]<.001
             and control_contact["ray_height_error_m_nominal"]<.001
             and abs(ray_delta-delta)<.001)
        gate(f"{seed}_physical_contact_exists",first_a is not None and first_b is not None
             and active_contact["positive_contact_events"]>0
             and control_contact["positive_contact_events"]>0
             and active_contact["worst_penetration_m_nominal"]>=-.05
             and control_contact["worst_penetration_m_nominal"]>=-.05)
        if first_a is not None and first_b is not None:
            first_delta=(first_a["terrain_xyz_m_nominal"][2]-
                         first_b["terrain_xyz_m_nominal"][2])
            gate(f"{seed}_first_contact_follows_changed_soil",
                 first_delta*delta>0. and abs(first_delta)>=.003
                 and abs(first_delta-delta)<=.03)
    one=cases[7321]
    repeat=erode(raw[7321],7321,bullet4.SOURCE_HASH[7321],e4.K_ACTIVE)
    patch_index=one["index"]
    patch_before=one["no_erosion"]["final_terrain"][patch_index[0]:patch_index[0]+2,
                                                 patch_index[1]:patch_index[1]+2]
    repeated_contact=contact_probe(repeat["owner"],raw[7321],7321,
                    bullet4.SOURCE_HASH[7321],e4.K_ACTIVE,patch_index,patch_before)
    original=one["active_contact"]
    gate("bit_identical_replay",
         repeat["exported_soil_kg"]==one["active_eroded"]["exported_soil_kg"]
         and repeat["changed_soil_cells"]==one["active_eroded"]["changed_soil_cells"]
         and np.array_equal(repeat["owner"]["soil_mass_kg"].values,
                            one["active_eroded"]["owner"]["soil_mass_kg"].values)
         and repeated_contact["joint_owner_sha256"]==original["joint_owner_sha256"]
         and repeated_contact["first_positive_terrain_contact"]==
             original["first_positive_terrain_contact"])
    rejected=rejected_states(original["owner"],raw[7321],7321,
                          bullet4.SOURCE_HASH[7321],e4.K_ACTIVE)
    with tempfile.TemporaryDirectory(prefix="world_h31_") as td:
        path=pathlib.Path(td)/"joint_soil_gravity_owner.nc"
        original["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:
            loaded=f.load()
        validate_joint(loaded,raw[7321],7321,bullet4.SOURCE_HASH[7321],
                       e4.K_ACTIVE)
        gate("joint_checkpoint_exact",owner_hash(loaded)==original["joint_owner_sha256"])
        saved=path.stat().st_size
    def public_case(s):
        return {
            "seed":s["active_eroded"]["source_seed"],
            "patch_index":list(s["index"]),
            "physical_soil_height_change_m_nominal":s["patch_delta_z"],
            "active_soil_export_kg":s["active_eroded"]["exported_soil_kg"],
            "control_soil_export_kg":s["no_erosion"]["exported_soil_kg"],
            "peak_active_mass_residual_kg":s["active_eroded"]["peak_mass_residual_kg"],
            "soil_cells_changed":s["active_eroded"]["changed_soil_cells"],
            "active_contact":{k:v for k,v in s["active_contact"].items() if k!="owner"},
            "control_contact":{k:v for k,v in s["control_contact"].items() if k!="owner"},
        }
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"E5 H31 one-way erosion->surface->rigid contact via one material owner",
        "python":platform.python_version(),"landlab":landlab.__version__,
        "pybullet":version("pybullet"),"numpy":np.__version__,
        "xarray":xr.__version__,"source_worldengine_SHA":upstream,
        "source_units":"arbitrary -> m_nominal 0..50, NOT calibrated",
        "seed_7321":public_case(cases[7321]),"seed_8128":public_case(cases[8128]),
        "soil_initial_kg":e4.MASS0,"rigid_body_kg":BODY_MASS,
        "total_world_plus_export_initial_kg":e4.MASS0+BODY_MASS,
        "native_erosion_steps":EROSION_STEPS,"native_rigid_steps":CONTACT_STEPS,
        "two_separate_solver_clocks":True,
        "one_way_coupling_only":True,
        "negative_owner_states_rejected":rejected,
        "bit_identical_replay":True,"netcdf_bytes":saved,
        "failed_preregistered_gates":fail,
        "limitations":"Owner includes rigid reservoir from t0; release is a prescribed boundary event after erosion. Bullet contacts eroded owner-derived static terrain but does NOT feed forces back to soil. No common calibrated clock, no coupled water/heat/energy or autonomous continuous world."
    },sort_keys=True),flush=True)
    if fail:
        raise AssertionError("H31 preregistered gates failed: "+", ".join(fail))

if __name__=="__main__":
    main(sys.argv[1])
