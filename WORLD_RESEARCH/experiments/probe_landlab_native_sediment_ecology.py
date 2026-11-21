"""Etapa 0, ensayos de componentes Landlab ya existentes.

H4: SPACE (erosión + sedimentos) vs erosividad nula.
H5: SoilMoisture + Vegetation en la misma malla/estado de Landlab.
No implementa un motor propio ni acopla proyectos de licencias distintas.
"""
import json
import time
import numpy as np
from landlab import RasterModelGrid
from landlab.components import FlowAccumulator, Space, SoilMoisture, Vegetation


def soil_and_sediment(k_sed=0.03, k_br=0.002, steps=10):
    grid=RasterModelGrid((14,14),xy_spacing=1.0)
    grid.status_at_node[grid.nodes_at_left_edge]=grid.BC_NODE_IS_CLOSED
    grid.status_at_node[grid.nodes_at_right_edge]=grid.BC_NODE_IS_CLOSED
    grid.status_at_node[grid.nodes_at_top_edge]=grid.BC_NODE_IS_CLOSED
    grid.status_at_node[grid.nodes_at_bottom_edge]=grid.BC_NODE_IS_FIXED_VALUE
    base=0.11*grid.node_y+0.005*grid.node_x + 0.017*np.sin(grid.node_x*.6+grid.node_y*.3)
    z=grid.add_field("topographic__elevation",base.copy(),at="node")
    depth=grid.add_field("soil__depth",np.full(grid.number_of_nodes,.5),at="node")
    flow=FlowAccumulator(grid,flow_director="D8",runoff_rate=1.0)
    flow.run_one_step()
    model=Space(grid,K_sed=k_sed,K_br=k_br,F_f=0.1,phi=0.2,H_star=0.1,
                v_s=0.001,m_sp=0.5,n_sp=1.0,solver="adaptive")
    for _ in range(steps):
        flow.run_one_step()
        model.run_one_step(dt=0.1)
    sed_out=np.asarray(grid.at_node["sediment__outflux"])
    bedrock=np.asarray(grid.at_node["bedrock__elevation"])
    assert np.all(np.isfinite(z)), "H4: topography nonfinite"
    assert np.all(np.isfinite(depth)), "H4: soil depth nonfinite"
    assert np.all(depth>=-1e-8), "H4: soil became negative"
    assert np.all(np.isfinite(sed_out)), "H4: sediment flux nonfinite"
    assert np.all(np.isfinite(bedrock)), "H4: bedrock nonfinite"
    return {
        "mean_topographic_change":float(np.mean(np.abs(z[grid.core_nodes]-base[grid.core_nodes]))),
        "total_sediment_outflux_on_core_nodes":float(np.sum(sed_out[grid.core_nodes])),
        "min_soil_depth":float(np.min(depth)),
        "soil_depth_change_core_sum":float(np.sum(depth[grid.core_nodes]-.5)),
        "bedrock_max_difference_from_initial":float(np.max(np.abs((z-depth)-(base-.5)))),
        "topography":z.copy()
    }


def eco_pair(rain):
    grid=RasterModelGrid((6,6),xy_spacing=1.0)
    n=grid.number_of_cells
    # Inputs documented by SoilMoisture and Vegetation on the shared cell grid.
    grid.at_cell["vegetation__plant_functional_type"]=np.zeros(n,dtype=int)
    grid.at_cell["vegetation__cover_fraction"]=np.full(n,0.45)
    grid.at_cell["vegetation__live_leaf_area_index"]=np.full(n,0.85)
    # Growth is conditional on PET30 > threshold (6.8 by default).
    # Earlier exploratory PET=0.25 tested senescence, where biomass did
    # not respond to water stress; switch to a growing-season condition.
    grid.at_cell["surface__potential_evapotranspiration_rate"]=np.full(n,8.0)
    grid.at_cell["surface__potential_evapotranspiration_30day_mean"]=np.full(n,8.0)
    grid.at_cell["soil_moisture__initial_saturation_fraction"]=np.full(n,0.25)
    grid.at_cell["rainfall__daily_depth"]=np.full(n,float(rain))
    soil=SoilMoisture(grid)
    soil.current_time=0.5
    soil.update()
    sat=grid.at_cell["soil_moisture__saturation_fraction"].copy()
    stress=grid.at_cell["vegetation__water_stress"].copy()
    veg=Vegetation(grid)
    veg.update()
    biomass=grid.at_cell["vegetation__live_biomass"].copy()
    assert all(np.all(np.isfinite(a)) for a in (sat,stress,biomass))
    return {
        "mean_saturation":float(np.mean(sat)),
        "mean_water_stress":float(np.mean(stress)),
        "mean_live_biomass_after_update":float(np.mean(biomass)),
        "n_cells":n,
    }


def main():
    t0=time.perf_counter()
    active=soil_and_sediment()
    control=soil_and_sediment(k_sed=0.0,k_br=0.0)
    assert active["total_sediment_outflux_on_core_nodes"]>0,"H4: active sediment transport absent"
    assert active["mean_topographic_change"]>1e-8,"H4: expected coupled erosion absent"
    assert control["mean_topographic_change"]<1e-10,"H4: negative control should not erode"
    assert control["total_sediment_outflux_on_core_nodes"]<1e-10,"H4: no sediment without erosion"
    r=eco_pair(rain=25.0)
    d=eco_pair(rain=0.0)
    assert r["mean_saturation"]>d["mean_saturation"],"H5: rain did not change moisture"
    assert r["mean_live_biomass_after_update"]>d["mean_live_biomass_after_update"],"H5: growing-season biomass did not respond to moisture"
    print("WORLD_EVAL_JSON "+json.dumps({
        "candidate":"Landlab native sediment/ecology",
        "sediment_active":{k:v for k,v in active.items() if k!="topography"},
        "sediment_control":{k:v for k,v in control.items() if k!="topography"},
        "soil_vegetation_with_rain":r,
        "soil_vegetation_without_rain":d,
        "same_landlab_grid_for_eco_pair":True,
        "limitation":"No complete river-water-soil-vegetation feedback loop; check units and node-cell mapping before integration. SPACE is open system; full global sediment balance not asserted.",
        "elapsed_seconds":round(time.perf_counter()-t0,3)
    },sort_keys=True))


if __name__=="__main__":
    main()
