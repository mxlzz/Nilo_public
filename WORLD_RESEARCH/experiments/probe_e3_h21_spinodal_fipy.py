"""H21: native FiPy Cahn-Hilliard phase segregation with one canonical A/B mass owner.

Uses exact PDE term structure from NIST FiPy examples/cahnHilliard/mesh2D.py.
No custom PDE or solver. Pre-registered physical/statistical acceptance criteria
in ETAPA_3_H21_PROTOCOLO_CAHN_HILLIARD.md.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import platform
import tempfile

import fipy
import numpy as np
import scipy
import xarray as xr
from fipy import CellVariable, DefaultSolver, DiffusionTerm, Grid2D, TransientTerm
from scipy.ndimage import label

NY=NX=20
N_STEPS=400
SEED=20261122
NULL_SEED=20261123
N_NULL=512
PER_CELL_KG=1.0
A_EPSILON=1.0
EPSILON=1.0
FOUR_NEIGHBORS=np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=np.int8)


def clean(v):
    return v.item() if isinstance(v,np.generic) else v


def digest(ds):
    h=hashlib.sha256()
    h.update(ds["material_mass_kg"].values.tobytes())
    h.update(ds["material_mass_kg"].attrs["units"].encode())
    h.update(json.dumps({
        "material":[str(z) for z in ds.coords["material"].values.tolist()],
        "y":[int(z) for z in ds.coords["y"].values.tolist()],
        "x":[int(z) for z in ds.coords["x"].values.tolist()],
        "attrs":{k:clean(v) for k,v in ds.attrs.items()},
    },sort_keys=True).encode())
    return h.hexdigest()


def perturbations():
    rng=np.random.default_rng(SEED)
    return rng.uniform(-.07,.07,(NY,NX)).astype(np.float64)


def make_owner(mean):
    phi=mean+perturbations()
    mass=np.stack((phi,1.-phi))*PER_CELL_KG
    ds=xr.Dataset(
        {
            "material_mass_kg":(("material","y","x"),mass,
                {"units":"kg", "role":"canonical per-material mass"})
        },
        coords={
            "material":np.array(["A","B"],dtype="U1"),
            "y":np.arange(NY,dtype=np.int32),
            "x":np.arange(NX,dtype=np.int32),
        },
        attrs={
            "schema_version":1,"seed":SEED,
            "initial_mean_A":float(mean),
            "baseline_mass_A_kg":float(np.sum(mass[0])),
            "baseline_mass_B_kg":float(np.sum(mass[1])),
            "dx":.25,"dy":.25,"cell_mass_kg":PER_CELL_KG,
        }
    )
    validate(ds)
    return ds


def validate(ds):
    if set(ds.data_vars)!={"material_mass_kg"}:
        raise ValueError("Wrong or duplicated mass owner")
    v=ds["material_mass_kg"]
    if v.dims!=("material","y","x") or v.shape!=(2,NY,NX):
        raise ValueError("Wrong topology")
    if v.attrs.get("units")!="kg":
        raise ValueError("Wrong units")
    if [str(x) for x in ds.coords["material"].values.tolist()]!=["A","B"]:
        raise ValueError("Material ID corrupted")
    if [int(x) for x in ds.coords["y"].values.tolist()]!=list(range(NY)) or [int(x) for x in ds.coords["x"].values.tolist()]!=list(range(NX)):
        raise ValueError("Invalid coordinates")
    attrs=dict(ds.attrs)
    if attrs.get("schema_version")!=1 or attrs.get("seed")!=SEED or attrs.get("dx")!=.25 or attrs.get("dy")!=.25 or attrs.get("cell_mass_kg")!=PER_CELL_KG:
        raise ValueError("Schema or physical domain changed")
    m=attrs.get("initial_mean_A")
    if m not in (.5,.1):
        raise ValueError("Unexpected initial composition")
    if not np.isfinite(v.values).all() or np.any(v.values<0):
        raise ValueError("Negative/nonfinite component mass")
    if not np.allclose(v.values.sum(axis=0),PER_CELL_KG,rtol=0,atol=1e-12):
        raise ValueError("Material created or duplicated within a cell")
    aa=float(v.values[0].sum())
    bb=float(v.values[1].sum())
    if abs(aa-float(attrs["baseline_mass_A_kg"]))>=1e-4 or abs(bb-float(attrs["baseline_mass_B_kg"]))>=1e-4:
        raise ValueError("Material source/sink globally outside gate")
    return {
        "mass_A_kg":aa,"mass_B_kg":bb,
        "total_kg":aa+bb,
        "mass_A_residual_kg":aa-float(attrs["baseline_mass_A_kg"])
    }


def fraction(ds):
    m=ds["material_mass_kg"].values
    return m[0]/m.sum(axis=0)


def same_edge_score(mask):
    m=np.asarray(mask,dtype=bool)
    n=int(np.count_nonzero(m[:,:-1]==m[:,1:])+
          np.count_nonzero(m[:-1,:]==m[1:,:]))
    return float(n/(NY*(NX-1)+NX*(NY-1)))


def null_conditioned(mask):
    rng=np.random.default_rng(NULL_SEED)
    counts=np.asarray(mask.sum(axis=1),dtype=int)
    scores=[]
    for _ in range(N_NULL):
        sample=np.zeros((NY,NX),dtype=bool)
        for row,n in enumerate(counts):
            if n:
                selected=rng.choice(NX,size=int(n),replace=False)
                sample[row,selected]=True
        scores.append(same_edge_score(sample))
    return {
        "seed":NULL_SEED,"n_trials":N_NULL,"row_counts":counts.tolist(),
        "p95_same_edges":float(np.quantile(scores,.95,method="higher")),
        "mean_same_edges":float(np.mean(scores)),
        "max_same_edges":float(max(scores)),
    }


def describe(phi):
    mask=phi>.5
    labs,count=label(mask,structure=FOUR_NEIGHBORS)
    sizes=np.bincount(labs[labs>0],minlength=count+1)[1:] if count else np.array([],dtype=int)
    return {
        "q05":float(np.quantile(phi,.05)),
        "q95":float(np.quantile(phi,.95)),
        "variance":float(np.var(phi)),
        "mean":float(np.mean(phi)),
        "n_high":int(mask.sum()),
        "n_low":int(mask.size-mask.sum()),
        "same_edge_score":same_edge_score(mask),
        "high_domain_components":int(count),
        "high_domain_largest":int(max(sizes)) if sizes.size else 0,
    }


def run_case(mobility,mean):
    owner=make_owner(mean)
    start=describe(fraction(owner))
    first=fraction(owner).copy()
    mesh=Grid2D(nx=NX,ny=NY,dx=.25,dy=.25)
    phi=CellVariable(mesh=mesh,value=first.ravel().copy(),name="temporary composition A")
    PHI=phi.arithmeticFaceValue
    D=float(mobility)
    # Exact 4th-order conservative PDE term structure from upstream example.
    eq=(TransientTerm()==DiffusionTerm(coeff=D*A_EPSILON**2*(1-6*PHI*(1-PHI)))
        -DiffusionTerm(coeff=(D,EPSILON**2)))
    solver=DefaultSolver()
    peak_mass_error=0.
    points={}
    elapsed=0.
    for step in range(1,N_STEPS+1):
        phi.setValue(fraction(owner).ravel())
        dt=min(100.,math.exp(-5.+.01*(step-1)))
        eq.solve(var=phi,dt=dt,solver=solver)
        elapsed+=dt
        next_fraction=np.array(phi.value,dtype=np.float64).reshape((NY,NX))
        if not np.isfinite(next_fraction).all():
            raise ValueError("Nonfinite FiPy composition")
        candidate=owner.copy(deep=True)
        candidate["material_mass_kg"].values[0,:,:]=next_fraction*PER_CELL_KG
        candidate["material_mass_kg"].values[1,:,:]=(1.-next_fraction)*PER_CELL_KG
        budget=validate(candidate)
        peak_mass_error=max(peak_mass_error,abs(budget["mass_A_residual_kg"]))
        owner=candidate
        if step in (300,400):
            points[step]=fraction(owner).copy()
    final=fraction(owner).copy()
    return {
        "owner":owner,"initial":first,"snapshots":points,
        "seed":SEED,"mobility":D,"initial_mean":mean,
        "initial_stats":start,"final_stats":describe(final),
        "peak_mass_A_residual_kg":peak_mass_error,
        "elapsed_model_time":elapsed,
        "mass_final_kg":float(owner["material_mass_kg"].sum()),
        "owner_hash":digest(owner),
    }


def reject_candidates(owner):
    original=digest(owner)
    flags={}
    def reject(label,patch):
        c=owner.copy(deep=True)
        patch(c)
        try:
            validate(c)
        except ValueError:
            flags[label]=True
        else:
            raise AssertionError("Invalid matter state accepted "+label)
        if digest(owner)!=original:
            raise AssertionError("Owner changed on rejection")
    reject("unaccounted_plus_1kg",lambda d:d["material_mass_kg"].values.__setitem__((0,1,1),d["material_mass_kg"].values[0,1,1]+1.))
    reject("negative_A_mass",lambda d:d["material_mass_kg"].values.__setitem__((0,1,1),-1.))
    reject("wrong_units",lambda d:d["material_mass_kg"].attrs.__setitem__("units","g"))
    reject("new_species_id",lambda d:d.coords.__setitem__("material",np.array(["A","C"])))
    reject("extra_phi_stock",lambda d:d.__setitem__("phi",xr.DataArray(np.ones((NY,NX)),dims=("y","x"))))
    reject("corrupt_cell_id",lambda d:d.coords.__setitem__("x",np.arange(NX)+2))
    reject("overcapacity",lambda d:d["material_mass_kg"].values.__setitem__((1,2,2),2.))
    return flags


def main():
    active=run_case(1.,.5)
    disabled=run_case(0.,.5)
    stable=run_case(1.,.1)
    replay=run_case(1.,.5)

    final=fraction(active["owner"])
    mask=final>.5
    mask_early=active["snapshots"][300]>.5
    union=int(np.logical_or(mask,mask_early).sum())
    overlap=float(np.logical_and(mask,mask_early).sum()/union) if union else 0.
    null=null_conditioned(mask)
    no_mob=float(np.max(np.abs(fraction(disabled["owner"])-disabled["initial"])))
    good=describe(final)
    bad=describe(fraction(stable["owner"]))
    fail=[]
    def check(name,ok):
        if not ok:fail.append(name)
    check("global_mass_A_B_conserved",all(q["peak_mass_A_residual_kg"]<1e-4 and
          q["mass_final_kg"]==400. for q in (active,disabled,stable,replay)))
    check("both_fractions_present",good["n_high"]>=8 and good["n_low"]>=8)
    check("segregation_quantiles",good["q95"]>.7 and good["q05"]<.3)
    check("variance_growth",good["variance"]>2*active["initial_stats"]["variance"])
    check("spatial_organization_over_row_null",good["same_edge_score"]>null["p95_same_edges"]+.08)
    check("pattern_persists",overlap>=.60)
    check("zero_mobility_unchanged",no_mob<1e-8)
    check("stable_mean_no_strong_segregation",bad["q95"]<.3 and bad["variance"]<1.5*stable["initial_stats"]["variance"])
    check("exact_replay",np.array_equal(active["owner"]["material_mass_kg"].values,
                                        replay["owner"]["material_mass_kg"].values)
          and np.array_equal(active["snapshots"][300],replay["snapshots"][300])
          and active["owner_hash"]==replay["owner_hash"])
    rejected=reject_candidates(active["owner"])
    with tempfile.TemporaryDirectory(prefix="world_e3_h21_") as td:
        p=pathlib.Path(td)/"binary_matter_owner.nc"
        active["owner"].to_netcdf(p,engine="scipy")
        with xr.open_dataset(p,engine="scipy") as f:
            loaded=f.load()
        validate(loaded)
        check("checkpoint_owner_exact",digest(loaded)==active["owner_hash"]
              and np.array_equal(loaded["material_mass_kg"].values,
                                 active["owner"]["material_mass_kg"].values))
        checkpoint_size=p.stat().st_size
    def public(d):
        return {k:v for k,v in d.items() if k not in ("owner","initial","snapshots")}
    print("WORLD_EVAL_JSON "+json.dumps({
        "experiment":"E3 H21 FiPy Cahn-Hilliard conserved binary segregation 2D",
        "provider":"NIST FiPy examples/cahnHilliard/mesh2D.py",
        "fipy":fipy.__version__,"numpy":np.__version__,
        "scipy":scipy.__version__,"xarray":xr.__version__,"python":platform.python_version(),
        "grid":[NY,NX],"total_mass_kg":400.,
        "steps":N_STEPS,"rng_seed":SEED,
        "active":public(active),"no_mobility":public(disabled),
        "stable_composition":public(stable),
        "conditioned_row_null":null,
        "pattern_jaccard_step300_step400":overlap,
        "no_mobility_max_fraction_change":no_mob,
        "negative_candidates_rejected":rejected,
        "replay_exact":True,"netcdf_bytes":checkpoint_size,
        "failed_preregistered_gates":fail,
        "limitations":"2D ideal dimensionless binary mixture; no kinetics beyond Cahn-Hilliard, no mechanical support, heat or sediment coupling; spatial organization is not new objects or universal emergence."
    },sort_keys=True),flush=True)
    if fail:
        raise AssertionError("H21 preregistered gates failed: "+", ".join(fail))


if __name__=="__main__":
    main()
