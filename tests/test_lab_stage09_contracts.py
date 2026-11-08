"""Etapa 09: contradicciones comprobadas entre prompt, normalizador y registro.
Regresiones sin red, sin mundo real y sin modificar SQLite.
"""
from __future__ import annotations

import copy
import unittest

from inventions import register_design
from nilo_runtime.agent import prompts
from nilo_runtime.agent.responses import normalize_decision
from nilo_runtime.core.operations import get_spec, manual_lines


def decision(**fields):
    return {"cuaderno": "Anoto lo que pienso.", "accion_proyecto": "sin_proyecto",
            "plan": [{"op": "inspect", "target": "suelo"}], **fields}


class Stage09Contracts(unittest.TestCase):
    def test_design_prediction_text_reaches_persisted_design(self):
        step = {"op": "design", "name": "punta", "purpose": "perforar roca",
                "principle": "un mineral duro puede fracturar roca",
                "components": [{"name": "cabeza", "material": "mineral oscuro"}],
                "prediction": "  podría fracturar una muestra  "}
        payload = decision(plan=[step])
        original = copy.deepcopy(payload)
        result = normalize_decision(payload)
        self.assertEqual(payload, original)
        self.assertEqual(result["plan"][0]["prediction"], "podría fracturar una muestra")
        person = {}
        ok, message = register_design(person, result["plan"][0], "Día 1")
        self.assertTrue(ok, message)
        self.assertEqual(person["designs"][0]["versions"][0]["prediction"],
                         "podría fracturar una muestra")
        self.assertEqual(person["designs"][0]["status"], "hipotesis")

    def test_design_prediction_is_not_confused_with_measured_prediction(self):
        design = decision(plan=[{"op": "design", "prediction": "  " }])
        result = normalize_decision(design)
        self.assertNotIn("prediction", result["plan"][0])
        numeric = {"hypothesis": "Creo que resistirá", "expected_effect": "Soporta una carga"}
        outcome = normalize_decision(decision(plan=[{"op": "use", "prediction": numeric}]))
        self.assertIsInstance(outcome["plan"][0]["prediction"], dict)

    def test_null_optional_text_never_becomes_literal_none(self):
        fields = ("pregunta", "hipotesis", "objetivo", "motivo", "proyecto_id",
                  "prueba_cierre", "estado_actual")
        raw = decision(**{key: None for key in fields})
        raw["accion_proyecto"] = None
        result = normalize_decision(raw)
        for key in fields:
            with self.subTest(field=key):
                self.assertEqual(result[key], "")
        self.assertEqual(result["accion_proyecto"], "nuevo")
        self.assertEqual(result["cuaderno"], "Anoto lo que pienso.")

    def test_notebook_limit_matches_prompt(self):
        result = normalize_decision(decision(cuaderno="á" * 430))
        self.assertEqual(len(result["cuaderno"]), 350)
        self.assertIn("máximo 350 caracteres", prompts.SYSTEM)
        self.assertIn("máximo 350 caracteres", prompts.GROQ_SYSTEM)
        with self.assertRaises(ValueError):
            normalize_decision(decision(cuaderno=None))

    def test_one_action_contract_and_empty_close(self):
        self.assertEqual(len(normalize_decision(decision())["plan"]), 1)
        self.assertEqual(len(normalize_decision(decision(
            plan=[{"op": "inspect", "target": "suelo"}] * 14))["plan"]), 12)
        self.assertEqual(normalize_decision(decision(
            accion_proyecto="pausar", plan=[]))["plan"], [])
        with self.assertRaises(ValueError):
            normalize_decision(decision(plan=[]))
        self.assertIn("1 a 12 acciones", prompts.SYSTEM)
        self.assertIn("1–12 operaciones", prompts.GROQ_SYSTEM)

    def test_descend_manual_and_hidden_need_increase(self):
        descend = get_spec("descend").description
        ascend = get_spec("ascend").description
        self.assertIn('{"op":"descend"}', descend)
        self.assertIn("entrada", descend)
        self.assertNotEqual(descend, ascend)
        self.assertIn('{"op":"descend"}', "\n".join(manual_lines()))
        drink = get_spec("drink").description
        self.assertNotIn("+27 hidratación", drink)
        self.assertIn("0,18", drink)  # Cantidad real de agua, no reserva corporal.


if __name__ == "__main__":
    unittest.main()
