"""H32 source/owner validation for a spatial Landlab erodibility intervention.

The native solver is still Landlab. This file ONLY extends the H31
canonical xarray state with a spatial K_sed parameter and its provenance;
material and body budgets are validated by the *same* H31 contract.
Python 3.13 native Landlab and Python 3.11 Bullet import this pure module.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import xarray as xr

import probe_e5_h31_owner_contract as c

LOCAL_FIELD="erodibility_K_sed_at_node"
EXTRA_KEYS={
    "scenario_local_mode","erodibility_target_y","erodibility_target_x",
    "erodibility_patch_radius","flow_receivers_sha256",
}

def original_projection(owner):
    """A view of identical canonical matter, without the K field metadata."""
    view=owner.drop_vars(LOCAL_FIELD).copy(deep=False)
    view.attrs={k:v for k,v in owner.attrs.items() if k not in EXTRA_KEYS}
    return view

def target_patch_coords(index):
    y,x=index
    if not (2<=y<=15 and 2<=x<=31):
        raise ValueError("Local intervention cannot cross core boundary")
    return {(i,j) for i in range(y-1,y+2) for j in range(x-1,x+2)}

def k_map(index,mode):
    if mode not in ("control","local_off"):
        raise ValueError("Unknown local K trial")
    values=np.full(c.SHAPE,c.K_ACTIVE,dtype=np.float64)
    if mode=="local_off":
        y,x=index
        target_patch_coords(index)
        values[y-1:y+2,x-1:x+2]=0.
    return values

def make(base,index,mode,receiver_sha):
    if set(base.data_vars)!=c.FIELDS_ALL:
        raise ValueError("H32 requires exact H31 material+body owner")
    target_patch_coords(index)
    result=base.copy(deep=True)
    result[LOCAL_FIELD]=xr.DataArray(
        k_map(index,mode),dims=("y","x"),
        attrs={"units":"K_sed_benchmark","role":"local native SPACE erodibility parameter, not material stock"})
    result.attrs.update({
        "scenario_local_mode":str(mode),
        "erodibility_target_y":int(index[0]),
        "erodibility_target_x":int(index[1]),
        "erodibility_patch_radius":1,
        "flow_receivers_sha256":str(receiver_sha),
    })
    return result

def validate(owner,raw,seed,index,mode,receiver_sha):
    if set(owner.data_vars)!=c.FIELDS_ALL|{LOCAL_FIELD}:
        raise ValueError("Missing or duplicated H32 world field")
    if owner[LOCAL_FIELD].dims!=("y","x") or owner[LOCAL_FIELD].shape!=c.SHAPE:
        raise ValueError("Invalid spatial K shape")
    if owner[LOCAL_FIELD].attrs.get("units")!="K_sed_benchmark":
        raise ValueError("K erodibility parameter units changed")
    if not np.array_equal(owner[LOCAL_FIELD].values,k_map(index,mode)):
        raise ValueError("Erodibility altered outside preregistered local patch")
    expected={
        "scenario_local_mode":mode,
        "erodibility_target_y":int(index[0]),
        "erodibility_target_x":int(index[1]),
        "erodibility_patch_radius":1,
        "flow_receivers_sha256":str(receiver_sha),
    }
    if any(owner.attrs.get(k)!=v for k,v in expected.items()):
        raise ValueError("Local target/provenance tampered")
    # This projection shares SAME matter arrays but excludes K metadata only
    # for calling the audited H31 material budget invariant validator.
    result=c.validate(original_projection(owner),raw,seed,c.K_ACTIVE)
    return result

def hash_owner(owner):
    original=c.hash_owner(original_projection(owner))
    h=hashlib.sha256(original.encode())
    h.update(owner[LOCAL_FIELD].values.tobytes())
    h.update(owner[LOCAL_FIELD].attrs["units"].encode())
    h.update(json.dumps({k:owner.attrs[k] for k in sorted(EXTRA_KEYS)},
                        sort_keys=True).encode())
    return h.hexdigest()

def receiver_hash(receivers):
    return hashlib.sha256(np.ascontiguousarray(
        receivers,dtype="<i8").tobytes()).hexdigest()

def derived_terrain(owner):
    return c.topography(original_projection(owner))
