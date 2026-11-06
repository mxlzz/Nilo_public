"""Regresiones 0.5.9.3.28: evidencia del diseño, capacidades y bucle de energía."""
import random
import unittest

from action_results import evidence_before, result_from_execution
from brain import context_for, compact_context
from inventions import register_design, record_design_test
from laboratory import measured_physics
from nilo import initial_state
from research_cycle import prediction_metric_warning
from world import execute_action
from action_results import _physical_evidence


def design(person,name,purpose,components):
    ok,_=register_design(person,{'op':'design','name':name,'purpose':purpose,
        'principle':'Transferir esfuerzo mecánico a los materiales disponibles.',
        'components':[{'name':n,'material':m,'function':'sostener','connection':'fija'}
                      for n,m in components]},'Día 1')
    assert ok
    return person['designs'][-1]


class PhysicalMetrics(unittest.TestCase):
    def test_real_action_result_uses_static_capacity_not_retention_percent(self):
        s=initial_state()
        p,w=s['person'],s['world']
        p['inventory']['madera']=8
        step={'op':'craft','name':'cuenco','form':'recipiente','materials':['madera','madera']}
        duration,facts,success,_=execute_action(w,p,step,random.Random(2))
        self.assertTrue(success,facts)
        tool=p['items'][-1]
        # La medición física real exige prueba nueva del objeto y agua disponible.
        tool['tests'].append({'method':'llenar','target':'agua','success':True})
        prior={'unmodeled':0,'knowledge':set(),'tests':{tool['id']:0},
               'capability_evidence':None,'capability_diagnostic':None}
        from action_results import _physical_evidence
        info=_physical_evidence({'op':'use','item':tool['id'],'method':'llenar'},
                                p,prior,True)
        self.assertEqual(set(info['metrics']),{'capacidad_util_agua'})
        self.assertGreater(info['metrics']['capacidad_util_agua'],0)
        self.assertNotIn('retencion_pct',info['metrics'])
        self.assertNotIn('agua_retenida',info['metrics'])
        self.assertIn('pérdida temporal',info['precision'])
        self.assertEqual(prediction_metric_warning({'op':'use','method':'llenar',
             'prediction':{'metric':'capacidad_util_agua','operator':'gte','threshold':0.1}}),'')
        self.assertIn('no mide',prediction_metric_warning({'op':'use','method':'llenar',
             'prediction':{'metric':'retencion_pct','operator':'gte','threshold':70}}))


