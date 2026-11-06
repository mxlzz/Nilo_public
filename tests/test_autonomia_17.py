"""Nilo 0.7 etapa 17: proyectos, evidencia, agenda, hábitos y bucles."""
from __future__ import annotations

import copy
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nilo import Simulation, initial_state
from project_lifecycle import retire_project, project_needs_review, closure_diagnostic
from project_progress import advance_evidence
from goal_evidence import select_closure_evidence
from agenda import normalize_task, safe_step, choose_agenda_step, awaken_reminders
from habits import (choose_wait_action, set_wait_preferences,
                    _near_water, _forage_access, _reachable, record_wait_selection)
from strategy_review import repeated_strategies
from nilo_runtime.autonomy import projects, agenda as agenda_core, habits as habits_core
from nilo_runtime.autonomy import strategy, goal_evidence as goal_evidence_core


def person(project=None):
    return {"pos":[15,10,0],"clock_minutes":100,"project":project,
            "projects":[],"research":[],"agenda":[],"inventory":{"alimento":2},
            "needs":{"energia":75,"hidratacion":65,"nutricion":70},
            "waiting_preferences":[],"waiting_preference_usage":{},
            "skills":{}}


def task(pid=None, state="pendiente", op="rest"):
    return {"id":"tar-uno","titulo":"Actividad elegida","modo":"tarea",
            "proyecto_id":pid,"cuando":{"tipo":"ahora"},
            "pasos":[{"op":op,"minutes":30}],"indice":0,"estado":state,
            "motivo":"Quise hacerlo","intentos":0,"resultados":[]}


class Projects17(unittest.TestCase):
    def test_completion_without_evidence_is_atomic(self):
        p={"id":"p1","status":"activo","progress":44}
        owner=person(p)
        before=copy.deepcopy((p,owner))
        with self.assertRaises(ValueError):
            retire_project(owner,p,"terminado","Día 2",evidence=None)
        self.assertEqual((p,owner),before)

    def test_pause_does_not_claim_success_or_close_unrelated_research(self):
        project={"id":"p1","status":"activo","progress":50}
        other={"id":"r-otra","question":"¿Es dura la arcilla?","state":"abierta",
               "project_ids":["p2"]}
        related={"id":"r-misma","question":"¿Resiste la madera?","state":"abierta",
                 "project_ids":["p1"]}
        owner=person(project)
        owner["research"]=[other,related]
        owner["active_research"]=other["question"]
        owner["agenda"]=[task("p1"),task("p2")]
        retire_project(owner,project,"pausado","Día 2","Decidí detenerme.")
        self.assertIsNone(owner["project"])
        self.assertEqual(project["status"],"pausado")
        self.assertEqual(project["progress"],50)
        self.assertNotIn("closure_evidence",project)
        self.assertEqual(related["state"],"pausada")
        self.assertEqual(other["state"],"abierta")
        self.assertEqual(owner["active_research"],other["question"])
        self.assertEqual(owner["agenda"][0]["estado"],"pospuesta")
        self.assertEqual(owner["agenda"][1]["estado"],"pendiente")

    def test_closed_project_cannot_keep_active_task(self):
        project={"id":"p1","status":"activo"}
        owner=person(project)
        owner["agenda"]=[task("p1")]
        retire_project(owner,project,"abandonado","Día 2","Otro interés")
        self.assertEqual(owner["agenda"][0]["estado"],"cancelada")
        self.assertEqual(choose_agenda_step({},owner),None)

    def test_loop_review_is_informative_not_automatic_completion(self):
        p={"id":"p1","status":"activo","deliberations":19,
           "deliberations_since_progress":8,"progress":75}
        self.assertTrue(project_needs_review(p))
        self.assertEqual(p["status"],"activo")
        self.assertFalse(closure_diagnostic(p,person(p))["comprobado"])


