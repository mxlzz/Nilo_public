"""Etapa 06: fuente única LLM → planificador → reloj → dispatcher → laboratorio."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from action_contracts import (
    ACTION_GUIDE, COMMON_RULES, SUPPORTED_OPERATIONS, VERIFIABLE,
    instructions, spec_for,
)
from brain import normalize_decision
from capabilities import manifest, offered_methods
from nilo import ACTION_DURATIONS, Simulation
from nilo_runtime.core.operations import (
    get_spec, registered_operations, validate_operation, manual_lines,
    NAVIGATION_OPERATIONS, DOCUMENT_EXECUTORS,
)
from nilo_runtime.application.operation_dispatch import execute_document


def decision(*steps):
    return {
        "cuaderno":"Registro de observación",
        "accion_proyecto":"sin_proyecto",
        "plan": list(steps),
    }


class RegistryContract(unittest.TestCase):
    def test_one_operation_catalog_for_manual_durations_and_executor(self):
        registry=registered_operations()
        self.assertEqual(set(registry),set(ACTION_GUIDE))
        self.assertEqual(set(registry),set(ACTION_DURATIONS))
        self.assertEqual(set(registry),set(SUPPORTED_OPERATIONS))
        self.assertEqual(set(VERIFIABLE)-set(registry),set())
        self.assertEqual(set(NAVIGATION_OPERATIONS)-set(registry),set())
        for op,spec in registry.items():
            with self.subTest(op=op):
                self.assertEqual(spec.name,op)
                self.assertEqual(spec.description,ACTION_GUIDE[op])
                self.assertEqual(spec.planned_minutes,ACTION_DURATIONS[op])
                self.assertGreater(spec.planned_minutes,0)
                self.assertIn(spec.executor,("physical",*DOCUMENT_EXECUTORS.values()))
                self.assertEqual(spec.navigable,op in NAVIGATION_OPERATIONS)
                self.assertEqual(spec.verified_preconditions,
                                 VERIFIABLE.get(op,{}).get("pre"))
                self.assertEqual(spec.verified_postconditions,
                                 VERIFIABLE.get(op,{}).get("post"))
                record=spec.to_record()
                self.assertEqual(record["op"],op)
                self.assertEqual(record["planned_minutes"],spec.planned_minutes)
        with self.assertRaises(TypeError):
            registry["invented"] = registry["go"]

    def test_manual_is_generated_in_registry_order_and_legacy_text_preserved(self):
        lines=instructions().splitlines()
        self.assertEqual(lines[0],"Operaciones disponibles (usar SOLO estas):")
        self.assertEqual(lines[1:1+len(SUPPORTED_OPERATIONS)],manual_lines())
        self.assertTrue(instructions().endswith(COMMON_RULES))
        for op in SUPPORTED_OPERATIONS:
            with self.subTest(op=op):
                record=spec_for(op)
                spec=get_spec(op)
                self.assertEqual(record["descripcion"],spec.description)
                self.assertEqual(record["duracion_prevista_minutos"],spec.planned_minutes)
                self.assertEqual(record["ejecutor"],spec.executor)
                self.assertEqual(record["requisitos_de_forma"],list(spec.required_fields))
        self.assertIsNone(spec_for("invented")["descripcion"])

    def test_core_rejects_unknown_ops_and_wrong_shapes(self):
        for s in (
            None,
            [],
            {"op": "invented"},
            {"op": 55},
            {"op": "build","materials": "madera"},
            {"op": "craft","geometry": []},
            {"op": "explore","region": "al norte"},
            {"op": "interact","x": True},
            {"op": "gather","evidence_ids": {"med-1": True}},
        ):
            with self.subTest(step=s):
                self.assertFalse(validate_operation(s).valid)
        for s in (
            {"op":"GO","x":"15","y":10},
            {"op":"gather","target":"madera"},
            {"op":"use","item":"test"},
            {"op":"design","name":"herramienta","prediction":"parece útil",
             "components":[{"name":"pieza","material":"madera"}]},
            {"op":"experiment","prediction":{"hypothesis":"ensayo"}},
            {"op":"interact","method":"aún no instalado"},
        ):
            with self.subTest(step=s):
                self.assertTrue(validate_operation(s).valid)
        self.assertFalse(validate_operation({"op":"gather"},
                                            check_required=True).valid)
        self.assertFalse(validate_operation({"op":"interact"},
                                            check_required=True).valid)
        self.assertTrue(validate_operation({"op":"rest"},check_required=True).valid)
        with self.assertRaises(ValueError):
            get_spec("op_inexistente")

    def test_method_dispatch_extends_interact_not_llm_operation_catalog(self):
        self.assertEqual(get_spec("interact").executor,"physical")
        mods=manifest()
        self.assertTrue(mods)
        methods=offered_methods()
        self.assertIn("llenar",methods)
        self.assertIn("probar_carga",methods)
        self.assertTrue(all(m not in registered_operations() for m in methods))
        self.assertEqual(len(methods),sum(len(c["methods"]) for c in mods))


class DecisionAndDispatcherContract(unittest.TestCase):
    def test_design_text_prediction_survives_shape_validation_without_physical_predicate(self):
        step={"op":"design","name":"punta diseñada","purpose":"perforar roca",
              "principle":"dureza","requirements":"madera y mineral oscuro",
              "procedure":"unir punta y mango","prediction":"debería fracturar roca",
              "components":[{"name":"cabeza","material":"mineral oscuro",
                             "function":"perforar","connection":"fija"}]}
        result=normalize_decision(decision(step))
        self.assertEqual(result["plan"][0]["op"],"design")
        # Las predicciones textuales de design no son el esquema de un ensayo.
        self.assertNotIn("prediction",result["plan"][0])

    def test_llm_invalid_schema_filtered_without_executing_world(self):
        s=decision(
            {"op":"build","materials":"madera"},
            {"op":"go","x":16,"y":10},
        )
        result=normalize_decision(s)
        self.assertEqual([x["op"] for x in result["plan"]],["go"])
        self.assertEqual(result["plan"][0]["x"],16)

    def test_runtime_rejects_unknown_steps_in_planner_and_preserves_valid_ones(self):
        with tempfile.TemporaryDirectory(prefix="nilo-registry-plan-") as path:
            sim=Simulation(db_path=Path(path)/"test.sqlite3")
            try:
                valid=sim.validate_plan([
                    {"op":"invented"},
                    {"op":"build","materials":"madera"},
                    {"op":"rest","minutes":30},
                ])
                self.assertNotIn("invented",[a["op"] for a in valid])
                self.assertIn("rest",[a["op"] for a in valid])
            finally:
                sim.conn.close()

    def test_document_dispatch_never_fabricates_object(self):
        with tempfile.TemporaryDirectory(prefix="nilo-doc-07-") as path:
            sim=Simulation(db_path=Path(path)/"test.sqlite3")
            try:
                p=sim.s["person"]
                w=sim.s["world"]
                count=(len(w["structures"]),len(p["items"]))
                step={"op":"design","name":"arco documentado",
                      "purpose":"estudiar fuerza",
                      "principle":"elasticidad","procedure":"unir",
                      "requirements":"madera",
                      "components":[{"name":"vara","material":"madera",
                                     "function":"soporte","connection":"fija"}]}
                facts,success,notable=execute_document(sim,p,step)
                self.assertTrue(success,facts)
                self.assertEqual((len(w["structures"]),len(p["items"])),count)
                self.assertEqual(get_spec(step["op"]).executor,"design")
                with self.assertRaises(ValueError):
                    execute_document(sim,p,{"op":"gather","target":"madera"})
                # Se pueden leer documentos, pero no convertir la ficha en obra.
                self.assertTrue(any(isinstance(f,str) for f in facts))
            finally:
                sim.conn.close()

    def test_document_dispatch_rejects_unmeasured_compare_and_conclude(self):
        with tempfile.TemporaryDirectory(prefix="nilo-doc-results-") as path:
            sim=Simulation(db_path=Path(path)/"test.sqlite3")
            try:
                p=sim.s["person"]
                original=len(p["measurements"])
                for op,extra in (
                    ("compare",{"metric":"dureza","evidence_ids":[]}),
                    ("conclude",{"topic":"dureza","evidence_ids":[]}),
                ):
                    with self.subTest(op=op):
                        facts,success,notable=execute_document(
                            sim,p,{"op":op,**extra})
                        self.assertFalse(success,facts)
                self.assertEqual(len(p["measurements"]),original)
            finally:
                sim.conn.close()


if __name__=="__main__":
    unittest.main()
