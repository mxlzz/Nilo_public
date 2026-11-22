"""E3/H23: late Cahn-Hilliard domain stability and three distinct initial seeds.

Prerecorded protocol ETAPA_3_H23_PROTOCOLO_PERSISTENCIA_SEMILLAS.md.
Uses native FiPy fourth-order equation and H21's existing material contract.
No new solver; H21/H22 results, parameters and code remain unchanged.
"""
from __future__ import annotations

import json
import math
import pathlib
import platform
import tempfile

import fipy
import numpy as np
import xarray as xr
from fipy import CellVariable, DefaultSolver, DiffusionTerm, Grid2D, TransientTerm

import probe_e3_h21_spinodal_fipy as h21

SEEDS=(20261122,20261123,20261124)
NSTEPS=600
EPSILON=.5
SAMPLES=(500,600)

def scenario(seed, mobility=1.):
    original_seed=h21.SEED
    try:
        h21.SEED=int(seed)
        owner=h21.make_owner(.5)
        initial=h21.fraction(owner).copy()
        mesh=Grid2D(nx=h21.NX,ny=h21.NY,dx=.25,dy=.25)
        phi=CellVariable(mesh=mesh,value=initial.ravel().copy())
        P=phi.arithmeticFaceValue
        D=float(mobility)
        equation=(TransientTerm() ==
                  DiffusionTerm(coeff=D*(1.-6.*P*(1.-P)))
                  -DiffusionTerm(coeff=(D,EPSILON**2)))
        solver=DefaultSolver()
        start_stat=h21.describe(initial)
        observations={}
        max_residual=0.
        elapsed=0.
        for index in range(NSTEPS):
            phi.setValue(h21.fraction(owner).ravel())
            dt=min(100., math.exp(-5.+.01*index))
            equation.solve(var=phi,dt=dt,solver=solver)
            next_phi=np.asarray(phi.value,dtype=np.float64).reshape((h21.NY,h21.NX))
            if not np.isfinite(next_phi).all() or np.any((next_phi<0.)|(next_phi>1.)):
                print("WORLD_EVAL_JSON "+json.dumps({
                    "experiment":"E3 H23",
                    "failed_preregistered_gates":["nonphysical_phi_or_nonfinite"],
                    "seed":seed,"mobility":mobility,"step":index+1,
                    "min_phi":float(np.nanmin(next_phi)),
                    "max_phi":float(np.nanmax(next_phi)),
                }),flush=True)
                raise ValueError("Out-of-range composition; no clipping allowed")
            candidate=owner.copy(deep=True)
            candidate["material_mass_kg"].values[0]=next_phi
            candidate["material_mass_kg"].values[1]=1.-next_phi
            try:
                b=h21.validate(candidate)
            except ValueError as error:
                print("WORLD_EVAL_JSON "+json.dumps({
                    "experiment":"E3 H23",
                    "failed_preregistered_gates":["owner_invariant_invalid"],
                    "seed":seed,"mobility":mobility,"step":index+1,
                    "error":str(error)
                }),flush=True)
                raise
            max_residual=max(max_residual,abs(b["mass_A_residual_kg"]))
            owner=candidate
            elapsed+=dt
            step=index+1
            if step in SAMPLES:
                observations[step]=h21.fraction(owner).copy()
        return {
            "owner":owner, "initial":initial, "snapshots":observations,
            "seed":int(seed),"mobility":float(mobility),
            "initial_stats":start_stat,"final_stats":h21.describe(h21.fraction(owner)),
            "max_species_mass_error_kg":max_residual,
            "total_mass_kg":float(owner["material_mass_kg"].sum()),
            "time_simulated":elapsed,
            "state_sha":h21.digest(owner),
        }
    finally:
        h21.SEED=original_seed


