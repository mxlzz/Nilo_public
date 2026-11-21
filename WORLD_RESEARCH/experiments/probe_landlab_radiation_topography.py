"""H10a—probamos Landlab Radiation y PET con relieve mutado, sin física propia.

Plan definido antes del código: ETAPA_0_6_PROTOCOLO_RETORNO_RADIACION.md.
Esta prueba detecta geometría guardada en constructor y la utilidad de
reinstanciar, sin afirmar aún un ciclo ecohidrológico continuo.
"""
import json
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import Radiation, PotentialEvapotranspiration

SHAPE=(8,8)
DX=10.0
DAY_IN_YEAR=.5
CHANGE_M=12.0

def main():
    g=RasterModelGrid(SHAPE,xy_spacing=DX)
    x,y=g.node_x,g.node_y
    baseline=100.0 + 0.025*x+0.015*y+0.25*np.sin((x+y)/18.0)
    g.at_node["topographic__elevation"]=baseline.copy()
    rad=Radiation(g,latitude=34.0,current_time=DAY_IN_YEAR)
    pet=PotentialEvapotranspiration(g,method="Cosine",
        current_time=DAY_IN_YEAR,MeanTmaxF=8.0,delta_d=0.0)
    rad.update()
    pet.update()
    ratio_a=g.at_cell["radiation__ratio_to_flat_surface"].copy()
    pet_a=g.at_cell["surface__potential_evapotranspiration_rate"].copy()
    slope_a=g.at_cell["Slope"].copy()

    rad.update();pet.update()
    assert np.array_equal(ratio_a,g.at_cell["radiation__ratio_to_flat_surface"]), "H10a repeated radiation not deterministic"
    assert np.array_equal(pet_a,g.at_cell["surface__potential_evapotranspiration_rate"]), "H10a repeated PET not deterministic"

    target=int(g.node_at_cell[len(g.node_at_cell)//2])
    g.at_node["topographic__elevation"][target]+=CHANGE_M
    rad.update();pet.update()
    ratio_b=g.at_cell["radiation__ratio_to_flat_surface"].copy()
    pet_b=g.at_cell["surface__potential_evapotranspiration_rate"].copy()
    slope_b=g.at_cell["Slope"].copy()

    newrad=Radiation(g,latitude=34.0,current_time=DAY_IN_YEAR)
    newrad.update();pet.update()
    ratio_c=g.at_cell["radiation__ratio_to_flat_surface"].copy()
    pet_c=g.at_cell["surface__potential_evapotranspiration_rate"].copy()
    slope_c=g.at_cell["Slope"].copy()

    stale=np.max(np.abs(ratio_b-ratio_a))
    new=np.max(np.abs(ratio_c-ratio_a))
    difference=np.max(np.abs(ratio_c-ratio_b))
    delta_pet=float(np.max(np.abs(pet_c-pet_b)))
    metrics={
        "candidate":"Landlab Radiation + PotentialEvapotranspiration",
        "landlab_version":landlab.__version__,
        "shape":SHAPE,"grid_spacing_m":DX,"test_day_fractional_year":DAY_IN_YEAR,
        "topographic_change_one_node_m":CHANGE_M,
        "ratio_mean_baseline":float(np.mean(ratio_a)),
        "ratio_mean_same_object_mutated_topography":float(np.mean(ratio_b)),
        "ratio_mean_fresh_object_mutated_topography":float(np.mean(ratio_c)),
        "same_object_ratio_change_max":float(stale),
        "fresh_vs_original_ratio_change_max":float(new),
        "fresh_vs_stale_ratio_change_max":float(difference),
        "PET_fresh_vs_stale_max_mm_per_day":delta_pet,
        "PET_baseline_mean":float(np.mean(pet_a)),
        "PET_fresh_mean":float(np.mean(pet_c)),
        "slope_change_same_object_max":float(np.max(np.abs(slope_b-slope_a))),
        "slope_change_fresh_object_max":float(np.max(np.abs(slope_c-slope_a))),
        "disclaimer":"One static geometric perturbation only; no calibrated feedback. PET units follow component API; no mass budget or evolving ecology."
    }
    print("WORLD_EVAL_JSON "+json.dumps(metrics,sort_keys=True))
    assert np.isfinite(ratio_c).all() and np.isfinite(pet_c).all()
    assert np.all(ratio_c>=0.0)
    assert stale<=1e-14,"H10a: cached ratio unexpectedly changed, update architectural assumption"
    assert np.max(np.abs(slope_b-slope_a))<=1e-14,"H10a: cached slope unexpectedly updated"
    assert np.max(np.abs(slope_c-slope_a))>1e-6,"H10a: reinitialization failed to refresh slope"
    assert new>1e-5,"H10a: reinitialization failed to refresh incidence"
    assert delta_pet>1e-5,"H10a: geometric PET output not responding"

if __name__=="__main__":
    main()
