"""E3 H19: assess connected, persistent sediment deposits against conditional nulls.

No transport law written here: native Landlab physics H9 supplies every step.
Pre-registered before implementation: ETAPA_3_H19_PROTOCOLO_DEPOSITO_CONEXO.md.
"""
from __future__ import annotations

import json
import pathlib
import platform
import tempfile

import landlab
import numpy as np
import scipy
import xarray as xr
from scipy.ndimage import label

import probe_e1_h9_sediment_owner as h9

NNULL=512
SEED=20261122
STRUCTURE=np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=np.int8)
CORE_SLICE=(slice(1,-1),slice(1,-1))


def topology(mask):
    components,n=label(mask,structure=STRUCTURE)
    if n==0:
        return {"component_count":0,"largest_component":0,"component_sizes":[],"labeled":components}
    sizes=np.bincount(components[components>0],minlength=n+1)[1:]
    return {
        "component_count":int(n),
        "largest_component":int(sizes.max()),
        "component_sizes":sorted([int(z) for z in sizes],reverse=True),
        "labeled":components,
    }


def nulls(observed):
    inner=np.asarray(observed,dtype=bool)[CORE_SLICE]
    n=int(inner.sum())
    rng=np.random.default_rng(SEED)
    total=inner.size
    by_row=inner.sum(axis=1).astype(int)
    shape=inner.shape
    all_sizes=[]
    conditional_sizes=[]
    for _ in range(NNULL):
        choice=rng.choice(total,size=n,replace=False)
        simple=np.zeros(total,dtype=bool)
        simple[choice]=True
        all_sizes.append(topology(simple.reshape(shape))["largest_component"])
        conditioned=np.zeros(shape,dtype=bool)
        for y,num in enumerate(by_row):
            if num:
                xs=rng.choice(shape[1],size=int(num),replace=False)
                conditioned[y,xs]=True
        conditional_sizes.append(topology(conditioned)["largest_component"])
    return {
        "rng_seed":SEED,"trials_per_null":NNULL,
        "row_winners":by_row.tolist(),
        "largest_global_p95":int(np.quantile(all_sizes,.95,method="higher")),
        "largest_row_preserving_p95":int(np.quantile(conditional_sizes,.95,method="higher")),
        "largest_global_mean":float(np.mean(all_sizes)),
        "largest_row_preserving_mean":float(np.mean(conditional_sizes)),
        "largest_global_max":int(max(all_sizes)),
        "largest_row_preserving_max":int(max(conditional_sizes)),
    }


def run_active():
    grid,flow,space,owner=h9.make_scene(h9.K_ACTIVE)
    initial_mass=owner["soil_mass_kg"].values.copy()
    initial_sum=float(owner.attrs["initial_soil_kg"])
    states={}
    largest_residual=0.
    all_flux_erosion=[]
    all_flux_deposition=[]
    for step in range(1,25):
        candidate,ledger=h9.advance_native_step(grid,flow,space,owner,initial_sum)
        owner=candidate
        largest_residual=max(largest_residual,abs(ledger["residual_kg"]))
        erosion=grid.at_node["sediment__erosion_flux"][grid.core_nodes]
        deposition=grid.at_node["sediment__deposition_flux"][grid.core_nodes]
        all_flux_erosion.append(bool(np.any(erosion>1e-15)))
        all_flux_deposition.append(bool(np.any(deposition>1e-15)))
        if step in (12,24):
            mask=(owner["soil_mass_kg"].values-initial_mass>1e-6)
            mask&=owner["is_core_node"].values.astype(bool)
            t=topology(mask)
            states[step]={
                "mask":mask.copy(),
                "owner":owner.copy(deep=True),
                "count":int(mask.sum()),
                "component_count":t["component_count"],
                "largest_component":t["largest_component"],
                "component_sizes":t["component_sizes"],
                "largest_component_mask":t["labeled"]==int(np.argmax(
                    np.bincount(t["labeled"][t["labeled"]>0],minlength=t["component_count"]+1)[1:])+1)
                    if t["component_count"] else np.zeros_like(mask,dtype=bool),
                "exported_mass_kg":float(owner.attrs["exported_soil_kg"]),
                "remaining_mass_kg":float(owner["soil_mass_kg"].sum()),
                "sha256":h9.checksum(owner),
            }
    return {
        "states":states,"total_initial_mass_kg":initial_sum,
        "peak_abs_mass_residual_kg":largest_residual,
        "erosion_steps":sum(all_flux_erosion),
        "deposition_steps":sum(all_flux_deposition),
    }


