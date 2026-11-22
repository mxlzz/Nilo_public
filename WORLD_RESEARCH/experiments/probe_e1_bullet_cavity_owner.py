"""E1/H8: original H5 voxel ROI supplies Bullet's rigid collision geometry.

No physics implemented: Bullet resolves gravity/contact. A material-owned cube
is reallocated from a prescribed cavity excavation; the remaining removed
mass is an explicit external sink. Both still follow a single xarray dataset.

The cube is placed *inside* an enclosed void; same heightfield filled
columns would make its initial placement invalid. This is a test of contact
relevance, not emergence or excavation physics.

Prerecorded protocol: ETAPA_1_H8_PROTOCOLO_CAVIDAD_CONTACTO.md.
"""
from __future__ import annotations
import hashlib
import json
import math
import pathlib
import platform
import sys
import time
from importlib.metadata import version

import numpy as np
import xarray as xr
import pybullet as p

# The producer runs H5/Landlab in Python3.13. This consumer uses only
# the verified NetCDF, in Python3.11 with Bullet; no Landlab imported.
X0,Y0=2,1
W,H,Z=12,8,7
MATERIALS=("A","B")

def static_totals(ds):
    a=ds["outside_column_mass"].values
    b=ds["roi_voxel_mass"].values
    return {name:float(a[i].sum()+b[i].sum()) for i,name in enumerate(MATERIALS)}

def surface_heights(ds):
    """Geometric verification of data-only interface; no simulation."""
    d=ds["material_density"].values
    elev=(ds["outside_column_mass"].values/d[:,None,None]).sum(axis=0)
    occ=(ds["roi_voxel_mass"].values/d[:,None,None,None]).sum(axis=0)>0
    roof=np.where(occ,np.arange(Z)[:,None,None]+1,0).max(axis=0)
    ys=ds.coords["roi_y"].values.astype(int)
    xs=ds.coords["roi_x"].values.astype(int)
    elev[np.ix_(ys,xs)]=roof
    return elev

DT=1.0/240.0
STEPS=360
CUBE_SIDE_M=1.0
CUBE_START=(5.5,3.5,3.4)
CUBE_EXPECTED_REST_Z=2.5
BASE_INVENTORY={"A":762.0, "B":3.0}


def canonical_hash(ds):
    return hashlib.sha256(
        ds["outside_column_mass"].values.tobytes()
        + ds["roi_voxel_mass"].values.tobytes()
        + ds["rigid_body_mass"].values.tobytes()
        + json.dumps(ds.attrs["external_sinks_A_kg"]).encode()
    ).hexdigest()


def load_owner(folder):
    file=folder/"h8_material_owner.nc"
    manifest=json.loads((folder/"h8_manifest.json").read_text())
    if hashlib.sha256(file.read_bytes()).hexdigest()!=manifest["netcdf_file_sha256"]:
        raise ValueError("NetCDF source hash mismatch")
    with xr.open_dataset(file,engine="scipy") as opened:
        ds=opened.load()
    if canonical_hash(ds)!=manifest["owner_sha256"]:
        raise ValueError("Material owner hash differs across Python versions")
    if hashlib.sha256(surface_heights(ds).tobytes()).hexdigest()!=manifest["heightfield_sha256"]:
        raise ValueError("Height projections disagree across Python versions")
    for key in ("original_height_equals_hollow",
                "full_world_body_initial_position_blocked",
                "hollow_world_body_initial_position_clear"):
        if manifest[key] is not True:
            raise ValueError("Producer geometric control failed: "+key)
    return ds,manifest