def domain_statistics(s):
    binary=s["snapshots"][600]>.5
    preceding=s["snapshots"][500]>.5
    both=np.logical_or(binary,preceding)
    persistence=float(np.logical_and(binary,preceding).sum()/both.sum()) if both.any() else 0.
    conditioned=h21.null_conditioned(binary)
    stats=s["final_stats"]
    delta=stats["same_edge_score"]-conditioned["p95_same_edges"]
    segregation=(stats["q05"]<.3 and stats["q95"]>.7 and
                 stats["variance"]>2*s["initial_stats"]["variance"])
    structured=delta>.08
    persists=persistence>=.6
    return {
        "seed":s["seed"],
        "last_step":NSTEPS,
        "initial_stats":s["initial_stats"],
        "final_stats":stats,
        "null_model":conditioned,
        "same_edge_excess_over_p95":delta,
        "jaccard_500_600":persistence,
        "segregation_pass":segregation,
        "structure_pass":structured,
        "persistence_pass":persists,
        "combined_structure_and_persistence_pass":structured and persists,
        "max_species_mass_error_kg":s["max_species_mass_error_kg"],
        "total_mass_kg":s["total_mass_kg"],
        "state_sha":s["state_sha"],
        "simulated_time":s["time_simulated"],
    }


def main():
    runs=[scenario(seed) for seed in SEEDS]
    no_mob=scenario(SEEDS[0],0.)
    replay=scenario(SEEDS[0])
    info=[domain_statistics(s) for s in runs]
    bad=[]
    def gate(name,condition):
        if not condition:
            bad.append(name)
    gate("mass_owner_all_cases",all(
        x["max_species_mass_error_kg"]<1e-4 and
        abs(x["total_mass_kg"]-400.)<1e-9 for x in runs+[no_mob,replay]))
    gate("segregation_3_of_3",all(row["segregation_pass"] for row in info))
    gate("conditioned_spatial_structure_2_of_3",
         sum(row["structure_pass"] for row in info)>=2)
    gate("temporal_persistence_2_of_3",
         sum(row["persistence_pass"] for row in info)>=2)
    gate("structure_and_persistence_same_2_seeds",
         sum(row["combined_structure_and_persistence_pass"] for row in info)>=2)
    diversity=[]
    for i in range(len(runs)):
        for j in range(i+1,len(runs)):
            difference=float(np.mean(
                (runs[i]["snapshots"][600]>.5)!=(runs[j]["snapshots"][600]>.5)))
            diversity.append({"seeds":[runs[i]["seed"],runs[j]["seed"]],
                              "different_cells_fraction":difference})
    gate("seed_changes_result",any(x["different_cells_fraction"]>=.10 for x in diversity))
    gate("zero_mobility_stable",np.array_equal(no_mob["initial"],
                                             h21.fraction(no_mob["owner"])))
    gate("exact_replay",np.array_equal(
        runs[0]["owner"]["material_mass_kg"].values,
        replay["owner"]["material_mass_kg"].values)
        and all(np.array_equal(runs[0]["snapshots"][t],replay["snapshots"][t])
                for t in SAMPLES)
        and runs[0]["state_sha"]==replay["state_sha"])

    rejected=h21.reject_candidates(runs[0]["owner"])
    with tempfile.TemporaryDirectory(prefix="world_h23_") as folder:
        path=pathlib.Path(folder)/"two_species_owner.nc"
        runs[0]["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:
            restored=f.load()
        h21.validate(restored)
        gate("checkpoint_exact",np.array_equal(
            runs[0]["owner"]["material_mass_kg"].values,
            restored["material_mass_kg"].values)
            and h21.digest(restored)==runs[0]["state_sha"])
        bytes_written=path.stat().st_size

    result={
        "experiment":"E3 H23 late-time conservation and morphology across 3 seeds",
        "epsilon":EPSILON, "seeds":SEEDS,"steps":NSTEPS,"samples":SAMPLES,
        "python":platform.python_version(),"fipy":fipy.__version__,
        "numpy":np.__version__,"xarray":xr.__version__,
        "all_seeds":info,"diversity":diversity,
        "no_mobility_max_change":float(np.max(np.abs(
            no_mob["initial"]-h21.fraction(no_mob["owner"])))),
        "negative_states_rejected":rejected,
        "replay_exact":True,"checkpoint_bytes":bytes_written,
        "failed_preregistered_gates":bad,
        "limitations":"Only 3 seeds, two late snapshots and one abstract binary mixture. Neither three-dimensional material mechanics nor physical geologic stability is inferred."
    }
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True),flush=True)
    if bad:
        raise AssertionError("H23 preregistered gates failed: "+", ".join(bad))

if __name__=="__main__":
    main()
