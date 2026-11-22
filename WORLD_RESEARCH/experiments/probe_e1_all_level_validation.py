"""E1-H3: validate ALL material layers before publishing a staged state.

No physics. Uses the H1 MatterGrid oracle and existing Pandera xarray schemas.
An explicit, single-writer numpy.copyto commit leaves Landlab zero-copy
views attached. No claim of thread-safe atomicity.
Prerecorded: ETAPA_1_H3_PROTOCOLO_VALIDACION_COMMIT.md.
"""
from __future__ import annotations
import hashlib
import json
import time

import landlab
import numpy as np
import pandera
import pandera.xarray as pa
import xarray as xr

from probe_e1_state_representations import (
    HEIGHT, MATERIALS, WIDTH, dataset_projection, oracle,
    validate_and_restore,
)
from probe_e1_shared_state_views import bind_fields, matter_totals

DIMS=("material","level","y","x")

def schema():
    def valid_contents(ds):
        mass=ds["material_mass"].values
        density=ds["material_density"].values
        if not np.isfinite(mass).all() or not np.isfinite(density).all():
            return False
        if np.any(mass < 0) or np.any(density <= 0):
            return False
        vol=np.sum(mass/density[:,None,None,None],axis=0)
        cap=float(ds.attrs["cell_capacity_m3"])
        return bool(np.all(vol<=cap+1e-10))
    return pa.DatasetSchema(
        data_vars={
            "material_mass":pa.DataVar(
                dtype=np.float64,dims=DIMS,attrs={"units":"kg"}
            ),
            "material_density":pa.DataVar(
                dtype=np.float64,dims=("material",),attrs={"units":"kg m-3"}
            )
        },
        dims=DIMS,
        sizes={"material":len(MATERIALS),"level":2,"y":HEIGHT,"x":WIDTH},
        attrs={"schema_version":1,"cell_capacity_m3":1.0},
        checks=pa.Check(valid_contents, name="finite_nonnegative_capacity_all_levels"),
        strict=True,
    )

def validate_full(candidate,validator,expected_totals):
    """Schema and physics-independent, existing MatterGrid cell invariants."""
    validator.validate(candidate)
    actual_names=candidate.coords["material"].values.tolist()
    if actual_names!=sorted(MATERIALS):
        raise ValueError("Unexpected material identifiers or index ordering")
    if candidate.coords["level"].values.tolist()!=[0,1]:
        raise ValueError("Unknown layer labels/order")
    for level in (0,1):
        validate_and_restore(candidate,level=level)
    totals=matter_totals(candidate)
    if not all(np.isclose(totals[k],expected_totals[k],rtol=0,atol=1e-12)
               for k in expected_totals):
        raise ValueError("Unaccounted source or sink in a closed material inventory")
    return totals

def corrupted_scenarios(ds):
    def negative_upper(d):
        d["material_mass"].values[0,1,0,0]=-0.05
    def overcapacity_upper(d):
        d["material_mass"].values[1,1,0,0]=1.1
    def nan_upper(d):
        d["material_mass"].values[0,1,0,0]=np.nan
    def unaccounted_mass(d):
        d["material_mass"].values[0,1,0,0]=0.05
    def wrong_units(d):
        d["material_mass"].attrs["units"]="g"
    def permuted_dims(d):
        d["material_mass"]=d["material_mass"].transpose("material","level","x","y")
    def unexpected_material(d):
        d.coords["material"]=np.asarray(["A","Z"])
    return {
        "negative_upper_layer":negative_upper,
        "capacity_exceeded_upper_layer":overcapacity_upper,
        "nan_upper_layer":nan_upper,
        "unaccounted_source_upper_layer":unaccounted_mass,
        "unit_mismatch":wrong_units,
        "permuted_material_mass_dimensions":permuted_dims,
        "unexpected_material_identifier":unexpected_material,
    }

def main():
    initial=dataset_projection(oracle())
    owner=initial["material_mass"].values
    g,mapping,aliases=bind_fields(initial)
    assert all(aliases.values())
    before_hash=hashlib.sha256(owner.tobytes()).hexdigest()
    orig_totals=matter_totals(initial)
    val=schema()
    start=time.perf_counter()
    assert validate_full(initial,val,orig_totals)==orig_totals
    baseline_validation_ms=(time.perf_counter()-start)*1000

    old_bytes=owner.tobytes()
    old_fields={m:g.at_cell[f"material_mass__{m}"].copy() for m in MATERIALS}
    rejected={}
    for name,mutate in corrupted_scenarios(initial).items():
        proposed=initial.copy(deep=True)
        assert not np.shares_memory(owner,proposed["material_mass"].values)
        mutate(proposed)
        try:
            validate_full(proposed,val,orig_totals)
        except (pa.errors.SchemaError,pa.errors.SchemaErrors,ValueError) as e:
            rejected[name]={"rejected":True,"error_type":type(e).__name__}
        else:
            rejected[name]={"rejected":False,"error_type":"none"}
        assert rejected[name]["rejected"], (name,"INVALID STATE WAS ACCEPTED")
        assert owner.tobytes()==old_bytes, (name,"rejected candidate mutated owner")
        for m in MATERIALS:
            assert np.array_equal(g.at_cell[f"material_mass__{m}"],old_fields[m])

    candidate=initial.copy(deep=True)
    values=candidate["material_mass"].values
    x,y=2,1
    material_idx=0 # sorted A,B
    assert values[material_idx,0,y,x]>=.1
    values[material_idx,0,y,x]-=.1
    values[material_idx,1,y,x]+=.1
    valid_totals=validate_full(candidate,val,orig_totals)

    assert owner.tobytes()==old_bytes, "staging already altered canonical owner"
    start=time.perf_counter()
    np.copyto(owner,values)
    commit_us=(time.perf_counter()-start)*1e6
    assert all(np.shares_memory(
        g.at_cell[f"material_mass__{m}"],owner
    ) for m in MATERIALS)
    assert g.at_cell["material_mass__A"][mapping[(x,y)]]==owner[0,0,y,x]
    assert np.array_equal(owner,values)
    assert matter_totals(initial)==valid_totals
    assert np.array_equal(owner[:,1,:,:],values[:,1,:,:])
    assert owner[0,1,y,x]==.1
    assert owner[0,0,y,x]==.4
    assert validate_full(initial,val,orig_totals)==orig_totals

    report={
        "test":"E1-H3 pandera schema + existing MatterGrid all-layer validator",
        "landlab_version":landlab.__version__,
        "xarray_version":xr.__version__,
        "pandera_version":pandera.__version__,
        "shape":list(owner.shape),
        "before_sha256":before_hash,
        "after_sha256":hashlib.sha256(owner.tobytes()).hexdigest(),
        "rejected_corruptions":rejected,
        "rejection_count":len(rejected),
        "rejected_candidate_never_mutated_owner":True,
        "staged_transfer_A_kg":.1,
        "mass_conserved_in_all_layers":valid_totals,
        "landlab_views_still_share_memory":True,
        "upper_layer_manual_transfer_only":True,
        "schema_validation_ms":round(baseline_validation_ms,4),
        "single_writer_copyto_commit_us":round(commit_us,4),
        "limits":"Test proves only safe staged validation in a single writer. Numpy.copyto is not a concurrency transaction; shared arrays still permit bypass edits. Pandera adds dependencies; no 3D solver or physical law implemented."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
