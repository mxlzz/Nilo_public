"""Etapa 10: contexto modular experimental con baseline preservado.

No utiliza la red, no escribe partidas y compara cuerpos de solicitud reales.
"""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from auditar_contexto_llm import PROVIDERS, scenario_context
from nilo_runtime.agent.context_modules import (
    semantic_context, detect_focuses, modular_context, modular_instructions,
    policy_sections,
)
from nilo_runtime.agent.gateway import build_deliberation_request
from nilo_runtime.core.operations import registered_operations
from nilo_runtime.core.lab_settings import baseline, validate
from nilo_runtime.cognition.memory import recall_relevant
from nilo_runtime.labs.hub import LabHub, _request


def sent_context(provider, payload):
    if provider == "gemini":
        return json.loads(payload["contents"][0]["parts"][0]["text"].split(
            "SITUACIÓN REAL: ", 1)[1])
    return json.loads(payload["messages"][1]["content"])


class ModularSelection10(unittest.TestCase):
    def test_empty_fields_are_explicitly_whitelisted(self):
        context = {"momento": "Día 1", "posición": [0, 0, 0],
                   "proyecto_actual": None, "resultados_de_acciones": [],
                   "inventario_materiales": {"madera": 0}, "estancamiento_detectado": False,
                   "propuestas_pendientes": [], "revision_de_estrategia": None,
                   "ultimo_cierre_rechazado": None, "regla": "No inventar."}
        original = copy.deepcopy(context)
        selected = semantic_context(context)
        self.assertEqual(original, context)
        self.assertNotIn("propuestas_pendientes", selected)
        self.assertNotIn("revision_de_estrategia", selected)
        for key in ("proyecto_actual", "resultados_de_acciones",
                    "inventario_materiales", "estancamiento_detectado",
                    "ultimo_cierre_rechazado", "regla"):
            self.assertEqual(selected[key], context[key])

    def test_duplicate_evidence_keeps_conflicts_and_different_ids(self):
        row = {"id": "act-1", "hecho": "Algo cambió", "fuente": "motor"}
        conflict = {"id": "act-1", "hecho": "No cambió", "fuente": "motor"}
        original = [row, copy.deepcopy(row), conflict,
                    {"id": "act-2", "hecho": "Algo cambió", "fuente": "motor"},
                    {"hecho": "sin referencia"}, {"hecho": "sin referencia"}]
        selected = semantic_context({"memorias_relevantes": original,
                                     "resultados_de_acciones": [row, row]})
        self.assertEqual(len(selected["memorias_relevantes"]), 5)
        self.assertEqual(len(selected["resultados_de_acciones"]), 1)
        self.assertIn(conflict, selected["memorias_relevantes"])
        self.assertEqual(len(original), 6)

    def test_multifocus_from_research_and_action_not_only_project_title(self):
        context = {
            "proyecto_actual": {"title": "Explorar una ruta del norte"},
            "investigaciones_activas": [
                {"question": "¿Qué resistencia tiene este mineral oscuro?"}],
            "resultados_de_acciones": [{"operacion": "craft", "destino": "punta"}],
        }
        focuses = detect_focuses(context)
        self.assertIn("navegacion", focuses)
        self.assertIn("experimentacion", focuses)
        self.assertIn("fabricacion", focuses)
        self.assertEqual(focuses, detect_focuses(copy.deepcopy(context)))

    def test_unreduced_minimal_context_has_no_fake_reduction_marker(self):
        sample = {"momento": "Día 1", "posición": [0, 0, 0]}
        self.assertEqual(modular_context(sample, provider="gemini"), sample)
        self.assertEqual(modular_context(sample, provider="groq"), sample)

    def test_protected_incomplete_and_negative_data_survive(self):
        sample = {"momento": "Día 1", "posición": [0, 0, 0],
                  "proyecto_actual": None,
                  "necesidades": {"hidratacion": "sin sed"},
                  "inventario_materiales": {"fibra": 0},
                  "ultimo_cierre_rechazado": {"motivo": "sin mediciones"},
                  "resultados_de_acciones": []}
        selected = modular_context(sample, provider="gemini")
        for key in ("proyecto_actual", "ultimo_cierre_rechazado",
                    "resultados_de_acciones", "inventario_materiales"):
            self.assertIn(key, selected)
            self.assertEqual(sample[key], selected[key])
        self.assertEqual(sample["inventario_materiales"]["fibra"], 0)

    def test_policy_and_operation_index_come_from_real_registry(self):
        focus = {"proyecto_actual": {"title": "Construir un instrumento"},
                 "resultados_de_acciones": [{"operacion": "experiment"}]}
        ids = [key for key, _ in policy_sections(focus, "gemini")]
        self.assertIn("identidad", ids)
        self.assertIn("mediciones", ids)
        self.assertIn("investigacion", ids)
        self.assertIn("agenda", ids)
        system, manual = modular_instructions(focus, "gemini")
        self.assertIn("REGLAS GENERALES", manual)
        for name in registered_operations():
            with self.subTest(op=name):
                self.assertIn('"op":"' + name + '"', manual)
        compact_system, compact_manual = modular_instructions(focus, "groq")
        self.assertEqual(compact_manual, "")
        for name in registered_operations():
            self.assertIn('"op":"' + name + '"', compact_system)
        self.assertNotIn('"menor_que":60', system)

    def test_both_provider_payloads_keep_literal_roles_and_baseline(self):
        context = scenario_context("contexto_extenso")
        original = copy.deepcopy(context)
        for provider in ("gemini", "groq"):
            with self.subTest(provider=provider):
                cfg = dict(PROVIDERS[provider])
                _, old, _ = build_deliberation_request(cfg, context)
                cfg["_LAB_CONTEXT_MODE"] = "modular"
                _, candidate, _ = build_deliberation_request(cfg, context)
                old_context = sent_context(provider, old)
                new_context = sent_context(provider, candidate)
                self.assertEqual(original, context)
                self.assertIn("posición", new_context)
                self.assertIn("necesidades", new_context)
                self.assertNotIn("valores", new_context["necesidades"])
                self.assertIn("proyecto_actual", new_context)
                self.assertNotEqual(old, candidate)
                self.assertTrue(new_context.keys())
                json.dumps(candidate, ensure_ascii=False)
                self.assertTrue(old_context.keys())
                if provider == "groq":
                    self.assertLessEqual(len(json.dumps(candidate, ensure_ascii=False).encode()), 14500)
                else:
                    self.assertIn("SITUACIÓN REAL: ", candidate["contents"][0]["parts"][0]["text"])
        for invalid in ("", "unknown", 123, True, None):
            cfg = dict(PROVIDERS["gemini"], _LAB_CONTEXT_MODE=invalid)
            if invalid is None or invalid == "":
                # La ausencia y la cadena vacía mantienen el baseline antiguo.
                self.assertEqual(build_deliberation_request(cfg, context)[1],
                                 build_deliberation_request(PROVIDERS["gemini"], context)[1])
            else:
                with self.assertRaises(ValueError):
                    build_deliberation_request(cfg, context)

    def test_memory_retrieval_respects_simultaneous_open_topics(self):
        person = {"pos": [10, 10, 0],
                  "project": {"id": "p1", "title": "Explorar rutas", "reason": ""},
                  "active_research": None,
                  "research": [{"state": "abierta", "question": "¿Resiste el mineral oscuro?",
                                "hypothesis": "El mineral soportará una carga"}],
                  "action_outcomes": [{"target": "madera", "op": "gather"}],
                  "life_history": [
                      {"id": "exp-1", "fact": "Observé mineral oscuro en una muestra.",
                       "action": "inspect", "successful": True},
                      {"id": "exp-2", "fact": "Recolecté madera junto al sendero.",
                       "action": "gather", "successful": True}]}
        world = {"sites": {}, "revealed": []}
        before = copy.deepcopy((person, world))
        seen = recall_relevant(person, world)
        self.assertEqual({r["id"] for r in seen}, {"exp-1", "exp-2"})
        self.assertEqual((person, world), before)


class ModularHub10(unittest.TestCase):
    def test_hub_can_compare_without_saving_or_applying(self):
        with tempfile.TemporaryDirectory() as tmp:
            hub = LabHub(Path(tmp))
            profile = baseline()
            context = scenario_context("inicio")
            before = _request(profile, context, "gemini")
            after = _request(profile, context, "gemini", context_mode="modular")
            self.assertEqual(before["modo_contexto"], "baseline")
            self.assertEqual(after["modo_contexto"], "modular")
            self.assertFalse(after["enviado_a_llm"])
            self.assertNotEqual(before["solicitud_serializada"],
                                after["solicitud_serializada"])
            self.assertEqual(validate(profile), profile)
            with self.assertRaises(ValueError):
                _request(profile, context, "gemini", context_mode="invalid")
            illegal = dict(profile, context_mode="modular")
            with self.assertRaises(ValueError):
                validate(illegal)
            self.assertFalse((Path(tmp) / "lab_profiles" / "active.json").exists())


if __name__ == "__main__":
    unittest.main()
