"""0.5.9.3.13: regressions from the 14-day run; no real-world secrets or save files."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nilo
from archive import History
from cognition import register_research
from goal_evidence import check_goal, select_closure_evidence
from observer import pending_sources
from project_lifecycle import retire_project
from review_store import ReviewStore


def measurement(mid,op,description,target='',method='',delta=None):
    return {'id':mid,'op':op,'target':target,'method':method,
            'success':True,'evaluation_status':'verified_success',
            'verified_facts':[description],'needs_delta':delta or {}}


def project(title,records):
    return {'id':'pr-1','title':title,'verified_results':[
        {'action':op,'measurement_id':mid,'result':description,'when':'Día 5'}
        for mid,op,description in records]}


class GoalsAreNotProofs(unittest.TestCase):
    def test_water_does_not_prove_solid_containment(self):
        fact="Llené 'recipiente_mineral' con agua. Retención estimada 86%."
        pr=project('Fabricar un recipiente mineral capaz de contener materiales sólidos sin pérdida',
                   [('med-water','use',fact)])
        p={'measurements':[measurement('med-water','use',fact,'agua','contener')]}
        self.assertFalse(check_goal(pr,p)[0])
        self.assertIsNone(select_closure_evidence(pr,p,fact))

    def test_solid_trial_must_not_prove_zero_loss(self):
        fact="El recipiente 'recipiente_mineral' sostuvo una muestra de arcilla."
        pr=project('Contener materiales sólidos sin pérdida',[('med-solid','use',fact)])
        p={'measurements':[measurement('med-solid','use',fact,'arcilla','contener')]}
        self.assertFalse(check_goal(pr,p)[0])

    def test_excavation_does_not_prove_return_and_rest(self):
        fact='Despejé la casilla (14,13) al excavar roca y recuperé dos piedras.'
        pr=project('Regresar al refugio y descansar para recuperar energía',
                   [('med-rock','use',fact)])
        p={'measurements':[measurement('med-rock','use',fact,'roca','excavar')]}
        self.assertIsNone(select_closure_evidence(pr,p,fact))

    def test_water_does_not_prove_exploration(self):
        fact="Llené 'recipiente_mineral' con agua."
        pr=project('Explorar el sector este buscando materiales resistentes y ruinas',
                   [('med-water','use',fact)])
        p={'measurements':[measurement('med-water','use',fact,'agua','contener')]}
        self.assertFalse(check_goal(pr,p)[0])

    def test_verified_fabrication_of_same_object_is_accepted(self):
        fact='Fabriqué un recipiente mineral con piedra y mineral.'
        pr=project('Fabricar un recipiente mineral',[('med-craft','craft',fact)])
        p={'measurements':[measurement('med-craft','craft',fact)]}
        result=select_closure_evidence(pr,p,fact)
        self.assertIsNotNone(result)
        self.assertEqual(result['evidence_ids'],['med-craft'])

    def test_verified_solid_containment_without_zero_loss_claim_is_accepted(self):
        fact="El recipiente 'recipiente_mineral' sostuvo una muestra de arcilla."
        pr=project('Verificar que el recipiente mineral pueda contener sólidos',
                   [('med-arcilla','use',fact)])
        p={'measurements':[measurement('med-arcilla','use',fact,'arcilla','contener')]}
        self.assertTrue(check_goal(pr,p)[0])

    def test_missing_measurement_cannot_be_fabricated_from_prose(self):
        fact='El recipiente retuvo todos los sólidos.'
        pr=project('Contener sólidos',[('med-inexistente','use',fact)])
        self.assertIsNone(select_closure_evidence(pr,{'measurements':[]},fact))


class ResearchProvenance(unittest.TestCase):
    def test_pause_and_resume_same_question_without_false_conclusion(self):
        p={'project':{'id':'project-one','title':'Recipiente','status':'activo',
                       'verified_results':[],'progress':20},
           'projects':[],'research':[],'agenda':[],'conclusions':[]}
        first,created=register_research(
            p,'¿Cómo medir la capacidad del recipiente?',
            'Una prueba con arcilla permitiría medirla.','Día 1','research-one')
        self.assertTrue(created)
        self.assertEqual(first['project_ids'],['project-one'])
        retire_project(p,p['project'],'pausado','Día 2')
        self.assertEqual(first['state'],'pausada')
        self.assertNotIn('conclusion',first)
        p['project']={'id':'project-two','title':'Investigación retomada','status':'activo'}
        same,new=register_research(p,'¿Cómo medir la capacidad del recipiente?',
                                   'Repetir con otro sólido.','Día 3','research-two')
        self.assertFalse(new)
        self.assertIs(first,same)
        self.assertEqual(same['state'],'abierta')
        self.assertIn('project-two',same['project_ids'])

    def test_historical_unlinked_research_remains_unmodified(self):
        p={'project':{'id':'project-one','title':'Caso','progress':20},
           'projects':[],'research':[{'id':'old','question':'¿Cómo excavar?',
                                     'state':'abierta'}],'agenda':[]}
        retire_project(p,p['project'],'abandonado','Día 2')
        self.assertEqual(p['research'][0]['state'],'abierta')


class BalancedSummary(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.sim=nilo.Simulation(db_path=Path(self.tmp.name)/'world.sqlite')
        self.sim.bootstrap_reviews({})
        self.settings={'PROVIDER':'gemini','MODEL':'fake','GEMINI_API_KEY':'placeholder'}
        self.patches=[
            patch.object(nilo,'config',return_value=self.settings),
            patch.object(nilo,'available',return_value=True),
            patch.object(nilo,'route',
                         return_value=(('Síntesis comprobada.',{}),'gemini','fake'))]
        for p in self.patches:p.start()

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.sim.conn.close()
        self.tmp.cleanup()

    def test_mixed_page_does_not_hide_high_priority_leftovers(self):
        candidates=[]
        for i in range(16):
            rid=f'pr-{i}'
            self.sim.archive.add('project',{'id':rid,'title':f'Construí un proyecto {i}',
                                            'status':'activo','started':f'Día {i+1}'})
            candidates.append({'tab':'projects','key':rid+':activo',
                               'kind':'project','id':rid})
        for i in range(3):
            rid=f'med-{i}'
            self.sim.archive.add('measurement',{
                'id':rid,'op':'use','method':'contener','target':'arcilla',
                'verified_facts':[f'Probé contención de arcilla {i}'],
                'evaluation_status':'verified_success'})
            candidates.append({'tab':'measurements','key':rid,
                               'kind':'measurement','id':rid})
        first=self.sim.observer_summary(candidates)
        self.assertEqual(first['count'],12)
        kinds={r['category'] for r in first['links']}
        self.assertIn('measurement',kinds)
        self.assertIn('project',kinds)
        self.sim.acknowledge_observer_summary(first['id'])
        second=self.sim.observer_summary(candidates,first['continuation'])
        self.assertEqual(second['count'],7)
        self.sim.acknowledge_observer_summary(second['id'])
        self.assertTrue(all(self.sim.review.is_seen('projects',f'pr-{i}:activo')
                            for i in range(16)))
        self.assertTrue(all(self.sim.review.is_seen('measurements',f'med-{i}')
                            for i in range(3)))


if __name__=='__main__':
    unittest.main()