class Proof17(unittest.TestCase):
    def case(self):
        fact="Fabriqué un recipiente mineral con piedra y mineral."
        project={"id":"p1","title":"Fabricar un recipiente mineral",
                 "verified_results":[{"action":"craft","result":fact,
                                      "measurement_id":"med-craft"}]}
        owner={"measurements":[{"id":"med-craft","op":"craft","success":True,
                                "evaluation_status":"verified_success",
                                "verified_facts":[fact]}]}
        return project,owner,fact

    def test_full_verbatim_result_can_cite_real_measurement(self):
        p,owner,fact=self.case()
        self.assertEqual(select_closure_evidence(p,owner,fact)["evidence_ids"],
                         ["med-craft"])

    def test_prose_fragment_does_not_count_as_complete_proof(self):
        p,owner,fact=self.case()
        self.assertIsNone(select_closure_evidence(
            p,owner,"recipiente mineral con piedra"))
        self.assertIsNone(select_closure_evidence(
            p,owner,"Fue comprobado con med-craft-extra"))
        self.assertEqual(p.get("status"),None)

    def test_exact_id_token_and_physical_goal_are_both_required(self):
        p,owner,_=self.case()
        self.assertIsNotNone(select_closure_evidence(
            p,owner,"La prueba física es med-craft."))
        p["title"]="Demostrar la potabilidad del agua"
        self.assertIsNone(select_closure_evidence(
            p,owner,"La prueba física es med-craft."))

    def test_retired_project_is_not_reopened_from_text(self):
        p={"id":"p1","status":"pausado"}
        self.assertIsNone(select_closure_evidence(p,{"measurements":[]},
                          "Creo que completé todo."))


class Agenda17(unittest.TestCase):
    def test_orphaned_task_is_cancelled_without_executing(self):
        owner=person()
        owner["agenda"]=[task("p-inexistente")]
        self.assertIsNone(choose_agenda_step({},owner))
        self.assertEqual(owner["agenda"][0]["estado"],"cancelada")
        self.assertEqual(owner["agenda"][0]["ultimo_motivo"],
                         "Proyecto no activo")

    def test_paused_project_cannot_reactivate_task_by_clock(self):
        owner=person()
        owner["projects"]=[{"id":"p1","status":"pausado"}]
        owner["agenda"]=[task("p1")]
        self.assertIsNone(choose_agenda_step({},owner))
        paused=owner["agenda"][0]
        self.assertEqual(paused["estado"],"pospuesta")
        self.assertGreater(paused["reanudar_minuto"],1e14)
        owner["clock_minutes"]=1e8
        self.assertIsNone(choose_agenda_step({},owner))
        owner["project"]={"id":"p1","status":"activo"}
        paused["reanudar_minuto"]=owner["clock_minutes"]
        operation,_=choose_agenda_step({},owner)
        self.assertEqual(operation["_agenda_id"],"tar-uno")

    def test_task_without_project_still_runs_if_delegated(self):
        owner=person()
        owner["agenda"]=[task(None)]
        step,selected=choose_agenda_step({},owner)
        self.assertEqual(step["op"],"rest")
        self.assertEqual(selected["estado"],"en_curso")
        self.assertEqual(step["_origin"],"agenda")

    def test_reminder_for_paused_project_only_notifies(self):
        owner=person()
        owner["projects"]=[{"id":"p1","status":"pausado"}]
        reminder={"id":"tar-recordar","modo":"recordatorio",
                  "titulo":"Reconsiderar estudio","estado":"pendiente",
                  "proyecto_id":"p1","cuando":{"tipo":"ahora"}}
        owner["agenda"]=[reminder]
        notifications=awaken_reminders(owner,"Día 3")
        self.assertEqual(len(notifications),1)
        self.assertEqual(reminder["estado"],"lista_para_revisar")
        self.assertIsNone(owner["project"])
        self.assertEqual(awaken_reminders(owner,"Día 3"),[])

    def test_non_finite_or_boolean_conditions_are_rejected(self):
        for c in ({"tipo":"despues_de_minutos","minutos":float("nan")},
                  {"tipo":"despues_de_minutos","minutos":float("inf")},
                  {"tipo":"despues_de_minutos","minutos":True},
                  {"tipo":"cuando_necesidad","necesidad":"energia",
                   "menor_que":float("nan")},
                  {"tipo":"cuando_haya_material","material":"madera",
                   "cantidad":True}):
            with self.subTest(condition=c):
                self.assertIsNone(normalize_task(
                    {"titulo":"Tarea delegada","pasos":[{"op":"rest"}],
                     "cuando":c},100))

    def test_derived_records_are_not_independent_evidence(self):
        owner=person()
        owner["measurements"]=[
            {"id":"med-uno","op":"experiment"},
            {"id":"med-dos","op":"compare"}]
        self.assertFalse(safe_step({},owner,
            {"op":"compare","evidence_ids":["med-uno","med-dos"]}))
        self.assertFalse(safe_step({},owner,
            {"op":"conclude","evidence_ids":["med-dos"]}))
        self.assertFalse(safe_step({},owner,
            {"op":"conclude","evidence_ids":["med-inventado"]}))
        self.assertTrue(safe_step({},owner,
            {"op":"conclude","evidence_ids":["med-uno"]}))


