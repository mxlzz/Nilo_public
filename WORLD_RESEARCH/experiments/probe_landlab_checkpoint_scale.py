"""H13: true process-restart checkpoint and hydrologic scaling.

Protocol pre-registered in ETAPA_0_9_PROTOCOLO_H13_PERSISTENCIA_ESCALA.md.
Existing Landlab components only: OverlandFlow (de Almeida), Green-Ampt.
Model physics is NOT implemented here.

This test creates and reads only its OWN pickle; NEVER load arbitrary pickles.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import pickle
import platform
import resource
import sys
import time
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import OverlandFlow, SoilInfiltrationGreenAmpt

DX=1.0
DT=0.5
RATE=2e-5
K=1e-6
INIT_FILM=1e-8
INIT_INF=.01
TOTAL_STEPS=80
PREP_STEPS=40
FIELDS = (
    ("node","topographic__elevation"),
    ("node","surface_water__depth"),
    ("node","soil_water_infiltration__depth"),
    ("link","surface_water__discharge"),
    ("link","water_surface__gradient"),
)


def create_world(size):
    g=RasterModelGrid((size,size),xy_spacing=DX)
    x,y=g.node_x,g.node_y
    cx=(size-1)*.5
    cy=cx
    g.at_node["topographic__elevation"]=(
        1.0+.01*y+.003*x+.03*np.exp(-((x-cx)**2+(y-cy)**2)/4.)
    )
    g.at_node["surface_water__depth"]=np.zeros(g.number_of_nodes)
    g.at_node["soil_water_infiltration__depth"]=np.full(g.number_of_nodes,INIT_INF)
    g.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,left_is_closed=True,
        right_is_closed=True,top_is_closed=True)
    flow=OverlandFlow(g,h_init=INIT_FILM,steep_slopes=False,
        rainfall_intensity=RATE,mannings_n=.03)
    inf=SoilInfiltrationGreenAmpt(g,hydraulic_conductivity=K,
        soil_type="sandy loam",surface_water_minimum_depth=INIT_FILM)
    return g,flow,inf


def run_steps(g,flow,inf,n):
    for _ in range(n):
        flow.run_one_step(DT)
        inf.run_one_step(DT)


def arrays(g):
    return {f"{where}:{name}":np.array(g[where][name],copy=True)
            for where,name in FIELDS}


def budget(g,steps):
    core=g.core_nodes
    a=g.cell_area_at_node[core]
    surf=float(np.sum(g.at_node["surface_water__depth"][core]*a))
    inf=float(np.sum(g.at_node["soil_water_infiltration__depth"][core]*a))
    area=float(np.sum(a))
    expected=INIT_INF*area+INIT_FILM*area+RATE*DT*steps*area
    residual=surf+inf-expected
    rain=RATE*DT*steps*area
    return {
        "area_m2":area,
        "rain_m3":rain,
        "surface_water_m3":surf,
        "infiltrated_cumulative_m3":inf,
        "residual_m3":residual,
        "relative_residual_on_rain":abs(residual)/max(rain,1e-12),
        "min_depth_m":float(np.min(g.at_node["surface_water__depth"][core])),
        "min_infiltration_m":float(np.min(g.at_node["soil_water_infiltration__depth"][core])),
    }


def ensure_valid(g,n):
    b=budget(g,n)
    assert b["relative_residual_on_rain"]<.001,b
    assert b["min_depth_m"]>=-1e-9
    assert b["min_infiltration_m"]>=0
    assert all(np.isfinite(v).all() for v in arrays(g).values())
    return b


def checkpaths(folder):
    return {
        "ref":folder/"baseline.npz",
        "checkpoint":folder/"checkpoint.pkl",
        "metadata":folder/"checkpoint.json",
    }


def mode_baseline(folder):
    g,flow,inf=create_world(12)
    run_steps(g,flow,inf,TOTAL_STEPS)
    b=ensure_valid(g,TOTAL_STEPS)
    np.savez_compressed(checkpaths(folder)["ref"],**arrays(g))
    print("WORLD_EVAL_JSON "+json.dumps({
        "stage":"H13a baseline", "steps":TOTAL_STEPS,
        "landlab_version":landlab.__version__, "budget":b
    },sort_keys=True))


def mode_prepare(folder):
    g,flow,inf=create_world(12)
    run_steps(g,flow,inf,PREP_STEPS)
    b=ensure_valid(g,PREP_STEPS)
    packed=pickle.dumps((g,flow,inf),protocol=pickle.HIGHEST_PROTOCOL)
    p=checkpaths(folder)
    p["checkpoint"].write_bytes(packed)
    metadata={
        "landlab_version":landlab.__version__,
        "python":platform.python_version(),
        "checkpoint_sha256":hashlib.sha256(packed).hexdigest(),
        "steps_completed":PREP_STEPS,
        "bytes":len(packed),
        "policy":"Only load own checkpoint produced in this CI job."
    }
    p["metadata"].write_text(json.dumps(metadata,indent=2))
    print("WORLD_EVAL_JSON "+json.dumps({
        "stage":"H13a checkpoint prepared","metadata":metadata,
        "budget":b
    },sort_keys=True))


def mode_resume(folder):
    p=checkpaths(folder)
    meta=json.loads(p["metadata"].read_text())
    packed=p["checkpoint"].read_bytes()
    assert hashlib.sha256(packed).hexdigest()==meta["checkpoint_sha256"]
    assert meta["landlab_version"]==landlab.__version__
    assert meta["python"]==platform.python_version()
    g,flow,inf=pickle.loads(packed) # own checkpoint only
    assert flow.grid is g, "solver grid identity broken by pickle"
    assert inf.grid is g, "infiltration grid identity broken by pickle"
    run_steps(g,flow,inf,TOTAL_STEPS-PREP_STEPS)
    b=ensure_valid(g,TOTAL_STEPS)
    actual=arrays(g)
    with np.load(p["ref"]) as expected:
        per_field={key:bool(np.array_equal(v,expected[key])) for key,v in actual.items()}
    print("WORLD_EVAL_JSON "+json.dumps({
        "stage":"H13a resume in another Python process",
        "checkpoint_bytes":meta["bytes"],
        "checksum_verified":True,
        "same_grid_object":True,
        "exact_match_per_field":per_field,
        "budget":b,
    },sort_keys=True))
    assert all(per_field.values()),"H13a checkpointed replay differs from uninterrupted run"


def mode_scale(size):
    t0=time.perf_counter()
    g,flow,inf=create_world(size)
    setup_s=time.perf_counter()-t0
    t1=time.perf_counter()
    n=60
    run_steps(g,flow,inf,n)
    compute_s=time.perf_counter()-t1
    b=ensure_valid(g,n)
    metrics={
        "test":"H13b scale existing OverlandFlow+GreenAmpt",
        "landlab":landlab.__version__,
        "shape":[size,size],
        "total_nodes":g.number_of_nodes,
        "active_nodes":len(g.core_nodes),
        "steps":n,
        "simulated_seconds":n*DT,
        "setup_seconds":round(setup_s,6),
        "compute_seconds":round(compute_s,6),
        "compute_ms_per_node_step":compute_s*1000/(g.number_of_nodes*n),
        "maxrss_kib_linux":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "water_budget":b,
        "scope":"Hydrologic pair only; current runner, no geomorphic/vegetation solver."
    }
    print("WORLD_EVAL_JSON "+json.dumps(metrics,sort_keys=True))


if __name__=="__main__":
    if len(sys.argv)<2:
        raise SystemExit("Usage: script [baseline|prepare|resume|scale] [folder|size]")
    mode=sys.argv[1]
    if mode=="scale":
        mode_scale(int(sys.argv[2]))
    else:
        folder=pathlib.Path(sys.argv[2])
        folder.mkdir(parents=True,exist_ok=True)
        {"baseline":mode_baseline,"prepare":mode_prepare,"resume":mode_resume}[mode](folder)
