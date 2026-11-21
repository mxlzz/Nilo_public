"""E1/H1: compare two existing data containers against matter_v0 oracle.

NO falling sand, heat law, infiltration physics or new world engine here.
Input: existing MatterGrid minimal invariant-proven manual transfers.
Output: Landlab 2D cell fields and xarray 2-level data with NetCDF replay.
Plan: WORLD_RESEARCH/ETAPA_1_H1_PROTOCOLO_ESTADO_MATERIA.md.
"""
from __future__ import annotations
import hashlib
import json
import math
import pathlib
import sys
import numpy as np
import xarray as xr
import landlab
from landlab import RasterModelGrid
from matter_v0 import Material, MatterGrid

WIDTH=3
HEIGHT=2
MATERIALS={"A":Material("A",2.0),"B":Material("B",1.0)}
CELL_VOLUME_M3=1.0

def oracle():
    m=MatterGrid(WIDTH,HEIGHT,MATERIALS,cell_volume=CELL_VOLUME_M3)
    m.add_initial((0,0),"A",.6)
    m.add_initial((0,0),"B",.2)
    m.add_initial((1,0),"B",.4)
    m.add_initial((2,1),"A",.5)
    m.transfer((0,0),(1,0),"A",.1)
    assert m.mass_by_material()=={"A":1.1,"B":.6000000000000001} or m.mass_by_material()=={"A":1.1,"B":.6}
    return m

def landlab_projection(m):
    # A RasterModelGrid's cells are represented by its interior core nodes;
    # access each center's physical x/y rather than assuming 1D ordering.
    g=RasterModelGrid((HEIGHT+2,WIDTH+2),xy_spacing=1.0)
    for name in sorted(MATERIALS):
        g.add_zeros(f"material_mass__{name}",at="cell",units="kg")
    index={}
    for cell,node in enumerate(g.node_at_cell):
        x=int(round(g.x_of_node[node]))-1
        y=int(round(g.y_of_node[node]))-1
        assert 0<=x<WIDTH and 0<=y<HEIGHT
        assert (x,y) not in index
        index[(x,y)]=cell
    assert len(index)==WIDTH*HEIGHT
    for (x,y),stock in m.cells.items():
        for material_id,amount in stock.items():
            g.at_cell[f"material_mass__{material_id}"][index[(x,y)]]=amount
    assert all(g.field_units(f"material_mass__{name}",at="cell")=="kg" for name in MATERIALS)
    m2=MatterGrid(WIDTH,HEIGHT,MATERIALS,cell_volume=CELL_VOLUME_M3)
    for (x,y),i in index.items():
        for name in MATERIALS:
            stock=float(g.at_cell[f"material_mass__{name}"][i])
            if stock>0:m2.add_initial((x,y),name,stock)
    assert m.snapshot()==m2.snapshot(),"Landlab projection not exactly reversible"
    return g,index,m2

def dataset_projection(m):
    density=np.asarray([MATERIALS[n].density for n in sorted(MATERIALS)],dtype=float)
    masses=np.zeros((len(MATERIALS),2,HEIGHT,WIDTH),dtype=np.float64)
    names=sorted(MATERIALS)
    for (x,y),stock in m.cells.items():
        for name,amount in stock.items():
            masses[names.index(name),0,y,x]=amount
    ds=xr.Dataset(
        data_vars={
            "material_mass":(
                ("material","level","y","x"),masses,
                {"units":"kg","description":"stored material mass, no dynamics"}
            ),
            "material_density":(
                ("material",),density,
                {"units":"kg m-3"}
            )
        },
        coords={
            "material":names,"level":[0,1],
            "y":np.arange(HEIGHT,dtype=np.int32),
            "x":np.arange(WIDTH,dtype=np.int32)
        },
        attrs={
            "schema_version":1,
            "cell_capacity_m3":CELL_VOLUME_M3,
            "model":"E1 H1 material state, not a solver",
        }
    )
    return ds

