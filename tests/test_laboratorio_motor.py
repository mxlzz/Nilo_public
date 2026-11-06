"""Pruebas del laboratorio sobre el motor real, sin red ni partida persistida."""
from __future__ import annotations

import json
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from laboratorio_motor import MotorLab


class MotorLabTests(unittest.TestCase):
    def setUp(self):
        self.lab = MotorLab()

    def test_uses_actual_engine_and_trace_for_exploration(self):
        result = self.lab.act({"op": "explore"})
        self.assertIn("status", result["last"]["result"])
        self.assertTrue(result["last"]["trace"])
        self.assertTrue(any(r["file"] == "navigation.py" and
                            r["function"] == "exploration_frontier"
                            for r in result["last"]["trace"]))
        for row in result["last"]["trace"]:
            self.assertGreaterEqual(row["first"], 1)
            self.assertGreaterEqual(row["last"], row["first"])
            self.assertIn("#L", row["url"])
            self.assertIn("github.com/mxlzz/Nilo_public/blob/refactor/0.7/",
                          row["url"])
            if row["file"] == "navigation.py":
                self.assertIn("/nilo_runtime/worlds/navigation.py#L", row["url"])

    def test_fabricate_and_test_load_with_real_capability(self):
        before = self.lab.person["inventory"]["madera"]
        built = self.lab.act({
            "op": "build", "name": "plataforma de pruebas",
            "purpose": "ensayo de carga",
            "materials": ["madera", "madera"],
            "geometry": {"shape": "plataforma", "size": 2}
        })
        self.assertTrue(built["last"]["result"]["success"],
                        built["last"]["result"]["facts"])
        self.assertEqual(self.lab.person["inventory"]["madera"], before - 2)
        ident = self.lab.world["structures"][-1]["id"]
        record = self.lab.act({"op": "interact", "method": "probar_carga",
                               "item": ident, "material": "piedra", "quantity": 2})
        self.assertEqual(record["last"]["result"]["status"], "verified_success")
        names = [(r["file"],r["function"]) for r in record["last"]["trace"]]
        self.assertIn(("capabilities.py", "dispatch"), names)
        self.assertIn(("structural_loads.py", "interact"), names)
        self.assertIn(("action_results.py", "result_from_execution"), names)
        self.assertTrue(self.lab.world["structures"][-1]["ensayos_de_carga"])

    def test_craft_trace_resolves_physical_object_module(self):
        result=self.lab.act({"op":"craft","name":"hacha ficticia",
                             "materials":["madera"],"form":"punta"})
        self.assertTrue(result["last"]["result"]["success"])
        rows=result["last"]["trace"]
        functions={(row["file"],row["function"]) for row in rows}
        self.assertIn(("objects.py","physical_item"),functions)
        self.assertIn(("objects.py","item_effects"),functions)
        for row in rows:
            if row["file"]=="objects.py":
                self.assertIn("/nilo_runtime/worlds/objects.py#L",row["url"])

    def test_rest_duration_respects_user_choice(self):
        first = self.lab.person["clock_minutes"]
        result = self.lab.act({"op": "rest", "minutes": 60})
        # Etapa 21: el sandbox ejecuta Simulation.tick; la duración del
        # handler puede ser estimada, la medición real manda.
        self.assertAlmostEqual(
            self.lab.person["measurements"][-1]["duration_minutes"],60,places=3)
        # plan_ready registra además la entrada de cuaderno; ese tiempo
        # transcurre en el motor real y no forma parte del descanso medido.
        self.assertGreaterEqual(self.lab.person["clock_minutes"]-first,60)
        self.assertLess(self.lab.person["clock_minutes"]-first,62)

    def test_context_preview_does_not_call_a_provider(self):
        for name in ("gemini", "groq"):
            result = self.lab.payload(name)
            self.assertEqual(result["provider"], name)
            self.assertIn("posición", result["context"])
            self.assertTrue(result["trace"])
            self.assertIn("build_deliberation_request",
                          [r["function"] for r in result["trace"]])

    def test_reset_discards_actions_and_can_start_without_kit(self):
        self.lab.act({"op": "eat"})
        reset = self.lab.reset("nuevo", 7321, False)
        self.assertEqual(reset["history"], [])
        self.assertIsNone(reset["last"])
        self.assertNotIn("materiales de prueba", reset["origin"])

    def test_live_snapshot_copy_never_writes_database(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nilo_mundo.sqlite3"
            state = __import__("nilo").initial_state(7321)
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE snapshot (id INTEGER PRIMARY KEY, payload TEXT)")
            data = json.dumps(state)
            conn.execute("INSERT INTO snapshot VALUES (1, ?)", (data,))
            conn.commit()
            conn.close()
            with patch("laboratorio_motor.DB", path):
                cloned = self.lab.reset("partida", 1, True)
                self.assertIn("Copia", cloned["origin"])
                self.lab.act({"op": "eat"})
                check = sqlite3.connect(path)
                try:
                    persisted = check.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
                finally:
                    check.close()
                self.assertEqual(persisted, data)

    def test_rejects_unknown_op_without_mutating(self):
        before = json.dumps([self.lab.world, self.lab.person], sort_keys=True)
        with self.assertRaises(ValueError):
            self.lab.act({"op": "unrestricted_python"})
        self.assertEqual(before, json.dumps([self.lab.world, self.lab.person], sort_keys=True))




class UserInterfaceTests(unittest.TestCase):
    def test_html_embeds_all_operations(self):
        from action_contracts import SUPPORTED_OPERATIONS
        from laboratorio_motor import HTML_FILE
        html = HTML_FILE.read_text(encoding="utf-8")
        self.assertIn("Cómo funciona el motor", html)
        for op in SUPPORTED_OPERATIONS:
            self.assertIn('"' + op + '"', html)

    def test_frontend_script_syntax_when_node_is_available(self):
        import shutil
        import subprocess
        from laboratorio_motor import HTML_FILE
        node = shutil.which("node")
        if not node:
            self.skipTest("Node no disponible: syntax check de HTML omitido")
        html = HTML_FILE.read_text(encoding="utf-8")
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "laboratorio.js"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run([node, "--check", str(path)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
