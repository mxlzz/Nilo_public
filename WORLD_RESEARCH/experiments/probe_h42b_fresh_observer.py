"""H42b: same preregistered measurements, independent static scene per sample."""
import json
import pathlib
import sys
import probe_h42_directional_cover as h42
import probe_h40_live_body_soil_epochs as h40

OriginalObserver=h42.Observer

class FreshObserver:
    def __init__(self,patch):
        self.patch=patch
    def close(self):
        pass
    def measure(self,points):
        obs=OriginalObserver(self.patch)
        try:return obs.measure(points)
        finally:obs.close()
    def instrument(self):
        obs=OriginalObserver(self.patch)
        try:return obs.instrument()
        finally:obs.close()

def main(folder,out):
    root=pathlib.Path(folder)
    result=json.loads((root/"result.json").read_text())
    for seed in h40.SEEDS:
        ds,soil=h42.load(root,seed,.1,"active",result)
        pos=ds.h41_grain_state.values[:,:3].copy()
        patch=h40.terrain(soil,seed)
        old=OriginalObserver(patch)
        try:
            old_first=old.measure(pos)
            old_repeat=old.measure(pos)
        finally:old.close()
        fresh=FreshObserver(patch)
        a,b=fresh.measure(pos),fresh.measure(pos)
        print("WORLD_DIAGNOSTIC_JSON "+json.dumps({"seed":seed,"old_first":old_first,"old_repeat":old_repeat,
           "fresh_first":a,"fresh_repeat":b,"old_equal":old_first==old_repeat,"fresh_equal":a==b},sort_keys=True),flush=True)
    h42.Observer=FreshObserver
    h42.main(folder,out)

if __name__=="__main__":main(*sys.argv[1:])