def check_ledger(ds):
    expected_static={"A":730.,"B":3.}
    if tuple(ds["outside_column_mass"].dims)!=("material","y","x") or tuple(ds["roi_voxel_mass"].dims)!=("material","z","roi_y","roi_x"):
        raise ValueError("Unexpected tensor dimensions")
    if ds["outside_column_mass"].attrs.get("units")!="kg" or ds["roi_voxel_mass"].attrs.get("units")!="kg":
        raise ValueError("Material units invalid")
    if ds["material_density"].attrs.get("units")!="kg m-3":
        raise ValueError("Density units invalid")
    if ds.attrs.get("schema_version")!=1:
        raise ValueError("Owner version unknown")
    if ds.coords["roi_x"].values.tolist()!=list(range(2,10)) or ds.coords["roi_y"].values.tolist()!=list(range(1,7)):
        raise ValueError("ROI coordinate order differs")
    mask=ds["region_is_volume"].values
    expected_mask=np.zeros((H,W),dtype=bool)
    expected_mask[1:7,2:10]=True
    if not np.array_equal(mask,expected_mask):
        raise ValueError("Owner ROI mask invalid")
    outside=ds["outside_column_mass"].values
    voxel=ds["roi_voxel_mass"].values
    density=ds["material_density"].values
    if outside.shape!=(2,H,W) or voxel.shape!=(2,Z,6,8):
        raise ValueError("Material shape invalid")
    if not all(np.isfinite(x).all() for x in (outside,voxel,density)):
        raise ValueError("Nonfinite material")
    if np.any(outside<0) or np.any(voxel<0) or np.any(density<=0):
        raise ValueError("Negative mass or invalid density")
    if np.any(outside[:,mask]!=0):
        raise ValueError("Surface and voxel states both own ROI matter")
    if np.any(outside[1]!=0):
        raise ValueError("Invalid exterior material composition")
    if np.any((voxel/density[:,None,None,None]).sum(axis=0)>1.+1e-12):
        raise ValueError("Material exceeds voxel capacity")
    if static_totals(ds)!=expected_static:
        raise ValueError("Static material count changed")
    if ds["rigid_body_mass"].attrs.get("units")!="kg":
        raise ValueError("rigid body unit invalid")
    material_names=ds.coords["material"].values.tolist()
    if material_names!=list(MATERIALS):
        raise ValueError("bad material coordinate order")
    mobile=ds["rigid_body_mass"].values
    if mobile.shape!=(2,1) or not np.isfinite(mobile).all() or (mobile<0).any():
        raise ValueError("invalid mobile material")
    if float(mobile[0,0])!=2.0 or float(mobile[1,0])!=0:
        raise ValueError("wrong mobile material provenance")
    if float(ds.attrs["rigid_body_cube_side_m"])!=CUBE_SIDE_M:
        raise ValueError("wrong mobile volume")
    source_volume=float(mobile[0,0])/float(ds["material_density"].values[0])
    if source_volume!=CUBE_SIDE_M**3:
        raise ValueError("mobile rigid geometry incompatible with source material")
    sink=float(ds.attrs.get("external_sinks_A_kg",float("nan")))
    if not math.isfinite(sink) or sink<0:
        raise ValueError("invalid sink ledger")
    static=static_totals(ds)
    if not math.isclose(static["A"]+float(mobile[0,0])+sink,
                        BASE_INVENTORY["A"],rel_tol=0,abs_tol=1e-10):
        raise ValueError("A stock duplicated or disappeared")
    if not math.isclose(static["B"]+float(mobile[1,0]),
                        BASE_INVENTORY["B"],rel_tol=0,abs_tol=1e-10):
        raise ValueError("B stock changed")
    return {
        "original":{"A":BASE_INVENTORY["A"],"B":BASE_INVENTORY["B"]},
        "remaining_static":static,
        "mobile":{"A":float(mobile[0,0]),"B":float(mobile[1,0])},
        "external_sink_A_kg":sink,
    }


def voxel_occupancy(ds):
    raw=ds["roi_voxel_mass"].values
    density=ds["material_density"].values
    occupancy=(raw/density[:,None,None,None]).sum(axis=0)
    if np.any(occupancy>1+1e-12):
        raise ValueError("voxel material exceeds physical volume")
    return occupancy>0


def placement_is_empty(ds):
    # The cubic body is 1m wide and sits strictly inside the cavity in XY.
    # Its Z span [2.9,3.9] intersects both levels z2 and z3, none occupied.
    filled=voxel_occupancy(ds)
    ix=5-X0
    iy=3-Y0
    return not bool(filled[2,iy,ix] or filled[3,iy,ix])


