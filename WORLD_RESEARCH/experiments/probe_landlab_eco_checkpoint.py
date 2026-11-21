"""H14: checkpoint/restart of actual 90-day Landlab ecology+soil system.

H9 original scenario used as reference without modifying it. Existing
SoilMoisture, Vegetation, DepthDependentDiffuser supply all process physics.
Checkpoint is a tuple of OUR OWN generated components, not external data.
Pre-registered in ETAPA_0_10_PROTOCOLO_H14_ECO_CHECKPOINT.md.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import pickle
import platform
import sys
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import SoilMoisture, Vegetation, DepthDependentDiffuser
from probe_landlab_90day_loop import scenario as h9_reference
from probe_landlab_90day_loop import ALPHA, KB, DEPTH, H0, DAYS_PER_WINDOW

TOTAL_DAYS=90
HALF_DAY=45

def build():
    g=RasterModelGrid((8,8),xy_spacing=1.0)
    x,y=g.node_x,g.node_y
    topo=.025*x+.03*y+2.0*np.exp(-((x-3.5)**2+(y-3.5)**2)/3.)
    g.at_node["topographic__elevation"]=topo.copy()
    g.at_node["soil__depth"]=np.full(g.number_of_nodes,H0)
    g.at_node["bedrock__elevation"]=topo-H0
    g.at_node["soil_production__rate"]=np.zeros(g.number_of_nodes)
    g.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,left_is_closed=True,
        right_is_closed=True,top_is_closed=True)
    n=g.number_of_cells
    g.at_cell["vegetation__plant_functional_type"]=np.zeros(n,dtype=int)
    g.at_cell["vegetation__cover_fraction"]=np.full(n,.45)
    g.at_cell["vegetation__live_leaf_area_index"]=np.full(n,.85)
    g.at_cell["surface__potential_evapotranspiration_rate"]=np.full(n,8.)
    g.at_cell["surface__potential_evapotranspiration_30day_mean"]=np.full(n,8.)
    g.at_cell["soil_moisture__initial_saturation_fraction"]=np.full(n,.25)
    g.at_cell["rainfall__daily_depth"]=np.zeros(n)
    soil=SoilMoisture(g)
    veg=Vegetation(g,Bdead_init=0.0)
    soil.Tr=1.;soil.Tb=23.
    veg.Tr=1.;veg.Tb=23.
    velocity=np.full(g.number_of_links,KB*np.exp(-ALPHA*.45)/DEPTH)
    creep=DepthDependentDiffuser(g,soil_transport_velocity=velocity,
                                soil_transport_decay_depth=DEPTH)
    core=g.core_nodes
    vol_init=float(np.sum(g.at_node["soil__depth"][core] *
                          g.cell_area_at_node[core]))
    return {
        "grid":g,"soil":soil,"veg":veg,"creep":creep,
        "velocity":velocity,
        "initial_volume":vol_init,
        "completed_days":0,
        "windows":[],
    }

def evolve(state,until_day):
    g=state["grid"]
    soil=state["soil"]
    veg=state["veg"]
    creep=state["creep"]
    velocity=state["velocity"]
    core=g.core_nodes
    area=g.cell_area_at_node[core]
    for day in range(state["completed_days"],until_day):
        g.at_cell["rainfall__daily_depth"][:]=12.0 if day%5==0 else 0.
        soil.update()
        veg.update()
        if (day+1)%DAYS_PER_WINDOW==0:
            cover=np.asarray(g.at_cell["vegetation__cover_fraction"]).copy()
            biomass=np.asarray(g.at_cell["vegetation__live_biomass"]).copy()
            saturation=np.asarray(g.at_cell["soil_moisture__saturation_fraction"]).copy()
            Vnodes=np.full(g.number_of_nodes,.45)
            Vnodes[g.node_at_cell]=cover
            Vlinks=.5*(Vnodes[g.node_at_link_tail]+Vnodes[g.node_at_link_head])
            velocity[:]=KB*np.exp(-ALPHA*Vlinks)/DEPTH
            before=g.at_node["topographic__elevation"].copy()
            creep.run_one_step(dt=DAYS_PER_WINDOW/90.0)
            after=g.at_node["topographic__elevation"].copy()
            vol=float(np.sum(g.at_node["soil__depth"][core]*area))
            state["windows"].append({
               "window":(day+1)//DAYS_PER_WINDOW,
               "hydrological_years":float(soil.current_time),
               "mean_biomass":float(np.mean(biomass)),
               "mean_cover":float(np.mean(cover)),
               "mean_saturation":float(np.mean(saturation)),
               "mean_diffusivity":float(np.mean(velocity[g.active_links]*DEPTH)),
               "max_terrain_change_this_window_m":float(np.max(np.abs(after[core]-before[core]))),
               "soil_volume_m3":vol,
               "soil_residual_m3":vol-state["initial_volume"]
            })
            assert np.isfinite(g.at_node["soil__depth"]).all()
            assert np.all(g.at_node["soil__depth"]>=-1e-12)
            assert abs(vol-state["initial_volume"])<=1e-4*state["initial_volume"]
        state["completed_days"]=day+1

def paths(folder):
    return {
        "baseline":folder/"h9_baseline.npz",
        "baseline_windows":folder/"h9_windows.json",
        "checkpoint":folder/"h14_ecoworld.pkl",
        "metadata":folder/"h14_metadata.json"
    }

def baseline(folder):
    ref=h9_reference(True,ALPHA)
    p=paths(folder)
    np.savez_compressed(p["baseline"],
       soil=ref["soil_final_core"], topography=ref["topographic_final_core"])
    p["baseline_windows"].write_text(json.dumps(ref["windows"],sort_keys=True))
    print("WORLD_EVAL_JSON "+json.dumps({
        "stage":"H14 baseline H9 original, unchanged",
        "landlab_version":landlab.__version__,
        "window_count":len(ref["windows"]),
        "final_cover":ref["windows"][-1]["mean_cover"]
    },sort_keys=True))

def prepare(folder):
    state=build()
    evolve(state,HALF_DAY)
    payload=pickle.dumps(state,protocol=pickle.HIGHEST_PROTOCOL)
    p=paths(folder)
    p["checkpoint"].write_bytes(payload)
    meta={
        "sha256":hashlib.sha256(payload).hexdigest(),
        "python":platform.python_version(),
        "landlab":landlab.__version__,
        "complete_days":state["completed_days"],
        "bytes":len(payload),
        "warning":"Only load this own generated trusted pickle"
    }
    p["metadata"].write_text(json.dumps(meta,sort_keys=True))
    print("WORLD_EVAL_JSON "+json.dumps({
        "stage":"H14 eco checkpoint created",
        "metadata":meta,
        "months_completed":len(state["windows"]),
        "current_hydrological_years":float(state["soil"].current_time),
    },sort_keys=True))

def resume(folder):
    p=paths(folder)
    meta=json.loads(p["metadata"].read_text())
    raw=p["checkpoint"].read_bytes()
    assert hashlib.sha256(raw).hexdigest()==meta["sha256"]
    assert meta["python"]==platform.python_version()
    assert meta["landlab"]==landlab.__version__
    state=pickle.loads(raw) # self-generated only
    g=state["grid"]
    assert state["soil"].grid is g
    assert state["veg"].grid is g
    assert state["creep"].grid is g
    assert state["completed_days"]==HALF_DAY
    evolve(state,TOTAL_DAYS)
    core=g.core_nodes
    with np.load(p["baseline"]) as ref:
        exact={
            "soil":bool(np.array_equal(ref["soil"],g.at_node["soil__depth"][core])),
            "topography":bool(np.array_equal(ref["topography"],g.at_node["topographic__elevation"][core]))
        }
    win_ref=json.loads(p["baseline_windows"].read_text())
    # As written by Python json, the reference window values are the
    # same bit-represented floats; compare all metrics, not just final mean.
    windows_equal=win_ref==state["windows"]
    solid_residual=float(state["windows"][-1]["soil_residual_m3"])
    report={
        "stage":"H14 restored ecology and geomorphology across processes",
        "landlab_version":landlab.__version__,
        "completed_days":state["completed_days"],
        "checkpoint_bytes":meta["bytes"],
        "checkpoint_checksum_ok":True,
        "component_grid_identities_ok":True,
        "exact_match_arrays":exact,
        "exact_match_all_window_metrics":windows_equal,
        "final_cover_mean":state["windows"][-1]["mean_cover"],
        "final_biomass_mean":state["windows"][-1]["mean_biomass"],
        "final_solid_residual_m3":solid_residual,
        "final_clock_years":float(state["soil"].current_time),
        "limitations":"Three components only, with synthetic fixed PET; no Radiation, OverlandFlow or river sediment. Same Python/Landlab version only."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))
    assert all(exact.values()),"H14 saved-state arrays differ from original uninterrupted H9"
    assert windows_equal,"H14 monthly audit differs from H9 original"
    assert abs(solid_residual)<1e-4*state["initial_volume"]
    assert abs(state["soil"].current_time-90./365.25)<1e-8

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: script [baseline|prepare|resume] folder")
    target=pathlib.Path(sys.argv[2]);target.mkdir(parents=True,exist_ok=True)
    {"baseline":baseline,"prepare":prepare,"resume":resume}[sys.argv[1]](target)
