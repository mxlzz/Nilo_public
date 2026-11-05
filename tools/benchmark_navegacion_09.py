"""Comparación empírica de navegación 0.7/09 con BFS literal de 0.6.4.

Mide selección de frontera en mapa conocido artificial denso. No cambia
generación de mundos ni partidas y compara destino + estado RNG en cada seed.
"""
from __future__ import annotations
from collections import deque
import json
import random
import time
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from nilo_runtime.worlds.island import DIRS,PASSABLE,valid,tile_key,tile,set_tile,new_world
from nilo_runtime.worlds.navigation import choose_frontier,passable


def legacy_path(w,origin,target,known_only=True):
    sx,sy,sz=origin;tx,ty,tz=target
    if sz!=tz or not valid(tx,ty) or not passable(w,tx,ty,tz):
        return []
    if known_only and tile_key(tx,ty,tz) not in w['revealed']:return []
    queue=deque([(sx,sy)])
    back={(sx,sy):None}
    while queue:
        x,y=queue.popleft()
        if (x,y)==(tx,ty):
            result=[];current=(tx,ty)
            while current!=(sx,sy):
                result.append(current);current=back[current]
            return result[::-1]
        for dx,dy in DIRS:
            nx,ny=x+dx,y+dy
            if ((nx,ny) not in back and
                (not known_only or tile_key(nx,ny,sz) in w['revealed']) and
                tile(w,nx,ny,sz) in PASSABLE):
                back[(nx,ny)]=(x,y)
                queue.append((nx,ny))
    return []


def legacy_frontier(w,p,rng):
    x,y,z=p['pos'];known=set(w['revealed']);options=[]
    for k in w['revealed']:
        tx,ty,tz=map(int,k.split(','))
        if tz!=z or not passable(w,tx,ty,z):continue
        if not any(valid(tx+dx,ty+dy) and tile_key(tx+dx,ty+dy,z) not in known
                   for dx,dy in DIRS):continue
        route=legacy_path(w,(x,y,z),(tx,ty,z))
        if not route and (x,y)!=(tx,ty):continue
        options.append((len(route)+rng.random()*3+w['visited'].get(k,0)*2,(tx,ty)))
    if not options:return None
    options.sort(key=lambda v:v[0])
    return rng.choice(options[:min(6,len(options))])[1]


def run(samples=4):
    world=new_world(7321)
    for y in range(6,15):
        for x in range(7,27):
            set_tile(world,x,y,0,'.')
    world['revealed']=[tile_key(x,y,0)
                       for y in range(6,15) for x in range(7,27)]
    person={'pos':[15,10,0],'vehicle_id':None}
    starts=range(samples)
    t0=time.perf_counter()
    old=[]
    for seed in starts:
        rng=random.Random(seed)
        old.append((legacy_frontier(world,person,rng),rng.getstate()))
    t1=time.perf_counter()
    new=[]
    for seed in starts:
        rng=random.Random(seed)
        new.append((choose_frontier(world,person,rng),rng.getstate()))
    t2=time.perf_counter()
    if old!=new:
        raise AssertionError('Selección o consumo RNG difieren de la referencia')
    return {
        'test':'frontier_bfs_legacy_vs_indexed',
        'known_cells':len(world['revealed']),
        'samples':samples,
        'legacy_ms':round((t1-t0)*1000,3),
        'indexed_ms':round((t2-t1)*1000,3),
        'speedup':round((t1-t0)/max(1e-12,t2-t1),2),
        'destinations_and_rng_identical':True,
        'note':'Medición local al runner; no equivale a mejora de autonomía con LLM.'
    }

if __name__=='__main__':
    print(json.dumps(run(),indent=2,ensure_ascii=False))