def execute(ds,gravity):
    report_before=check_ledger(ds)
    initial_hash=canonical_hash(ds)
    ids={}
    cid=p.connect(p.DIRECT)
    assert cid>=0
    try:
        p.setPhysicsEngineParameter(
            fixedTimeStep=DT,
            numSolverIterations=50,
            deterministicOverlappingPairs=1,
            physicsClientId=cid,
        )
        p.setGravity(0,0,gravity,physicsClientId=cid)
        static_shape=p.createCollisionShape(
            p.GEOM_BOX,halfExtents=[.5,.5,.5],physicsClientId=cid
        )
        occupied=voxel_occupancy(ds)
        xs=ds.coords["roi_x"].values
        ys=ds.coords["roi_y"].values
        for iz,iy,ix in np.argwhere(occupied):
            x=int(xs[ix])
            y=int(ys[iy])
            z=int(iz)
            static_id=p.createMultiBody(
                baseMass=0.0,
                baseCollisionShapeIndex=static_shape,
                basePosition=[x+.5,y+.5,z+.5],
                physicsClientId=cid
            )
            ids[static_id]=(x,y,z)
        assert len(ids)==272, "Unexpected ROI static voxel count"
        collision_shape=p.createCollisionShape(
            p.GEOM_BOX,halfExtents=[CUBE_SIDE_M/2]*3,physicsClientId=cid
        )
        mass=float(ds["rigid_body_mass"].values[0,0])
        body=p.createMultiBody(
            baseMass=mass,baseCollisionShapeIndex=collision_shape,
            basePosition=CUBE_START,physicsClientId=cid
        )
        p.changeDynamics(
            body,-1,restitution=0.0,lateralFriction=0.5,
            linearDamping=0.0,angularDamping=0.0,physicsClientId=cid
        )
        bullet_mass=float(p.getDynamicsInfo(body,-1,physicsClientId=cid)[0])
        assert bullet_mass==mass
        samples=[]
        start=time.perf_counter()
        for step in range(STEPS):
            p.stepSimulation(physicsClientId=cid)
            if step in (0,59,119,179,239,STEPS-1):
                pos,_=p.getBasePositionAndOrientation(body,physicsClientId=cid)
                vel,_=p.getBaseVelocity(body,physicsClientId=cid)
                samples.append([float((step+1)*DT),float(pos[2]),float(vel[2])])
        elapsed=time.perf_counter()-start
        pos,_=p.getBasePositionAndOrientation(body,physicsClientId=cid)
        velocity,_=p.getBaseVelocity(body,physicsClientId=cid)
        allcontacts=p.getContactPoints(bodyA=body,physicsClientId=cid)
        support_contacts=[
            c for c in allcontacts if c[2] in ids and ids[c[2]][2]==1
            and ids[c[2]][0]==5 and ids[c[2]][1]==3
        ]
        after=check_ledger(ds)
        assert report_before==after
        assert canonical_hash(ds)==initial_hash, "Physics changed material owner"
        return {
            "gravity_mps2":gravity,
            "static_voxel_colliders":len(ids),
            "final_center_z_m":float(pos[2]),
            "final_vertical_velocity_m_s":float(velocity[2]),
            "total_contacts_last_step":len(allcontacts),
            "cavity_floor_contact_count":len(support_contacts),
            "contact_geometry_debug":[{"static_voxel_xyz":list(ids.get(contact[2],(-1,-1,-1))),
                         "distance_m":float(contact[8]),
                         "normal_on_B_xyz":[float(v) for v in contact[7]],
                         "normal_force_N":float(contact[9])}
                        for contact in allcontacts[:18]],
            "mobile_mass_cached_kg":bullet_mass,
            "inventories_unchanged":True,
            "elapsed_step_seconds":round(elapsed,6),
            "sampled_time_z_vz":samples,
        }
    finally:
        p.disconnect(physicsClientId=cid)


