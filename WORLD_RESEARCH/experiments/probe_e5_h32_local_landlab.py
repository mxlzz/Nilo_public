"""E5 H32 stage 1 Python3.13: native local K_sed intervention.

Upstream Landlab SPACE accepts a nodewise K_sed array. We choose one
3x3 erodibility patch from INITIAL D8 flow (before any treatment data),
run both branches, record receiver chains, and write one canonical owner
NetCDF for each scene. H32 protocol preregistered before this code.
"""
from __future__ import annotations

import json
import pathlib
import platform
import sys

import landlab
import numpy as np
import xarray as xr
from landlab import RasterModelGrid
from landlab.components import PriorityFloodFlowRouter, SpaceLargeScaleEroder

import probe_e4_h29_generated_owner_landlab as e4
import probe_e5_h31_owner_contract as c
import probe_e5_h32_local_contract as local

def is_core_node(node):
    y,x=divmod(int(node),c.SHAPE[1])
    return 1<=y<=16 and 1<=x<=32

def path_core(receiver,starting):
    out=[]
    current=int(starting)
    seen={current}
    for _ in range(len(receiver)):
        nxt=int(receiver[current])
        if nxt==current or nxt in seen:
            break
        seen.add(nxt)
        if is_core_node(nxt):
            out.append(nxt)
        current=nxt
    return out

def initial_flow_and_target(raw,seed):
    base=e4.create(raw,seed,c.SOURCES[seed])
    # The native routing condition is derived ONLY from initial geometry.
    grid,router,eroder,outlet=e4.setup_scene(base,c.K_ACTIVE)
    router.run_one_step()
    receiver=np.asarray(grid.at_node["flow__receiver_node"],dtype=np.int64).copy()
    area=np.asarray(grid.at_node["drainage_area"],dtype=np.float64).copy()
    if receiver.shape!=(np.prod(c.SHAPE),) or not np.isfinite(area).all():
        raise ValueError("Native D8 routing returned invalid receiver/drainage field")
    candidates=[]
    for y in range(2,16):
        for x in range(2,32):
            node=y*c.SHAPE[1]+x
            path=path_core(receiver,node)
            target_cells=local.target_patch_coords((y,x))
            beyond=[nid for nid in path
                    if divmod(int(nid),c.SHAPE[1]) not in target_cells]
            if len(path)>=4 and beyond:
                candidates.append((-float(area[node]),int(node),y,x))
    if not candidates:
        raise ValueError("No source with a >=4-core-node downstream drainage path")
    _,nid,y,x=min(candidates)
    patch=local.target_patch_coords((y,x))
    outgoing=set()
    for sy,sx in patch:
        node=sy*c.SHAPE[1]+sx
        outgoing.update(
            j for j in path_core(receiver,node)
            if divmod(int(j),c.SHAPE[1]) not in patch)
    if not outgoing:
        raise ValueError("Selected patch has no downstream core recipients")
    return {
        "target":[int(y),int(x)],
        "target_node_id":nid,
        "target_drainage_area":float(area[nid]),
        "outlet_node":int(outlet),
        "receivers_sha256":local.receiver_hash(receiver),
        "source_path_core":path_core(receiver,nid),
        "downstream_nodes_outside_patch":sorted(int(z) for z in outgoing),
    }

def scene(owner):
    kfield=owner[local.LOCAL_FIELD].values
    grid=RasterModelGrid(c.SHAPE,xy_spacing=c.DX)
    base=local.original_projection(owner)
    bedrock=base["bedrock_elevation_m"].values.ravel().copy()
    soil=(base["soil_mass_kg"].values/(c.RHO*c.AREA)).ravel().copy()
    grid.at_node["bedrock__elevation"]=bedrock
    grid.at_node["soil__depth"]=soil
    grid.at_node["topographic__elevation"]=bedrock+soil
    grid.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,left_is_closed=True,
        right_is_closed=True,top_is_closed=True)
    outlet=e4.outlet_from_edge(c.topography(base))
    grid.set_watershed_boundary_condition_outlet_id(
        outlet,grid.at_node["topographic__elevation"],-9999.)
    flow=PriorityFloodFlowRouter(grid,flow_metric="D8",suppress_out=True)
    space=SpaceLargeScaleEroder(
        grid,K_sed=kfield.ravel().copy(),
        K_br=0.,F_f=0.,phi=0.,H_star=1.,v_s=3.,
        m_sp=.5,n_sp=1.,sp_crit_sed=0,sp_crit_br=0)
    return grid,flow,space,int(outlet)

