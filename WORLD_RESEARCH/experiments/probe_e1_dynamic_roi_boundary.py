"""E1/H6: promote a surface column to a local volume, and safely demote it.

Uses xarray.reindex (existing), NumPy, and Landlab's derived-height fields.
No dynamics, stability, 3D collision or physics model. All operations are
representation migrations with explicit material owners.
Plan: ETAPA_1_H6_PROTOCOLO_ROI_DINAMICA.md.
"""
import hashlib
import json
import pathlib
import platform

import numpy as np
import xarray as xr
import landlab
from landlab import RasterModelGrid

from probe_e1_surface_volume_partition import (
    make_state,totals,validate as validate_fixed,
    roi_mask as old_mask,
    W,H,Z,X0,X1,Y0,Y1,MATERIALS,
)

def validate_dynamic(ds, expected):
    mask=np.asarray(ds["region_is_volume"].values,dtype=bool)
    xvals=ds.coords["roi_x"].values.astype(int).tolist()
    yvals=ds.coords["roi_y"].values.astype(int).tolist()
    assert xvals==list(range(xvals[0],xvals[-1]+1))
    assert yvals==list(range(Y0,Y1))
    predicted_mask=np.zeros((H,W),dtype=bool)
    predicted_mask[np.ix_(yvals,xvals)]=True
    if not np.array_equal(mask,predicted_mask):
        raise ValueError("ROI bounds and ownership mask disagree")
    a=ds["outside_column_mass"].values
    b=ds["roi_voxel_mass"].values
    d=ds["material_density"].values
    if a.shape!=(2,H,W) or b.shape!=(2,Z,len(yvals),len(xvals)):
        raise ValueError("Dimension/schema mismatch")
    if ds["outside_column_mass"].attrs.get("units")!="kg" or ds["roi_voxel_mass"].attrs.get("units")!="kg":
        raise ValueError("Mass unit missing")
    if ds.coords["material"].values.tolist()!=list(MATERIALS):
        raise ValueError("Material labels do not match schema")
    if not all(np.isfinite(q).all() for q in (a,b,d)):
        raise ValueError("Nonfinite mass or density")
    if np.any(a<0) or np.any(b<0) or np.any(d<=0):
        raise ValueError("Negative mass or nonpositive density")
    if np.any(a[:,mask]!=0):
        raise ValueError("Double ownership of material")
    if np.any(a[1]!=0):
        raise ValueError("Exterior column material mixture unsupported by this contract")
    volumes=(b/d[:,None,None,None]).sum(axis=0)
    if np.any(volumes>1.+1e-12):
        raise ValueError("Voxel exceeds volume")
    got=totals(ds)
    for key in MATERIALS:
        if not np.isclose(got[key],expected[key],atol=1e-10,rtol=0):
            raise ValueError("Missing or invented material "+key)
    return got


def height(ds):
    dens=ds["material_density"].values
    outside=ds["outside_column_mass"].values
    # All surface-only columns are compact, supported from z0.
    elev=np.sum(outside/dens[:,None,None],axis=0)
    b=ds["roi_voxel_mass"].values
    filled=np.sum(b/dens[:,None,None,None],axis=0)>0
    roi_height=np.where(filled,np.arange(Z)[:,None,None]+1,0).max(axis=0)
    ys=ds.coords["roi_y"].values.astype(int)
    xs=ds.coords["roi_x"].values.astype(int)
    elev[np.ix_(ys,xs)]=roi_height
    return elev


def landlab_preview(ds):
    g=RasterModelGrid((H+2,W+2),xy_spacing=1.)
    z=g.add_zeros("topographic__elevation",at="node",units="m")
    h=height(ds)
    for node in g.node_at_cell:
        x=int(round(g.x_of_node[node]))-1
        y=int(round(g.y_of_node[node]))-1
        z[node]=h[y,x]
    for node in g.node_at_cell:
        x=int(round(g.x_of_node[node]))-1
        y=int(round(g.y_of_node[node]))-1
        assert g.at_node["topographic__elevation"][node]==h[y,x]
    return g


def digest(ds):
    return hashlib.sha256(
        ds["outside_column_mass"].values.tobytes()+
        ds["roi_voxel_mass"].values.tobytes()+
        ds["region_is_volume"].values.tobytes()
    ).hexdigest()


def make_cavity():
    ds=make_state()
    roi=ds["roi_voxel_mass"].values
    assert np.all(roi[0,2:4,2:4,2:6]==2.)
    removed=float(roi[0,2:4,2:4,2:6].sum())
    assert removed==32.
    roi[0,2:4,2:4,2:6]=0.
    expected={"A":730.,"B":3.}
    validate_fixed(ds,expected)
    validate_dynamic(ds,expected)
    return ds,expected,removed


def promote_boundary(ds):
    assert ds.coords["roi_x"].values.tolist()==list(range(X0,X1))
    candidate=ds.reindex(roi_x=np.arange(X0,X1+1),fill_value=0).copy(deep=True)
    outside=candidate["outside_column_mass"].values
    newroi=candidate["roi_voxel_mass"].values
    assert np.all(outside[0,Y0:Y1,X1]==4.)
    assert np.all(newroi[:,:,:,-1]==0.)
    mass_migrated=float(np.sum(outside[0,Y0:Y1,X1]))
    assert mass_migrated==24.
    newroi[0,0:2,:,-1]=2.
    outside[0,Y0:Y1,X1]=0.
    candidate["region_is_volume"].values[Y0:Y1,X1]=True
    return candidate,mass_migrated


