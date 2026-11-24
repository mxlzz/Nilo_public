"""P0-B-D: compare retained states and isolate cross-runner numerical differences."""
import hashlib
import json
import os
import pathlib
import platform
import subprocess
import sys
import numpy as np
import xarray as xr
import probe_e5_h31_owner_contract as c
import probe_e6_h33_resume_landlab as h33

MID={
(7321,0.):"aaeb17bce915227ba1b1fd5cbb6d4cf9aac2d9fd19340939c357c67e3786f97a",
(7321,.1):"ee60f5248cb11b5e7b336a270bae93fb2afe571612c183cd73d5845b05eaa810",
(8128,0.):"05061e3a2784b877836146a0bc8087bed704d8d36257137efbbaf16e4f37e7b3",
(8128,.1):"0556a712036fb6fdf62809f08e914f30c61c38b4313e7e88b7eb7d24491b8b36"}
REF={
(7321,0.):"28d3aacfa5a3daf589964c91892e100cd133bfd85a1e2df2511e8717b9430760",
(7321,.1):"33f352be6a90001f331f8ff97dde4fb12dcd044c02008a3bbcca61bba0b30d0b",
(8128,0.):"2a86b57667f5c2c554094c18117e74e4058c1f2868c68ce1320b97ebc76b8d02",
(8128,.1):"b97a8af673b509330e4a95423da371aaeac623530c3cbba12a243ceb3b48d5c6"}
OTHER={**REF,(7321,.1):"69fcd064a26333d6d9361736c0936b56a94c0314318e6e610e4857b5bb7ca810",
(8128,.1):"56041f73654b3938be1f7aa28ce2dbc99c1225d0034246fa3ac1a30ecc5f626c"}
WORKER=pathlib.Path(__file__).with_name("p0a_landlab_worker.py")

def load(path):
    with xr.open_dataset(path,engine="scipy") as f:return f.load()
def project(ds,raw,seed,k):
    out=c.augment(c.soil_only(ds),seed,c.SOURCES[seed],k)
    for key in ("landlab_step","landlab_t_bench"):out.attrs[key]=ds.attrs[key]
    c.validate(out,raw,seed,k)
    return out
def json_value(v):
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,np.ndarray):return v.tolist()
    raise TypeError(type(v).__name__)
def compare(a,b):
    differences={}
    for name in sorted(set(a.variables)|set(b.variables)):
        if name not in a or name not in b:
            differences[name]={"missing":True};continue
        x,y=a[name].values,b[name].values
        if x.shape!=y.shape: differences[name]={"shape":[list(x.shape),list(y.shape)]};continue
        bit_equal=x.dtype==y.dtype and x.tobytes()==y.tobytes()
        if not bit_equal:
            rec={"dtype":[str(x.dtype),str(y.dtype)],"unequal_elements":int(np.count_nonzero(x!=y))}
            if np.issubdtype(x.dtype,np.number) and np.issubdtype(y.dtype,np.number):
                delta=y.astype(np.float64)-x.astype(np.float64)
                rec.update(max_abs=float(np.max(np.abs(delta))),sum_delta=float(np.sum(delta)))
                if x.dtype==y.dtype==np.float64:
                    rec["unequal_bits"]=int(np.count_nonzero(x.view(np.uint64)!=y.view(np.uint64)))
                indices=np.argwhere(x!=y)
                rec["examples"]=[{"index":idx.tolist(),"a":float(x[tuple(idx)]),"b":float(y[tuple(idx)])} for idx in indices[:5]]
            differences[name]=rec
        if a[name].attrs!=b[name].attrs:differences[name+"_attrs"]={"a":a[name].attrs,"b":b[name].attrs}
    attrs={}
    for name in sorted(set(a.attrs)|set(b.attrs)):
        x,y=a.attrs.get(name),b.attrs.get(name)
        if x!=y or type(x)!=type(y):attrs[name]={"a":x,"b":y,"types":[type(x).__name__,type(y).__name__]}
    return {"fields":differences,"attrs":attrs,"sha_a":c.hash_owner(a),"sha_b":c.hash_owner(b)}

