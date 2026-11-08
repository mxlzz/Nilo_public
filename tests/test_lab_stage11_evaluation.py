"""Etapa 11 · aceptación del protocolo A/B y métricas sin secretos."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nilo_runtime.core.lab_settings import baseline
from nilo_runtime.labs.ab_experiment import context_pair, live_pair
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


if __name__ == "__main__":
    unittest.main()
