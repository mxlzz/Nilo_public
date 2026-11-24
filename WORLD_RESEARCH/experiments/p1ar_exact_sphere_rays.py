"""P1-A-R: validate exact vertical sphere intersection, then reuse original thermal test."""
import json
import math
import pathlib
import sys
import numpy as np
import p1a_thermal_response as a
import probe_h42_directional_cover as h42
import probe_h40_live_body_soil_epochs as h40
import probe_h37_sequential_bullet_contact as h37
import p0d_granular_world as pd
import p0b_joint_restart as b

ORIGINAL=a.ray_map

def exact(patch,points):
    points=np.asarray(points,dtype=np.float64).reshape(-1,3)
    if not len(points):return np.full(len(a.XY),-1,dtype=np.int32)
    delta=a.XY[:,None,:]-points[None,:,:2]
    disc=pd.R**2-np.sum(delta**2,axis=2)
    z=points[None,:,2]+np.sqrt(np.maximum(disc,0.))
    base=h42.elevation(patch,a.XY)+.005
    valid=(disc>=0.)&(z>=base[:,None])
    height=np.where(valid,z,-np.inf)
    first=np.argmax(height,axis=1)
    return np.where(np.any(valid,axis=1),first,-1).astype(np.int32)

def scalar_reference(patch,points):
    # Solve the general ray/sphere quadratic in a sphere-local frame.
    points=np.asarray(points,dtype=np.float64).reshape(-1,3)
    base=h42.elevation(patch,a.XY)+.005
    top=max(float(base.max()),float(points[:,2].max()+pd.R) if len(points) else 0.)+1.
    result=[]
    for (x,y),end in zip(a.XY,base):
        winner=-1;closest=math.inf
        for i,(cx,cy,cz) in enumerate(points):
            dx=float(x-cx);dy=float(y-cy);dz=float(top-cz)
            # For direction (0,0,-1), use the algebraically reduced
            # discriminant to avoid subtracting two large vertical terms.
            discriminant=math.fsum((pd.R**2,-dx*dx,-dy*dy))
            if discriminant<0.:continue
            t=dz-math.sqrt(discriminant)
            if 0.<=t<=top-end and t<closest:
                winner=i;closest=t
        result.append(winner)
    return np.asarray(result,dtype=np.int32)

def checked(patch,points):
    v=exact(patch,points);s=scalar_reference(patch,points)
    a.REQ(np.array_equal(v,s),"analytical instrument/reference disagree")
    return v

def diagnostic(rawpath,folder):
    raw=h37.read_raw(rawpath);root=pathlib.Path(folder)
    ref=json.loads((root/"result.json").read_text())
    data={};original_failed=False
    for seed in h40.SEEDS:
        for epoch in (0,6):
            key=f"{seed}_0.1"
            ds=b.read_owner(root/key/f"epoch_{epoch}.nc")
            soil=pd.extract_soil(ds);pd.validate(ds,soil,raw[seed],seed,.1,epoch)
            a.REQ(pd.hash_owner(ds,soil)==ref["cases"][key]["epochs"][epoch]["owner_sha"],"diagnostic source")
            patch=h40.terrain(soil,seed)
            center=np.array([40.012,30.009]);z=float(h42.elevation(patch,center))+.3
            sphere=np.array([[*center,z]])
            expected=np.linalg.norm(a.XY-center,axis=1)<pd.R
            orig=ORIGINAL(patch,sphere);analytic=checked(patch,sphere)
            a.REQ(np.array_equal(analytic>=0,expected) and expected.any(),"analytic disk")
            mismatch=np.flatnonzero((orig>=0)!=expected)
            original_failed=original_failed or bool(len(mismatch))
            a.REQ(np.all(ORIGINAL(patch,np.empty((0,3)))==-1),"original bare")
            a.REQ(np.all(checked(patch,np.empty((0,3)))==-1),"analytic bare")
            upper=checked(patch,np.array([[*center,z],[*center,z+.2]]))
            a.REQ(np.array_equal(upper>=0,expected) and np.all(upper[expected]==1),"first upper hit")
            below=checked(patch,np.array([[*center,z-1.]]))
            a.REQ(np.all(below==-1),"sphere below receiver")
            other=center+np.array([.35,0.]);otherz=float(h42.elevation(patch,other))+.3
            twin=checked(patch,np.array([[*center,z],[*other,otherz]]))
            a.REQ(np.array_equal(twin==0,expected) and np.array_equal(twin==1,np.linalg.norm(a.XY-other,axis=1)<pd.R),"disjoint disks")
            points=ds.grain_state.values[:,:3].copy()
            actual_orig=ORIGINAL(patch,points);actual_exact=checked(patch,points)
            item={"seed":seed,"epoch":epoch,"expected_disk":int(expected.sum()),"original_disk":int((orig>=0).sum()),
                "analytic_disk":int((analytic>=0).sum()),"mismatch":[{"xy":a.XY[i].tolist(),"distance":float(np.linalg.norm(a.XY[i]-center)),"bullet":int(orig[i]),"expected":bool(expected[i])} for i in mismatch],
                "actual_original_occluded":int((actual_orig>=0).sum()),"actual_analytic_occluded":int((actual_exact>=0).sum()),
                "actual_mask_difference":int(np.count_nonzero((actual_orig>=0)!=(actual_exact>=0))),
                "actual_first_id_difference":int(np.count_nonzero(actual_orig!=actual_exact))}
            data[f"{seed}_{epoch}"]=item
            print("P1A_R_DIAGNOSTIC_JSON "+json.dumps(item,sort_keys=True),flush=True)
    a.REQ(original_failed,"original failure not reproduced: no instrument substitution")
    return data

def main(rawpath,folder,outdir):
    data=diagnostic(rawpath,folder)
    path=pathlib.Path(outdir).with_name("p1ar-diagnosis.json")
    path.write_text(json.dumps(data,indent=2,sort_keys=True))
    # Replace ONLY the geometric measurement in the original harness.
    # Thermal PDE, control cases, protocol and thresholds remain intact.
    a.ray_map=checked
    a.main(rawpath,folder,outdir)
if __name__=="__main__":main(*sys.argv[1:])
