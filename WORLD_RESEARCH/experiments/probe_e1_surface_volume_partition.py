"""E1/H5: one material owner per spatial region, Landlab height as cache.

NO physical law, erosion or dynamical coupling. The manual removal operations
are prescribed external interventions with explicitly accounted mass leaving.
Protocol: ETAPA_1_H5_PROTOCOLO_ACOPLAMIENTO_ESTADO.md.

The 2D exterior surface owns uninterrupted solid columns only.
The local 3D region owns material voxels, including enclosed voids.
Landlab's node elevations are a DERIVED VIEW, NEVER material inventory.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import platform

import numpy as np
import xarray as xr
import landlab
from landlab import RasterModelGrid

W,H,Z=12,8,7
X0,X1=2,10
Y0,Y1=1,7
RX,RY=X1-X0,Y1-Y0
PITCH_M=1.
DENSITIES=np.array([2.,1.],dtype=np.float64)
MATERIALS=("A","B")


def roi_mask():
    mask=np.zeros((H,W),dtype=bool)
    mask[Y0:Y1,X0:X1]=True
    return mask


def make_state():
    mask=roi_mask()
    outside=np.zeros((2,H,W),dtype=np.float64)
    outside[0,~mask]=4.0 # two 1m³ A voxels per exterior column
    roi=np.zeros((2,Z,RY,RX),dtype=np.float64)
    roi[0,0:6,:,:]=2.
    for x in (5,6,7):
        roi[0,5,2-Y0,x-X0]=0.
        roi[1,5,2-Y0,x-X0]=1.
    state=xr.Dataset(
        data_vars={
            "outside_column_mass":(
                ("material","y","x"),outside,
                {"units":"kg","meaning":"exclusive mass owner outside voxel ROI; full columns"}
            ),
            "roi_voxel_mass":(
                ("material","z","roi_y","roi_x"),roi,
                {"units":"kg","meaning":"exclusive voxel mass owner within ROI"}
            ),
            "material_density":(("material",),DENSITIES,
                                {"units":"kg m-3"}),
            "region_is_volume":(("y","x"),mask,
                                {"meaning":"true means all stock must be in roi_voxel_mass"}),
        },
        coords={
            "material":list(MATERIALS),
            "y":np.arange(H,dtype=np.int32),
            "x":np.arange(W,dtype=np.int32),
            "roi_y":np.arange(Y0,Y1,dtype=np.int32),
            "roi_x":np.arange(X0,X1,dtype=np.int32),
            "z":np.arange(Z,dtype=np.int32),
        },
        attrs={
            "schema_version":1,
            "voxel_volume_m3":1.0,
            "voxel_pitch_m":1.0,
            "roi_origin_x":X0,
            "roi_origin_y":Y0,
            "rule":"2D columns own mass only OUTSIDE ROI; voxel field owns mass only INSIDE ROI. Derived height is not another owner.",
        }
    )
    return state


def totals(ds):
    return {
        name:float(
            ds["outside_column_mass"].sel(material=name).sum().item()+
            ds["roi_voxel_mass"].sel(material=name).sum().item()
        ) for name in MATERIALS
    }


def validate(ds, expected_mass_by_material):
    if ds.attrs.get("schema_version")!=1 or ds.attrs.get("voxel_volume_m3")!=1.:
        raise ValueError("Unknown voxel model version or capacity")
    if ds["outside_column_mass"].attrs.get("units")!="kg" or ds["roi_voxel_mass"].attrs.get("units")!="kg":
        raise ValueError("Mass unit mismatch")
    if ds["material_density"].attrs.get("units")!="kg m-3":
        raise ValueError("Density unit mismatch")
    if ds.coords["material"].values.tolist()!=list(MATERIALS):
        raise ValueError("Material identity mismatch")
    if ds.coords["roi_x"].values.tolist()!=list(range(X0,X1)) or ds.coords["roi_y"].values.tolist()!=list(range(Y0,Y1)):
        raise ValueError("ROI coordinate convention mismatch")
    mask=ds["region_is_volume"].values
    if not np.array_equal(mask,roi_mask()):
        raise ValueError("ROI mask diverged from declared ownership")
    outside=ds["outside_column_mass"].values
    voxel=ds["roi_voxel_mass"].values
    dens=ds["material_density"].values
    if not(np.isfinite(outside).all() and np.isfinite(voxel).all() and np.isfinite(dens).all()):
        raise ValueError("Nonfinite material/density")
    if np.any(outside<0) or np.any(voxel<0) or np.any(dens<=0):
        raise ValueError("Invalid material value")
    if np.any(outside[:,mask]!=0):
        raise ValueError("DOUBLE OWNERSHIP: outside mass present inside ROI")
    # Outside this microtest has ONLY uninterrupted A columns, so B is
    # prohibited outside; general mixtures require their own contract.
    if np.any(outside[1]!=0):
        raise ValueError("Outside B requires another geometric assumption")
    volume=np.sum(voxel/dens[:,None,None,None],axis=0)
    if np.any(volume>1.+1e-12):
        raise ValueError("Voxel capacity exceeded")
    observed=totals(ds)
    for mat in MATERIALS:
        if not np.isclose(observed[mat],expected_mass_by_material[mat],rtol=0,atol=1e-10):
            raise ValueError("Unaccounted material source/sink: "+mat)
    return observed


def derive_heights(ds):
    mask=ds["region_is_volume"].values
    stock=ds["outside_column_mass"].values
    density=ds["material_density"].values
    # Exterior is a solid continuous column, known base at z=0.
    outside_height=np.sum(stock/density[:,None,None],axis=0) * PITCH_M**-2
    h=np.asarray(outside_height,dtype=np.float64)
    voxel=ds["roi_voxel_mass"].values
    occupied=(np.sum(voxel/density[:,None,None,None],axis=0)>0)
    top=np.where(occupied,np.arange(Z)[:,None,None]+1,0).max(axis=0)*PITCH_M
    h[Y0:Y1,X0:X1]=top
    assert np.all(h>=0) and np.isfinite(h).all()
    return h


def landlab_preview(ds):
    g=RasterModelGrid((H+2,W+2),xy_spacing=PITCH_M)
    elev=g.add_zeros("topographic__elevation",at="node",units="m")
    h=derive_heights(ds)
    mapping={}
    for cell,node in enumerate(g.node_at_cell):
        x=int(round(g.x_of_node[node]))-1
        y=int(round(g.y_of_node[node]))-1
        assert 0<=x<W and 0<=y<H
        mapping[(x,y)]=int(node)
        elev[node]=h[y,x]
    assert len(mapping)==W*H
    return g,mapping


def check_cache(g,mapping,ds):
    target=derive_heights(ds)
    for (x,y),node in mapping.items():
        if g.at_node["topographic__elevation"][node]!=target[y,x]:
            raise ValueError("Landlab derived elevation cache stale at node")
    return True


def mass_hash(ds):
    a=ds["outside_column_mass"].values
    b=ds["roi_voxel_mass"].values
    return hashlib.sha256(a.tobytes()+b.tobytes()).hexdigest()


def main():
    state=make_state()
    initial=totals(state)
    assert initial["A"]==762. and initial["B"]==3.
    assert validate(state,initial)==initial
    g,index=landlab_preview(state)
    assert check_cache(g,index,state)
    initial_h=derive_heights(state).copy()
    assert np.all(initial_h[~roi_mask()]==2.)
    assert np.all(initial_h[roi_mask()]==6.)
    baseline_hash=mass_hash(state)

    # Prescribed EXTERNAL excavation, 16 full A voxels; not geomorphology.
    hollow=state.copy(deep=True)
    v=hollow["roi_voxel_mass"].values
    assert np.all(v[0,2:4,2:4,2:6]==2.)
    removed_a=float(np.sum(v[0,2:4,2:4,2:6]))
    assert removed_a==32.
    v[0,2:4,2:4,2:6]=0.
    excav_expected={"A":initial["A"]-removed_a,"B":initial["B"]}
    no_sink_rejected=False
    try:
        validate(hollow,initial)  # deliberately missing material outflow
    except ValueError:
        no_sink_rejected=True
    assert no_sink_rejected
    assert validate(hollow,excav_expected)==excav_expected
    assert np.array_equal(derive_heights(hollow),initial_h)
    assert (initial["A"]-totals(hollow)["A"])==removed_a

    # Publish candidate state as a new snapshot, not a solver-mutated field.
    state=hollow
    assert check_cache(g,index,state)
    after_excavation_hash=mass_hash(state)
    assert after_excavation_hash!=baseline_hash

    # Remove one A roof voxel and explicitly account its outgoing mass.
    top=state.copy(deep=True)
    roof=top["roi_voxel_mass"].values
    assert roof[0,5,3-Y0,5-X0]==2.
    removed_roof_a=float(roof[0,5,3-Y0,5-X0])
    roof[0,5,3-Y0,5-X0]=0.
    total_removed=removed_a+removed_roof_a
    final_expected={"A":initial["A"]-total_removed,"B":initial["B"]}
    assert validate(top,final_expected)==final_expected
    next_h=derive_heights(top)
    delta=initial_h-next_h
    assert delta[3,5]==1.0
    assert np.count_nonzero(delta)==1
    stale_cache_detected=False
    try:
        check_cache(g,index,top)
    except ValueError:
        stale_cache_detected=True
    assert stale_cache_detected
    # Refreshed from owner; no material duplicate.
    for (x,y),node in index.items():
        g.at_node["topographic__elevation"][node]=next_h[y,x]
    assert check_cache(g,index,top)

    # Deliberately corrupt the cache. Validator sees stale-derived view.
    g.at_node["topographic__elevation"][index[(5,3)]]+=.2
    malicious_cache_detected=False
    try:
        check_cache(g,index,top)
    except ValueError:
        malicious_cache_detected=True
    assert malicious_cache_detected
    assert totals(top)==final_expected
    g.at_node["topographic__elevation"][index[(5,3)]]=next_h[3,5]
    assert check_cache(g,index,top)

    # Explicit double ownership must be rejected.
    corrupted=top.copy(deep=True)
    corrupted["outside_column_mass"].values[0,3,5]=1.
    duplicate_rejected=False
    try:
        validate(corrupted,final_expected)
    except ValueError:
        duplicate_rejected=True
    assert duplicate_rejected
    assert validate(top,final_expected)==final_expected

    # Consistency on disk: only owner, NOT a second surface elevation stock.
    path=pathlib.Path("/tmp/e1_h5_partitioned_owner.nc")
    top.to_netcdf(path,engine="scipy")
    with xr.open_dataset(path,engine="scipy") as reopened:
        loaded=reopened.load()
    assert validate(loaded,final_expected)==final_expected
    assert np.array_equal(loaded["roi_voxel_mass"].values,top["roi_voxel_mass"].values)
    assert np.array_equal(loaded["outside_column_mass"].values,top["outside_column_mass"].values)
    assert np.array_equal(loaded["region_is_volume"].values,top["region_is_volume"].values)
    assert np.array_equal(derive_heights(loaded),next_h)
    new_g,new_index=landlab_preview(loaded)
    assert check_cache(new_g,new_index,loaded)
    assert mass_hash(loaded)==mass_hash(top)

    # Naive all-height-volume columns incorrectly fill entire cavity:
    # at 2kg/m3, exact 32kg A would be manufactured as phantom stock.
    false_mass_kg=16*2.
    assert false_mass_kg==removed_a
    report={
        "test":"E1 H5 partitioned surface and local volume, no new physics",
        "python":platform.python_version(),
        "landlab_version":landlab.__version__,
        "xarray_version":xr.__version__,
        "shape_xy":[H,W],
        "roi_xyz":[RX,RY,Z],
        "outside_columns":int(np.count_nonzero(~roi_mask())),
        "roi_columns":int(np.count_nonzero(roi_mask())),
        "inventory_initial_kg":initial,
        "cavity_manually_excavated_m3":16,
        "cavity_material_external_sink_kg":removed_a,
        "hidden_cavity_does_not_change_surface_heights":True,
        "missing_sink_rejected":no_sink_rejected,
        "roof_manually_removed_kg":removed_roof_a,
        "roof_surface_change_m":1.,
        "surface_columns_changed":int(np.count_nonzero(delta)),
        "stale_surface_cache_detected":stale_cache_detected,
        "surface_cache_tampering_detected":malicious_cache_detected,
        "double_owner_control_rejected":duplicate_rejected,
        "inventory_final_kg":final_expected,
        "global_material_conservation_with_sinks":True,
        "naive_filled_column_phantom_material_kg":false_mass_kg,
        "baseline_sha256":baseline_hash,
        "after_excavation_sha256":after_excavation_hash,
        "final_sha256":mass_hash(top),
        "netcdf_bytes":path.stat().st_size,
        "netcdf_reconstruction_exact":True,
        "landlab_height_is_derived_cache_only":True,
        "limitations":"Fixed rectangular ROI and 1m voxels, full homogeneous exterior columns. No motion, deformation, load-bearing test, expanding ROI, physics, thread safety or automatic synchronization with a Landlab solver."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
