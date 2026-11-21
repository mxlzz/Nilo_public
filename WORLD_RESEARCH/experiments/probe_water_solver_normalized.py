"""H11c: two native Landlab overland-flow methods with identical Green-Ampt test.

Preregistration: WORLD_RESEARCH/ETAPA_0_8_DRYp_ALTERNATIVAS_Y_H11C_PLAN.md
NO own shallow-water, infiltration or sediment physics.

Same: terrain, fixed grid, initial surface film, initial infiltration column,
Green-Ampt parameters, time/rain intensity, boundary, Manning roughness.
Different: de Almeida versus locally implicit kinematic-wave equation.
"""
import json
import time
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import (
    OverlandFlow, KinwaveImplicitOverlandFlow, SoilInfiltrationGreenAmpt
)

SHAPE = (12, 12)
DX = 1.0
RAIN_MM_HR = 72.0
STEP = 0.5
STEPS = 120
SURFACE_FILM_M = 1e-8
INITIAL_INF_M = .01
ACTIVE_K = 1e-6


def trial(solver, rain, k, bump=False):
    g = RasterModelGrid(SHAPE, xy_spacing=DX)
    x, y = g.node_x, g.node_y
    z = 1. + .01 * y + .003 * x + .03 * np.exp(
        -((x - 5.5)**2 + (y - 5.5)**2) / 4.
    )
    if bump:
        z[int(g.node_at_cell[len(g.node_at_cell)//2])] += .2
    g.at_node["topographic__elevation"] = z.copy()
    g.at_node["surface_water__depth"] = np.zeros(g.number_of_nodes)
    g.at_node["soil_water_infiltration__depth"] = np.full(
        g.number_of_nodes, INITIAL_INF_M
    )
    g.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True, left_is_closed=True,
        right_is_closed=True, top_is_closed=True,
    )
    core = g.core_nodes
    area = g.cell_area_at_node[core]
    if solver == "deAlmeida":
        water = OverlandFlow(
            g, h_init=SURFACE_FILM_M,
            steep_slopes=False, rainfall_intensity=rain/3.6e6,
            mannings_n=.03
        )
    elif solver == "Kinwave":
        water = KinwaveImplicitOverlandFlow(
            g, runoff_rate=rain, roughness=.03,
            changing_topo=True, depth_exp=5.0/3.0
        )
        g.at_node["surface_water__depth"][:] = SURFACE_FILM_M
    else:
        raise ValueError(solver)
    inf = SoilInfiltrationGreenAmpt(
        g, hydraulic_conductivity=k,
        soil_type="sandy loam", surface_water_minimum_depth=SURFACE_FILM_M
    )
    start_surface = float(np.sum(
        g.at_node["surface_water__depth"][core] * area))
    start_soil = float(np.sum(
        g.at_node["soil_water_infiltration__depth"][core] * area))
    t0 = time.perf_counter()
    for _ in range(STEPS):
        water.run_one_step(STEP)
        inf.run_one_step(STEP)
    elapsed = time.perf_counter() - t0
    h = g.at_node["surface_water__depth"][core].copy()
    infiltration = g.at_node["soil_water_infiltration__depth"][core].copy()
    v_surface = float(np.sum(h*area))
    v_soil = float(np.sum(infiltration*area))
    introduced = rain/3.6e6*STEPS*STEP*float(np.sum(area))
    residual = (v_surface+v_soil) - (start_surface+start_soil+introduced)
    return {
        "solver":solver, "rain_mm_per_hour":rain, "K_m_per_s":k,
        "topology_bump_m": .2 if bump else 0.,
        "initial_surface_volume_m3":start_surface,
        "initial_infiltration_record_m3":start_soil,
        "rain_volume_m3":introduced,
        "final_surface_volume_m3":v_surface,
        "final_infiltration_record_m3":v_soil,
        "new_infiltration_m3":v_soil-start_soil,
        "balance_residual_m3":residual,
        "relative_error_vs_rain":abs(residual)/introduced if introduced>0 else None,
        "min_surface_m":float(np.min(h)),
        "min_infiltration_m":float(np.min(infiltration)),
        "runtime_seconds":round(elapsed,6),
        "depth_core":h,
        "infiltration_core":infiltration,
    }


def main():
    results={}
    for solver in ("deAlmeida","Kinwave"):
        active=trial(solver,RAIN_MM_HR,ACTIVE_K)
        noinf=trial(solver,RAIN_MM_HR,0.)
        dry=trial(solver,0.,ACTIVE_K)
        bump=trial(solver,RAIN_MM_HR,ACTIVE_K,True)
        replay=trial(solver,RAIN_MM_HR,ACTIVE_K)
        for label,scene in (("active",active),("noinf",noinf),("dry",dry),("bump",bump)):
            print("H11C_DIAGNOSTIC "+json.dumps({"solver":solver,"scene":label,
                 "residual":scene["balance_residual_m3"],"rain_m3":scene["rain_volume_m3"],
                 "relative_error":scene["relative_error_vs_rain"]}))
            assert scene["min_surface_m"]>=-1e-9, (solver,"negative surface")
            assert scene["min_infiltration_m"]>=0, (solver,"negative infiltrated column")
            if scene["rain_volume_m3"]>0:
                assert scene["relative_error_vs_rain"]<.001, (solver,label,"relative water conservation",scene["relative_error_vs_rain"])
            else:
                assert abs(scene["balance_residual_m3"])<1e-9, (solver,label,"absolute zero-rain water conservation",scene["balance_residual_m3"])
        assert active["new_infiltration_m3"]>1e-6, (solver,"no infiltration")
        assert abs(noinf["new_infiltration_m3"])<1e-9, (solver,"K=0 infiltrated")
        assert abs(dry["new_infiltration_m3"])<1e-9, (solver,"dry leaked")
        assert active["final_surface_volume_m3"]<noinf["final_surface_volume_m3"]
        assert np.array_equal(active["depth_core"],replay["depth_core"]), (solver,"nondeterministic depth")
        spatial=float(np.max(np.abs(active["depth_core"]-bump["depth_core"])))
        assert spatial>1e-7, (solver,"did not react to terrain change")
        def reported(d):
            return {k:v for k,v in d.items() if k not in ("depth_core","infiltration_core")}
        results[solver]={
            "active":reported(active),
            "K0_control":reported(noinf),
            "no_rain_control":reported(dry),
            "bump_control":reported(bump),
            "terrain_sensitivity_max_depth_m":spatial,
        }
    A=results["deAlmeida"]["active"]
    B=results["Kinwave"]["active"]
    results["cross_solver"]={
        "surface_storage_difference_m3":A["final_surface_volume_m3"]-B["final_surface_volume_m3"],
        "infiltrated_storage_difference_m3":A["new_infiltration_m3"]-B["new_infiltration_m3"],
        "runtime_ratio_kinwave_over_deAlmeida":B["runtime_seconds"]/max(A["runtime_seconds"],1e-12)
    }
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"H11c normalized paired Landlab flow+GreenAmpt budget",
        "landlab_version":landlab.__version__,
        "units":{"rain":"mm/h at Kinwave; m/s at deAlmeida",
                 "depth":"m", "dt":"s", "volume":"m3"},
        "domain":SHAPE,"dx_m":DX,"dt_s":STEP,"steps":STEPS,
        "initial_surface_film_m":SURFACE_FILM_M,
        "infiltration_column_initial_m":INITIAL_INF_M,
        "both_use_same_GreenAmpt":True,
        "results":results,
        "limits":"Both hydraulic equations are intentionally different. Single 1-minute synthetic storm; no root moisture, evapotranspiration or open-boundary outlet. Runtime comparison descriptive only."
    },sort_keys=True))


if __name__=="__main__":
    main()
