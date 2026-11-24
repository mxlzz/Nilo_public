"""H42 static directional exposure on retained H41 owners. No time steps."""
import hashlib
import json
import pathlib
import sys
import numpy as np
import pybullet as p
import xarray as xr
from scipy.ndimage import label
import probe_h41_aggregate_transit as h41
import probe_h40_live_body_soil_epochs as h40
import probe_e5_h31_owner_contract as c

CENTER=np.array([40.,30.])
R=.075
MIN=.13
CELL=.05
DIRS=np.array([[0.,0.,1.],[1.,0.,1.],[-1.,0.,1.],[0.,1.,1.],[0.,-1.,1.]])
CHAIN_SEEDS={7321:(2026114201,2026114202),8128:(2026114211,2026114212)}
BURN=20000
BETWEEN=2000
SAMPLES=64
XY=np.stack(np.meshgrid(38.5+(np.arange(60)+.5)*CELL,28.5+(np.arange(60)+.5)*CELL),axis=-1).reshape(-1,2)

def elevation(patch,xy):
    u=xy[...,0]/c.DX
    v=xy[...,1]/c.DX
    a,b,z,d=patch[0,0],patch[0,1],patch[1,1],patch[1,0]
    return np.where(u>=v,(1-u)*a+(u-v)*b+v*z,(1-v)*a+u*z+(v-u)*d)

def min_dist(pos):
    dist=np.linalg.norm(pos[:,None]-pos[None,:],axis=2)
    np.fill_diagonal(dist,np.inf)
    return float(dist.min())

def load(root,seed,k,mode,results):
    key=f"{seed}_{k}_{mode}"
    with xr.open_dataset(root/(key+".nc"),engine="scipy") as f:ds=f.load()
    record=results["cases"][str((seed,k,mode))]
    if record["failed"]:raise ValueError("H41 case failed integrity: "+key)
    soil=ds.drop_vars([v for v in ds.variables if v.startswith("h41_")])
    soil.attrs={key:val for key,val in soil.attrs.items() if not key.startswith("h41_")}
    if c.hash_owner(soil)!=h40.EXPECTED[seed,k]:raise ValueError("H40 soil hash")
    if int(soil.attrs["landlab_step"])!=6:raise ValueError("Not t6")
    h41.validate_owner(ds,soil,mode,int(ds.attrs["h41_bullet_steps"]))
    if h41.owner_hash(ds,soil)!=record["owner_sha"]:raise ValueError("H41 owner hash")
    return ds,soil

class Observer:
    def __init__(self,patch):
        self.cid=p.connect(p.DIRECT)
        self.ground=h41.make_ground(self.cid,patch)
        self.patch=patch
        self.shape=p.createCollisionShape(p.GEOM_SPHERE,radius=R,physicsClientId=self.cid)
        self.grains=[]
        origins=np.column_stack((XY,elevation(patch,XY)+.005))
        self.starts=origins.tolist()
        self.ends=[(origins+5*d).tolist() for d in DIRS]
    def close(self):p.disconnect(physicsClientId=self.cid)
    def place(self,points):
        if len(self.grains)!=len(points):
            for body in self.grains:p.removeBody(body,physicsClientId=self.cid)
            self.grains=[p.createMultiBody(0.,self.shape,basePosition=xyz.tolist(),physicsClientId=self.cid) for xyz in points]
        else:
            for body,xyz in zip(self.grains,points):
                p.resetBasePositionAndOrientation(body,xyz.tolist(),[0,0,0,1],physicsClientId=self.cid)
    def measure(self,points):
        self.place(points)
        ids=set(self.grains)
        masks=[]
        terrain_counts=[]
        for ends in self.ends:
            hits=p.rayTestBatch(self.starts,ends,numThreads=1,physicsClientId=self.cid)
            obj=np.array([x[0] for x in hits])
            masks.append(np.isin(obj,list(ids)))
            terrain_counts.append(int(np.count_nonzero(obj==self.ground)))
        both=np.logical_and.reduce(masks).reshape(60,60)
        cc,n=label(both)
        sizes=np.bincount(cc.ravel())[1:]
        return {"connected_cells":int(sizes.max()) if n else 0,"protected_cells":int(both.sum()),
                "direction_cells":[int(v.sum()) for v in masks],"terrain_hits":terrain_counts}
    def instrument(self):
        z=float(elevation(self.patch,CENTER))
        self.place(np.array([[40.,30.,z+.3]]))
        hits=p.rayTestBatch([[40.,30.,z+.005],[40.3,30.,float(elevation(self.patch,np.array([40.3,30.])))+.005]],
                            [[40.,30.,z+5],[40.3,30.,z+5]],physicsClientId=self.cid)
        return hits[0][0]==self.grains[0] and hits[1][0]==-1