class DesignEvidence(unittest.TestCase):
    def setUp(self):
        s=initial_state()
        self.p,self.w=s['person'],s['world']
        self.p['inventory']['madera']=8
        self.p['inventory']['mineral oscuro']=5

    def test_created_tool_binds_design_but_not_verified_on_fabrication(self):
        d=design(self.p,'punta mineral','excavar roca',
                 [('cabeza','mineral oscuro'),('mango','madera')])
        step={'op':'craft','name':'punta mineral','form':'punta',
              'materials':['mineral oscuro','madera'],'design_id':d['id']}
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(1))
        self.assertTrue(success)
        tool=self.p['items'][-1]
        self.assertEqual(tool['design_id'],d['id'])
        self.assertEqual(step['_built_object_id'],tool['id'])
        record_design_test(self.p,step,True,facts,'Día 1',measurement_id='med-c',
                           measurement={'success':True},world=self.w)
        self.assertEqual(d['status'],'prototipo construido')
        self.assertFalse(d['verified'])
        self.assertEqual(d['tests'][0]['object_id'],tool['id'])
        self.assertEqual(d['linked_object_ids'],[tool['id']])
        # La asociación por nombre ambiguo o el éxito narrado sin prueba no verifica.
        fake={'op':'use','item':tool['id'],'method':'excavar'}
        record_design_test(self.p,fake,True,['Funcionó'], 'Día 1',
                           measurement_id='med-f',measurement={'success':True},world=self.w)
        self.assertFalse(d['verified'])
        self.assertEqual(len(d['tests']),1)
        tool['tests'].append({'method':'excavar','success':True,'revision':1})
        record_design_test(self.p,fake,True,['Excavé roca'],'Día 1',
                           measurement_id='med-u',measurement={'success':True},world=self.w)
        self.assertTrue(d['verified'])
        self.assertEqual(d['status'],'funcion comprobada')
        self.assertEqual(d['verified_functions'][0]['name'],'excavar')
        self.assertEqual(d['tests'][-1]['measurement_id'],'med-u')

    def test_shelter_rest_links_to_design_only_with_positive_energy_under_cover(self):
        d=design(self.p,'refugio básico','abrigo y seguridad',
                 [(f'poste {i}','madera') for i in range(1,5)])
        step={'op':'build','name':'refugio básico','purpose':'abrigo',
              'materials':['madera']*4,'design_id':d['id']}
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(2))
        self.assertTrue(success,facts)
        shelter=self.w['structures'][-1]
        self.assertEqual(shelter['design_id'],d['id'])
        self.assertNotIn('shelter_condition',shelter)
        record_design_test(self.p,step,success,facts,'Día 1',measurement_id='med-b',
                           measurement={'success':True},world=self.w)
        self.assertEqual(d['status'],'prototipo construido')
        sample={'id':'med-r','success':True,'op':'rest','condition':'refugio',
                'start':{'position':list(self.p['pos']),'sheltered':True},
                'needs_delta':{'energia':3.0}}
        # Descansar sobre la celda inicial h no verifica que la obra fabricada
        # aporte cubierta. Ni un registro inventado puede conceder eficacia.
        evidence=record_design_test(self.p,{'op':'rest'},True,
                                    ['Recuperé 3 puntos'],'Día 1',
                                    measurement_id='med-r',measurement=sample,
                                    world=self.w)
        self.assertIsNone(evidence)
        self.assertEqual(d['status'],'prototipo construido')
        self.assertFalse(d['verified'])
        self.assertFalse(d.get('verified_functions'))
        self.assertEqual(len(d['tests']),1)

    def test_no_spontaneous_claim_from_unlinked_legacy_object(self):
        d=design(self.p,'herramienta','excavar roca',[('cabeza','piedra')])
        self.p['items'].append({'id':'old-tool','name':'herramienta','form':'punta',
            'tests':[{'method':'excavar','success':True,'revision':1}], 'revision':1})
        out=record_design_test(self.p,{'op':'use','item':'old-tool','method':'excavar',
                    'design_id':d['id']},True,['Éxito'],'Día 1',
                    measurement_id='med-old',measurement={'success':True},world=self.w)
        self.assertIsNone(out)
        self.assertFalse(d['verified'])


class CognitiveContext(unittest.TestCase):
    def test_compact_model_context_retains_infeasible_rest_and_failed_closure(self):
        s=initial_state()
        w,p=s['world'],s['person']
        from survival import ensure_needs
        ensure_needs(p)['energia']=100
        p['project']={'id':'project-rest','title':'Comparar recuperación en refugio',
                      'status':'activo','reason':'Estudiar descanso'}
        p['last_closure_rejection']={'project_id':'project-rest','reason':'Sin ensayo válido'}
        context=context_for(w,p,[],'Día 1')
        eligibility=context['condiciones_de_ensayo_descanso']
        # Desde .34.1 la saturación exacta pertenece al motor; Nilo
        # puede experimentar sin conocer por introspección la cifra.
        self.assertNotIn('energia_actual',eligibility)
        self.assertNotIn('energia_actual_apta_para_ensayo',eligibility)
        self.assertIn('ensayos no saturados',eligibility['aclaracion'])
        compact=compact_context(context,4300)
        self.assertEqual(compact['ultimo_cierre_rechazado']['reason'],'Sin ensayo válido')
        self.assertNotIn('energia_actual_apta_para_ensayo',
                         compact['condiciones_de_ensayo_descanso'])
        self.assertEqual(compact['necesidades']['energia'],'con mucha energía')


if __name__=='__main__':unittest.main()
