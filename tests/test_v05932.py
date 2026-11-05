"""0.5.9.3.2 — contrato de inspección, proyectos, pruebas y diagnóstico."""
import json
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from action_contracts import ACTION_GUIDE, instructions, spec_for
from archive import History
from brain import normalize_decision, demo_decision
from cognition import same_research
from inventions import submit_debug_report
from project_lifecycle import completion_evidence
from research_cycle import prediction_metric_warning
from world import execute_action, new_world
from nilo import Simulation

ROOT=Path(__file__).resolve().parent.parent


class ManualAndInspection(unittest.TestCase):
    def setUp(self):
        self.world=new_world()
        self.person={'pos':[15,10,0],'inventory':{'alimento':14},'items':[],
                     'clock_minutes':0,'needs':{'energia':50,'nutricion':65,'hidratacion':65,
                                               'seguridad':90,'abrigo':90}}
        self.world['structures'].append({'id':'obra-ref-1','name':'Refugio de prueba',
                    'pos':[15,10,0],'materials':['madera'],'status':'Prototipo sin verificar',
                    'function_tests':[]})

    def test_contract_is_a_reference_not_an_action(self):
        self.assertIn('inspect',ACTION_GUIDE)
        self.assertNotIn('manual',ACTION_GUIDE)
        self.assertIn('inspect',instructions())
        self.assertIn('contrato',spec_for('inspect'))

    def test_local_structure_by_id_and_coordinates(self):
        for step in ({'op':'inspect','target':'obra-ref-1'},
                     {'op':'inspect','x':15,'y':10},
                     {'op':'inspect','target':'Refugio de prueba (15,10)'}):
            _,facts,success,_=execute_action(self.world,self.person,step,random.Random(1))
            self.assertTrue(success,facts)
            self.assertIn('obra-ref-1',facts[0])

    def test_remote_building_is_known_but_out_of_range(self):
        self.world['structures'][0]['pos']=[30,15,0]
        _,facts,success,_=execute_action(self.world,self.person,
                      {'op':'inspect','target':'obra-ref-1'},random.Random(1))
        self.assertFalse(success)
        self.assertIn('fuera de alcance',facts[0])

    def test_held_tool_by_id(self):
        self.person['items']=[{'id':'tool-1','name':'Cincel','form':'punta',
                              'materials':['piedra'],'durability':85,'tests':[]}]
        _,facts,success,_=execute_action(self.world,self.person,
                    {'op':'inspect','target':'tool-1'},random.Random(1))
        self.assertTrue(success)
        self.assertIn('Durabilidad: 85',facts[0])

    def test_food_stock_cap_is_non_destructive(self):
        before=dict(self.person['inventory'])
        _,facts,success,_=execute_action(self.world,self.person,
                    {'op':'forage'},random.Random(1))
        self.assertFalse(success)
        self.assertIn('14 porciones',facts[0])
        self.assertEqual(self.person['inventory'],before)


class PlansAndPredictions(unittest.TestCase):
    def test_new_project_does_not_reuse_selected_id(self):
        with tempfile.TemporaryDirectory() as path:
            sim=Simulation(db_path=Path(path)/'run.sqlite3')
            try:
                sim.s['person']['project']={'id':'older','title':'Antigua misión','status':'activo',
                                  'progress':95,'steps_done':5,'verified_results':[]}
                decision={'objetivo':'Inventar un mecanismo','motivo':'Tengo una idea',
                  'proyecto_id':'older','accion_proyecto':'nuevo','plan':[{'op':'inspect','target':'suelo'}],
                  'subobjetivos':[],'cuaderno':'Pensaré otro problema.','pregunta':'',
                  'hipotesis':'','revisar_en_minutos':60,'avance_estimado':2,
                  'estado_actual':'Preparando','prueba_cierre':'','agenda':[]}
                sim.plan_ready(decision,'demo')
                self.assertNotEqual(sim.s['person']['project']['id'],'older')
                self.assertEqual(sim.s['person']['project']['progress'],2)
                self.assertTrue(any(q['id']=='older' for q in sim.s['person']['projects']))
            finally:sim.conn.close()

    def test_project_close_requires_its_own_evidence(self):
        project={'title':'Descansar para recuperar energía',
                 'verified_results':[{'when':'Día 2','action':'rest',
                   'result':'Recuperé energía al descansar',
                   'measurement_id':'med-1234567890'}]}
        person={'measurements':[{'id':'med-1234567890','op':'rest','success':True,
                 'evaluation_status':'verified_success','needs_delta':{'energia':8},
                 'verified_facts':['Recuperé energía al descansar']}]}
        self.assertIsNotNone(completion_evidence(project,'med-1234567890',person))
        self.assertIsNone(completion_evidence(project,'med-no-existe12345',person))
        self.assertIsNone(completion_evidence(project,'descansar es bueno',person))

    def test_preflight_keeps_physical_action_and_blocks_unmodelled_metric(self):
        step={'op':'use','method':'contener',
              'prediction':{'metric':'potabilidad','operator':'gte','threshold':80}}
        self.assertIn('no mide',prediction_metric_warning(step))
        step['prediction']['metric']='capacidad_util_agua'
        self.assertEqual(prediction_metric_warning(step),'')
        self.assertEqual(prediction_metric_warning({'op':'rest','method':'',
                     'prediction':{'metric':'energy_per_hour','operator':'gt','threshold':0}}),'')

    def test_manual_is_not_accepted_as_an_action(self):
        with self.assertRaises(ValueError):
            normalize_decision({'cuaderno':'No debe existir un comando manual','plan':[{'op':'manual','target':'inspect'}]})


class DiagnosticAndHistory(unittest.TestCase):
    def test_manual_link_in_debug_report_is_explicit(self):
        person={'proposals':[],'action_outcomes':[{'id':'act-123','op':'inspect','success':False,
                          'facts':['No pude identificarlo'],'when':'Día 2'}]}
        success,_=submit_debug_report(person,{
          'title':'El objeto no se encuentra','expected':'Encontrar mi construcción',
          'observed':'No identifico el objetivo','rationale':'Estoy al lado del refugio',
          'related_action':'inspect','issue_kind':'limitacion','evidence_ids':['act-123']},'Día 2')
        self.assertTrue(success)
        self.assertEqual(person['proposals'][0]['issue_kind'],'limitacion')
        self.assertEqual(person['proposals'][0]['manual_reference'],'inspect')
        self.assertEqual(len(person['proposals'][0]['evidence']),1)

    def test_duplicate_history_does_not_inflate_sqlite_sequence(self):
        db=sqlite3.connect(':memory:')
        try:
            archive=History(db)
            record={'id':'note-a','when':'Día 1','text':'Una sola entrada'}
            archive.add('journal',record)
            first=db.execute("SELECT seq FROM sqlite_sequence WHERE name='history'").fetchone()[0]
            for _ in range(25):archive.add('journal',record)
            last=db.execute("SELECT seq FROM sqlite_sequence WHERE name='history'").fetchone()[0]
            self.assertEqual(first,last)
            self.assertEqual(archive.counts()['journal'],1)
        finally:db.close()

    def test_proposals_have_internal_filters_without_new_tab(self):
        html=(ROOT/'interfaz.html').read_text('utf-8')
        self.assertIn('data-proposal-filter=',html)
        self.assertIn("proposalFilter==='debug'",html)
        self.assertIn("issue_kind==='limitacion'",html)
        self.assertNotIn('data-tab="debug"',html)

if __name__=='__main__':unittest.main()
