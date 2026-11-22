"""H28 hard-core Monte Carlo randomization of reproducible H26 geometry.

Only a geometric NULL sampler (existing hard-sphere Metropolis method).
No new material/forces, no modification of H26 original physics.
Protocol: ETAPA_3_H28_PROTOCOLO_NULO_MCMC.md (preregistered).
"""
from __future__ import annotations

import json
import math
import platform
from importlib.metadata import version

import numpy as np

import probe_e3_h26_gravity_feed as h26
import probe_e3_h24_granular_pile as h24
import probe_e3_h27_hardcore_spatial_null as h27

HARD_MIN_DIST=2*h24.R-.002
BURN_IN=20000
BETWEEN=2000
SAMPLES_PER_CHAIN=128
CHAIN_SEEDS={20261122:(2026112801,2026112802),
             20261123:(2026112901,2026112902)}

def minimum_separation(points):
    d=np.linalg.norm(points[:,None,:]-points[None,:,:],axis=2)
    np.fill_diagonal(d,np.inf)
    return float(np.min(d))

def chain(positions, seed):
    """Single-particle hard-core moves, heights & radial membership fixed."""
    init=np.asarray(positions,dtype=np.float64)
    pos=init.copy()
    n=len(pos)
    radii=np.linalg.norm(init[:,:2],axis=1)
    median=float(np.median(radii))
    maximum=float(np.max(radii))
    membership=(radii>median).astype(np.int8)
    lower=np.where(membership==0,0.,median)
    upper=np.where(membership==0,median,maximum)
    rng=np.random.default_rng(seed)
    total=BURN_IN+BETWEEN*SAMPLES_PER_CHAIN
    accepted=0
    sizes=[]
    edges=[]
    min_dist=float("inf")
    for iteration in range(1,total+1):
        k=int(rng.integers(n))
        old_xy=pos[k,:2]
        if rng.random()<.8:
            test_xy=old_xy+rng.normal(0.,.05,size=2)
        else:
            angle=rng.uniform(0.,2*math.pi)
            radial=math.sqrt(rng.uniform(float(lower[k]**2),float(upper[k]**2)))
            test_xy=np.array([radial*math.cos(angle),radial*math.sin(angle)])
        test_radius=float(np.linalg.norm(test_xy))
        if lower[k] - 1e-12<=test_radius<=upper[k]+1e-12:
            distances=np.sqrt(np.sum((pos[:,:2]-test_xy)**2,axis=1)
                              + (pos[:,2]-pos[k,2])**2)
            distances[k]=np.inf
            if np.all(distances>=HARD_MIN_DIST):
                pos[k,:2]=test_xy
                accepted+=1
        if iteration>BURN_IN and (iteration-BURN_IN)%BETWEEN==0:
            if not np.array_equal(pos[:,2],init[:,2]):
                raise AssertionError("MCMC modified heights")
            rb=np.linalg.norm(pos[:,:2],axis=1)
            if not np.array_equal((rb>median).astype(np.int8),membership):
                raise AssertionError("MCMC modified radial-band count")
            distance=minimum_separation(pos)
            min_dist=min(min_dist,distance)
            if distance<HARD_MIN_DIST-1e-12:
                raise AssertionError("Hard-core exclusion broken in MCMC")
            st=h27.largest_near_component(pos)
            sizes.append(st["largest"])
            edges.append(st["edges"])
    displacement=np.linalg.norm(pos[:,:2]-init[:,:2],axis=1)
    return {
        "seed":seed,
        "samples":sizes,
        "edge_counts":edges,
        "acceptance_ratio":float(accepted/total),
        "fraction_grains_displaced_over_R":float(np.mean(displacement>h24.R)),
        "median_final_xy_displacement_m":float(np.median(displacement)),
        "mean_largest_component":float(np.mean(sizes)),
        "min_distance_in_saved_samples_m":min_dist,
        "n_samples":len(sizes),
        "burnin_proposals":BURN_IN,
        "between_samples_proposals":BETWEEN,
    }