def chain(pos,patch,seed,obs):
    xy=pos[:,:2]-CENTER
    init=xy.copy()
    rel=pos[:,2]-elevation(patch,pos[:,:2])
    current=pos.copy()
    radii=np.linalg.norm(init,axis=1)
    median=float(np.median(radii))
    maximum=float(radii.max())
    band=radii>median
    low=np.where(band,median,0.)
    high=np.where(band,maximum,median)
    rng=np.random.default_rng(seed)
    samples=[]
    accepted=0
    lowest=float("inf")
    total=BURN+BETWEEN*SAMPLES
    for i in range(1,total+1):
        j=int(rng.integers(len(pos)))
        if rng.random()<.8:
            proposal=xy[j]+rng.normal(0.,.05,2)
        else:
            angle=rng.uniform(0.,2*np.pi)
            rr=np.sqrt(rng.uniform(low[j]**2,high[j]**2))
            proposal=rr*np.array([np.cos(angle),np.sin(angle)])
        radius=np.linalg.norm(proposal)
        world=proposal+CENTER
        if low[j]<=radius<=high[j] and np.all((world>2)&(world<98)):
            candidate=np.r_[world,float(elevation(patch,world))+rel[j]]
            dist=np.linalg.norm(current-candidate,axis=1)
            dist[j]=np.inf
            if np.all(dist>=MIN):
                xy[j]=proposal
                current[j]=candidate
                accepted+=1
        if i>BURN and (i-BURN)%BETWEEN==0:
            dd=min_dist(current)
            lowest=min(lowest,dd)
            if dd<MIN-1e-12 or not np.array_equal(np.linalg.norm(xy,axis=1)>median,band) or np.max(np.abs(current[:,2]-elevation(patch,current[:,:2])-rel))>1e-10:
                raise ValueError("Null invariant")
            m=obs.measure(current)
            samples.append(m)
    return {"seed":seed,"acceptance":accepted/total,"mobility":float(np.mean(np.linalg.norm(xy-init,axis=1)>R)),"min_dist":lowest,"samples":samples}

def main(folder,out):
    root=pathlib.Path(folder)
    result=json.loads((root/"result.json").read_text())
    if result["experiment"]!="H41":raise ValueError("Wrong source")
    failed=[]
    cases={}
    def gate(name,ok):
        if not ok:failed.append(name)
    for seed in h40.SEEDS:
        for k in (0.,.1):
            key=f"{seed}_{k}"
            ds,soil=load(root,seed,k,"active",result)
            control,control_soil=load(root,seed,k,"terrain",result)
            gate(key+"_same_soil",c.hash_owner(control_soil)==c.hash_owner(soil))
            sha=h41.owner_hash(ds,soil)
            pos=ds.h41_grain_state.values[:,:3].copy()
            patch=h40.terrain(soil,seed)
            obs=Observer(patch)
            try:
                gate(key+"_instrument",obs.instrument())
                empty=obs.measure(np.empty((0,3)))
                gate(key+"_empty",not any(empty["direction_cells"]) and not any(empty["terrain_hits"]))
                actual=obs.measure(pos)
                gate(key+"_repeat",actual==obs.measure(pos))
                entry={"actual":actual,"empty":empty,"source_sha":sha,"initial_min_distance":min_dist(pos),"chains":[]}
                if k:
                    if min_dist(pos)<MIN-1e-12:
                        failed.append(key+"_invalid_initial_null")
                    else:
                        chains=[chain(pos,patch,s,obs) for s in CHAIN_SEEDS[seed]]
                        entry["chains"]=chains
                        vals=np.array([m["connected_cells"] for ch in chains for m in ch["samples"]])
                        observed=actual["connected_cells"]
                        p95=int(np.quantile(vals,.95,method="higher"))
                        rank=(1+int(np.count_nonzero(vals>=observed)))/(1+len(vals))
                        diff=abs(np.mean([m["connected_cells"] for m in chains[0]["samples"]])-np.mean([m["connected_cells"] for m in chains[1]["samples"]]))*CELL**2
                        gate(key+"_chains",all(ch["acceptance"]>.01 and ch["mobility"]>.5 and len(ch["samples"])==SAMPLES for ch in chains) and diff<=.025)
                        gate(key+"_function",observed*CELL**2>=.025-1e-12 and (observed-p95)*CELL**2>=.01-1e-12 and rank<=.05)
                        entry.update(null_p95_cells=p95,rank=rank,chain_mean_area_difference=diff)
                gate(key+"_owner_unchanged",h41.owner_hash(ds,soil)==sha)
                cases[key]=entry
                print("WORLD_CASE_JSON "+json.dumps({"case":key,**{a:b for a,b in entry.items() if a!="chains"}},sort_keys=True),flush=True)
            finally:obs.close()
    data={"experiment":"H42","cell_area":CELL**2,"cases":cases,"failed_preregistered_gates":failed}
    path=pathlib.Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,sort_keys=True))
    compact={**data,"cases":{k:{**v,"chains":[{a:b for a,b in ch.items() if a!="samples"} for ch in v["chains"]]} for k,v in cases.items()}}
    print("WORLD_EVAL_JSON "+json.dumps(compact,sort_keys=True),flush=True)
    if failed:raise AssertionError("H42 gates: "+str(failed))

if __name__=="__main__":main(*sys.argv[1:])
