"""H10b: controlled 90-day geometry-to-radiation-to-ecology-to-soil feedback.

All physical solvers are existing Landlab components: Radiation,
PotentialEvapotranspiration, SoilMoisture, Vegetation, DepthDependentDiffuser.

The externally imposed 12-m bedrock uplift at day 46 is an intentional
sensitivity intervention, not an endogenous law. The negative control routes
PET from a fixed original reference topography (same weather/time), without
disabling vegetation or soil movement.

Protocol pre-registered in ETAPA_0_6_PROTOCOLO_RETORNO_RADIACION.md.
"""
import json
import time
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import (
    Radiation, PotentialEvapotranspiration, SoilMoisture,
    Vegetation, DepthDependentDiffuser
)

DAYS=90
SHAPE=(8,8)
DX=10.0
H0=.6
KB=2.5e-4
ALPHA=.3
DEPTH=1.0
UPLIFT_M=12.0
UPLIFT_DAY_INDEX=45
START_YEAR=.5

def topo_initial(g):
    x,y=g.node_x,g.node_y
    return (100.0 + .025*x+.03*y
            + 2.0*np.exp(-((x-35.)**2+(y-35.)**2)/300.0))

def grid_initial(with_soil):
    g=RasterModelGrid(SHAPE,xy_spacing=DX)
    baseline=topo_initial(g)
    g.at_node["topographic__elevation"]=baseline.copy()
    if with_soil:
        g.at_node["soil__depth"]=np.full(g.number_of_nodes,H0)
        g.at_node["bedrock__elevation"]=baseline-H0
        g.at_node["soil_production__rate"]=np.zeros(g.number_of_nodes)
    g.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,left_is_closed=True,
        right_is_closed=True,top_is_closed=True)
    return g