def run_worker(rawpath,seed,k,source,dest,env):
    sub=subprocess.run([sys.executable,str(WORKER),str(rawpath),str(seed),str(k),str(source),"6",str(dest)],env=env,capture_output=True,text=True)
    if sub.returncode:raise RuntimeError(sub.stdout+"\n"+sub.stderr)
    return load(dest)

def main(rawpath,a_root,b_root,b_result,outdir):
    root=pathlib.Path(outdir);root.mkdir(parents=True,exist_ok=False)
    a_root,b_root,b_result=map(pathlib.Path,(a_root,b_root,b_result))
    raw=h33.read_raw(rawpath)
    from numpy._core import _multiarray_umath as cpu
    base=list(cpu.__cpu_baseline__)
    dispatch=list(cpu.__cpu_dispatch__)
    enabled=cpu.__cpu_features__
    restricted=[x for x in dispatch if x not in base and enabled.get(x,False)]
    env=dict(os.environ)
    base_env={**env,"NPY_DISABLE_CPU_FEATURES":",".join(restricted),"OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1"}
    runtime={"platform":platform.platform(),"python":sys.version,"numpy":np.__version__,"baseline":base,"dispatch":dispatch,"enabled":enabled,"restricted":restricted,"environment":{k:env.get(k) for k in ("NPY_DISABLE_CPU_FEATURES","OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","PYTHONHASHSEED")}}
    print("P0B_RUNTIME_JSON "+json.dumps(runtime,sort_keys=True),flush=True)
    np.show_runtime()
    records={}
    for seed,k in MID:
        key=f"{seed}_{k}"
        work=root/key;work.mkdir()
        mid_a=project(load(a_root/key/"epoch_1.nc"),raw[seed],seed,k)
        mid_b=project(load(b_root/key/"owner.nc"),raw[seed],seed,k)
        final_a=project(load(a_root/key/"epoch_2.nc"),raw[seed],seed,k)
        final_b=project(load(b_result/(key+".nc")),raw[seed],seed,k)
        if not(c.hash_owner(mid_a)==c.hash_owner(mid_b)==MID[seed,k] and c.hash_owner(final_a)==REF[seed,k] and c.hash_owner(final_b)==OTHER[seed,k]):raise ValueError("Historical input hash mismatch: "+key)
        src_a,src_b=work/"mid_a.nc",work/"mid_b.nc"
        mid_a.to_netcdf(src_a,engine="scipy");mid_b.to_netcdf(src_b,engine="scipy")
        rec={"checkpoint_comparison":compare(mid_a,mid_b),"historical_final_comparison":compare(final_a,final_b),
             "input_file_bytes_equal":src_a.read_bytes()==src_b.read_bytes(),"runs":{}}
        for name,source in (("a",src_a),("b",src_b)):
            for profile,settings,count in (("native",env,2),("restricted",base_env,2)):
                for rep in range(count):
                    label=f"{name}_{profile}_{rep}"
                    got=run_worker(rawpath,seed,k,source,work/(label+".nc"),settings)
                    rec["runs"][label]={"sha":c.hash_owner(got),"vs_reference":compare(final_a,got),"vs_consumer":compare(final_b,got)}
        records[key]=rec
        concise={"case":key,"historical_final":rec["historical_final_comparison"],"mid_equal":rec["checkpoint_comparison"],"input_file_bytes_equal":rec["input_file_bytes_equal"],"run_hashes":{name:r["sha"] for name,r in rec["runs"].items()}}
        print("WORLD_DIAGNOSTIC_JSON "+json.dumps(concise,sort_keys=True,default=json_value),flush=True)
    data={"experiment":"P0-B-D","runtime":runtime,"cases":records,"status":"diagnostic_only"}
    (root/"result.json").write_text(json.dumps(data,sort_keys=True,indent=2,default=json_value))
if __name__=="__main__":main(*sys.argv[1:])