class Habits17(unittest.TestCase):
    def test_no_unassigned_care_when_llm_has_not_delegated(self):
        owner=person()
        owner["inventory"]["alimento"]=2
        self.assertIsNone(choose_wait_action({},owner))

    def test_hidden_water_never_triggers_current_automatic_drink(self):
        owner=person()
        with patch.object(habits_core,"valid",return_value=True), \
             patch.object(habits_core,"tile",return_value="~"):
            self.assertTrue(_near_water({"revealed":[]},owner))
            self.assertFalse(_near_water({"revealed":[]},owner,
                                         known_only=True))
            set_wait_preferences(owner,[{"op":"drink"}],"Día 1")
            self.assertIsNone(choose_wait_action({"revealed":[]},owner))

    def test_hidden_plant_does_not_trigger_current_forage(self):
        owner=person()
        owner["pos"]=[15,10,0]
        with patch.object(habits_core,"valid",return_value=True), \
             patch.object(habits_core,"tile",return_value="T"):
            self.assertTrue(_forage_access({"revealed":[]},owner,1))
            self.assertFalse(_forage_access({"revealed":[]},owner,1,
                                            known_only=True))

    def test_known_only_pathfinding_is_requested_once(self):
        owner=person()
        with patch.object(habits_core,"pathfind",
                          return_value=[(15,10),(16,10)]) as route:
            self.assertTrue(_reachable({},owner,(16,10),3,
                                       known_only=True))
        self.assertEqual(route.call_count,1)
        self.assertTrue(route.call_args.kwargs["known_only"])

    def test_failed_delegate_does_not_loop_without_new_decision(self):
        from habits import record_wait_result
        owner=person()
        owner["inventory"]["alimento"]=0
        owner["skills"]={"forage":{"verified":True}}
        set_wait_preferences(owner,[{"op":"forage","hasta":3}],"Día 1")
        for _ in range(3):
            record_wait_result(owner,{"op":"forage","_origin":"rutina"},
                               False,["No hubo material"],"Día 2")
        self.assertEqual(owner["waiting_failure_counts"]["forage:"],3)
        with patch.object(habits_core,"_forage_access",return_value=True):
            self.assertIsNone(choose_wait_action({},owner))
            set_wait_preferences(owner,[{"op":"forage","hasta":3}],"Día 3")
            self.assertIsNotNone(choose_wait_action({},owner))

    def test_legacy_wait_results_do_not_gain_modern_failure_state(self):
        from habits import record_wait_result
        owner=person()
        record_wait_result(owner,{"op":"forage","_origin":"rutina"},
                           False,["Falló"],"Día 2",legacy=True)
        self.assertNotIn("waiting_failure_counts",owner)

    def test_non_finite_wait_preferences_do_not_crash(self):
        from habits import _safe_preference
        for field in ("hasta","radio","veces"):
            with self.subTest(field=field):
                self.assertIsNotNone(_safe_preference(
                    {"op":"rest","minutes":30,field:float("inf")}))

    def test_invalid_coordinates_do_not_crash_agenda(self):
        for x,y in ((float("inf"),10),(True,2),(2,False)):
            with self.subTest(x=x,y=y):
                self.assertIsNone(normalize_task({
                    "titulo":"Moverse","pasos":[{"op":"go","x":x,"y":y}]},0))

    def test_finite_delegated_rest_does_not_repeat_forever(self):
        owner=person()
        set_wait_preferences(owner,[{"op":"rest","minutes":45,
                                     "veces":1}],"Día 1")
        chosen=choose_wait_action({},owner)
        self.assertEqual(chosen[0],{"op":"rest","minutes":45})
        record_wait_selection(owner,chosen[0])
        self.assertIsNone(choose_wait_action({},owner))


