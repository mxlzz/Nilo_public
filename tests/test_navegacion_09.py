"""Nilo 0.7/09: rutas, fronteras, progreso y compatibilidad algorítmica."""
from __future__ import annotations
import random
import unittest
from collections import deque
from copy import deepcopy
from unittest.mock import patch

import world
from nilo_runtime.worlds import navigation as nav
from nilo_runtime.worlds.island import DIRS,W,H,tile_key,tile,valid,set_tile,new_world


def baseline_path(w,origin,target,allow_water=False,known_only=False):
    sx,sy,sz=origin;tx,ty,tz=target
    if sz!=tz or not valid(tx,ty) or not (
        tile(w,tx,ty,tz) in nav.PASSABLE or
        (allow_water and tz==0 and tile(w,tx,ty,tz)=='~')):return []
    if known_only and tile_key(tx,ty,tz) not in w.get('revealed',[]):return []
    queue=deque([(sx,sy)]);back={(sx,sy):None}
    while queue:
        x,y=queue.popleft()
        if (x,y)==(tx,ty):
            p=[];cur=(tx,ty)
            while cur!=(sx,sy):
                p.append(cur);cur=back[cur]
            return p[::-1]
        for dx,dy in DIRS:
            nx,ny=x+dx,y+dy
            if ((nx,ny) not in back and
                (not known_only or tile_key(nx,ny,sz) in w.get('revealed',[])) and
                (tile(w,nx,ny,sz) in nav.PASSABLE or
                 (allow_water and sz==0 and tile(w,nx,ny,sz)=='~'))):
                back[(nx,ny)]=(x,y);queue.append((nx,ny))
    return []


def baseline_frontier(w,p,rng):
    x,y,z=p['pos'];known=set(w['revealed']);opts=[]
    for k in w['revealed']:
        tx,ty,tz=map(int,k.split(','))
        if tz!=z or not (nav.passable(w,tx,ty,z) or
            (p.get('vehicle_id') and z==0 and tile(w,tx,ty,z)=='~')):continue
        if not any(tile_key(tx+dx,ty+dy,z) not in known and valid(tx+dx,ty+dy)
                   for dx,dy in DIRS):continue
        route=baseline_path(w,(x,y,z),(tx,ty,z),
                            allow_water=bool(p.get('vehicle_id')),known_only=True)
        if not route and (x,y)!=(tx,ty):continue
        opts.append((len(route)+rng.random()*3+w['visited'].get(k,0)*2,(tx,ty)))
    if not opts:return None
    opts.sort(key=lambda n:n[0])
    return rng.choice(opts[:min(6,len(opts))])[1]


