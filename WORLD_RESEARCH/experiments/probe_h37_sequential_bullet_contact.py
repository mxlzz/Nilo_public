"""H37: compare native Bullet contacts after continuous vs resumed Landlab soil.

No custom physics. Same original H31 terrain mesh, raycast and contact
solver; the resumed owner is output of the separate H37/H33 Landlab runner.
Two clocks remain explicit, not a calibrated common simulation second.
Protocol: H37_PROTOCOLO_RESTART_CADENA_SUELO_CONTACTO.md.
"""
from __future__ import annotations

import json
import pathlib
import platform
import sys
import tempfile
from importlib.metadata import version

import numpy as np
import pybullet
import xarray as xr

import probe_e5_h31_owner_contract as c
import probe_e5_h31_bullet_stage as bullet

SEEDS=(7321,8128)
CASES={
    (7321,.1):"seed7321_active",
    (7321,0.):"seed7321_zero_K",
    (8128,.1):"seed8128_active",
    (8128,0.):"seed8128_zero_K",
}

def np_scalar(x):
    if isinstance(x,np.generic): return x.item()
    raise TypeError(type(x).__name__)

def read_raw(path):
    with np.load(path,allow_pickle=False) as inp:
        raws={seed:np.asarray(inp[f"elevation_seed_{seed}"],dtype="<f8").copy()
              for seed in SEEDS}
        revision=str(inp["worldengine_revision"][0])
        hashes=[str(x) for x in inp["source_sha256"]]
    if revision!=c.SOURCE_REVISION or hashes!=[c.SOURCES[s] for s in SEEDS]:
        raise ValueError("H37 changed WorldEngine source revision or SHA metadata")
    if any(c.sha_raw(raws[s])!=c.SOURCES[s] for s in SEEDS):
        raise ValueError("Raw elevation field differs from original H31")
    return raws

def read_owner(path,raw,seed,k,hash_value):
    with xr.open_dataset(path,engine="scipy") as f:owner=f.load()
    c.validate(owner,raw,seed,k)
    if c.hash_owner(owner)!=hash_value or int(owner.attrs["landlab_step"])!=6 or owner.attrs["body_status"]!="reservoir" or owner.attrs["bullet_t_s"]!=0.:
        raise ValueError("H37 handoff owner is not exact original/resumed t6")
    return owner

