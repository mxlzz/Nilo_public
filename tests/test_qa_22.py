"""Nilo 0.7 etapa 22: QA transversal y pruebas metamórficas del motor real.

Las semillas y los cronogramas se fijan explícitamente. No hay red, LLM,
partidas personales ni umbrales de tiempo dependientes del runner.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from nilo import Simulation
from nilo_runtime.core.state import validate_current_state
from nilo_runtime.worlds.island import (
    W, H, DIRS, PASSABLE, new_world, set_tile, tile, tile_key, valid,
    validate_generated_world,
)
from nilo_runtime.worlds.navigation import pathfind, resolve_go, choose_frontier
from nilo_runtime.worlds.resources import transfer_units
from nilo_runtime.physiology.needs import update_needs, NEEDS_DEFAULT
from nilo_runtime.storage.backups import backup_to_new_path, inspect_backup


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",",":"), default=str)


def known_bfs(world, start, target):
    """Referencia BFS independiente, únicamente sobre celdas descubiertas."""
    x,y,z=start
    tx,ty,tz=target
    if z!=tz or not valid(tx,ty):
        return []
    known=set(world.get("revealed",()))
    if tile_key(tx,ty,z) not in known or tile(world,tx,ty,z) not in PASSABLE:
        return []
    seen={(x,y):None}
    queue=deque([(x,y)])
    while queue:
        cx,cy=queue.popleft()
        if (cx,cy)==(tx,ty):
            path=[]
            current=(tx,ty)
            while seen[current] is not None:
                path.append(current)
                current=seen[current]
            return list(reversed(path))
        for dx,dy in DIRS:
            nx,ny=cx+dx,cy+dy
            if ((nx,ny) not in seen and valid(nx,ny)
                    and tile_key(nx,ny,z) in known
                    and tile(world,nx,ny,z) in PASSABLE):
                seen[(nx,ny)]=(cx,cy)
                queue.append((nx,ny))
    return []


class GeneratedWorldProperties22(unittest.TestCase):
    def test_topology_and_serialized_generation_32_seeds(self):
        for seed in range(32):
            with self.subTest(seed=seed):
                a=new_world(seed)
                validate_generated_world(a)
                self.assertEqual(encoded(a),encoded(new_world(seed)))
                self.assertTrue(a.get("revealed"))
                self.assertEqual(a["seed"],seed)

    def test_generated_world_does_not_consume_global_rng(self):
        saved=random.getstate()
        try:
            for seed in (0,1,7,23,7321,100000):
                with self.subTest(seed=seed):
                    random.seed(98371)
                    before=random.getstate()
                    new_world(seed)
                    self.assertEqual(random.getstate(),before)
        finally:
            random.setstate(saved)

    def test_known_routes_match_independent_bfs_16_seeds(self):
        for seed in range(16):
            w=new_world(seed)
            origin=(15,10,0)
            targets=[]
            for k in w["revealed"]:
                x,y,z=map(int,k.split(","))
                if z==0 and tile(w,x,y,0) in PASSABLE:
                    targets.append((x,y,z))
            for target in targets[:12]:
                with self.subTest(seed=seed,target=target):
                    actual=pathfind(w,origin,target,known_only=True)
                    expected=known_bfs(w,origin,target)
                    self.assertEqual(actual,expected)
                    self.assertTrue(all(tile_key(x,y,0) in w["revealed"]
                                        for x,y in actual))

    def test_hidden_changes_cannot_affect_known_route_or_frontier(self):
        for seed in (0,4,12,7321):
            w=new_world(seed)
            set_tile(w,16,10,0,".")
            if tile_key(16,10,0) not in w["revealed"]:
                w["revealed"].append(tile_key(16,10,0))
            before_path=pathfind(w,(15,10,0),(16,10,0),known_only=True)
            changed=deepcopy(w)
            known=set(w["revealed"])
            hidden=next(( (x,y) for x in range(1,W-1) for y in range(1,H-1)
                          if tile_key(x,y,0) not in known),None)
            self.assertIsNotNone(hidden)
            set_tile(changed,*hidden,0,"^")
            self.assertEqual(pathfind(changed,(15,10,0),(16,10,0),
                                      known_only=True),before_path)
            actor={"pos":[15,10,0],"vehicle_id":None}
            for rseed in (5,9,12):
                r1=random.Random(rseed)
                r2=random.Random(rseed)
                self.assertEqual(choose_frontier(w,actor,r1),
                                 choose_frontier(changed,actor,r2))
                self.assertEqual(r1.getstate(),r2.getstate())

    def test_invalid_coordinates_rejected_without_mutating_world(self):
        w=new_world(7321)
        person={"pos":[15,10,0],"vehicle_id":None}
        before=encoded(w),encoded(person)
        bad=((float("inf"),10),(10,float("-inf")),
             (float("nan"),10),(10,None),(True,10),(False,10),
             (10,True),([],10),("1e999",10))
        for x,y in bad:
            with self.subTest(x=x,y=y):
                destination,water,why=resolve_go(w,person,
                                                  {"op":"go","x":x,"y":y})
                self.assertIsNone(destination)
                self.assertIsNone(water)
                self.assertIn("coordenadas",why)
                self.assertEqual((encoded(w),encoded(person)),before)

    def test_seeded_resource_transfer_conserves_stock_100_cases(self):
        for seed in range(100):
            rng=random.Random(seed)
            available=rng.randrange(1,30)
            carried=rng.randrange(30)
            qty=rng.randrange(1,available+1)
            source={"stock":available}
            inventory={"recurso":carried}
            balance=available+carried
            receipt=transfer_units(source,"stock",inventory,"recurso",qty)
            self.assertEqual(source["stock"]+inventory["recurso"],balance)
            self.assertEqual(receipt.quantity,qty)
            self.assertGreaterEqual(source["stock"],0)


class PhysiologyProperties22(unittest.TestCase):
    def test_no_nonfinite_or_out_of_bounds_needs_25_runs(self):
        for seed in range(25):
            rng=random.Random(seed)
            actor={"clock_minutes":0.0,
                   "needs":{key:float(rng.randrange(15,101))
                            for key in NEEDS_DEFAULT}}
            for i in range(40):
                duration=rng.choice((0.5,2,10,20,60,120))
                update_needs(actor,{},duration,at_shelter=(i%2==0),
                             active=(i%3==0),resting=(i%3==1))
                actor["clock_minutes"]+=duration
                self.assertTrue(all(0<=float(v)<=100
                                    for v in actor["needs"].values()))

    def test_negative_or_invalid_elapsed_never_changes_reserves(self):
        for value in (float("nan"),float("inf"),True,"12"):
            actor={"needs":dict(NEEDS_DEFAULT)}
            before=deepcopy(actor)
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    update_needs(actor,{},value)
                self.assertEqual(actor,before)

    def test_no_spontaneous_eating_or_drinking_without_delegation(self):
        actor={"clock_minutes":0.0,"inventory":{"alimento":5},
               "needs":{"nutricion":30,"hidratacion":25,"energia":65,
                        "abrigo":80,"seguridad":70}}
        before=actor["inventory"].copy()
        for i in range(40):
            update_needs(actor,{},120)
        self.assertEqual(actor["inventory"],before)


class WholeEngineProperties22(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="nilo-qa-22-")
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)
        self.sim=self.simulation("live.sqlite3")

    def simulation(self,name,seed=7321):
        obj=Simulation(db_path=self.path/name,world_seed=seed,rng_seed=9821)
        obj.think=lambda:None
        obj.s["paused"]=False
        obj.s["speed"]=60
        obj.s["auto_wait_frozen"]=False
        obj.s["mode"]="demo"
        self.addCleanup(obj.conn.close)
        return obj

    def test_clock_fragmentation_preserves_physics_across_8_seeds(self):
        for seed in range(8):
            single=self.simulation(f"single-{seed}.sqlite3",seed)
            split=self.simulation(f"split-{seed}.sqlite3",seed)
            single.tick(10)
            split.tick(4)
            split.tick(6)
            a,b=single.s["person"],split.s["person"]
            self.assertAlmostEqual(a["clock_minutes"],b["clock_minutes"],places=8)
            self.assertEqual(a["pos"],b["pos"])
            self.assertEqual(a["inventory"],b["inventory"])
            self.assertEqual(a["needs"],b["needs"])

    def test_pause_freezes_clock_and_random_state(self):
        sim=self.sim
        sim.s["paused"]=True
        state=encoded(sim.s)
        rng=sim.rng.getstate()
        sim.tick(20)
        self.assertEqual(encoded(sim.s),state)
        self.assertEqual(sim.rng.getstate(),rng)

    def test_read_projections_do_not_mutate_state_or_db(self):
        sim=self.sim
        sim.s["journal"].extend([
            {"id":f"qa-nota-{i}","when":"Día 1","text":f"Nota física {i}"}
            for i in range(150)])
        sim.write()
        before=encoded(sim.s)
        rng=sim.rng.getstate()
        total=sim.conn.total_changes
        for _ in range(12):
            sim.public_state()
            sim.domain_snapshot()
            sim.archive.recent("journal",5)
        self.assertEqual(encoded(sim.s),before)
        self.assertEqual(sim.rng.getstate(),rng)
        self.assertEqual(sim.conn.total_changes,total)

    def test_history_append_vs_batch_keeps_ids_and_order(self):
        all_records=[
            {"id":f"qa-entry-{i:04d}","when":"Día 2",
             "text":f"Observación {i} sin atribución no verificada"}
            for i in range(400)]
        batch=self.simulation("batch.sqlite3")
        batch.s["journal"].extend(deepcopy(all_records))
        batch.write()
        seq=self.simulation("segments.sqlite3")
        for first in range(0,len(all_records),40):
            seq.s["journal"].extend(deepcopy(all_records[first:first+40]))
            seq.write()
        def ids(sim):
            return [r[0] for r in sim.conn.execute(
                "SELECT item_id FROM history WHERE category='journal' "
                "AND item_id LIKE 'qa-entry-%' ORDER BY seq")]
        expected=[x["id"] for x in all_records]
        self.assertEqual(ids(batch),expected)
        self.assertEqual(ids(seq),expected)
        self.assertEqual(ids(batch),ids(seq))

    def test_mid_sync_failure_rolls_back_history_and_cache(self):
        sim=self.sim
        sim.s["journal"].append(
            {"id":"qa-mid-sync-failed","when":"Día 1","text":"Observación"})
        old_digest=dict(sim.archive._sync_digest)
        old_seen=set(sim.archive._sync_seen_static)
        sync=sim.archive.sync
        def after_write(state):
            sync(state)
            raise RuntimeError("fallo simulado después del archivo")
        with patch.object(sim.archive,"sync",side_effect=after_write):
            with self.assertRaisesRegex(RuntimeError,"fallo simulado"):
                sim.write()
        self.assertEqual(sim.archive._sync_digest,old_digest)
        self.assertEqual(sim.archive._sync_seen_static,old_seen)
        self.assertEqual(sim.conn.execute(
            "SELECT COUNT(*) FROM history WHERE item_id='qa-mid-sync-failed'"
            ).fetchone()[0],0)
        sim.write()
        self.assertEqual(sim.conn.execute(
            "SELECT COUNT(*) FROM history WHERE item_id='qa-mid-sync-failed'"
            ).fetchone()[0],1)

    def test_long_idle_time_reopens_without_negative_inventory(self):
        sim=self.sim
        for i in range(110):
            sim.tick(20)
        validate_current_state(sim.s,strict_physics=True)
        p=sim.s["person"]
        self.assertGreaterEqual(p["clock_minutes"],2000)
        self.assertFalse(any(v<0 for v in p["inventory"].values()))
        sim.write()
        reopened=Simulation(db_path=self.path/"live.sqlite3")
        self.addCleanup(reopened.conn.close)
        self.assertAlmostEqual(reopened.s["person"]["clock_minutes"],
                               p["clock_minutes"],places=5)
        self.assertEqual(reopened.s["person"]["pos"],p["pos"])
        self.assertEqual(reopened.s["person"]["inventory"],p["inventory"])
        self.assertEqual(reopened.entropy_origin,"restored_exact")

    def test_backup_restores_research_project_and_archive_ids(self):
        sim=self.sim
        p=sim.s["person"]
        p["research"].append({
            "id":"qa-research-1","question":"¿Cuán dura es la roca?",
            "hypothesis":"La roca es dura","state":"abierta","evidence":[]})
        p["projects"].append({
            "id":"qa-project-1","title":"Comparar dureza",
            "status":"pausado","progress":20})
        sim.s["journal"].append({
            "id":"qa-journal-1","when":"Día 2",
            "text":"Se registró una observación de prueba."})
        sim.write()
        destination=self.path/"backup.sqlite3"
        meta=backup_to_new_path(sim.conn,destination)
        self.assertEqual(meta,inspect_backup(destination))
        restored=Simulation(db_path=destination)
        self.addCleanup(restored.conn.close)
        r=restored.s["person"]
        self.assertIn("qa-research-1",[x["id"] for x in r["research"]])
        self.assertIn("qa-project-1",[x["id"] for x in r["projects"]])
        self.assertEqual(restored.archive.get("journal","qa-journal-1")["id"],
                         "qa-journal-1")
        self.assertEqual(restored.entropy_origin,"restored_exact")

    def test_two_worlds_do_not_share_runtime_state(self):
        a=self.sim
        b=self.simulation("isolated.sqlite3")
        before=encoded(b.s["world"]),b.rng.getstate()
        a.s["person"]["inventory"]["madera"]=17
        a.s["world"]["visited"]["qa-tile"]=9
        a.write()
        self.assertEqual((encoded(b.s["world"]),b.rng.getstate()),before)
        self.assertNotEqual(a.s["person"]["inventory"]["madera"],
                            b.s["person"]["inventory"].get("madera"))


if __name__=="__main__":
    unittest.main()
