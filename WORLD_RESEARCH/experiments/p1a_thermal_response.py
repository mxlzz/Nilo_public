"""P1-A: direct-beam absorption and native FiPy conduction on frozen P0-D snapshots."""
import hashlib
import json
import pathlib
import sys
import time
import numpy as np
import pybullet as p
import xarray as xr
from scipy.ndimage import label
from fipy import Grid2D, CellVariable, TransientTerm, DiffusionTerm
from fipy.solvers import LinearLUSolver
import probe_h42_directional_cover as h42
import probe_h40_live_body_soil_epochs as h40
import probe_h41_aggregate_transit as h41
import probe_e5_h31_owner_contract as c
import probe_h37_sequential_bullet_contact as h37
import p0d_granular_world as pd
import p0b_profile_restart as profile
import p0b_joint_restart as b

N=pd.N
CELL=h42.CELL
AREA=CELL**2
CAP=4800.
CP=800.
THICK=.005
DT=10.
STEPS=6
FLUX=600.
XY=h42.XY
REQ=pd.REQ

def ray_map(patch,points):
    """First downward intersection; separate fresh static scene, no solver steps."""
    points=np.asarray(points,dtype=np.float64).reshape(-1,3)
    cid=p.connect(p.DIRECT)
    try:
        ground=h41.make_ground(cid,patch)
        shape=p.createCollisionShape(p.GEOM_SPHERE,radius=pd.R,physicsClientId=cid)
        ids={p.createMultiBody(0.,shape,basePosition=pos.tolist(),physicsClientId=cid):i for i,pos in enumerate(points)}
        base=h42.elevation(patch,XY)+.005
        top=max(float(base.max()),float(points[:,2].max()+pd.R) if len(points) else 0.)+1.
        starts=np.column_stack((XY,np.full(len(XY),top))).tolist()
        ends=np.column_stack((XY,base)).tolist()
        hits=p.rayTestBatch(starts,ends,numThreads=1,physicsClientId=cid)
        REQ(len(hits)==len(XY),"ray result length")
        values=np.asarray([int(h[0]) for h in hits])
        REQ(not np.any(values==ground) and all(x==-1 or x in ids for x in values),"unexpected ray intersection")
        return np.array([ids.get(x,-1) for x in values],dtype=np.int32)
    finally:p.disconnect(physicsClientId=cid)

def instrument(patch):
    center=np.array([40.012,30.009]);z=float(h42.elevation(patch,center))+.3
    hits=ray_map(patch,np.array([[*center,z]]))
    expected=np.linalg.norm(XY-center,axis=1)<pd.R
    REQ(np.array_equal(hits>=0,expected) and expected.any(),"single sphere analytical disk")

def templates(patch):
    result={}
    xy=np.array([[40.+(i-2)*.16,30.+(j-2)*.16] for j in range(5) for i in range(5)])
    result["stack"]=np.concatenate([np.column_stack((xy,h42.elevation(patch,xy)+pd.R+layer*2*pd.R)) for layer in range(5)])
    xy=np.array([[40.+(i-5.5)*.16,30.+(j-5)*.16] for j in range(11) for i in range(12)])[:N]
    xy+=h41.CENTER-xy.mean(axis=0)
    result["monolayer"]=np.column_stack((xy,h42.elevation(patch,xy)+pd.R))
    for pos in result.values():
        REQ(len(pos)==N and h42.min_dist(pos)>=2*pd.R-1e-10,"template overlap")
    return result

def solve(blocked,flux=FLUX,k=1.,start=None,steps=STEPS):
    blocked=np.asarray(blocked,dtype=bool)
    REQ(blocked.shape==(len(XY),),"load shape")
    grid=Grid2D(nx=60,ny=60,dx=CELL,dy=CELL)
    centers=np.asarray(grid.cellCenters).T+np.array([38.5,28.5])
    REQ(np.allclose(centers,XY,rtol=0,atol=1e-12),"FiPy vs ray grid alignment")
    init=np.zeros(len(XY),dtype=np.float64) if start is None else np.asarray(start,dtype=np.float64).copy()
    temp=CellVariable(mesh=grid,value=init/(CAP*AREA))
    load=CellVariable(mesh=grid,value=flux*(~blocked))
    eq=TransientTerm(coeff=CAP)==DiffusionTerm(coeff=k*THICK)+load
    solver=LinearLUSolver(tolerance=1e-10)
    residuals=[]
    for i in range(steps):
        eq.solve(var=temp,dt=DT,solver=solver)
        val=np.asarray(temp.value,dtype=np.float64)
        e=val*CAP*AREA
        expected=float(init.sum())+flux*AREA*int((~blocked).sum())*(i+1)*DT
        residual=float(e.sum())-expected
        REQ(np.isfinite(val).all() and val.min()>=-1e-7 and abs(residual)<=.01,"surface energy budget")
        residuals.append(residual)
    return e.copy(),max(map(abs,residuals),default=0.)

