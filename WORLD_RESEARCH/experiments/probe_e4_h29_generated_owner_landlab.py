"""E4 H29: adopt generated raw WorldEngine heights as valid Landlab initial conditions.

The earlier bridge silently treated cell-center values as node vertices and
used arbitrary vertical units. Here nodes 1..16/1..32 represent sample centers
explicitly (origin -50m), halo nodes are non-material boundaries, vertical
units are explicitly *nominal meters*. Landlab native physics is unchanged.
Pre-registered ETAPA_4_H29_PROTOCOLO_SEMILLAS_TERRITORIO.md.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import platform
import sys
import tempfile

import landlab
import numpy as np
import xarray as xr
from landlab import RasterModelGrid
from landlab.components import PriorityFloodFlowRouter, SpaceLargeScaleEroder

WORLD_SEEDS=(7321,8128)
SHAPE=(18,34)
SOURCE_SHAPE=(16,32)
DX=100.
AREA=DX**2
RHO=1200.
SOIL_DEPTH=.15
STEPS=6
DT=.2
K_ACTIVE=.10
MASS0=16*32*AREA*RHO*SOIL_DEPTH
GRID_ORIGIN_OFFSET_M=-50.

def digest(arr):
    return hashlib.sha256(np.ascontiguousarray(arr,dtype="<f8").tobytes()).hexdigest()

def normal_attr(v):
    if isinstance(v,np.generic):return v.item()
    return v

def owner_sha(ds):
    h=hashlib.sha256()
    for name in ("soil_mass_kg","bedrock_elevation_m","is_core_node"):
        a=ds[name]
        h.update(name.encode())
        h.update(a.values.tobytes())
        h.update(str(a.attrs.get("units","1")).encode())
    h.update(json.dumps({k:normal_attr(v) for k,v in ds.attrs.items()},
                        sort_keys=True).encode())
    h.update(ds.coords["y"].values.tobytes())
    h.update(ds.coords["x"].values.tobytes())
    return h.hexdigest()

def normalize(raw):
    low=float(raw.min())
    high=float(raw.max())
    if not np.isfinite([low,high]).all() or high<=low:
        raise ValueError("Flat or invalid source height")
    return 50.*(raw-low)/(high-low)

def create(raw,seed,expected_hash):
    if raw.shape!=SOURCE_SHAPE or not np.isfinite(raw).all():
        raise ValueError("Invalid world source")
    if digest(raw)!=expected_hash:
        raise ValueError("WorldEngine source hash mismatch")
    core_height=normalize(raw)
    if not np.isclose(float(core_height.min()),0.,atol=1e-12) or not np.isclose(float(core_height.max()),50.,atol=1e-12):
        raise AssertionError("Nominal elevation mapping invalid")
    bedrock=np.pad(core_height,1,mode="edge")
    mask=np.zeros(SHAPE,dtype=np.int8)
    mask[1:-1,1:-1]=1
    mass=np.where(mask.astype(bool),AREA*RHO*SOIL_DEPTH,0.).astype(np.float64)
    ds=xr.Dataset({
        "soil_mass_kg":(("y","x"),mass,{"units":"kg","role":"sole mobile soil inventory"}),
        "bedrock_elevation_m":(("y","x"),bedrock,{"units":"m_nominal","role":"immobile terrain geometry"}),
        "is_core_node":(("y","x"),mask,{"units":"1","role":"physical WorldEngine sample nodes"}),
    },coords={"y":np.arange(SHAPE[0],dtype=np.int32),
              "x":np.arange(SHAPE[1],dtype=np.int32)},
    attrs={
        "schema_version":1,"source_generator":"WorldEngine",
        "source_seed":int(seed),"source_hash_sha256":str(expected_hash),
        "source_units":"arbitrary",
        "nominal_elevation_range_m":50.,
        "normalization":"50*(raw-min)/(max-min)",
        "landlab_x_y_offset_m":GRID_ORIGIN_OFFSET_M,
        "core_sample_alignment":"core node (1,1) corresponds to WorldEngine sample center (50m,50m)",
        "horizontal_spacing_m":DX,"cell_area_m2":AREA,
        "density_kg_m3":RHO,"original_soil_kg":MASS0,
        "exported_soil_kg":0.,
        "soil_material":"A",
    })
    validate(ds,raw,expected_hash,seed)
    return ds

def geom(ds):
    return ds["bedrock_elevation_m"].values+ds["soil_mass_kg"].values/(RHO*AREA)

def validate(ds,raw,expected_hash,seed):
    if set(ds.data_vars)!={"soil_mass_kg","bedrock_elevation_m","is_core_node"}:
        raise ValueError("Unknown duplicated or missing stock")
    if any(ds[v].dims!=("y","x") or ds[v].shape!=SHAPE for v in ds.data_vars):
        raise ValueError("Wrong world topology")
    if list(ds.coords["x"].values)!=list(range(SHAPE[1])) or list(ds.coords["y"].values)!=list(range(SHAPE[0])):
        raise ValueError("Invalid world coords")
    if (ds["soil_mass_kg"].attrs.get("units")!="kg"
        or ds["bedrock_elevation_m"].attrs.get("units")!="m_nominal"
        or ds["is_core_node"].attrs.get("units")!="1"):
        raise ValueError("Invalid physical units")
    attrs=ds.attrs
    reference={
        "schema_version":1,"source_generator":"WorldEngine",
        "source_seed":seed,"source_hash_sha256":expected_hash,
        "source_units":"arbitrary","nominal_elevation_range_m":50.,
        "normalization":"50*(raw-min)/(max-min)",
        "landlab_x_y_offset_m":GRID_ORIGIN_OFFSET_M,
        "core_sample_alignment":"core node (1,1) corresponds to WorldEngine sample center (50m,50m)",
        "horizontal_spacing_m":DX,"cell_area_m2":AREA,"density_kg_m3":RHO,
        "original_soil_kg":MASS0,"soil_material":"A",
    }
    if any(attrs.get(k)!=v for k,v in reference.items()) or set(attrs)!=set(reference)|{"exported_soil_kg"}:
        raise ValueError("Source, material, geometry or constants changed")
    mask=ds["is_core_node"].values
    expected=np.zeros(SHAPE,dtype=np.int8);expected[1:-1,1:-1]=1
    if not np.array_equal(mask,expected):
        raise ValueError("Impossible material mask")
    z=ds["bedrock_elevation_m"].values
    expected_z=np.pad(normalize(raw),1,mode="edge")
    if not np.array_equal(z,expected_z):
        raise ValueError("World height changed after mapping or halo inconsistent")
    soil=ds["soil_mass_kg"].values
    if not np.isfinite(soil).all() or np.any(soil<0.) or np.any(soil[mask==0]!=0.):
        raise ValueError("Invalid mobile soil")
    exported=float(attrs["exported_soil_kg"])
    if not np.isfinite(exported) or exported<0.:
        raise ValueError("Invalid external soil export")
    discrepancy=float(soil.sum()+exported-MASS0)
    tolerance=max(1e-4,1e-8*MASS0)
    if abs(discrepancy)>tolerance:
        raise ValueError("Mass budget mismatch "+str(discrepancy))
    return {"remaining_kg":float(soil.sum()),"exported_kg":exported,
            "mass_residual_kg":discrepancy,"mass_tolerance_kg":tolerance}

def outlet_from_edge(surface):
    nrows,ncols=surface.shape
    border=np.zeros_like(surface,dtype=bool)
    border[0,:]=True;border[-1,:]=True;border[:,0]=True;border[:,-1]=True
    ids=np.flatnonzero(border.ravel())
    outlet=int(ids[np.argmin(surface.ravel()[ids])])
    return outlet

def setup_scene(owner,k):
    grid=RasterModelGrid(SHAPE,xy_spacing=DX)
    bedrock=owner["bedrock_elevation_m"].values.ravel().copy()
    depth=(owner["soil_mass_kg"].values/(RHO*AREA)).ravel().copy()
    top=bedrock+depth
    grid.at_node["bedrock__elevation"]=bedrock
    grid.at_node["soil__depth"]=depth
    grid.at_node["topographic__elevation"]=top
    grid.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,left_is_closed=True,
        right_is_closed=True,top_is_closed=True)
    outlet=outlet_from_edge(top.reshape(SHAPE))
    grid.set_watershed_boundary_condition_outlet_id(
        outlet,grid.at_node["topographic__elevation"],-9999.)
    router=PriorityFloodFlowRouter(grid,flow_metric="D8",suppress_out=True)
    eroder=SpaceLargeScaleEroder(grid,K_sed=k,K_br=0.,
         F_f=0.,phi=0.,H_star=1.,v_s=3.,m_sp=.5,n_sp=1.,
         sp_crit_sed=0,sp_crit_br=0)
    return grid,router,eroder,outlet

def execute(raw,seed,hash_source,k):
    owner=create(raw,seed,hash_source)
    grid,flow,eroder,outlet=setup_scene(owner,k)
    original=owner["soil_mass_kg"].values.copy()
    original_terrain=geom(owner).copy()
    peak_res=0.
    for _ in range(STEPS):
        depth=owner["soil_mass_kg"].values.ravel()/(RHO*AREA)
        np.copyto(grid.at_node["soil__depth"],depth)
        np.copyto(grid.at_node["topographic__elevation"],
                  geom(owner).ravel())
        flow.run_one_step()
        suspended,bedload=eroder.run_one_step(DT)
        if not np.isfinite([suspended,bedload]).all() or suspended<0 or bedload<0:
            raise ValueError("Invalid native Landlab sediment flux")
        newdepth=grid.at_node["soil__depth"].reshape(SHAPE)
        if not np.isfinite(newdepth).all() or np.any(newdepth<0):
            raise ValueError("Landlab published negative soil depth")
        candidate=owner.copy(deep=True)
        candidate["soil_mass_kg"].values[:]=newdepth*RHO*AREA
        candidate.attrs["exported_soil_kg"]=float(owner.attrs["exported_soil_kg"])+(float(suspended)+float(bedload))*RHO
        result=validate(candidate,raw,hash_source,seed)
        peak_res=max(peak_res,abs(result["mass_residual_kg"]))
        owner=candidate
    current=validate(owner,raw,hash_source,seed)
    gained=int(np.count_nonzero(owner["soil_mass_kg"].values>original+1e-6))
    changed=int(np.count_nonzero(np.abs(owner["soil_mass_kg"].values-original)>1e-6))
    return {
        "owner":owner,"source_seed":seed,"source_sha256":hash_source,
        "outlet_node":outlet,"outlet_initial_height_m_nominal":float(
            np.pad(normalize(raw),1,mode="edge").ravel()[outlet]),
        "mass_initial_kg":MASS0,"mass_final_kg":current["remaining_kg"],
        "export_kg":current["exported_kg"],"peak_abs_balance_error_kg":peak_res,
        "changed_core_nodes":changed,"net_gain_nodes":gained,
        "max_abs_terrain_change_m_nominal":float(np.max(np.abs(geom(owner)-original_terrain))),
        "final_state_sha256":owner_sha(owner),
    }

def negative_candidates(ds,raw,seed,sha_source):
    key=owner_sha(ds);bad={}
    def reject(label,mutate):
        candidate=ds.copy(deep=True)
        mutate(candidate)
        try:validate(candidate,raw,sha_source,seed)
        except ValueError:bad[label]=True
        else:raise AssertionError("Invalid E4 owner accepted: "+label)
        if owner_sha(ds)!=key:raise AssertionError("Original changed on rejected candidate")
    reject("unaccounted_1kg",lambda x:x["soil_mass_kg"].values.__setitem__((2,2),x["soil_mass_kg"].values[2,2]+1.))
    reject("negative_soil",lambda x:x["soil_mass_kg"].values.__setitem__((2,2),-1.))
    reject("boundary_soil",lambda x:x["soil_mass_kg"].values.__setitem__((0,2),1.))
    reject("kg_to_g",lambda x:x["soil_mass_kg"].attrs.__setitem__("units","g"))
    reject("wrong_seed",lambda x:x.attrs.__setitem__("source_seed",999))
    reject("wrong_source_hash",lambda x:x.attrs.__setitem__("source_hash_sha256","tampered"))
    reject("extra_height_stock",lambda x:x.__setitem__("topographic__elevation",xr.DataArray(np.ones(SHAPE),dims=("y","x"))))
    reject("negative_export",lambda x:x.attrs.__setitem__("exported_soil_kg",-1.))
    return bad

def main(input_file):
    with np.load(input_file,allow_pickle=False) as data:
        raw_a=np.asarray(data["elevation_seed_7321"],dtype="<f8").copy()
        raw_b=np.asarray(data["elevation_seed_8128"],dtype="<f8").copy()
        expected=[str(z) for z in data["source_sha256"]]
        seeds=[int(z) for z in data["generator_seeds"]]
        global_rng=int(data["global_numpy_seed"][0])
        revision=str(data["worldengine_revision"][0])
        raw_unit=str(data["native_height_units"][0])
    failures=[]
    def gate(name,ok):
        if not ok:failures.append(name)
    gate("producer_metadata",seeds==[7321,8128] and global_rng==1234
         and revision=="3b9113ecfad884cab4b32081d138a15e6262ada8"
         and raw_unit=="arbitrary")
    gate("producer_raw_hash_exact",digest(raw_a)==expected[0] and digest(raw_b)==expected[1])
    gate("different_source_maps",np.count_nonzero(np.abs(raw_a-raw_b)>1e-8)>=.1*raw_a.size)
    aa=execute(raw_a,7321,expected[0],K_ACTIVE)
    bb=execute(raw_b,8128,expected[1],K_ACTIVE)
    inactive=execute(raw_a,7321,expected[0],0.)
    replay=execute(raw_a,7321,expected[0],K_ACTIVE)
    gate("both_terrains_movable",aa["changed_core_nodes"]>0
         and bb["changed_core_nodes"]>0
         and aa["max_abs_terrain_change_m_nominal"]>0
         and bb["max_abs_terrain_change_m_nominal"]>0)
    gate("both_mass_ledgers",aa["peak_abs_balance_error_kg"]<=9.216
         and bb["peak_abs_balance_error_kg"]<=9.216)
    gate("zero_erodibility_inert",inactive["changed_core_nodes"]==0
         and inactive["export_kg"]==0.)
    gate("exact_replay",np.array_equal(aa["owner"]["soil_mass_kg"].values,
                                     replay["owner"]["soil_mass_kg"].values)
         and aa["export_kg"]==replay["export_kg"]
         and aa["final_state_sha256"]==replay["final_state_sha256"])
    invalid=negative_candidates(aa["owner"],raw_a,7321,expected[0])
    with tempfile.TemporaryDirectory(prefix="world_h29_") as td:
        path=pathlib.Path(td)/"generated_territory_owner.nc"
        aa["owner"].to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as fd:
            restored=fd.load()
        validate(restored,raw_a,expected[0],7321)
        gate("owner_checkpoint_exact",owner_sha(restored)==aa["final_state_sha256"]
             and np.array_equal(geom(restored),geom(aa["owner"])))
        snapshot_bytes=path.stat().st_size
    def pub(case):
        return {key:value for key,value in case.items() if key!="owner"}
    report={
        "experiment":"E4 H29 generated territory owner compatible with Landlab native sediment dynamics",
        "producer_upstream_SHA":revision,"native_height_units":"arbitrary",
        "normalized_elevation_units":"m_nominal, arbitrary 0..50 scale",
        "grid_shape":SHAPE,"generator_shape":SOURCE_SHAPE,
        "spacing_m_nominal":DX,"offset_m":GRID_ORIGIN_OFFSET_M,
        "material_A_mass_initial_kg":MASS0,"model_steps":STEPS,
        "python":platform.python_version(),"numpy":np.__version__,
        "landlab":landlab.__version__,"xarray":xr.__version__,
        "seed_7321_active":pub(aa),"seed_8128_active":pub(bb),
        "seed_7321_no_erodibility":pub(inactive),
        "negative_owner_states":invalid,"replay_exact":True,
        "checkpoint_bytes":snapshot_bytes,
        "failed_preregistered_gates":failures,
        "limitations":"WorldEngine raw heights converted to arbitrary nominal meters without geophysical calibration; 2.5D Landlab nodal soil and one outlet on low boundary, no world-volume caves, no Bullet/thermal coupling."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if failures:
        raise AssertionError("H29 original gates failed: "+", ".join(failures))

if __name__=="__main__":
    main(sys.argv[1])
