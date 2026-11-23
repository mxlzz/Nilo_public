"""E4 H29: pinned upstream WorldEngine generates two reproducible raw terrains.

Python 3.11 producer. No physical meter conversion; raw heights are arbitrary.
Pre-registered ETAPA_4_H29_PROTOCOLO_SEMILLAS_TERRITORIO.md.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import numpy as np
from worldengine.plates import world_gen

UPSTREAM_SHA="3b9113ecfad884cab4b32081d138a15e6262ada8"
SHAPE=(16,32)
SEEDS=(7321,8128)
GLOBAL_SEED=1234

def height(seed):
    np.random.seed(GLOBAL_SEED)
    w=world_gen("world-research",SHAPE[1],SHAPE[0],int(seed),verbose=False)
    a=np.asarray(w.layers["elevation"].data,dtype="<f8").copy()
    if a.shape!=SHAPE or not np.isfinite(a).all():
        raise ValueError("Generator output is not finite 16x32")
    if float(np.max(a)-np.min(a))<=0. or float(np.std(a))<=1e-8:
        raise ValueError("Flat generated terrain")
    return a

def digest(array):
    return hashlib.sha256(np.ascontiguousarray(array,dtype="<f8").tobytes()).hexdigest()

def main(destination):
    a=height(SEEDS[0])
    b=height(SEEDS[1])
    replay=height(SEEDS[0])
    diffs=int(np.count_nonzero(np.abs(a-b)>1e-8))
    gates=[]
    if not np.array_equal(a,replay):
        gates.append("exact_seed_and_global_rng_replay")
    if digest(a)==digest(b) or diffs<.1*a.size:
        gates.append("different_seed_terrain")
    out=pathlib.Path(destination)
    out.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(
        out,
        elevation_seed_7321=a,
        elevation_seed_8128=b,
        generator_seeds=np.array(SEEDS,dtype=np.int64),
        global_numpy_seed=np.array([GLOBAL_SEED],dtype=np.int64),
        source_sha256=np.array([digest(a),digest(b)]),
        worldengine_revision=np.array([UPSTREAM_SHA]),
        native_height_units=np.array(["arbitrary"]),
    )
    with np.load(out,allow_pickle=False) as data:
        if not np.array_equal(a,data["elevation_seed_7321"]) or not np.array_equal(b,data["elevation_seed_8128"]):
            gates.append("producer_npz_roundtrip")
        if list(data["generator_seeds"])!=list(SEEDS):
            gates.append("producer_npz_seeds")
    report={
        "experiment":"E4 H29 original WorldEngine raw heightmap 2 seeds and replay",
        "upstream":"Mindwerks/worldengine","source_commit":UPSTREAM_SHA,
        "numpy":np.__version__,"seed_global":GLOBAL_SEED,
        "seeds":SEEDS,"shape":SHAPE,
        "heights_raw_units":"arbitrary, NOT meters",
        "seed_7321":{"sha256":digest(a),"min":float(a.min()),"max":float(a.max()),"std":float(a.std())},
        "seed_8128":{"sha256":digest(b),"min":float(b.min()),"max":float(b.max()),"std":float(b.std())},
        "differing_cells_gt_1e_minus8":diffs,
        "same_seed_replay_exact":bool(np.array_equal(a,replay)),
        "output_npz_bytes":out.stat().st_size,
        "preregistered_gates_failed":gates,
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if gates:
        raise AssertionError("H29 generator gates failed: "+", ".join(gates))

if __name__=="__main__":
    main(sys.argv[1])
