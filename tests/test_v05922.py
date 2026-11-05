"""0.5.9.2.2 — regresión del run real: piedra y afloramiento mal atribuido."""
import random
import tempfile
import unittest
from pathlib import Path

from brain import context_for, gather_outcome_discrepancies
from nilo import Simulation, initial_state
from world import (execute_action, gather_material, prepare_navigation,
                   new_world, tile, tile_key, nearest_known, set_tile)


class TargetAndSource(unittest.TestCase):
    def setUp(self):
        state=initial_state(7321)
        self.p=state["person"]
        self.w=state["world"]
        self.rng=random.Random(123)

    def test_aliases_are_explicit_not_substrings(self):
        self.assertEqual(gather_material("piedra"),"piedra")
        self.assertEqual(gather_material("roca"),"piedra")
        self.assertEqual(gather_material("afloramiento mineral"),"mineral oscuro")
        self.assertEqual(gather_material("MINERAL OSCURO"),"mineral oscuro")
        self.assertIsNone(gather_material("materiales"))
        self.assertIsNone(gather_material("afloramiento"))
        self.assertIsNone(gather_material("madera petrificada"))

    def test_real_seed_mineral_deposit_not_tree(self):
        # El run proporcionado agotó la arboleda 7,14, no el afloramiento 7,15.
        self.p["pos"]=[7,15,0]
        self.assertEqual(tile(self.w,7,15,0),"o")
        self.assertEqual(tile(self.w,7,14,0),"T")
        self.w["revealed"]=[tile_key(7,15,0),tile_key(7,14,0)]
        original_wood=self.p["inventory"].get("madera",0)
        mineral_before=self.w["deposits"][tile_key(7,15,0)]
        tree_before=self.w["deposits"][tile_key(7,14,0)]
        duration,facts,ok,_=execute_action(self.w,self.p,
                       {"op":"gather","target":"afloramiento mineral"},self.rng)
        self.assertTrue(ok)
        self.assertGreater(duration,0)
        self.assertEqual(self.p["inventory"]["mineral oscuro"],2)
        self.assertEqual(self.p["inventory"]["madera"],original_wood)
        self.assertEqual(self.w["deposits"][tile_key(7,15,0)],mineral_before-2)
        self.assertEqual(self.w["deposits"][tile_key(7,14,0)],tree_before)
        self.assertIn("afloramiento mineral",facts[0])

    def test_known_stone_is_harvested_at_adjacent_rock(self):
        self.p["pos"]=[5,18,0]
        self.w["revealed"]=[tile_key(5,18,0),tile_key(5,17,0)]
        self.assertEqual(tile(self.w,5,17,0),"^")
        amount=self.w["deposits"][tile_key(5,17,0)]
        self.assertGreaterEqual(amount,2)
        _,facts,ok,_=execute_action(self.w,self.p,
                      {"op":"gather","target":"piedra"},self.rng)
        self.assertTrue(ok)
        self.assertEqual(self.p["inventory"]["piedra"],3)
        self.assertEqual(self.w["deposits"][tile_key(5,17,0)],amount-2)
        self.assertTrue(any("piedra" in f and "roca" in f for f in facts))

    def test_inspect_piedra_recognizes_roca_without_harvesting(self):
        self.p["pos"]=[5,18,0]
        self.w["revealed"]=[tile_key(5,18,0),tile_key(5,17,0)]
        prior=self.p["inventory"]["piedra"]
        _,facts,success,_=execute_action(
            self.w,self.p,{"op":"inspect","target":"piedra"},self.rng)
        self.assertTrue(success,facts)
        self.assertIn("Examiné roca",facts[0])
        self.assertEqual(self.p["inventory"]["piedra"],prior)

    def test_unknown_target_fails_without_nearest_unrelated_resource(self):
        self.p["pos"]=[7,15,0]
        before=dict(self.p["inventory"])
        deposits=dict(self.w["deposits"])
        self.assertIsNone(prepare_navigation(self.w,self.p,
                         {"op":"gather","target":"materiales"},self.rng))
        _,facts,success,_=execute_action(self.w,self.p,
                         {"op":"gather","target":"materiales"},self.rng)
        self.assertFalse(success)
        self.assertIn("No reconozco",facts[0])
        self.assertEqual(before,self.p["inventory"])
        self.assertEqual(deposits,self.w["deposits"])


