"""E3 H25: follow the EXACT H24 contact physics longer, without tuning.

H24 CI failed resting/connectedness gates after 1600 steps. This new
preregistered test extends same simulation to 3600 steps, checks H24 prefix
SHA at step1600 and evaluates a new late-time observation window 3000-3600.
"""
from __future__ import annotations

import json
import pathlib
import platform
import tempfile

import numpy as np
import pybullet
import xarray as xr

import probe_e3_h24_granular_pile as h24

STEPS_LATE=3600
SAMPLES_LATE=(1200,1600,3000,3600)
PREFIX_SHA={
    ("active",20261122):"9e249c09b73176f81a696c4443ccbc36a2aed274cc9e8c4a44160d922d17ca96",
    ("active",20261123):"ec6d269e7621dfbd8244ed57722fc0b6e71b721d870a7d3653321f151a647b67",
    ("no_friction",20261122):"aa35551b0e761173696e0fc89916152ed98663dd549a23cc214c4b3d588ca594"
}

def prefix_hash(case):
    prefix=h24.owner_for(case["seed"],case["friction"],case["gravity"])
    for key,value in case["samples"][1600].items():
        np.copyto(prefix[key].values,value)
    prefix.attrs["time_s"]=1600*h24.DT
    return h24.state_sha(prefix)

def settle_stats(case):
    prior=case["samples"][3000]["position_m"]
    after=case["samples"][3600]["position_m"]
    late_move=np.linalg.norm(after-prior,axis=1)
    return {
        "median_displacement_steps3000_3600_m":float(np.median(late_move)),
        "p90_displacement_steps3000_3600_m":float(np.quantile(late_move,.9)),
        "max_top_height_at_1600_m":float(np.max(case["samples"][1600]["position_m"][:,2]+h24.R)),
        "max_top_height_at_3600_m":case["max_top_height_m"]
    }

def report_case(case):
    return {k:v for k,v in case.items() if k not in ("owner","samples")}

def main():
    # The original code remains untouched; the only change is simulation time.
    h24.STEPS=STEPS_LATE
    h24.SAMPLES=SAMPLES_LATE
    active=h24.execute(h24.SEED1,True,True)
    alternative=h24.execute(h24.SEED2,True,True)
    frictionless=h24.execute(h24.SEED1,False,True)
    replay=h24.execute(h24.SEED1,True,True)
    first=settle_stats(active)
    second=settle_stats(alternative)
    third=settle_stats(frictionless)
    errors=[]
    def gate(key,condition):
        if not condition:
            errors.append(key)

    actual_prefix={
        "active_seed1":prefix_hash(active),
        "active_seed2":prefix_hash(alternative),
        "zero_friction":prefix_hash(frictionless),
    }
    gate("prefix_active_seed1_exact",
         actual_prefix["active_seed1"]==PREFIX_SHA[("active",h24.SEED1)])
    gate("prefix_active_seed2_exact",
         actual_prefix["active_seed2"]==PREFIX_SHA[("active",h24.SEED2)])
    gate("prefix_zero_friction_exact",
         actual_prefix["zero_friction"]==PREFIX_SHA[("no_friction",h24.SEED1)])
    gate("mass_and_owner",all(c["mass_kg"]==h24.N*h24.M for c in
                              (active,alternative,frictionless,replay)))
    for name,case in (("active_seed1",active),("active_seed2",alternative)):
        gate(name+"_late_heap",case["max_top_height_m"]>.36 and
             case["grains_above_first_layer"]>=30 and
             case["mean_descent_m"]>.15)
        gate(name+"_connected_supported",case["grain_positive_contact_count"]>0 and
             case["floor_positive_contact_count"]>0 and
             case["largest_force_contact_component"]>=45)
    gate("active_seed1_resting",first["median_displacement_steps3000_3600_m"]<.025 and
         active["p90_speed_m_s"]<.08)
    gate("active_seed2_resting",second["median_displacement_steps3000_3600_m"]<.025 and
         alternative["p90_speed_m_s"]<.08)
    gate("friction_effect_height",active["max_top_height_m"]>=
         frictionless["max_top_height_m"]+.08)
    gate("friction_effect_spread",active["radial_p90_m"]<=
         frictionless["radial_p90_m"]-.06)
    gate("friction_effect_contact",active["largest_force_contact_component"]>=
         frictionless["largest_force_contact_component"]+10)
    gate("different_seed_geometry",np.max(np.abs(
         active["owner"]["position_m"].values-
         alternative["owner"]["position_m"].values))>.01)
    gate("bitwise_replay",all(np.array_equal(
         active["owner"][k].values,replay["owner"][k].values) for k in
         ("material_mass_kg","position_m","velocity_mps",
          "angular_velocity_rad_s","orientation_xyzw"))
         and all(all(np.array_equal(active["samples"][s][name],
                                   replay["samples"][s][name])
         for name in active["samples"][s]) for s in SAMPLES_LATE))

    rejected=h24.bad_states(active["owner"])
    with tempfile.TemporaryDirectory(prefix="world_h25_") as td:
        path=pathlib.Path(td)/"extended_granular_owner.nc"
        active["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:
            back=f.load()
        h24.check(back,h24.SEED1,True,True)
        gate("netcdf_owner_identical",h24.state_sha(back)==active["final_sha"])
        size=path.stat().st_size
    output={
        "experiment":"E3 H25 unchanged PyBullet granular pile extended 1600->3600",
        "steps":STEPS_LATE,"dt_s":h24.DT,
        "python":platform.python_version(),
        "numpy":np.__version__,"xarray":xr.__version__,
        "active_seed1":report_case(active),
        "active_seed2":report_case(alternative),
        "frictionless_control":report_case(frictionless),
        "late_metrics":{"active_seed1":first,"active_seed2":second,
                        "zero_friction":third},
        "prefix_sha_at_step1600":actual_prefix,
        "all_prefix_sha_verified":all([
            actual_prefix["active_seed1"]==PREFIX_SHA[("active",h24.SEED1)],
            actual_prefix["active_seed2"]==PREFIX_SHA[("active",h24.SEED2)],
            actual_prefix["zero_friction"]==PREFIX_SHA[("no_friction",h24.SEED1)]
        ]),
        "negative_states_rejected":rejected,
        "checkpoint_bytes":size,"replay_exact":True,
        "failed_preregistered_gates":errors,
        "limitations":"Spherical frictional particles dropped from 5x5x5 initial lattice with jitter; no rock cohesiveness, source generation, caverns or 3D soil continuum. Longer wall-clock is model integration time, not geological calibration."
    }
    print("WORLD_EVAL_JSON "+json.dumps(output,sort_keys=True),flush=True)
    if errors:
        raise AssertionError("H25 preregistered gates failed: "+", ".join(errors))

if __name__=="__main__":
    main()
