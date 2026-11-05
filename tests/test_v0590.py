"""Pruebas del circuito supervisado de autodiagnóstico 0.5.9."""
import json
import tempfile
import unittest
from pathlib import Path

from action_results import ActionResult
from diagnostics import inspect_invariants, record_invariant_issue, review_packet
from inventions import ensure_records, submit_debug_report, submit_proposal, review_proposal
from nilo import Simulation, initial_state


class InvariantDetection(unittest.TestCase):
    def setUp(self):
        s = initial_state(7321)
        self.w, self.p = s["world"], s["person"]
        ensure_records(self.p)
        self.result = ActionResult.from_legacy({"op":"inspect"}, ["No vi nada"], False, False)

    def test_normal_failure_does_not_trigger_issue(self):
        self.assertEqual(inspect_invariants(self.w, self.p, self.result,
                                            self.p["pos"]), [])

    def test_structural_violations_are_detected_without_text_analysis(self):
        self.p["inventory"]["piedra"] = -2
        self.p.setdefault("needs", {})["energia"] = 105
        invalid = ActionResult.from_legacy({"op":"inspect"}, ["Todo bien"], True, False)
        object.__setattr__(invalid, "status", "verified_failure")
        issues = inspect_invariants(self.w, self.p, invalid, [1000, -1, 0])
        self.assertEqual({x["check_id"] for x in issues}, {
            "position_invalid", "inventory_negative",
            "need_out_of_range", "result_status_mismatch"})

    def test_no_automatic_bug_confirmation_and_deduplication(self):
        outcome = {"id":"act-1", "op":"inspect", "success":True, "facts":["x"],
                   "evaluation_status":"verified_success"}
        issue = {"check_id":"inventory_negative",
                 "observed":{"material":"piedra","quantity":-1}}
        first = record_invariant_issue(self.p, issue, outcome, "Día 1", "isla_v1")
        self.assertEqual(first["status"], "pendiente")
        self.assertEqual(first["origin"], "motor")
        self.assertEqual(first["evidence"][0]["id"], "act-1")
        again = record_invariant_issue(self.p, issue, outcome, "Día 1", "isla_v1")
        self.assertIsNone(again)
        self.assertEqual(len(self.p["proposals"]), 1)

    def test_anomaly_is_not_a_conclusion_about_unimplemented_physics(self):
        self.assertEqual(inspect_invariants(self.w, self.p, None,
                                            self.p["pos"]), [])


