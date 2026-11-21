"""H8a: coupling feasibility, NOT a calibrated eco-geomorphic world.

- Landlab SoilMoisture -> Vegetation (same CELL grid)
- Landlab LinearDiffuser on NODE grid using field from published equation
  K_d = K_b exp(-alpha * V), Sharma & Ehlers 2023 eq. 3, table A1.
- alpha=.3, Kb=2.5e-4 m^2 per season, values from paper, not invented.
- Deposition/sediment mass budget deliberately NOT assessed with
  LinearDiffuser; SpaceLargeScaleEroder is investigated separately.
- Moisture event and 1-season geomorphic increment are NOT a dynamically
  time-consistent coupled timestep. This is ONLY a causal interface smoke.

Source: https://doi.org/10.5194/esurf-11-1161-2023
Table: https://esurf.copernicus.org/articles/11/1161/2023/esurf-11-1161-2023-t02.png
"""
import json
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import SoilMoisture, Vegetation, LinearDiffuser

ALPHA = 0.3
BARE_KD = 2.5e-4
SHAPE = (8, 8)


def one_shot(rain_mm, alpha):
    g = RasterModelGrid(SHAPE, xy_spacing=1.0)
    x,y=g.node_x,g.node_y
    baseline=.025*x+.03*y+2.0*np.exp(-((x-3.5)**2+(y-3.5)**2)/3.)
    g.at_node["topographic__elevation"]=baseline.copy()
    n=g.number_of_cells
    g.at_cell["vegetation__plant_functional_type"]=np.zeros(n,dtype=int)
    g.at_cell["vegetation__cover_fraction"]=np.full(n,.45)
    g.at_cell["vegetation__live_leaf_area_index"]=np.full(n,.85)
    g.at_cell["surface__potential_evapotranspiration_rate"]=np.full(n,8.0)
    g.at_cell["surface__potential_evapotranspiration_30day_mean"]=np.full(n,8.0)
    g.at_cell["soil_moisture__initial_saturation_fraction"]=np.full(n,.25)
    g.at_cell["rainfall__daily_depth"]=np.full(n,float(rain_mm))
    soil=SoilMoisture(g)
    soil.current_time=.5
    soil.update()
    sat=g.at_cell["soil_moisture__saturation_fraction"].copy()
    stress=g.at_cell["vegetation__water_stress"].copy()

    # Default Bdead_init=450 saturates LAI_total at its ceiling, masking
    # any causal influence of wet/dry growth on COVER (not on biomass).
    # Use an initial litter-free state; equations and published alpha/Kb
    # remain unchanged. The original failing run is preserved in CI.
    veg=Vegetation(g, Bdead_init=0.0)
    veg.update()
    cover=np.asarray(g.at_cell["vegetation__cover_fraction"]).copy()
    biomass=np.asarray(g.at_cell["vegetation__live_biomass"]).copy()
    assert np.isfinite(cover).all()
    assert ((cover>=0)&(cover<=1)).all(),"plant cover outside 0..1"

    # Only cell-centered core nodes receive a computed plant cover.
    # The perimeter is a fixed external boundary, not evidence of ecology.
    at_node=np.full(g.number_of_nodes,.45,dtype=float)
    at_node[g.node_at_cell]=cover
    diffusivity=BARE_KD*np.exp(-alpha*at_node)
    diff=LinearDiffuser(g,linear_diffusivity=diffusivity)
    diff.run_one_step(1.0) # 1 *published geomorphic season*, NOT same as hydrologic event
    after=g.at_node["topographic__elevation"].copy()
    assert np.isfinite(after).all()
    return {
        "sat_mean":float(np.mean(sat)),
        "water_stress_mean":float(np.mean(stress)),
        "biomass_mean":float(np.mean(biomass)),
        "cover_mean":float(np.mean(cover)),
        "kd_core_mean":float(np.mean(diffusivity[g.core_nodes])),
        "max_abs_elevation_change_m":float(np.max(np.abs(after-baseline))),
        "core_elevations":after[g.core_nodes].copy()
    }


def main():
    wet=one_shot(25.,ALPHA)
    dry=one_shot(0.,ALPHA)
    wet_no_veg=one_shot(25.,0.)
    dry_no_veg=one_shot(0.,0.)
    def scalar(d):return {k:v for k,v in d.items() if k!="core_elevations"}
    diff_wet_dry=float(np.max(np.abs(wet["core_elevations"]-dry["core_elevations"])))
    diff_control=float(np.max(np.abs(wet_no_veg["core_elevations"]-dry_no_veg["core_elevations"])))
    print("WORLD_EVAL_JSON "+json.dumps({
        "test":"H8a native Landlab causal interface, no full ecofeedback",
        "landlab_version":landlab.__version__,"grid_shape":SHAPE,
        "alpha_published":ALPHA,"bare_diffusivity_m2_per_season":BARE_KD,
        "rain_mm_wet_event":25.0,"rain_mm_dry_event":0.0,
        "wet":scalar(wet),"dry":scalar(dry),
        "with_published_vegetation_influence_max_difference_m":diff_wet_dry,
        "without_vegetation_influence_max_difference_m":diff_control,
        "scope":"Hydrology event, one-shot biomass and a distinct geomorphic season. No multi-timestep feedback, runoff routing or sediment balance."
    },sort_keys=True))
    assert wet["sat_mean"]>dry["sat_mean"],"H8a wet soil saturation did not increase"
    assert wet["biomass_mean"]>dry["biomass_mean"],"H8a growth did not respond"
    assert wet["cover_mean"]>dry["cover_mean"],"H8a cover did not respond"
    assert wet["kd_core_mean"]<dry["kd_core_mean"],"H8a wet vegetation did not reduce Kd"
    assert diff_wet_dry>1e-13,"H8a field-controlled terrain changes not observed"
    assert diff_control<=1e-13,"H8a disabling cover→diffusion did not remove difference"
    # Run repeatability checks without random seeds
    repeat=one_shot(25.,ALPHA)
    assert np.array_equal(repeat["core_elevations"],wet["core_elevations"]),"H8a replay mismatch"


if __name__=="__main__":
    main()