def validate_and_restore(ds,level=0):
    assert tuple(ds["material_mass"].dims)==("material","level","y","x")
    assert ds["material_mass"].attrs.get("units")=="kg"
    assert ds["material_density"].attrs.get("units")=="kg m-3"
    assert ds.attrs.get("schema_version")==1
    density={
        name:float(ds["material_density"].sel(material=name).item())
        for name in MATERIALS
    }
    materials={name:Material(name,v) for name,v in density.items()}
    result=MatterGrid(WIDTH,HEIGHT,materials,cell_volume=float(ds.attrs["cell_capacity_m3"]))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            for name in MATERIALS:
                value=float(ds["material_mass"].sel(material=name,level=level,y=y,x=x).item())
                if not math.isfinite(value) or value<0:
                    raise ValueError("Nonfinite/negative amount in xarray material field")
                if value>0:
                    result.add_initial((x,y),name,value)
    return result

def main():
    original=oracle()
    g,index,landlab_restored=landlab_projection(original)
    ds=dataset_projection(original)
    ds_restored=validate_and_restore(ds,level=0)
    assert ds_restored.snapshot()==original.snapshot()
    assert np.all(ds["material_mass"].sel(level=1).values==0)

    # Distinct vertical layer; an EXPLICIT initial stock, not an emergent
    # law or transport. Its separate capacity is independently validated.
    extra=ds.copy(deep=True)
    extra["material_mass"].loc[dict(material="A",level=1,x=1,y=0)]=.3
    upper=validate_and_restore(extra,level=1)
    assert upper.mass_by_material()=={"A":.3,"B":0.}
    assert validate_and_restore(extra,level=0).snapshot()==original.snapshot()
    totalA=original.mass_by_material()["A"]+upper.mass_by_material()["A"]

    invalid=ds.copy(deep=True)
    invalid["material_mass"].loc[dict(material="A",level=0,x=0,y=0)]=-1.
    try:
        validate_and_restore(invalid)
        raise AssertionError("Negative material amount silently accepted by the STATE CONTRACT")
    except ValueError:
        pass
    excess=ds.copy(deep=True)
    excess["material_mass"].loc[dict(material="A",level=0,x=0,y=0)]=3.
    try:
        validate_and_restore(excess)
        raise AssertionError("Over-capacity cell silently accepted by the STATE CONTRACT")
    except ValueError:
        pass

    # netCDF is data only, not a pickle of code execution.
    path=pathlib.Path("/tmp/e1_h1_material_multilevel.nc")
    extra.to_netcdf(path,engine="scipy")
    loaded=xr.open_dataset(path,engine="scipy").load()
    assert loaded["material_mass"].attrs.get("units")=="kg"
    assert loaded["material_density"].attrs.get("units")=="kg m-3"
    assert np.array_equal(loaded["material_mass"].values,extra["material_mass"].values)
    assert loaded.attrs["schema_version"]==1
    assert validate_and_restore(loaded,0).snapshot()==original.snapshot()
    assert validate_and_restore(loaded,1).snapshot()==upper.snapshot()
    loaded.close()

    report={
        "test":"E1-H1 existing material oracle reversible to Landlab cell fields and 2-level xarray",
        "landlab_version":landlab.__version__,
        "xarray_version":xr.__version__,
        "grid_cells":g.number_of_cells,
        "material_count":len(MATERIALS),
        "catalogue_density_kg_m3":{name:MATERIALS[name].density for name in sorted(MATERIALS)},
        "baseline_mass_kg":original.mass_by_material(),
        "baseline_oracle_sha256":hashlib.sha256(original.snapshot().encode()).hexdigest(),
        "projection_landlab_exact":landlab_restored.snapshot()==original.snapshot(),
        "projection_xarray_level0_exact":ds_restored.snapshot()==original.snapshot(),
        "vertical_second_layer_is_independent":True,
        "extra_upper_layer_A_mass_kg":upper.mass_by_material()["A"],
        "both_levels_A_total_kg":totalA,
        "invalid_negative_rejected":True,
        "invalid_capacity_rejected":True,
        "netcdf_bytes":path.stat().st_size,
        "netcdf_roundtrip_exact":True,
        "limitations":"Library fields do NOT automatically enforce conservation, solidity, species transitions, contact or layer interactions. Landlab is 2D surface, xarray 2-level only supports labelled storage, NOT physical 3D."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))
    assert report["projection_landlab_exact"]
    assert report["projection_xarray_level0_exact"]

if __name__=="__main__":
    main()
