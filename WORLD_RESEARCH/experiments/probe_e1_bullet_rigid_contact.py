"""H7: verify EXISTING PyBullet rigid gravity/contact with one xarray owner.

No physics implemented in this file: steps and collisions are Bullet's APIs.
No translation from voxel fields to free-form meshes is attempted.
Material amount and composition are owned only by the Dataset;
Bullet owns kinematics while running, and observations are read out.

Protocol: ETAPA_1_H7_PROTOCOLO_RIGID_CONTACT_BULLET.md
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

DT = 1.0 / 240.0
STEPS = 480
START_CENTER_Z_M = 3.0
SIDE_M = 1.0
BODY_NAME = "cube_0"
MATERIALS = ("A", "B")
DENSITIES_KG_M3 = (2.0, 1.0)


def material_owner():
    """One canonical amount per species; shape & capacity declared in meters."""
    return xr.Dataset(
        data_vars={
            "material_mass":(
                ("material", "body"),
                np.array([[2.0], [0.0]], dtype=np.float64),
                {"units": "kg", "owner": "canonical_material_inventory"},
            ),
            "material_density":(
                ("material",),
                np.asarray(DENSITIES_KG_M3, dtype=np.float64),
                {"units": "kg m-3", "note": "effective input properties"},
            ),
        },
        coords={"material": list(MATERIALS), "body": [BODY_NAME]},
        attrs={
            "schema_version": 1,
            "cube_side_m": SIDE_M,
            "geometry_volume_m3": SIDE_M ** 3,
            "system": "rigid single-cube, floor as external geometric boundary",
            "note": "Bullet receives a cached body mass, not ownership of material inventory",
        },
    )


def validate_owner(ds):
    if ds.coords["material"].values.tolist() != list(MATERIALS):
        raise ValueError("Unexpected material labels")
    if ds.coords["body"].values.tolist() != [BODY_NAME]:
        raise ValueError("Unexpected body identity")
    if tuple(ds["material_mass"].dims) != ("material", "body"):
        raise ValueError("Unexpected mass dimensions")
    if tuple(ds["material_density"].dims) != ("material",):
        raise ValueError("Unexpected density dimensions")
    if ds["material_mass"].attrs.get("units") != "kg":
        raise ValueError("Material mass units invalid")
    if ds["material_density"].attrs.get("units") != "kg m-3":
        raise ValueError("Material density units invalid")
    if ds.attrs.get("schema_version") != 1:
        raise ValueError("Unrecognized inventory schema")
    mass = ds["material_mass"].values
    densities = ds["material_density"].values
    side = float(ds.attrs["cube_side_m"])
    volume = float(ds.attrs["geometry_volume_m3"])
    if not (
        np.isfinite(mass).all()
        and np.isfinite(densities).all()
        and math.isfinite(side)
        and math.isfinite(volume)
    ):
        raise ValueError("Nonfinite mass, density or geometry")
    if np.any(mass < 0) or np.any(densities <= 0) or side <= 0 or volume <= 0:
        raise ValueError("Negative material or nonpositive geometry or density")
    if not math.isclose(side**3, volume, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Geometric volume inconsistent with side length")
    occupancy = float(np.sum(mass[:, 0] / densities))
    if occupancy > volume + 1e-12:
        raise ValueError("Material exceeds rigid body volume")
    if occupancy < volume - 1e-12:
        raise ValueError("Test body does not fill declared rigid shape")
    total = float(np.sum(mass))
    if total <= 0:
        raise ValueError("Body has zero material")
    return {
        "body_mass_kg": total,
        "geometric_volume_m3": volume,
        "occupied_volume_m3": occupancy,
        "bulk_density_derived_kg_m3": total / volume,
        "material_inventory_kg": {
            name: float(mass[i, 0]) for i, name in enumerate(MATERIALS)
        },
    }


def owner_hash(ds):
    return hashlib.sha256(
        ds["material_mass"].values.tobytes()
        + ds["material_density"].values.tobytes()
    ).hexdigest()


def negative_cases(owner):
    def negative(a):
        a["material_mass"].values[0, 0] = -1.0

    def invalid_density(a):
        a["material_density"].values[0] = 0.0

    def excess_volume(a):
        a["material_mass"].values[1, 0] = 0.1

    def invalid_mass_unit(a):
        a["material_mass"].attrs["units"] = "g"

    results = {}
    initial = owner_hash(owner)
    for name, operation in (
        ("negative_mass", negative),
        ("zero_density", invalid_density),
        ("over_capacity", excess_volume),
        ("invalid_mass_unit", invalid_mass_unit),
    ):
        invalid = owner.copy(deep=True)
        operation(invalid)
        try:
            validate_owner(invalid)
        except ValueError:
            results[name] = True
        else:
            results[name] = False
        assert results[name], f"Invalid material state accepted: {name}"
        assert owner_hash(owner) == initial, "Corruption mutated canonical owner"
    return results


def scene(ds, g_mps2=-9.81, with_floor=True):
    material = validate_owner(ds)
    before = owner_hash(ds)
    cid = p.connect(p.DIRECT)
    if cid < 0:
        raise RuntimeError("PyBullet DIRECT not available")
    try:
        p.setPhysicsEngineParameter(
            fixedTimeStep=DT, numSolverIterations=50,
            deterministicOverlappingPairs=1, physicsClientId=cid
        )
        p.setGravity(0, 0, g_mps2, physicsClientId=cid)
        ground = None
        if with_floor:
            ground_shape = p.createCollisionShape(
                p.GEOM_PLANE, planeNormal=[0, 0, 1], physicsClientId=cid
            )
            ground = p.createMultiBody(
                baseMass=0.0, baseCollisionShapeIndex=ground_shape,
                basePosition=[0, 0, 0], physicsClientId=cid
            )

        collider = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[SIDE_M / 2.0] * 3,
            physicsClientId=cid
        )
        body = p.createMultiBody(
            baseMass=material["body_mass_kg"],
            baseCollisionShapeIndex=collider,
            basePosition=[0, 0, START_CENTER_Z_M],
            physicsClientId=cid
        )
        p.changeDynamics(
            body, -1,
            restitution=0.0,
            lateralFriction=0.5,
            linearDamping=0.0,
            angularDamping=0.0,
            physicsClientId=cid
        )
        cached_mass = float(p.getDynamicsInfo(body, -1, physicsClientId=cid)[0])
        assert math.isclose(cached_mass, material["body_mass_kg"], abs_tol=1e-12)
        sampled = []
        start = time.perf_counter()
        for i in range(STEPS):
            p.stepSimulation(physicsClientId=cid)
            if i in (0, 119, 239, 359, STEPS - 1):
                pos, _ = p.getBasePositionAndOrientation(body, physicsClientId=cid)
                vel, _ = p.getBaseVelocity(body, physicsClientId=cid)
                sampled.append([float((i + 1) * DT), float(pos[2]), float(vel[2])])
        elapsed = time.perf_counter() - start
        pos, _ = p.getBasePositionAndOrientation(body, physicsClientId=cid)
        vel, _ = p.getBaseVelocity(body, physicsClientId=cid)
        contacts = (
            p.getContactPoints(bodyA=body, bodyB=ground, physicsClientId=cid)
            if ground is not None else ()
        )
        arr = np.asarray(sampled, dtype=np.float64)
        # Observations are NOT kinematic owner and contain NO repeated material.
        observations = xr.Dataset(
            {"z":(("sample",),arr[:,1],{"units":"m"}),
             "vertical_velocity":(("sample",),arr[:,2],{"units":"m s-1"})},
            coords={"sample":np.arange(len(arr)), "sim_time_s":(("sample",),arr[:,0])},
            attrs={"role":"read_only_solver_observation", "physics":"pybullet DIRECT"}
        )
        assert np.isfinite(arr).all()
        assert owner_hash(ds) == before, "Solver silently changed inventory"
        assert validate_owner(ds) == material
        return {
            "gravity_mps2":g_mps2,
            "floor_present":with_floor,
            "final_center_z_m":float(pos[2]),
            "final_velocity_z_m_s":float(vel[2]),
            "contact_count_last_step":len(contacts),
            "cached_bullet_mass_kg":cached_mass,
            "canonical_material_mass_kg":material["body_mass_kg"],
            "owner_inventory_unchanged":True,
            "step_elapsed_seconds":round(elapsed,6),
            "samples_time_z_vz":arr.tolist(),
            "observation_dataset":observations,
        }
    finally:
        p.disconnect(physicsClientId=cid)


def main():
    owner = material_owner()
    properties = validate_owner(owner)
    invalid = negative_cases(owner)
    before = owner_hash(owner)
    with_ground = scene(owner, -9.81, True)
    zero_gravity = scene(owner, 0.0, True)
    freefall = scene(owner, -9.81, False)
    replay = scene(owner, -9.81, True)

    assert with_ground["final_center_z_m"] >= 0.45
    assert with_ground["final_center_z_m"] <= 0.60
    assert START_CENTER_Z_M - with_ground["final_center_z_m"] > 2.0
    assert with_ground["contact_count_last_step"] > 0
    assert abs(with_ground["final_velocity_z_m_s"]) < 0.1
    assert abs(zero_gravity["final_center_z_m"] - START_CENTER_Z_M) < 1e-9
    assert abs(zero_gravity["final_velocity_z_m_s"]) < 1e-9
    assert zero_gravity["contact_count_last_step"] == 0
    assert freefall["final_center_z_m"] < -10.
    assert freefall["contact_count_last_step"] == 0
    assert with_ground["samples_time_z_vz"] == replay["samples_time_z_vz"]
    assert with_ground["contact_count_last_step"] == replay["contact_count_last_step"]
    assert owner_hash(owner) == before

    path=pathlib.Path("/tmp/e1_h7_material_owner.nc")
    owner.to_netcdf(path, engine="scipy")
    with xr.open_dataset(path, engine="scipy") as source:
        restored=source.load()
    assert validate_owner(restored)==properties
    assert owner_hash(restored)==before

    def public_case(data):
        return {key:value for key,value in data.items() if key!="observation_dataset"}

    report={
        "test":"E1 H7 existing Bullet rigid contact and gravity with single xarray inventory owner",
        "pybullet_distribution_version":version("pybullet"),
        "python_version":platform.python_version(),
        "xarray_version":xr.__version__,
        "dt_s":DT,
        "steps":STEPS,
        "body_materials":properties,
        "owner_sha256_before_after_identical":True,
        "rejected_invalid_material_cases":invalid,
        "with_ground":public_case(with_ground),
        "zero_gravity_control":public_case(zero_gravity),
        "no_ground_control":public_case(freefall),
        "replay_bitwise_equal_observed_samples":True,
        "netcdf_material_owner_exact":True,
        "netcdf_owner_size_bytes":path.stat().st_size,
        "physics_written_by_us":False,
        "limit":"One 1m rigid cube and abstract geometric floor. Body shape and material quantities imported, NOT voxel dynamics. Bullet is the exclusive kinematic solver, xarray only material inventory owner. No deformable materials, granular sediment, temperature, conservation of dissipated mechanical energy or 3D cavities evolving. Python3.11 compatibility only."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))


if __name__ == "__main__":
    main()
