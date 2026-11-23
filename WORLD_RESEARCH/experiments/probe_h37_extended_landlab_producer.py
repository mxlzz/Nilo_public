"""H37 four-case checkpoint producer; reuse original H33 for first three.

Add seed8128 with K=0 as the extra *pre-registered* matched control.
No change to sediment equations, Landlab dt, common owner, or prior H33.
"""
from __future__ import annotations
import json
import pathlib
import sys

import numpy as np
import xarray as xr

import probe_e6_h33_resume_landlab as h33
import probe_e5_h31_owner_contract as c

EXTRA="seed8128_zero_K"

def run(rawpath,folder):
    h33.producer(rawpath,folder)
    root=pathlib.Path(folder)
    raws=h33.read_raw(rawpath)
    seed=8128
    k=0.
    original=h33.initial_owner(raws[seed],seed,k)
    baseline,full_metrics=h33.advance(original,raws[seed],seed,k,1,6)
    split,split_metrics=h33.advance(
        h33.initial_owner(raws[seed],seed,k),raws[seed],seed,k,1,3)
    for label,owner,step in (("baseline",baseline,6),("checkpoint",split,3)):
        if int(owner.attrs["landlab_step"])!=step:
            raise ValueError("Wrong checkpoint at pre-registered H37 K0 time")
        file=root/f"{EXTRA}_{label}.nc"
        owner.to_netcdf(file,engine="scipy")
        with xr.open_dataset(file,engine="scipy") as f:
            restored=f.load()
        c.validate(restored,raws[seed],seed,k)
        if c.hash_owner(restored)!=c.hash_owner(owner):
            raise ValueError("H37 extra K0 NetCDF checksum mismatch")
    desc={
        "seed":seed,"K":k,
        "mid_sha256":c.hash_owner(split),
        "baseline_sha256":c.hash_owner(baseline),
        "split_soil_kg":float(split["soil_mass_kg"].sum()),
        "split_exported_kg":float(split.attrs["exported_soil_kg"]),
        "baseline_soil_kg":float(baseline["soil_mass_kg"].sum()),
        "baseline_exported_kg":float(baseline.attrs["exported_soil_kg"]),
        "mid_budget_max_error_kg":split_metrics["max_abs_mass_error_kg"],
        "baseline_budget_max_error_kg":full_metrics["max_abs_mass_error_kg"],
        "outlet_continuous":full_metrics["outlet"],
        "outlet_prefix":split_metrics["outlet"]
    }
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    manifest["cases"][EXTRA]=desc
    manifest["h37_extended_zeroK_seed8128"]=True
    (root/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"H37 extend H33 producer for four matched 2-seed K0/control cases",
        "extra_case":EXTRA,"detail":desc,
        "original_H33_three_cases_unchanged":True,
        "preregistered_gates_failed":[]
    },sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: raw_worlds.npz checkpoint_output_dir")
    run(*sys.argv[1:])