def scenario(uplift,geom_feedback):
    t0=time.perf_counter()
    g=grid_initial(with_soil=True)
    g_ref=grid_initial(with_soil=False) if not geom_feedback else None

    Radiation(g,current_time=START_YEAR,latitude=34.0).update()
    pet=PotentialEvapotranspiration(
        g,method="Cosine",MeanTmaxF=10.0,delta_d=0.0,current_time=START_YEAR)
    pet.update()
    n=g.number_of_cells
    g.at_cell["vegetation__plant_functional_type"]=np.zeros(n,dtype=int)
    g.at_cell["vegetation__cover_fraction"]=np.full(n,.45)
    g.at_cell["vegetation__live_leaf_area_index"]=np.full(n,.85)
    g.at_cell["surface__potential_evapotranspiration_30day_mean"]=np.full(n,10.)
    g.at_cell["soil_moisture__initial_saturation_fraction"]=np.full(n,.25)
    g.at_cell["rainfall__daily_depth"]=np.zeros(n)
    soil=SoilMoisture(g)
    veg=Vegetation(g,Bdead_init=0.)
    soil.Tr=1.;soil.Tb=23.;veg.Tr=1.;veg.Tb=23.

    velocity=np.full(g.number_of_links,KB*np.exp(-ALPHA*.45)/DEPTH)
    creep=DepthDependentDiffuser(g,soil_transport_velocity=velocity,
                                soil_transport_decay_depth=DEPTH)

    core=g.core_nodes
    initial_volume=float(np.sum(g.at_node["soil__depth"][core]*g.cell_area_at_node[core]))
    target=int(g.node_at_cell[len(g.node_at_cell)//2])
    pet_history=[]
    moisture_history=[]
    biomass_history=[]
    canopy_history=[]
    topo_history=[]
    ratio_history=[]
    checkpoints=[]
    for d in range(DAYS):
        if uplift and d==UPLIFT_DAY_INDEX:
            # Geological intervention affects bedrock elevation AND total
            # topographic elevation; it does not create/remove mobile soil.
            g.at_node["bedrock__elevation"][target]+=UPLIFT_M
            g.at_node["topographic__elevation"][target]+=UPLIFT_M

        current=START_YEAR+d/365.25
        Radiation(g,current_time=current,latitude=34.0).update()
        if not geom_feedback:
            Radiation(g_ref,current_time=current,latitude=34.0).update()
            # Negative control: only topography->PET is disabled.
            g.at_cell["radiation__ratio_to_flat_surface"][:]=g_ref.at_cell[
                "radiation__ratio_to_flat_surface"]
        pet.current_time=current
        pet.update()
        today_pet=g.at_cell["surface__potential_evapotranspiration_rate"].copy()
        pet_history.append(today_pet)
        ratio_history.append(g.at_cell["radiation__ratio_to_flat_surface"].copy())
        g.at_cell["surface__potential_evapotranspiration_30day_mean"][:]=np.mean(
            np.asarray(pet_history[-30:]),axis=0)
        g.at_cell["rainfall__daily_depth"][:]=12.0 if d%5==0 else 0.0

        soil.update()
        veg.update()
        moisture_history.append(g.at_cell["soil_moisture__saturation_fraction"].copy())
        biomass_history.append(g.at_cell["vegetation__live_biomass"].copy())
        canopy_history.append(g.at_cell["vegetation__cover_fraction"].copy())

        if (d+1)%30==0:
            cover=g.at_cell["vegetation__cover_fraction"]
            Vnode=np.full(g.number_of_nodes,.45)
            Vnode[g.node_at_cell]=cover
            Vlink=.5*(Vnode[g.node_at_link_tail]+Vnode[g.node_at_link_head])
            velocity[:]=KB*np.exp(-ALPHA*Vlink)/DEPTH
            creep.run_one_step(dt=30.0/90.0)
            vol=float(np.sum(g.at_node["soil__depth"][core]*g.cell_area_at_node[core]))
            assert abs(vol-initial_volume)<1e-4*initial_volume,"H10b mobile soil budget failed"
            assert np.isfinite(g.at_node["soil__depth"]).all()
            assert np.all(g.at_node["soil__depth"]>=-1e-10)
            checkpoints.append({
                "day":d+1,"mean_cover":float(np.mean(cover)),
                "mean_moisture":float(np.mean(moisture_history[-1])),
                "soil_volume_m3":vol,
                "soil_residual_m3":vol-initial_volume
            })
        topo_history.append(g.at_node["topographic__elevation"].copy())

    assert abs(soil.current_time-DAYS/365.25)<1e-8,"H10b clock mismatch"
    return {
        "uplift":uplift,"geometry_link":geom_feedback,
        "pet":np.asarray(pet_history),
        "ratio":np.asarray(ratio_history),
        "moisture":np.asarray(moisture_history),
        "biomass":np.asarray(biomass_history),
        "canopy":np.asarray(canopy_history),
        "topo":np.asarray(topo_history),
        "checkpoints":checkpoints,
        "elapsed_seconds":time.perf_counter()-t0,
        "soil_final_volume_m3":float(np.sum(g.at_node["soil__depth"][core]*g.cell_area_at_node[core])),
        "bedrock_bump_m":UPLIFT_M if uplift else 0.0
    }

def max_delta(a,b,key,start=0):
    return float(np.max(np.abs(a[key][start:]-b[key][start:])))

def main():
    active_base=scenario(False,True)
    active_bump=scenario(True,True)
    frozen_base=scenario(False,False)
    frozen_bump=scenario(True,False)
    replay=scenario(True,True)

    results={
        "test":"H10b 90-day topology-energy-ecology-soil closed causal interface",
        "landlab_version":landlab.__version__,
        "topology_intervention":"+12m external bedrock and topography elevation at day 46",
        "topography_caches":"Recreate Radiation daily; no custom radiation law",
        "climatic_conditions":"Same rainfall 12mm every 5 days; time 1h storm 23h interstorm; PET base 10mm/day times topographic solar ratio",
        "active_delta_PET_before_day46":float(np.max(np.abs(active_base["pet"][:UPLIFT_DAY_INDEX]-active_bump["pet"][:UPLIFT_DAY_INDEX]))),
        "active_delta_PET_day46":float(np.max(np.abs(active_base["pet"][UPLIFT_DAY_INDEX]-active_bump["pet"][UPLIFT_DAY_INDEX]))),
        "active_delta_PET_after_day46":max_delta(active_base,active_bump,"pet",UPLIFT_DAY_INDEX),
        "active_delta_moisture_after_day46":max_delta(active_base,active_bump,"moisture",UPLIFT_DAY_INDEX),
        "active_delta_biomass_after_day46":max_delta(active_base,active_bump,"biomass",UPLIFT_DAY_INDEX),
        "active_delta_canopy_after_day46":max_delta(active_base,active_bump,"canopy",UPLIFT_DAY_INDEX),
        "ablated_delta_PET_after_day46":max_delta(frozen_base,frozen_bump,"pet",UPLIFT_DAY_INDEX),
        "ablated_delta_moisture_after_day46":max_delta(frozen_base,frozen_bump,"moisture",UPLIFT_DAY_INDEX),
        "ablated_delta_biomass_after_day46":max_delta(frozen_base,frozen_bump,"biomass",UPLIFT_DAY_INDEX),
        "endogenous_geom_energy_difference_base_vs_frozen_no_bump_after_day30":max_delta(active_base,frozen_base,"pet",30),
        "final_checkpoints_active_bump":active_bump["checkpoints"],
        "final_checkpoints_frozen_bump":frozen_bump["checkpoints"],
        "duration_seconds_per_scenario":{k:round(v["elapsed_seconds"],3) for k,v in [
            ("active_base",active_base),("active_bump",active_bump),
            ("frozen_base",frozen_base),("frozen_bump",frozen_bump)]},
        "limitation":"A +12m exogenous bedrock uplift is a sensitivity intervention, not emergent geological movement. This is a modeled solar-PET return, NOT fluvial hydrology, water budget, or geomorphic calibration."
    }
    print("WORLD_EVAL_JSON "+json.dumps(results,sort_keys=True))
    assert results["active_delta_PET_before_day46"]<1e-12,"H10b initial worlds differ"
    assert results["active_delta_PET_day46"]>1e-5,"H10b topo change didn't affect PET"
    assert results["active_delta_moisture_after_day46"]>1e-9,"H10b topo-PET didn't affect moisture"
    assert results["active_delta_biomass_after_day46"]>1e-9,"H10b topo-PET didn't affect vegetation"
    assert results["ablated_delta_PET_after_day46"]<1e-12,"H10b ablated PET responds to bump"
    assert results["ablated_delta_moisture_after_day46"]<1e-12,"H10b ablated moisture responds to bump"
    assert results["ablated_delta_biomass_after_day46"]<1e-12,"H10b ablated biomass responds to bump"
    assert np.array_equal(active_bump["topo"],replay["topo"]),"H10b nondeterministic topography"
    assert np.array_equal(active_bump["pet"],replay["pet"]),"H10b nondeterministic PET"

if __name__=="__main__":
    main()
