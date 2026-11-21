"""H9 — Continuity of native Landlab components over 90 days.

PRE-REGISTERED protocol: ETAPA_0_5_CONTRATO_TIEMPO_Y_CONTINUIDAD.md
H9 is a one-way coupled time experiment, NOT a closed climate-landform loop.
Uses only public Landlab components and a published Kd(V) relation.
"""
import json
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import SoilMoisture, Vegetation, DepthDependentDiffuser

ALPHA=0.3
KB=2.5e-4
DEPTH=1.0
H0=.6
DAYS_PER_WINDOW=30
WINDOWS=3

def scenario(wet,alpha):
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
    g.at_cell["vegetation__plant_functional_type"]=np.zeros(g.number_of_cells,dtype=int)
    g.at_cell["vegetation__cover_fraction"]=np.full(g.number_of_cells,.45)
    g.at_cell["vegetation__live_leaf_area_index"]=np.full(g.number_of_cells,.85)
    g.at_cell["surface__potential_evapotranspiration_rate"]=np.full(g.number_of_cells,8.)
    g.at_cell["surface__potential_evapotranspiration_30day_mean"]=np.full(g.number_of_cells,8.)
    g.at_cell["soil_moisture__initial_saturation_fraction"]=np.full(g.number_of_cells,.25)
    g.at_cell["rainfall__daily_depth"]=np.zeros(g.number_of_cells)
    soil=SoilMoisture(g)
    veg=Vegetation(g,Bdead_init=0.0)
    soil.Tr=1.0;soil.Tb=23.0
    veg.Tr=1.0;veg.Tb=23.0

    # Native fields are the sole source of truth. Link velocity is a
    # geometrical projection of published vegetation-dependent Kd.
    velocity=np.full(g.number_of_links, KB*np.exp(-alpha*.45)/DEPTH)
    creep=DepthDependentDiffuser(g,soil_transport_velocity=velocity,
                                soil_transport_decay_depth=DEPTH)
    core=g.core_nodes
    area=g.cell_area_at_node[core]
    vol_init=float(np.sum(g.at_node["soil__depth"][core]*area))
    windows=[]
    for w in range(WINDOWS):
        for d in range(DAYS_PER_WINDOW):
            absolute_day=w*DAYS_PER_WINDOW+d
            rain=12.0 if wet and absolute_day%5==0 else 0.0
            g.at_cell["rainfall__daily_depth"][:]=rain
            soil.update()
            veg.update()
        cover=np.asarray(g.at_cell["vegetation__cover_fraction"]).copy()
        biomass=np.asarray(g.at_cell["vegetation__live_biomass"]).copy()
        saturation=np.asarray(g.at_cell["soil_moisture__saturation_fraction"]).copy()
        Vnodes=np.full(g.number_of_nodes,.45)
        Vnodes[g.node_at_cell]=cover
        Vlinks=.5*(Vnodes[g.node_at_link_tail]+Vnodes[g.node_at_link_head])
        velocity[:]=KB*np.exp(-alpha*Vlinks)/DEPTH
        before=g.at_node["topographic__elevation"].copy()
        creep.run_one_step(dt=DAYS_PER_WINDOW/90.0)
        after=g.at_node["topographic__elevation"].copy()
        vol=float(np.sum(g.at_node["soil__depth"][core]*area))
        windows.append({
           "window":w+1,
           "hydrological_years":float(soil.current_time),
           "mean_biomass":float(np.mean(biomass)),
           "mean_cover":float(np.mean(cover)),
           "mean_saturation":float(np.mean(saturation)),
           "mean_diffusivity":float(np.mean(velocity[g.active_links]*DEPTH)),
           "max_terrain_change_this_window_m":float(np.max(np.abs(after[core]-before[core]))),
           "soil_volume_m3":vol,
           "soil_residual_m3":vol-vol_init
        })
        assert np.all(np.isfinite(g.at_node["soil__depth"])), "H9 nonfinite soil"
        assert np.all(g.at_node["soil__depth"]>=-1e-12), "H9 negative sediment"
        assert abs(vol-vol_init) <= 1e-4*vol_init, "H9 solid mass not conserved"
    assert abs(soil.current_time-90.0/365.25)<1e-8, "H9 current_time inconsistent with days"
    return {
        "rain":wet,"alpha":alpha,
        "windows":windows,
        "soil_final_core":g.at_node["soil__depth"][core].copy(),
        "topographic_final_core":g.at_node["topographic__elevation"][core].copy(),
        "bedrock_max_change_m":float(np.max(np.abs(g.at_node["bedrock__elevation"]-(topo-H0))))
    }


def main():
    wet=scenario(True,ALPHA)
    dry=scenario(False,ALPHA)
    wet_no_feedback=scenario(True,0.)
    dry_no_feedback=scenario(False,0.)
    delta=float(np.max(np.abs(wet["topographic_final_core"]-dry["topographic_final_core"])))
    ablated=float(np.max(np.abs(wet_no_feedback["topographic_final_core"]-dry_no_feedback["topographic_final_core"])))
    wet_last=wet["windows"][-1];dry_last=dry["windows"][-1]
    print("WORLD_EVAL_JSON "+json.dumps({
        "test":"H9 multievent native Landlab 90 days (unidirectional)",
        "landlab_version":landlab.__version__,
        "weather":"Tr=1h, Tb=23h, wet 12mm every 5th day, dry 0mm",
        "geomorphic_rate":"published Kb per season; dt 30/90 season per window",
        "wet_windows":wet["windows"],"dry_windows":dry["windows"],
        "topo_difference_wet_dry_m":delta,
        "topo_difference_control_alpha0_m":ablated,
        "scope":"No topography->water feedback, no river sediment SPACE, no physically calibrated climate"
    },sort_keys=True))
    assert len(wet["windows"])==3
    assert wet_last["mean_cover"]>dry_last["mean_cover"],"H9 wet weather did not retain cover difference at day90"
    assert wet_last["mean_biomass"]>dry_last["mean_biomass"],"H9 wet biomass not greater"
    assert delta>1e-12,"H9 no cumulative vegetation-dependent morphologic effect"
    assert ablated<=1e-12,"H9 disabling vegetative coupling not null"
    assert wet["bedrock_max_change_m"]<1e-12
    repeat=scenario(True,ALPHA)
    assert np.array_equal(repeat["topographic_final_core"],wet["topographic_final_core"]),"H9 not reproducible"


if __name__=="__main__":
    main()
