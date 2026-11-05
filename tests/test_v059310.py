"""Regresiones de decisiones autónomas posteriores al run de casi diez días.

Casos sintéticos derivados de fallos observados, sin API, SQLite externa ni
reconstrucción de información que la partida antigua no registró.
"""
import tempfile
import hashlib
import json
import zipfile
import unittest
from pathlib import Path

from brain import normalize_decision
from episodic_memory import recall_relevant
from laboratory import compare, comparison_candidates
from nilo import Simulation


def decision(action,plan=None,proof='',objective='Evaluar el refugio',pid='pr-1'):
    return normalize_decision({
        'cuaderno':'Voy a registrar qué hacer con esta investigación.',
        'objetivo':objective,'motivo':'No obtuve nuevos ensayos evaluables.',
        'estado_actual':'La línea actual no produjo una conclusión.',
        'proyecto_id':pid,'accion_proyecto':action,
        'prueba_cierre':proof,'plan':plan if plan is not None else [],
        'avance_estimado':95})


class DecisionContract(unittest.TestCase):
    def test_empty_plan_valid_only_when_closing_or_pausing(self):
        for a in ('completar','abandonar','pausar'):
            self.assertEqual(decision(a)['plan'],[])
        with self.assertRaises(ValueError):
            decision('nuevo')
        with self.assertRaises(ValueError):
            decision('continuar')

    def test_remember_non_evaluable_is_not_equivalent_to_verified_failure(self):
        self.assertIn('abandonar', decision('abandonar')['accion_proyecto'])


