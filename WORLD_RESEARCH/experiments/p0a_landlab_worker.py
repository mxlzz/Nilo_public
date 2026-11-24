"""P0-A Landlab worker, one explicit requested transition; no future states."""
import json
import pathlib
import sys
import xarray as xr
import probe_e6_h33_resume_landlab as h33
import probe_e5_h31_owner_contract as c

def main(rawpath,seed,k,previous,target,output):
    seed=int(seed); k=float(k); target=int(target)
    raw=h33.read_raw(rawpath)[seed]
    out=pathlib.Path(output)
    if out.exists():raise ValueError("Refuse to overwrite completed transition")
    if target==0 and previous=="-":
        owner=h33.initial_owner(raw,seed,k)
        start=None; input_sha=None
    elif target in (3,6) and previous!="-":
        with xr.open_dataset(previous,engine="scipy") as f:old=f.load()
        c.validate(old,raw,seed,k)
        if int(old.attrs["landlab_step"])!=target-3:raise ValueError("Out of sequence")
        input_sha=c.hash_owner(old)
        start=target-2
        owner,metrics=h33.advance(old,raw,seed,k,start,target)
        if metrics["executed_from"]!=start or metrics["executed_to"]!=target:raise ValueError("Range mismatch")
    else:raise ValueError("Unsupported transition")
    c.validate(owner,raw,seed,k)
    tmp=out.with_suffix(".tmp.nc")
    owner.to_netcdf(tmp,engine="scipy")
    with xr.open_dataset(tmp,engine="scipy") as f:back=f.load()
    c.validate(back,raw,seed,k)
    sha=c.hash_owner(owner)
    if c.hash_owner(back)!=sha:raise ValueError("Worker roundtrip failed")
    tmp.replace(out)
    print("P0_SOIL_JSON "+json.dumps({"seed":seed,"K":k,"from":start,"to":target,"input_sha":input_sha,"output_sha":sha},sort_keys=True),flush=True)

if __name__=="__main__":main(*sys.argv[1:])
