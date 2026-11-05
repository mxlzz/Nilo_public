"""Regresiones para salidas subterráneas y límites físicos explícitos."""
import copy
import json
import os
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path

import nilo
from world import (new_world, tile, tile_key, pathfind, known_exit_route, prepare_navigation,
                   advance_navigation, navigation_result, execute_action, cave_exit, set_tile)
from brain import context_for, compact_context
from habits import choose_wait_action
from inventions import submit_proposal

RUN=Path(os.environ['NILO_TEST_SAVE']) if os.environ.get('NILO_TEST_SAVE') else None

class ExitTests(unittest.TestCase):
    def setUp(self):
        self.s=nilo.initial_state();self.w=self.s['world'];self.p=self.s['person']
        self.p['pos']=[23,7,-1]
        from world import reveal
        reveal(self.w,23,7,-1,3)
    def test_new_world_has_visible_exit_and_passable(self):
        self.assertEqual(tile(self.w,23,7,-1),'e')
        self.assertIn('e',self.w.get('levels',{}).get('-1')[7])
        self.assertEqual(known_exit_route(self.w,self.p),[])
    def test_exit_navigates_revealed_route_without_shortcuts(self):
        self.p['pos']=[21,7,-1]
        for x in [21,22,23]:
            set_tile(self.w,x,7,-1,'e' if x==23 else ':')
            if tile_key(x,7,-1) not in self.w['revealed']:
                self.w['revealed'].append(tile_key(x,7,-1))
        self.assertEqual(known_exit_route(self.w,self.p),[(22,7),(23,7)])
        nav=prepare_navigation(self.w,self.p,{'op':'ascend'},random.Random(1))
        self.assertEqual(nav['kind'],'ascend')
        advance_navigation(self.w,self.p,nav,2)
        self.assertEqual(self.p['pos'],[23,7,-1])
        facts,success,_=navigation_result(nav,self.p)
        self.assertTrue(success)
        self.assertIn('salida',facts[0])
        _,results,ok,_=execute_action(self.w,self.p,{'op':'ascend'},random.Random(1))
        self.assertTrue(ok)
        self.assertEqual(self.p['pos'],[23,7,0])
    def test_exit_known_path_not_through_unseen_tiles(self):
        self.p['pos']=[21,7,-1]
        self.w['revealed']=[tile_key(x,7,-1) for x in (21,23)]
        for x in range(21,24):set_tile(self.w,x,7,-1,'e' if x==23 else ':')
        self.assertIsNone(known_exit_route(self.w,self.p))
        self.assertIsNone(prepare_navigation(self.w,self.p,{'op':'ascend'},random.Random(0)))
    def test_critical_thirst_selects_exit(self):
        self.p['needs']={'hidratacion':25,'nutricion':60,'energia':50,'abrigo':80,'seguridad':80}
        self.p['pos']=[22,7,-1]
        self.w['revealed'].extend([tile_key(x,7,-1) for x in (22,23)])
        self.assertEqual(choose_wait_action(self.w,self.p,legacy_wait_policy=True)[0]['op'],'ascend')
        self.assertEqual(context_for(self.w,self.p,[],"Día 1")['salida_conocida']['accion'],'ascend')
    def test_plan_can_include_ascent_then_water_search(self):
        self.p['pos']=[22,7,-1]
        self.w['revealed'].extend([tile_key(x,7,-1) for x in (22,23)])
        # Validation defers water position to post-ascent and preserves both actions.
        with tempfile.TemporaryDirectory() as t:
            db=nilo.DB
            try:
                nilo.DB=Path(t)/'world.sqlite3';sim=nilo.Simulation()
                sim.s['world']=self.w;sim.s['person']=self.p
                plan=sim.validate_plan([{'op':'ascend'}, {'op':'go','target':'agua'}])
                self.assertEqual([a['op'] for a in plan],['ascend','go'])
                sim.conn.close()
            finally:nilo.DB=db
    def test_actual_run_can_return_without_modifying_source(self):
        if not RUN or not RUN.exists():self.skipTest('Definir NILO_TEST_SAVE para probar una partida propia')
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'run.sqlite3'
            with sqlite3.connect(str(RUN)) as src,sqlite3.connect(str(target)) as dst:src.backup(dst)
            db=nilo.DB
            try:
                nilo.DB=target
                sim=nilo.Simulation()
                sim.think=lambda:None
                self.assertEqual(tile(sim.s['world'],23,7,-1),'e')
                sim.s['person']['pending']=None
                sim.s['person']['plan']=[{'op':'ascend'}]
                sim.s['speed']=60
                sim.tick(1)
                self.assertIsNotNone(sim.s['person']['pending'])
                sim.tick(20)
                self.assertEqual(sim.s['person']['pos'][2],0)
                sim.conn.close()
            finally:nilo.DB=db

class UnmodeledTests(unittest.TestCase):
    def setUp(self):
        self.s=nilo.initial_state();self.p=self.s['person'];self.w=self.s['world']
        self.p['items']=[{'id':'obj-1','name':'cuenco de piedra','form':'recipiente',
                          'materials':['piedra'],'durability':100}]
    def test_condensation_does_not_generate_water(self):
        original=copy.deepcopy(self.p.get('inventory'))
        _,facts,success,_=execute_action(self.w,self.p,{'op':'use','item':'obj-1','method':'condensar'},random.Random(2))
        self.assertFalse(success)
        self.assertEqual(self.p['inventory'],original)
        self.assertTrue(facts[0].startswith('FÍSICA NO IMPLEMENTADA:'))
        self.assertEqual(self.p['unmodeled_attempts'][0]['result'],'no_evaluable')
    def test_unmodeled_experiment_not_assumed_failure(self):
        # El método sin modelo se registra cuando la muestra existe realmente.
        _,facts,success,_=execute_action(self.w,self.p,{'op':'experiment','target':'madera','method':'condensar'},random.Random(0))
        self.assertFalse(success)
        self.assertIn('No observé un fracaso físico',facts[0])
        self.assertEqual(len(self.p['unmodeled_attempts']),1)

    def test_missing_sample_is_not_a_missing_physics_diagnosis(self):
        _,facts,success,_=execute_action(self.w,self.p,{'op':'experiment','target':'material inexistente','method':'condensar'},random.Random(0))
        self.assertFalse(success)
        self.assertIn('muestra',facts[0])
        self.assertFalse(self.p.get('unmodeled_attempts'))
    def test_proposal_links_genuine_evidence(self):
        execute_action(self.w,self.p,{'op':'use','item':'obj-1','method':'condensar'},random.Random(1))
        evidence=self.p['unmodeled_attempts'][0]
        ok,_=submit_proposal(self.p,{'phenomenon':'Evaporación y condensación de agua',
                    'missing_capability':'No se modela temperatura ni humedad',
                    'rationale':'Busco capturar agua de aire húmedo',
                    'experiment':'Comparar condensado recogido en dos temperaturas',
                    'evidence_ids':['inventado',evidence['id']]},'Día 1',[])
        self.assertTrue(ok)
        self.assertEqual(self.p['proposals'][0]['evidence_ids'],[evidence['id']])
        self.assertFalse(self.p['proposals'][0]['engine_ready'])
    def test_known_material_test_still_returns_result(self):
        _,facts,ok,_=execute_action(self.w,self.p,{'op':'experiment','target':'madera','method':'golpear'},random.Random(1))
        self.assertTrue(ok)
        self.assertIn('dureza',facts[0])

if __name__=='__main__':unittest.main()
