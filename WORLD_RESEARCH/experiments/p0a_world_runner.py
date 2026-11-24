"""P0-A finite, headless world runner. H40 consumes requested soil epochs lazily."""
import argparse
import json
import pathlib
import subprocess
import tempfile
import time
import numpy as np
import xarray as xr
import probe_h40_live_body_soil_epochs as h40
import probe_h37_sequential_bullet_contact as h37
import probe_e5_h31_owner_contract as c

REFERENCE={
(7321,0.):("b72798b4faa32c8c2ad912479e411ea010e9378994e4b92748858e8026b80ea0",(
"5899e70ea69d4ac1da274a2020f52a3155e19cc18ded3d15efad53cf694cd7ed",
"4d0b35e0c30abb9d4ace38046535fea4bf3c0e5200e11a2074c05a0c0fef38f0",
"2bb7fe3a72c4805d81fe920f85cc1f940a72bcb48a79cd3c90ba653a69a696a8")),
(7321,.1):("763fc0afab3f7afaa2c23bca2d3a3a523f14c72f48d59380a64962019e70d3b4",(
"ef5cffa37f621af94b90137c809ced3a2dd4d7c1be410a8f3f21cda79cd01f02",
"31c0fa561b3039cfaf4a71a2d9027eb79f6d4fb6c74c48399c59e3625e2e17c2",
"27ad7aaeed0c6938f51aff589c84c25ed47da811162c90e811a54020d6bfd1e6")),
(8128,0.):("f4fe53c9fa67074e95cb93c25b0bab9446bd48eefc338cbdd6ccb85cbc2a9197",(
"9b206cbfe0eadbdff16d317b7ec08e6ed64966328bb7c75a0a09efa5a3b901c2",
"f7db34f7b449ae80e8ff54231599dfb05e4ac920dc2a657cc5dbb2c956f092fe",
"d3afc98df991a5da3554f09a5c857fa8788f25db4635deda71688524e5e956af")),
(8128,.1):("7c844185286eb2e9c1e7c52ba4f68d710089d8304b77e23000354bcd2b624f15",(
"ec2e2d1352bec21895d443b3a70767ec1046c1db82e56ba52e698171654c0a4b",
"0efe55596f8594643ae83b0732987bec1e9dfd637465feea25f420b42e505c9e",
"b26cdc72fcf2cfaedbb0908010256ee3302e6b5f159629c2566332fa8bc609ad"))
}
WORKER=pathlib.Path(__file__).with_name("p0a_landlab_worker.py")
ORDER=["INIT","FIN720","SOIL3","FIN1440","SOIL6","FIN2160"]

class OnDemand:
    def __init__(self,python,rawpath,raw,seed,k,folder):
        self.python=python
        self.rawpath=rawpath
        self.raw=raw
        self.seed=seed
        self.k=k
        self.folder=pathlib.Path(folder)
        self.cache=[]
        self.events=[]
        self.joints=[]
    def __getitem__(self,index):
        if index==0 and self.cache:
            if self.events[-1]["event"]!="INIT":raise ValueError("Unexpected t0 reuse")
            return self.cache[0]
        if index!=len(self.cache) or index not in (0,1,2):
            raise ValueError("Out of sequence request")
        if index and (not self.events or self.events[-1]["event"]!=f"FIN{720*index}"):
            raise ValueError("Soil requested before mechanics boundary")
        target=3*index
        output=self.folder/f"soil_{target}.nc"
        previous="-" if index==0 else str(self.folder/f"soil_{target-3}.nc")
        if output.exists():raise ValueError("Future state present")
        process=subprocess.run([self.python,str(WORKER),str(self.rawpath),str(self.seed),str(self.k),
            previous,str(target),str(output)],capture_output=True,text=True,check=False)
        if process.returncode:
            raise RuntimeError("Landlab worker failed: "+process.stdout+"\n"+process.stderr)
        lines=[line.split("P0_SOIL_JSON ",1)[1] for line in process.stdout.splitlines() if line.startswith("P0_SOIL_JSON ")]
        if len(lines)!=1:raise ValueError("Worker event missing or duplicated")
        event=json.loads(lines[0])
        with xr.open_dataset(output,engine="scipy") as f:ds=f.load()
        c.validate(ds,self.raw,self.seed,self.k)
        expected={"seed":self.seed,"K":self.k,"from":None if not index else target-2,"to":target,
                  "input_sha":None if not index else c.hash_owner(self.cache[-1]),"output_sha":c.hash_owner(ds)}
        if event!=expected or int(ds.attrs["landlab_step"])!=target:raise ValueError("Worker transition mismatch")
        self.cache.append(ds)
        self.events.append({"event":"INIT" if not index else f"SOIL{target}",**event})
        return ds
    def __iter__(self):
        for index in range(3):yield self[index]
    def publish(self,soil,state,seed,steps,original_joint):
        index=len(self.joints)
        if index>=len(self.cache) or steps!=(index+1)*720 or c.hash_owner(soil)!=c.hash_owner(self.cache[index]):
            raise ValueError("Publication out of order")
        joint=original_joint(soil,state,seed,steps)
        self.joints.append(joint.copy(deep=True))
        self.events.append({"event":f"FIN{steps}","owner_sha":c.hash_owner(joint),"bullet_steps":steps})
        return joint

