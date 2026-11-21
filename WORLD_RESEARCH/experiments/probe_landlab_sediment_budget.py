"""H7: deposición, transporte y balance de sedimentos usando solamente Landlab 2.11.

Protocolo: WORLD_RESEARCH/ETAPA_0_4_PROTOCOLO_SEDIMENTO_FEEDBACK.md
Modelo público: SpaceLargeScaleEroder (procesos roca/sedimento), FlowRouter.
Ninguna ecuación física nueva; el script aporta condiciones de prueba y métricas.

No afirmar cierre perfecto de balance si el residual no lo confirma.
"""
import json
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import PriorityFloodFlowRouter, SpaceLargeScaleEroder

SHAPE = (16,16)
SPACING = 10.0
DT = 0.2
STEPS = 12


def scenario(k_sed):
    g = RasterModelGrid(SHAPE, xy_spacing=SPACING)
    x, y = g.node_x, g.node_y
    # Plane gently sloping to bottom-left; small analytic relief perturbation.
    # The source of mobile sediment is ONLY the initial alluvium.
    br = 0.042 * y + 0.021 * x + 0.016*np.sin(x*.024 + y*.025)
    h = np.full(g.number_of_nodes, 0.6)
    g.at_node["bedrock__elevation"] = br.copy()
    g.at_node["soil__depth"] = h.copy()
    g.at_node["topographic__elevation"] = br.copy() + h
    g.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True, left_is_closed=True,
        right_is_closed=True, top_is_closed=True)
    g.set_watershed_boundary_condition_outlet_id(
        0,g.at_node["topographic__elevation"],-9999.0)
    fr = PriorityFloodFlowRouter(g, flow_metric="D8", suppress_out=True)
    sp = SpaceLargeScaleEroder(
        g, K_sed=k_sed, K_br=0.0, F_f=0.0, phi=0.0, H_star=1.0,
        v_s=3.0, m_sp=.5, n_sp=1.0,
        sp_crit_sed=0, sp_crit_br=0
    )
    area = g.cell_area_at_node[g.core_nodes]
    initial_volume = float(np.sum(h[g.core_nodes]*area))
    cumulative_out=0.
    cumulative_fines=0.
    depositional_steps=0
    erosional_steps=0
    max_dep=0.
    max_er=0.
    for _ in range(STEPS):
        fr.run_one_step()
        suspended_out,bedload_out=sp.run_one_step(DT)
        cumulative_out += float(bedload_out)
        cumulative_fines += float(suspended_out)
        deposition = g.at_node["sediment__deposition_flux"][g.core_nodes]
        erosion = g.at_node["sediment__erosion_flux"][g.core_nodes]
        depositional_steps += int(np.any(deposition > 1e-15))
        erosional_steps += int(np.any(erosion > 1e-15))
        max_dep = max(max_dep,float(np.max(deposition)))
        max_er = max(max_er,float(np.max(erosion)))
        assert np.isfinite(g.at_node["soil__depth"]).all(),"non-finite soil depth"
        assert np.isfinite(g.at_node["topographic__elevation"]).all(),"non-finite relief"
        assert (g.at_node["soil__depth"] >= -1e-10).all(),"negative soil layer"
    final_volume = float(np.sum(g.at_node["soil__depth"][g.core_nodes] * area))
    soil_delta = final_volume - initial_volume
    residual = soil_delta + cumulative_out + cumulative_fines
    mobilized = max(abs(soil_delta),abs(cumulative_out + cumulative_fines),1e-12)
    rel_residual = abs(residual)/mobilized
    return {
        "initial_sediment_volume_m3":initial_volume,
        "final_sediment_volume_m3":final_volume,
        "sediment_volume_change_m3":soil_delta,
        "bedload_export_volume_m3":cumulative_out,
        "fine_export_volume_m3":cumulative_fines,
        "mass_balance_residual_m3":residual,
        "mass_balance_relative_residual":rel_residual,
        "deposition_detected_in_steps":depositional_steps,
        "erosion_detected_in_steps":erosional_steps,
        "max_deposition_flux":max_dep,
        "max_erosion_flux":max_er,
        "net_soil_gain_node_count":int(np.count_nonzero(g.at_node["soil__depth"][g.core_nodes] - .6>1e-9)),
        "node_elevations":g.at_node["topographic__elevation"].copy(),
        "node_soil":g.at_node["soil__depth"].copy()
    }


def main():
    active=scenario(k_sed=.10)
    control=scenario(k_sed=0.)
    def scalars(d):
        return {k:v for k,v in d.items() if k not in ("node_elevations","node_soil")}
    print("WORLD_EVAL_JSON "+json.dumps({
        "model":"SpaceLargeScaleEroder",
        "landlab_version":landlab.__version__,
        "shape":SHAPE,"spacing_m":SPACING,"dt":DT,"steps":STEPS,
        "source_conditions":"K_br=0, F_f=0, phi=0; initial sediment mobile; single outlet",
        "active":scalars(active),"control":scalars(control),
        "interpretation":"Balance accounts for sediment storage and modeled exit. Deposit flux >0 is not identical to net local soil gain; values are experimental not field-calibrated."
    },sort_keys=True))
    assert active["erosion_detected_in_steps"]>0,"H7 erosion not demonstrated"
    assert active["deposition_detected_in_steps"]>0,"H7 deposition not demonstrated"
    assert active["bedload_export_volume_m3"]>=0,"H7 negative outlet export"
    assert control["erosion_detected_in_steps"]==0,"H7 no-erosivity control eroded"
    assert control["deposition_detected_in_steps"]==0,"H7 no-erosivity control deposited"
    assert np.array_equal(control["node_soil"],np.full(control["node_soil"].shape,.6)),"H7 control soil changed"
    assert control["bedload_export_volume_m3"]==0,"H7 control exported sediment"
    assert active["mass_balance_relative_residual"]<0.01, "H7 measured budget exceeds 1% tolerance; inspect units/boundary fluxes before claim"
    replay=scenario(k_sed=.10)
    assert np.array_equal(active["node_soil"],replay["node_soil"]),"H7 replay soil differs"


if __name__=="__main__":
    main()
