"""Etapa 04 — IDs y RNG reproducibles, restauración de partidas y legado."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
import uuid
from unittest.mock import patch

from nilo import Simulation
from nilo_runtime.core.identity import (
    EntropyError, EntropySession, id_bits, new_uuid, physical_suffix,
)
from nilo_runtime.storage.entropy import load_entropy, persist_entropy
from world import make_item, execute_action
from nilo import initial_state
from historical_lab import select_event, replay


PROPS={"dureza":4.0,"resistencia":3.0,"peso":1.0}


class IdentitySequenceTests(unittest.TestCase):
    def test_same_seeds_produce_same_ids_without_global_rng(self):
        x=EntropySession(7321,9821)
        y=EntropySession(7321,9821)
        with x.bind():
            ids_x=[new_uuid().hex for _ in range(1000)]
        with y.bind():
            ids_y=[new_uuid().hex for _ in range(1000)]
        self.assertEqual(ids_x,ids_y)
        self.assertEqual(len({value[:8] for value in ids_x}),len(ids_x))
        self.assertTrue(all(uuid.UUID(hex=value).version==4 for value in ids_x))

    def test_id_allocations_do_not_advance_physical_rng(self):
        a=EntropySession(7321,9821)
        b=EntropySession(7321,9821)
        with a.bind():
            _=[new_uuid() for _ in range(15)]
            _=[id_bits(52) for _ in range(6)]
        self.assertEqual(a.agent_rng.getstate(),b.agent_rng.getstate())
        self.assertEqual(a.agent_rng.random(),b.agent_rng.random())

    def test_serialization_restores_both_rngs_and_counter(self):
        one=EntropySession(5,19)
        one.agent_rng.random()
        with one.bind():
            first=new_uuid().hex
            value=id_bits(16)
            self.assertIsInstance(value,int)
        state=one.to_record()
        encoded=json.loads(json.dumps(state))
        restored=EntropySession.from_record(encoded,world_seed=5)
        with one.bind():
            expected=(one.agent_rng.random(),new_uuid().hex,id_bits(52))
        with restored.bind():
            actual=(restored.agent_rng.random(),new_uuid().hex,id_bits(52))
        self.assertEqual(expected,actual)
        self.assertNotEqual(first,actual[1])

    def test_context_is_per_thread_and_restored_on_exit(self):
        a=EntropySession(1,2)
        b=EntropySession(3,4)
        def worker(session):
            with session.bind():
                return [new_uuid().hex for _ in range(6)]
        with ThreadPoolExecutor(max_workers=2) as ex:
            left,right=list(ex.map(worker,(a,b)))
        self.assertNotEqual(left,right)
        fresh=EntropySession(1,2)
        self.assertEqual(left,[fresh.uuid4().hex for _ in range(6)])
        with patch("uuid.uuid4",return_value=uuid.UUID(int=1234)):
            self.assertEqual(new_uuid(),uuid.UUID(int=1234))

    def test_corrupt_identity_checkpoint_is_rejected(self):
        x=EntropySession(17,23)
        record=x.to_record()
        for change in (
            lambda d: d.update(uuid_counter=-1),
            lambda d: d.update(id_seed="otra"),
            lambda d: d.update(world_seed=88),
            lambda d: d.update(id_rng_state=[1,2]),
        ):
            with self.subTest(change=change):
                bad=deepcopy(record)
                change(bad)
                with self.assertRaises(EntropyError):
                    EntropySession.from_record(bad,world_seed=17)


class SQLiteEntropyTests(unittest.TestCase):
    def test_snapshot_and_rng_resume_exactly(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-rng-") as td:
            path=Path(td)/"state.sqlite3"
            sim=Simulation(db_path=path,world_seed=7321,rng_seed=991)
            try:
                self.assertEqual(sim.entropy_origin,"new_seeded")
                with sim.entropy.bind():
                    _=new_uuid()
                    _=id_bits(52)
                _=sim.rng.random()
                sim.write()
                with sim.entropy.bind():
                    expected=(new_uuid().hex,id_bits(52),sim.rng.random())
                expected_seed=sim.rng_seed
            finally:
                sim.conn.close()
            reopened=Simulation(db_path=path,world_seed=8888,rng_seed=17)
            try:
                self.assertEqual(reopened.entropy_origin,"restored_exact")
                self.assertEqual(reopened.rng_seed,expected_seed)
                with reopened.entropy.bind():
                    actual=(new_uuid().hex,id_bits(52),reopened.rng.random())
                self.assertEqual(actual,expected)
            finally:
                reopened.conn.close()

    def test_old_save_without_entropy_uses_documented_legacy_fallback(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-oldrng-") as td:
            path=Path(td)/"old.sqlite3"
            sim=Simulation(db_path=path,world_seed=7321)
            try:
                sim.s["person"]["clock_minutes"]=124.5
                sim.write()
            finally:
                sim.conn.close()
            with sqlite3.connect(path) as db:
                db.execute("DROP TABLE runtime_entropy")
            resumed=Simulation(db_path=path)
            try:
                self.assertEqual(resumed.entropy_origin,"legacy_seeded_without_history")
                self.assertEqual(resumed.rng_seed,9821+124)
                self.assertEqual(resumed.s["person"]["clock_minutes"],124.5)
            finally:
                resumed.conn.close()

    def test_invalid_entropy_does_not_overwrite_snapshot(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-corrupt-rng-") as td:
            path=Path(td)/"broken.sqlite3"
            sim=Simulation(db_path=path)
            sim.conn.close()
            with sqlite3.connect(path) as db:
                before=db.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
                db.execute("UPDATE runtime_entropy SET payload=? WHERE id=1",
                           ('{"format":"nilo-entropy-v1","uuid_counter":-5}',))
            with self.assertRaises(EntropyError):
                Simulation(db_path=path)
            with sqlite3.connect(path) as db:
                after=db.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
            self.assertEqual(before,after)

    def test_issue_143_build_id_independent_of_global_seed(self):
        def build(global_seed):
            state=initial_state(world_seed=7321)
            world,person=state["world"],state["person"]
            person["inventory"]["madera"]=8
            random.seed(global_seed)
            effect=execute_action(
                world,person,{"op":"build","name":"apoyo de piedra",
                              "materials":["madera"],"purpose":"ensayo"},
                random.Random(444))
            self.assertTrue(effect[2],effect[1])
            return world["structures"][-1]["id"]
        try:
            old_state=random.getstate()
            a=build(11)
            b=build(987654)
            self.assertEqual(a,b)
        finally:
            random.setstate(old_state)

    def test_physical_number_is_not_reused_after_save_and_removal(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-ids-") as td:
            db=Path(td)/"world.sqlite3"
            sim=Simulation(db_path=db,world_seed=7321,rng_seed=9821)
            try:
                with sim.entropy.bind():
                    first=make_item("punta","ensayo",["madera"],PROPS,0)["id"]
                    _=physical_suffix(16)
                sim.write()
            finally:
                sim.conn.close()
            resumed=Simulation(db_path=db)
            try:
                with resumed.entropy.bind():
                    second=make_item("punta","ensayo",["madera"],PROPS,0)["id"]
                    third=physical_suffix(16)
                self.assertNotEqual(first,second)
                self.assertGreater(int(second.split("-")[-1]),int(first.split("-")[-1]))
                self.assertGreater(third,int(second.split("-")[-1]))
                self.assertGreater(int(first.split("-")[-1]),1<<96)
            finally:
                resumed.conn.close()

    def test_checkpoint_includes_full_modern_identity_state(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-timeline-") as td:
            db=Path(td)/"world.sqlite3"
            sim=Simulation(db_path=db,rng_seed=12345)
            try:
                cp=sim.timeline.record("action",sim.s,sim.rng,
                    action={"op":"wait","minutes":30},source="llm",
                    engine_version="0.7",entropy=sim.entropy)
                sim.conn.commit()
                event=select_event(db,"cp:"+str(cp),full=True)
                saved=event["_restorable"]["entropy_state"]
                replay_identity=EntropySession.from_record(
                    saved,world_seed=sim.s["world"]["seed"])
                with sim.entropy.bind():
                    expected=(new_uuid().hex,physical_suffix(16))
                with replay_identity.bind():
                    actual=(new_uuid().hex,physical_suffix(16))
                self.assertEqual(actual,expected)
            finally:
                sim.conn.close()

    def test_checkpoint_063_replays_physics_without_changing_source(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-legacy-checkpoint-") as td:
            path=Path(td)/"old.sqlite3"
            sim=Simulation(db_path=path,rng_seed=9821)
            try:
                sim.think=lambda:None
                sim.s["person"]["inventory"]["madera"]=5
                step={"op":"build","materials":["madera"],
                      "name":"plataforma de apoyo","purpose":"experimento"}
                sim.s["person"]["plan"]=[dict(step)]
                sim.s["speed"]=60
                sim.s["paused"]=False
                cp=sim.timeline.record("action",sim.s,sim.rng,
                                       source="llm",action=step,
                                       engine_version="0.6.3",entropy=None)
                sim.conn.commit()
            finally:
                sim.conn.close()
            baseline=path.read_bytes()
            run=replay(path,"cp:"+str(cp),max_ticks=100)
            self.assertGreaterEqual(run["completed_actions"],1)
            self.assertGreater(run["after"]["structures"],
                               run["before"]["structures"])
            self.assertEqual(path.read_bytes(),baseline)
            self.assertEqual(run["version_recorded"],"0.6.3")

    def test_legacy_snapshot_replacement_is_explicitly_reseeded(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-reimport-") as td:
            db=Path(td)/"world.sqlite3"
            sim=Simulation(db_path=db)
            sim.conn.close()
            old=initial_state()
            with sqlite3.connect(db) as con:
                con.execute("UPDATE snapshot SET payload=? WHERE id=1",
                            (json.dumps(old,ensure_ascii=False),))
            next_sim=Simulation(db_path=db)
            try:
                self.assertEqual(next_sim.entropy_origin,
                                 "legacy_reimported_without_history")
                self.assertEqual(next_sim.s["world"]["seed"],7321)
            finally:
                next_sim.conn.close()

    def test_world_item_identity_uses_bound_stream(self):
        a=EntropySession(7321,9821)
        b=EntropySession(7321,9821)
        with patch("random.getrandbits",side_effect=AssertionError("RNG global prohibido")):
            with a.bind():
                first=make_item("punta","excavar",["madera"],PROPS,0)
            with b.bind():
                second=make_item("punta","excavar",["madera"],PROPS,0)
        self.assertEqual(first["id"],second["id"])

    def test_snapshot_rewritten_by_old_engine_is_detected(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-mismatch-") as td:
            path=Path(td)/"snapshot.sqlite3"
            sim=Simulation(db_path=path)
            sim.conn.close()
            with sqlite3.connect(path) as db:
                snapshot=json.loads(db.execute(
                    "SELECT payload FROM snapshot WHERE id=1").fetchone()[0])
                snapshot["speed"]=2
                db.execute("UPDATE snapshot SET payload=? WHERE id=1",
                           (json.dumps(snapshot,ensure_ascii=False),))
            with self.assertRaisesRegex(EntropyError,"snapshot cambió"):
                Simulation(db_path=path)

    def test_legacy_replay_path_uses_uuid_patch(self):
        with tempfile.TemporaryDirectory(prefix="nilo-07-legacy-rng-") as td:
            sim=Simulation(db_path=Path(td)/"world.sqlite3")
            try:
                sim.historical_replay=True
                fixed=uuid.UUID("fedcba98-0000-4000-8000-000000000001")
                with patch("uuid.uuid4",return_value=fixed):
                    sim.event(["Registro histórico"],"resultado")
                self.assertEqual(sim.s["events"][-1]["id"],str(fixed)[:15])
            finally:
                sim.conn.close()


if __name__=="__main__":
    unittest.main()
