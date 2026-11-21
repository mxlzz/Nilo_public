"""Prueba G2-G4: transportar DATOS WorldEngine 3.11 -> Landlab 3.13.

No es un adaptador de producción, ni una validación de unidades físicas.
Una altura generada por celda se proyecta experimentalmente a nodos Landlab
sin afirmar compatibilidad geométrica (centro de celda != vértice).
"""
import hashlib
import json
import sys
import numpy as np
import landlab
from landlab import RasterModelGrid
from landlab.components import FlowAccumulator, StreamPowerEroder


def normalize(source):
    low=float(source.min())
    high=float(source.max())
    assert high>low,"heightmap is flat"
    return 50.0*(source-low)/(high-low)


def quantize_five_levels(values):
    lower=float(values.min())
    upper=float(values.max())
    # Use fixed baseline range to compare before/after; caller decides bounds.
    assert upper>lower
    return np.rint(np.clip(4*(values-lower)/(upper-lower),0,4)).astype(np.uint8)


def run_evolution(base,erode=True,steps=8):
    height,width=base.shape
    grid=RasterModelGrid((height,width),xy_spacing=100.0)
    grid.status_at_node[grid.nodes_at_left_edge]=grid.BC_NODE_IS_CLOSED
    grid.status_at_node[grid.nodes_at_right_edge]=grid.BC_NODE_IS_CLOSED
    grid.status_at_node[grid.nodes_at_top_edge]=grid.BC_NODE_IS_CLOSED
    grid.status_at_node[grid.nodes_at_bottom_edge]=grid.BC_NODE_IS_FIXED_VALUE
    z=grid.add_field("topographic__elevation",base.flatten().copy(),at="node")
    flow=FlowAccumulator(grid,flow_director="D8",runoff_rate=1.0)
    model=StreamPowerEroder(grid,K_sp=0.02)
    for _ in range(steps):
        flow.run_one_step()
        if erode:
            model.run_one_step(dt=0.2)
    assert np.isfinite(z).all(),"Landlab produced invalid height"
    return z.reshape(base.shape).copy()


def main(input_file,output_file):
    with np.load(input_file) as data:
        source=np.array(data["elevation"],dtype="<f8",copy=True)
        seed=int(data["generator_seed"][0])
    assert source.shape==(16,32) and np.isfinite(source).all()
    before_hash=hashlib.sha256(source.tobytes()).hexdigest()
    elevation=normalize(source)
    evolved=run_evolution(elevation,erode=True)
    control=run_evolution(elevation,erode=False)
    assert np.array_equal(control,elevation),"G3: control changed height"
    eroded=elevation-evolved
    assert np.count_nonzero(eroded>1e-7)>0,"G3: generated world did not erode"

    classes_before=quantize_five_levels(elevation)
    # Important: fixed original elevation bounds, not new min and max.
    lo=float(elevation.min());hi=float(elevation.max())
    classes_after=np.rint(np.clip(4*(evolved-lo)/(hi-lo),0,4)).astype(np.uint8)
    reconstruction=lo+(hi-lo)*classes_before/4.0
    rmse=float(np.sqrt(np.mean((reconstruction-elevation)**2)))
    eroded_nodes=eroded>1e-7
    undetected=np.logical_and(eroded_nodes,classes_before==classes_after)
    hidden_fraction=float(np.sum(undetected)/max(1,np.sum(eroded_nodes)))
    assert classes_before.max()<=4
    assert rmse>0.0,"G4: expected quantization loss was absent"

    np.savez_compressed(output_file,elevation_input=elevation,elevation_after=evolved,
        quantized_before=classes_before,quantized_after=classes_after)
    report={
        "pipeline":"WorldEngine heightmap data -> Landlab erosion",
        "source_seed":seed,
        "source_height_sha256":before_hash,
        "shape":list(source.shape),
        "experimental_elevation_scale_meters":[lo,hi],
        "horizontal_spacing_meters":100.0,
        "eroded_nodes":int(np.sum(eroded_nodes)),
        "max_height_loss_meters":float(np.max(eroded)),
        "unchanged_when_eroder_disabled":True,
        "quantization_to_five_levels_rmse_meters":rmse,
        "eroded_nodes_invisible_after_five_level_quantization_fraction":hidden_fraction,
        "landlab_version":landlab.__version__,
        "output_file":output_file,
        "scope_warning":"Technical data import only: WorldEngine heights are arbitrary; cell centers were used as Landlab nodes; Shanhai 0-4 classes are categories, not elevations in meters; no physically calibrated coupling."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main(sys.argv[1],sys.argv[2])
