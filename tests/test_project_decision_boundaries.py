"""Contrato integral: el proyecto no controla acciones físicas ni su autoría.

La matriz prueba el flujo real Simulation.plan_ready + ClockUseCases.tick,
sin proveedores, sobre SQLite temporal y con historial/agenda observable.
"""
from __future__ import annotations
import unittest
from unittest.mock import patch

from agenda import set_agenda
from nilo_runtime.agent.responses import normalize_decision
from nilo_runtime.autonomy.decision_intents import active_project_for_action
from nilo_runtime.labs.ab_experiment import _drive_decision, _SilentTrace
from nilo_runtime.labs.sandbox import SimulationSandbox


class ProjectDecisionBoundaries(unittest.TestCase):
    def setUp(self):
        self.lab=SimulationSandbox(_SilentTrace)
        self.lab.reset("nuevo",7321,False)

    def tearDown(self):
        self.lab.close()

    @property
    def person(self):
        return self.lab.sim.s["person"]

    def decide(self, action, plan, **fields):
        payload={
            "cuaderno": f"Decido {action}.",
            "objetivo":fields.get("objetivo", "Estudiar el territorio"),
            "motivo":"Quiero elegir con libertad.",
            "accion_proyecto":action,
            "plan":plan,
            "revisar_en_minutos":180,
            **fields,
        }
        return _drive_decision(self.lab,normalize_decision(payload))

    def start_project(self):
        result=self.decide("nuevo",[{"op":"wait","minutes":2}])
        self.assertTrue(result["plan_accepted"])
        self.assertTrue(self.person.get("project"))
        return self.person["project"]["id"]

    def archived(self, project_id):
        return next((p for p in self.person.get("projects", [])
                     if p.get("id")==project_id),None)

    def test_pause_executes_rest_and_records_diary_under_archived_id(self):
        project_id=self.start_project()
        before=self.person["clock_minutes"]
        result=self.decide("pausar",[{"op":"rest","minutes":120}],
                           proyecto_id=project_id)
        self.assertEqual(result["admitted_operations"],1)
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertGreater(self.person["clock_minutes"]-before,110)
        self.assertIsNone(self.person["project"])
        self.assertEqual(self.archived(project_id)["status"],"pausado")
        self.assertEqual(result["project_transition"]["previous_status_after"],"pausado")
        self.assertEqual(self.lab.sim.s["journal"][-1]["project_id"],project_id)
        self.assertTrue(self.person.get("review_at_minutes")>=before)

    def test_abandon_keeps_unrelated_immediate_actions_without_reactivating(self):
        project_id=self.start_project()
        result=self.decide("abandonar",[{"op":"wait","minutes":15}],
                           proyecto_id=project_id)
        self.assertEqual(result["admitted_operations"],1)
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertIsNone(self.person["project"])
        self.assertEqual(self.archived(project_id)["status"],"abandonado")
        self.assertEqual(self.lab.sim.s["journal"][-1]["project_id"],project_id)

    def test_completar_without_proof_does_not_archive_and_can_rest(self):
        project_id=self.start_project()
        result=self.decide("completar",[{"op":"rest","minutes":20}],
                           proyecto_id=project_id,prueba_cierre="")
        self.assertEqual(result["admitted_operations"],1)
        self.assertEqual(self.person["project"]["id"],project_id)
        self.assertNotEqual(self.person["project"]["status"],"terminado")
        self.assertIn("last_closure_rejection",self.person)
        self.assertEqual(result["operation_results"][0]["state"],"completada")

    def test_completar_with_confirmed_proof_retires_then_executes(self):
        project_id=self.start_project()
        with patch("nilo_runtime.autonomy.project_decisions.completion_evidence",
                   return_value={"measurement_ids":["med-sintetica"]}):
            result=self.decide("completar",[{"op":"wait","minutes":8}],
                               proyecto_id=project_id,
                               prueba_cierre="Resultado físico verificado sintético")
        self.assertEqual(result["admitted_operations"],1)
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertEqual(result["project_transition"]["previous_status_after"],"terminado")
        self.assertEqual(self.archived(project_id)["status"],"terminado")
        self.assertIsNone(self.person["project"])

    def test_sin_proyecto_while_active_does_not_attribute_physical_progress(self):
        project_id=self.start_project()
        original=self.person["project"]
        steps=original.get("steps_done",0)
        result=self.decide("sin_proyecto",[{"op":"rest","minutes":20}])
        self.assertTrue(result["plan_accepted"])
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertEqual(self.person["project"]["id"],project_id)
        self.assertEqual(self.person["project"]["steps_done"],steps)
        latest=self.person["action_outcomes"][-1]
        self.assertIsNone(latest.get("project_id"))
        measurement=self.person["measurements"][-1]
        self.assertNotIn("project_id",measurement)
        self.assertNotIn("project_id",self.lab.sim.s["journal"][-1])

    def test_new_project_formally_pauses_old_and_its_deferred_tasks(self):
        project_id=self.start_project()
        set_agenda(self.person,[{
            "titulo":"Analizar una muestra pendiente",
            "motivo":"Prueba del propietario anterior",
            "cuando":{"tipo":"despues_de_minutos","minutos":150},
            "pasos":[{"op":"inspect","x":15,"y":10}],
        }],self.person["clock_minutes"],project_id)
        old_task=next(t for t in self.person["agenda"]
                      if t.get("proyecto_id")==project_id)
        self.assertEqual(old_task["estado"],"pendiente")
        result=self.decide("nuevo",[{"op":"wait","minutes":4}],
                           objetivo="Un nuevo interés sin relación")
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertNotEqual(self.person["project"]["id"],project_id)
        self.assertEqual(self.archived(project_id)["status"],"pausado")
        self.assertEqual(old_task["estado"],"pospuesta")
        self.assertEqual(old_task["ultimo_motivo"],"Proyecto pausado")

    def test_resume_past_project_preserves_identity_and_history(self):
        project_id=self.start_project()
        self.decide("pausar",[{"op":"wait","minutes":2}],
                    proyecto_id=project_id)
        self.assertIsNone(self.person["project"])
        result=self.decide("continuar",[{"op":"wait","minutes":3}],
                           proyecto_id=project_id)
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertEqual(self.person["project"]["id"],project_id)
        self.assertEqual(self.person["project"]["status"],"activo")
        self.assertIsNone(self.archived(project_id))

    def test_resume_other_project_formally_retires_current(self):
        # Reanudar B mientras A está activo no puede dejar A huérfano.
        id_a=self.start_project()
        self.decide("pausar",[{"op":"wait","minutes":2}],
                    proyecto_id=id_a)
        self.decide("nuevo",[{"op":"wait","minutes":2}],
                    objetivo="Investigación alternativa B")
        id_b=self.person["project"]["id"]
        self.assertNotEqual(id_a,id_b)
        result=self.decide("continuar",[{"op":"wait","minutes":3}],
                           proyecto_id=id_a,
                           objetivo="Estudiar el territorio")
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertEqual(self.person["project"]["id"],id_a)
        self.assertEqual(self.person["project"]["status"],"activo")
        self.assertEqual(self.archived(id_b)["status"],"pausado")
        self.assertIsNone(self.archived(id_a))

    def test_personal_experience_provenance_follows_the_action(self):
        from inventions import record_personal_experience
        project_id=self.start_project()
        stamp=self.lab.sim.stamp()
        record_personal_experience(
            self.person,{"op":"inspect","_decision_project_id":None},
            True,True,["Observé una roca."],stamp)
        self.assertNotIn("project_id",self.person["life_history"][-1])
        record_personal_experience(
            self.person,{"op":"inspect","_decision_project_id":project_id},
            True,True,["Observé otra roca."],stamp)
        self.assertEqual(self.person["life_history"][-1]["project_id"],project_id)

    def test_research_id_cannot_reopen_or_silently_create_project(self):
        # Reproduce el A/B real: tras abandonar, Gemini usa un ID de
        # investigaciones_activas como si fuera proyecto_id.
        research_id="f2418e2d"
        self.person.setdefault("research",[]).append({
            "id":research_id,"question":"¿Puedo recuperar energía?",
            "hypothesis":"Descansar ayuda","state":"abierta",
        })
        self.assertIsNone(self.person.get("project"))
        result=self.decide(
            "continuar",[{"op":"rest","minutes":60}],
            objetivo="Recuperar energía mediante descanso voluntario",
            proyecto_id=research_id)
        self.assertTrue(result["plan_accepted"])
        self.assertEqual(result["operation_results"][0]["op"],"rest")
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertIsNone(self.person.get("project"))
        self.assertIsNone(result["project_transition"]["current_project_id"])
        self.assertEqual(result["project_transition"]["effective_action"],
                         "referencia_invalida")
        self.assertEqual(self.person["last_project_reference_rejection"]
                         ["requested_id"],research_id)
        self.assertEqual(self.person["last_project_reference_rejection"]
                         ["reason_code"],"id_de_investigacion")
        self.assertNotIn("project_id",self.lab.sim.s["journal"][-1])
        self.assertIsNone(self.person["action_outcomes"][-1].get("project_id"))
        from laboratorio_contexto import contexto_de_deliberacion, solicitud_completa
        msg=solicitud_completa(contexto_de_deliberacion(self.lab.sim),
                               "gemini")["datos_recibidos_con_valores"]
        self.assertEqual(msg["ultima_referencia_de_proyecto_rechazada"]
                         ["reason_code"],"id_de_investigacion")

    def test_invalid_project_id_cannot_close_a_different_active_project(self):
        # El fallback de selección no puede archivar el proyecto equivocado.
        active_id=self.start_project()
        result=self.decide(
            "abandonar",[{"op":"wait","minutes":4}],
            proyecto_id="id-inexistente")
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertEqual(self.person["project"]["id"],active_id)
        self.assertEqual(self.person["project"]["status"],"activo")
        self.assertEqual(result["project_transition"]["effective_action"],
                         "referencia_invalida")
        self.assertIsNone(self.archived(active_id))

    def test_invalid_continue_does_not_reassign_to_current_project(self):
        active_id=self.start_project()
        steps=self.person["project"].get("steps_done",0)
        result=self.decide(
            "continuar",[{"op":"rest","minutes":20}],
            proyecto_id="id-de-investigacion",objetivo="Descansar")
        self.assertEqual(result["operation_results"][0]["state"],"completada")
        self.assertEqual(self.person["project"]["id"],active_id)
        self.assertEqual(self.person["project"]["steps_done"],steps)
        self.assertIsNone(self.person["action_outcomes"][-1].get("project_id"))

    def test_legacy_steps_without_ownership_marker_keep_old_projection(self):
        active={"id":"hist","status":"activo"}
        p={"project":active}
        self.assertIs(active_project_for_action(p,{"op":"rest"}),active)
        self.assertIsNone(active_project_for_action(
            p,{"op":"rest","_decision_project_id":None}))
        self.assertIs(active_project_for_action(
            p,{"op":"rest","_decision_project_id":"hist"}),active)
        self.assertIsNone(active_project_for_action(
            p,{"op":"rest","_decision_project_id":"retirado"}))


if __name__=="__main__":
    unittest.main()
