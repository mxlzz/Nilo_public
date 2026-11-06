"""0.7.1: regresión de proyectos duplicados del run real (fixture sintético)."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from brain import normalize_decision
from nilo import Simulation
from nilo_runtime.autonomy.projects import completed_project_reference

GOAL="Localizar una orilla de agua transitable"
FACT="Fabriqué un recipiente mineral con piedra y mineral."

def make_decision(action,goal=GOAL,project_id="",proof="",plan=None):
    return normalize_decision({
        "cuaderno":"Estoy revisando lo aprendido.",
        "accion_proyecto":action,"objetivo":goal,"proyecto_id":project_id,
        "motivo":"Revisar evidencia.","prueba_cierre":proof,
        "plan":[] if plan is None else plan,"revisar_en_minutos":30})

class ReferenceTests(unittest.TestCase):
    def test_id_and_exact_title(self):
        p={"id":"p-agua","title":GOAL,"status":"terminado"}
        saved=[{"id":"p-pausa","title":GOAL,"status":"pausado"},p]
        self.assertIs(completed_project_reference(saved,title=GOAL),p)
        self.assertIs(completed_project_reference(saved,project_id="p-agua"),p)
        self.assertIsNone(completed_project_reference(saved,title="Explorar otros ríos"))
        self.assertIsNone(completed_project_reference(saved,project_id="p-pausa"))
        self.assertIsNone(completed_project_reference([],title=GOAL))

class RealRunRegression(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-regresion-071-")
        self.addCleanup(self.temp.cleanup)
        self.sim=Simulation(db_path=Path(self.temp.name)/"mundo.sqlite3",
                            world_seed=7321,rng_seed=9821)
        self.addCleanup(self.sim.conn.close)

    @property
    def p(self):return self.sim.s["person"]

    def send(self,action,goal=GOAL,project_id="",proof="",plan=None):
        self.sim.plan_ready(make_decision(action,goal,project_id,proof,plan),"demo")

    def test_success_then_repeated_completion_does_not_recreate(self):
        pr={"id":"p1","title":"Fabricar un recipiente mineral",
            "status":"activo","progress":75,
            "verified_results":[{"action":"craft","result":FACT,
                                 "measurement_id":"med-craft"}]}
        self.p["project"]=pr
        self.p["measurements"]=[{"id":"med-craft","op":"craft","success":True,
            "evaluation_status":"verified_success","verified_facts":[FACT]}]
        self.p["last_closure_rejection"]={"project_id":"p1","reason":"Faltó cita"}
        self.send("completar",goal=pr["title"],project_id="p1",
                  proof="Verificado mediante med-craft")
        self.assertIsNone(self.p["project"])
        self.assertEqual(pr["status"],"terminado")
        self.assertNotIn("last_closure_rejection",self.p)
        self.assertEqual(pr["closure_evidence"]["evidence_ids"],["med-craft"])
        self.send("completar",goal=pr["title"],project_id="p1",
                  proof="Verificado mediante med-craft")
        self.assertIsNone(self.p["project"])
        self.assertEqual(len(self.p["projects"]),1)
        self.assertTrue(self.p["last_closure_rejection"]["already_completed"])

    def test_same_title_without_id_remains_closed(self):
        self.p["projects"]=[{"id":"p-agua","title":GOAL,"status":"terminado",
                             "closure_evidence":{"evidence_ids":["med-agua"]}}]
        for _ in range(4):
            self.send("completar",proof="Hallé agua: med-agua")
        self.assertIsNone(self.p["project"])
        self.assertEqual(len(self.p["projects"]),1)
        self.assertTrue(self.p["last_closure_rejection"]["already_completed"])

    def test_no_project_does_not_become_a_new_project(self):
        self.send("completar",proof="Pude terminar.")
        self.assertIsNone(self.p["project"])
        self.assertEqual(self.p["projects"],[])
        self.assertFalse(self.p["last_closure_rejection"]["already_completed"])

    def test_old_id_cannot_complete_a_different_current_project(self):
        self.p["projects"]=[{"id":"p-agua","title":GOAL,"status":"terminado"}]
        active={"id":"p-otro","title":"Fabricar un recipiente mineral",
                "status":"activo","verified_results":[{"action":"craft",
                "result":FACT,"measurement_id":"med-craft"}]}
        self.p["project"]=active
        self.p["measurements"]=[{"id":"med-craft","op":"craft","success":True,
             "evaluation_status":"verified_success","verified_facts":[FACT]}]
        self.send("completar",goal=GOAL,project_id="p-agua",
                  proof="Verificado mediante med-craft")
        self.assertIs(self.p["project"],active)
        self.assertEqual(active["status"],"activo")
        self.assertEqual(len(self.p["projects"]),1)

    def test_explicit_new_is_allowed(self):
        self.p["projects"]=[{"id":"p-agua","title":GOAL,"status":"terminado"}]
        self.send("nuevo",plan=[{"op":"inspect","target":"suelo"}])
        self.assertEqual(self.p["project"]["title"],GOAL)
        self.assertNotEqual(self.p["project"]["id"],"p-agua")

if __name__=="__main__":unittest.main()