class RealNavigationAndLegacy(unittest.TestCase):
    def test_gather_approach_then_harvest_is_one_verified_action(self):
        with tempfile.TemporaryDirectory() as temp:
            sim=Simulation(db_path=Path(temp)/"run.sqlite3")
            try:
                w,p=sim.s["world"],sim.s["person"]
                p["pos"]=[7,18,0]
                w["revealed"]=[tile_key(x,y,0) for x,y in
                               [(7,18),(6,18),(5,18),(5,17)]]
                self.assertEqual(tile(w,6,18,0) in ".T,s=rho",True)
                p["inventory"]["piedra"]=0
                sim.s["planning"]=True
                p["plan"]=[{"op":"gather","target":"piedra"}]
                sim.s["speed"]=60
                # Primer tick programa ruta; siguientes realizan pasos y extracción.
                for _ in range(5):sim.tick(8)
                matches=[a for a in p.get("action_outcomes",[])
                         if a.get("op")=="gather"]
                self.assertEqual(len(matches),1,matches)
                outcome=matches[0]
                self.assertTrue(outcome["success"],outcome)
                self.assertEqual(outcome["physical_result"]["inventory_delta"]["piedra"],2)
                self.assertEqual(p["inventory"]["piedra"],2)
                self.assertTrue(any("Recogí 2 unidades de piedra" in f
                                    for f in outcome["facts"]))
            finally:
                sim.conn.close()

    def test_partial_navigation_is_not_counted_as_stone_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            sim=Simulation(db_path=Path(temp)/"partial.sqlite3")
            try:
                w,p=sim.s["world"],sim.s["person"]
                p["pos"]=[10,10,0]
                p["inventory"]["piedra"]=0
                # Fuente lejana, transitable hasta una roca que no admite caminar sobre ella.
                for x in range(10,31):set_tile(w,x,10,0,"." if x<30 else "^")
                w["revealed"]=[tile_key(x,10,0) for x in range(10,31)]
                w["deposits"][tile_key(30,10,0)]=2
                sim.s["planning"]=True
                p["plan"]=[{"op":"gather","target":"piedra"}]
                sim.s["speed"]=60
                for _ in range(5):sim.tick(15)
                outcomes=[r for r in p.get("action_outcomes",[]) if r["op"]=="gather"]
                self.assertEqual(len(outcomes),1,outcomes)
                result=outcomes[0]
                self.assertFalse(result["success"])
                self.assertEqual(result["evaluation_status"],"verified_failure")
                self.assertEqual(result["physical_result"]["inventory_delta"],{})
                self.assertEqual(p["inventory"]["piedra"],0)
                self.assertTrue(any("No completé la extracción" in v for v in result["facts"]))
                self.assertEqual(p["pos"],[20,10,0])
            finally:
                sim.conn.close()

    def test_historical_misleading_outcomes_become_visible_diagnostics(self):
        state=initial_state()
        p=state["person"]
        p["action_outcomes"]=[
            {"id":"act-3d6d35c608a0","op":"gather","target":"piedra",
             "success":True,"physical_result":{"inventory_delta":{}}},
            {"id":"act-a3f6398ecf9c","op":"gather",
             "target":"afloramiento mineral","success":True,
             "physical_result":{"inventory_delta":{"madera":2}}},
        ]
        diagnostic=gather_outcome_discrepancies(p)
        self.assertEqual(len(diagnostic),2)
        self.assertEqual(diagnostic[0]["material_obtenido"],{})
        self.assertEqual(diagnostic[1]["material_previsto"],"mineral oscuro")
        self.assertEqual(diagnostic[1]["material_obtenido"],{"madera":2})
        ctx=context_for(state["world"],p,[],"Día 3")
        self.assertEqual(ctx["inconsistencias_recoleccion_previas"],diagnostic)
        self.assertFalse(p.get("proposals"))
        self.assertEqual(len(p["action_outcomes"]),2)  # sin reescribir históricos

    def test_correct_recollection_does_not_create_diagnostic(self):
        p=initial_state()["person"]
        p["action_outcomes"]=[{"id":"x","op":"gather","target":"piedra",
            "success":True,"physical_result":{"inventory_delta":{"piedra":2}}}]
        self.assertEqual(gather_outcome_discrepancies(p),[])


if __name__=="__main__":
    unittest.main()
