"""H20A isolated upstream pyDeltaRCM morphology & budget diagnostics.

The delta solver is imported untouched and never publishes a mass owner.
This is SCREENING ONLY: upstream explicitly lacks strict mass conservation.
Pre-registered protocol: ETAPA_3_H20A_PROTOCOLO_PYDELTARCM.md.
"""
from __future__ import annotations

import json
import pathlib
import platform
import tempfile
import time

import numpy as np
import pyDeltaRCM

A_SEED=20261122
B_SEED=20261123
UPSTREAM_SHA="a107c1d0f6b18ac19ac15ec4586179678329ae35"
N_STEPS=12

PARAMS={
    "Length":1500.0,"Width":2000.0,"dx":50.0,
    "L0_meters":150.0,"N0_meters":250.0,
    "Np_water":100,"Np_sed":100,"itermax":1,
    "verbose":0,"save_metadata":False,
    "save_eta_grids":False,"save_eta_figs":False,
    "save_checkpoint":False,
}


def requires_real(value,label):
    try:
        f=float(value)
    except (TypeError,ValueError,AttributeError) as exc:
        raise ValueError("Missing upstream diagnostic "+label) from exc
    if not np.isfinite(f):
        raise ValueError("Upstream reported nonfinite "+label)
    return f


def run(seed,folder):
    kwargs=dict(PARAMS)
    kwargs["seed"]=int(seed)
    kwargs["out_dir"]=str(pathlib.Path(folder)/f"run_{seed}_{pathlib.Path(folder).name}")
    started=time.perf_counter()
    model=pyDeltaRCM.DeltaModel(**kwargs)
    records=[]
    try:
        initial_eta=np.asarray(model.eta_init,dtype=np.float64).copy()
        first_eta=np.asarray(model.eta,dtype=np.float64).copy()
        if initial_eta.shape!=first_eta.shape:
            raise ValueError("Initial elevation dimension mismatch")
        cumulative_input=0.
        cumulative_lost=0.
        cumulative_export=0.
        cumulative_inlet=0.
        for step in range(1,N_STEPS+1):
            model.update()
            cumulative_input+=requires_real(model.Qs0,"Qs0")*requires_real(model.dt,"dt")
            sr,mr=model._sr,model._mr
            lost=requires_real(sr.Vp_lost,"sr.Vp_lost")+requires_real(mr.Vp_lost,"mr.Vp_lost")
            export=requires_real(sr.Vp_exported,"sr.Vp_exported")+requires_real(mr.Vp_exported,"mr.Vp_exported")
            inlet=requires_real(model._Vp_inletbc,"_Vp_inletbc")
            cumulative_lost+=lost
            cumulative_export+=export
            cumulative_inlet+=inlet
            if step in (1,6,12):
                eta=np.asarray(model.eta,dtype=np.float64)
                delta=eta-initial_eta
                records.append({
                    "step":step,
                    "changed_count":int(np.count_nonzero(np.abs(delta)>1e-6)),
                    "max_abs_delta_elevation_m":float(np.max(np.abs(delta))),
                    "std_delta_elevation_m":float(np.std(delta)),
                    "cumulative_input_sediment_volume_m3":cumulative_input,
                })
        final=np.asarray(model.eta,dtype=np.float64).copy()
    finally:
        model.finalize()
    elapsed=time.perf_counter()-started
    delta=final-initial_eta
    delta_outside_inlet=delta[max(1,int(PARAMS["L0_meters"]/PARAMS["dx"])):,:]
    deposited_geometry=float(np.sum(delta)*PARAMS["dx"]**2)
    budget={
        "input_volume_m3":cumulative_input,
        "bed_change_volume_m3":deposited_geometry,
        "lost_volume_m3":cumulative_lost,
        "export_volume_m3":cumulative_export,
        "inlet_adjustment_volume_m3":cumulative_inlet,
        "apparent_bed_minus_input_fraction":float((deposited_geometry-cumulative_input)/cumulative_input) if cumulative_input!=0 else None,
        "notes":"Not a closed sediment balance. Do not count unobserved upstream non-conservation as material or inferred sink."
    }
    return {
        "initial_eta":initial_eta,"final_eta":final,
        "seed":seed,"shape":list(final.shape),"elapsed_seconds":elapsed,
        "changed_count":int(np.count_nonzero(np.abs(delta)>1e-6)),
        "changed_count_outside_initial_inlet":int(np.count_nonzero(np.abs(delta_outside_inlet)>1e-6)),
        "max_abs_delta_elevation_m":float(np.max(np.abs(delta))),
        "std_delta_elevation_m":float(np.std(delta)),
        "all_finite":bool(np.isfinite(final).all()),
        "budget_diagnostic":budget,"milestones":records
    }


def main():
    with tempfile.TemporaryDirectory(prefix="world_h20a_") as parent:
        a=run(A_SEED,str(pathlib.Path(parent)/"first"))
        ar=run(A_SEED,str(pathlib.Path(parent)/"replay"))
        b=run(B_SEED,str(pathlib.Path(parent)/"other"))
    failed=[]
    def check(key,condition):
        if not condition:failed.append(key)
    check("finite_in_all_runs",all(x["all_finite"] for x in (a,ar,b)))
    check("same_topology",a["shape"]==ar["shape"]==b["shape"] and a["shape"][0]>=20 and a["shape"][1]>=20)
    check("landscape_changes",a["changed_count"]>=5 and a["std_delta_elevation_m"]>1e-7)
    check("landscape_changes_outside_inlet",a["changed_count_outside_initial_inlet"]>0)
    check("replay_identical",np.array_equal(a["final_eta"],ar["final_eta"])
          and a["budget_diagnostic"]==ar["budget_diagnostic"])
    between=float(np.max(np.abs(a["final_eta"]-b["final_eta"])))
    check("different_seed_different_physical_outcome",between>1e-9)
    check("budget_diagnostic_nonempty",all(
        isinstance(x["budget_diagnostic"]["input_volume_m3"],float)
        and x["budget_diagnostic"]["input_volume_m3"]>0
        for x in (a,b,ar)))
    def public(d):
        return {k:v for k,v in d.items() if k not in ("initial_eta","final_eta")}
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"E3 H20A screening reduced delta model, never promoted as owner",
        "upstream":"DeltaRCM/pyDeltaRCM","upstream_sha":UPSTREAM_SHA,
        "upstream_version":getattr(pyDeltaRCM,"__version__","not exposed"),
        "python":platform.python_version(),"numpy":np.__version__,
        "scene_params":PARAMS,
        "primary":public(a),"same_seed_replay":public(ar),
        "other_seed":public(b),
        "max_bed_elevation_difference_between_seeds_m":between,
        "failed_preregistered_gates":failed,
        "warning":"The upstream DeltaRCM mathematical formulation is explicitly not strictly mass-conservative for water or sediment. No world owner adoption, no implied closed sediment budget.",
        "limitations":"Short 12-step, intentionally coarse seed-dependent delta screening; no conditioned statistical morphology benchmark, no 3D structure, no full conservation."
    },sort_keys=True),flush=True)
    if failed:
        raise AssertionError("H20A preregistered screening gates failed: "+", ".join(failed))


if __name__=="__main__":
    main()
