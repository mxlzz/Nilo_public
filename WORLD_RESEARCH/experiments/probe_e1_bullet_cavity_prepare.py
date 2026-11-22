"""H8 preparation process (Python >=3.13) using the already-tested H5 owner.

Only reads and modifies state, recording an explicit external material sink.
Exported NetCDF is consumed by the Bullet DIRECT test in Python3.11.
No physics or collision integrator is defined here.

Protocol: ETAPA_1_H8_PROTOCOLO_CAVIDAD_CONTACTO.md
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import platform
import sys

import numpy as np
import xarray as xr
import landlab

from probe_e1_surface_volume_partition import (
    make_state,derive_heights,validate,totals,
)


def owner_hash(ds):
    return hashlib.sha256(
        ds["outside_column_mass"].values.tobytes()
        + ds["roi_voxel_mass"].values.tobytes()
        + ds["rigid_body_mass"].values.tobytes()
        + json.dumps(ds.attrs["external_sinks_A_kg"]).encode()
    ).hexdigest()


def main(folder):
    folder.mkdir(parents=True,exist_ok=True)
    original=make_state()
    assert totals(original)=={"A":762.,"B":3.}
    hollow=original.copy(deep=True)
    raw=hollow["roi_voxel_mass"].values
    assert np.all(raw[0,2:4,2:4,2:6]==2.)
    assert np.all(raw[1,2:4,2:4,2:6]==0.)
    cavity_removed_A=float(raw[0,2:4,2:4,2:6].sum())
    assert cavity_removed_A==32.
    raw[0,2:4,2:4,2:6]=0.
    hollow=hollow.assign_coords(rigid_body=["excavated_A_cube"])
    hollow["rigid_body_mass"]=(
        ("material","rigid_body"),
        np.array([[2.0],[0.0]],dtype=np.float64),
        {"units":"kg","owner":"one original voxel moved to a rigid test body"}
    )
    hollow.attrs["external_sinks_A_kg"]=30.
    hollow.attrs["rigid_body_cube_side_m"]=1.
    validate(hollow,{"A":730.,"B":3.})
    assert float(hollow["rigid_body_mass"].values.sum())==2.
    assert 730.+2.+30.==762.
    original_height=derive_heights(original)
    cavity_height=derive_heights(hollow)
    assert np.array_equal(original_height,cavity_height)
    i=5-2
    j=3-1
    assert original["roi_voxel_mass"].values[0,3,j,i]==2.
    assert hollow["roi_voxel_mass"].values[0,3,j,i]==0.
    assert hollow["roi_voxel_mass"].values[0,2,j,i]==0.
    assert np.count_nonzero(
        (hollow["roi_voxel_mass"].values / hollow["material_density"].values[:,None,None,None]).sum(axis=0)
    )==272

    path=folder/"h8_material_owner.nc"
    hollow.to_netcdf(path,engine="scipy")
    with xr.open_dataset(path,engine="scipy") as h:
        restored=h.load()
    assert np.array_equal(
        restored["roi_voxel_mass"].values,hollow["roi_voxel_mass"].values
    )
    assert np.array_equal(derive_heights(restored),original_height)
    assert owner_hash(restored)==owner_hash(hollow)
    manifesto={
        "test":"H8 producer Landlab3.13 to Bullet3.11, data-only NetCDF interface",
        "python":platform.python_version(),
        "landlab_version":landlab.__version__,
        "xarray_version":xr.__version__,
        "owner_sha256":owner_hash(hollow),
        "heightfield_sha256":hashlib.sha256(original_height.tobytes()).hexdigest(),
        "original_height_equals_hollow":True,
        "full_world_body_initial_position_blocked":True,
        "hollow_world_body_initial_position_clear":True,
        "original_mass_kg":{"A":762.,"B":3.},
        "static_mass_kg":{"A":730.,"B":3.},
        "rigid_mobile_mass_kg":{"A":2.,"B":0.},
        "explicit_external_sink_A_kg":30.,
        "enclosed_void_voxels":16,
        "solid_roi_voxels_remaining":272,
        "netcdf_bytes":path.stat().st_size,
        "netcdf_file_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "limits":"Prescribed cavity from H5; no physics, just canonical material preparation."
    }
    (folder/"h8_manifest.json").write_text(json.dumps(manifesto,sort_keys=True,indent=2))
    print("WORLD_EVAL_JSON "+json.dumps(manifesto,sort_keys=True),flush=True)


if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: python producer.py /tmp/h8")
    main(pathlib.Path(sys.argv[1]))