class ProjectLifecycle(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.sim=Simulation(db_path=Path(self.folder.name)/'world.sqlite')
        self.p=self.sim.s['person']
        self.project={'id':'pr-1','title':'Evaluar el refugio','status':'activo',
            'progress':95,'verified_results':[],'no_progress_steps':9,
            'deliberations':19,'deliberations_since_progress':9}
        self.p['project']=self.project
        self.p.setdefault('agenda',[]).append({
            'id':'task-old','proyecto_id':'pr-1','estado':'pendiente',
            'pasos':[{'op':'inspect','target':'refugio'}]})

    def tearDown(self):
        self.sim.conn.close()
        self.folder.cleanup()

    def test_abandonment_stops_project_without_claiming_success(self):
        self.sim.plan_ready(decision('abandonar'), 'llm')
        self.assertIsNone(self.p['project'])
        self.assertEqual(self.p['plan'],[])
        self.assertEqual(self.project['status'],'abandonado')
        self.assertEqual(self.project['progress'],95)
        self.assertNotIn('closure_evidence',self.project)
        self.assertEqual(len(self.p['projects']),1)
        self.assertEqual(self.p['agenda'][-1]['estado'],'cancelada')
        self.assertEqual(self.project['closure_kind'],'abandonado')

    def test_completion_with_evidence_does_not_restart_project(self):
        fact='Fabriqué y comprobé un recipiente con materiales reales.'
        self.project['title']='Fabricar un recipiente'
        self.project['verified_results']=[{'action':'craft','result':fact,
                                            'measurement_id':'med-probada','when':'Día 1'}]
        self.p.setdefault('measurements',[]).append({
            'id':'med-probada','op':'craft','success':True,
            'evaluation_status':'verified_success','verified_facts':[fact]})
        self.sim.plan_ready(decision('completar',proof=fact), 'llm')
        self.assertIsNone(self.p['project'])
        self.assertEqual(self.p['plan'],[])
        self.assertEqual(self.project['status'],'terminado')
        self.assertEqual(self.project['progress'],100)
        self.assertEqual(len(self.p['projects']),1)

    def test_unverified_completion_does_not_claim_success(self):
        self.sim.plan_ready(decision('completar'), 'llm')
        self.assertIs(self.p['project'],self.project)
        self.assertNotIn('closure_evidence',self.project)
        self.assertNotEqual(self.project.get('status'),'terminado')

    def test_paused_project_does_not_run_old_agenda(self):
        self.sim.plan_ready(decision('pausar'), 'llm')
        self.assertIsNone(self.p['project'])
        task=self.p['agenda'][-1]
        self.assertEqual(task['estado'],'pospuesta')
        self.assertGreater(task['reanudar_minuto'],self.p['clock_minutes']+100000)
        self.assertEqual(self.project['status'],'pausado')
        self.sim.plan_ready(decision('continuar',plan=[{'op':'rest'}]), 'llm')
        self.assertEqual(self.p['project']['id'],'pr-1')
        self.assertEqual(task['ultimo_motivo'],'Proyecto retomado')
        self.assertLessEqual(task['reanudar_minuto'],self.p['clock_minutes'])


class EvidenceAndComparison(unittest.TestCase):
    def test_rest_comparison_uses_real_measured_rates(self):
        samples=[{'id':'med-ref','op':'rest','rest_comparable':True,'condition':'refugio',
                  'energy_per_hour':10.2},
                 {'id':'med-ext','op':'rest','rest_comparable':True,'condition':'intemperie',
                  'energy_per_hour':6.5},
                 {'id':'med-empty','op':'inspect','physical':None}]
        p={'measurements':samples,'conclusions':[]}
        candidates=comparison_candidates(p)
        self.assertEqual(candidates[0]['evidence_ids'],['med-ref','med-ext'])
        ok,_,result=compare(p,{'evidence_ids':['med-ref','med-ext'],
                              'metric':'energia_por_hora'},'Día 2')
        self.assertTrue(ok)
        self.assertEqual(result['evidence_ids'],['med-ref','med-ext'])
        self.assertFalse(compare(p,{'evidence_ids':['med-empty','med-ref']},'Día 2')[0])
        self.assertFalse(compare(p,{'evidence_ids':['med-ref','med-ref']},'Día 2')[0])


class SpatialMemory(unittest.TestCase):
    def test_successful_known_cave_returned_when_surface_stagnates(self):
        p={'pos':[15,10,0],'project':{'title':'Investigar límites de construcciones',
            'no_progress_steps':5},'life_history':[
                {'id':'transition','when':'Día 3','action':'descend','successful':True,
                 'fact':'Descendí a la cueva; observé una salida hacia la superficie.'},
                *[{'id':f'failed-{i}','when':'Día 10','action':'explore',
                    'successful':False,'fact':'No encuentro sectores desconocidos accesibles.'}
                  for i in range(6)]]}
        world={'sites':{'cueva':{'x':23,'y':7,'z':0}},'revealed':['23,7,0']}
        remembered=recall_relevant(p,world)
        self.assertTrue(remembered)
        self.assertEqual(remembered[0]['id'],'transition')
        self.assertEqual(remembered[0]['lugar_conocido'],[23,7,0])
        world['revealed']=[]
        self.assertFalse(any(row.get('lugar_conocido') for row in recall_relevant(p,world)))


class PackageVersion(unittest.TestCase):
    def test_version_and_complete_artifact_manifest(self):
        from empaquetar_version import build_package
        root=Path(__file__).resolve().parent.parent
        version=(root/'VERSION').read_text('utf-8').strip()
        self.assertTrue(version and all(part.isdigit() for part in version.split('.')))
        with tempfile.TemporaryDirectory() as folder:
            package=build_package(root,Path(folder))
            with zipfile.ZipFile(package) as z:
                prefix=f'Nilo-{version}/'
                manifest=json.loads(z.read(prefix+'MANIFIESTO_SHA256.json'))
                self.assertEqual(manifest['version'],version)
                for required in ('brain.py','diagnostic_guidance.py','project_lifecycle.py',
                                 'laboratory.py','tests/test_v059310.py'):
                    self.assertIn(required,manifest['files'])
                for path,digest in manifest['files'].items():
                    self.assertEqual(hashlib.sha256(z.read(prefix+path)).hexdigest(),digest)
                self.assertFalse(any(name.endswith('config.env') for name in z.namelist()))



if __name__=='__main__':
    unittest.main()
