"""H14 conserved heat exchange: the physical PDE is solved by NIST FiPy.

Preregistered protocol: ETAPA_1_H14_PROTOCOLO_ENERGIA_FIPY.md.
No finite-difference/finite-volume engine is written here.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import platform
import tempfile

import numpy as np
import xarray as xr
import fipy
from fipy import Grid1D, CellVariable, TransientTerm, DiffusionTerm

NX=8
CELL_VOLUME_M3=1.0
DX_M=1.0
MASS_KG=2.0
CP_J_PER_KG_K=500.0
RHOCP_J_PER_M3_K=1000.0
CONDUCTIVITY_W_PER_M_K=20.0
STEPS=100
DT_S=0.1
INITIAL_E_J=2_400_000.0


def make_owner(uniform=False):
    temp=np.full(NX,300.,dtype=np.float64) if uniform else np.array([330.]*4+[270.]*4,dtype=np.float64)
    masses=np.full(NX,MASS_KG,dtype=np.float64)
    energy=temp*masses*CP_J_PER_KG_K
    state=xr.Dataset(
        data_vars={
            "material_mass_kg":(("cell",),masses,{"units":"kg", "role":"canonical_mass_owner"}),
            "internal_thermal_energy_J":(("cell",),energy,{"units":"J","role":"canonical_heat_owner"}),
        },
        coords={"cell":np.arange(NX,dtype=np.int32)},
        attrs={
            "schema_version":1,
            "cp_J_per_kg_K":CP_J_PER_KG_K,
            "cell_volume_m3":CELL_VOLUME_M3,
            "external_energy_flow_J":0.0,
            "note":"temperature is derived, no duplicated temperature inventory",
        }
    )
    validate(state)
    return state


def hash_owner(ds):
    return hashlib.sha256(
        ds["material_mass_kg"].values.tobytes()+
        ds["internal_thermal_energy_J"].values.tobytes()
    ).hexdigest()


def validate(ds):
    if set(ds.data_vars)!={"material_mass_kg","internal_thermal_energy_J"}:
        raise ValueError("Unexpected duplicated inventory variable")
    if any(tuple(ds[k].dims)!=("cell",) for k in ds.data_vars):
        raise ValueError("Invalid material tensor dimension")
    if ds.sizes.get("cell")!=NX or ds.coords["cell"].values.tolist()!=list(range(NX)):
        raise ValueError("Invalid material cell coordinates")
    if ds["material_mass_kg"].attrs.get("units")!="kg" or ds["internal_thermal_energy_J"].attrs.get("units")!="J":
        raise ValueError("Unsupported inventory units")
    if ds.attrs.get("schema_version")!=1 or ds.attrs.get("cp_J_per_kg_K")!=CP_J_PER_KG_K or ds.attrs.get("cell_volume_m3")!=CELL_VOLUME_M3:
        raise ValueError("Material heat-capacity/schema changed")
    if ds.attrs.get("external_energy_flow_J")!=0.0:
        raise ValueError("Unexpected energy exchange outside closed system")
    m=ds["material_mass_kg"].values
    e=ds["internal_thermal_energy_J"].values
    if not np.isfinite(m).all() or not np.isfinite(e).all() or np.any(m<=0) or np.any(e<0):
        raise ValueError("Invalid nonfinite or negative state")
    if not np.array_equal(m,np.full(NX,MASS_KG,dtype=np.float64)) or m.sum()!=16.0:
        raise ValueError("Unaccounted material variation")
    total=float(e.sum())
    residual=total-INITIAL_E_J
    if abs(residual)>0.01:
        raise ValueError(f"Thermal energy creation/loss {residual} J exceeds preregistered tolerance")
    return {"mass_kg":float(m.sum()),"energy_J":total,"balance_residual_J":residual}


def derive_temp(ds):
    return ds["internal_thermal_energy_J"].values/(ds["material_mass_kg"].values*CP_J_PER_KG_K)


def run_case(k,uniform=False):
    owner=make_owner(uniform=uniform)
    initial=derive_temp(owner).copy()
    grid=Grid1D(nx=NX,dx=DX_M)
    temperature=CellVariable(mesh=grid,value=initial.copy(),name="derived_temperature_K")
    eq=TransientTerm(coeff=RHOCP_J_PER_M3_K)==DiffusionTerm(coeff=float(k))
    baseline_mass=owner["material_mass_kg"].values.copy()
    max_resid=0.
    for _ in range(STEPS):
        # Copy values from sole material owner; FiPy state is a temporary computational view.
        temperature.setValue(derive_temp(owner))
        eq.solve(var=temperature,dt=DT_S)
        next_t=np.asarray(temperature.value,dtype=np.float64)
        if not np.isfinite(next_t).all() or np.any(next_t<0):
            raise ValueError("Invalid physical temperature from FiPy")
        candidate=owner.copy(deep=True)
        candidate["internal_thermal_energy_J"].values[:]=next_t*baseline_mass*CP_J_PER_KG_K
        ledger=validate(candidate) # rejects unaccounted energy before publication
        owner=candidate
        max_resid=max(max_resid,abs(ledger["balance_residual_J"]))
    after=derive_temp(owner)
    assert np.array_equal(baseline_mass,owner["material_mass_kg"].values)
    return {"owner":owner,"initial_temp_K":initial,"final_temp_K":after.copy(),
            "max_energy_balance_abs_J":max_resid,
            "final_energy_J":float(owner["internal_thermal_energy_J"].sum().item()),
            "energy_residual_J":float(owner["internal_thermal_energy_J"].sum().item()-INITIAL_E_J),
            "temperature_contrast_initial_K":float(initial.max()-initial.min()),
            "temperature_contrast_final_K":float(after.max()-after.min()),
            "initial_interface_hot_K":float(initial[3]),
            "initial_interface_cold_K":float(initial[4]),
            "final_interface_hot_K":float(after[3]),
            "final_interface_cold_K":float(after[4])}


def negative_cases(ds):
    sha=hash_owner(ds)
    flags={}
    def test(label,patch):
        b=ds.copy(deep=True)
        patch(b)
        try:
            validate(b)
        except ValueError:
            flags[label]=True
        else:
            raise AssertionError("Invalid thermal owner accepted: "+label)
        if hash_owner(ds)!=sha:
            raise AssertionError("Rejected mutation changed good owner")
    test("energy_appeared",lambda d: d["internal_thermal_energy_J"].values.__setitem__(3,d["internal_thermal_energy_J"].values[3]+1.0))
    test("negative_energy",lambda d: d["internal_thermal_energy_J"].values.__setitem__(2,-1.))
    test("negative_mass",lambda d: d["material_mass_kg"].values.__setitem__(2,-1.))
    test("wrong_energy_units",lambda d: d["internal_thermal_energy_J"].attrs.__setitem__("units","kJ"))
    test("changed_cp",lambda d: d.attrs.__setitem__("cp_J_per_kg_K",CP_J_PER_KG_K+1))
    return flags


def main():
    active=run_case(CONDUCTIVITY_W_PER_M_K,uniform=False)
    zero_k=run_case(0.,uniform=False)
    uniform=run_case(CONDUCTIVITY_W_PER_M_K,uniform=True)
    replay=run_case(CONDUCTIVITY_W_PER_M_K,uniform=False)
    assert active["initial_interface_hot_K"]-active["final_interface_hot_K"]>0.1
    assert active["final_interface_cold_K"]-active["initial_interface_cold_K"]>0.1
    assert active["temperature_contrast_final_K"]<active["temperature_contrast_initial_K"]
    assert np.all(active["final_temp_K"]>=270.) and np.all(active["final_temp_K"]<=330.)
    assert np.max(np.abs(zero_k["owner"]["internal_thermal_energy_J"].values-
                         make_owner()["internal_thermal_energy_J"].values))<1e-7
    assert np.max(np.abs(uniform["owner"]["internal_thermal_energy_J"].values-
                         make_owner(uniform=True)["internal_thermal_energy_J"].values))<1e-7
    assert np.array_equal(active["owner"]["internal_thermal_energy_J"].values,
                          replay["owner"]["internal_thermal_energy_J"].values)
    rejected=negative_cases(active["owner"])
    with tempfile.TemporaryDirectory(prefix="world_h14_") as td:
        f=pathlib.Path(td)/"heat_material_owner.nc"
        active["owner"].to_netcdf(f,engine="scipy")
        with xr.open_dataset(f,engine="scipy") as opened:
            loaded=opened.load()
        assert validate(loaded)
        assert hash_owner(loaded)==hash_owner(active["owner"])
        assert np.array_equal(loaded["internal_thermal_energy_J"].values,active["owner"]["internal_thermal_energy_J"].values)
        assert np.array_equal(derive_temp(loaded),active["final_temp_K"])
        assert "temperature_K" not in loaded and "temperature" not in loaded
        filesize=f.stat().st_size
    def p(d):
        return {k:v for k,v in d.items() if k not in ("owner","initial_temp_K","final_temp_K")}
    report={
        "experiment":"E1 H14 native FiPy conservative heat conduction with sole xarray thermal energy owner",
        "fipy":fipy.__version__,"python":platform.python_version(),"numpy":np.__version__,"xarray":xr.__version__,
        "nx":NX,"dt_s":DT_S,"steps":STEPS,
        "mass_initial_final_kg":16.0,"thermal_energy_initial_J":INITIAL_E_J,
        "thermal_conductivity_W_per_m_K":CONDUCTIVITY_W_PER_M_K,
        "cp_J_per_kg_K":CP_J_PER_KG_K,
        "active":p(active),"zero_conductivity":p(zero_k),"uniform_temperature":p(uniform),
        "replay_exact":True,"negative_owner_rejections":rejected,
        "netcdf_bytes":filesize,"netcdf_owner_exact":True,
        "final_sha256":hash_owner(active["owner"]),
        "limitations":"1D fixed abstract material, closed no-flux, constant cp and k, no advection, frictional heat, phase change, radiation or 3D matter coupling."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