def sample_case(owner,physical_seed):
    positions=owner["position_m"].values
    start_min=minimum_separation(positions)
    observed=h27.largest_near_component(positions)
    if start_min<HARD_MIN_DIST-1e-12:
        result={"physical_seed":physical_seed,
                "initial_min_center_distance_m":start_min,
                "hardcore_minimum_m":HARD_MIN_DIST,
                "observed":observed,
                "preregistered_null_invalid_reason":"H26 snapshot overlaps more than 2mm; MCMC has no valid initial state"}
        return result
    chains=[chain(positions,seed) for seed in CHAIN_SEEDS[physical_seed]]
    nulls=chains[0]["samples"]+chains[1]["samples"]
    observed_n=observed["largest"]
    p95=int(np.quantile(nulls,.95,method="higher"))
    empirical=(1+sum(x>=observed_n for x in nulls))/(1+len(nulls))
    acceptance=all(
        c["acceptance_ratio"]>.01 and
        c["fraction_grains_displaced_over_R"]>.5 and
        c["n_samples"]==SAMPLES_PER_CHAIN
        for c in chains)
    chain_mean_diff=abs(chains[0]["mean_largest_component"]-
                        chains[1]["mean_largest_component"])
    compact_chains=[{k:v for k,v in c.items() if k not in ("samples","edge_counts")}
                    for c in chains]
    result={
        "physical_seed":physical_seed,
        "initial_min_center_distance_m":start_min,
        "hardcore_minimum_m":HARD_MIN_DIST,
        "observed":observed,
        "chains":compact_chains,
        "nnull":len(nulls),
        "null_largest_mean":float(np.mean(nulls)),
        "null_largest_p95":p95,
        "null_largest_max":int(np.max(nulls)),
        "null_edges_mean":float(np.mean(chains[0]["edge_counts"]+
                                       chains[1]["edge_counts"])),
        "mean_component_difference_between_chains":chain_mean_diff,
        "chain_acceptance_mobility_gates":acceptance,
        "chain_mean_agreement_gate":chain_mean_diff<10,
        "empirical_one_sided_p":empirical,
        "observed_minus_null_p95":observed_n-p95,
        "geometric_pattern_significance_gate":observed_n>=p95+10 and empirical<=.05,
    }
    return result

def main():
    a=h26.main_scene(20261122,True)
    b=h26.main_scene(20261123,True)
    fail=[]
    def gate(key,success):
        if not success:
            fail.append(key)
    gate("H26_original_seed1_SHA",a["owner_sha"]==h27.EXPECTED_SHA[20261122])
    gate("H26_original_seed2_SHA",b["owner_sha"]==h27.EXPECTED_SHA[20261123])
    gate("H26_supported_and_resting",all(z["largest_contact_component"]>=45
          and z["p90_final_speed_m_s"]<.08 for z in (a,b)))
    results=[]
    for q in (a,b):
        x=sample_case(q["owner"],q["seed"])
        x["original_H26_sha256"]=q["owner_sha"]
        x["force_contact_largest_component"]=q["largest_contact_component"]
        results.append(x)
        seed=q["seed"]
        gate(f"{seed}_nonoverlap_initial",
             "preregistered_null_invalid_reason" not in x)
        if "preregistered_null_invalid_reason" not in x:
            gate(f"{seed}_256_samples",x["nnull"]==256)
            gate(f"{seed}_chains_mobile",x["chain_acceptance_mobility_gates"])
            gate(f"{seed}_chain_means_agree",x["chain_mean_agreement_gate"])
            gate(f"{seed}_spatial_null_rejected",x["geometric_pattern_significance_gate"])
        else:
            fail.append(f"{seed}_null_unavailable")
    report={
        "experiment":"E3 H28 two-chain hard-core MCMC conditioned random material null",
        "python":platform.python_version(),"numpy":np.__version__,
        "pybullet":version("pybullet"),
        "model":"H26 original two seeds and native Bullet friction",
        "mcmc_per_chain_burnin":BURN_IN,
        "mcmc_between_samples":BETWEEN,
        "mcmc_samples_per_chain":SAMPLES_PER_CHAIN,
        "mcmc_chains_per_physical_seed":2,
        "minimum_center_separation_m":HARD_MIN_DIST,
        "same_near_contact_threshold_m":2*h24.R+h27.NEAR_GAP_M,
        "results":results,
        "failed_preregistered_gates":fail,
        "limitations":"Hard-core MCMC remains autocorrelated; diagnostics check mobility and two-chain agreement but not full mixing/independent effective sample size. The null holds each grain Z and radial-bin membership, not the exact radial distribution or force-bearing equilibrium. No general evidence of geology or autonomous world."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if fail:
        raise AssertionError("H28 preregistered null gates failed: "+", ".join(fail))

if __name__=="__main__":
    main()
