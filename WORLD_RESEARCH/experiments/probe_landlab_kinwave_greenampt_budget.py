"""H11b: existing Landlab KinwaveImplicitOverlandFlow + Green-Ampt infiltration.

Implements only a test harness for an existing documented combination:
docs/source/tutorials/overland_flow/soil_infiltration_green_ampt.
Scientific models: kinematic wave runoff and Green-Ampt soil infiltration.

Runoff input: mm/h; dt: seconds; depth variables: meters. H11a previously
tested de Almeida OverlandFlow (m/s rain) separately; not the same model.
Pre-registered criteria in ETAPA_0_7_PROTOCOLO_H11_AGUA.md.
"""
import json
import time
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import KinwaveImplicitOverlandFlow, SoilInfiltrationGreenAmpt

SHAPE=(12,12)
DX=1.
STEP_SECONDS=.5
STEPS=120
RAIN_MM_HR=72.
INFILT_INIT=.01
K_ACTIVE=1e-6

def run(rain_mmhr,k,bump=False):
    t0=time.perf_counter()
    g=RasterModelGrid(SHAPE,xy_spacing=DX)
    x,y=g.node_x,g.node_y
    z=1.0+.01*y+.003*x+.03*np.exp(-((x-5.5)**2+(y-5.5)**2)/4.)
    if bump:
        at=int(g.node_at_cell[len(g.node_at_cell)//2])
        z[at]+=.2
    g.at_node["topographic__elevation"]=z.copy()
    g.at_node["surface_water__depth"]=np.zeros(g.number_of_nodes)
    g.at_node["soil_water_infiltration__depth"]=np.full(g.number_of_nodes,INFILT_INIT)
    g.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,left_is_closed=True,
        right_is_closed=True,top_is_closed=True)
    core=g.core_nodes
    cell_area=g.cell_area_at_node[core]
    init_surface=float(np.sum(g.at_node["surface_water__depth"][core]*cell_area))
    init_infilt=float(np.sum(g.at_node["soil_water_infiltration__depth"][core]*cell_area))
    kw=KinwaveImplicitOverlandFlow(g,runoff_rate=rain_mmhr,
             roughness=.03,changing_topo=True,depth_exp=5./3.)
    infiltration=SoilInfiltrationGreenAmpt(g,
             hydraulic_conductivity=k,
             soil_type="sandy loam",
             surface_water_minimum_depth=1e-8)
    for _ in range(STEPS):
        kw.run_one_step(STEP_SECONDS)
        infiltration.run_one_step(STEP_SECONDS)

    surface=g.at_node["surface_water__depth"][core].copy()
    infilt=g.at_node["soil_water_infiltration__depth"][core].copy()
    total_surface=float(np.sum(surface*cell_area))
    total_infilt=float(np.sum(infilt*cell_area))
    added=rain_mmhr/3.6e6*(STEP_SECONDS*STEPS)*float(np.sum(cell_area))
    residual=(total_surface+total_infilt)-(init_surface+init_infilt+added)
    return {
        "rain_mm_per_hour":rain_mmhr,"K_m_per_s":k,"terrain_bump_m":.2 if bump else 0.,
        "initial_surface_water_m3":init_surface,
        "initial_infiltrated_m3":init_infilt,
        "rainfall_volume_expected_m3":added,
        "final_surface_water_m3":total_surface,
        "final_infiltrated_water_m3":total_infilt,
        "infiltration_increment_m3":total_infilt-init_infilt,
        "joint_water_balance_residual_m3":residual,
        "joint_water_balance_relative_residual":abs(residual)/max(added,init_surface+init_infilt,1e-10),
        "min_surface_water_m":float(np.min(surface)),
        "min_infiltrated_column_m":float(np.min(infilt)),
        "elapsed_wall_seconds":round(time.perf_counter()-t0,3),
        "surface_depth":surface,"infiltration_depth":infilt
    }

def main():
    active=run(RAIN_MM_HR,K_ACTIVE)
    non_infiltrating=run(RAIN_MM_HR,0.)
    dry=run(0.,K_ACTIVE)
    altered=run(RAIN_MM_HR,K_ACTIVE,True)
    replay=run(RAIN_MM_HR,K_ACTIVE)
    max_dist=float(np.max(np.abs(active["surface_depth"]-altered["surface_depth"])))
    def scalars(d):
        return{k:v for k,v in d.items() if k not in ("surface_depth","infiltration_depth")}
    print("WORLD_EVAL_JSON "+json.dumps({
        "test":"H11b native KinwaveImplicitOverlandFlow + GreenAmpt total water budget",
        "landlab_version":landlab.__version__,
        "grid":SHAPE,"grid_spacing_m":DX,
        "dt_s":STEP_SECONDS,"steps":STEPS,
        "active":scalars(active),"no_infiltration":scalars(non_infiltrating),
        "no_rain":scalars(dry),"altered_topography":scalars(altered),
        "difference_in_surface_depth_due_to_terrain_m":max_dist,
        "limitation":"Infiltrated column is cumulative absorbed water, not root zone soil saturation. Separate solver and units from de Almeida OverlandFlow H11a; no evapotranspiration or open-boundary outflow."
    },sort_keys=True))
    for d in (active,non_infiltrating,dry,altered):
        assert d["joint_water_balance_relative_residual"]<.001,"H11b joint water budget failed"
        assert d["min_surface_water_m"]>=-1e-8,"H11b negative surface depth"
        assert d["min_infiltrated_column_m"]>=0.,"H11b negative infiltration column"
    assert active["infiltration_increment_m3"]>1e-6,"H11b no infiltration"
    assert active["final_surface_water_m3"]<non_infiltrating["final_surface_water_m3"],"H11b infiltration did not reduce surface"
    assert abs(dry["infiltration_increment_m3"])<1e-9,"H11b dry run infiltrated without water"
    assert abs(non_infiltrating["infiltration_increment_m3"])<1e-9,"H11b K=0 still infiltrated"
    assert max_dist>1e-7,"H11b terrain change did not affect water distribution"
    assert np.array_equal(active["surface_depth"],replay["surface_depth"]),"H11b not reproducible"

if __name__=="__main__":
    main()
