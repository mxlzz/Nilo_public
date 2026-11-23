"""H31 stage 1/2: Landlab on Python3.13 updates authoritative soil+body owner.

Writes NetCDF checkpoints containing BOTH material stocks, owner metadata,
body-reservoir status, native sediment ledger and source hashes. The next
job MUST read these exact checkpoints; no second material inventory.
Original physical H31 gates remain unchanged; runtime split amendment
preregistered after environment failure before this code.
"""
from __future__ import annotations

import json
import pathlib
import platform
import sys

import landlab
import numpy as np
import xarray as xr

import probe_e4_h29_generated_owner_landlab as h29
import probe_e5_h31_owner_contract as contract

def native_run(raw,seed,sha,k):
    base=h29.create(raw,seed,sha)
    owner=contract.augment(base,seed,sha,k)
    initial_hash=contract.hash_owner(owner)
    contract.validate(owner,raw,seed,k)
    grid,router,solver,outlet=h29.setup_scene(contract.soil_only(owner),k)
    start_mass=owner["soil_mass_kg"].values.copy()
    max_imbalance=0.
    for step in range(1,contract.TIMESTEPS+1):
        current_soil=contract.soil_only(owner)
        np.copyto(grid.at_node["soil__depth"],
                  owner["soil_mass_kg"].values.ravel()/(contract.RHO*contract.AREA))
        np.copyto(grid.at_node["topographic__elevation"],
                  contract.topography(owner).ravel())
        router.run_one_step()
        suspended,bedload=solver.run_one_step(contract.LANDLAB_DT)
        if (not np.isfinite([suspended,bedload]).all() or
            suspended<0 or bedload<0):
            raise ValueError("Native Landlab supplied invalid sediment flux")
        newdepth=grid.at_node["soil__depth"].reshape(contract.SHAPE)
        if not np.isfinite(newdepth).all() or np.any(newdepth<0):
            raise ValueError("Native solver generated invalid depth")
        candidate=owner.copy(deep=True)
        candidate["soil_mass_kg"].values[:]=newdepth*contract.RHO*contract.AREA
        candidate.attrs["exported_soil_kg"]=(
            float(owner.attrs["exported_soil_kg"])+
            float(suspended+bedload)*contract.RHO
        )
        candidate.attrs["landlab_step"]=step
        candidate.attrs["landlab_t_bench"]=step*contract.LANDLAB_DT
        report=contract.validate(candidate,raw,seed,k)
        h29.validate(contract.soil_only(candidate),raw,sha,seed)
        if (not np.array_equal(candidate["body_mass_kg"].values,
                               owner["body_mass_kg"].values) or
            candidate.attrs["body_status"]!="reservoir"):
            raise ValueError("Erosion touched unreleased body")
        max_imbalance=max(max_imbalance,abs(report["mass_residual_kg"]))
        owner=candidate
    final=contract.validate(owner,raw,seed,k)
    return {
        "owner":owner,"seed":seed,"k":float(k),
        "outlet_node":int(outlet),
        "initial_owner_sha":initial_hash,
        "final_owner_sha":contract.hash_owner(owner),
        "changed_soil_nodes":int(np.count_nonzero(np.abs(owner["soil_mass_kg"].values-start_mass)>1e-6)),
        "exported_soil_kg":final["export_kg"],
        "mass_soil_remaining_kg":final["soil_remaining_kg"],
        "body_mass_kg":final["body_kg"],
        "peak_closed_mass_error_kg":max_imbalance,
    }

def main(rawpath,outdir):
    target=pathlib.Path(outdir)
    target.mkdir(parents=True,exist_ok=True)
    with np.load(rawpath,allow_pickle=False) as data:
        raw={
            7321:np.asarray(data["elevation_seed_7321"],dtype="<f8").copy(),
            8128:np.asarray(data["elevation_seed_8128"],dtype="<f8").copy(),
        }
        upstream=str(data["worldengine_revision"][0])
        source_hashes=[str(x) for x in data["source_sha256"]]
    if (upstream!=contract.SOURCE_REVISION or
        source_hashes!=[contract.SOURCES[7321],contract.SOURCES[8128]] or
        any(contract.sha_raw(raw[seed])!=contract.SOURCES[seed]
            for seed in contract.SOURCES)):
        raise ValueError("Generator source or raw arrays not H29")
    runs={}
    for seed in contract.SOURCES:
        for k in (contract.K_ACTIVE,0.):
            key=f"{seed}_{'active' if k else 'control'}"
            case=native_run(raw[seed],seed,contract.SOURCES[seed],k)
            path=target/f"{key}.nc"
            case["owner"].to_netcdf(path,engine="scipy")
            with xr.open_dataset(path,engine="scipy") as f:
                loaded=f.load()
            contract.validate(loaded,raw[seed],seed,k)
            if contract.hash_owner(loaded)!=case["final_owner_sha"]:
                raise ValueError("Canonical NetCDF owner hash changed")
            info={n:v for n,v in case.items() if n!="owner"}
            info["checkpoint_name"]=path.name
            info["checkpoint_bytes"]=path.stat().st_size
            runs[key]=info
    repeated=native_run(raw[7321],7321,contract.SOURCES[7321],contract.K_ACTIVE)
    if (repeated["final_owner_sha"]!=runs["7321_active"]["final_owner_sha"]
        or repeated["exported_soil_kg"]!=runs["7321_active"]["exported_soil_kg"]):
        raise ValueError("Native Landlab stage replay failed")
    selection={}
    for seed in contract.SOURCES:
        a=runs[f"{seed}_active"]
        b=runs[f"{seed}_control"]
        with xr.open_dataset(target/a["checkpoint_name"],engine="scipy") as f:
            active=f.load()
        with xr.open_dataset(target/b["checkpoint_name"],engine="scipy") as f:
            control=f.load()
        prior=contract.topography(control)
        updated=contract.topography(active)
        index,delta=contract.select_patch(prior,updated)
        selection[str(seed)]={
            "patch_index":[int(index[0]),int(index[1])],
            "delta_z_m_nominal":float(delta),
        }
        if (a["changed_soil_nodes"]<=0 or b["changed_soil_nodes"]!=0
            or b["exported_soil_kg"]!=0. or
            abs(delta)<=.005 or
            max(a["peak_closed_mass_error_kg"],b["peak_closed_mass_error_kg"])>.09216):
            raise AssertionError(f"Preexisting H31 native soil gates failed seed{seed}")
    manifest={
        "experiment":"E5 H31 stage1 canonical native material+body checkpoint",
        "source_upstream_SHA":upstream,
        "python":platform.python_version(),"landlab":landlab.__version__,
        "numpy":np.__version__,"xarray":xr.__version__,
        "source_raw_hashes":source_hashes,
        "runs":runs,"patch_selection":selection,
        "landlab_replay_seed7321_exact":True,
        "model":"Native SPACE erosion, body retained in reservoir"
    }
    (target/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("WORLD_EVAL_JSON "+json.dumps(manifest,sort_keys=True),flush=True)

if __name__=="__main__":
    main(sys.argv[1],sys.argv[2])
