"""E1/H4: disprove lossless heightfield geometry for voids and bridges.

This is ONLY data representation, no invented physics/gravity/cohesion laws.
Pre-registered in ETAPA_1_H4_PROTOCOLO_REPRESENTACION_3D.md.
Uses published Trimesh VoxelGrid dense and sparse encodings, NumPy, xarray,
and scipy.ndimage labelling. Geometry is a prescribed TEST FIXTURE, not an
emergent structure.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform

import numpy as np
import scipy
from scipy import ndimage
import xarray as xr
import trimesh
from trimesh.voxel.encoding import DenseEncoding, SparseEncoding

SHAPE_XYZ=(12,8,7)      # x,y,z counts, positive z is "up"
VOXEL_VOLUME_M3=1.0
DENSITIES_KG_M3=np.array([2.,1.],dtype=np.float64)
MATERIALS=["A","B"]


def heightfield(xyz):
    assert xyz.shape==SHAPE_XYZ
    heights=np.where(xyz,np.arange(xyz.shape[2])[None,None,:],-1)
    return heights.max(axis=2)


def heightfield_to_solid(heights):
    z=np.arange(SHAPE_XYZ[2])
    return ((heights[:,:,None]>=0)&(z[None,None,:]<=heights[:,:,None]))


def test_encodings(xyz):
    assert xyz.dtype==np.bool_
    d=trimesh.voxel.VoxelGrid(DenseEncoding(xyz))
    s=trimesh.voxel.VoxelGrid(SparseEncoding.from_dense(xyz))
    assert np.array_equal(d.matrix,xyz)
    assert np.array_equal(s.matrix,xyz)
    assert d.filled_count==s.filled_count==int(np.count_nonzero(xyz))
    assert np.array_equal(
        np.sort(d.sparse_indices,axis=0),
        np.sort(s.sparse_indices,axis=0)
    )
    return int(d.filled_count)


def h4a():
    full=np.zeros(SHAPE_XYZ,dtype=bool)
    full[2:10,1:7,0:6]=True   # x-width8 * y-width6 * z-height6 = 288
    hollow=full.copy()
    hollow[4:8,3:5,2:4]=False # x4 * y2 * z2 = 16 fully enclosed air
    hf_full=heightfield(full)
    hf_hollow=heightfield(hollow)
    assert np.array_equal(hf_full,hf_hollow)
    labels,n=ndimage.label(~hollow,structure=ndimage.generate_binary_structure(3,1))
    cavity_label=int(labels[5,3,2])
    assert cavity_label>0
    positions=np.argwhere(labels==cavity_label)
    assert len(positions)==16
    assert all((positions.min(axis=0)>0)) and all((positions.max(axis=0)<np.asarray(SHAPE_XYZ)-1)), (
        "Cavity must not communicate with any world boundary")
    reconstruction=heightfield_to_solid(hf_hollow)
    false_occupied=int(np.count_nonzero(reconstruction & ~hollow))
    assert false_occupied==16
    assert test_encodings(full)==288
    assert test_encodings(hollow)==272
    assert not np.array_equal(full,hollow)
    return {
        "block_solid_m3":int(full.sum()),
        "block_hollow_m3":int(hollow.sum()),
        "enclosed_air_cavity_m3":len(positions),
        "same_heightfield":True,
        "distinct_3d_sha256":hashlib.sha256(full.tobytes()).hexdigest()!=hashlib.sha256(hollow.tobytes()).hexdigest(),
        "solid_reconstruction_false_positive_voxels":false_occupied,
        "mass_difference_kg_at_density2":2.*(full.sum()-hollow.sum()),
        "cavity_component_is_disconnected_from_domain_exterior":True,
    }


def make_bridge_xyz():
    v=np.zeros(SHAPE_XYZ,dtype=bool)
    v[2:4,2:6,0:5]=True    # left pillar
    v[8:10,2:6,0:5]=True   # right pillar
    v[2:10,2:6,4:5]=True   # connected upper beam
    return v


def h4b():
    v=make_bridge_xyz()
    hf=heightfield(v)
    assert v[5,3,4] and not v[5,3,2]
    reconstructed=heightfield_to_solid(hf)
    false_vox=int(np.count_nonzero(reconstructed & ~v))
    assert false_vox>0
    assert test_encodings(v)==int(np.count_nonzero(v))
    labels,n=ndimage.label(v,structure=ndimage.generate_binary_structure(3,1))
    assert n==1, "The two pillars and beam must be one 6-connected geometry"
    assert np.all(reconstructed|(~v))
    return {
        "bridge_geometry_6_connected_components":int(n),
        "bridge_roof_voxel_occupied":bool(v[5,3,4]),
        "space_under_bridge_empty":bool(not v[5,3,2]),
        "real_occupied_voxels":int(v.sum()),
        "heightfield_reconstructed_occupied_voxels":int(reconstructed.sum()),
        "false_occupied_voxels_due_to_heightfield":false_vox,
        "mechanical_stability_tested":False
    }


def bridge_material_ds():
    # x,y,z -> z,y,x
    o=make_bridge_xyz().transpose(2,1,0)
    mass=np.zeros((2,SHAPE_XYZ[2],SHAPE_XYZ[1],SHAPE_XYZ[0]),dtype=np.float64)
    mass[0,o]=2.0
    # A few roof voxels are B, not a second material in the same cell.
    for x in (5,6,7):
        assert o[4,3,x]
        mass[0,4,3,x]=0.
        mass[1,4,3,x]=1.
    ds=xr.Dataset(
        data_vars={
            "material_mass":(
                ("material","z","y","x"),mass,
                {"units":"kg","meaning":"full voxel masses, geometric test fixture"}
            ),
            "material_density":(
                ("material",),DENSITIES_KG_M3.copy(),
                {"units":"kg m-3"}
            )
        },
        coords={
            "material":MATERIALS,
            "z":np.arange(SHAPE_XYZ[2],dtype=np.int32),
            "y":np.arange(SHAPE_XYZ[1],dtype=np.int32),
            "x":np.arange(SHAPE_XYZ[0],dtype=np.int32),
        },
        attrs={
            "schema_version":1,
            "voxel_volume_m3":VOXEL_VOLUME_M3,
            "description":"Prescribed 3D material state. Not a gravity/structural solver.",
        }
    )
    return ds


def occupancy_and_check(ds):
    ma=ds["material_mass"].values
    densities=ds["material_density"].values
    vol=np.sum(ma/densities[:,None,None,None],axis=0)
    assert np.isfinite(ma).all()
    assert np.all(ma>=0)
    assert np.all(vol<=VOXEL_VOLUME_M3+1e-12)
    assert np.all(vol>=0)
    return vol>0.0


def h4c():
    ds=bridge_material_ds()
    occupancy_zyx=occupancy_and_check(ds)
    bridge_xyz=make_bridge_xyz()
    assert np.array_equal(occupancy_zyx.transpose(2,1,0),bridge_xyz)
    assert test_encodings(bridge_xyz)==int(bridge_xyz.sum())
    mass_initial=ds["material_mass"].sum(dim=("z","y","x"))
    expected_kg=dict(zip(MATERIALS,[float(x) for x in mass_initial.values]))
    assert expected_kg["B"]==3.0
    assert expected_kg["A"]==float(int(bridge_xyz.sum())-3)*2.0

    # Two materials can have the SAME occupancy but different species mass:
    # this is an alternative INITIAL condition, not an unaccounted reaction.
    replacement=ds.copy(deep=True)
    for x in (5,6,7):
        replacement["material_mass"].values[0,4,3,x]=2.
        replacement["material_mass"].values[1,4,3,x]=0.
    assert np.array_equal(occupancy_and_check(replacement),occupancy_zyx)
    alternate_kg={
        key:float(replacement["material_mass"].sel(material=key).sum().item())
        for key in MATERIALS
    }
    assert alternate_kg!=expected_kg
    assert test_encodings(occupancy_zyx.transpose(2,1,0))==int(bridge_xyz.sum())

    filename=pathlib.Path("/tmp/e1_h4_3d_materials.nc")
    ds.to_netcdf(filename,engine="scipy")
    with xr.open_dataset(filename,engine="scipy") as saved:
        loaded=saved.load()
    assert loaded["material_mass"].attrs["units"]=="kg"
    assert loaded["material_density"].attrs["units"]=="kg m-3"
    assert loaded.attrs["voxel_volume_m3"]==1.0
    assert np.array_equal(loaded["material_mass"].values,ds["material_mass"].values)
    assert np.array_equal(occupancy_and_check(loaded),occupancy_zyx)
    return {
        "owner_shape_material_z_y_x":list(ds["material_mass"].shape),
        "voxel_geometry_preserved_dense_and_sparse":True,
        "material_mass_kg_before":expected_kg,
        "same_occupancy_different_material_inventory":alternate_kg,
        "identities_not_in_trimesh_occupancy":True,
        "netcdf_roundtrip_exact":True,
        "netcdf_bytes":filename.stat().st_size,
        "physical_3d_simulation_tested":False
    }


def h4d():
    rng=np.random.default_rng(7321)
    dims=(96,96,64)
    m=np.zeros(dims,dtype=bool)
    n=3000
    choose=rng.choice(m.size,size=n,replace=False)
    m.flat[choose]=True
    sparse=SparseEncoding.from_dense(m)
    assert np.array_equal(sparse.dense,m)
    grid=trimesh.voxel.VoxelGrid(sparse)
    assert grid.filled_count==n
    assert bool(np.all(grid.is_filled(sparse.sparse_indices)))
    dense_payload=int(m.nbytes)
    sparse_indices=sparse.sparse_indices
    sparse_values=sparse.sparse_values
    sparse_payload=int(sparse_indices.nbytes+sparse_values.nbytes)
    return {
        "shape":list(dims),
        "seed":7321,
        "occupied_voxels":n,
        "occupancy_fraction":n/m.size,
        "dense_boolean_payload_bytes":dense_payload,
        "sparse_indices_plus_values_payload_bytes":sparse_payload,
        "sample_encoding_ratio_payload_only":sparse_payload/dense_payload,
        "warning":"Payload arrays ONLY, excludes Trimesh/SciPy/Python allocations and material identities. This is not benchmark of simulation memory."
    }


def main():
    report={
        "test":"E1 H4 geometry representability, not mechanical physics",
        "trimesh_version":trimesh.__version__,
        "xarray_version":xr.__version__,
        "scipy_version":scipy.__version__,
        "numpy_version":np.__version__,
        "python_version":platform.python_version(),
        "voxel_pitch_m":1.0,
        "H4a_height_collision_and_enclosed_cavity":h4a(),
        "H4b_static_bridge_geometry":h4b(),
        "H4c_material_identity_and_netcdf":h4c(),
        "H4d_sparse_occupancy_payload":h4d(),
        "limits":"A voxel fixture is authored as a test shape, NOT emergent. Neither mesh nor voxel array demonstrates mechanical stability, 3D dynamics, conservation during simulation, physically calibrated masses, or suitability of entire world for voxels. A heightmap collision is mathematical, not evidence of Landlab failure."
    }
    print("WORLD_EVAL_JSON "+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
