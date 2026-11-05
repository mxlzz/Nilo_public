"""Etapa 03: éxito tipado, procedencia de mediciones y compatibilidad de tuplas."""
from __future__ import annotations

from copy import deepcopy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from action_results import ActionResult, evidence_before, result_from_execution
from nilo_runtime.core.outcomes import (
    ActionResult as CoreActionResult, LegacyExecution, RecordedEffect,
    causal_event_from_measurement,
    CAUSAL_EVENT_SCHEMA_VERSION,
)
from nilo import Simulation, initial_state
from habits import record_skill


class ActionResultContract(unittest.TestCase):
    def test_one_type_shared_with_legacy_import(self):
        self.assertIs(ActionResult, CoreActionResult)

    def test_legacy_projection_has_same_four_fields_and_json_record(self):
        source = {"kind": "material", "subject": "madera",
                  "metrics": {"dureza": 4}}
        result = ActionResult.from_legacy(
            {"op": "experiment"}, ["Golpeé la muestra."], True, True, 12,
            physical=source)
        self.assertEqual(result.as_legacy(), (12.0, ["Golpeé la muestra."], True, True))
        self.assertEqual(set(result.to_record()), {
            "op", "status", "success", "notable", "duration_minutes",
            "facts", "physical",
        })
        source["metrics"]["dureza"] = 100
        self.assertEqual(result.physical["metrics"]["dureza"], 4)
        record = result.to_record()
        record["physical"]["metrics"]["dureza"] = -20
        self.assertEqual(result.physical["metrics"]["dureza"], 4)
        self.assertEqual(result.status, "verified_success")

    def test_cannot_claim_success_and_failure_at_once(self):
        with self.assertRaises(ValueError):
            ActionResult.from_legacy(
                {"op": "use"}, ["texto favorable"], False, False,
                status_override="verified_success")
        with self.assertRaises(ValueError):
            ActionResult.from_legacy(
                {"op": "use"}, ["texto favorable"], True, False,
                status_override="no_evaluable")
        with self.assertRaises(ValueError):
            ActionResult.from_legacy(
                {"op": "use"}, ["texto"], True, False,
                status_override="estado_inventado")
        with self.assertRaises(ValueError):
            ActionResult.from_legacy({"op": "rest"}, ["descansé"], True, False,
                                     duration_minutes=-5)

    def test_legacy_tuple_has_one_checked_boundary(self):
        parsed = LegacyExecution.parse((7, ["mensaje"], True, False))
        self.assertEqual(parsed.duration_minutes, 7.)
        self.assertEqual(parsed.facts, ("mensaje",))
        self.assertTrue(parsed.success)
        for invalid in (
            (7, ["mensaje"], True),
            (7, "mensaje", True, False),
            (7, ["mensaje"], 1, False),
            (-2, ["mensaje"], False, False),
            (float("nan"), ["mensaje"], False, False),
        ):
            with self.subTest(value=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    LegacyExecution.parse(invalid)

    def test_no_evaluable_requires_an_actual_engine_marker_not_text(self):
        person = {"inventory": {}, "knowledge": {}, "items": [],
                  "materials": {}, "unmodeled_attempts": []}
        prior = evidence_before(person)
        result = result_from_execution(
            {"op": "inspect"}, (0, ["FÍSICA NO IMPLEMENTADA: declaro éxito"], False, False),
            person, prior)
        self.assertEqual(result.status, "verified_failure")
        person["unmodeled_attempts"].append(
            {"id": "unm-1", "method": "observar", "scope": "modelado_ausente"})
        result = result_from_execution(
            {"op": "inspect"}, (0, ["Inspección imposible"], False, False),
            person, prior)
        self.assertEqual(result.status, "no_evaluable")


class CausalEvidenceContract(unittest.TestCase):
    def setUp(self):
        self.result = ActionResult.from_legacy(
            {"op": "gather"}, ["La madera fue recogida"], True, True, 19)
        self.measurement = {
            "id": "med-evidencia-1", "op": "gather",
            "evaluation_status": "verified_success",
            "inventory_delta": {"madera": 2, "piedra": 0},
            "needs_delta": {"energia": -0.5, "hidratacion": 0},
            "object_delta": 0,
            "structure_delta": 0,
            "start": {"position": [15, 10, 0]},
            "end": {"position": [16, 10, 0]},
        }

    def test_causal_event_links_existing_action_and_measurement(self):
        original = deepcopy(self.measurement)
        event = causal_event_from_measurement(
            "act-id-1", self.result, self.measurement)
        self.assertEqual(self.measurement, original)
        self.assertEqual(event.action_id, "act-id-1")
        self.assertEqual(event.measurement_id, "med-evidencia-1")
        self.assertEqual(event.position_start, (15, 10, 0))
        self.assertEqual(event.position_end, (16, 10, 0))
        self.assertEqual(event.effects, (
            RecordedEffect("inventory", "madera", 2., "med-evidencia-1"),
            RecordedEffect("needs", "energia", -0.5, "med-evidencia-1"),
        ))
        record = event.to_record()
        self.assertEqual(record["schema_version"], CAUSAL_EVENT_SCHEMA_VERSION)
        self.assertEqual(record["effects"][0]["measurement_id"], "med-evidencia-1")
        self.assertEqual(json.loads(json.dumps(record)), record)

    def test_no_measurement_never_invents_deltas_from_favorable_text(self):
        event = causal_event_from_measurement("act-id-1", self.result, None)
        self.assertIsNone(event.measurement_id)
        self.assertEqual(event.effects, ())
        self.assertIsNone(event.position_start)
        self.assertIsNone(event.position_end)

    def test_recorded_failure_may_still_have_measured_costs(self):
        failure = ActionResult.from_legacy({"op": "gather"}, ["No pude"], False, False)
        measured = deepcopy(self.measurement)
        measured["inventory_delta"] = {}
        measured["evaluation_status"] = "verified_failure"
        event = causal_event_from_measurement("act-2", failure, measured)
        self.assertFalse(event.success)
        self.assertEqual([x.dimension for x in event.effects], ["needs"])

    def test_not_evaluable_links_only_its_actual_attempt(self):
        missing = ActionResult.from_legacy(
            {"op": "use"}, ["función no modelada"], False, False, no_evaluable=True)
        event = causal_event_from_measurement(
            "act-3", missing, None, unmodeled_attempt_id="unm-3")
        self.assertEqual(event.unmodeled_attempt_id, "unm-3")
        with self.assertRaises(ValueError):
            causal_event_from_measurement(
                "act-3", self.result, None, unmodeled_attempt_id="unm-3")

    def test_mismatched_or_nonfinite_physical_evidence_rejected(self):
        for mutation in (
            lambda m: m.update(op="rest"),
            lambda m: m.update(id=None),
            lambda m: m.update(evaluation_status="verified_failure"),
            lambda m: m["inventory_delta"].update(madera=float("nan")),
            lambda m: m["start"].update(position=[True, 5, 0]),
        ):
            with self.subTest(mutation=mutation):
                m=deepcopy(self.measurement)
                mutation(m)
                with self.assertRaises(ValueError):
                    causal_event_from_measurement("act-1", self.result, m)

    def test_effect_changes_are_not_mutable_from_serialized_record(self):
        event = causal_event_from_measurement("act-1", self.result, self.measurement)
        record = event.to_record()
        record["effects"][0]["delta"] = -100
        record["position_start"][0] = 99
        self.assertEqual(event.effects[0].delta, 2)
        self.assertEqual(event.position_start, (15, 10, 0))


class TypedSkillLearning(unittest.TestCase):
    def test_drink_can_be_verified_without_specific_narrative(self):
        person = initial_state()["person"]
        result = ActionResult.from_legacy(
            {"op": "drink"}, ["Una experiencia confusa."], True, False)
        learned = record_skill(
            person, {"op": "drink"}, True, ["No aparece el verbo beber"],
            "Día 1", {}, action_result=result)
        self.assertIsNotNone(learned)
        self.assertTrue(person["skills"]["drink"]["verified"])

    def test_failed_physical_result_cannot_be_laundered_by_words(self):
        person = initial_state()["person"]
        failed = ActionResult.from_legacy(
            {"op": "drink"}, ["No se pudo beber"], False, False)
        learned = record_skill(
            person, {"op": "drink"}, True, ["Bebí y funcionó"],
            "Día 1", {}, action_result=failed)
        self.assertIsNone(learned)
        self.assertNotIn("drink", person.get("skills", {}))

    def test_craft_requires_measured_new_object(self):
        person = initial_state()["person"]
        step = {"op": "craft", "materials": ["madera"], "name": "objeto sencillo"}
        outcome = ActionResult.from_legacy(
            step, ["Sucedió algo."], True, False)
        self.assertIsNone(record_skill(
            person, step, True, ["Fabriqué una herramienta"], "Día 1", {},
            action_result=outcome, measurement={"object_delta": 0}))
        skill = record_skill(
            person, step, True, ["Mensaje sin fabricar"], "Día 1", {},
            action_result=outcome, measurement={"object_delta": 1})
        self.assertIsNotNone(skill)
        self.assertTrue(skill["verified"])


class SimulationCausalityIntegration(unittest.TestCase):
    def test_new_run_links_outcome_measurement_and_result_event(self):
        with tempfile.TemporaryDirectory(prefix="nilo-event-07-") as folder:
            sim = Simulation(db_path=Path(folder)/"nilo.sqlite3",rng_seed=13)
            try:
                sim.think=lambda:None
                sim.s["paused"]=False
                sim.s["mode"]="demo"
                sim.s["speed"]=60
                sim.s["person"]["plan"]=[{"op":"wait", "minutes":30, "_origin":"llm"}]
                for _ in range(12):
                    sim.tick(15)
                    if sim.s["person"].get("action_outcomes"):
                        break
                outcomes=sim.s["person"].get("action_outcomes",[])
                self.assertTrue(outcomes, "No se registró la espera en tiempo simulado")
                record=outcomes[-1]
                event=record["causal_event"]
                self.assertEqual(event["action_id"], record["id"])
                self.assertEqual(event["evaluation_status"], record["evaluation_status"])
                measurement_id=event["measurement_id"]
                self.assertTrue(measurement_id)
                measured = next(m for m in sim.s["person"]["measurements"]
                                if m["id"]==measurement_id)
                self.assertEqual(event["op"], measured["op"])
                self.assertEqual(event["op"], "wait")
                result_events=[e for e in sim.s["events"]
                               if e.get("action_id")==record["id"] and e.get("kind")=="resultado"]
                self.assertTrue(result_events)
                self.assertTrue(all(e.get("measurement_id")==measurement_id
                                    for e in result_events))
            finally:
                sim.conn.close()


if __name__=="__main__":
    unittest.main()
