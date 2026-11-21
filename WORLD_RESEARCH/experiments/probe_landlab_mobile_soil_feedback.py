"""H8b: native Landlab, rain -> vegetation cover -> CONSERVATIVE soil creep.

Not a production world or a dynamic multi-season closed-loop simulation.
This test uses DepthDependentDiffuser's existing soil-flux equation:
q = -K * slope * d* (1 - exp(-H / d*)).
Published vegetation factor K_d = K_b exp(-alpha V):
Sharma & Ehlers 2023 eqs. 2-3, Table A1 alpha=.3, Kb=2.5e-4 m2/season.
Using d* = 1m (Landlab component default), K=Kd/d* (m/season).
"""
import json
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import SoilMoisture, Vegetation, DepthDependentDiffuser

SHAPE=(8,8)
ALPHA=.3
KB=2.5e-4
DECAY_DEPTH_M=1.0
H0=0.6


def scenario(rain_mm, alpha):
    g=RasterModelGrid(SHAPE,xy_spacing=1.0)
    x,y=g.node_x,g.node_y
    baseline=.025*x+.03*y+2.0*np.exp(-((x-3.5)**2+(y-3.5)**2)/3.)
    g.at_node["topographic__elevation"]=baseline.copy()
    g.at_node["soil__depth"]=np.full(g.number_of_nodes,H0)
    g.at_node["bedrock__elevation"]=baseline-H0
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
    g.at_cell["rainfall__daily_depth"]=np.full(n,float(rain_mm))

    sm=SoilMoisture(g)
    sm.current_time=.5
    sm.update()
    saturation=g.at_cell["soil_moisture__saturation_fraction"].copy()
    vegetation=Vegetation(g,Bdead_init=0.)
    vegetation.update()
    cover=g.at_cell["vegetation__cover_fraction"].copy()
    biomass=g.at_cell["vegetation__live_biomass"].copy()

    Vnodes=np.full(g.number_of_nodes,.45)
    Vnodes[g.node_at_cell]=cover
    Vlinks=.5*(Vnodes[g.node_at_link_tail]+Vnodes[g.node_at_link_head])
    Kd=KB*np.exp(-alpha*Vlinks)
    velocity=Kd/DECAY_DEPTH_M  # documented DepthDependentDiffuser K units
    before_depth=g.at_node["soil__depth"].copy()
    before_bed=g.at_node["bedrock__elevation"].copy()
    before_elev=g.at_node["topographic__elevation"].copy()
    core=g.core_nodes
    cell_area=g.cell_area_at_node[core]
    volume_before=float(np.sum(before_depth[core]*cell_area))

    diff=DepthDependentDiffuser(g,soil_transport_velocity=velocity,
                                soil_transport_decay_depth=DECAY_DEPTH_M)
    diff.run_one_step(dt=1.0)
    after_depth=g.at_node["soil__depth"].copy()
    after_elev=g.at_node["topographic__elevation"].copy()
    vol_after=float(np.sum(after_depth[core]*cell_area))
    residual=vol_after-volume_before
    assert np.isfinite(after_depth).all()
    assert np.isfinite(after_elev).all()
    return {
        "rain_mm":rain_mm,
        "mean_saturation":float(np.mean(saturation)),
        "mean_biomass":float(np.mean(biomass)),
        "mean_cover":float(np.mean(cover)),
        "mean_active_link_diffusivity":float(np.mean(Kd[g.active_links])),
        "max_depth_change_m":float(np.max(np.abs(after_depth[core]-before_depth[core]))),
        "total_soil_volume_before_m3":volume_before,
        "total_soil_volume_after_m3":vol_after,
        "volume_residual_m3":residual,
        "max_bedrock_difference_m":float(np.max(np.abs(g.at_node["bedrock__elevation"]-before_bed))),
        "min_soil_depth_m":float(np.min(after_depth)),
        "core_after_elev":after_elev[core]
    }


def main():
    wet=scenario(25.,ALPHA)
    dry=scenario(0.,ALPHA)
    wet_ablated=scenario(25.,0.)
    dry_ablated=scenario(0.,0.)
    delta=float(np.max(np.abs(wet["core_after_elev"]-dry["core_after_elev"])))
    null_delta=float(np.max(np.abs(wet_ablated["core_after_elev"]-dry_ablated["core_after_elev"])))
    def scalar(v):return {k:x for k,x in v.items() if k!="core_after_elev"}
    print("WORLD_EVAL_JSON "+json.dumps({
       "test":"H8b SoilMoisture->Vegetation->DepthDependentDiffuser",
       "landlab_version":landlab.__version__,
       "parameters":{"alpha":ALPHA,"bare_Kd_m2_per_season":KB,
                     "depth_decay_m":DECAY_DEPTH_M,"soil_initial_m":H0},
       "wet":scalar(wet),"dry":scalar(dry),
       "vegetation_enabled_elevation_difference_m":delta,
       "vegetation_ablated_elevation_difference_m":null_delta,
       "scope":"single separated rain event + 1 geomorphic season; no river SPACE or repeated eco-geomorphic time loop"
    },sort_keys=True))
    assert wet["mean_saturation"]>dry["mean_saturation"]
    assert wet["mean_cover"]>dry["mean_cover"]
    assert wet["mean_active_link_diffusivity"]<dry["mean_active_link_diffusivity"]
    assert wet["max_depth_change_m"]>1e-10
    assert delta>1e-13,"H8b landform response absent"
    assert null_delta<=1e-13,"H8b alpha=0 did not remove differential landform"
    for item in (wet,dry,wet_ablated,dry_ablated):
        assert item["min_soil_depth_m"]>=-1e-10
        assert abs(item["volume_residual_m3"])<1e-4*max(item["total_soil_volume_before_m3"],1)
        assert item["max_bedrock_difference_m"]<1e-13
    replay=scenario(25.,ALPHA)
    assert np.array_equal(replay["core_after_elev"],wet["core_after_elev"])


if __name__=="__main__":
    main()