def is_lossless_column_demotable(ds, x, y):
    xs=ds.coords["roi_x"].values.tolist()
    ys=ds.coords["roi_y"].values.tolist()
    if x not in xs or y not in ys:
        return False
    v=ds["roi_voxel_mass"].values[:,:,ys.index(y),xs.index(x)]
    occupied=v.sum(axis=0)>0
    count=int(occupied.sum())
    compact=bool(np.array_equal(occupied, np.arange(Z)<count))
    # Only a homogeneous material A compact column is representable by
    # this particular 2D exterior contract. No B or void under roof.
    return compact and np.all(v[1]==0) and np.all(v[0,:count]==2.) and np.all(v[0,count:]==0)


def demote_new_strip(ds):
    assert ds.coords["roi_x"].values.tolist()==list(range(X0,X1+1))
    for y in range(Y0,Y1):
        assert is_lossless_column_demotable(ds,X1,y),("new strip cannot be demoted",y)
    reverted=ds.sel(roi_x=slice(X0,X1-1)).copy(deep=True)
    reverted["outside_column_mass"].values[0,Y0:Y1,X1]=4.
    reverted["region_is_volume"].values[Y0:Y1,X1]=False
    return reverted


def main():
    base, expected, sink=make_cavity()
    first_hash=digest(base)
    first_heights=height(base)
    assert first_heights[3,5]==6.
    before_3d=base["roi_voxel_mass"].values.copy()
    g_before=landlab_preview(base)
    assert g_before.number_of_cells==H*W

    grown, transferred=promote_boundary(base)
    assert validate_dynamic(grown,expected)==expected
    assert np.array_equal(height(grown),first_heights), "Representational change unexpectedly altered height"
    assert np.array_equal(grown["roi_voxel_mass"].values[:,:,:,:-1],before_3d)
    assert landlab_preview(grown).number_of_cells==H*W
    assert transferred==24.

    # Negative: if promoted stock is counted twice, reject.
    dup=grown.copy(deep=True)
    dup["outside_column_mass"].values[0,Y0:Y1,X1]=4.
    duplication_rejected=False
    try:
        validate_dynamic(dup,expected)
    except ValueError:
        duplication_rejected=True
    assert duplication_rejected

    # Negative: removing outside stock without moving it into new owner
    # must be rejected by the global material balance.
    missing=base.reindex(roi_x=np.arange(X0,X1+1),fill_value=0).copy(deep=True)
    missing["outside_column_mass"].values[0,Y0:Y1,X1]=0.
    missing["region_is_volume"].values[Y0:Y1,X1]=True
    missing_stock_rejected=False
    try:
        validate_dynamic(missing,expected)
    except ValueError:
        missing_stock_rejected=True
    assert missing_stock_rejected

    # A column with an internal cavity under an occupied roof must not
    # be reduced to one exterior height + compact-column mass.
    assert not is_lossless_column_demotable(grown,5,3)
    assert is_lossless_column_demotable(grown,X1,3)
    illegal_demote_rejected=True

    # NetCDF preserves the enlarged ROI mask, labels, stock, and height.
    path=pathlib.Path("/tmp/e1_h6_expanded_roi.nc")
    grown.to_netcdf(path,engine="scipy")
    with xr.open_dataset(path,engine="scipy") as loaded:
        reloaded=loaded.load()
    assert validate_dynamic(reloaded,expected)==expected
    assert digest(reloaded)==digest(grown)
    assert np.array_equal(height(reloaded),first_heights)

    # Reverse ONLY the new compact outer strip; no hollow column can be
    # silently collapsed into the height-only domain.
    reverted=demote_new_strip(grown)
    assert validate_dynamic(reverted,expected)==expected
    assert np.array_equal(height(reverted),first_heights)
    assert np.array_equal(reverted["roi_voxel_mass"].values,before_3d)
    assert np.array_equal(reverted["outside_column_mass"].values,base["outside_column_mass"].values)
    assert np.array_equal(reverted["region_is_volume"].values,base["region_is_volume"].values)
    assert digest(reverted)==first_hash
    assert landlab_preview(reverted).number_of_cells==H*W

    report={
        "test":"E1 H6 reversible dynamic ROI boundary representation without physics",
        "python_version":platform.python_version(),
        "xarray_version":xr.__version__,
        "landlab_version":landlab.__version__,
        "initial_roi_x_end_exclusive":X1,
        "expanded_roi_x_end_exclusive":X1+1,
        "roi_columns_original":int(base["region_is_volume"].values.sum()),
        "roi_columns_expanded":int(grown["region_is_volume"].values.sum()),
        "roi_columns_reverted":int(reverted["region_is_volume"].values.sum()),
        "migrated_material_kg":transferred,
        "tracked_external_cavity_sink_A_kg":sink,
        "global_inventory_after_cavity_kg":expected,
        "height_unchanged_through_all_migrations":True,
        "original_cavity_preserved_exactly":True,
        "double_owner_rejected":duplication_rejected,
        "missing_stock_rejected":missing_stock_rejected,
        "cavity_demote_rejected":illegal_demote_rejected,
        "compact_new_strip_demoted_losslessly":True,
        "roundtrip_original_owner_hash_equal":True,
        "netcdf_expanded_bytes":path.stat().st_size,
        "netcdf_expanded_state_exact":True,
        "limits":"Fixed single rectangular strip promotion only; full homogeneous exterior columns. No automatic detection/retessellation, allocation benchmarks, concurrent actors, movement, mechanistic model, partial cells or 3D structural stability."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
