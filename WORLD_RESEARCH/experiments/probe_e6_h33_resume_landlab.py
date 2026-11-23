"""E6 H33: end-to-end mid-run Landlab restart across separate CI processes.

No custom sediment physics. Original native Landlab SpaceLargeScaleEroder
from H31, same WorldEngine raw source, same canonical xarray body+soil owner.
Preregistration: ETAPA_6_H33_PROTOCOLO_RESTART_LANDLAB.md.
"""
from __future__ import annotations

import json
import pathlib
import platform
import sys
import tempfile

import landlab
import numpy as np
import xarray as xr

import probe_e4_h29_generated_owner_landlab as h29
import probe_e5_h31_owner_contract as c

SPLIT_STEP=3
END_STEP=c.TIMESTEPS
CASES=((7321,c.K_ACTIVE),(8128,c.K_ACTIVE),(7321,0.))
NAMES=("seed7321_active","seed8128_active","seed7321_zero_K")

def json_numpy_scalar(value):
    """Only convert reporting scalars; never modify scientific state/gates."""
    if isinstance(value,np.generic):
        return value.item()
    raise TypeError("Unsupported diagnostic JSON object: "+type(value).__name__)


def read_raw(filepath):
    with np.load(filepath,allow_pickle=False) as data:
        raws={seed:np.asarray(data[f"elevation_seed_{seed}"],dtype="<f8").copy()
              for seed in (7321,8128)}
        revision=str(data["worldengine_revision"][0])
        sources=[str(x) for x in data["source_sha256"]]
    if revision!=c.SOURCE_REVISION or sources!=[c.SOURCES[7321],c.SOURCES[8128]]:
        raise ValueError("H33 WorldEngine revision/source metadata altered")
    if any(c.sha_raw(raws[s])!=c.SOURCES[s] for s in raws):
        raise ValueError("H33 source raw hash corrupted")
    return raws


def initial_owner(raw,seed,k):
    soil=h29.create(raw,seed,c.SOURCES[seed])
    owner=c.augment(soil,seed,c.SOURCES[seed],k)
    c.validate(owner,raw,seed,k)
    return owner


def model_from_owner(owner,k):
    # Deliberately discard the old native solver. This constructs it anew
    # exclusively from material fields in the canonical owner.
    grid,router,solver,outlet=h29.setup_scene(c.soil_only(owner),k)
    return grid,router,solver,int(outlet)


def advance(owner,raw,seed,k,first,last):
    if int(owner.attrs["landlab_step"])!=first-1:
        raise ValueError("Attempt to replay already completed physical steps")
    grid,flow,solver,outlet=model_from_owner(owner,k)
    max_error=0.
    for step in range(first,last+1):
        np.copyto(grid.at_node["soil__depth"],
                  owner["soil_mass_kg"].values.ravel()/(c.RHO*c.AREA))
        np.copyto(grid.at_node["topographic__elevation"],
                  c.topography(owner).ravel())
        flow.run_one_step()
        suspended,bedload=solver.run_one_step(c.LANDLAB_DT)
        if not np.isfinite([suspended,bedload]).all() or suspended<0 or bedload<0:
            raise ValueError("Landlab supplied invalid sediment transfer")
        newdepth=grid.at_node["soil__depth"].reshape(c.SHAPE)
        if not np.isfinite(newdepth).all() or (newdepth<0).any():
            raise ValueError("Landlab supplied physically invalid soil depth")
        candidate=owner.copy(deep=True)
        candidate["soil_mass_kg"].values[:]=newdepth*c.RHO*c.AREA
        candidate.attrs["exported_soil_kg"]=(
            float(owner.attrs["exported_soil_kg"])+
            float(suspended+bedload)*c.RHO)
        candidate.attrs["landlab_step"]=step
        candidate.attrs["landlab_t_bench"]=step*c.LANDLAB_DT
        check=c.validate(candidate,raw,seed,k)
        h29.validate(c.soil_only(candidate),raw,c.SOURCES[seed],seed)
        if candidate.attrs["body_status"]!="reservoir" or (
            not np.array_equal(candidate["body_mass_kg"].values,owner["body_mass_kg"].values)):
            raise ValueError("Rigid reservoir altered by sediment")
        if candidate.attrs["bullet_t_s"]!=0.:
            raise ValueError("Bullets clock advanced without rigid release")
        max_error=max(max_error,abs(check["mass_residual_kg"]))
        owner=candidate
    return owner,{"outlet":outlet,"max_abs_mass_error_kg":max_error,
                  "executed_from":first,"executed_to":last}


