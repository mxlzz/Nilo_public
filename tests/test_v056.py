"""Nilo 05.6: comparación física verificable, rutinas menos invasivas y migración."""
import json
import tempfile
import unittest
from pathlib import Path
import nilo
from world import execute_action
from experiment_log import measure,capture
from laboratory import compare,measured_physics
from survival import ensure_needs,update_needs
from motivation import maintenance_summary,record_maintenance
from brain import normalize_decision,context_for


class GeneralLaboratoryTests(unittest.TestCase):
    def setUp(self):
        self.s=nilo.initial_state();self.p=self.s['person'];self.w=self.s['world']
        ensure_needs(self.p)
    def trial(self,material,method='golpear'):
        step={'op':'experiment','target':material,'method':method}
        a=capture(self.w,self.p)
        length,facts,success,_=execute_action(self.w,self.p,step,__import__('random').Random(5))
        self.assertTrue(success,facts)
        self.p['clock_minutes']+=length
        return measure(self.p,step,a,capture(self.w,self.p),facts,success,'Día 1')
    def test_material_hardness_real_and_comparison(self):
        a,b=self.trial('madera'),self.trial('piedra')
        self.assertEqual(a['physical']['kind'],'material')
        self.assertEqual(a['physical']['metrics']['dureza'],self.p['materials']['madera']['dureza'])
        ok,message,c=compare(self.p,{'evidence_ids':[a['id'],b['id']],'metric':'dureza'},'Día 2')
        self.assertTrue(ok,message)
        self.assertEqual(c['status'],'comparacion_medida')
        self.assertEqual(c['evidence_ids'],[a['id'],b['id']])
        self.assertIn('no demuestran',c['text'])
    def test_methods_cannot_be_mixed(self):
        a=self.trial('madera','golpear');b=self.trial('piedra','cargar')
        ok,why,c=compare(self.p,{'evidence_ids':[a['id'],b['id']]},'Día 2')
        self.assertFalse(ok);self.assertIsNone(c)
        self.assertIn('incompatibles',why)
    def test_cannot_compare_repeated_same_sample_or_forged_ids(self):
        a=self.trial('madera')
        ok,_,_=compare(self.p,{'evidence_ids':[a['id'],'med-forjado']},'Día 2')
        self.assertFalse(ok)
        a2=measure(self.p,{'op':'experiment','target':'madera','method':'golpear'},
            {'minute':0,'needs':dict(self.p['needs']),'inventory':dict(self.p['inventory']),
             'position':list(self.p['pos']),'sheltered':False,'objects':0,'structures':0},
            {'minute':3,'needs':dict(self.p['needs']),'inventory':dict(self.p['inventory']),
             'position':list(self.p['pos']),'sheltered':False,'objects':0,'structures':0},
            ['Ya había comprobado la respuesta'],True,'Día 2')
        self.assertNotIn('physical',a2)
        ok,_,_=compare(self.p,{'evidence_ids':[a['id'],a2['id']]},'Día 2')
        self.assertFalse(ok)
    def test_tool_rejects_imagined_outcome(self):
        item={'id':'obj-test','name':'recipiente','materials':['madera'],'geometry':{'shape':'hueco','size':1.8},'contents':{}}
        self.p.setdefault('items',[]).append(item)
        self.assertIsNone(measured_physics(self.p,{'op':'use','item':'obj-test','method':'llenar'},True,
                                           ['Quiero llenarlo mañana']))
        info=measured_physics(self.p,{'op':'use','item':'obj-test','method':'llenar'},True,
                                ["Llené 'recipiente' con 0.9 unidades de agua. Capacidad útil estimada: 0.9 unidades."])
        self.assertEqual(info['kind'],'recipiente')
        self.assertIn('capacidad_util_agua',info['metrics'])
    def test_normalizer_and_context_offer_compare(self):
        raw={'cuaderno':'Voy a comparar dos ensayos que ya medí.','plan':[{'op':'compare','evidence_ids':['med-1','med-2'],'metric':'dureza'}]}
        self.assertEqual(normalize_decision(raw)['plan'][0]['op'],'compare')
        ctx=context_for(self.w,self.p,[],'Día 1')
        self.assertIn('costo_mantenimiento_reciente',ctx)


class SurvivalAndMaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.p=nilo.initial_state()['person'];ensure_needs(self.p)
    def test_hydration_and_nutrition_less_invasive(self):
        before=dict(self.p['needs']);update_needs(self.p,{},60,False,False,True)
        self.assertAlmostEqual(before['hidratacion']-self.p['needs']['hidratacion'],.55,places=2)
        self.assertAlmostEqual(before['nutricion']-self.p['needs']['nutricion'],.32,places=2)
    def test_safety_and_shelter_not_magic(self):
        initial=dict(self.p['needs'])
        update_needs(self.p,{},120,False,False,False)
        self.assertEqual(self.p['needs']['seguridad'],initial['seguridad'])
        self.assertEqual(self.p['needs']['abrigo'],initial['abrigo'])
        update_needs(self.p,{},120,True,False,False)
        self.assertEqual(self.p['needs']['seguridad'],initial['seguridad'])
    def test_observed_maintenance_not_forced_objective(self):
        self.p['clock_minutes']=200
        for _ in range(4):record_maintenance(self.p,'forage','Día 1',target='alimento')
        s=maintenance_summary(self.p)
        self.assertTrue(s['repeticion_detectada'])
        self.assertIn('podría',s['observacion'])
        self.assertNotIn('plan',s)


class MigrationAndPersistenceTests(unittest.TestCase):
    def test_old_save_safe_and_new_comparison_persists(self):
        old=nilo.DB
        with tempfile.TemporaryDirectory() as d:
            try:
                nilo.DB=Path(d)/'nilo_mundo.sqlite3'
                sim=nilo.Simulation();sim.think=lambda:None
                p=sim.s['person'];w=sim.s['world']
                p.pop('maintenance_history',None)
                p.setdefault('measurements',[]).append({'id':'med-a','physical':{'kind':'material','method':'golpear','subject':'madera','metrics':{'dureza':3},'conditions':{'material':'madera'}}})
                p['measurements'].append({'id':'med-b','physical':{'kind':'material','method':'golpear','subject':'piedra','metrics':{'dureza':8},'conditions':{'material':'piedra'}}})
                ok,_,conclusion=compare(p,{'evidence_ids':['med-a','med-b'],'metric':'dureza'},'Día 3')
                self.assertTrue(ok)
                sim.archive.add('conclusion',conclusion)
                sim.write();sim.conn.close()
                reopened=nilo.Simulation();reopened.think=lambda:None
                self.assertIn('maintenance_history',reopened.s['person'])
                self.assertEqual(reopened.s['person']['conclusions'][-1]['id'],conclusion['id'])
                self.assertGreaterEqual(reopened.archive.counts()['conclusion'],1)
                reopened.conn.close()
            finally:nilo.DB=old

if __name__=='__main__':unittest.main()