def cold_metrics(energy,bare):
    delta=(bare-energy)/(CAP*AREA)
    mask=delta.reshape(60,60)>=1.
    cc,n=label(mask)
    sizes=np.bincount(cc.ravel())[1:]
    return {"cool_cells":int(mask.sum()),"largest_cool_component":int(sizes.max()) if n else 0,
            "max_deficit_K":float(delta.max()),"mean_deficit_K":float(delta.mean())}

def owner(hits,energy,source_sha,flux,k):
    counts=np.bincount(hits[hits>=0],minlength=N)
    grains=counts.astype(np.float64)*flux*AREA*DT*STEPS
    ds=xr.Dataset({"surface_energy_J":(("ty","tx"),energy.reshape(60,60),{"units":"J"}),
                   "grain_energy_J":(("grain",),grains,{"units":"J"}),
                   "first_hit":(("ty","tx"),hits.reshape(60,60),{"units":"1"})},
                  coords={"ty":np.arange(60,dtype=np.int32),"tx":np.arange(60,dtype=np.int32),"grain":np.arange(N,dtype=np.int32)},
                  attrs={"source_sha":source_sha,"flux_W_m2":float(flux),"k_W_mK":float(k),"thermal_seconds":60.,
                         "capacity_J_m2K":CAP,"cell_area_m2":AREA,"grain_cp_J_kgK":CP,"grain_mass_kg":pd.M,
                         "incident_energy_J":float(flux*AREA*len(XY)*60.)})
    validate(ds,hits,source_sha,flux,k)
    return ds

def validate(ds,hits,source_sha,flux,k):
    REQ(set(ds.data_vars)=={"surface_energy_J","grain_energy_J","first_hit"} and set(ds.coords)=={"ty","tx","grain"},"thermal schema")
    REQ(np.array_equal(ds.ty.values,np.arange(60)) and np.array_equal(ds.tx.values,np.arange(60)) and np.array_equal(ds.grain.values,np.arange(N)),"thermal coords")
    REQ(ds.surface_energy_J.dims==("ty","tx") and ds.grain_energy_J.dims==("grain",) and ds.first_hit.dims==("ty","tx"),"thermal topology")
    REQ(ds.surface_energy_J.attrs=={"units":"J"} and ds.grain_energy_J.attrs=={"units":"J"} and ds.first_hit.attrs=={"units":"1"},"thermal units")
    expected={"source_sha":source_sha,"flux_W_m2":float(flux),"k_W_mK":float(k),"thermal_seconds":60.,"capacity_J_m2K":CAP,"cell_area_m2":AREA,"grain_cp_J_kgK":CP,"grain_mass_kg":pd.M,"incident_energy_J":float(flux*AREA*len(XY)*60.)}
    REQ(dict(ds.attrs)==expected,"thermal metadata")
    REQ(np.array_equal(ds.first_hit.values.ravel(),hits) and np.all((hits>=-1)&(hits<N)),"first hit identity")
    e=ds.surface_energy_J.values;g=ds.grain_energy_J.values
    counts=np.bincount(hits[hits>=0],minlength=N)
    REQ(np.array_equal(g,counts.astype(np.float64)*flux*AREA*DT*STEPS),"grain absorbed energy")
    REQ(np.isfinite(e).all() and e.min()>=-1e-7*CAP*AREA and e.max()<=CAP*AREA*(flux*60./CAP+1e-7),"surface bounds")
    REQ(abs(float(e.sum()+g.sum())-expected["incident_energy_J"])<=.01,"combined energy budget")

def digest(ds):
    h=hashlib.sha256()
    for name in sorted(ds.variables):h.update(name.encode()+ds[name].values.tobytes())
    h.update(json.dumps({k:c.normal(v) for k,v in ds.attrs.items()},sort_keys=True).encode())
    return h.hexdigest()

def run_one(patch,points,sha,path,flux=FLUX,k=1.):
    hits=ray_map(patch,points)
    e,res=solve(hits>=0,flux,k)
    ds=owner(hits,e,sha,flux,k)
    # Grain energy is deposited at the same constant rate each thermal step;
    # per-step combined closure follows from the surface residual measured by solve.
    bad=ds.copy(deep=True);bad.surface_energy_J.values[0,0]+=1.
    try:validate(bad,hits,sha,flux,k)
    except ValueError:pass
    else:raise ValueError("energy corruption accepted")
    ds.to_netcdf(path,engine="scipy")
    back=b.read_owner(path);validate(back,hits,sha,flux,k)
    REQ(digest(back)==digest(ds),"thermal roundtrip")
    return hits,e,{"state_sha":digest(ds),"intercepted_cells":int((hits>=0).sum()),
        "surface_energy_J":float(e.sum()),"grain_energy_J":float(ds.grain_energy_J.sum()),
        "max_balance_residual_J":res,"grain_max_delta_K":float(ds.grain_energy_J.max())/(pd.M*CP)}