class Strategy17(unittest.TestCase):
    def test_repeat_requires_same_method_target_and_item(self):
        rows=[
            {"project_id":"p1","progress":False,"op":"use",
             "method":"golpear","item":"martillo","target":"roca"},
            {"project_id":"p1","progress":False,"op":"use",
             "method":"golpear","item":"martillo","target":"madera"},
            {"project_id":"p1","progress":False,"op":"use",
             "method":"golpear","item":"martillo","target":"roca"},
            {"project_id":"p1","progress":False,"op":"use",
             "method":"golpear","item":"martillo","target":"roca"}]
        repeated=repeated_strategies(rows,"p1")
        self.assertEqual(len(repeated),1)
        self.assertEqual(repeated[0]["objetivo"],"roca")
        self.assertEqual(repeated[0]["intentos_sin_avance"],3)

    def test_no_signature_only_operation_or_different_project(self):
        attempts=[{"project_id":"p1","progress":False,"op":"explore"}
                  for _ in range(4)]
        self.assertEqual(repeated_strategies(attempts,"p1"),[])
        self.assertEqual(repeated_strategies([
            {"project_id":"p2","progress":False,"op":"use",
             "target":"roca","method":"excavar"} for _ in range(5)
        ],"p1"),[])

    def test_project_progress_no_automatic_objective_claim(self):
        outcome=advance_evidence(new_tiles=1)
        self.assertTrue(outcome["progress"])
        self.assertNotIn("objective_completed",outcome)
        self.assertNotIn("closure_evidence",outcome)

    def test_auto_tool_followup_is_legacy_only(self):
        from nilo_runtime.application.clockwork import ClockUseCases
        source=inspect.getsource(ClockUseCases._tick_slice)
        self.assertIn("self.followup_without_llm()",source)
        self.assertIn("getattr(self,'historical_replay',False)",source)
        self.assertIn("getattr(self,'legacy_replay_rules',False)",source)


class Facades17(unittest.TestCase):
    def test_compatibility_names_reference_unique_owners(self):
        import project_lifecycle, strategy_review, goal_evidence
        import project_progress, agenda, habits
        from nilo_runtime.autonomy import progress
        self.assertIs(project_lifecycle.retire_project,projects.retire_project)
        self.assertIs(strategy_review.repeated_strategies,strategy.repeated_strategies)
        self.assertIs(goal_evidence.select_closure_evidence,
                      goal_evidence_core.select_closure_evidence)
        self.assertIs(project_progress.advance_evidence,progress.advance_evidence)
        self.assertIs(agenda.choose_agenda_step,agenda_core.choose_agenda_step)
        self.assertIs(habits.choose_wait_action,habits_core.choose_wait_action)


if __name__=="__main__":
    unittest.main()