def native_run(raw,seed,selection,mode):
    index=tuple(selection["target"])
    source_sha=c.SOURCES[seed]
    base=c.augment(e4.create(raw,seed,source_sha),seed,source_sha,c.K_ACTIVE)
    owner=local.make(base,index,mode,selection["receivers_sha256"])
    local.validate(owner,raw,seed,index,mode,selection["receivers_sha256"])
    initially=owner["soil_mass_kg"].values.copy()
    grid,router,solver,outlet=scene(owner)
    max_error=0.
    for step in range(1,c.TIMESTEPS+1):
        np.copyto(grid.at_node["soil__depth"],
                  owner["soil_mass_kg"].values.ravel()/(c.RHO*c.AREA))
        np.copyto(grid.at_node["topographic__elevation"],
                  local.derived_terrain(owner).ravel())
        router.run_one_step()
        suspended,bedload=solver.run_one_step(c.LANDLAB_DT)
        if (not np.isfinite([suspended,bedload]).all() or
            suspended<0. or bedload<0.):
            raise ValueError("Invalid native Landlab SPACE sediment flux")
        depth=grid.at_node["soil__depth"].reshape(c.SHAPE)
        if not np.isfinite(depth).all() or np.any(depth<0.):
            raise ValueError("Native SPACE produced invalid soil depth")
        candidate=owner.copy(deep=True)
        candidate["soil_mass_kg"].values[:]=depth*c.RHO*c.AREA
        candidate.attrs["exported_soil_kg"]=(
            float(owner.attrs["exported_soil_kg"])+
            (float(suspended)+float(bedload))*c.RHO)
        candidate.attrs["landlab_step"]=step
        candidate.attrs["landlab_t_bench"]=step*c.LANDLAB_DT
        check=local.validate(candidate,raw,seed,index,mode,
                             selection["receivers_sha256"])
        max_error=max(max_error,abs(check["mass_residual_kg"]))
        if (not np.array_equal(candidate["body_mass_kg"].values,
                               owner["body_mass_kg"].values) or
            candidate.attrs["body_status"]!="reservoir"):
            raise ValueError("Landlab altered fixed source body")
        owner=candidate
    return {
        "owner":owner,"seed":seed,"mode":mode,
        "sha256":local.hash_owner(owner),
        "outlet_node":outlet,
        "soil_remaining_kg":float(owner["soil_mass_kg"].sum()),
        "exported_soil_kg":float(owner.attrs["exported_soil_kg"]),
        "maximum_closed_mass_error_kg":max_error,
        "total_material_plus_export_kg":float(
            owner["soil_mass_kg"].sum()+owner.attrs["exported_soil_kg"]+c.BODY_MASS),
        "changed_soil_nodes":int(np.count_nonzero(np.abs(
            owner["soil_mass_kg"].values-initially)>1e-6)),
    }

def choose_downstream_patch(before,after,local_patch,downstream):
    eligible=[]
    local_coords=local.target_patch_coords(tuple(local_patch))
    downstream_ids=set(int(z) for z in downstream)
    for y in range(1,16):
        for x in range(1,32):
            cells={(y,x),(y,x+1),(y+1,x),(y+1,x+1)}
            if cells&local_coords:
                continue
            node_ids={i*c.SHAPE[1]+j for i,j in cells}
            if not node_ids&downstream_ids:
                continue
            b=before[y:y+2,x:x+2]
            a=after[y:y+2,x:x+2]
            change=float(.6*(a[0,0]-b[0,0])+
                         .1*(a[0,1]-b[0,1])+
                         .3*(a[1,1]-b[1,1]))
            eligible.append((-abs(change),y,x,change))
    if not eligible:
        raise ValueError("No pure downstream patch outside perturbed K region")
    _,y,x,delta=min(eligible)
    return [y,x],delta,len(eligible)