def main(folder):
    ds,manifest=load_owner(folder)
    assert placement_is_empty(ds), "Cavity should contain empty cube placement"
    assert manifest["enclosed_void_voxels"]==16
    base=canonical_hash(ds)
    ledger=check_ledger(ds)
    rejected={}
    for name,operation in (
        ("double_owned_material",
         lambda a:a["roi_voxel_mass"].values.__setitem__((0,2,3-Y0,5-X0),2.)),
        ("missing_external_sink",
         lambda a:a.attrs.__setitem__("external_sinks_A_kg",0.)),
    ):
        candidate=ds.copy(deep=True)
        operation(candidate)
        try:
            check_ledger(candidate)
        except ValueError:
            rejected[name]=True
        else:
            rejected[name]=False
        assert rejected[name], ("invalid case passed",name)
        assert canonical_hash(ds)==base, "Rejected scenario changed owner"

    with_gravity=execute(ds,-9.81)
    no_gravity=execute(ds,0.0)
    replay=execute(ds,-9.81)
    for label,case in (("gravity",with_gravity),("no_gravity",no_gravity),("replay",replay)):
        print("H8_DIAGNOSTIC "+json.dumps({"case":label,"center_z":case["final_center_z_m"],
               "velocity_z":case["final_vertical_velocity_m_s"],
               "contacts":case["contact_geometry_debug"],
               "cavity_floor_contact_count":case["cavity_floor_contact_count"]},sort_keys=True),flush=True)
    assert CUBE_EXPECTED_REST_Z-.05<=with_gravity["final_center_z_m"]<=CUBE_EXPECTED_REST_Z+.10
    assert abs(with_gravity["final_vertical_velocity_m_s"])<.1
    assert with_gravity["total_contacts_last_step"]>0
    assert with_gravity["cavity_floor_contact_count"]>0
    assert abs(no_gravity["final_center_z_m"]-CUBE_START[2])<1e-9
    assert no_gravity["total_contacts_last_step"]==0
    assert with_gravity["sampled_time_z_vz"]==replay["sampled_time_z_vz"]
    assert with_gravity["total_contacts_last_step"]==replay["total_contacts_last_step"]
    assert canonical_hash(ds)==base

    path=folder/"h8_bullet_owner_roundtrip.nc"
    ds.to_netcdf(path,engine="scipy")
    with xr.open_dataset(path,engine="scipy") as f:
        restored=f.load()
    assert check_ledger(restored)==ledger
    assert canonical_hash(restored)==base
    assert np.array_equal(surface_heights(restored),surface_heights(ds))
    assert placement_is_empty(restored)

    report={
        "test":"E1 H8 Bullet 3D contact INSIDE cavity that heightfield cannot represent",
        "python_version":platform.python_version(),
        "pybullet_version":version("pybullet"),
        "xarray_version":xr.__version__,
        "dt_s":DT,"steps":STEPS,
        "same_visible_heightfield_full_and_hollow":manifest["original_height_equals_hollow"],
        "landlab_state_produced_python_version":manifest["python"],
        "bullet_solver_python_version":platform.python_version(),
        "cross_runtime_netcdf_source_sha256":manifest["netcdf_file_sha256"],
        "separate_python_runtime_data_interface":True,
        "enclosed_hole_removed_voxels":16,
        "solid_world_rejects_initial_body_placement":True,
        "hollow_world_accepts_initial_body_placement":True,
        "single_owner_mass_ledger":ledger,
        "invalid_material_state_rejected":rejected,
        "with_gravity":with_gravity,
        "zero_gravity_control":no_gravity,
        "exact_replay":True,
        "netcdf_owner_bytes":path.stat().st_size,
        "netcdf_owner_restored_exactly":True,
        "limit":"Hollow terrain is prescribed. 272 static voxel colliders do not move/deform; no geology, cave formation, fluid, temperature, energy closure, autonomous material exchange or emergence demonstrated. Cannot extrapolate collider count to world scale."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: consumer.py /tmp/h8")
    main(pathlib.Path(sys.argv[1]))
