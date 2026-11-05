"""0.5.6.3: continuidad real, seguridad de agenda y espera sin cuota."""
import copy
import os
import random
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import nilo
from agenda import (ensure_agenda, set_agenda, choose_agenda_step, record_agenda_result,
                    normalize_task, safe_step)
from brain import normalize_decision, context_for
from world import tile_key, set_tile, W, H, execute_action

class AgendaTests(unittest.TestCase):
    def setUp(self):
        self.s=nilo.initial_state();self.p=self.s['person'];self.w=self.s['world']
        from survival import ensure_needs
        ensure_needs(self.p)
        ensure_agenda(self.p)
    def new_task(self, pasos, cuando=None):
        return {'titulo':'Prueba programada','motivo':'Comparar con evidencia',
                'cuando':cuando or {'tipo':'ahora'},'pasos':pasos}
    def test_saved_task_waits_until_condition(self):
        # Una tarea de un proyecto solo se activa si ese proyecto sigue vivo.
        self.p['project']={'id':'proj','status':'activo'}
        set_agenda(self.p,[self.new_task([{'op':'inspect','target':''}],
            {'tipo':'despues_de_minutos','minutos':60})],0,'proj')
        self.assertIsNone(choose_agenda_step(self.w,self.p))
        self.p['clock_minutes']=60
        selected=choose_agenda_step(self.w,self.p)
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0]['_origin'],'agenda')
        record_agenda_result(self.p,selected[0],True,['Observé una roca'], 'Día 1')
        self.assertEqual(self.p['agenda'][0]['estado'],'completada')
        self.assertIsNone(choose_agenda_step(self.w,self.p))
    def test_steps_link_and_failure_stops(self):
        set_agenda(self.p,[self.new_task([{'op':'inspect','target':''},{'op':'rest'}])],0)
        step,_=choose_agenda_step(self.w,self.p)
        record_agenda_result(self.p,step,False,['El intento falló'],'Día 1')
        self.assertEqual(self.p['agenda'][0]['indice'],0)
        self.assertEqual(self.p['agenda'][0]['estado'],'bloqueada')
        self.assertIsNone(choose_agenda_step(self.w,self.p))
    def test_does_not_pathfind_through_unknown(self):
        self.p['pos']=[1,1,0];self.w['levels']['0']=['.'*W for _ in range(H)]
        self.w['revealed']=[tile_key(1,1,0),tile_key(3,1,0)]
        self.assertFalse(safe_step(self.w,self.p,{'op':'go','x':3,'y':1}))
        self.w['revealed'].append(tile_key(2,1,0))
        self.assertTrue(safe_step(self.w,self.p,{'op':'go','x':3,'y':1}))
    def test_no_manual_exploration_in_agenda(self):
        self.assertIsNone(normalize_task(self.new_task([{'op':'explore'}]),0))
        self.assertIsNone(normalize_task(self.new_task([{'op':'build','materials':['madera']}]),0))
    def test_missing_material_retries_bounded(self):
        set_agenda(self.p,[self.new_task([{'op':'craft','materials':['madera'],'name':'cuenco'}],
                 {'tipo':'cuando_haya_material','material':'madera','cantidad':1})],0)
        self.p['inventory']['madera']=0
        self.assertIsNone(choose_agenda_step(self.w,self.p))
        self.p['inventory']['madera']=1
        self.assertIsNotNone(choose_agenda_step(self.w,self.p))
    def test_physical_needs_do_not_cancel_feasible_queued_work(self):
        set_agenda(self.p,[self.new_task([{'op':'inspect','target':''}])],0)
        self.p['needs']['hidratacion']=12
        self.assertIsNotNone(choose_agenda_step(self.w,self.p))
    def test_strict_inspect_missing_target(self):
        _,facts,success,_=execute_action(self.w,self.p,{'op':'inspect','target':'agua'},random.Random(2))
        self.assertFalse(success)
        self.assertIn('agua',facts[0])
        self.assertNotIn('Examiné arboleda',facts[0])
    def test_parse_agenda_from_llm(self):
        d=normalize_decision({'cuaderno':'Una prueba.','plan':[{'op':'rest'}],
                               'agenda':[self.new_task([{'op':'rest'}])]})
        self.assertEqual(len(d['agenda']),1)
    def test_user_retry_respects_429(self):
        old=nilo.DB
        with tempfile.TemporaryDirectory() as d:
            try:
                nilo.DB=Path(d)/'world.sqlite3';sim=nilo.Simulation()
                from providers import candidate_configs
                cfg={'PROVIDER':'gemini','MODEL':'gemini-3.1-flash-lite',
                     'GEMINI_API_KEY':'fake','GEMINI_FALLBACK_MODELS':'',
                     'BACKUP_PROVIDER':'none','MAX_LLM_CALLS_PER_DAY':'999'}
                health_key=candidate_configs(cfg)[0][1]['_health_key']
                sim.s['provider_health'][health_key]={'cooldown_until':time.time()+2000,
                    'last_status':429}
                with patch.object(nilo,'config',return_value=cfg):
                    self.assertFalse(sim.retry_llm()['ok'])
                sim.conn.close()
            finally:nilo.DB=old
    def test_autopause_keeps_sim_clock_and_attempts_again(self):
        old=nilo.DB
        with tempfile.TemporaryDirectory() as d:
            try:
                nilo.DB=Path(d)/'world.sqlite3';sim=nilo.Simulation()
                sim.s['person']['clock_minutes']=200
                sim.s['auto_wait_frozen']=True
                sim.s['next_deliberation_real']=time.time()+3600
                sim.tick(25)
                self.assertEqual(sim.s['person']['clock_minutes'],200)
                invoked=[];sim.think=lambda:invoked.append(True)
                sim.s['next_deliberation_real']=0
                sim.tick(5)
                self.assertEqual(invoked,[True])
                sim.conn.close()
            finally:nilo.DB=old

if __name__=='__main__':unittest.main()

class GoalTests(unittest.TestCase):
    def test_verified_simple_goal_closes_with_real_evidence(self):
        from goals import verified_simple_goal
        s=nilo.initial_state();p=s['person'];w=s['world']
        p['project']={'id':'proj','status':'activo','title':'Explorar el entorno inmediato y localizar una fuente de agua.','progress':95}
        from world import set_tile
        set_tile(w,2,2,0,'~')
        w['revealed'].append(tile_key(2,2,0))
        w['visited']={f'{i},1,0':1 for i in range(26)}
        p['skills']={'drink':{'verified':True}}
        r=verified_simple_goal(w,p,'Día 9')
        self.assertIsNotNone(r)
        self.assertIsNone(p['project'])
        self.assertEqual(p['projects'][0]['closure_evidence']['accion_verificada'],'drink')
    def test_goal_not_closed_without_drinking_or_if_experiment(self):
        from goals import verified_simple_goal
        s=nilo.initial_state();p=s['person'];w=s['world']
        p['project']={'status':'activo','title':'Investigar condensación de agua'}
        p['skills']={'drink':{'verified':True}}
        self.assertIsNone(verified_simple_goal(w,p,'Día 9'))
