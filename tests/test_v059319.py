"""0.5.9.3.19 — cerrar objetivos de reconocimiento con evidencias de mundo.

Regresión derivada de los patrones registrados en un run, sin incorporar
la base SQLite privada en el repositorio.
"""
import unittest
import tempfile
from pathlib import Path
from goal_evidence import check_goal,select_closure_evidence
from brain import normalize_decision
from nilo import Simulation


class TerrainAndWaterGoal(unittest.TestCase):
    def setUp(self):
        self.project={"id":"p-1","title":"Reconocimiento del terreno y hallazgo de agua.",
                      "verified_results":[]}
        self.person={"measurements":[]}

    def sample(self,id,op,facts,*,target="",success=True):
        m={"id":id,"op":op,"target":target,"verified_facts":facts,
           "success":success,"evaluation_status":"verified_success" if success else "verified_failure"}
        self.person["measurements"].append(m)
        self.project["verified_results"].append({"measurement_id":id,"action":op,
                                               "result":facts[0] if facts else ""})
        return m

    def test_can_close_with_recorded_exploration_and_water(self):
        self.sample("med-mapa","explore",[
            "Recorrí 3 tramos del nivel 0, hasta [30, 8].",
            "Observé por primera vez: agua (32,6), arboleda (32,9)."])
        self.sample("med-agua","inspect",[
            "Examiné agua en [28, 0] (distancia 1)."],target="agua")
        proof="Identifiqué fuentes de agua tras exploraciones registradas: med-mapa."
        self.assertTrue(check_goal(self.project,self.person)[0])
        result=select_closure_evidence(self.project,self.person,proof)
        self.assertIsNotNone(result)
        self.assertIn("med-mapa",result["evidence_ids"])
        self.assertEqual(self.project.get("status"),None) # el validador no cambia el proyecto

    def test_cited_recent_observation_is_prioritized(self):
        self.sample("med-old","explore",["Observé por primera vez: roca (4,4)."])
        self.sample("med-water-old","go",["Avancé hasta la orilla; el agua queda junto a (28,0)."])
        self.sample("med-cited","explore",["Recorrí tres tramos.", "Observé por primera vez: agua (33,6)."])
        proof="Nueva exploración de agua verificada en med-cited."
        result=select_closure_evidence(self.project,self.person,proof)
        self.assertIsNotNone(result)
        self.assertIn("med-cited",result["evidence_ids"])

    def test_terrain_only_does_not_verify_water(self):
        self.sample("med-mapa","explore",["Observé por primera vez: roca (6,8)."])
        self.assertFalse(check_goal(self.project,self.person)[0])

    def test_missing_terrain_exploration_does_not_verify_survey(self):
        self.sample("med-agua","inspect",["Examiné agua en [28,0] (distancia 1)."],target="agua")
        ok,_,why=check_goal(self.project,self.person)
        self.assertFalse(ok)
        self.assertIn("exploración",why)

    def test_conclusion_and_project_name_are_not_evidence(self):
        self.sample("med-col","conclude",[
            "Registré una conclusión sobre agua y recursos abundantes."])
        self.assertFalse(check_goal(self.project,self.person)[0])

    def test_citing_an_unrelated_measurement_never_closes(self):
        self.sample("med-map","explore",["Observé por primera vez: agua (10,10)."])
        self.sample("med-other","rest",["Me detuve a descansar."])
        self.assertIsNone(select_closure_evidence(
            self.project,self.person,"Mi descanso medido en med-other confirma el cierre."))

    def test_unrelated_discovery_still_not_valid(self):
        self.project["title"]="Explorar para hallar ruinas antiguas"
        self.sample("med-map","explore",["Observé por primera vez: agua (10,10)."])
        self.assertFalse(check_goal(self.project,self.person)[0])

    def test_water_goal_is_not_claim_of_potability(self):
        self.project["title"]="Encontrar agua potable"
        self.sample("med-map","explore",["Observé por primera vez: agua (10,10)."])
        self.assertFalse(check_goal(self.project,self.person)[0])


class IntegrationClosure(unittest.TestCase):
    def test_agent_can_close_real_survey_goal_without_new_actions(self):
        with tempfile.TemporaryDirectory() as folder:
            sim=Simulation(db_path=Path(folder)/"test.sqlite3")
            try:
                person=sim.s["person"]
                project={"id":"survey-1","title":"Reconocimiento del terreno y hallazgo de agua.",
                         "status":"activo","progress":95,"verified_results":[
                             {"action":"explore","measurement_id":"med-explore","result":"Observé por primera vez: agua (33,6)."}],
                         "no_progress_steps":0,"deliberations":11,"deliberations_since_progress":9}
                person["project"]=project
                person["measurements"]=[{"id":"med-explore","op":"explore","target":"","success":True,
                        "evaluation_status":"verified_success",
                        "verified_facts":["Recorrí 3 tramos.","Observé por primera vez: agua (33,6)."]}]
                decision=normalize_decision({
                    "cuaderno":"Reconocí el terreno y hallé agua en el sector observado.",
                    "objetivo":"Continuar con otra investigación","motivo":"Tengo pruebas de reconocimiento.",
                    "accion_proyecto":"completar","proyecto_id":"survey-1",
                    "prueba_cierre":"Hallazgo de agua y terreno observado: med-explore.",
                    "plan":[]})
                sim.plan_ready(decision,"llm")
                self.assertIsNone(person["project"])
                self.assertEqual(project["status"],"terminado")
                self.assertEqual(project["progress"],100)
                self.assertEqual(project["closure_evidence"]["evidence_ids"],["med-explore"])
            finally:
                sim.conn.close()

    def test_rejected_proof_explains_which_measurement_is_pertinent(self):
        with tempfile.TemporaryDirectory() as folder:
            sim=Simulation(db_path=Path(folder)/"test.sqlite3")
            try:
                p=sim.s["person"]
                project={"id":"survey-1","title":"Reconocimiento del terreno y hallazgo de agua.",
                         "status":"activo","progress":95,"verified_results":[
                            {"action":"explore","measurement_id":"med-explore","result":"Observé agua y terreno."}],
                         "deliberations":1,"deliberations_since_progress":1}
                p["project"]=project
                p["measurements"]=[{"id":"med-explore","op":"explore","success":True,
                    "evaluation_status":"verified_success",
                    "verified_facts":["Observé por primera vez: agua (33,6)."]}]
                decision=normalize_decision({
                    "cuaderno":"Quiero cerrar, aunque falta referenciar el ensayo.",
                    "objetivo":"Cerrar reconocimiento","motivo":"Ya observé agua.",
                    "accion_proyecto":"completar","proyecto_id":"survey-1",
                    "prueba_cierre":"Se confirmó por hechos generales del diario.","plan":[]})
                sim.plan_ready(decision,"llm")
                self.assertIs(p["project"],project)
                self.assertTrue(any("med-explore" in e.get("text","")
                                    for e in sim.s["events"]))
            finally:
                sim.conn.close()


if __name__=="__main__":unittest.main()