class Navigation09(unittest.TestCase):
    def test_single_owner_and_compatible_api(self):
        for name in ('pathfind','choose_frontier','exploration_frontier','cave_exit',
                     'known_exit_route','reachable_shores','resolve_go','move',
                     'advance_navigation'):
            self.assertIs(getattr(world,name),getattr(nav,name))

    def test_bfs_equal_to_original_four_seeds_two_levels(self):
        for seed in (0,1,42,7321):
            w=new_world(seed)
            for z in (0,-1):
                x,y=(15,10) if z==0 else (23,7)
                if z==-1:
                    w['revealed'].extend(
                        tile_key(xx,yy,z) for xx in range(18,29)
                        for yy in range(3,13))
                for known in (False,True):
                    for water in (False,True):
                        for tx in range(1,W,6):
                            for ty in range(1,H,5):
                                target=(tx,ty,z)
                                self.assertEqual(
                                    nav.pathfind(w,(x,y,z),target,water,known),
                                    baseline_path(w,(x,y,z),target,water,known),
                                    (seed,z,target,water,known))

    def test_unknown_cells_not_used_as_shortcut(self):
        w=new_world(7321);origin=(15,10,0)
        self.assertEqual(nav.pathfind(w,origin,(36,20,0),known_only=True),[])
        self.assertEqual(nav.pathfind(w,origin,(23,7,-1),known_only=True),[])
        for tx,ty in ((15,10),(16,10),(17,10)):
            route=nav.pathfind(w,origin,(tx,ty,0),known_only=True)
            self.assertTrue(all(tile_key(x,y,0) in w['revealed'] for x,y in route))

    def test_frontier_destination_and_rng_equal_legacy(self):
        w=new_world(7321);p={'pos':[15,10,0],'vehicle_id':None}
        for seed in range(40):
            a=random.Random(seed);b=random.Random(seed)
            self.assertEqual(nav.choose_frontier(w,p,a),
                             baseline_frontier(w,p,b))
            self.assertEqual(a.getstate(),b.getstate())

    def test_guided_frontier_uses_known_terrain_and_reachable_route(self):
        w=new_world(7321);p={'pos':[15,10,0],'vehicle_id':None}
        for d in ('north','south','east','west'):
            destination,reason=nav.exploration_frontier(
                w,p,random.Random(2),{'op':'explore','direction':d})
            if destination is None:
                self.assertIn('No encuentro',reason)
            else:
                self.assertIn(tile_key(*destination,0),w['revealed'])
                self.assertIsNotNone(nav.NavigationIndex(
                    w,p['pos'],known_only=True).distance(destination))

    def test_rebuilt_index_not_stale_after_reveal_or_rock(self):
        w=new_world(7321);origin=(15,10,0)
        w['revealed']=[tile_key(*origin)]
        old=nav.NavigationIndex(w,origin,known_only=True)
        self.assertIsNone(old.distance((15,9)))
        w['revealed'].append(tile_key(15,9,0))
        set_tile(w,15,9,0,'.')
        self.assertIsNone(old.distance((15,9)))
        self.assertEqual(nav.NavigationIndex(w,origin,known_only=True).distance((15,9)),1)
        set_tile(w,15,9,0,'#')
        self.assertIsNone(nav.NavigationIndex(w,origin,known_only=True).distance((15,9)))

    def test_known_shores_are_reachable(self):
        w=new_world(7321);p={'pos':[15,10,0],'vehicle_id':None}
        for shore in nav.reachable_shores(w,p):
            self.assertIn(tile_key(*shore['shore'],0),w['revealed'])
            self.assertEqual(len(shore['route']),shore['steps'])
            self.assertTrue(all(tile_key(x,y,0) in w['revealed']
                                for x,y in shore['route']))

    def test_portal_route_only_known_and_no_teleport(self):
        w=new_world(7321);ex,ey=nav.cave_exit(w)
        p={'pos':[ex,ey,-1]}
        w['revealed']=[tile_key(ex,ey,-1)]
        self.assertEqual(nav.known_exit_route(w,p),[])
        p['pos']=[ex+3,ey,-1]
        self.assertIsNone(nav.known_exit_route(w,p))
        for x in range(ex,ex+4):
            set_tile(w,x,ey,-1,':')
            if tile_key(x,ey,-1) not in w['revealed']:
                w['revealed'].append(tile_key(x,ey,-1))
        self.assertEqual(nav.known_exit_route(w,p),[(ex+2,ey),(ex+1,ey),(ex,ey)])

    def test_exploration_without_frontier_is_not_success(self):
        w=new_world(7321)
        w['revealed']=[tile_key(x,y,0) for y in range(H) for x in range(W)]
        p={'pos':[15,10,0],'vehicle_id':None,'inventory':{},'items':[],
           'clock_minutes':0}
        before=deepcopy(w['revealed'])
        _,facts,success,notable=world.execute_action(
            w,p,{'op':'explore'},random.Random(2))
        self.assertFalse(success)
        self.assertFalse(notable)
        self.assertEqual(before,w['revealed'])
        self.assertIn('No encuentro',facts[0])

    def test_one_bfs_per_frontier_selection(self):
        w=new_world(7321);p={'pos':[15,10,0],'vehicle_id':None}
        previous=nav.NavigationIndex;calls=[]
        class Tracked(previous):
            def __init__(self,*args,**kwargs):
                calls.append(True)
                super().__init__(*args,**kwargs)
        with patch.object(nav,'NavigationIndex',Tracked):
            nav.choose_frontier(w,p,random.Random(1))
        self.assertEqual(len(calls),1)

if __name__=='__main__':
    unittest.main()