def main(npz,outdir):
    target=pathlib.Path(outdir);target.mkdir(parents=True,exist_ok=True)
    with np.load(npz,allow_pickle=False) as fd:
        raw={
            7321:np.asarray(fd["elevation_seed_7321"],dtype="<f8").copy(),
            8128:np.asarray(fd["elevation_seed_8128"],dtype="<f8").copy()
        }
        revision=str(fd["worldengine_revision"][0])
        hashes=[str(h) for h in fd["source_sha256"]]
    if (revision!=c.SOURCE_REVISION or
        hashes!=[c.SOURCES[7321],c.SOURCES[8128]] or
        any(c.sha_raw(raw[s])!=c.SOURCES[s] for s in raw)):
        raise ValueError("WorldEngine source of H32 differs from preregistered H29")
    metrics={}
    failures=[]
    def gate(name,cond):
        if not cond:failures.append(name)
    for seed in raw:
        selection=initial_flow_and_target(raw[seed],seed)
        cases={}
        for mode in ("control","local_off"):
            run=native_run(raw[seed],seed,selection,mode)
            outfile=target/f"{seed}_{mode}.nc"
            run["owner"].to_netcdf(outfile,engine="scipy")
            with xr.open_dataset(outfile,engine="scipy") as f:loaded=f.load()
            local.validate(loaded,raw[seed],seed,tuple(selection["target"]),
                           mode,selection["receivers_sha256"])
            if local.hash_owner(loaded)!=run["sha256"]:
                raise ValueError("H32 owner lost exact K/mass/pose/flow provenance")
            info={k:v for k,v in run.items() if k!="owner"}
            info["checkpoint"]=outfile.name
            info["checkpoint_bytes"]=outfile.stat().st_size
            cases[mode]=(run,info)
        control=cases["control"][0]["owner"]
        altered=cases["local_off"][0]["owner"]
        diff=altered["soil_mass_kg"].values-control["soil_mass_kg"].values
        node_delta=diff.ravel()[selection["downstream_nodes_outside_patch"]]
        idx,z_delta,candidates=choose_downstream_patch(
            local.derived_terrain(control),local.derived_terrain(altered),
            selection["target"],selection["downstream_nodes_outside_patch"])
        seedspec={
            "initial_flow_selection":selection,
            "runs":{k:info for k,(_,info) in cases.items()},
            "max_abs_downstream_material_delta_kg":float(np.max(np.abs(node_delta))),
            "number_downstream_nodes_abs_delta_gt100kg":int(
                np.count_nonzero(np.abs(node_delta)>=100.)),
            "downstream_patch_index":idx,
            "downstream_patch_delta_z_m_nominal":float(z_delta),
            "downstream_eligible_patches":candidates,
            "overall_changed_nodes_between_scenarios":int(
                np.count_nonzero(np.abs(diff)>1e-6)),
            "global_mass_difference_in_soil_kg":float(diff.sum()),
            "export_difference_kg":float(altered.attrs["exported_soil_kg"]-
                                         control.attrs["exported_soil_kg"]),
        }
        metrics[str(seed)]=seedspec
        gate(f"{seed}_local_K_exact_9_nodes",np.count_nonzero(
             altered[local.LOCAL_FIELD].values!=control[local.LOCAL_FIELD].values)==9)
        gate(f"{seed}_downstream_material_response",
             seedspec["max_abs_downstream_material_delta_kg"]>=100.)
        gate(f"{seed}_downstream_surface_response",abs(z_delta)>.003)
        gate(f"{seed}_mass_closes",
             all(cases[m][1]["maximum_closed_mass_error_kg"]<=.09216
                 for m in cases))
        gate(f"{seed}_total_soil_export_equal_from_same_source",
             abs(seedspec["global_mass_difference_in_soil_kg"]+
                 seedspec["export_difference_kg"])<=.09216)
    selection=metrics["7321"]["initial_flow_selection"]
    replay=native_run(raw[7321],7321,selection,"local_off")
    gate("seed7321_intervention_replay",replay["sha256"]==
         metrics["7321"]["runs"]["local_off"]["sha256"])
    manifest={
        "experiment":"E5 H32 nodewise native Landlab erodibility intervention",
        "python":platform.python_version(),"landlab":landlab.__version__,
        "numpy":np.__version__,"xarray":xr.__version__,
        "source_SHA":revision,"source_raw_hashes":hashes,
        "model_clocks":{"Landlab_steps":c.TIMESTEPS,"Landlab_dt_benchmark":c.LANDLAB_DT},
        "seeds":metrics,"replay_exact":True,
        "failed_preregistered_gates":failures,
        "limitations":"Local K_sed patch is an imposed experiment, not emergent erosion chemistry. Flow path labels are from initial D8 routing, and solver can reroute sediment. No rigid feedback, nominal geometry or globally synchronized clock."
    }
    (target/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("WORLD_EVAL_JSON "+json.dumps(manifest,sort_keys=True),flush=True)
    if failures:raise AssertionError("H32 local Landlab gates failed: "+", ".join(failures))

if __name__=="__main__":
    main(sys.argv[1],sys.argv[2])
