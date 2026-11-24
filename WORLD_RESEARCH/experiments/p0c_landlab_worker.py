"""P0-C worker: strictly ordered finite-horizon requests to the existing H33 solver."""
import pathlib
import sys
import json
import xarray as xr
import probe_e6_h33_resume_landlab as h33
import probe_e5_h31_owner_contract as c
HORIZON=18

def main(rawpath,seed,k,previous,target,output):
    seed=int(seed);k=float(k);target=int(target)
    raw=h33.read_raw(rawpath)[seed];out=pathlib.Path(output)
    if out.exists() or target not in range(0,HORIZON+1,3):raise ValueError("Invalid request")
    if target==0:
        if previous!="-":raise ValueError("Unexpected predecessor")
        owner=h33.initial_owner(raw,seed,k)
        input_sha=None;first=None;residual=0.
    else:
        with xr.open_dataset(previous,engine="scipy") as f:old=f.load()
        c.validate(old,raw,seed,k,max_step=HORIZON)
        if int(old.attrs["landlab_step"])!=target-3:raise ValueError("Wrong predecessor")
        input_sha=c.hash_owner(old);first=target-2
        owner,metrics=h33.advance(old,raw,seed,k,first,target,max_step=HORIZON)
        if (metrics["executed_from"],metrics["executed_to"])!=(first,target):raise ValueError("Wrong advance")
        residual=metrics["max_abs_mass_error_kg"]
    c.validate(owner,raw,seed,k,max_step=HORIZON)
    sha=c.hash_owner(owner)
    tmp=out.with_suffix(".tmp.nc");owner.to_netcdf(tmp,engine="scipy")
    with xr.open_dataset(tmp,engine="scipy") as f:back=f.load()
    c.validate(back,raw,seed,k,max_step=HORIZON)
    if c.hash_owner(back)!=sha:raise ValueError("Roundtrip")
    tmp.replace(out)
    print("P0C_SOIL_JSON "+json.dumps({"seed":seed,"K":k,"from":first,"to":target,"input_sha":input_sha,"output_sha":sha,"max_residual_kg":residual},sort_keys=True),flush=True)

if __name__=="__main__":main(*sys.argv[1:])
