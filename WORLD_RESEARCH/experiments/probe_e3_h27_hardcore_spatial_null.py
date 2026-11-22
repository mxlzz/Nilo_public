"""E3 H27: geometric hard-sphere conditioned null against H26 granular heaps.

Strictly a spatial statistical test: no new physical law or simulated forces.
The preregistered test keeps each grain's height, radial-bin membership
and hard-sphere exclusion while randomizing XY coordinates. Original H26
and its friction/contact physics remain untouched.
"""
from __future__ import annotations

import json
import math
import platform
from importlib.metadata import version

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

import probe_e3_h26_gravity_feed as h26
import probe_e3_h24_granular_pile as h24

N_NULL=256
MAX_ATTEMPTS_PER_GRAIN=1000
MAX_RESTARTS=5
NEAR_GAP_M=.015
RNG_SEEDS={20261122:20261127,20261123:20261128}
EXPECTED_SHA={
    20261122:"ac1dd51b214ede889328a672237a07a850ba7e183b0fa4ed4ffbf73b4e223697",
    20261123:"b364de5794470a7677eed42d5e544fcfbfa0fb282db2dc6cbecf2c651391ab4d",
}

def largest_near_component(positions):
    """Same Euclidean near-neighbor statistic for real and null geometries."""
    dist=np.linalg.norm(positions[:,None,:]-positions[None,:,:],axis=2)
    edges=(dist<=2*h24.R+NEAR_GAP_M)
    np.fill_diagonal(edges,False)
    count,labels=connected_components(csr_matrix(edges),directed=False)
    lengths=np.bincount(labels,minlength=count)
    return {"largest":int(lengths.max()),"edges":int(np.count_nonzero(np.triu(edges,1))),
            "components":int(count)}

def build_null_one(rng, height, membership, midpoint, maximum):
    """Hard-core rejection sampler, bounded by preregistered budgets."""
    n=len(height)
    for restart in range(MAX_RESTARTS):
        output=np.zeros((n,3),dtype=np.float64)
        filled=0
        failed=False
        order=rng.permutation(n)
        for grain in order:
            low=0. if membership[grain]==0 else midpoint
            high=midpoint if membership[grain]==0 else maximum
            placed=False
            for _ in range(MAX_ATTEMPTS_PER_GRAIN):
                radial=math.sqrt(rng.uniform(low**2,high**2))
                angle=rng.uniform(0.,2*math.pi)
                candidate=np.array((radial*math.cos(angle),
                     radial*math.sin(angle),height[grain]),dtype=np.float64)
                if filled:
                    separation=np.linalg.norm(output[order[:filled]]-candidate,axis=1)
                    if np.any(separation<2*h24.R):
                        continue
                output[grain]=candidate
                filled+=1
                placed=True
                break
            if not placed:
                failed=True
                break
        if not failed and filled==n:
            dist=np.linalg.norm(output[:,None,:]-output[None,:,:],axis=2)
            np.fill_diagonal(dist,np.inf)
            if np.min(dist)<2*h24.R-1e-12:
                raise AssertionError("Null placed overlapping grains")
            return output,restart
    return None,MAX_RESTARTS

