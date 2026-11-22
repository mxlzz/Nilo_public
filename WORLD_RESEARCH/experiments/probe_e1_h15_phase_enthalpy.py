"""H15: phase-fraction transformation from one conserved material+energy owner.

Physics: NIST FiPy finite volumes, apparent heat capacity/enthalpy method.
Protocol preregistered in ETAPA_1_H15_PROTOCOLO_FASE_ENTALPIA.md.
The constitutive relation is a standard published equilibrium mushy-zone
approximation, not a new general-purpose solver.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import tempfile

import fipy
import numpy as np
import xarray as xr
from fipy import CellVariable, DiffusionTerm, Grid1D, TransientTerm

CELLS=8
DX_M=1.0
VOLUME_M3=1.0
MASS_CELL_KG=2.0
CP=500.0 # J/(kg K)
LATENT=50000.0 # J/kg; fictitious PCM
SOLIDUS_K=290.0
LIQUIDUS_K=310.0
K_ACTIVE=1000.0 # W/(m K)
DT_S=0.1
N_STEPS=100
MASS_TOTAL_KG=16.0
SCHEMA=1


def liquid_fraction(temp_K, latent):
    t=np.asarray(temp_K,dtype=np.float64)
    if latent==0.:
        # Thermal ablation D: no phase transition material.
        return np.zeros_like(t)
    return np.clip((t-SOLIDUS_K)/(LIQUIDUS_K-SOLIDUS_K),0.,1.)


def energy_from_temp(temp_K,latent):
    t=np.asarray(temp_K,dtype=np.float64)
    return MASS_CELL_KG*(CP*t+latent*liquid_fraction(t,latent))


def make_owner(latent=LATENT, uniform=False):
    start=np.full(CELLS,300.,dtype=np.float64) if uniform else np.array([306.]*4+[294.]*4)
    ds=xr.Dataset(
        data_vars={
            "material_mass_kg":(("cell",),np.full(CELLS,MASS_CELL_KG,dtype=np.float64),
                {"units":"kg", "role":"authoritative material inventory"}),
            "internal_energy_J":(("cell",),energy_from_temp(start,latent),
                {"units":"J", "role":"authoritative sensible+latent internal energy"}),
        },
        coords={"cell":np.arange(CELLS,dtype=np.int32)},
        attrs={
            "schema_version":SCHEMA,"material":"A",
            "cp_J_per_kg_K":CP,"latent_J_per_kg":float(latent),
            "solidus_K":SOLIDUS_K,"liquidus_K":LIQUIDUS_K,
            "cell_volume_m3":VOLUME_M3,"external_heat_J":0.0,
        },
    )
    validate(ds,latent,float(energy_from_temp(start,latent).sum()))
    return ds


def state_sha(ds):
    h=hashlib.sha256()
    for key in ("material_mass_kg","internal_energy_J"):
        h.update(ds[key].values.tobytes())
        h.update(key.encode())
        h.update(ds[key].attrs["units"].encode())
    h.update(ds.coords["cell"].values.tobytes())
    h.update(json.dumps({k: (v.item() if isinstance(v, np.generic) else v) for k, v in ds.attrs.items()}, sort_keys=True).encode())
    return h.hexdigest()


def validate(ds, expected_latent, expected_total_energy):
    if set(ds.data_vars)!={"material_mass_kg","internal_energy_J"}:
        raise ValueError("Duplicated or missing canonical state field")
    if ds.sizes.get("cell")!=CELLS or ds.coords["cell"].values.tolist()!=list(range(CELLS)):
        raise ValueError("Cell ID/shape changed")
    if any(ds[k].dims!=("cell",) for k in ds.data_vars):
        raise ValueError("Invalid material field topology")
    if ds.attrs.get("schema_version")!=SCHEMA or ds.attrs.get("material")!="A":
        raise ValueError("Wrong material/schema")
    if ds["material_mass_kg"].attrs.get("units")!="kg" or ds["internal_energy_J"].attrs.get("units")!="J":
        raise ValueError("Wrong physical units")
    if (
        ds.attrs.get("cp_J_per_kg_K")!=CP
        or ds.attrs.get("latent_J_per_kg")!=expected_latent
        or ds.attrs.get("solidus_K")!=SOLIDUS_K
        or ds.attrs.get("liquidus_K")!=LIQUIDUS_K
        or ds.attrs.get("cell_volume_m3")!=VOLUME_M3
        or ds.attrs.get("external_heat_J")!=0.
    ):
        raise ValueError("Changed constitutive data or unexpected external heat")
    m,e=ds["material_mass_kg"].values,ds["internal_energy_J"].values
    if not (np.isfinite(m).all() and np.isfinite(e).all() and np.all(m>0) and np.all(e>=0)):
        raise ValueError("Nonphysical mass/energy")
    if not np.array_equal(m,np.full(CELLS,MASS_CELL_KG,dtype=np.float64)):
        raise ValueError("Material created or lost inside closed cell")
    error=float(e.sum()-expected_total_energy)
    if abs(error)>0.02:
        raise ValueError("No-flux energy balance violated: "+str(error))
    return error


def derived_temperature(ds):
    # This explicit inverse is valid ONLY when every cell remains in the
    # mushy interval, and is guarded before publishing each next state.
    m=ds["material_mass_kg"].values
    h=ds["internal_energy_J"].values/m
    latent=ds.attrs["latent_J_per_kg"]
    c_eff=CP+latent/(LIQUIDUS_K-SOLIDUS_K)
    T=(h + latent*SOLIDUS_K/(LIQUIDUS_K-SOLIDUS_K))/c_eff
    if not (np.isfinite(T).all() and np.all(T>SOLIDUS_K) and np.all(T<LIQUIDUS_K)):
        raise ValueError("Out of validated linear transition interval; no clipping")
    return T


def phases(ds):
    temp=derived_temperature(ds)
    fraction=liquid_fraction(temp,ds.attrs["latent_J_per_kg"])
    m=ds["material_mass_kg"].values
    ml=m*fraction
    ms=m-ml
    if np.max(np.abs(ml+ms-m))>1e-12 or np.any(ml<0) or np.any(ms<0):
        raise ValueError("Phase components do not partition matter")
    # Not persisted: all derived from *same* canonical mass and energy.
    return {"T_K":temp,"liquid_fraction":fraction,"liquid_mass_kg":ml,"solid_mass_kg":ms}


def solve_case(k,latent=LATENT,uniform=False):
    owner=make_owner(latent,uniform)
    total_E=float(owner["internal_energy_J"].sum())
    input_sha=state_sha(owner)
    before=phases(owner)
    mesh=Grid1D(nx=CELLS,dx=DX_M)
    var=CellVariable(mesh=mesh,name="temporary derived temperature_K",
                     value=before["T_K"].copy())
    apparent_cp=CP+latent/(LIQUIDUS_K-SOLIDUS_K)
    rho_cp=MASS_CELL_KG/VOLUME_M3*apparent_cp
    equation=TransientTerm(coeff=rho_cp)==DiffusionTerm(coeff=float(k))
    peak_balance=0.
    for step in range(N_STEPS):
        var.setValue(derived_temperature(owner))
        equation.solve(var=var,dt=DT_S)
        t=np.array(var.value,dtype=np.float64)
        if not (np.isfinite(t).all() and np.all(t>SOLIDUS_K) and np.all(t<LIQUIDUS_K)):
            raise ValueError(f"Step {step}: temperature escaped linear interval")
        next_owner=owner.copy(deep=True)
        next_owner["internal_energy_J"].values[:]=energy_from_temp(t,latent)
        err=validate(next_owner,latent,total_E)
        if not np.array_equal(next_owner["material_mass_kg"].values,owner["material_mass_kg"].values):
            raise AssertionError("Material created")
        peak_balance=max(peak_balance,abs(err))
        owner=next_owner
    after=phases(owner)
    return {
        "owner":owner,"before":before,"after":after,
        "start_sha":input_sha,"end_sha":state_sha(owner),
        "total_mass_kg":float(owner["material_mass_kg"].sum()),
        "initial_energy_J":total_E,
        "final_energy_J":float(owner["internal_energy_J"].sum()),
        "peak_energy_balance_abs_J":peak_balance,
        "final_energy_error_J":float(owner["internal_energy_J"].sum()-total_E),
        "interface_delta_T_K":float(after["T_K"][3]-after["T_K"][4]),
        "hot_interface_T_initial_K":float(before["T_K"][3]),
        "hot_interface_T_final_K":float(after["T_K"][3]),
        "cold_interface_T_initial_K":float(before["T_K"][4]),
        "cold_interface_T_final_K":float(after["T_K"][4]),
        "hot_liquid_fraction_initial":float(before["liquid_fraction"][3]),
        "hot_liquid_fraction_final":float(after["liquid_fraction"][3]),
        "cold_liquid_fraction_initial":float(before["liquid_fraction"][4]),
        "cold_liquid_fraction_final":float(after["liquid_fraction"][4]),
        "liquid_mass_total_initial_kg":float(before["liquid_mass_kg"].sum()),
        "liquid_mass_total_final_kg":float(after["liquid_mass_kg"].sum()),
        "initial_thermal_contrast_K":float(np.ptp(before["T_K"])),
        "final_thermal_contrast_K":float(np.ptp(after["T_K"])),
    }


def invalid_candidates(ds,total):
    digest=state_sha(ds)
    latent=ds.attrs["latent_J_per_kg"]
    passed={}
    def reject(label,mutate):
        candidate=ds.copy(deep=True)
        mutate(candidate)
        try:
            validate(candidate,latent,total)
        except ValueError:
            passed[label]=True
        else:
            raise AssertionError("Invalid material candidate accepted: "+label)
        assert state_sha(ds)==digest
    reject("plus_1J_without_source",lambda x:x["internal_energy_J"].values.__setitem__(2,x["internal_energy_J"].values[2]+1.))
    reject("negative_energy",lambda x:x["internal_energy_J"].values.__setitem__(0,-1.))
    reject("negative_mass",lambda x:x["material_mass_kg"].values.__setitem__(0,-1.))
    reject("wrong_energy_unit",lambda x:x["internal_energy_J"].attrs.__setitem__("units","kJ"))
    reject("changed_latent_heat",lambda x:x.attrs.__setitem__("latent_J_per_kg",latent+1.))
    reject("changed_solidus",lambda x:x.attrs.__setitem__("solidus_K",SOLIDUS_K-1.))
    reject("duplicate_phase_stock",lambda x:x.__setitem__("liquid_fraction",xr.DataArray(np.ones(CELLS),dims=("cell",))))
    return passed


def main():
    a=solve_case(K_ACTIVE,LATENT)
    b=solve_case(0.,LATENT)
    c=solve_case(K_ACTIVE,LATENT,uniform=True)
    d=solve_case(K_ACTIVE,0.)
    replay=solve_case(K_ACTIVE,LATENT)
    bad=[]
    def require(label,okay):
        if not okay: bad.append(label)
    # Mass and phase partition in same owner
    require("total_mass",all(v["total_mass_kg"]==MASS_TOTAL_KG for v in (a,b,c,d,replay)))
    require("phase_partition",all(np.max(np.abs(x["after"]["liquid_mass_kg"]+
                                               x["after"]["solid_mass_kg"]-x["owner"]["material_mass_kg"].values))<1e-12
                                  for x in (a,b,c,replay)))
    require("hot_liquid_fraction_drops",a["hot_liquid_fraction_initial"]-a["hot_liquid_fraction_final"]>0.01)
    require("cold_liquid_fraction_rises",a["cold_liquid_fraction_final"]-a["cold_liquid_fraction_initial"]>0.01)
    require("temperature_flows_down_gradient",a["hot_interface_T_final_K"]<a["hot_interface_T_initial_K"]
            and a["cold_interface_T_final_K"]>a["cold_interface_T_initial_K"])
    require("no_k_no_change",np.max(np.abs(b["owner"]["internal_energy_J"].values-
                                            make_owner(LATENT)["internal_energy_J"].values))<1e-7
            and np.max(np.abs(b["after"]["T_K"]-b["before"]["T_K"]))<1e-12
            and np.max(np.abs(b["after"]["liquid_fraction"]-b["before"]["liquid_fraction"]))<1e-12)
    require("no_gradient_no_change",np.max(np.abs(c["owner"]["internal_energy_J"].values-
                                                make_owner(LATENT,uniform=True)["internal_energy_J"].values))<1e-7
            and np.max(np.abs(c["after"]["liquid_fraction"]-c["before"]["liquid_fraction"]))<1e-12)
    require("latent_reduces_diffusion",d["interface_delta_T_K"]<0.8*a["interface_delta_T_K"])
    require("exact_replay",np.array_equal(a["owner"]["internal_energy_J"].values,
                                            replay["owner"]["internal_energy_J"].values))
    require("all_in_linear_interval",all(np.all((v["after"]["T_K"]>SOLIDUS_K)&(v["after"]["T_K"]<LIQUIDUS_K))
                                          for v in (a,b,c,d,replay)))
    require("mass_conserved_per_cell",all(np.array_equal(v["owner"]["material_mass_kg"].values,
                                                      make_owner(0. if v is d else LATENT)["material_mass_kg"].values)
                                          for v in (a,b,d,replay)))
    require("energy_preserved",all(v["peak_energy_balance_abs_J"]<0.02 for v in (a,b,c,d,replay)))
    rejected=invalid_candidates(a["owner"],a["initial_energy_J"])
    with tempfile.TemporaryDirectory(prefix="world_h15_") as td:
        p=pathlib.Path(td)/"phase_owner.nc"
        a["owner"].to_netcdf(p,engine="scipy")
        with xr.open_dataset(p,engine="scipy") as f:
            restored=f.load()
        validate(restored,LATENT,a["initial_energy_J"])
        require("exact_owner_snapshot",state_sha(restored)==state_sha(a["owner"])
                and np.array_equal(derived_temperature(restored),a["after"]["T_K"])
                and np.array_equal(phases(restored)["liquid_fraction"],a["after"]["liquid_fraction"]))
        sz=p.stat().st_size
    def out(s):
        return {k:v for k,v in s.items() if k not in ("owner","before","after")}
    report={
      "experiment":"E1 H15 energy-driven reversible phase fraction in one material owner",
      "fipy_version":fipy.__version__,"numpy_version":np.__version__,
      "xarray_version":xr.__version__,"python":platform.python_version(),
      "temperature_interval_K":[SOLIDUS_K,LIQUIDUS_K],
      "latent_heat_J_per_kg":LATENT,"cp_J_per_kg_K":CP,
      "conductivity_W_per_m_K":K_ACTIVE,"steps":N_STEPS,"dt_s":DT_S,
      "active":out(a),"no_conduction":out(b),"uniform_temperature":out(c),
      "no_latent_heat":out(d),"replay_exact":True,
      "rejected_invalid_states":rejected,"netcdf_bytes":sz,
      "preregistered_gates_failed":bad,
      "limitations":"All material fixed in 1D and within mushy zone: equilibrium fraction only, not freezing front, phase flow, volume change, mechanical coupling, or 3D heterogeneous world.",
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if bad:
        raise AssertionError("H15 preregistered physical gates failed: "+", ".join(bad))


if __name__=="__main__":
    main()
