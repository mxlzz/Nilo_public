"""Contrato inicial agente/escenario/entorno (Nilo 0.5.8).

El segundo mundo simulado completo NO está implementado en esta versión: se
comprueba la frontera de creación, persistencia y percepción del agente.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import environments
import scenarios
from agent import initial_agent
from brain import context_for
from environments import IslandEnvironment, get_environment
from nilo import Simulation, initial_state
from reproducir import run_replay


class ScenarioBoundary(unittest.TestCase):
    def test_legacy_default_remains_the_same(self):
        state=initial_state(7321)
        p=state["person"]
        self.assertEqual(state["scenario_id"],"territorio_desconocido")
        self.assertEqual(state["world"]["seed"],7321)
        self.assertEqual(p["pos"],[15,10,0])
        self.assertEqual(p["inventory"],{"madera":1,"piedra":1})
        self.assertEqual(p["knowledge_profile"],"contemporaneo")
        self.assertFalse(p["knowledge"])

    def test_alternative_starting_condition_same_physics(self):
        normal=initial_state(7321)
        unarmed=initial_state(7321,"territorio_sin_equipo")
        self.assertEqual(normal["world"],unarmed["world"])
        self.assertEqual(unarmed["person"]["inventory"],{})
        self.assertEqual(unarmed["person"]["name"],"Nilo")
        self.assertIsNot(normal["person"]["materials"],unarmed["person"]["materials"])
        unarmed["world"]["revealed"].clear()
        self.assertTrue(normal["world"]["revealed"])

    def test_scenario_persisted_without_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/"nilo.sqlite"
            sim=Simulation(db_path=file,scenario_id="territorio_sin_equipo")
            try:
                sim.s["person"]["knowledge"]["prueba"]="hallazgo documentado"
                sim.write()
            finally:sim.conn.close()
            resumed=Simulation(db_path=file)  # por defecto pide el original
            try:
                self.assertEqual(resumed.scenario.id,"territorio_sin_equipo")
                self.assertEqual(resumed.s["person"]["inventory"],{})
                self.assertEqual(resumed.s["person"]["knowledge"]["prueba"],"hallazgo documentado")
            finally:resumed.conn.close()

    def test_old_save_without_scenario_preserves_state(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/"old.sqlite"
            sim=Simulation(db_path=file)
            try:
                sim.s["world"]["seed"]=98223
                sim.s["person"]["inventory"]["piedra"]=9
                sim.s.pop("scenario_id")
                sim.write()
            finally:sim.conn.close()
            resumed=Simulation(db_path=file,scenario_id="territorio_sin_equipo")
            try:
                self.assertEqual(resumed.scenario.id,"territorio_desconocido")
                self.assertEqual(resumed.s["world"]["seed"],98223)
                self.assertEqual(resumed.s["person"]["inventory"]["piedra"],9)
            finally:resumed.conn.close()

    def test_invalid_scenario_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError,"Escenario desconocido"):
            initial_state(7321,"ciudad_inexistente")

    def test_environment_initialization_is_replaceable_without_agent_changes(self):
        class Probe(IslandEnvironment):
            environment_id="probe-test"

            def make_world(self,seed):
                return {"seed":seed,"abi":"minimal-v0"}

            def materials(self):
                return {"ensayo":{"dureza":3}}

        candidate=scenarios.Scenario("probe-start","probe-test","Nilo",(1,2,0),
                  (("ensayo",1),),"contemporaneo","curioso","Entorno sintético","Medir antes de creer.")
        with patch.dict(environments._ENVIRONMENTS,{"probe-test":Probe()}), patch.object(
                scenarios,"SCENARIOS",{"probe-start":candidate}):
            state=initial_state(81,"probe-start")
        self.assertEqual(state["world"],{"seed":81,"abi":"minimal-v0"})
        self.assertEqual(state["person"]["pos"],[1,2,0])
        self.assertEqual(state["person"]["inventory"],{"ensayo":1})
        # No se ejecuta Simulation sobre este mundo: motor, rutina y UI actuales
        # todavía conocen topología de isla_v1.

    def test_scenario_guides_context_but_not_world_truth(self):
        sim=Simulation(db_path=":memory:",scenario_id="territorio_sin_equipo")
        try:
            c=sim.environment.perceive(sim.s["world"],sim.s["person"],[],"Día 1",sim.scenario)
            self.assertEqual(c["escenario_id"],"territorio_sin_equipo")
            self.assertEqual(c["entorno_id"],"isla_v1")
            self.assertIn("sin materiales",c["situacion_inicial"])
            self.assertEqual(c["inventario_materiales"],{})
            # El contexto alternativo no cambia datos físicos no observados.
            self.assertEqual(sim.s["world"]["seed"],7321)
        finally:sim.conn.close()

    def test_replay_accepts_a_different_starting_condition(self):
        case=json.loads((Path(__file__).parent/"fixtures"/"replay_basico.json").read_text())
        case.pop("expected_fingerprint",None)
        reference=run_replay(case)
        case["scenario_id"]="territorio_sin_equipo"
        other=run_replay(case)
        self.assertEqual(other["scenario_id"],"territorio_sin_equipo")
        self.assertNotEqual(reference["fingerprint"],other["fingerprint"])

    def test_restart_does_not_recompute_writing_from_offline_wall_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Path(directory)/"write.sqlite"
            sim=Simulation(db_path=db)
            try:
                sim.s["planning"]=True
                sim.change_speed(speed=60)
                sim.journal("El progreso guardado no se pierde al reiniciar el programa.")
                sim.tick(2)
                remaining=sim.s["person"]["pending"]["remaining_real"]
                sim.write()
            finally:sim.conn.close()
            with patch("nilo.time.time",return_value=9999999999):
                sim2=Simulation(db_path=db)
            try:self.assertAlmostEqual(sim2.s["person"]["pending"]["remaining_real"],remaining)
            finally:sim2.conn.close()


if __name__=="__main__":
    unittest.main()