def main():
    actual=run_active()
    again=run_active()
    t12=actual["states"][12]
    t24=actual["states"][24]
    x12=again["states"][12]
    x24=again["states"][24]
    null=nulls(t12["mask"])
    union=np.logical_or(t12["mask"],t24["mask"]).sum()
    intersection=np.logical_and(t12["mask"],t24["mask"]).sum()
    jaccard=float(intersection/union) if union else 0.
    keep=float(t24["largest_component"]/t12["largest_component"]) if t12["largest_component"] else 0.

    inactive=h9.execute(0.)
    rejection=h9.negative_cases(t24["owner"])
    failed=[]
    def check(key,ok):
        if not ok:failed.append(key)
    check("t12_gains_exist",t12["count"]>=8)
    check("large_connected_pattern_above_row_null95",
          t12["largest_component"]>=null["largest_row_preserving_p95"]+3)
    check("pattern_overlap_persistent_12_to_24",jaccard>=.60)
    check("largest_component_size_persistent",keep>=.5)
    check("native_erosion_and_deposition",actual["erosion_steps"]>0 and actual["deposition_steps"]>0)
    check("mass_balance_24_steps",
          actual["peak_abs_mass_residual_kg"]<=max(1e-4,1e-8*actual["total_initial_mass_kg"]))
    check("K0_zero_deposition_and_export",
          inactive["mass_ledger"]["export_kg"]==0.
          and np.array_equal(inactive["original"],inactive["owner"]["soil_mass_kg"].values))
    check("physical_replay",
          np.array_equal(t12["mask"],x12["mask"])
          and np.array_equal(t24["mask"],x24["mask"])
          and np.array_equal(t24["owner"]["soil_mass_kg"].values,
                             x24["owner"]["soil_mass_kg"].values)
          and t24["exported_mass_kg"]==x24["exported_mass_kg"]
          and t24["sha256"]==x24["sha256"])
    with tempfile.TemporaryDirectory(prefix="world_e3_h19_") as td:
        file=pathlib.Path(td)/"sediment_owner_t24.nc"
        t24["owner"].to_netcdf(file,engine="scipy")
        with xr.open_dataset(file,engine="scipy") as f:
            loaded=f.load()
        h9.validate(loaded,actual["total_initial_mass_kg"])
        check("owner_snapshot_exact",
              h9.checksum(loaded)==t24["sha256"]
              and np.array_equal(loaded["soil_mass_kg"].values,
                                 t24["owner"]["soil_mass_kg"].values))
        disk_bytes=file.stat().st_size

    def public(t):
        return {k:v for k,v in t.items() if k not in ("mask","owner","largest_component_mask")}
    report={
        "experiment":"E3 H19 Landlab deposition 12->24 steps against row-conditioned null",
        "python":platform.python_version(),"landlab":landlab.__version__,
        "scipy":scipy.__version__,"numpy":np.__version__,"xarray":xr.__version__,
        "seed":SEED,"nnull":NNULL,"initial_soil_kg":actual["total_initial_mass_kg"],
        "t12":public(t12),"t24":public(t24),"null_model":null,
        "jaccard_t12_t24":jaccard,"largest_component_size_ratio_t24_over_t12":keep,
        "erosion_steps":actual["erosion_steps"],"deposition_steps":actual["deposition_steps"],
        "peak_abs_balance_residual_kg":actual["peak_abs_mass_residual_kg"],
        "K0_export_kg":inactive["mass_ledger"]["export_kg"],
        "rejected_invalid_owner":rejection,
        "replay_exact":True,"netcdf_bytes":disk_bytes,
        "failed_preregistered_gates":failed,
        "limitations":"Two timepoints, single prescribed initial watershed and one erodibility setting. Connected net deposit does not imply a coherent 3D body, mechanical stability, new function or open-ended emergence."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if failed:
        raise AssertionError("H19 preregistered pattern gates failed: "+", ".join(failed))


if __name__=="__main__":
    main()
