"""E1/H2: one material-state owner and an explicitly shared Landlab field view.

No simulation law. Manual inventories are changed with pre-existing
conservation/capacity validator from E1/H1. Published Landlab add_field(copy=)
is the candidate capability. Plan: ETAPA_1_H2_PROTOCOLO_PROPIEDAD_ESTADO.md.
"""
from __future__ import annotations
import hashlib
import json
import pathlib

import landlab
import numpy as np
import xarray as xr
from landlab import RasterModelGrid

from probe_e1_state_representations import (
    HEIGHT, MATERIALS, WIDTH, dataset_projection, oracle,
    validate_and_restore,
)


def bind_fields(ds, *, copy=False):
    """Bind to *existing* backing mass tensor. Never create independent stock."""
    g=RasterModelGrid((HEIGHT+2,WIDTH+2),xy_spacing=1.)
    mapping={}
    for ci,node in enumerate(g.node_at_cell):
        x=int(round(g.x_of_node[node]))-1
        y=int(round(g.y_of_node[node]))-1
        assert (x,y) not in mapping
        mapping[(x,y)]=ci
    assert len(mapping)==HEIGHT*WIDTH
    assert all(mapping[(x,y)]==y*WIDTH+x
               for y in range(HEIGHT) for x in range(WIDTH)), (
        "This test requires cell-to-tensor contiguous ordering; never silently reorder"
    )
    root=ds["material_mass"].values
    aliases={}
    for i,material in enumerate(ds.coords["material"].values.tolist()):
        view=root[i,0,:,:].reshape(-1)
        field=g.add_field(f"material_mass__{material}",view,
                          at="cell",units="kg",copy=copy)
        aliases[material]=bool(np.shares_memory(field,root))
        for (x,y),cell_idx in mapping.items():
            assert field[cell_idx]==root[i,0,y,x], (
                "Cell index did not match state tensor spatial convention"
            )
    return g,mapping,aliases


def matter_totals(ds):
    v=ds["material_mass"].values
    return {str(m):float(np.sum(v[i,:,:,:],dtype=np.float64))
            for i,m in enumerate(ds.coords["material"].values.tolist())}


def main():
    ds=dataset_projection(oracle())
    root=ds["material_mass"].values
    second_level_before=root[:,1,:,:].copy()
    before_totals=matter_totals(ds)
    g,mapping,aliases=bind_fields(ds)
    assert all(aliases.values()),"H2 copy=False is not a genuine shared memory view"

    # A single material flow is an imposed manual inventory transaction,
    # NOT a new gravity/contact/transport rule.
    a=g.at_cell["material_mass__A"]
    src=mapping[(0,0)]
    dst=mapping[(1,0)]
    assert a[src]>.125
    oldsrc=float(root[0,0,0,0]);olddst=float(root[0,0,0,1])
    a[src]-=.125
    a[dst]+=.125
    assert root[0,0,0,0]==oldsrc-.125
    assert root[0,0,0,1]==olddst+.125
    assert validate_and_restore(ds,0).mass_by_material()["A"]>0

    # The reverse direction uses the existing xarray backing array.
    old_from=float(a[dst])
    old_to=float(a[mapping[(2,1)]])
    root[0,0,0,1]-=.0625
    root[0,0,1,2]+=.0625
    assert a[dst]==old_from-.0625
    assert a[mapping[(2,1)]]==old_to+.0625
    totals=matter_totals(ds)
    assert all(np.isclose(totals[k],before_totals[k],rtol=0,atol=1e-12)
               for k in before_totals),"Manual transfer created/destroyed material"
    assert np.array_equal(root[:,1,:,:],second_level_before), (
        "The upper independent layer changed during lower layer edits"
    )
    valid=validate_and_restore(ds,0)
    valid_snapshot=valid.snapshot()

    # Negative control for alias behavior: a dedicated Landlab copy must
    # decouple from the canonical material mass array.
    g_copy,_,copy_aliases=bind_fields(ds,copy=True)
    assert not any(copy_aliases.values()),"copy=True unexpectedly shared storage"
    before_copy=float(g_copy.at_cell["material_mass__A"][src])
    canonical_before=float(a[src])
    a[src]+=.03125  # temporarily mutate; copies must not change
    assert float(g_copy.at_cell["material_mass__A"][src])==before_copy
    a[src]=canonical_before

    # Corrupter is intentionally able to mutate low-level NumPy state;
    # ONLY the external contract validator provides a rejection gate.
    negative_before=float(a[src])
    a[src]=-1.
    negative_rejected=False
    try:
        validate_and_restore(ds,0)
    except ValueError:
        negative_rejected=True
    finally:
        a[src]=negative_before
    assert negative_rejected,"Corrupt material state was not rejected"

    overcapacity_before=float(a[src])
    a[src]=3.
    capacity_rejected=False
    try:
        validate_and_restore(ds,0)
    except ValueError:
        capacity_rejected=True
    finally:
        a[src]=overcapacity_before
    assert capacity_rejected,"Overcapacity state not rejected"
    assert validate_and_restore(ds,0).snapshot()==valid_snapshot

    filename=pathlib.Path("/tmp/e1_h2_owner_shared_state.nc")
    ds.to_netcdf(filename,engine="scipy")
    restored=xr.open_dataset(filename,engine="scipy").load()
    try:
        # Data persists; references DO NOT survive serialization.
        assert np.array_equal(restored["material_mass"].values,root)
        new_grid,_,rebound_aliases=bind_fields(restored,copy=False)
        assert all(rebound_aliases.values())
        restored_grid_field=new_grid.at_cell["material_mass__A"]
        value=float(restored["material_mass"].values[0,0,0,0])
        restored_grid_field[src]+=.015625
        assert restored["material_mass"].values[0,0,0,0]==value+.015625
        restored_grid_field[src]=value
        assert validate_and_restore(restored,0).snapshot()==valid_snapshot
    finally:
        restored.close()

    output={
        "test":"E1-H2 shared single-owner material inventory with Landlab views",
        "landlab_version":landlab.__version__,
        "xarray_version":xr.__version__,
        "shape":list(root.shape),
        "cell_mapping_index_order_checked":True,
        "shares_memory_landlab_copy_false":aliases,
        "landlab_to_xarray_mutation_visible":True,
        "xarray_to_landlab_mutation_visible":True,
        "owner_totals_after_bidirectional_transactions":totals,
        "material_mass_conserved":True,
        "upper_layer_unchanged":True,
        "copy_true_shared_memory":copy_aliases,
        "independent_copy_negative_control_passed":True,
        "negative_mass_rejected_by_contract":negative_rejected,
        "overcapacity_rejected_by_contract":capacity_rejected,
        "netcdf_bytes":filename.stat().st_size,
        "reloaded_values_exact":True,
        "rebinding_after_reload_shares_memory":rebound_aliases,
        "restored_snapshot_sha256":hashlib.sha256(valid_snapshot.encode()).hexdigest(),
        "limitations":"No state lock, transactional write API, simultaneous solver alias guarantee, 3D physics, property-based solids, or cross-process pointer alias. Numpy fields permit invalid edits until validator is called."
    }
    print("WORLD_EVAL_JSON "+json.dumps(output,sort_keys=True))


if __name__=="__main__":
    main()