def run_nulls(owner,seed):
    positions=owner["position_m"].values
    if positions.shape!=(h24.N,3):
        raise AssertionError("Unexpected geometry")
    radial=np.linalg.norm(positions[:,:2],axis=1)
    median=float(np.median(radial))
    maximum=float(np.max(radial))
    if not (0<median<maximum):
        raise ValueError("Degenerate radial bins")
    membership=(radial>median).astype(np.int8)
    height=positions[:,2].copy()
    rng=np.random.default_rng(RNG_SEEDS[seed])
    observed=largest_near_component(positions)
    sizes=[]
    counts=[]
    restarts_used=0
    first_failed_trial=None
    for trial in range(N_NULL):
        points,restart=build_null_one(rng,height,membership,median,maximum)
        restarts_used+=restart
        if points is None:
            first_failed_trial=trial
            break
        if not np.array_equal(points[:,2],height):
            raise AssertionError("Null changed height of a grain")
        check_radius=np.linalg.norm(points[:,:2],axis=1)
        if not np.array_equal((check_radius>median).astype(np.int8),membership):
            raise AssertionError("Null changed its radial band")
        statistic=largest_near_component(points)
        sizes.append(statistic["largest"])
        counts.append(statistic["edges"])
    p95=int(np.quantile(sizes,.95,method="higher")) if sizes else None
    pvalue=(1+sum(v>=observed["largest"] for v in sizes))/(len(sizes)+1)
    return {
        "seed":seed,"observed_geometric":observed,
        "radial_median_m":median,"radial_max_m":maximum,
        "inner_grains":int(np.count_nonzero(membership==0)),
        "outer_grains":int(np.count_nonzero(membership==1)),
        "nulls_requested":N_NULL,"nulls_completed":len(sizes),
        "first_failed_trial_index":first_failed_trial,
        "null_total_restarts":restarts_used,
        "null_component_mean":float(np.mean(sizes)) if sizes else None,
        "null_component_p95":p95,
        "null_component_max":int(max(sizes)) if sizes else None,
        "null_edges_mean":float(np.mean(counts)) if counts else None,
        "empirical_one_sided_p":pvalue,
        "component_margin_over_p95":int(observed["largest"]-p95) if p95 is not None else None,
    }

def main():
    a=h26.main_scene(20261122,True)
    b=h26.main_scene(20261123,True)
    checks=[]
    def gate(name,result):
        if not result:
            checks.append(name)
    gate("identical_H26_seed1_sha",a["owner_sha"]==EXPECTED_SHA[20261122])
    gate("identical_H26_seed2_sha",b["owner_sha"]==EXPECTED_SHA[20261123])
    gate("H26_both_force_supported",a["largest_contact_component"]>=45
         and b["largest_contact_component"]>=45
         and a["p90_final_speed_m_s"]<.08
         and b["p90_final_speed_m_s"]<.08)
    results=[]
    for obj in (a,b):
        data=run_nulls(obj["owner"],obj["seed"])
        data["physical_force_contact_component"]=obj["largest_contact_component"]
        data["physical_grain_contacts"]=obj["grain_positive_contacts"]
        data["same_H26_owner_sha"]=obj["owner_sha"]
        results.append(data)
        gate(f"{obj['seed']}_256_valid_hardcore_nulls",
             data["nulls_completed"]==N_NULL)
        gate(f"{obj['seed']}_geometric_pattern_exceeds_null",
             data["component_margin_over_p95"] is not None
             and data["component_margin_over_p95"]>=10
             and data["empirical_one_sided_p"]<=.05)
    metrics={
        "experiment":"E3 H27 hard-sphere height-and-radial-bin-conditioned null",
        "python":platform.python_version(),"pybullet":version("pybullet"),
        "numpy":np.__version__,"null_count":N_NULL,
        "radius_m":h24.R,"near_contact_gap_m":NEAR_GAP_M,
        "max_attempts_per_grain":MAX_ATTEMPTS_PER_GRAIN,
        "max_global_restarts_per_null":MAX_RESTARTS,
        "real_material_mass_kg":a["total_mass_kg"],
        "results":results,
        "failed_preregistered_gates":checks,
        "limitations":"The null samples NON-overlapping hard spheres but is not itself in force equilibrium. It preserves each grain height and inner/outer radial membership, NOT exact radial positions or full pairwise correlations. A positive comparison demonstrates spatial proximity beyond this conditional placement null, not material cohesion or a new physical law."
    }
    print("WORLD_EVAL_JSON "+json.dumps(metrics,sort_keys=True),flush=True)
    if checks:
        raise AssertionError("H27 preregistered conditional null gates failed: "+", ".join(checks))

if __name__=="__main__":
    main()