def main(rawpath,folder,outdir):
    profile.runtime(sys.executable)
    raw=h37.read_raw(rawpath)
    root=pathlib.Path(folder);out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=False)
    ref=json.loads((root/"result.json").read_text())
    REQ(ref["experiment"]=="P0-D" and ref["mode"]=="produce" and not ref["failed_preregistered_gates"],"source P0-D invalid")
    cases={};fail=[]
    for seed in h40.SEEDS:
        for k in (0.,.1):
            key=f"{seed}_{k}";target=out/key;target.mkdir()
            for epoch in (0,3,6):
                name=f"{key}_epoch{epoch}"
                try:
                    start=time.monotonic()
                    path=root/key/f"epoch_{epoch}.nc"
                    ds=b.read_owner(path);soil=pd.extract_soil(ds);pd.validate(ds,soil,raw[seed],seed,k,epoch)
                    sha=pd.hash_owner(ds,soil);reference=ref["cases"][key]["epochs"][epoch]
                    REQ(sha==reference["owner_sha"] and c.hash_owner(soil)==reference["soil_sha"],"P0-D source digest")
                    points=ds.grain_state.values[:,:3].copy();patch=h40.terrain(soil,seed)
                    instrument(patch)
                    hits,energy,actual=run_one(patch,points,sha,target/f"epoch{epoch}_actual.nc")
                    empty,bare,control=run_one(patch,np.empty((0,3)),sha,target/f"epoch{epoch}_bare.nc")
                    REQ(np.all(empty==-1) and np.max(np.abs(bare/(CAP*AREA)-7.5))<=1e-7,"bare analytical heating")
                    actual.update(cold_metrics(energy,bare))
                    REQ(actual["intercepted_cells"]>0 and actual["largest_cool_component"]>=10,"thermal effect")
                    result={"actual":actual,"bare":control}
                    if k and epoch==6:
                        zero,zero_e,zero_report=run_one(patch,points,sha,target/"zero_flux.nc",flux=0.)
                        REQ(np.array_equal(zero,hits) and np.max(np.abs(zero_e))<=1e-9 and zero_report["grain_energy_J"]==0.,"zero flux")
                        zhits,ze,zrep=run_one(patch,points,sha,target/"zero_k.nc",k=0.)
                        REQ(np.array_equal(zhits,hits) and np.max(np.abs(ze/(CAP*AREA)-7.5*(hits<0)))<=1e-7,"zero conductivity analytic")
                        result["templates"]={}
                        for tag,pos in templates(patch).items():
                            th,te,tr=run_one(patch,pos,sha,target/(tag+".nc"))
                            result["templates"][tag]={**tr,**cold_metrics(te,bare)}
                        rng=np.random.default_rng(2026112400+seed);null=[]
                        for _ in range(32):
                            mask=rng.permutation(hits>=0)
                            REQ(int(mask.sum())==actual["intercepted_cells"],"null dose")
                            ne,nr=solve(mask)
                            REQ(abs(float(ne.sum()-energy.sum()))<=.01,"null energy dose")
                            null.append(cold_metrics(ne,bare)["largest_cool_component"])
                        p95=int(np.quantile(null,.95,method="higher"));observed=actual["largest_cool_component"]
                        rank=(1+sum(x>=observed for x in null))/(1+len(null))
                        result["null"]={"samples":null,"p95":p95,"rank":rank}
                        REQ(observed>=p95+4 and rank<=.05,"dose-matched thermal coherence")
                        if seed==7321:
                            rh,re,rr=run_one(patch,points,sha,target/"replay.nc")
                            REQ(np.array_equal(rh,hits) and np.array_equal(re,energy) and rr["state_sha"]==actual["state_sha"],"thermal replay")
                    REQ(pd.hash_owner(ds,soil)==sha and pd.hash_owner(b.read_owner(path),soil)==sha,"original owner altered")
                    result["wall_seconds"]=time.monotonic()-start
                    cases[name]=result
                    print("P1A_CASE_JSON "+json.dumps({"case":name,**result},sort_keys=True),flush=True)
                except Exception as ex:
                    fail.append(name+": "+str(ex));print("P1A_FAILURE_JSON "+json.dumps({"case":name,"error":str(ex)}),flush=True)
    data={"experiment":"P1-A","cases":cases,"failed_preregistered_gates":fail,"limitations":"Frozen geometry; hypothetical receiving slab; direct irradiation only; not a live world energy owner."}
    b.dump(out/"result.json",data);print("WORLD_EVAL_JSON "+json.dumps(data,sort_keys=True),flush=True)
    if fail:raise AssertionError(str(fail))
if __name__=="__main__":main(*sys.argv[1:])
