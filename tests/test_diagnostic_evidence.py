"""Regresiones del primer corte de diagnóstico autónomo trazable.

Pruebas deterministas: la decisión libre del LLM se evalúa con runs aparte.
"""
import unittest

from action_contracts import ACTION_GUIDE
from brain import compact_context, context_for
from diagnostic_support import (
    human_review_feedback, select_debug_evidence, select_physics_evidence)
from diagnostics import review_packet
from inventions import ensure_records, review_proposal, submit_debug_report, submit_proposal
from nilo import initial_state


def missing(rid, phenomenon, method="experimentar"):
    return {"id": rid, "phenomenon": phenomenon, "method": method,
            "result": "no_evaluable", "op": "experiment",
            "missing_capability": "Ley no modelada"}


def outcome(rid, op, success=False):
    return {"id": rid, "op": op, "target": "objeto", "success": success,
            "facts": ["Resultado del motor"], "evaluation_status":
            "verified_success" if success else "verified_failure"}


def physics_step(**extra):
    return {"phenomenon": "condensación", "missing_capability": "Transferencia térmica",
            "rationale": "No puedo medir agua recuperada",
            "experiment": "Medir condensado en condiciones comparables", **extra}


def debug_step(**extra):
    return {"title": "Movimiento inconsistente", "expected": "Desplazamiento al norte",
            "observed": "El desplazamiento real contradice la orientación",
            "rationale": "Contrastar resultado físico y narración",
            "related_action": "go", **extra}


class EvidenceSelection(unittest.TestCase):
    def test_physics_explicit_ids_only_same_phenomenon(self):
        rows = [missing("no-modelo-a", "Evaporación y condensación de agua"),
                missing("no-modelo-b", "Flotación de materiales")]
        selected, mode = select_physics_evidence(physics_step(
            evidence_ids=["no-modelo-a", "no-modelo-b", "no-modelo-inventado"]), rows)
        self.assertEqual([r["id"] for r in selected], ["no-modelo-a"])
        self.assertEqual(mode, "referencia_explicita")

    def test_physics_no_fallback_on_wrong_explicit_ids(self):
        rows = [missing("no-modelo-a", "Evaporación y condensación de agua")]
        selected, mode = select_physics_evidence(
            physics_step(evidence_ids=["no-modelo-inventado"]), rows)
        self.assertEqual(selected, [])
        self.assertEqual(mode, "sin_evidencia_coincidente")

    def test_physics_no_false_link_by_agua_or_unsupported_result(self):
        rows = [missing("no-modelo-thermal", "Evaporación y condensación de agua"),
                {"id": "act-bowl", "phenomenon": "Retención de agua",
                 "result": "verified_failure"}]
        selected, mode = select_physics_evidence(
            physics_step(phenomenon="Retención de agua"), rows)
        self.assertEqual(selected, [])
        self.assertEqual(mode, "sin_evidencia_coincidente")

    def test_physics_without_ids_can_recover_phenomenon_with_uncertain_link(self):
        rows = [missing("no-modelo-a", "Evaporación y condensación de agua"),
                missing("no-modelo-b", "Fricción estática")]
        selected, mode = select_physics_evidence(physics_step(), rows)
        self.assertEqual([r["id"] for r in selected], ["no-modelo-a"])
        self.assertEqual(mode, "coincidencia_de_fenomeno")

    def test_debug_invalid_explicit_ids_do_not_substitute_recent_failure(self):
        selected, mode = select_debug_evidence(
            debug_step(evidence_ids=["act-inexistente"]), [outcome("act-1", "go")])
        self.assertEqual(selected, [])
        self.assertEqual(mode, "sin_evidencia_coincidente")

    def test_debug_without_ids_marks_operation_match_as_uncertain(self):
        selected, mode = select_debug_evidence(
            debug_step(), [outcome("act-1", "go"),
                           outcome("act-2", "rest"), outcome("act-3", "go", True)])
        self.assertEqual([r["id"] for r in selected], ["act-1"])
        self.assertEqual(mode, "misma_operacion_sin_relacion_verificada")

    def test_debug_without_operation_or_ids_has_no_evidence(self):
        selected, _ = select_debug_evidence(
            {"title": "Duda"}, [outcome("act-1", "go")])
        self.assertFalse(selected)


