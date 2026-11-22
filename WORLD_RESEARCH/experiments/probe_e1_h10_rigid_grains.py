"""E1/H10: collective 3D rigid grains with *existing* PyBullet physics.

A scoped falsifiable test of grain-grain contact, not a continuum granular
solver, geological fracture model, autonomous world, or a novel physical law.
Protocol: WORLD_RESEARCH/ETAPA_1_H10_PROTOCOLO_GRANOS_RIGIDOS.md.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
from importlib.metadata import version

import numpy as np
import pybullet as p
import xarray as xr

N = 27
MASS_KG = 0.25
RADIUS_M = 0.1
GRAVITY_M_S2 = -9.81
DT = 1.0 / 240.0
STEPS = 720
SAMPLES = (119, 239, 359, 479, 599, 719)


def make_owner():
    return xr.Dataset(
        data_vars={"material_mass_kg": (
            ("material", "grain"), np.full((1, N), MASS_KG, dtype=np.float64),
            {"units": "kg", "owner": "only_material_inventory"}
        )},
        coords={"material": ["A"], "grain": [f"grain_{i:02d}" for i in range(N)]},
        attrs={"schema_version": 1, "sphere_radius_m": RADIUS_M,
               "description": "27 abstract rigid grains; Bullet caches mass, owns kinematics"},
    )


def check_owner(ds):
    if tuple(ds.data_vars) != ("material_mass_kg",):
        raise ValueError("Unexpected inventory fields")
    if tuple(ds["material_mass_kg"].dims) != ("material", "grain"):
        raise ValueError("Inventory dimension mismatch")
    if ds.coords["material"].values.tolist() != ["A"] or ds.coords["grain"].values.tolist() != [
        f"grain_{i:02d}" for i in range(N)
    ]:
        raise ValueError("Material or grain identities invalid")
    if ds["material_mass_kg"].attrs.get("units") != "kg" or ds.attrs.get("schema_version") != 1:
        raise ValueError("Unit or schema invalid")
    r = float(ds.attrs.get("sphere_radius_m", math.nan))
    if not math.isfinite(r) or r != RADIUS_M:
        raise ValueError("Geometry altered")
    arr = ds["material_mass_kg"].values
    if arr.shape != (1, N) or not np.isfinite(arr).all() or np.any(arr <= 0.0):
        raise ValueError("Nonpositive or nonfinite material mass")
    if not np.array_equal(arr, np.full((1, N), MASS_KG)):
        raise ValueError("External source or sink not authorized")
    return float(np.sum(arr))


def owner_hash(ds):
    return hashlib.sha256(ds["material_mass_kg"].values.tobytes()).hexdigest()


def initial_positions():
    loc = []
    for k in range(3):
        dx, dy = ((0.045, 0.025) if k == 1 else (0.0, 0.0))
        for i in range(3):
            for j in range(3):
                loc.append([-0.24+0.24*i+dx, -0.24+0.24*j+dy, 0.85+0.24*k])
    v = np.asarray(loc, dtype=np.float64)
    assert v.shape == (N, 3)
    d = v[:, None, :] - v[None, :, :]
    ds = np.linalg.norm(d, axis=2) + np.eye(N)*1000
    assert np.min(ds) > 2*RADIUS_M, "Initial bodies interpenetrate"
    return v


def reject_bad_owners(ds):
    pre = owner_hash(ds)
    rejected = {}
    def fails(name, patch):
        candidate = ds.copy(deep=True)
        patch(candidate)
        try:
            check_owner(candidate)
        except ValueError:
            rejected[name] = True
        else:
            raise AssertionError("Invalid owner accepted: "+name)
        assert owner_hash(ds) == pre
    fails("negative_mass", lambda x: x["material_mass_kg"].values.__setitem__((0, 0), -0.1))
    fails("unauthorized_mass", lambda x: x["material_mass_kg"].values.__setitem__((0, 0), 0.3))
    fails("wrong_mass_unit", lambda x: x["material_mass_kg"].attrs.__setitem__("units", "g"))
    fails("wrong_radius", lambda x: x.attrs.__setitem__("sphere_radius_m", 0))
    fails("altered_identity", lambda x: x.coords["grain"].values.__setitem__(0, "bogus"))
    return rejected


def scene(ds, gravity=True, ground=True):
    total = check_owner(ds)
    source_hash = owner_hash(ds)
    initial = initial_positions()
    cid = p.connect(p.DIRECT)
    if cid < 0:
        raise RuntimeError("DIRECT Bullet engine unavailable")
    try:
        p.setPhysicsEngineParameter(
            fixedTimeStep=DT, numSolverIterations=50,
            deterministicOverlappingPairs=1, physicsClientId=cid,
        )
        p.setGravity(0, 0, GRAVITY_M_S2 if gravity else 0.0, physicsClientId=cid)
        floor_id = None
        if ground:
            floor_shape = p.createCollisionShape(
                p.GEOM_PLANE, planeNormal=[0, 0, 1], physicsClientId=cid
            )
            floor_id = p.createMultiBody(
                baseMass=0, baseCollisionShapeIndex=floor_shape, physicsClientId=cid
            )
            p.changeDynamics(
                floor_id, -1, lateralFriction=0.6, restitution=0,
                physicsClientId=cid,
            )
        sphere_shape = p.createCollisionShape(
            p.GEOM_SPHERE, radius=RADIUS_M, physicsClientId=cid
        )
        grains = []
        for idx, pos in enumerate(initial):
            bid = p.createMultiBody(
                baseMass=float(ds["material_mass_kg"].values[0, idx]),
                baseCollisionShapeIndex=sphere_shape,
                basePosition=pos.tolist(), physicsClientId=cid
            )
            p.changeDynamics(
                bid, -1, lateralFriction=0.6, restitution=0.0,
                linearDamping=0.0, angularDamping=0.0,
                physicsClientId=cid
            )
            assert float(p.getDynamicsInfo(bid, -1, physicsClientId=cid)[0]) == MASS_KG
            grains.append(bid)
        known = set(grains)
        floor_force_steps = grain_force_steps = 0
        peak_grain_contacts = 0
        sample_values = []
        for step in range(STEPS):
            p.stepSimulation(physicsClientId=cid)
            cps = p.getContactPoints(physicsClientId=cid)
            ff = sum(1 for c in cps if (c[1] in known and c[2] == floor_id
                                     or c[2] in known and c[1] == floor_id)
                     and c[9] > 1e-8) if floor_id is not None else 0
            gf = sum(1 for c in cps if c[1] in known and c[2] in known and c[9] > 1e-8)
            floor_force_steps += int(ff > 0)
            grain_force_steps += int(gf > 0)
            peak_grain_contacts = max(peak_grain_contacts, gf)
            if step in SAMPLES:
                sampled_pos = np.asarray(
                    [p.getBasePositionAndOrientation(b, physicsClientId=cid)[0]
                     for b in grains], dtype=np.float64
                )
                sampled_vel = np.asarray(
                    [p.getBaseVelocity(b, physicsClientId=cid)[0]
                     for b in grains], dtype=np.float64
                )
                sample_values.extend(sampled_pos.ravel().tolist())
                sample_values.extend(sampled_vel.ravel().tolist())
        final = np.asarray(
            [p.getBasePositionAndOrientation(b, physicsClientId=cid)[0]
             for b in grains], dtype=np.float64,
        )
        assert np.isfinite(final).all()
        pairdist = np.linalg.norm(final[:, None, :] - final[None, :, :], axis=2) + np.eye(N)*1000
        lateral = np.linalg.norm((final-initial)[:, :2], axis=1)
        assert owner_hash(ds) == source_hash and check_owner(ds) == total
        return {
            "gravity": bool(gravity), "floor": bool(ground),
            "grain_count": N, "material_inventory_kg": total,
            "center_of_mass_start_z_m": float(initial[:,2].mean()),
            "center_of_mass_end_z_m": float(final[:,2].mean()),
            "min_final_center_z_m": float(final[:,2].min()),
            "min_final_center_separation_m": float(pairdist.min()),
            "max_lateral_displacement_m": float(lateral.max()),
            "max_initial_final_position_abs_m": float(np.max(np.abs(final-initial))),
            "positive_floor_force_steps": floor_force_steps,
            "positive_grain_contact_steps": grain_force_steps,
            "peak_grain_contact_count": peak_grain_contacts,
            "sample_sha256": hashlib.sha256(
                np.asarray(sample_values, dtype=np.float64).tobytes()
            ).hexdigest(),
            "sample_values": sample_values,
            "material_owner_unchanged": True,
        }
    finally:
        p.disconnect(physicsClientId=cid)


def main():
    ds = make_owner()
    mass = check_owner(ds)
    h = owner_hash(ds)
    rejected = reject_bad_owners(ds)
    active = scene(ds, gravity=True, ground=True)
    no_g = scene(ds, gravity=False, ground=True)
    no_floor = scene(ds, gravity=True, ground=False)
    replay = scene(ds, gravity=True, ground=True)

    assert mass == N*MASS_KG == 6.75
    assert active["center_of_mass_start_z_m"] - active["center_of_mass_end_z_m"] > 0.4
    assert active["min_final_center_z_m"] >= 0.08
    assert active["positive_floor_force_steps"] > 0
    assert active["positive_grain_contact_steps"] > 0
    assert active["max_lateral_displacement_m"] > 0.01
    assert active["min_final_center_separation_m"] >= 0.18

    assert no_g["max_initial_final_position_abs_m"] < 1e-9
    assert no_g["positive_floor_force_steps"] == 0
    assert no_g["positive_grain_contact_steps"] == 0
    assert no_floor["center_of_mass_end_z_m"] < -5.0
    assert no_floor["positive_floor_force_steps"] == 0
    assert no_floor["max_lateral_displacement_m"] < 1e-9

    assert active["sample_values"] == replay["sample_values"]
    assert active["positive_grain_contact_steps"] == replay["positive_grain_contact_steps"]
    assert active["positive_floor_force_steps"] == replay["positive_floor_force_steps"]
    assert owner_hash(ds) == h
    report = {
        "test": "E1 H10 emergent rigid-grain 3D contact test, not soil deformation",
        "pybullet_version": version("pybullet"),
        "python": platform.python_version(), "xarray_version": xr.__version__,
        "steps": STEPS, "dt_s": DT, "radius_m": RADIUS_M,
        "per_grain_mass_kg": MASS_KG, "inventory_initial_final_kg": mass,
        "owner_sha256": h, "invalid_state_rejections": rejected,
        "active": {k:v for k,v in active.items() if k!="sample_values"},
        "zero_gravity": {k:v for k,v in no_g.items() if k!="sample_values"},
        "no_floor": {k:v for k,v in no_floor.items() if k!="sample_values"},
        "replay_exact": True, "solver_physics_written_locally": False,
        "limitations": "27 rigid spheres only, no constitutive granular stress, no true deformable rock/soil, no thermal budget, no calibrated angle of repose, no persistence of Bullet velocities."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