def run_case(python,rawpath,raw,seed,k,output):
    start=time.monotonic()
    failed=[]
    def gate(name,ok):
        if not ok:failed.append(name)
    with tempfile.TemporaryDirectory(prefix="p0a-private-") as folder:
        stream=OnDemand(python,rawpath,raw,seed,k,folder)
        try:stream[1]
        except ValueError:pass
        else:failed.append("premature_request_accepted")
        original=h40.joint
        h40.joint=lambda soil,state,s,steps:stream.publish(soil,state,s,steps,original)
        try:result=h40.run(stream,seed,k)
        finally:h40.joint=original
        gate("event_order",[e["event"] for e in stream.events]==ORDER)
        gate("private_files",sorted(f.name for f in pathlib.Path(folder).iterdir())==["soil_0.nc","soil_3.nc","soil_6.nc"])
        gate("historical_trajectory",result["history_sha"]==REFERENCE[seed,k][0])
        gate("historical_joint_owners",tuple(c.hash_owner(ds) for ds in stream.joints)==REFERENCE[seed,k][1])
        gate("historical_final_soil",c.hash_owner(stream.cache[-1])==h40.EXPECTED[seed,k])
        failed.extend(result["failed"])
        output.mkdir(parents=True,exist_ok=False)
        for i,(joint,soil) in enumerate(zip(stream.joints,stream.cache)):
            path=output/f"epoch_{i}.nc"
            joint.to_netcdf(path,engine="scipy")
            with xr.open_dataset(path,engine="scipy") as f:back=f.load()
            h40.validate_joint(back,soil,seed,720*(i+1))
            gate(f"roundtrip_{i}",c.hash_owner(back)==c.hash_owner(joint))
            bad=joint.copy(deep=True)
            bad["body_mass_kg"].values[0]+=1.
            try:h40.validate_joint(bad,soil,seed,720*(i+1))
            except ValueError:pass
            else:failed.append(f"mass_corruption_{i}_accepted")
            gate(f"original_unchanged_{i}",c.hash_owner(joint)==result["epochs"][i]["owner_sha"])
        record={k:v for k,v in result.items() if k!="owner"}
        record.update(provider_events=stream.events,failed_preregistered_gates=failed,wall_seconds=time.monotonic()-start)
        (output/"manifest.json").write_text(json.dumps(record,indent=2,sort_keys=True,default=h37.np_scalar))
        return record

def main():
    ap=argparse.ArgumentParser(description="P0-A bounded world: two solver clocks; no physical SI mapping")
    ap.add_argument("raw");ap.add_argument("landlab_python");ap.add_argument("out")
    ap.add_argument("--seed",type=int,choices=h40.SEEDS)
    ap.add_argument("--K",type=float,choices=[0.,.1],default=.1)
    args=ap.parse_args()
    raw=h37.read_raw(args.raw)
    root=pathlib.Path(args.out);root.mkdir(parents=True,exist_ok=False)
    cases={}
    fail=[]
    pairs=[(args.seed,args.K)] if args.seed is not None else [(s,k) for s in h40.SEEDS for k in (0.,.1)]
    for seed,k in pairs:
        key=f"{seed}_{k}"
        cases[key]=run_case(args.landlab_python,args.raw,raw[seed],seed,k,root/key)
        fail.extend(key+"_"+x for x in cases[key]["failed_preregistered_gates"])
    if args.seed is None:
        for seed in h40.SEEDS:
            a,b=cases[f"{seed}_0.1"],cases[f"{seed}_0.0"]
            if a["prefix_sha"]!=b["prefix_sha"]:fail.append(f"{seed}_prefix")
            if np.linalg.norm(np.array(a["epochs"][-1]["end_pose"][:3])-np.array(b["epochs"][-1]["end_pose"][:3]))<.01:
                fail.append(f"{seed}_different_final_pose")
        replay=run_case(args.landlab_python,args.raw,raw[7321],7321,.1,root/"replay")
        ref=cases["7321_0.1"]
        if any(replay[key]!=ref[key] for key in ref if key!="wall_seconds"):fail.append("replay")
    result={"experiment":"P0-A","cases":cases,"failed_preregistered_gates":fail,
            "limitations":"Finite nominal benchmark; independent clocks; one-way coupling; no joint restart."}
    (root/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True,default=h37.np_scalar))
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True,default=h37.np_scalar),flush=True)
    if fail:raise AssertionError("P0-A gates: "+str(fail))

if __name__=="__main__":main()
