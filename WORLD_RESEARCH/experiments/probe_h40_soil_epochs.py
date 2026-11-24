"""H40 native Landlab checkpoints t0, t3, t6 for the one-way contact experiment."""
import json
import pathlib
import sys
import xarray as xr
import probe_h37_extended_landlab_producer as h37
import probe_e6_h33_resume_landlab as h33
import probe_e5_h31_owner_contract as c

def main(rawpath,outdir):
    h37.run(rawpath,outdir)
    out=pathlib.Path(outdir)
    raw=h33.read_raw(rawpath)
    manifest=json.loads((out/"manifest.json").read_text())
    for name,(seed,k) in zip((*h33.NAMES,"seed8128_zero_K"),(*h33.CASES,(8128,0.))):
        state=h33.initial_owner(raw[seed],seed,k)
        c.validate(state,raw[seed],seed,k)
        path=out/f"{name}_initial.nc"
        state.to_netcdf(path,engine="scipy")
        with xr.open_dataset(path,engine="scipy") as f:back=f.load()
        c.validate(back,raw[seed],seed,k)
        if c.hash_owner(state)!=c.hash_owner(back):raise ValueError("t0 roundtrip changed")
        manifest["cases"][name]["initial_sha256"]=c.hash_owner(state)
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print("H40 source/checkpoints validated for four cases",flush=True)
if __name__=="__main__":main(*sys.argv[1:])
