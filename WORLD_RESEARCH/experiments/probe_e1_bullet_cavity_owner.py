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
import time
from importlib.metadata import version

import numpy as np
import xarray as xr
import pybullet as p

from probe_e1_surface_volume_partition import (
    make_state, derive_heights, validate, totals,
    X0, Y0, MATERIALS,
)

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


def scenario_owner():
    full=make_state()
    assert totals(full)==BASE_INVENTORY
    hollow=full.copy(deep=True)
    voxel=hollow["roi_voxel_mass"].values
    assert np.all(voxel[0,2:4,2:4,2:6]==2.)
    assert np.all(voxel[1,2:4,2:4,2:6]==0.)
    removed=float(voxel[0,2:4,2:4,2:6].sum())
    assert removed==32.
    voxel[0,2:4,2:4,2:6]=0.
    hollow=hollow.assign_coords(rigid_body=["excavated_A_cube"])
    hollow["rigid_body_mass"]=(
        ("material","rigid_body"),
        np.array([[2.0],[0.0]],dtype=np.float64),
        {"units":"kg","owner":"one material body transferred from removed cavity stock"}
    )
    hollow.attrs["external_sinks_A_kg"]=removed-2.0
    hollow.attrs["rigid_body_cube_side_m"]=CUBE_SIDE_M
    check_ledger(hollow)
    assert np.array_equal(derive_heights(hollow),derive_heights(full))
    return full,hollow


def check_ledger(ds):
    expected_static={"A":730.,"B":3.}
    validate(ds,expected_static)
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
    static=totals(ds)
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
            "mobile_mass_cached_kg":bullet_mass,
            "inventories_unchanged":True,
            "elapsed_step_seconds":round(elapsed,6),
            "sampled_time_z_vz":samples,
        }
    finally:
        p.disconnect(physicsClientId=cid)


def main():
    full,ds=scenario_owner()
    assert not placement_is_empty(full), "Solid world should not allow cube placement"
    assert placement_is_empty(ds), "Voided world should allow cube placement"
    assert np.array_equal(derive_heights(ds),derive_heights(full))
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
    assert CUBE_EXPECTED_REST_Z-.05<=with_gravity["final_center_z_m"]<=CUBE_EXPECTED_REST_Z+.10
    assert abs(with_gravity["final_vertical_velocity_m_s"])<.1
    assert with_gravity["total_contacts_last_step"]>0
    assert with_gravity["cavity_floor_contact_count"]>0
    assert abs(no_gravity["final_center_z_m"]-CUBE_START[2])<1e-9
    assert no_gravity["total_contacts_last_step"]==0
    assert with_gravity["sampled_time_z_vz"]==replay["sampled_time_z_vz"]
    assert with_gravity["total_contacts_last_step"]==replay["total_contacts_last_step"]
    assert canonical_hash(ds)==base

    path=pathlib.Path("/tmp/e1_h8_cavity_and_body_owner.nc")
    ds.to_netcdf(path,engine="scipy")
    with xr.open_dataset(path,engine="scipy") as f:
        restored=f.load()
    assert check_ledger(restored)==ledger
    assert canonical_hash(restored)==base
    assert np.array_equal(derive_heights(restored),derive_heights(full))
    assert placement_is_empty(restored)

    report={
        "test":"E1 H8 Bullet 3D contact INSIDE cavity that heightfield cannot represent",
        "python_version":platform.python_version(),
        "pybullet_version":version("pybullet"),
        "xarray_version":xr.__version__,
        "dt_s":DT,"steps":STEPS,
        "same_visible_heightfield_full_and_hollow":True,
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
    main()
