"""Etapa 23: evaluación de evidencia real, sin APIs ni credenciales en CI."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from archive import History
from run_history import RunHistory
from tools.evaluar_autonomia_23 import (
    analyze_autonomy, compare_autonomy, report_text, _runs, _plan_signature,
)
from tools.ejecutar_autonomia_23 import preflight


class Autonomia23(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "VERSION").write_text("0.6.4\n", encoding="utf-8")

    def fixture(self, name="run.sqlite3", seed=7321, calls=2, chat=False):
        path = self.root / name
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE snapshot (id INTEGER PRIMARY KEY, payload TEXT)")
        archive = History(db)
        sessions = RunHistory(db, self.root)
        person = {
            "clock_minutes": 150,
            "measurements": [{"id": "m1"}],
            "behavior_metrics": {
                "actions": 2, "new_tiles": 3, "novelty_actions": 1,
                "by_origin": {"llm": 2}
            }
        }
        state = {
            "scenario_id": "territorio_desconocido",
            "world": {"seed": seed, "revealed": [], "structures": []},
            "person": person,
        }
        sessions.start(state, "territorio_desconocido", "isla_v1",
                       "gemini", "gemini-test", rng_seed=123)
        decision = {"accion_proyecto": "nuevo", "objetivo": "TEXTO_PRIVADO",
                    "motivo": "SECRETO_NO_EXPORTABLE",
                    "plan": [{"op": "explore", "direction": "north"}]}
        for i in range(calls):
            sessions.note_llm("gemini", "gemini-test")
            archive.add("llm_decision", {
                "id": "llm-" + str(i), "provider": "gemini",
                "model": "gemini-test", "context_sha256": "a" * 64,
                "decision": decision
            })
        for i in range(3):
            archive.add("diagnostic", {
                "id": "d" + str(i), "op": "go",
                "target": "río", "success": False,
                "origin": "llm"
            })
        archive.add("measurement", {"id": "m1", "op": "rest"})
        archive.add("diagnostic", {
            "id": "d4", "op": "rest", "success": True,
            "origin": "llm", "physical_result": {"measurement_id": "m1"}
        })
        archive.add("journal", {"id": "p", "text": "DIARIO_PRIVADO"})
        if chat:
            archive.add("chat", {"role": "user", "text": "CHAT_PRIVADO"})
        db.execute("INSERT INTO snapshot (id,payload) VALUES (1,?)",
                   (json.dumps(state, ensure_ascii=False),))
        db.commit()
        db.close()
        return path

    def test_evidence_requires_actual_usage_records(self):
        path = self.fixture()
        report = analyze_autonomy(path)
        self.assertTrue(report["verified_real_llm"])
        self.assertEqual(report["llm"]["decisions_archived"], 2)
        self.assertEqual(report["llm"]["successful_deliberations_counted"], 2)
        self.assertEqual(report["llm"]["repeated_plan_signatures"]["repeated_transitions"], 1)
        self.assertEqual(report["behavior"]["consecutive_identical_failed_actions"]["longest_identical_streak"], 3)
        self.assertEqual(report["behavior"]["physically_measured_actions"], 1)
        self.assertEqual(report["behavior"]["review_cases_failed_actions"][0]["first_record_id"], "d0")
        self.assertEqual(report["behavior"]["review_cases_failed_actions"][0]["last_record_id"], "d2")
        self.assertEqual(report["behavior"]["new_tiles_since_instrumentation"], 3)

    def test_missing_usage_not_claimed_real(self):
        path = self.fixture(calls=0)
        db = sqlite3.connect(path)
        archive = History(db)
        archive.add("llm_decision", {
            "id": "unbacked", "provider": "groq", "model": "x",
            "decision": {"plan": []}
        })
        db.commit()
        db.close()
        report = analyze_autonomy(path)
        self.assertFalse(report["verified_real_llm"])
        self.assertTrue(any("evidencia suficiente" in x for x in report["warnings"]))

    def test_outputs_redact_subjective_and_private_text(self):
        report = analyze_autonomy(self.fixture())
        text = json.dumps(report, ensure_ascii=False) + report_text([report])
        for secret in ("TEXTO_PRIVADO", "SECRETO_NO_EXPORTABLE",
                       "DIARIO_PRIVADO", "CHAT_PRIVADO"):
            self.assertNotIn(secret, text)
        self.assertNotIn("decision", report.get("behavior", {}))

    def test_chat_marks_uncontrolled_intervention(self):
        report = analyze_autonomy(self.fixture(chat=True))
        self.assertEqual(report["coverage"]["recorded_chat_entries"], 1)
        self.assertTrue(any("chat" in w.lower() for w in report["warnings"]))

    def test_compare_with_same_seed_is_not_causal(self):
        reports = [analyze_autonomy(self.fixture(name))
                   for name in ("a.sqlite3", "b.sqlite3")]
        result = compare_autonomy(reports)
        self.assertTrue(result["conditions"]["real_llm_in_all"])
        self.assertTrue(result["conditions"]["same_world_seed"])
        self.assertTrue(result["conditions"]["same_rng_seed"])
        self.assertTrue(result["conditions"]["same_initial_snapshot"])
        self.assertFalse(result["causal_claim_allowed"])

    def test_different_world_seed_not_a_match(self):
        left = analyze_autonomy(self.fixture("a.sqlite3", seed=7321))
        right = analyze_autonomy(self.fixture("b.sqlite3", seed=1129))
        self.assertFalse(compare_autonomy([left, right])["conditions"]["same_world_seed"])

    def test_signature_ignores_narrative_and_detects_actions(self):
        a = {"accion_proyecto": "nuevo", "motivo": "uno",
             "plan": [{"op": "go", "target": "agua"}]}
        b = {"accion_proyecto": "nuevo", "motivo": "dos",
             "plan": [{"op": "go", "target": "agua"}]}
        c = {"accion_proyecto": "nuevo", "motivo": "tres",
             "plan": [{"op": "go", "target": "cueva"}]}
        self.assertEqual(_plan_signature(a), _plan_signature(b))
        self.assertNotEqual(_plan_signature(a), _plan_signature(c))
        self.assertEqual(_runs(["a", "a", "a", "b", "a", "a"])["repeated_transitions"], 3)

    def test_preflight_demands_real_credential_and_bounded_budget(self):
        values = {"GEMINI_API_KEY": "test-key-only"}
        self.assertEqual(preflight("gemini", "gemini-test", 8, 420,
                                   7321, 1129, values), "GEMINI_API_KEY")
        for provider, env in (("groq", values), ("gemini", {}), ("demo", values)):
            with self.assertRaises(ValueError):
                preflight(provider, "model-test", 8, 420, 7321, 1129, env)
        with self.assertRaises(ValueError):
            preflight("gemini", "gemini-test", 101, 420, 7321, 1129, values)
        with self.assertRaises(ValueError):
            preflight("gemini", "gemini-test", 8, 420, -1, 1129, values)

    def test_no_sqlite_write_in_report(self):
        path = self.fixture()
        original = path.read_bytes()
        analyze_autonomy(path)
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