def reject_bad_checkpoint(owner,raw,seed,k):
    original=c.hash_owner(owner)
    flags={}
    def reject(label,patch):
        other=owner.copy(deep=True)
        patch(other)
        try:c.validate(other,raw,seed,k)
        except ValueError:flags[label]=True
        else:raise AssertionError("Corrupted H33 checkpoint accepted: "+label)
        if c.hash_owner(owner)!=original:
            raise AssertionError("Rejected mutation altered canonical checkpoint")
    reject("invented_soil_1kg",lambda d:d["soil_mass_kg"].values.__setitem__((2,2),d["soil_mass_kg"].values[2,2]+1))
    reject("negative_soil",lambda d:d["soil_mass_kg"].values.__setitem__((2,2),-1.))
    reject("wrong_unit",lambda d:d["soil_mass_kg"].attrs.__setitem__("units","g"))
    reject("wrong_world_seed",lambda d:d.attrs.__setitem__("source_seed",999))
    reject("changed_body_mass",lambda d:d["body_mass_kg"].values.__setitem__(0,3.))
    reject("wrong_clock",lambda d:d.attrs.__setitem__("landlab_step",4))
    reject("wrong_body_reservoir_state",lambda d:d.attrs.__setitem__("body_status","released"))
    reject("negative_export",lambda d:d.attrs.__setitem__("exported_soil_kg",-1.))
    reject("extra_mass_inventory",lambda d:d.__setitem__("duplicate_soil",xr.DataArray(np.zeros(c.SHAPE),dims=("y","x"))))
    return flags


def producer(rawpath,output):
    raws=read_raw(rawpath)
    out=pathlib.Path(output);out.mkdir(parents=True,exist_ok=True)
    manifest={
        "experiment":"E6 H33 checkpoint producer at native step3; uninterrupted baseline6",
        "landlab":landlab.__version__,"python":platform.python_version(),
        "np_version":np.__version__,"xarray":xr.__version__,
        "split_step":SPLIT_STEP,"end_step":END_STEP,
        "source_revision":c.SOURCE_REVISION,
        "cases":{},"replay_seed7321":False
    }
    for name,(seed,k) in zip(NAMES,CASES):
        original=initial_owner(raws[seed],seed,k)
        continuous,diagnostics=advance(original,raws[seed],seed,k,1,END_STEP)
        split,split_metrics=advance(initial_owner(raws[seed],seed,k),
                                    raws[seed],seed,k,1,SPLIT_STEP)
        if split.attrs["landlab_step"]!=3 or split.attrs["body_status"]!="reservoir":
            raise AssertionError("Split checkpoint is not at legitimate mid-history state")
        if continuous.attrs["landlab_step"]!=6:
            raise AssertionError("Baseline was not run to six steps")
        for prefix,owner in (("baseline",continuous),("checkpoint",split)):
            path=out/f"{name}_{prefix}.nc"
            owner.to_netcdf(path,engine="scipy")
            with xr.open_dataset(path,engine="scipy") as f:
                restored=f.load()
            c.validate(restored,raws[seed],seed,k)
            if c.hash_owner(restored)!=c.hash_owner(owner):
                raise ValueError("E6 producer checkpoint SHA not roundtrip exact")
        report={
            "seed":seed,"K":k,
            "mid_sha256":c.hash_owner(split),
            "baseline_sha256":c.hash_owner(continuous),
            "split_soil_kg":float(split["soil_mass_kg"].sum()),
            "split_exported_kg":float(split.attrs["exported_soil_kg"]),
            "baseline_soil_kg":float(continuous["soil_mass_kg"].sum()),
            "baseline_exported_kg":float(continuous.attrs["exported_soil_kg"]),
            "mid_budget_max_error_kg":split_metrics["max_abs_mass_error_kg"],
            "baseline_budget_max_error_kg":diagnostics["max_abs_mass_error_kg"],
            "outlet_continuous":diagnostics["outlet"],
            "outlet_prefix":split_metrics["outlet"],
        }
        manifest["cases"][name]=report
    duplicate,checks=advance(initial_owner(raws[7321],7321,c.K_ACTIVE),
                             raws[7321],7321,c.K_ACTIVE,1,END_STEP)
    manifest["replay_seed7321"]=c.hash_owner(duplicate)==manifest["cases"][NAMES[0]]["baseline_sha256"]
    if not manifest["replay_seed7321"]:
        raise ValueError("Native baseline replay not deterministic")
    src=raws[7321]
    with xr.open_dataset(out/f"{NAMES[0]}_checkpoint.nc",engine="scipy") as f:
        mid=f.load()
    manifest["invalid_checkpoint_states_rejected"]=reject_bad_checkpoint(
        mid,src,7321,c.K_ACTIVE)
    manifest["producer_gate_failed"]=[]
    if any(z["baseline_budget_max_error_kg"]>.09216 or z["mid_budget_max_error_kg"]>.09216
           for z in manifest["cases"].values()):
        manifest["producer_gate_failed"].append("closed_material_budget")
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("WORLD_EVAL_JSON "+json.dumps(manifest,sort_keys=True),flush=True)
    if manifest["producer_gate_failed"]:
        raise AssertionError("H33 producer gates failed")


