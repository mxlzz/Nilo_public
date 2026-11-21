"""Ensayo de reutilización de Landlab: NO implementa un nuevo simulador.

Usa APIs documentadas: RasterModelGrid, FlowAccumulator, StreamPowerEroder.
Contraste de flujo de aportes, erosión sí/no, restauración determinista.

No pretende que StreamPowerEroder conserve sedimentos: este ensayo mide
incisión, y su limitación en masa sedimentaria queda explícita.
"""
import io
import json
import platform
import time
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import FlowAccumulator, StreamPowerEroder

STEPS = 12
SHAPE = (18, 18)
K = 0.015


def initial_elev(grid):
    x = grid.node_x.astype(float)
    y = grid.node_y.astype(float)
    return 0.12 * y + 0.002 * (x - 9.0) ** 2 + 0.013 * np.sin(0.37 * x + 0.31 * y)


def make(grid_elevation, rate=1.0):
    mg = RasterModelGrid(SHAPE, xy_spacing=1.0)
    mg.status_at_node[mg.nodes_at_left_edge] = mg.BC_NODE_IS_CLOSED
    mg.status_at_node[mg.nodes_at_right_edge] = mg.BC_NODE_IS_CLOSED
    mg.status_at_node[mg.nodes_at_top_edge] = mg.BC_NODE_IS_CLOSED
    # bottom edge = fixed-value outlet (keep its nodes unchanged)
    mg.status_at_node[mg.nodes_at_bottom_edge] = mg.BC_NODE_IS_FIXED_VALUE
    z = mg.add_field("topographic__elevation", np.asarray(grid_elevation, dtype=float).copy(), at="node")
    flow = FlowAccumulator(mg, flow_director="D8", runoff_rate=rate)
    eroder = StreamPowerEroder(mg, K_sp=K)
    return mg,z,flow,eroder


def run(z_start, erosion, rate, n=STEPS):
    mg,z,flow,eroder=make(z_start, rate)
    for _ in range(n):
        flow.run_one_step()
        if erosion:
            eroder.run_one_step(dt=0.4)
    return mg,z.copy()


def main():
    t0=time.perf_counter()
    geometry=RasterModelGrid(SHAPE, xy_spacing=1.0)
    base=initial_elev(geometry)
    rain_grid,z_r,flow_r,_=make(base, rate=1.0)
    flow_r.run_one_step()
    discharge_r=rain_grid.at_node["surface_water__discharge"].copy()

    dry_grid,z_d,flow_d,_=make(base, rate=0.0)
    flow_d.run_one_step()
    discharge_d=dry_grid.at_node["surface_water__discharge"].copy()
    core=rain_grid.core_nodes
    assert float(np.max(discharge_r[core]))>0.0, "L1: flow does not respond to rainfall"
    assert np.allclose(discharge_d[core],0,atol=1e-12), "L1: dry scenario still produces discharge"

    mg,final=run(base,erosion=True,rate=1.0)
    difference=base-final
    assert np.all(np.isfinite(final)), "L2: non-finite elevations"
    assert np.any(difference[mg.core_nodes]>1e-5), "L2: no measurable erosion"
    assert np.all(difference[mg.core_nodes]>=-1e-8), "L2: erosion raised terrain in interior"
    _,control=run(base,erosion=False,rate=1.0)
    assert np.array_equal(control,base),"L3: topology changed without erosion"
    _,replay=run(base,erosion=True,rate=1.0)
    assert np.allclose(replay,final,atol=1e-12),"L4: replay mismatch"

    # Restart by serializing only the physical state used by this smoke,
    # then recreating flow and eroder with the same constants.
    _,mid=run(base,erosion=True,rate=1.0,n=STEPS//2)
    buffer=io.BytesIO()
    np.savez(buffer,elevation=mid)
    buffer.seek(0)
    with np.load(buffer) as restored:
        _,second=run(restored["elevation"],erosion=True,rate=1.0,n=STEPS//2)
    assert np.allclose(second,final,atol=1e-12),"L4: explicit checkpoint continuation mismatch"

    result={
        "candidate":"Landlab",
        "landlab_version":getattr(landlab,"__version__","unknown"),
        "numpy_version":np.__version__,
        "python":platform.python_version(),
        "shape":list(SHAPE),
        "steps":STEPS,
        "dt_per_step":0.4,
        "K_sp":K,
        "flow_discharge_max_with_input":float(np.max(discharge_r[core])),
        "flow_discharge_max_zero_input":float(np.max(discharge_d[core])),
        "eroded_core_nodes":int(np.sum(difference[mg.core_nodes]>1e-5)),
        "max_core_elevation_decrease":float(np.max(difference[mg.core_nodes])),
        "control_unchanged":bool(np.array_equal(control,base)),
        "replay_and_state_restore_equal":True,
        "elapsed_seconds":round(time.perf_counter()-t0,4),
        "important_scope":"FlowAccumulator routes effective runoff; no water storage balance tested. StreamPowerEroder incises bedrock without recording sediment mass in this test."
    }
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True))


if __name__ == "__main__":
    main()
