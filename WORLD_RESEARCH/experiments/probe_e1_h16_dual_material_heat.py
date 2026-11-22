"""H16: one material-energy inventory for A/B + physical thermal response.

Preregistered E1 H16 protocol (before this code). NIST FiPy solves
the finite-volume PDE; here we only adapt a published phase enthalpy law.
Not a world engine or constitutive physics implementation.
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

MATERIALS=("A","B")
N=8
MASS_PER_CELL=2.
CELL_VOLUME=1.
RHO={"A":2.,"B":2.}
CP={"A":500.,"B":1000.}
LATENT_A=50000.
TS=290.
TL=310.
K=1000.
STEPS=100
DT=0.1


def as_normal(x):
    if isinstance(x,np.generic):
        return x.item()
    return x


def state_hash(ds):
    h=hashlib.sha256()
    for key in ("material_mass_kg","internal_energy_J"):
        a=ds[key]
        h.update(key.encode())
        h.update(a.values.tobytes())
        h.update(a.attrs["units"].encode())
    h.update(json.dumps({
        "materials":[str(m) for m in ds.coords["material"].values.tolist()],
        "cells":[int(v) for v in ds.coords["cell"].values.tolist()],
        "attrs":{k:as_normal(v) for k,v in ds.attrs.items()},
    },sort_keys=True).encode())
    return h.hexdigest()


def expected_temp(uniform=False):
    return np.full(N,300.,dtype=np.float64) if uniform else np.array([306.]*4+[294.]*4,dtype=np.float64)


def active_index(mass):
    m=np.asarray(mass)
    if m.shape!=(2,N) or not np.isfinite(m).all() or np.any(m<0):
        raise ValueError("Invalid species dimension/mass")
    count=(m>0).sum(axis=0)
    if not np.all(count==1):
        raise ValueError("Exactly one phase-capable or inert material per cell in H16")
    return np.argmax(m,axis=0)


def phase_A_liquid_fraction(t,active):
    fraction=np.zeros(N,dtype=np.float64)
    idx=active==0
    if idx.any():
        if not (np.all(t[idx]>TS) and np.all(t[idx]<TL)):
            raise ValueError("A temperature escaped preregistered mushy band")
        fraction[idx]=(t[idx]-TS)/(TL-TS)
    return fraction


def energy_for_temp(t,mass):
    active=active_index(mass)
    fraction=phase_A_liquid_fraction(np.asarray(t),active)
    e=np.zeros((2,N),dtype=np.float64)
    for i in range(N):
        mat=MATERIALS[int(active[i])]
        m=mass[int(active[i]),i]
        L=LATENT_A if mat=="A" else 0.
        e[int(active[i]),i]=m*(CP[mat]*float(t[i])+L*float(fraction[i]))
    return e


def starting_material(composition):
    m=np.zeros((2,N),dtype=np.float64)
    if composition=="AB":
        m[0,:4]=MASS_PER_CELL
        m[1,4:]=MASS_PER_CELL
    elif composition=="BB":
        m[1,:]=MASS_PER_CELL
    else:
        raise ValueError("Unregistered composition")
    return m


def make_owner(composition,uniform=False):
    mass=starting_material(composition)
    energy=energy_for_temp(expected_temp(uniform),mass)
    ds=xr.Dataset(
        {
            "material_mass_kg":(("material","cell"),mass,{"units":"kg", "role":"single matter owner"}),
            "internal_energy_J":(("material","cell"),energy,{"units":"J","role":"single sensible-plus-latent energy owner"})
        },
        coords={"material":np.array(MATERIALS,dtype="U1"),"cell":np.arange(N,dtype=np.int32)},
        attrs={
            "schema_version":1,
            "rho_A_kg_m3":RHO["A"],"rho_B_kg_m3":RHO["B"],
            "cp_A_J_kgK":CP["A"],"cp_B_J_kgK":CP["B"],
            "latent_A_J_kg":LATENT_A,
            "solidus_A_K":TS,"liquidus_A_K":TL,
            "cell_volume_m3":CELL_VOLUME,"external_mass_kg":0.,"external_energy_J":0.,
        }
    )
    validate(ds,mass,float(energy.sum()))
    return ds


def validate(ds,expected_mass,initial_energy):
    if set(ds.data_vars)!={"material_mass_kg","internal_energy_J"}:
        raise ValueError("Extra or missing material/energy stock")
    if ds["material_mass_kg"].dims!=("material","cell") or ds["internal_energy_J"].dims!=("material","cell"):
        raise ValueError("Wrong dimensions")
    if [str(v) for v in ds.coords["material"].values.tolist()]!=list(MATERIALS):
        raise ValueError("Material identity changed")
    if [int(v) for v in ds.coords["cell"].values.tolist()]!=list(range(N)):
        raise ValueError("Cell identity changed")
    if ds["material_mass_kg"].attrs.get("units")!="kg" or ds["internal_energy_J"].attrs.get("units")!="J":
        raise ValueError("Unexpected units")
    expected_attrs={
        "schema_version":1,
        "rho_A_kg_m3":RHO["A"],"rho_B_kg_m3":RHO["B"],
        "cp_A_J_kgK":CP["A"],"cp_B_J_kgK":CP["B"],
        "latent_A_J_kg":LATENT_A,"solidus_A_K":TS,"liquidus_A_K":TL,
        "cell_volume_m3":CELL_VOLUME,"external_mass_kg":0.,"external_energy_J":0.,
    }
    if dict(ds.attrs)!=expected_attrs:
        raise ValueError("Constitutive parameter, geometry, schema or external ledger changed")
    m=ds["material_mass_kg"].values
    e=ds["internal_energy_J"].values
    if not (np.isfinite(m).all() and np.isfinite(e).all() and
            np.all(m>=0) and np.all(e>=0)):
        raise ValueError("Negative/nonfinite material or energy")
    if not np.array_equal(m,expected_mass) or float(m.sum())!=16.:
        raise ValueError("Material composition, total mass or per-cell material changed")
    a=active_index(m)
    v=m[0]/RHO["A"]+m[1]/RHO["B"]
    if not np.allclose(v,np.full(N,CELL_VOLUME),rtol=0,atol=1e-12):
        raise ValueError("Overcapacity or loss of occupied volume")
    if np.any(e[m==0.]!=0.):
        raise ValueError("Energy assigned to nonexistent matter")
    err=float(e.sum()-initial_energy)
    if abs(err)>=0.02:
        raise ValueError("Energy ledger imbalance: "+str(err))
    return err


def derive(ds):
    m=ds["material_mass_kg"].values
    e=ds["internal_energy_J"].values
    ai=active_index(m)
    t=np.empty(N,dtype=np.float64)
    for i in range(N):
        j=int(ai[i])
        mat=MATERIALS[j]
        latent=LATENT_A if mat=="A" else 0.
        h=e[j,i]/m[j,i]
        eff=CP[mat]+latent/(TL-TS)
        t[i]=(h+latent*TS/(TL-TS))/eff
    if not np.isfinite(t).all():
        raise ValueError("Invalid derived temperature")
    f=phase_A_liquid_fraction(t,ai)
    m_liquid=m[0]*f
    m_solid=m[0]-m_liquid
    if np.max(np.abs(m_liquid+m_solid-m[0]))>1e-12:
        raise ValueError("Phase A does not partition its mass")
    # B is inert thermally in the sense of phase conversion:
    # no fictitious solid-liquid B fraction is defined.
    return {"temp_K":t,"fraction_A_liquid":f,
            "A_liquid_kg":m_liquid,"A_solid_kg":m_solid,
            "volume_occupied_m3":m[0]/RHO["A"]+m[1]/RHO["B"]}


def capacities(ds):
    m=ds["material_mass_kg"].values
    ai=active_index(m)
    coeff=np.empty(N,dtype=np.float64)
    for i in range(N):
        mat=MATERIALS[int(ai[i])]
        latent=LATENT_A if mat=="A" else 0.
        coeff[i]=(m[int(ai[i]),i]/CELL_VOLUME)*(CP[mat]+latent/(TL-TS))
    return coeff


def run_case(composition="AB",conductivity=K,uniform=False):
    owner=make_owner(composition,uniform)
    baseline_m=owner["material_mass_kg"].values.copy()
    initial_E=float(owner["internal_energy_J"].sum())
    before=derive(owner)
    first_sha=state_hash(owner)
    mesh=Grid1D(nx=N,dx=1.)
    temp=CellVariable(mesh=mesh,value=before["temp_K"].copy())
    cap=CellVariable(mesh=mesh,value=capacities(owner))
    equation=TransientTerm(coeff=cap)==DiffusionTerm(coeff=float(conductivity))
    peak_residual=0.
    for step in range(STEPS):
        temp.setValue(derive(owner)["temp_K"])
        equation.solve(var=temp,dt=DT)
        t=np.asarray(temp.value,dtype=np.float64)
        # energy_for_temp checks that material A stays in its transition band.
        e=energy_for_temp(t,baseline_m)
        candidate=owner.copy(deep=True)
        candidate["internal_energy_J"].values[:,:]=e
        res=validate(candidate,baseline_m,initial_E)
        peak_residual=max(peak_residual,abs(res))
        owner=candidate
    after=derive(owner)
    mfinal=owner["material_mass_kg"].values
    return {
        "owner":owner,"before":before,"after":after,
        "composition":composition,"conductivity_W_mK":conductivity,"uniform":uniform,
        "mass_A_kg":float(mfinal[0].sum()),
        "mass_B_kg":float(mfinal[1].sum()),
        "total_mass_kg":float(mfinal.sum()),
        "total_occupied_volume_m3":float(after["volume_occupied_m3"].sum()),
        "initial_energy_J":initial_E,
        "final_energy_J":float(owner["internal_energy_J"].sum()),
        "peak_energy_error_J":peak_residual,
        "hot_cell3_temp_initial_K":float(before["temp_K"][3]),
        "hot_cell3_temp_final_K":float(after["temp_K"][3]),
        "cold_cell4_temp_initial_K":float(before["temp_K"][4]),
        "cold_cell4_temp_final_K":float(after["temp_K"][4]),
        "A3_liquid_fraction_initial":float(before["fraction_A_liquid"][3]),
        "A3_liquid_fraction_final":float(after["fraction_A_liquid"][3]),
        "A_liquid_mass_initial_kg":float(before["A_liquid_kg"].sum()),
        "A_liquid_mass_final_kg":float(after["A_liquid_kg"].sum()),
        "state_sha256_initial":first_sha,
        "state_sha256_final":state_hash(owner),
    }


def rejection_tests(owner,initial_E):
    digest=state_hash(owner)
    masses=owner["material_mass_kg"].values.copy()
    flags={}
    def reject(label,change):
        c=owner.copy(deep=True)
        change(c)
        try:
            validate(c,masses,initial_E)
        except ValueError:
            flags[label]=True
        else:
            raise AssertionError("Invalid material state accepted "+label)
        assert state_hash(owner)==digest
    reject("add_energy_without_source",lambda d:d["internal_energy_J"].values.__setitem__((0,2),d["internal_energy_J"].values[0,2]+1.))
    reject("negative_mass",lambda d:d["material_mass_kg"].values.__setitem__((0,2),-1.))
    reject("overcapacity",lambda d:d["material_mass_kg"].values.__setitem__((0,2),3.))
    reject("two_species_same_filled_cell",lambda d:d["material_mass_kg"].values.__setitem__((1,2),0.01))
    reject("wrong_energy_units",lambda d:d["internal_energy_J"].attrs.__setitem__("units","kJ"))
    reject("different_heat_capacity",lambda d:d.attrs.__setitem__("cp_A_J_kgK",CP["A"]+1.))
    reject("different_density",lambda d:d.attrs.__setitem__("rho_B_kg_m3",RHO["B"]+1.))
    reject("duplicate_temperature_stock",lambda d:d.__setitem__("temperature_K",xr.DataArray(np.ones(N),dims=("cell",))))
    reject("material_identity_changed",lambda d:d.coords.__setitem__("material",np.array(["C","B"])))
    return flags


def main():
    ab=run_case("AB",K)
    k0=run_case("AB",0.)
    uniform=run_case("AB",K,uniform=True)
    bb=run_case("BB",K)
    replay=run_case("AB",K)
    failed=[]
    def check(label,okay):
        if not okay:failed.append(label)
    check("material_mass_exact",all(z["total_mass_kg"]==16. for z in (ab,k0,uniform,bb,replay)))
    check("material_composition_exact",ab["mass_A_kg"]==8. and ab["mass_B_kg"]==8. and bb["mass_B_kg"]==16.)
    check("exclusive_volume",all(z["total_occupied_volume_m3"]==8. for z in (ab,k0,uniform,bb,replay)))
    check("latent_phase_change_A_cell3",ab["A3_liquid_fraction_initial"]-ab["A3_liquid_fraction_final"]>0.02)
    check("B_cell4_warmed",ab["cold_cell4_temp_final_K"]-ab["cold_cell4_temp_initial_K"]>0.5)
    check("B_no_fictitious_phase",np.all(bb["after"]["fraction_A_liquid"]==0.))
    check("k0_unchanged_energy",np.max(np.abs(k0["owner"]["internal_energy_J"].values-
                                  make_owner("AB")["internal_energy_J"].values))<1e-7)
    check("k0_unchanged_temperature",np.max(np.abs(k0["after"]["temp_K"]-k0["before"]["temp_K"]))<1e-12)
    check("uniform_unchanged_energy",np.max(np.abs(uniform["owner"]["internal_energy_J"].values-
                                  make_owner("AB",uniform=True)["internal_energy_J"].values))<1e-7)
    check("uniform_unchanged_temperature",np.max(np.abs(uniform["after"]["temp_K"]-uniform["before"]["temp_K"]))<1e-12)
    ab_drop=ab["hot_cell3_temp_initial_K"]-ab["hot_cell3_temp_final_K"]
    bb_drop=bb["hot_cell3_temp_initial_K"]-bb["hot_cell3_temp_final_K"]
    check("different_composition_different_response",bb_drop-ab_drop>0.25)
    check("replay_exact_energy_and_mass",np.array_equal(ab["owner"]["internal_energy_J"].values,
                                             replay["owner"]["internal_energy_J"].values)
          and np.array_equal(ab["owner"]["material_mass_kg"].values,replay["owner"]["material_mass_kg"].values))
    check("all_energy_ledgers",all(z["peak_energy_error_J"]<0.02 for z in (ab,k0,uniform,bb,replay)))
    check("no_A_phase_stock",all(set(z["owner"].data_vars)=={"material_mass_kg","internal_energy_J"}
                                for z in (ab,k0,uniform,bb,replay)))
    rejected=rejection_tests(ab["owner"],ab["initial_energy_J"])
    with tempfile.TemporaryDirectory(prefix="world_h16_") as td:
        p=pathlib.Path(td)/"joint_matter_energy.nc"
        ab["owner"].to_netcdf(p,engine="scipy")
        with xr.open_dataset(p,engine="scipy") as fd:
            loaded=fd.load()
        validate(loaded,ab["owner"]["material_mass_kg"].values,ab["initial_energy_J"])
        check("checkpoint_restored_exact",state_hash(loaded)==state_hash(ab["owner"])
              and np.array_equal(derive(loaded)["temp_K"],ab["after"]["temp_K"])
              and np.array_equal(derive(loaded)["fraction_A_liquid"],ab["after"]["fraction_A_liquid"]))
        bytes_saved=p.stat().st_size
    def results(z):
        return {k:v for k,v in z.items() if k not in ("owner","before","after")}
    report={
        "experiment":"E1 H16 two-material mass-volume-energy common owner with phase-A conversion",
        "fipy":fipy.__version__,"numpy":np.__version__,"xarray":xr.__version__,"python":platform.python_version(),
        "temperature_range_A_K":[TS,TL],
        "mass_total_kg":16.,"cell_count":N,"dt_s":DT,"steps":STEPS,
        "active_AB":results(ab),"no_conductivity_AB":results(k0),
        "uniform_AB":results(uniform),"all_B_control":results(bb),
        "cell3_cooling_AB_K":ab_drop,"cell3_cooling_BB_K":bb_drop,
        "composition_cooling_difference_BB_minus_AB_K":bb_drop-ab_drop,
        "replay_exact":True,"rejected_invalid_states":rejected,
        "checkpoint_bytes":bytes_saved,"preregistered_gates_failed":failed,
        "limitations":"A/B occupy separate 1D cells with equal abstract density; only A has reversible mushy phase fraction. No intracell mixing, 3D ROI, fluid transport, volumetric change or mechanics."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True),flush=True)
    if failed:
        raise AssertionError("H16 gates failed: "+", ".join(failed))


if __name__=="__main__":
    main()