class AuditPacket(unittest.TestCase):
    def setUp(self):
        self.p = initial_state(7321)["person"]
        ensure_records(self.p)

    def test_debug_packet_links_only_recorded_action_ids(self):
        self.p["action_outcomes"] = [{
            "id":"act-valid", "when":"Día 3", "op":"use",
            "target":"objeto", "success":False, "facts":["Prueba fallida"],
            "pos":[12,8,0], "evaluation_status":"verified_failure",
            "action_result":{"status":"verified_failure","physical":None},
        }]
        step = {"title":"Comportamiento contradictorio",
                "expected":"Se esperaba X","observed":"Se observó Y",
                "rationale":"El resultado contradice la hipótesis",
                "related_action":"use", "evidence_ids":["act-valid","act-falso"]}
        ok,_ = submit_debug_report(self.p,step,"Día 3")
        self.assertTrue(ok)
        report = self.p["proposals"][-1]
        packet = review_packet(self.p,report["id"],scenario_id="territorio_desconocido",
                               environment_id="isla_v1",version="0.5.9.0")
        self.assertEqual(packet["evidence_ids"],["act-valid"])
        self.assertNotIn("act-falso",json.dumps(packet))
        self.assertEqual(packet["evidence_level"],"registro_verificado")
        self.assertEqual(packet["reproduction"]["status"],"orientativo_sin_snapshot_inicial")
        self.assertFalse(packet["automatic_patch"])
        self.assertEqual(packet["digest_sha256"],
                         review_packet(self.p,report["id"],scenario_id="territorio_desconocido",
                                       environment_id="isla_v1",version="0.5.9.0")["digest_sha256"])
        self.assertNotIn("GEMINI_API_KEY",json.dumps(packet))

    def test_physics_packet_uses_actual_unmodeled_evidence(self):
        self.p["unmodeled_attempts"] = [{
            "id":"no-modelo-1","when":"Día 2","op":"use",
            "phenomenon":"evaporación","missing_capability":"calor",
            "method":"evaporar","result":"no_evaluable",
        }]
        ok,_=submit_proposal(self.p,{"phenomenon":"evaporación",
               "rationale":"Interacción sin modelo", "experiment":"Aplicar calor",
               "missing_capability":"Modelo térmico", "evidence_ids":["no-modelo-1"]},
               "Día 2",[])
        self.assertTrue(ok)
        packet=review_packet(self.p,self.p["proposals"][-1]["id"])
        self.assertEqual(packet["kind"],"physics")
        self.assertEqual(packet["evidence_ids"],["no-modelo-1"])
        self.assertEqual(packet["reproduction"]["status"],"requiere_implementacion_de_fisica")
        self.assertEqual(packet["statement"]["phenomenon"],"evaporación")

    def test_no_evidence_is_not_misrepresented_as_verified(self):
        ok,_=submit_debug_report(self.p,{"title":"Sospecha sin prueba",
                 "expected":"x", "observed":"y", "rationale":"duda"}, "Día 1")
        self.assertTrue(ok)
        packet=review_packet(self.p,self.p["proposals"][-1]["id"])
        self.assertEqual(packet["evidence_ids"],[])
        self.assertEqual(packet["evidence_level"],"sin_evidencia_adjunta")

    def test_review_remains_human_and_does_not_change_physics(self):
        issue = record_invariant_issue(self.p,{"check_id":"inventory_negative",
            "observed":{"quantity":-1}},{"id":"act-1","op":"inspect"},
            "Día 1","isla_v1")
        reviewed=review_proposal(self.p,issue["id"],"bug",
                                 "Debe investigarse", "Día 2")
        self.assertEqual(reviewed["status"],"error_confirmado_pendiente_de_correccion")
        packet=review_packet(self.p,issue["id"])
        self.assertFalse(packet["code_change_allowed"])


class SimulationAndUi(unittest.TestCase):
    def test_execution_creates_a_single_review_for_real_invariant_violation(self):
        with tempfile.TemporaryDirectory() as folder:
            sim = Simulation(db_path=Path(folder)/"test.sqlite")
            try:
                sim.s["planning"] = True
                person=sim.s["person"]
                person["inventory"]["piedra"] = -2
                person["plan"] = [{"op":"inspect","target":"suelo"}]
                sim.change_speed(speed=60)
                for _ in range(5):
                    sim.tick(15)
                issues=[x for x in person["proposals"]
                        if x.get("origin")=="motor" and x.get("check_id")=="inventory_negative"]
                self.assertEqual(len(issues),1)
                packet=sim.diagnostic_package(issues[0]["id"])
                self.assertEqual(packet["evidence"][0]["id"],issues[0]["evidence"][0]["id"])
                self.assertEqual(packet["engine_version"],(Path(__file__).resolve().parent.parent/"VERSION").read_text().strip())
                self.assertFalse(packet["automatic_patch"])
            finally:
                sim.conn.close()

    def test_interface_exposes_export_without_modify_endpoint(self):
        markup=(Path(__file__).resolve().parent.parent/"interfaz.html").read_text("utf-8")
        self.assertIn('data-diagnostic=',markup)
        self.assertIn("/api/diagnostic?id=",markup)
        self.assertIn("application/json",markup)
        self.assertIn("JSON.stringify(packet,null,2)+'\\n'",markup)
        self.assertNotIn("/api/auto-patch",markup)


if __name__ == "__main__":
    unittest.main()
