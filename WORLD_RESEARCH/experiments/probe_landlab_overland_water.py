"""H11a: measured free-surface-water budget with native Landlab OverlandFlow.

Protocol: ETAPA_0_7_PROTOCOLO_H11_AGUA.md (recorded BEFORE script).
No custom fluid law; use shallow-water solver from Landlab.

Model units: water depth m at nodes, discharge m²/s on links,
rainfall intensity m/s, dt seconds. All boundaries are closed, so
volume in the core nodes should equal initial thin film + added rain.
"""
import json
import time
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import OverlandFlow

SHAPE=(12,12)
RAIN=2e-5  # m/s -> 72mm/h, synthetic pulse
STEP_SECONDS=0.5
N_STEPS=120
DX=1.0
INIT_H=1e-5

def run(rain,bump=False):
    t0=time.perf_counter()
    g=RasterModelGrid(SHAPE,xy_spacing=DX)
    x,y=g.node_x,g.node_y
    z=1.0+.01*y+.003*x+.03*np.exp(-((x-5.5)**2+(y-5.5)**2)/4.)
    if bump:
        target=int(g.node_at_cell[len(g.node_at_cell)//2])
        z[target]+=.2
    g.at_node["topographic__elevation"]=z.copy()
    g.at_node["surface_water__depth"]=np.zeros(g.number_of_nodes,dtype=float)
    g.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,left_is_closed=True,
        right_is_closed=True,top_is_closed=True)
    flow=OverlandFlow(g,h_init=INIT_H,steep_slopes=False,
                      rainfall_intensity=rain,mannings_n=.03)
    core=g.core_nodes
    area=g.cell_area_at_node[core]
    initial=float(np.sum(g.at_node["surface_water__depth"][core]*area))
    simulated=0.0
    for _ in range(N_STEPS):
        simulated+=flow.run_one_step(dt=STEP_SECONDS)
    depth=g.at_node["surface_water__depth"]
    vol=float(np.sum(depth[core]*area))
    expected_rain=rain*simulated*float(np.sum(area))
    residual=(vol-initial)-expected_rain
    denominator=max(abs(expected_rain),initial,1e-12)
    report={
        "source_rain_m_per_s":rain,
        "topo_intervention":bump,
        "simulated_time_s":simulated,
        "volume_initial_m3":initial,
        "volume_final_m3":vol,
        "rain_added_expected_m3":expected_rain,
        "water_mass_residual_m3":residual,
        "relative_residual":abs(residual)/denominator,
        "min_water_depth_m":float(np.min(depth[core])),
        "max_water_depth_m":float(np.max(depth[core])),
        "max_absolute_link_discharge_m2_per_s":float(np.max(np.abs(g.at_link["surface_water__discharge"]))),
        "elapsed_wall_seconds":round(time.perf_counter()-t0,3),
        "core_depth":depth[core].copy()
    }
    return report

def main():
    a=run(RAIN,False)
    b=run(0.,False)
    c=run(RAIN,True)
    a_repeat=run(RAIN,False)
    spatial=float(np.max(np.abs(a["core_depth"]-c["core_depth"])))
    def small(r):return{k:v for k,v in r.items() if k!="core_depth"}
    print("WORLD_EVAL_JSON "+json.dumps({
        "test":"H11a native OverlandFlow volumetric water budget",
        "landlab_version":landlab.__version__,
        "grid":SHAPE,"grid_spacing_m":DX,"initial_film_m":INIT_H,
        "steps":N_STEPS,"dt_s":STEP_SECONDS,
        "rainfall_synthetic_m_per_s":RAIN,
        "with_rain":small(a),"no_rain":small(b),
        "rain_with_topography_bump":small(c),
        "maximum_different_depth_after_topology_change_m":spatial,
        "limitation":"No infiltration, evaporation or outlet; no SoilMoisture coupling. This is a closed-grid water-storage smoke, not a whole-world hydrology."
    },sort_keys=True))
    for item in (a,b,c):
        assert abs(item["simulated_time_s"]-60.)<1e-9,"H11a wrong simulated time"
        assert item["min_water_depth_m"]>=-1e-8,"H11a negative water depth"
        assert item["relative_residual"]<=.001,"H11a water balance exceeds 0.1%"
    assert a["max_absolute_link_discharge_m2_per_s"]>0,"H11a no hydraulic movement"
    assert spatial>1e-7,"H11a terrain did not alter water distribution"
    assert np.array_equal(a["core_depth"],a_repeat["core_depth"]),"H11a non-reproducible"

if __name__=="__main__":
    main()
