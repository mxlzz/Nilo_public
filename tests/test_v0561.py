"""Regresión 0.5.6.1: problemas observados en partida real.

No requiere red, ni altera partidas del usuario.
"""
from __future__ import annotations
import copy
import io
import json
import sqlite3
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import nilo
from brain import compact_context, request_llm, context_for
from construction import apply_intervention, ensure_object
from habits import choose_wait_action, set_wait_preferences
from providers import error_from_http
from survival import ensure_needs, NEEDS_DEFAULT, update_needs
from world import W, H, pathfind, prepare_navigation, set_tile, tile_key

class StabilizationTests(unittest.TestCase):
    def setUp(self):
        self.s=nilo.initial_state();self.p=self.s['person'];self.w=self.s['world']
        ensure_needs(self.p)

    def test_rest_preference_stops_before_engine_ceiling(self):
        self.p['waiting_preferences']=[{'op':'rest','target':'','hasta':2,'radio':2,'motivo':'Descanso previsto'}]
        self.p['needs'].update(energia=70,hidratacion=80)
        self.assertNotEqual((choose_wait_action(self.w,self.p,legacy_wait_policy=True) or ({},))[0].get('op'),'rest')
        self.p['needs']['energia']=69
        self.assertEqual(choose_wait_action(self.w,self.p,legacy_wait_policy=True)[0]['op'],'rest')
        self.p['needs']['energia']=75.06
        self.assertNotEqual((choose_wait_action(self.w,self.p,legacy_wait_policy=True) or ({},))[0].get('op'),'rest')

    def test_water_takes_priority_over_rest_if_critical(self):
        self.p['pos']=[2,2,0]
        set_tile(self.w,3,2,0,'~')
        self.p['needs'].update(energia=35,hidratacion=0)
        self.assertEqual(choose_wait_action(self.w,self.p,legacy_wait_policy=True)[0]['op'],'drink')

    def test_known_safe_shore_navigation(self):
        self.p['pos']=[1,1,0]
        self.w['levels']['0']=['.'*W for _ in range(H)]
        set_tile(self.w,3,1,0,'~')
        self.w['revealed']=[tile_key(x,1,0) for x in (1,2,3)]
        self.p['needs'].update(energia=65,hidratacion=0)
        step,reason=choose_wait_action(self.w,self.p,legacy_wait_policy=True)
        self.assertEqual(step['op'],'go')
        self.assertEqual((step['x'],step['y']),(2,1))
        plan=prepare_navigation(self.w,self.p,dict(step,_origin='espera'),None)
        self.assertIsNotNone(plan)
        self.assertEqual(plan['route'],[[2,1]])
        self.assertIn('conocid',reason)

    def test_autonomy_does_not_enter_unseen_tiles_on_route(self):
        self.p['pos']=[1,1,0]
        self.w['levels']['0']=['.'*W for _ in range(H)]
        set_tile(self.w,4,1,0,'~')
        self.w['revealed']=[tile_key(x,1,0) for x in (1,3,4)]
        self.p['needs'].update(energia=65,hidratacion=0)
        # There is an engine path, but it crosses unknown tile (2,1).
        self.assertTrue(pathfind(self.w,(1,1,0),(3,1,0)))
        self.assertFalse(pathfind(self.w,(1,1,0),(3,1,0),known_only=True))
        step=choose_wait_action(self.w,self.p,legacy_wait_policy=True)
        self.assertFalse(step and step[0]['op']=='go')

    def test_critical_water_drink_without_previous_explicit_skill(self):
        self.p['pos']=[2,2,0];set_tile(self.w,3,2,0,'~')
        self.p['needs']['hidratacion']=0
        self.assertEqual(choose_wait_action(self.w,self.p,legacy_wait_policy=True)[0]['op'],'drink')
        before=self.p['needs']['hidratacion']
        update_needs(self.p,self.w,1,near_water=True,legacy_autocare=True)
        self.assertGreater(self.p['needs']['hidratacion'],before)

    def test_legacy_zero_bars_migrate_only_once(self):
        old=nilo.DB
        with tempfile.TemporaryDirectory() as d:
            try:
                nilo.DB=Path(d)/'copy.sqlite3'
                sim=nilo.Simulation()
                self.assertTrue(sim.s['person']['passive_needs_migrated_v0561'])
                sim.s['person']['needs']['seguridad']=0
                sim.s['person']['needs']['abrigo']=0
                sim.s['person'].pop('passive_needs_migrated_v0561')
                sim.write();sim.conn.close()
                migrated=nilo.Simulation()
                p=migrated.s['person']
                self.assertEqual(p['needs']['seguridad'],NEEDS_DEFAULT['seguridad'])
                self.assertEqual(p['needs']['abrigo'],NEEDS_DEFAULT['abrigo'])
                self.assertEqual(len(p['migration_fixes']),1)
                p['needs']['seguridad']=41
                migrated.write();migrated.conn.close()
                again=nilo.Simulation()
                self.assertEqual(again.s['person']['needs']['seguridad'],41)
                self.assertEqual(len(again.s['person']['migration_fixes']),1)
                again.conn.close()
            finally:nilo.DB=old

    def test_tool_revision_does_not_inherit_past_test(self):
        obj={'id':'obj-local','name':'recipiente','purpose':'almacenar agua',
             'materials':['madera'],'form':'recipiente','portable':True,
             'resistance':5,'hardness':3,'weight':2,'durability':100,
             'geometry':{'shape':'hueco','size':1},
             'tests':[{'method':'llenar','success':True,'revision':1}],
             'verified_revision':1,'verified_function_current':True}
        ensure_object(obj,structure=False)
        self.p['items']=[obj]
        self.p['inventory']['madera']=4
        duration,facts,success,notable=apply_intervention(self.w,self.p,
             {'op':'modify','item':'obj-local','mode':'add','materials':['madera']})
        self.assertTrue(success,facts)
        self.assertEqual(obj['revision'],2)
        self.assertFalse(obj['verified_function_current'])
        self.assertIsNone(obj['verified_revision'])
        self.assertEqual(obj['tests'][0]['revision'],1)
        context=context_for(self.w,self.p,[],'Día 2')
        self.assertFalse(context['herramientas_que_llevo'][0]['pruebas_version_actual'])

    def test_http413_is_not_a_transient_retry(self):
        exc=urllib.error.HTTPError('https://example.com',413,'Too big',{},io.BytesIO(b'{"error":{"message":"Request too large"}}'))
        failure=error_from_http(exc,'groq')
        self.assertEqual(failure.category,'too_large')
        self.assertIn('413',str(failure))

    def test_compact_context_preserves_essentials_and_is_bounded(self):
        ctx=context_for(self.w,self.p,[],'Día 2')
        ctx['herramientas_que_llevo']=[{'id':str(i),'nombre':'x'*700} for i in range(100)]
        ctx['mediciones_reales_recientes']=[{'id':str(i),'value':'y'*200} for i in range(30)]
        slim=compact_context(ctx,4700)
        self.assertIn('necesidades',slim)
        self.assertIn('orillas_agua_conocidas_alcanzables',slim)
        self.assertLessEqual(len(json.dumps(slim,ensure_ascii=False,separators=(',',':'))),4700)

    def test_groq_request_budget_and_structured_json(self):
        cfg={'PROVIDER':'groq','GROQ_API_KEY':'fake','MODEL':'openai/gpt-oss-20b'}
        captured={}
        class FakeResponse:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*a):return b''
        def fake_open(req,timeout):
            payload=json.loads(req.data)
            captured.update(payload)
            assert len(payload['messages'][-1]['content'])<5000
            return io.BytesIO(json.dumps({'choices':[{'message':{'content':'{"plan":[{"op":"rest"}]}'}}],
               'usage':{'prompt_tokens':1,'completion_tokens':3}}).encode())
        with patch('brain.urllib.request.urlopen',side_effect=fake_open):
            raw,tokens=request_llm(cfg,context_for(self.w,self.p,[],'Día 1'))
        self.assertEqual(raw['plan'][0]['op'],'rest')
        self.assertLessEqual(captured['max_completion_tokens'],1550)


    def test_groq_chat_keeps_unread_catchup_in_context(self):
        from brain import request_chat
        cfg={'PROVIDER':'groq','GROQ_API_KEY':'fake','MODEL':'openai/gpt-oss-20b'}
        actual={}
        def fake_open(req,timeout):
            payload=json.loads(req.data)
            actual.update(payload)
            return io.BytesIO(json.dumps({'choices':[{'message':{'content':'Te cuento las novedades verificadas.'}}]}).encode())
        ctx={'posición':[1,1,0],'resumen_de_lo_no_leido':{'total':2,'entradas':[
            {'id':'nota-1','tipo':'Cuaderno','texto':'Observé una roca.'},
            {'id':'nota-2','tipo':'Novedad','texto':'Construí un refugio.'}]},
            'instruccion_de_resumen':'Resumí solo estas entradas.'}
        with patch('brain.urllib.request.urlopen',side_effect=fake_open):
            reply,tokens=request_chat(cfg,ctx,[{'role':'user','text':'¿Qué me perdí?'}])
        sent=actual['messages'][0]['content']
        self.assertIn('nota-1',sent)
        self.assertIn('nota-2',sent)
        self.assertIn('Resumí solo estas entradas',sent)

if __name__=='__main__':unittest.main()
