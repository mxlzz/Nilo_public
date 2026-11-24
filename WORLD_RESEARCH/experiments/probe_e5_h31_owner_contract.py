"""E5 H31 common xarray material-and-body state contract for TWO Python runtimes.

No physical solver here. Python 3.13 Landlab and Python 3.11 Bullet read/write
the SAME logical owner through exact validated NetCDF checkpoints. Protocol
includes H31.0 runtime split, recorded before these two-stage scripts.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import xarray as xr

SHAPE=(18,34)
SOURCE_SHAPE=(16,32)
DX=100.
AREA=10000.
RHO=1200.
MASS0=921600000.
BODY_MASS=2.
BODY_RADIUS=.5
TIMESTEPS=6
LANDLAB_DT=.2
BULLET_DT=1./240.
BULLET_STEPS=720
K_ACTIVE=.1
SOURCES={
    7321:"495e97c24477e68e0cffcab8f485481630d4425d31a01442c7ad1cbb0daa170d",
    8128:"d03e423f93b3c26ac097fba54e303c6322131f0b7fec0afb21d15e4c52e40781",
}
SOURCE_REVISION="3b9113ecfad884cab4b32081d138a15e6262ada8"
FIELDS_SOIL={"soil_mass_kg","bedrock_elevation_m","is_core_node"}
FIELDS_BODY={"body_mass_kg","body_position_m_nominal",
             "body_velocity_m_nominal_per_s","body_orientation_xyzw",
             "body_angular_velocity_rad_s"}
FIELDS_ALL=FIELDS_SOIL|FIELDS_BODY

def sha_raw(raw):
    return hashlib.sha256(
        np.ascontiguousarray(raw,dtype="<f8").tobytes()).hexdigest()

def nominal(raw):
    if raw.shape!=SOURCE_SHAPE or not np.isfinite(raw).all():
        raise ValueError("Invalid original WorldEngine array")
    delta=float(np.ptp(raw))
    if delta<=0.:
        raise ValueError("Flat invalid height source")
    return 50.*(raw-float(raw.min()))/delta

def baseline_attrs(seed,sha):
    return {
        "schema_version":1,
        "source_generator":"WorldEngine",
        "source_seed":int(seed),
        "source_hash_sha256":str(sha),
        "source_units":"arbitrary",
        "nominal_elevation_range_m":50.,
        "normalization":"50*(raw-min)/(max-min)",
        "landlab_x_y_offset_m":-50.,
        "core_sample_alignment":"core node (1,1) corresponds to WorldEngine sample center (50m,50m)",
        "horizontal_spacing_m":DX,
        "cell_area_m2":AREA,
        "density_kg_m3":RHO,
        "original_soil_kg":MASS0,
        "soil_material":"A",
    }

def extra_attrs(k):
    return {
        "body_status":"reservoir",
        "body_release_count":0,
        "body_source_mass_kg":BODY_MASS,
        "body_radius_m_nominal":BODY_RADIUS,
        "scenario_K_sed":float(k),
        "landlab_step":0,
        "landlab_t_bench":0.,
        "bullet_t_s":0.,
        "patch_y":-1,
        "patch_x":-1,
    }

def augment(base,seed,sha,k):
    """Add body already in reservoir at t0; no physical position yet."""
    owner=base.copy(deep=True)
    owner["body_mass_kg"]=xr.DataArray(
        np.array([BODY_MASS]),dims=("body",),attrs={"units":"kg"})
    owner["body_position_m_nominal"]=xr.DataArray(
        np.array([[0.,0.,0.]]),dims=("body","axis"),
        attrs={"units":"m_nominal"})
    owner["body_velocity_m_nominal_per_s"]=xr.DataArray(
        np.zeros((1,3)),dims=("body","axis"),
        attrs={"units":"m_nominal/s"})
    owner["body_orientation_xyzw"]=xr.DataArray(
        np.array([[0.,0.,0.,1.]]),dims=("body","quat"),
        attrs={"units":"1"})
    owner["body_angular_velocity_rad_s"]=xr.DataArray(
        np.zeros((1,3)),dims=("body","axis"),
        attrs={"units":"rad/s"})
    owner=owner.assign_coords({
        "body":np.array([0],dtype=np.int32),
        "axis":np.array(["x","y","z"]),
        "quat":np.array(["x","y","z","w"]),
    })
    owner.attrs.update(extra_attrs(k))
    return owner

def topography(owner):
    return (owner["bedrock_elevation_m"].values+
            owner["soil_mass_kg"].values/(RHO*AREA))

def soil_only(owner):
    allowed=(set(baseline_attrs(int(owner.attrs["source_seed"]),
                                owner.attrs["source_hash_sha256"])) |
             {"exported_soil_kg"})
    view=owner[list(FIELDS_SOIL)].copy(deep=False)
    # assign_attrs() merges extra body attrs; replace the attribute dictionary
    # so the H29 native solver sees ONLY its strict soil contract.
    view.attrs={k:v for k,v in owner.attrs.items() if k in allowed}
    return view

def validate(owner,raw,seed,k,*,max_step=TIMESTEPS):
    if seed not in SOURCES:
        raise ValueError("Unregistered WorldEngine seed")
    if sha_raw(raw)!=SOURCES[seed]:
        raise ValueError("Raw source hash invalid")
    if set(owner.data_vars)!=FIELDS_ALL:
        raise ValueError("Material or body stock missing/duplicated")
    for f in FIELDS_SOIL:
        if owner[f].dims!=("y","x") or owner[f].shape!=SHAPE:
            raise ValueError("Invalid terrain topology")
    if owner.coords["x"].values.tolist()!=list(range(SHAPE[1])) or owner.coords["y"].values.tolist()!=list(range(SHAPE[0])):
        raise ValueError("Wrong terrain indices")
    if (owner["soil_mass_kg"].attrs.get("units")!="kg" or
        owner["bedrock_elevation_m"].attrs.get("units")!="m_nominal" or
        owner["is_core_node"].attrs.get("units")!="1"):
        raise ValueError("Invalid terrain physical units")
    expected=np.pad(nominal(raw),1,mode="edge")
    if not np.array_equal(owner["bedrock_elevation_m"].values,expected):
        raise ValueError("Source height or geometry mutated")
    mask=np.zeros(SHAPE,dtype=np.int8)
    mask[1:-1,1:-1]=1
    if not np.array_equal(owner["is_core_node"].values,mask):
        raise ValueError("Invalid terrain core/halo property")
    for f,dimensions,unit in (
        ("body_mass_kg",("body",),"kg"),
        ("body_position_m_nominal",("body","axis"),"m_nominal"),
        ("body_velocity_m_nominal_per_s",("body","axis"),"m_nominal/s"),
        ("body_orientation_xyzw",("body","quat"),"1"),
        ("body_angular_velocity_rad_s",("body","axis"),"rad/s")
    ):
        if owner[f].dims!=dimensions or owner[f].attrs.get("units")!=unit:
            raise ValueError("Invalid body stock topology or units "+f)
    if owner.coords["body"].values.tolist()!=[0] or owner.coords["axis"].values.tolist()!=["x","y","z"] or owner.coords["quat"].values.tolist()!=["x","y","z","w"]:
        raise ValueError("Wrong rigid body identity/axis")
    if any(owner.attrs.get(a)!=v for a,v in baseline_attrs(seed,SOURCES[seed]).items()):
        raise ValueError("Source terrain attributes corrupted")
    static=extra_attrs(k)
    for attr in ("body_source_mass_kg","body_radius_m_nominal","scenario_K_sed"):
        if owner.attrs.get(attr)!=static[attr]:
            raise ValueError("Body source/fixed parameter changed")
    attrs_allowed=(set(baseline_attrs(seed,SOURCES[seed])) | set(static) | {"exported_soil_kg"})
    if set(owner.attrs)!=attrs_allowed:
        raise ValueError("Unrecognized owner attribute")
    step=owner.attrs.get("landlab_step")
    if not isinstance(max_step,int) or max_step<0:
        raise ValueError("Invalid declared soil horizon")
    if step not in range(max_step+1) or owner.attrs.get("landlab_t_bench")!=step*LANDLAB_DT:
        raise ValueError("Invalid Landlab progress")
    if owner.attrs.get("bullet_t_s") not in (0.,BULLET_STEPS*BULLET_DT):
        raise ValueError("Invalid Bullet time")
    status=owner.attrs.get("body_status")
    if (status,owner.attrs.get("body_release_count")) not in (("reservoir",0),("released",1)):
        raise ValueError("Illegal body release state")
    iy,ix=owner.attrs.get("patch_y"),owner.attrs.get("patch_x")
    pos=owner["body_position_m_nominal"].values
    vel=owner["body_velocity_m_nominal_per_s"].values
    spin=owner["body_angular_velocity_rad_s"].values
    q=owner["body_orientation_xyzw"].values
    if status=="reservoir":
        if (iy,ix)!=(-1,-1) or not np.array_equal(pos,[[0.,0.,0.]]):
            raise ValueError("Material in reservoir cannot have live pose")
        if owner.attrs["bullet_t_s"]!=0.:
            raise ValueError("Bullet time without actor release")
    elif not (1<=iy<=15 and 1<=ix<=31):
        raise ValueError("Invalid released body patch")
    if (not np.array_equal(owner["body_mass_kg"].values,[BODY_MASS]) or
        not all(np.isfinite(x).all() for x in (pos,vel,spin,q)) or
        abs(np.linalg.norm(q[0])-1.)>1e-4):
        raise ValueError("Body mass, motion or orientation invalid")
    m=owner["soil_mass_kg"].values
    outgoing=float(owner.attrs.get("exported_soil_kg",np.nan))
    if not np.isfinite(m).all() or np.any(m<0.) or np.any(m[mask==0]!=0.) or not np.isfinite(outgoing) or outgoing<0.:
        raise ValueError("Invalid soil/flow")
    residual=float(m.sum()+outgoing+BODY_MASS-(MASS0+BODY_MASS))
    tolerance=max(1e-4,1e-10*MASS0)
    if abs(residual)>tolerance:
        raise ValueError("Closed joint material budget failed: "+str(residual))
    return {"soil_remaining_kg":float(m.sum()),"export_kg":outgoing,
            "body_kg":BODY_MASS,"mass_residual_kg":residual,
            "mass_tolerance_kg":tolerance}

def normal(v):
    if isinstance(v,np.generic):
        return v.item()
    return v

def hash_owner(ds):
    h=hashlib.sha256()
    for key in sorted(FIELDS_ALL):
        field=ds[key]
        h.update(key.encode()+field.values.tobytes()+
                 field.attrs.get("units","").encode())
    h.update(json.dumps(
        {key:normal(v) for key,v in ds.attrs.items()},sort_keys=True
    ).encode())
    for coord in ("y","x","body","axis","quat"):
        h.update(repr(ds.coords[coord].values.tolist()).encode())
    return h.hexdigest()

def select_patch(before,after):
    """Maximum absolute *derived* interpolated relief change on core nodes."""
    candidate=[]
    for y in range(1,16):
        for x in range(1,32):
            a=before[y:y+2,x:x+2]
            b=after[y:y+2,x:x+2]
            za=.6*a[0,0]+.1*a[0,1]+.3*a[1,1]
            zb=.6*b[0,0]+.1*b[0,1]+.3*b[1,1]
            delta=float(zb-za)
            candidate.append((-abs(delta),y,x,delta))
    _,y,x,delta=min(candidate)
    return (y,x),delta