def consumer(rawpath,folder):
    raws=read_raw(rawpath)
    root=pathlib.Path(folder)
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    if (manifest["source_revision"]!=c.SOURCE_REVISION or
        manifest["split_step"]!=SPLIT_STEP or manifest["end_step"]!=END_STEP):
        raise ValueError("Restart manifest does not match preregistered time/source")
    metrics=[]
    failed=[]
    def gate(name,flag):
        if not flag:failed.append(name)
    for name,(seed,k) in zip(NAMES,CASES):
        spec=manifest["cases"][name]
        with xr.open_dataset(root/f"{name}_checkpoint.nc",engine="scipy") as f:
            saved=f.load()
        with xr.open_dataset(root/f"{name}_baseline.nc",engine="scipy") as f:
            baseline=f.load()
        c.validate(saved,raws[seed],seed,k)
        c.validate(baseline,raws[seed],seed,k)
        gate(name+"_sha_t3",c.hash_owner(saved)==spec["mid_sha256"])
        gate(name+"_sha_baseline_t6",c.hash_owner(baseline)==spec["baseline_sha256"])
        gate(name+"_progress_t3",saved.attrs["landlab_step"]==3 and
             saved.attrs["landlab_t_bench"]==3*c.LANDLAB_DT)
        continued,diagnostic=advance(saved,raws[seed],seed,k,
                                    SPLIT_STEP+1,END_STEP)
        same_mass=bool(np.array_equal(continued["soil_mass_kg"].values,
                                     baseline["soil_mass_kg"].values))
        same_export=(continued.attrs["exported_soil_kg"]==
                     baseline.attrs["exported_soil_kg"])
        same_sha=c.hash_owner(continued)==c.hash_owner(baseline)
        gate(name+"_bit_exact_mass",same_mass)
        gate(name+"_exact_export",same_export)
        gate(name+"_bit_exact_owner",same_sha)
        gate(name+"_budget",diagnostic["max_abs_mass_error_kg"]<=.09216)
        if k==0:
            initial=initial_owner(raws[seed],seed,k)
            gate(name+"_zeroK_inert",same_mass and
                 np.array_equal(continued["soil_mass_kg"].values,
                                initial["soil_mass_kg"].values)
                 and continued.attrs["exported_soil_kg"]==0.)
        else:
            initial=initial_owner(raws[seed],seed,k)
            changed=int(np.count_nonzero(np.abs(
                continued["soil_mass_kg"].values-
                initial["soil_mass_kg"].values)>1e-6))
            gate(name+"_real_erosion",changed>=100 and
                 continued.attrs["exported_soil_kg"]>0.)
        with tempfile.TemporaryDirectory(prefix="world_h33_restart_") as td:
            file=pathlib.Path(td)/"final_owner.nc"
            continued.to_netcdf(file,engine="scipy")
            with xr.open_dataset(file,engine="scipy") as f:
                restored=f.load()
            c.validate(restored,raws[seed],seed,k)
            gate(name+"_final_roundtrip",c.hash_owner(restored)==c.hash_owner(continued))
        metrics.append({
            "case":name,"resume_executed_first_step":diagnostic["executed_from"],
            "resume_executed_last_step":diagnostic["executed_to"],
            "soil_mass_equal_bitwise":same_mass,"export_equal_exact":same_export,
            "owner_hash_equal":same_sha,"baseline_sha256":spec["baseline_sha256"],
            "continued_sha256":c.hash_owner(continued),
            "baseline_export_kg":float(baseline.attrs["exported_soil_kg"]),
            "continued_export_kg":float(continued.attrs["exported_soil_kg"]),
            "resume_mass_error_max_kg":diagnostic["max_abs_mass_error_kg"],
            "initial_outlet":spec["outlet_prefix"],
            "restart_outlet":diagnostic["outlet"],
        })
        gate(name+"_outlet_not_changed",diagnostic["outlet"]==spec["outlet_prefix"])
    gate("seed_specific_outcomes",manifest["cases"][NAMES[0]]["baseline_sha256"]!=
         manifest["cases"][NAMES[1]]["baseline_sha256"])
    gate("producer_replay_exact",manifest["replay_seed7321"])
    result={
        "experiment":"E6 H33 cross-process Landlab checkpoint and resume mid-history",
        "python":platform.python_version(),"landlab":landlab.__version__,
        "np_version":np.__version__,"xarray":xr.__version__,
        "precomputed_continuous_6_steps":True,
        "resume_only_steps":[4,5,6],
        "replay_observerless":True,
        "case_results":metrics,
        "negative_owner_tests":manifest.get("invalid_checkpoint_states_rejected"),
        "failed_preregistered_gates":failed,
        "limitations":"Restart evaluated only for Landlab soil + inert rigid body reservoir, same runtime version. No Bullet contact solver continuation, granular source, cross-version portability or shared time clock."
    }
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True,default=json_numpy_scalar),flush=True)
    if failed:
        raise AssertionError("H33 preregistered resume gates failed: "+", ".join(failed))


if __name__=="__main__":
    if len(sys.argv)!=4 or sys.argv[1] not in ("producer","consumer"):
        raise SystemExit("Usage: stage producer|consumer worldengine_two_seeds.npz folder")
    globals()[sys.argv[1]](sys.argv[2],sys.argv[3])
