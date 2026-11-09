"""Etapa 11 · aceptación del protocolo A/B y métricas sin secretos."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nilo_runtime.core.lab_settings import baseline
from nilo_runtime.labs.ab_experiment import (
    context_pair, live_pair, _response_warnings, _execution_results,
    _drive_decision, _SilentTrace,
)
from nilo_runtime.agent.responses import normalize_decision
from nilo_runtime.agent.context_modules import modular_instructions
from nilo_runtime.labs.sandbox import SimulationSandbox
from nilo_runtime.labs.evaluation_11 import (
    analyze_context_ab, analyze_live_ab, SCHEMA,
)
from nilo_runtime.labs.hub import LabHub
from tools.evaluar_laboratorio_11 import evaluate, markdown


def fake_post(url, payload, headers, provider):
    assert provider == "groq"
    assert headers["Authorization"] == "Bearer sintética"
    assert payload["messages"][0]["role"] == "system"
    return {
        "choices": [{"message": {"content": json.dumps({
            "cuaderno": "Registro una decisión.",
            "accion_proyecto": "sin_proyecto",
            "plan": [{"op": "wait", "minutes": 20}],
        })}}],
        "usage": {"prompt_tokens": 290, "completion_tokens": 65},
    }


class OfflineStage11(unittest.TestCase):
    def test_offline_ab_modular_is_literal_and_private(self):
        with tempfile.TemporaryDirectory() as td:
            hub = LabHub(Path(td))
            with patch("nilo_runtime.labs.ab_experiment.gateway._post",
                       side_effect=AssertionError("No usar red en offline")):
                result = context_pair(hub, baseline(), provider="gemini",
                                      seed=7321, context_mode="modular")
            original = copy.deepcopy(result)
            metric = analyze_context_ab(result)
            self.assertEqual(result, original)
            self.assertEqual(metric["schema"], SCHEMA)
            self.assertEqual(metric["kind"], "offline_context_ab")
            self.assertEqual(metric["sample_size"], 0)
            self.assertFalse(metric["behavior_evaluated"])
            self.assertFalse(metric["causal_claim_allowed"])
            self.assertTrue(metric["both_preserve_required_fields"])
            self.assertEqual(metric["baseline"]["context_mode"], "baseline")
            self.assertEqual(metric["variant"]["context_mode"], "modular")
            self.assertEqual(metric["baseline"]["model"], metric["variant"]["model"])
            self.assertNotEqual(metric["baseline"]["request_sha256"],
                                metric["variant"]["request_sha256"])
            self.assertNotIn("SITUACIÓN REAL", json.dumps(metric, ensure_ascii=False))
            self.assertNotIn("Registro una decisión", json.dumps(metric, ensure_ascii=False))

    def test_all_providers_and_seeds_offline_matrix(self):
        with patch("nilo_runtime.labs.ab_experiment.gateway._post",
                   side_effect=AssertionError("Red no autorizada")):
            result = evaluate((315, 7321), ("groq", "gemini"))
        self.assertEqual(result["cases"], 4)
        self.assertEqual(result["llm_calls"], 0)
        self.assertFalse(result["behavior_evaluated"])
        self.assertFalse(result["original_worlds_modified"])
        self.assertEqual({r["provider"] for r in result["rows"]}, {"groq", "gemini"})
        self.assertTrue(all(r["both_preserve_required_fields"] for r in result["rows"]))
        for row in result["rows"]:
            self.assertGreater(row["baseline"]["bytes_request"], 0)
            self.assertGreater(row["variant"]["bytes_request"], 0)
            self.assertTrue(len(row["baseline"]["request_sha256"]) == 64)
        doc = markdown(result)
        self.assertIn("gemini", doc)
        self.assertIn("groq", doc)
        self.assertNotIn("systemInstruction", json.dumps(result))

    def test_wrong_mode_rejected_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            hub = LabHub(Path(td))
            for bad in ("", "legacy", None, 123, True, []):
                with self.subTest(mode=bad), self.assertRaises(ValueError):
                    context_pair(hub, baseline(), provider="groq",
                                 seed=9, context_mode=bad)
                with self.subTest(live=bad), self.assertRaises(ValueError):
                    live_pair(hub, baseline(), provider="groq",
                              seed=9, confirm=True, context_mode=bad)

    def test_reject_corrupted_request_and_untrusted_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            pair = context_pair(LabHub(Path(td)), baseline(),
                                provider="groq", seed=7321, context_mode="modular")
        corrupt = copy.deepcopy(pair)
        corrupt["variant"]["huella_solicitud_calculada"] = "0" * 64
        with self.assertRaises(ValueError):
            analyze_context_ab(corrupt)
        corrupt = copy.deepcopy(pair)
        corrupt["modified_original_world"] = True
        with self.assertRaises(ValueError):
            analyze_context_ab(corrupt)
        corrupt = copy.deepcopy(pair)
        corrupt["variant"]["enviado_a_llm"] = True
        with self.assertRaises(ValueError):
            analyze_context_ab(corrupt)


class LiveStage11(unittest.TestCase):
    def test_two_branch_calls_use_modular_only_for_b(self):
        with tempfile.TemporaryDirectory() as td:
            hub = LabHub(Path(td))
            requests = []
            def record(url, payload, headers, provider):
                requests.append(copy.deepcopy(payload))
                return fake_post(url, payload, headers, provider)
            with patch("nilo_runtime.labs.ab_experiment.config",
                       return_value={"GROQ_API_KEY": "sintética",
                                     "MIN_REAL_SECONDS_BETWEEN_CALLS": "15"}):
                result = live_pair(hub, baseline(), provider="groq",
                                   seed=7321, turns=1, context_mode="modular",
                                   confirm=True, poster=record, sleep_fn=lambda _:None)
        self.assertEqual(len(requests), 2)
        self.assertEqual(result["llm_calls"], 2)
        self.assertNotEqual(requests[0], requests[1])
        self.assertTrue(result["modified_original_world"] is False)
        self.assertEqual(result["baseline"]["turns"][0]["pre_context_sha256"],
                         result["variant"]["turns"][0]["pre_context_sha256"])
        self.assertIsNone(result["baseline"]["turns"][0]["world_effect"])
        summary = analyze_live_ab(result)
        self.assertEqual(summary["context_mode"], "modular")
        self.assertEqual(summary["baseline"]["normalized_decisions"], 1)
        self.assertEqual(summary["variant"]["normalized_decisions"], 1)
        self.assertFalse(summary["causal_claim_allowed"])
        self.assertNotIn("sintética", json.dumps(summary, ensure_ascii=False))
        self.assertNotIn("Registro una decisión", json.dumps(summary, ensure_ascii=False))

    def test_multiturn_executes_in_two_temporary_worlds(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("nilo_runtime.labs.ab_experiment.config",
                       return_value={"GROQ_API_KEY": "sintética",
                                     "MIN_REAL_SECONDS_BETWEEN_CALLS": "15"}):
                result = live_pair(LabHub(Path(td)), baseline(), provider="groq",
                                   seed=315, turns=2, context_mode="modular",
                                   confirm=True, poster=fake_post, sleep_fn=lambda _:None)
        self.assertEqual(result["llm_calls"], 4)
        metric = analyze_live_ab(result)
        self.assertEqual(metric["baseline"]["normalized_decisions"], 2)
        self.assertEqual(metric["variant"]["normalized_decisions"], 2)
        self.assertFalse(metric["causal_claim_allowed"])

    def test_live_report_rejects_missing_consent(self):
        report = {"experiment_type": "llm_two_branch_deliberation",
                  "explicit_live_consent": False,
                  "baseline": {"turns": []}, "variant": {"turns": []}}
        with self.assertRaises(ValueError):
            analyze_live_ab(report)


class CorrectionsStage11(unittest.TestCase):
    def test_detect_misspelled_hypothesis_without_rewriting_model_response(self):
        decision = {
            "cuaderno": "Estoy explorando.",
            "pregunta": "¿Hay agua?",
            "hipostesis": "La arboleda podría indicar agua.",
            "objetivo": "Explorar cerca de los árboles.",
            "motivo": "Reconocer el terreno.",
            "accion_proyecto": "nuevo",
            "plan": [{"op": "explore"}],
        }
        original = copy.deepcopy(decision)
        normalized = normalize_decision(decision)
        self.assertEqual(normalized["hipotesis"], "")
        warnings = _response_warnings(decision, normalized)
        self.assertIn({"code": "possible_misspelled_field",
                       "field": "hipotesis", "received_key": "hipostesis"},
                      warnings)
        self.assertEqual(decision, original)
        self.assertEqual(normalized["plan"][0]["op"], "explore")

    def test_trace_stages_do_not_claim_plan_acceptance_is_execution_success(self):
        submitted = [{"op": "explore"}, {"op": "go", "target": "agua"},
                     {"op": "inspect", "target": "roca"}]
        admitted = submitted[:2]
        outcomes = [
            {"id": "act-1", "op": "explore", "successful": True,
             "action_result": {"success": True, "status": "verified_success",
                               "facts": ["Recorrí cuatro tramos."]},
             "physical_result": {"measurement_id": "med-1", "inventory_delta": {}}},
            {"id": "act-2", "op": "go", "successful": False,
             "action_result": {"success": False, "status": "precondition_failed",
                               "facts": ["No hay orilla conocida."]}},
        ]
        rows = _execution_results(
            submitted, admitted, outcomes,
            rejected_reasons=["Plan validado: inspect: Objetivo fuera de alcance."])
        self.assertEqual([r["state"] for r in rows],
                         ["completada", "bloqueada", "filtrada_antes_de_ejecutar"])
        self.assertEqual(rows[2]["reason"],
                         "Plan validado: inspect: Objetivo fuera de alcance.")
        self.assertEqual(rows[2]["reason_source"], "motor.strategy_feedback")
        self.assertEqual(rows[0]["action_id"], "act-1")
        self.assertEqual(rows[0]["measurement_id"], "med-1")
        self.assertFalse(rows[1]["success"])
        self.assertIn("No hay orilla", rows[1]["facts"][0])
        self.assertIsNone(rows[2]["action_id"])

    def test_unmodeled_physics_is_not_a_failed_experiment(self):
        row = {"id": "act-no-modelo", "op": "experiment", "successful": False,
               "action_result": {"success": False, "status": "no_evaluable",
                                 "facts": ["El modelo no representa esa física."]}}
        result = _execution_results([{"op": "experiment"}],
                                    [{"op": "experiment"}], [row])
        self.assertEqual(result[0]["state"], "no_evaluable")
        self.assertFalse(result[0]["success"])

    def test_real_simulation_records_operations_without_mutating_source(self):
        lab = SimulationSandbox(_SilentTrace)
        try:
            lab.reset("nuevo", 7321, False)
            plan = normalize_decision({
                "cuaderno": "Exploro y busco agua.",
                "objetivo": "Encontrar una orilla cercana.",
                "motivo": "Conocer el entorno.",
                "accion_proyecto": "nuevo",
                "plan": [{"op": "explore"}, {"op": "go", "target": "agua"}],
            })
            report = _drive_decision(lab, plan)
            self.assertTrue(report["applied"])
            self.assertTrue(report["plan_accepted"])
            self.assertEqual(report["submitted_operations"], 2)
            self.assertLessEqual(report["admitted_operations"], 2)
            self.assertEqual(len(report["operation_results"]), 2)
            self.assertIn(report["operation_results"][0]["state"],
                          ("completada", "fallida"))
            self.assertNotEqual(report["operation_results"][1]["state"],
                                "completada")
            if report["operation_results"][1]["state"] == "filtrada_antes_de_ejecutar":
                self.assertEqual(report["operation_results"][1]["reason_source"],
                                 "motor.strategy_feedback")
            self.assertEqual(report["recorded_successes"],
                             sum(s["state"] == "completada"
                                 for s in report["operation_results"]))
            self.assertEqual(report["recorded_failures"],
                             sum(s["state"] == "fallida"
                                 for s in report["operation_results"]))
        finally:
            lab.close()

    def test_pausing_project_does_not_discard_voluntary_rest(self):
        """Caso real: Gemini pidió pausar el proyecto y descansar 120 min."""
        lab = SimulationSandbox(_SilentTrace)
        try:
            lab.reset("nuevo", 7321, False)
            first = normalize_decision({
                "cuaderno": "Voy a reconocer el terreno.",
                "objetivo": "Investigar si hay un acceso junto a las ruinas.",
                "motivo": "Quiero orientarme.",
                "accion_proyecto": "nuevo",
                "plan": [{"op": "inspect", "x": 15, "y": 10}],
            })
            _drive_decision(lab, first)
            original_project = lab.sim.s["person"]["project"]
            self.assertIsNotNone(original_project)
            project_id = original_project["id"]
            t0 = lab.sim.s["person"]["clock_minutes"]
            journal_count = len(lab.sim.s["journal"])
            pause = normalize_decision({
                "cuaderno": "Pausaré la investigación y descansaré.",
                "objetivo": original_project["title"],
                "motivo": "El procedimiento ya no aporta información.",
                "proyecto_id": project_id,
                "accion_proyecto": "pausar",
                "revisar_en_minutos": 120,
                "plan": [{"op": "rest", "minutes": 120}],
            })
            result = _drive_decision(lab, pause)
            self.assertTrue(result["plan_accepted"])
            self.assertEqual(result["submitted_operations"], 1)
            self.assertEqual(result["admitted_operations"], 1)
            self.assertEqual(result["operation_results"][0]["op"], "rest")
            self.assertEqual(result["operation_results"][0]["state"], "completada")
            self.assertGreater(result["time_after"] - t0, 110)
            self.assertIsNone(lab.sim.s["person"]["project"])
            archived = [p for p in lab.sim.s["person"]["projects"]
                        if p["id"] == project_id]
            self.assertEqual(len(archived), 1)
            self.assertEqual(archived[0]["status"], "pausado")
            self.assertGreater(len(lab.sim.s["journal"]), journal_count)
            self.assertEqual(lab.sim.s["journal"][-1]["project_id"], project_id)
            self.assertIn("Pausaré", lab.sim.s["journal"][-1]["text"])
        finally:
            lab.close()

    def test_pausing_without_plan_still_archives_and_records_cuaderno(self):
        lab = SimulationSandbox(_SilentTrace)
        try:
            lab.reset("nuevo", 7321, False)
            _drive_decision(lab, normalize_decision({
                "cuaderno": "Quiero averiguar si hay agua.",
                "objetivo": "Buscar agua",
                "accion_proyecto": "nuevo",
                "plan": [{"op": "wait", "minutes": 2}],
            }))
            project_id = lab.sim.s["person"]["project"]["id"]
            result = _drive_decision(lab, normalize_decision({
                "cuaderno": "Pauso esta idea; todavía no tengo evidencia.",
                "objetivo": "Buscar agua",
                "proyecto_id": project_id,
                "accion_proyecto": "pausar",
                "plan": [],
            }))
            self.assertEqual(result["submitted_operations"], 0)
            self.assertFalse(result["plan_accepted"])
            self.assertIsNone(lab.sim.s["person"]["project"])
            self.assertEqual(lab.sim.s["person"]["projects"][-1]["status"], "pausado")
            self.assertIn("Pauso", lab.sim.s["journal"][-1]["text"])
        finally:
            lab.close()

    def test_modular_start_has_full_navigation_contracts_both_providers(self):
        context = {"momento": "Día 1 · 00:00", "posición": [15, 10, 0],
                   "proyecto_actual": None, "investigaciones_activas": [],
                   "resultados_de_acciones": []}
        for provider in ("gemini", "groq"):
            with self.subTest(provider=provider):
                system, manual = modular_instructions(context, provider)
                content = system + manual
                self.assertIn('{"direction":"north|south|east|west"}', content)
                self.assertIn('{"op":"go","target":"agua"}', content)
                self.assertIn("frontera desconocida", content)

    def test_live_summary_tracks_failures_and_warnings_without_response_text(self):
        result = {
            "experiment_type": "llm_two_branch_multiturn",
            "explicit_live_consent": True, "modified_original_world": False,
            "provider": "gemini", "seed": 7321, "reference_sha256": "a" * 64,
            "context_mode": "modular", "llm_calls": 4, "max_llm_calls": 4,
            "baseline": {"turns": [
                {"turn": 1,
                 "response": {"normalized": {"plan": [{"op": "explore"}]},
                              "validation_warnings": [], "tokens": {}},
                 "world_effect": {"applied": True, "submitted_operations": 1,
                                  "admitted_operations": 1,
                                  "operation_results": [{"state": "completada"}],
                                  "recorded_successes": 1, "recorded_failures": 0}},
            ]},
            "variant": {"turns": [
                {"turn": 1,
                 "response": {"normalized": {"plan": [{"op": "go", "target": "agua"}]},
                              "validation_warnings": [{"code": "possible_misspelled_field",
                                                       "field": "hipotesis"}],
                              "tokens": {}},
                 "world_effect": {"applied": True, "submitted_operations": 1,
                                  "admitted_operations": 1,
                                  "operation_results": [{"state": "fallida",
                                                         "facts": ["No hay agua"]}],
                                  "recorded_successes": 0, "recorded_failures": 1}},
            ]},
        }
        summary = analyze_live_ab(result)
        self.assertEqual(summary["variant"]["semantic_warnings"], 1)
        self.assertEqual(summary["variant"]["recorded_physical_failures"], 1)
        self.assertEqual(summary["variant"]["turns"][0]["observed_operation_states"],
                         {"fallida": 1})
        self.assertNotIn("No hay agua", json.dumps(summary, ensure_ascii=False))
        self.assertFalse(summary["causal_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
