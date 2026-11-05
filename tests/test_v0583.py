"""Contrato ActionResult: evidencia verificable, independientemente de la narrativa."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from action_results import ActionResult, evidence_before, result_from_execution
from brain import context_for, compact_context
from nilo import Simulation, initial_state


class StructuredResult(unittest.TestCase):
    def setUp(self):
        self.person = initial_state(7321)["person"]

    def test_status_does_not_parse_facts(self):
        action = {"op": "inspect", "target": "suelo"}
        self.assertEqual(
            ActionResult.from_legacy(action, ["FÍSICA NO IMPLEMENTADA: inventado"], True, False).status,
            "verified_success",
        )
        result = ActionResult.from_legacy(
            action, ["Encontré agua"], False, True, no_evaluable=True,
        )
        self.assertEqual(result.status, "no_evaluable")
        self.assertFalse(result.success)
        self.assertEqual(result.to_record()["facts"], ["Encontré agua"])
        self.assertEqual(result.as_legacy(), (0.0, ["Encontré agua"], False, True))

    def test_physical_evidence_from_new_material_test_not_description(self):
        step = {"op": "experiment", "target": "piedra", "method": "golpear"}
        before = evidence_before(self.person)
        self.person["knowledge"]["piedra|golpear"] = "Observación verificada."
        first = result_from_execution(step, (18, ["Texto ajeno al resultado"], True, True),
                                      self.person, before)
        second = result_from_execution(step, (18, ["Cambié toda la narración"], True, True),
                                       self.person, before)
        self.assertEqual(first.physical, second.physical)
        self.assertEqual(first.physical["kind"], "material")
        self.assertIn("dureza", first.physical["metrics"])
        self.assertEqual(first.status, "verified_success")

    def test_repeat_experiment_without_new_knowledge_yields_no_new_measure(self):
        step = {"op": "experiment", "target": "piedra", "method": "golpear"}
        self.person["knowledge"]["piedra|golpear"] = "Ya medí esto."
        before = evidence_before(self.person)
        result = result_from_execution(step, (3, ["lo repetí"], True, False), self.person, before)
        self.assertIsNone(result.physical)

    def test_missing_physics_detected_from_recorded_attempt(self):
        step = {"op": "experiment", "target": "piedra", "method": "evaporar"}
        before = evidence_before(self.person)
        self.person.setdefault("unmodeled_attempts", []).append({"id": "fen-1"})
        result = result_from_execution(step, (6, ["Un comentario arbitrario"], False, False),
                                       self.person, before)
        self.assertEqual(result.status, "no_evaluable")
        self.assertIsNone(result.physical)

    def test_no_phantom_tool_measurements(self):
        self.person["items"].append({
            "id": "obj-1", "name": "recipiente", "form": "recipiente",
            "tests": [{"method": "llenar", "target": "agua", "success": True}],
        })
        step = {"op": "use", "item": "recipiente", "method": "llenar", "target": "agua"}
        before = evidence_before(self.person)
        result = result_from_execution(step, (3, ["Llené el recipiente"], True, False),
                                       self.person, before)
        self.assertIsNone(result.physical)

    def test_water_containment_alias_reads_a_real_new_trial(self):
        self.person["items"].append({
            "id": "obj-3", "name": "vaso", "form": "recipiente",
            "materials": ["arcilla"], "geometry": {"shape": "hueco", "size": 2},
            "tests": [],
        })
        step = {"op": "use", "item": "vaso", "method": "contener", "target": "agua"}
        before = evidence_before(self.person)
        self.person["items"][-1]["tests"].append({
            "method": "llenar", "target": "agua", "success": True,
        })
        result = result_from_execution(step, (16, ["Relato cualquiera"], True, True),
                                       self.person, before)
        self.assertEqual(result.physical["kind"], "recipiente")
        self.assertIn("capacidad_util_agua", result.physical["metrics"])

    def test_new_water_trial_has_measured_metrics_without_text_trigger(self):
        self.person["items"].append({
            "id": "obj-2", "name": "plataforma", "form": "simple",
            "materials": ["madera"], "geometry": {"shape": "plataforma", "size": 2},
            "tests": [], "resistance": 6,
        })
        step = {"op": "use", "item": "plataforma", "method": "flotar", "target": "agua"}
        before = evidence_before(self.person)
        self.person["items"][-1]["tests"].append({
            "method": "flotar", "target": "agua", "success": True,
        })
        result = result_from_execution(step, (20, ["No contiene una descripción relevante"], True, True),
                                       self.person, before)
        self.assertEqual(result.physical["kind"], "flotacion")
        self.assertIn("empuje", result.physical["metrics"])


class StructuredIntegration(unittest.TestCase):
    def test_real_tick_archives_structured_data_and_llm_sees_it(self):
        with tempfile.TemporaryDirectory() as directory:
            sim = Simulation(db_path=Path(directory) / "test.sqlite")
            try:
                p = sim.s["person"]
                sim.s["planning"] = True
                p["plan"] = [{"op": "experiment", "target": "piedra", "method": "golpear"}]
                sim.change_speed(speed=60)
                for _ in range(5):
                    sim.tick(15)
                outcomes = p["action_outcomes"]
                self.assertTrue(outcomes)
                physical = outcomes[-1]["action_result"]["physical"]
                self.assertEqual(outcomes[-1]["action_result"]["status"], "verified_success")
                self.assertEqual(physical["kind"], "material")
                self.assertEqual(outcomes[-1]["evaluation_status"], "verified_success")
                self.assertEqual(p["measurements"][-1]["physical"], physical)
                context = context_for(sim.s["world"], p, [], sim.stamp(), scenario=sim.scenario)
                evidence = context["resultados_de_acciones"][-1]["evidencia_fisica"]
                self.assertEqual(evidence, physical)
                compact = compact_context(context)
                self.assertTrue(compact.get("resultados_de_acciones"))
                json.dumps(outcomes[-1]["action_result"])
            finally:
                sim.conn.close()


if __name__ == "__main__":
    unittest.main()