class ProposalLifecycle(unittest.TestCase):
    def setUp(self):
        state = initial_state()
        self.world, self.p = state["world"], state["person"]
        ensure_records(self.p)

    def test_unsupported_physics_proposal_does_not_forge_support(self):
        self.p["unmodeled_attempts"] = [
            missing("no-modelo-thermal", "Evaporación y condensación de agua")]
        ok, _ = submit_proposal(
            self.p, physics_step(phenomenon="Flotación", evidence_ids=[
                "no-modelo-thermal"]), "Día 1", ())
        self.assertTrue(ok)
        report = self.p["proposals"][-1]
        self.assertEqual(report["evidence"], [])
        self.assertEqual(report["evidence_quality"], "hipotesis_sin_prueba_de_fisica")
        self.assertEqual(review_packet(self.p, report["id"])["evidence_ids"], [])

    def test_physics_proposal_coexists_with_prior_debug_report(self):
        self.assertTrue(submit_debug_report(self.p, debug_step(), "Día 1")[0])
        ok, _ = submit_proposal(self.p, physics_step(), "Día 2", ())
        self.assertTrue(ok)
        self.assertEqual([x["type"] for x in self.p["proposals"]],
                         ["debug", "physics"])

    def test_condensation_proposal_has_real_verified_no_model_record(self):
        self.p["unmodeled_attempts"] = [
            missing("no-modelo-thermal", "Evaporación y condensación de agua")]
        ok, _ = submit_proposal(self.p, physics_step(
            evidence_ids=["no-modelo-thermal"]), "Día 1", ())
        self.assertTrue(ok)
        report = self.p["proposals"][-1]
        self.assertEqual(report["evidence_relation"], "referencia_explicita")
        packet = review_packet(self.p, report["id"])
        self.assertEqual(packet["evidence_association"], "referencia_explicita")
        self.assertEqual(packet["evidence_ids"], ["no-modelo-thermal"])
        self.assertFalse(packet["automatic_patch"])

    def test_debug_report_fallback_does_not_claim_related_proof(self):
        self.p["action_outcomes"] = [outcome("act-go", "go")]
        ok, _ = submit_debug_report(self.p, debug_step(), "Día 1")
        self.assertTrue(ok)
        report = self.p["proposals"][-1]
        self.assertEqual(report["evidence_relation"],
                         "misma_operacion_sin_relacion_verificada")
        packet = review_packet(self.p, report["id"])
        self.assertEqual(packet["evidence_level"], "registro_verificado")
        self.assertEqual(packet["evidence_association"], report["evidence_relation"])

    def test_explicit_debug_id_does_not_fallback_to_failure(self):
        self.p["action_outcomes"] = [outcome("act-go", "go")]
        ok, _ = submit_debug_report(self.p, debug_step(
            evidence_ids=["act-imaginaria"]), "Día 1")
        self.assertTrue(ok)
        self.assertEqual(self.p["proposals"][-1]["evidence"], [])

    def test_human_review_is_available_without_physical_claim(self):
        self.p["action_outcomes"] = [outcome("act-go", "go")]
        ok, _ = submit_debug_report(self.p, debug_step(
            evidence_ids=["act-go"]), "Día 1")
        self.assertTrue(ok)
        report = self.p["proposals"][-1]
        review_proposal(self.p, report["id"], "interpretacion",
                        "Una casilla de agua no es caminable", "Día 2")
        feedback = human_review_feedback(self.p["proposals"])
        self.assertEqual(feedback[-1]["solicitud_id"], report["id"])
        self.assertFalse(feedback[-1]["es_una_medicion_fisica"])
        ctx = context_for(self.world, self.p, [], "Día 2")
        self.assertEqual(ctx["evaluaciones_externas_recientes"][-1]["fundamento_humano"],
                         "Una casilla de agua no es caminable")
        reduced = compact_context(ctx, char_budget=2000)
        self.assertIn("evaluaciones_externas_recientes", reduced)

    def test_review_history_remains_visible_after_nilo_adds_evidence(self):
        self.p["action_outcomes"] = [outcome("act-1", "go")]
        self.assertTrue(submit_debug_report(self.p, debug_step(), "Día 1")[0])
        report = self.p["proposals"][-1]
        review_proposal(self.p, report["id"], "ampliar",
                        "Necesito una prueba más específica", "Día 2")
        self.p["action_outcomes"].append(outcome("act-2", "go"))
        ok, _ = submit_debug_report(self.p, debug_step(
            evidence_ids=["act-2"]), "Día 3")
        self.assertTrue(ok)
        self.assertEqual(report["evidence_relation"], "referencia_explicita")
        self.assertEqual(report["status"], "pendiente")
        feedback = human_review_feedback(self.p["proposals"])
        self.assertEqual(feedback[-1]["fundamento_humano"],
                         "Necesito una prueba más específica")

    def test_late_review_of_older_proposal_remains_retrievable(self):
        proposals = [
            {"id": "sol-old", "type": "debug", "title": "Antigua",
             "review": {"decision": "ampliar", "reason": "Evidencia reciente",
                        "when": "Día 20 · 09:00"}},
            {"id": "sol-new", "type": "physics", "phenomenon": "Nueva",
             "review": {"decision": "rechazar", "reason": "Antiguo",
                        "when": "Día 3 · 12:00"}},
        ]
        self.assertEqual(human_review_feedback(proposals, limit=1)[0]["solicitud_id"],
                         "sol-old")

    def test_action_manual_advises_real_ids(self):
        self.assertIn("no-modelo-", ACTION_GUIDE["propose"])
        self.assertIn("act-", ACTION_GUIDE["report_issue"])


if __name__ == "__main__":
    unittest.main()
