"""Regresiones de historial de sesiones: no inventar versiones del pasado."""
from __future__ import annotations

import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nilo import Simulation, initial_state
from run_history import RunHistory, engine_identity


class RunHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "world.sqlite3"
        self.root = Path(self.temporary.name)
        (self.root / "VERSION").write_text("0.5.9.1\n", encoding="utf-8")
        (self.root / "MANIFIESTO_SHA256.json").write_text('{"version":"0.5.9.1"}',
                                                        encoding="utf-8")

    def test_new_world_starts_with_one_session_and_no_fabricated_history(self):
        conn = sqlite3.connect(self.db)
        history = RunHistory(conn, self.root)
        state = initial_state()
        history.start(state, "territorio_desconocido", "isla_v1", "gemini", "modelo-a")
        conn.commit()
        rows = history.recent()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["engine_version"], "0.5.9.1")
        self.assertEqual(rows[0]["configured_model"], "modelo-a")
        self.assertIsNone(rows[0]["code_commit"])
        self.assertRegex(rows[0]["started_utc"], r"\d{4}-\d{2}-\d{2}T")
        self.assertEqual(rows[0]["simulated_start_min"],
                         state["person"]["clock_minutes"])
        self.assertEqual(rows[0]["state"], "en_curso")
        conn.close()

    def test_session_real_model_and_close_persist(self):
        conn = sqlite3.connect(self.db)
        h = RunHistory(conn, self.root)
        s = initial_state()
        h.start(s, "territorio_desconocido", "isla_v1", "gemini", "modelo-a")
        h.note_llm("groq", "modelo-respaldo")
        h.note_llm("groq", "modelo-respaldo")
        h.note_llm("gemini", "modelo-a", "chat")
        h.touch(1482.5)
        h.finish(1490, "normal")
        conn.close()

        conn2 = sqlite3.connect(self.db)
        second = RunHistory(conn2, self.root)
        rows = second.recent()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["state"], "cerrada")
        self.assertEqual(rows[0]["simulated_end_min"], 1490)
        self.assertEqual(rows[0]["models_used"], [
            {"provider":"gemini","model":"modelo-a","purpose":"chat","calls":1},
            {"provider":"groq","model":"modelo-respaldo",
             "purpose":"deliberacion","calls":2},
        ])
        second.start(s, "territorio_desconocido", "isla_v1")
        rows = second.recent()
        self.assertEqual([x["state"] for x in rows], ["en_curso", "cerrada"])
        self.assertEqual(rows[1]["simulated_end_min"], 1490)
        self.assertEqual(rows[1]["models_used"][1]["calls"], 2)
        second.finish(0)
        conn2.close()

    def test_incomplete_session_is_not_assumed_to_have_ended_normally(self):
        conn = sqlite3.connect(self.db)
        one = RunHistory(conn, self.root)
        one.start(initial_state(), "territorio_desconocido", "isla_v1")
        one.touch(50)
        conn.commit()
        conn.close()
        reopened = sqlite3.connect(self.db)
        second = RunHistory(reopened, self.root)
        second.start(initial_state(), "territorio_desconocido", "isla_v1")
        rows = second.recent()
        self.assertEqual(rows[1]["state"], "sin_cierre_registrado")
        self.assertIsNone(rows[1]["ended_utc"])
        self.assertEqual(rows[1]["simulated_end_min"], 50)
        reopened.close()

    def test_bad_model_usage_is_rejected_and_does_not_change_counts(self):
        conn = sqlite3.connect(self.db)
        h = RunHistory(conn, self.root)
        h.start(initial_state(), "territorio_desconocido", "isla_v1")
        with self.assertRaises(ValueError):
            h.note_llm("gemini", "modelo-a", "reescribir_codigo")
        self.assertEqual(h.recent()[0]["models_used"], [])
        conn.close()

    def test_commit_not_guessed_without_git_and_fingerprint_is_real(self):
        with patch("run_history.subprocess.run", side_effect=FileNotFoundError()):
            info = engine_identity(self.root)
        self.assertIsNone(info["code_commit"])
        self.assertEqual(info["engine_version"], "0.5.9.1")
        self.assertRegex(info["manifest_sha256"], r"^[0-9a-f]{64}$")


class SimulationSessionIntegration(unittest.TestCase):
    def test_world_is_migrated_in_place_and_session_is_outside_agent_memory(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "existing.sqlite3"
            original = initial_state()
            original["person"]["clock_minutes"] = 2910
            original["person"]["inventory"]["madera"] = 7
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE snapshot (id INTEGER PRIMARY KEY,payload TEXT NOT NULL)")
            conn.execute("INSERT INTO snapshot (id,payload) VALUES (1,?)",
                         (json.dumps(original,ensure_ascii=False),))
            conn.commit()
            conn.close()
            sim = Simulation(db_path=db)
            try:
                self.assertEqual(sim.s["person"]["inventory"]["madera"], 7)
                self.assertEqual(sim.s["person"]["clock_minutes"], 2910)
                self.assertNotIn("engine_sessions", sim.s)
                self.assertNotIn("engine_version", sim.s["person"])
                self.assertEqual(len(sim.public_state()["engine_sessions"]), 1)
                actual=(Path(__file__).resolve().parent.parent/"VERSION").read_text("utf-8").strip()
                self.assertEqual(sim.sessions.identity["engine_version"], actual)
                self.assertEqual(sim.public_state()["engine_sessions"][0]["simulated_start_min"],
                                 2910)
                sim.sessions.note_llm("gemini","modelo-x")
                sim.write()
                self.assertEqual(sim.public_state()["engine_sessions"][0]["models_used"][0]["calls"],1)
                sim.sessions.finish(2910)
            finally:
                sim.conn.close()
            other = Simulation(db_path=db)
            try:
                rows = other.public_state()["engine_sessions"]
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[1]["state"], "cerrada")
                self.assertEqual(rows[1]["models_used"][0]["model"],"modelo-x")
                self.assertEqual(other.s["person"]["inventory"]["madera"], 7)
            finally:
                other.conn.close()

    def test_ui_exposes_versions_and_does_not_allow_editing_sessions(self):
        ui = (Path(__file__).resolve().parent.parent / "interfaz.html").read_text("utf-8")
        self.assertIn('data-setting-tab="versions"', ui)
        self.assertIn("function renderVersions()", ui)
        self.assertIn("engine_sessions", ui)
        self.assertNotIn("/api/edit-sessions", ui)


if __name__ == "__main__":
    unittest.main()
