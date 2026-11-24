"""P0-B-R: retain original P0-B gates with a preregistered common CPU profile."""
import json
import os
import pathlib
import platform
import subprocess
import sys
import tempfile
import numpy as np
import xarray as xr
import probe_h40_live_body_soil_epochs as h40
import probe_h37_sequential_bullet_contact as h37
import probe_e5_h31_owner_contract as c
import p0a_world_runner as a
import p0b_joint_restart as b

PROFILE={"NPY_DISABLE_CPU_FEATURES":"X86_V3,X86_V4,AVX512_ICL,AVX512_SPR",
         "OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1"}
NATIVE_REFERENCE=dict(a.REFERENCE)
NATIVE_SOIL=dict(h40.EXPECTED)
CHECK_CODE="""import json,numpy as n
from numpy._core import _multiarray_umath as u
print(json.dumps({"numpy":n.__version__,"baseline":list(u.__cpu_baseline__),"dispatch":list(u.__cpu_dispatch__),"enabled":u.__cpu_features__},sort_keys=True))"""

def runtime(python):
    if any(os.environ.get(k)!=v for k,v in PROFILE.items()):raise ValueError("Unexpected numerical profile environment")
    out=subprocess.check_output([python,"-c",CHECK_CODE],text=True)
    rec=json.loads(out.strip().splitlines()[-1])
    if any(rec["enabled"].get(k,False) for k in PROFILE["NPY_DISABLE_CPU_FEATURES"].split(",") if k in rec["dispatch"]):
        raise ValueError("CPU dispatch restriction not applied")
    return rec

def baseline(rawpath,python,raw,seed,k):
    with tempfile.TemporaryDirectory() as folder:
        stream=a.OnDemand(python,rawpath,raw,seed,k,folder)
        original=h40.joint
        h40.joint=lambda soil,state,s,steps:stream.publish(soil,state,s,steps,original)
        try:result=h40.run(stream,seed,k)
        finally:h40.joint=original
        if result["failed"] or [e["event"] for e in stream.events]!=a.ORDER:raise ValueError("Continuous baseline physics or order failed")
        owners=[]
        for i,(joint,soil) in enumerate(zip(stream.joints,stream.cache)):
            file=pathlib.Path(folder)/f"joint_{i}.nc"
            joint.to_netcdf(file,engine="scipy")
            with xr.open_dataset(file,engine="scipy") as f:back=f.load()
            h40.validate_joint(back,soil,seed,(i+1)*720)
            if c.hash_owner(back)!=c.hash_owner(joint):raise ValueError("Baseline roundtrip")
            owners.append(c.hash_owner(joint))
        ref={"history_sha":result["history_sha"],"prefix_sha":result["prefix_sha"],"owner_shas":owners,
             "soil_sha":c.hash_owner(stream.cache[-1]),"epochs":result["epochs"],"events":result["events"]}
        return ref,[joint.copy(deep=True) for joint in stream.joints]

def set_reference(refs):
    for seed in h40.SEEDS:
        for k in (0.,.1):
            ref=refs[f"{seed}_{k}"]
            a.REFERENCE[seed,k]=(ref["history_sha"],tuple(ref["owner_shas"]))
            h40.EXPECTED[seed,k]=ref["soil_sha"]

def verify_profile(meta):
    if meta.get("profile")!=PROFILE:raise ValueError("Incompatible numerical profile")

def comparison(a_root,seed,k,owners):
    results=[]
    for i,owner in enumerate(owners):
        path=pathlib.Path(a_root)/f"{seed}_{k}"/f"epoch_{i}.nc"
        with xr.open_dataset(path,engine="scipy") as f:old=f.load()
        if c.hash_owner(old)!=NATIVE_REFERENCE[seed,k][1][i]:raise ValueError("Historical owner hash")
        delta=owner.soil_mass_kg.values-old.soil_mass_kg.values
        result={"epoch":i,"historical_sha":c.hash_owner(old),"profile_sha":c.hash_owner(owner),
                "soil_max_abs_kg":float(np.max(np.abs(delta))),"soil_changed_nodes":int(np.count_nonzero(delta)),
                "export_delta_kg":float(owner.attrs["exported_soil_kg"]-old.attrs["exported_soil_kg"]),
                "motion_max_abs":{key:float(np.max(np.abs(owner[key].values-old[key].values))) for key in h40.MOTION}}
        results.append(result)
    return results

def main(mode,rawpath,python,folder,other):
    root=pathlib.Path(folder)
    runtimes={"landlab":runtime(python),"bullet":runtime(sys.executable),
              "machine":platform.machine(),"cpu":next((l.split(":",1)[1].strip() for l in pathlib.Path("/proc/cpuinfo").read_text().splitlines() if l.startswith("model name")),"unknown")}
    print("P0BR_RUNTIME_JSON "+json.dumps(runtimes,sort_keys=True),flush=True)
    if mode=="produce":
        raw=h37.read_raw(rawpath);refs={};comparison_results={}
        for seed in h40.SEEDS:
            for k in (0.,.1):
                key=f"{seed}_{k}"
                refs[key],owners=baseline(rawpath,python,raw[seed],seed,k)
                comparison_results[key]=comparison(other,seed,k,owners)
                if not k and (refs[key]["history_sha"]!=NATIVE_REFERENCE[seed,k][0] or refs[key]["soil_sha"]!=NATIVE_SOIL[seed,k]):raise ValueError("K0 changed under profile")
            active,zero=refs[f"{seed}_0.1"],refs[f"{seed}_0.0"]
            if active["prefix_sha"]!=zero["prefix_sha"]:raise ValueError("Prefix changed between controls")
            if np.linalg.norm(np.array(active["epochs"][-1]["end_pose"][:3])-np.array(zero["epochs"][-1]["end_pose"][:3]))<.01:raise ValueError("Active lacks physical contrast")
        replay,_=baseline(rawpath,python,raw[7321],7321,.1)
        if replay!=refs["7321_0.1"]:raise ValueError("Continuous profile replay mismatch")
        meta={"profile":PROFILE,"references":refs,"historical_comparison":comparison_results,"producer_runtime":runtimes}
        set_reference(refs)
        print("P0BR_REFERENCE_JSON "+json.dumps(meta,sort_keys=True,default=h37.np_scalar),flush=True)
        b.main("produce",rawpath,python,folder)
        (root/"profile_reference.json").write_text(json.dumps(meta,sort_keys=True,indent=2,default=h37.np_scalar))
    elif mode=="consume":
        meta=json.loads((root/"profile_reference.json").read_text())
        verify_profile(meta)
        try:verify_profile({**meta,"profile":{**PROFILE,"OPENBLAS_NUM_THREADS":"2"}})
        except ValueError:pass
        else:raise AssertionError("Incompatible profile was accepted")
        set_reference(meta["references"])
        b.main("consume",rawpath,python,folder,other)
        output=pathlib.Path(other)
        (output/"profile_runtime.json").write_text(json.dumps({"profile":PROFILE,"producer":meta["producer_runtime"],"consumer":runtimes},sort_keys=True,indent=2))
    else:raise ValueError("Mode")
if __name__=="__main__":main(*sys.argv[1:])