def main(rawpath,baselines,resumed):
    raw=read_raw(rawpath)
    root=pathlib.Path(baselines)
    new=pathlib.Path(resumed)
    base_manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    resume_manifest=json.loads((new/"manifest.json").read_text(encoding="utf-8"))
    failed=[]
    def gate(name,ok):
        if not ok: failed.append(name)
    result={
        "experiment":"H37 restored Landlab t3->t6 determines same downstream Bullet rigid contact as t1->t6",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"xarray":xr.__version__,
        "landlab_step_range_continuous":[1,6],
        "landlab_step_range_restart":[1,3,4,6],
        "rigid_steps_per_path":c.BULLET_STEPS,"rigid_dt_seconds":c.BULLET_DT,
        "landlab_dt_benchmark":c.LANDLAB_DT,
        "time_unit_warning":"Landlab benchmark time and Bullet seconds are DISTINCT clocks; heights m_nominal and erodibility not physically calibrated.",
        "seeds":{},"failed_preregistered_gates":failed
    }
    for seed in SEEDS:
        owners={}
        for k in (0.,.1):
            name=CASES[(seed,k)]
            expected=base_manifest["cases"][name]["baseline_sha256"]
            resumed_sha=resume_manifest["cases"][name]["resumed_t6_sha256"]
            owners[(k,"continuous")]=read_owner(
                root/f"{name}_baseline.nc",raw[seed],seed,k,expected)
            owners[(k,"resumed")]=read_owner(
                new/f"{name}_resumed.nc",raw[seed],seed,k,resumed_sha)
            gate(name+"_material_bit_equal",
                 c.hash_owner(owners[(k,"continuous")])==
                 c.hash_owner(owners[(k,"resumed")]))
            gate(name+"_closed_budget",abs(
                 float(owners[(k,"resumed")]["soil_mass_kg"].sum())+
                 float(owners[(k,"resumed")].attrs["exported_soil_kg"])+
                 c.BODY_MASS-(c.MASS0+c.BODY_MASS))<=.09216)
        initial=c.topography(owners[(0.,"continuous")])
        eroded=c.topography(owners[(.1,"continuous")])
        patch,delta=c.select_patch(initial,eroded)
        before_patch=initial[patch[0]:patch[0]+2,patch[1]:patch[1]+2]
        contact={}
        for k in (0.,.1):
            for mode in ("continuous","resumed"):
                contact[(k,mode)]=bullet.contact_from_owner(
                    owners[(k,mode)],raw[seed],seed,k,patch,before_patch)
                e=contact[(k,mode)]
                gate(f"{seed}_{k}_{mode}_ray",e["ray_error_m_nominal"]<1e-3)
                gate(f"{seed}_{k}_{mode}_actual_contact",
                     e["first_positive_contact"] is not None and
                     e["contact_events"]>0)
                c.validate(e["owner"],raw[seed],seed,k)
        for k in (0.,.1):
            a=contact[(k,"continuous")]
            b=contact[(k,"resumed")]
            gate(f"{seed}_{k}_contact_from_restarted_identical",
                 a["first_positive_contact"]==b["first_positive_contact"]
                 and a["contact_events"]==b["contact_events"]
                 and a["final_joint_owner_sha"]==b["final_joint_owner_sha"]
                 and all(np.array_equal(a["owner"][f].values,b["owner"][f].values)
                         for f in c.FIELDS_ALL))
        control=contact[(0.,"continuous")]
        altered=contact[(.1,"continuous")]
        height_shift=float(altered["first_positive_contact"]["terrain_xyz_m_nominal"][2]-
                           control["first_positive_contact"]["terrain_xyz_m_nominal"][2])
        gate(f"{seed}_K1_changes_contact",
             abs(delta)>=.003 and abs(height_shift)>=.003 and
             delta*height_shift>0.)
        gate(f"{seed}_K0_no_sediment",
             owners[(0.,"resumed")].attrs["exported_soil_kg"]==0.
             and abs(float(owners[(0.,"resumed")]["soil_mass_kg"].sum())-c.MASS0)<1e-6)
        with tempfile.TemporaryDirectory(prefix="h37_final_contact_") as td:
            file=pathlib.Path(td)/"body_after_resumed_erosion.nc"
            altered_resumed=contact[(.1,"resumed")]["owner"]
            altered_resumed.to_netcdf(file,engine="scipy")
            with xr.open_dataset(file,engine="scipy") as f:
                loaded=f.load()
            c.validate(loaded,raw[seed],seed,.1)
            gate(f"{seed}_endowner_netcdf_exact",
                 c.hash_owner(loaded)==contact[(.1,"continuous")]["final_joint_owner_sha"])
        result["seeds"][str(seed)]={
            "patch_yx":list(patch),
            "nominal_erosion_change_m":delta,
            "nominal_contact_shift_m":height_shift,
            "control_contact_first":control["first_positive_contact"],
            "eroded_contact_first":altered["first_positive_contact"],
            "continuous_vs_resumed_baseline_owner_sha":{
                "K0":c.hash_owner(owners[(0.,"continuous")]),
                "Kactive":c.hash_owner(owners[(.1,"continuous")])
            },
            "after_rigid_full_owner_sha":{
                "K0":control["final_joint_owner_sha"],
                "Kactive":altered["final_joint_owner_sha"]
            },
            "eroded_body_pos_after720_nominal_m":altered["final_position_xyz_m_nominal"],
            "contacts_K0":int(control["contact_events"]),
            "contacts_Kactive":int(altered["contact_events"]),
            "landlab_export_Kactive_kg":float(owners[(.1,"continuous")].attrs["exported_soil_kg"]),
            "post_bullet_owner_t_s":float(altered["owner"].attrs["bullet_t_s"]),
        }
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True,default=np_scalar),flush=True)
    if failed:
        raise AssertionError("H37 preregistered end-to-end causal gate failed: "+", ".join(failed))

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("Usage: raw_worlds.npz h33_producer_checkpoint_dir h37_resumed_landlab_dir")
    main(*sys.argv[1:])
