"""Regresión del depurador histórico sobre partidas reales en SQLite temporal."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import unittest

from brain import normalize_decision
from historical_lab import catalog, replay, select_event
from laboratorio_motor import HistorySource, HISTORY_HTML_FILE
from nilo import Simulation


class HistoricalLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nilo-test-history-")
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "partida.sqlite3"

    def _make_run(self):
        sim=Simulation(db_path=self.db, world_seed=7321, rng_seed=9821)
        sim.think=lambda: None
        sim.s["speed"]=60
        sim.s["paused"]=False
        sim.s["mode"]="demo"
        decision=normalize_decision({
            "objetivo":"Registrar un descanso experimental",
            "cuaderno":"Estoy probando el motor.",
            "motivo":"Prueba reproducible",
            "accion_proyecto":"sin_proyecto",
            "plan":[{"op":"wait","minutes":30}],
            "revisar_en_minutos":90
        })
        sim.plan_ready(decision,"llm",{})
        for i in range(35):
            sim.tick(3.0)
            if not sim.s["person"].get("pending") and not sim.s["person"].get("plan"):
                break
        sim.write()
        minute=sim.s["person"]["clock_minutes"]
        sim.conn.close()
        return minute

    def test_checkpoints_decision_and_action_are_recorded(self):
        minute=self._make_run()
        result=catalog(self.db)
        self.assertGreaterEqual(result["checkpoint_count"],2)
        ops={item["op"] for item in result["entries"] if item["replayable"]}
        self.assertIn("wait",ops)
        self.assertGreater(minute,0)
        self.assertTrue(all(item["engine_version"] for item in result["entries"] if item["replayable"]))

    def test_action_replay_isolated_and_has_differences(self):
        self._make_run()
        event=next(e for e in catalog(self.db)["entries"] if e["op"]=="wait" and e["replayable"])
        baseline=hashlib.sha256(self.db.read_bytes()).hexdigest()
        result=replay(self.db,event["id"],max_ticks=100)
        self.assertEqual(result["historical"]["id"],event["id"])
        self.assertGreaterEqual(result["completed_actions"],1)
        self.assertGreater(result["after"]["minute"],result["before"]["minute"])
        self.assertFalse(result["unfinished"])
        self.assertTrue(result["stages"])
        self.assertIn("outcome_comparison",result)
        self.assertEqual(baseline,hashlib.sha256(self.db.read_bytes()).hexdigest())

    def test_decision_replay_and_alternative_plan(self):
        self._make_run()
        event=next(e for e in catalog(self.db)["entries"] if e["kind"]=="decision")
        baseline=replay(self.db,event["id"],max_ticks=90)
        self.assertGreaterEqual(baseline["completed_actions"],1)
        different=json.loads(json.dumps(select_event(self.db,event["id"])["command"]))
        different["plan"]=[{"op":"rest","minutes":60}]
        alternate=replay(self.db,event["id"],override=different,max_ticks=100)
        self.assertGreater(alternate["after"]["minute"],alternate["before"]["minute"])
        self.assertNotEqual(alternate["changes"],baseline["changes"])

    def test_old_partida_has_read_only_history_without_false_replay(self):
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TABLE history (seq INTEGER PRIMARY KEY,category TEXT,simulated_at TEXT,payload TEXT)")
            db.execute("INSERT INTO history VALUES (1,'diagnostic','Día 1 · 08:00',?)",
                       (json.dumps({"op":"gather","action_result":{"op":"gather","success":False}}),))
        result=catalog(self.db)
        self.assertEqual(result["checkpoint_count"],0)
        event=result["entries"][0]
        self.assertFalse(event["replayable"])
        self.assertTrue(event["failed"])
        details=select_event(self.db,event["id"])
        self.assertFalse(details["replayable"])
        with self.assertRaises(ValueError):
            replay(self.db,event["id"])

    def test_upload_validates_sqlite_and_does_not_write_original(self):
        self._make_run()
        data=self.db.read_bytes()
        source=HistorySource()
        with self.assertRaises(ValueError):
            source.load_bytes(b"hello")
        copied=source.load_bytes(data)
        self.assertGreater(copied["checkpoint_count"],0)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(),
                         hashlib.sha256(data).hexdigest())
        source.temp_directory.cleanup()

    def test_invalid_event_and_override_fail_safely(self):
        self._make_run()
        with self.assertRaises(ValueError):
            select_event(self.db,"../secrets")
        action=next(e for e in catalog(self.db)["entries"] if e["kind"]=="action")
        with self.assertRaises(ValueError):
            replay(self.db,action["id"],override={"op":"new_uninstalled_operation"})

    def test_historical_interface_script_syntax(self):
        html=HISTORY_HTML_FILE.read_text(encoding="utf-8")
        self.assertIn("Depurador histórico",html)
        self.assertIn('id="timeline"',html)
        self.assertIn('id="file"',html)
        node=shutil.which("node")
        if node:
            js=html.split("<script>",1)[1].split("</script>",1)[0]
            path=Path(self.temp.name)/"historico.js"
            path.write_text(js,encoding="utf-8")
            test=subprocess.run([node,"--check",str(path)],
                                capture_output=True,text=True,timeout=10)
            self.assertEqual(test.returncode,0,test.stderr)


if __name__=="__main__":
    unittest.main()
