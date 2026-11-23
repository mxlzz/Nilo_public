"""H37 Landlab stage: restart t3 and persist the resulting t6 owner for Bullet.

Reuses H33 science and H31 owner as-is; no new erosional physics. The next
H37 stage in Python 3.11 compares the same rigid-body contacts from this
resumed owner and from the uninterrupted Landlab baseline.
"""
from __future__ import annotations

import json
import pathlib
import platform
import sys

import numpy as np
import xarray as xr
import landlab

import probe_e6_h33_resume_landlab as h33
import probe_e5_h31_owner_contract as c

CASE_NAMES=(*h33.NAMES,"seed8128_zero_K")
CASE_INPUTS=(*h33.CASES,(8128,0.))

def run(rawpath,checkpoints_dir,output):
    raw=h33.read_raw(rawpath)
    source=pathlib.Path(checkpoints_dir)
    out=pathlib.Path(output)
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((source/"manifest.json").read_text(encoding="utf-8"))
    if manifest["split_step"]!=3 or manifest["end_step"]!=6:
        raise ValueError("Incorrect physical Landlab benchmark length")
    report={"experiment":"H37 Landlab t3->t6 while preserving H33 restart",
            "python":platform.python_version(),"landlab":landlab.__version__,
            "numpy":np.__version__,"xarray":xr.__version__,
            "steps_executed_after_restart":[4,5,6],
            "cases":{},"failed_preregistered_gates":[]}
    for name,(seed,k) in zip(CASE_NAMES,CASE_INPUTS):
        with xr.open_dataset(source/f"{name}_checkpoint.nc",engine="scipy") as f:
            mid=f.load()
        with xr.open_dataset(source/f"{name}_baseline.nc",engine="scipy") as f:
            baseline=f.load()
        c.validate(mid,raw[seed],seed,k)
        c.validate(baseline,raw[seed],seed,k)
        source_desc=manifest["cases"][name]
        if (c.hash_owner(mid)!=source_desc["mid_sha256"] or
            c.hash_owner(baseline)!=source_desc["baseline_sha256"]):
            raise ValueError("Input H33 producer owners do not match manifest")
        new,metrics=h33.advance(mid,raw[seed],seed,k,4,6)
        fields_equal=all(np.array_equal(new[f].values,baseline[f].values)
                         for f in c.FIELDS_ALL)
        owner_same=c.hash_owner(new)==c.hash_owner(baseline)
        ledger_same=new.attrs["exported_soil_kg"]==baseline.attrs["exported_soil_kg"]
        if not(fields_equal and owner_same and ledger_same and
               abs(metrics["max_abs_mass_error_kg"])<=.09216 and
               int(new.attrs["landlab_step"])==6 and new.attrs["bullet_t_s"]==0.):
            report["failed_preregistered_gates"].append(name+"_resumed_owner_differs")
        dest=out/f"{name}_resumed.nc"
        new.to_netcdf(dest,engine="scipy")
        with xr.open_dataset(dest,engine="scipy") as f:
            loaded=f.load()
        c.validate(loaded,raw[seed],seed,k)
        if c.hash_owner(loaded)!=c.hash_owner(new):
            report["failed_preregistered_gates"].append(name+"_NetCDF_owner_different")
        report["cases"][name]={
            "seed":seed,"K_sed":k,
            "checkpoint_t3_sha256":source_desc["mid_sha256"],
            "baseline_t6_sha256":source_desc["baseline_sha256"],
            "resumed_t6_sha256":c.hash_owner(new),
            "same_owner_bitwise":bool(fields_equal and owner_same and ledger_same),
            "stored_soil_kg":float(new["soil_mass_kg"].sum()),
            "exported_soil_kg":float(new.attrs["exported_soil_kg"]),
            "max_mass_budget_error_kg":metrics["max_abs_mass_error_kg"],
            "executed_step_range":[4,6],
        }
    (out/"manifest.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if report["failed_preregistered_gates"]:
        raise AssertionError("H37 resumed Landlab owner differs from continuous t6")

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("Usage: raw_worlds.npz h33_producer_dir output_dir")
    run(*sys.argv[1:])
