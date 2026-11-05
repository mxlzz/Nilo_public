"""0.5.9.3.27: espera voluntaria, capacidad útil y vistas compactas de proyectos."""
import json
import math
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from brain import normalize_decision
from action_contracts import ACTION_GUIDE, SUPPORTED_OPERATIONS
from survival import update_needs
from bodily_policy import rest_minutes
from laboratory import METRIC_LABELS, measured_physics
from physics import evaluate_containment
from nilo import Simulation

ROOT=Path(__file__).resolve().parent.parent
HTML=(ROOT/'interfaz.html').read_text('utf-8')


class WaitOperation(unittest.TestCase):
    def test_wait_is_distinct_supported_action_with_duration_validation(self):
        self.assertIn('wait',SUPPORTED_OPERATIONS)
        self.assertIn('no fuerza una disminución de energía',ACTION_GUIDE['wait'].lower())
        for requested,expected in [(None,30),(1,1),(1440,1440),(45.5,45.5)]:
            raw={'op':'wait'}
            if requested is not None:raw['minutes']=requested
            decision=normalize_decision({'cuaderno':'Espero por decisión propia.',
                'accion_proyecto':'sin_proyecto','plan':[raw]})
            self.assertEqual(decision['plan'][0]['minutes'],expected)
        for invalid in (0,-1,1441,float('nan'),'sin tiempo',True):
            decision=normalize_decision({'cuaderno':'No elegí esperar.',
                'accion_proyecto':'sin_proyecto','plan':[{'op':'wait','minutes':invalid},
                                                            {'op':'inspect','target':'suelo'}]})
            self.assertEqual(len(decision['plan']),1)
            self.assertEqual(decision['plan'][0]['op'],'inspect')

    def test_passive_wait_rest_and_active_are_distinct_rates(self):
        needs=lambda:{'needs':{'energia':40,'hidratacion':90,'nutricion':90,'abrigo':80,'seguridad':80}}
        idle,rest,physical=needs(),needs(),needs()
        update_needs(idle,{},60,active=False,resting=False)
        update_needs(rest,{},60,active=False,resting=True)
        update_needs(physical,{},60,active=True,resting=False)
        self.assertAlmostEqual(idle['needs']['energia'],40.8,places=1)
        self.assertAlmostEqual(rest['needs']['energia'],46.6,places=1)
        self.assertLess(physical['needs']['energia'],40)
        self.assertFalse(any(k in ACTION_GUIDE for k in ('sleep','dormir')))

    def test_wait_real_tick_and_sqlite_reopen(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'wait.sqlite3'
            sim=Simulation(db_path=file)
            try:
                sim.think=lambda:None
                p=sim.s['person']
                p['needs']['energia']=40
                p['plan']=[{'op':'wait','minutes':60}]
                sim._tick_slice(0)
                self.assertEqual(p['pending']['step']['op'],'wait')
                before=p['clock_minutes']
                # La duración corresponde a minutos simulados, no los retornados
                # por la operación world.execute_action.
                sim.s['speed']=60
                sim.tick(20);sim.tick(20);sim.tick(20)
                self.assertIsNone(p['pending'])
                self.assertAlmostEqual(p['clock_minutes']-before,60,places=1)
                # En 0.7 wait transcurre sin descanso: solo aplica el
                # desgaste fisiológico basal, no recupera energía pasivamente.
                self.assertLess(p['needs']['energia'],40)
                self.assertAlmostEqual(p['needs']['energia'],39.4,places=1)
                rows=[m for m in p['measurements'] if m.get('op')=='wait']
                self.assertEqual(len(rows),1)
                self.assertFalse(rows[0]['rest_comparable'])
                self.assertFalse(any('Descanso registrado' in x for x in rows[0].get('verified_facts',[])))
                sim.write()
            finally:
                sim.conn.close()
            resumed=Simulation(db_path=file)
            try:
                self.assertTrue(any(m['op']=='wait' for m in resumed.s['person']['measurements']))
            finally:
                resumed.conn.close()


class VesselTerminology(unittest.TestCase):
    def test_new_measurement_exposes_capacity_not_false_time_retention(self):
        p={'items':[{'id':'vessel-1','name':'Cuenco','materials':['piedra']*3,
                      'geometry':{'shape':'hueco','size':3}}],
           'materials':{}}
        sample=measured_physics(p,{'op':'use','method':'llenar','item':'vessel-1'},
                                True,["Llené 'Cuenco' con agua."])
        self.assertIn('capacidad_util_agua',sample['metrics'])
        self.assertNotIn('retencion_pct',sample['metrics'])
        self.assertNotIn('agua_retenida',sample['metrics'])
        self.assertEqual(sample['metrics']['capacidad_util_agua'],
                         evaluate_containment(p['items'][0],'agua',{})['quantity'])
        self.assertIn('NO mide pérdidas',sample['precision'])

    def test_historical_metric_labels_are_readable_without_data_migration(self):
        self.assertIn('histórico',METRIC_LABELS['retencion_pct'])
        self.assertIn('Capacidad útil',METRIC_LABELS['agua_retenida'])
        self.assertIn('Capacidad útil',METRIC_LABELS['capacidad_util_agua'])
        self.assertNotIn('Retención estimada',ROOT.joinpath('world.py').read_text('utf-8'))


class ProjectRelatedUi(unittest.TestCase):
    def test_compaction_executes_in_real_js_and_journal_remains_full(self):
        if not shutil.which('node'):self.skipTest('Node no disponible')
        js=HTML[HTML.index('const RECORD_LABELS='):HTML.index('function recordDescription(')]
        runner=r"""
const assert=require('node:assert'),vm=require('node:vm');
const src=require('node:fs').readFileSync(0,'utf8');
const esc=x=>String(x),data={record_relations:{}};
vm.runInThisContext(src);
const entries=[
 {category:'measurement',id:'m1',seq:10,phase:'new',title:'Primera prueba'},
 {category:'measurement',id:'m2',seq:20,phase:'related',title:'Segunda prueba'},
 {category:'measurement',id:'m3',seq:30,phase:'related',title:'Ultima prueba'},
 {category:'research',id:'r1',seq:11,phase:'updated',title:'Investigacion vieja'},
 {category:'research',id:'r2',seq:29,phase:'related',title:'Investigacion nueva'},
 {category:'tool',id:'t1',seq:14,phase:'new',title:'Una herramienta'}
];
const journal=recordLinks('journal','j',entries);
const project=projectRecordLinks('p',entries);
assert.equal((journal.match(/record-link-label/g)||[]).length,6);
assert.equal((project.match(/record-link-label/g)||[]).length,6);
assert.equal((project.match(/project-related-family/g)||[]).length,5); // 3 familia + 2 data attribute
assert.equal((project.match(/<details/g)||[]).length,2);
assert.equal((project.match(/<details[^>]*open/g)||[]).length,0);
assert.ok(project.indexOf('Ultima prueba')<project.indexOf('Primera prueba'));
assert.ok(project.indexOf('Investigacion nueva')<project.indexOf('Investigacion vieja'));
assert.ok(project.includes('Ver anteriores (2)'));
assert.ok(project.includes('Ver anteriores (1)'));
assert.ok(!project.includes('Ver anteriores (0)'));
assert.ok(!journal.includes('project-related-older'));
assert.equal(projectRecordLinks('p',[]),'');
"""
        proc=subprocess.run(['node','-e',runner],input=js,text=True,capture_output=True)
        self.assertEqual(proc.returncode,0,proc.stderr)

    def test_map_border_and_screen_margins(self):
        self.assertIn('.map-references{border-bottom:',HTML)
        self.assertNotIn('.map-references{border-top:',HTML)
        self.assertIn('.layout{max-width:none;margin:0;',HTML)
        self.assertIn('gap:12px;padding:12px}',HTML)
        self.assertIn('header{padding:9px 12px;',HTML)
        self.assertIn('footer.footer{flex:none;padding:0 12px 8px}',HTML)
        self.assertIn('${projectRecordLinks(p.id)}',HTML)
        self.assertIn('${recordLinks(\'journal\',e.id)}',HTML)
        self.assertIn('Nilo '+(ROOT/'VERSION').read_text('utf-8').strip(),HTML)


if __name__=='__main__':unittest.main()
