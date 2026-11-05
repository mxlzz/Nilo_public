"""0.5.9.3.34.1 · Percepción corporal sin acceso introspectivo a barras."""
import copy
import json
import unittest

from survival import needs_summary, perceived_needs
from brain import build_deliberation_request, context_for
from nilo import initial_state


def created():
    return initial_state(world_seed=7321)['person']


class QualitativeBody(unittest.TestCase):
    def test_boundaries_and_no_mutation(self):
        cases=[
            (100,'completamente saciado','bien hidratado','con mucha energía'),
            (90,'completamente saciado','bien hidratado','con mucha energía'),
            (89.99,'sin hambre','sin sed','descansado'),
            (60,'sin hambre','sin sed','descansado'),
            (59.99,'algo de hambre','algo de sed','algo cansado'),
            (30,'algo de hambre','algo de sed','algo cansado'),
            (29.99,'mucha hambre','mucha sed','muy cansado'),
            (15,'mucha hambre','mucha sed','muy cansado'),
            (14.99,'hambre extrema','sed extrema','muy cansado'),
            (11.99,'hambre extrema','sed extrema','agotamiento severo'),
            (5,'hambre extrema','sed extrema','inconsciente')]
        for value,hunger,thirst,energy in cases:
            with self.subTest(value=value):
                p=created()
                p['needs']={'hidratacion':value,'nutricion':value,'energia':value,
                            'abrigo':80,'seguridad':70}
                before=copy.deepcopy(p['needs'])
                felt=perceived_needs(p)
                self.assertEqual(felt['alimentacion'],hunger)
                self.assertEqual(felt['hidratacion'],thirst)
                self.assertEqual(felt['energia'],energy)
                self.assertEqual(before,p['needs'])
                self.assertFalse(any(isinstance(v,(int,float)) for v in felt.values()))
                self.assertNotIn('valores',felt)

    def test_ui_observer_keeps_exact_reserves(self):
        p=created()
        p['needs']={'hidratacion':83.14,'nutricion':57.35,
                    'energia':67.99,'abrigo':80,'seguridad':68}
        self.assertEqual(needs_summary(p)['valores']['hidratacion'],83.14)
        self.assertEqual(perceived_needs(p)['hidratacion'],'sin sed')

    def test_real_context_only_sensations_not_reserves(self):
        state=initial_state(world_seed=7321)
        p=state['person']
        p['measurements']=[{'id':'med-123','op':'rest','duration_minutes':30,
                            'condition':'intemperie',
                            'start':{'needs':{'energia':41}},
                            'end':{'needs':{'energia':44}},
                            'energy_per_hour':6.6,'rest_comparable':True,
                            'physical':None,'verified_facts':[]}]
        context=context_for(state['world'],p,[],'Día 1 08:00')
        body=context['necesidades']
        self.assertEqual(body['hidratacion'],'sin sed')
        self.assertEqual(body['alimentacion'],'sin hambre')
        self.assertNotIn('valores',body)
        self.assertFalse(any(isinstance(v,(int,float)) for v in body.values()))
        sample=context['mediciones_reales_recientes'][0]
        self.assertNotIn('energia_inicial',sample)
        self.assertNotIn('energia_final',sample)
        self.assertNotIn('energia_por_hora',sample)
        for cfg in ({'PROVIDER':'groq','MODEL':'openai/gpt-oss-20b','GROQ_API_KEY':'dummy'},
                    {'PROVIDER':'gemini','MODEL':'gemini-3.1-flash-lite','GEMINI_API_KEY':'dummy'}):
            _,payload,_=build_deliberation_request(cfg,context)
            sent=(json.loads(payload['messages'][1]['content']) if cfg['PROVIDER']=='groq'
                  else json.loads(payload['contents'][0]['parts'][0]['text'].split('SITUACIÓN REAL: ',1)[1]))
            self.assertEqual(sent['necesidades'],body)

    def test_legacy_numeric_context_is_sanitized_at_provider_boundary(self):
        raw={'momento':'ahora','posición':[2,3,0],
             'necesidades':needs_summary({'needs':{'energia':90,'hidratacion':94,
                 'nutricion':82,'abrigo':77,'seguridad':67}}),
             'regla':'El motor verifica toda la física.'}
        old=copy.deepcopy(raw)
        for cfg in ({'PROVIDER':'groq','MODEL':'openai/gpt-oss-20b','GROQ_API_KEY':'dummy'},
                    {'PROVIDER':'gemini','MODEL':'gemini-3.1-flash-lite','GEMINI_API_KEY':'dummy'}):
            _,payload,_=build_deliberation_request(cfg,raw)
            sent=(json.loads(payload['messages'][1]['content']) if cfg['PROVIDER']=='groq'
                  else json.loads(payload['contents'][0]['parts'][0]['text'].split('SITUACIÓN REAL: ',1)[1]))
            self.assertEqual(sent['necesidades']['alimentacion'],'sin hambre')
            self.assertNotIn('valores',sent['necesidades'])
            self.assertNotIn('criticas',sent['necesidades'])
        self.assertEqual(raw,old)

    def test_measured_energy_history_available_when_nilo_investigates(self):
        s=initial_state(world_seed=7321)
        p=s['person']
        p['project']={'id':'p-1','title':'Comparar recuperación de energía en descanso',
                      'reason':'Quiero comprobar el efecto del refugio'}
        p['measurements']=[{'id':'med-test','op':'rest','duration_minutes':30,
                            'condition':'intemperie',
                            'start':{'needs':{'energia':41}},
                            'end':{'needs':{'energia':44}},
                            'energy_per_hour':6.6,'rest_comparable':True,
                            'physical':None,'verified_facts':[]}]
        context=context_for(s['world'],p,[],'Día 1 08:00')
        self.assertEqual(context['mediciones_reales_recientes'][0]['energia_inicial'],41)
        self.assertEqual(context['mediciones_reales_recientes'][0]['energia_final'],44)
        self.assertNotIn('energia_actual',context['condiciones_de_ensayo_descanso'])
        self.assertNotIn('valores',context['necesidades'])


    def test_bodily_numbers_only_for_a_chosen_study(self):
        s=initial_state(world_seed=7321)
        p=s['person']
        p['measurements']=[
            {'id':'med-agua','op':'drink','duration_minutes':5,'condition':'orilla',
             'start':{'needs':{'energia':82,'hidratacion':42,'nutricion':71}},
             'end':{'needs':{'energia':82,'hidratacion':66,'nutricion':71}},
             'verified_facts':[],'physical':None},
            {'id':'med-comida','op':'eat','duration_minutes':5,'condition':'suelo',
             'start':{'needs':{'energia':82,'hidratacion':66,'nutricion':41}},
             'end':{'needs':{'energia':82,'hidratacion':66,'nutricion':75}},
             'verified_facts':[],'physical':None}]
        p['project']={'id':'p-0','title':'Conseguir agua para el viaje','reason':'Planificar'}
        current=context_for(s['world'],p,[],'Día 1')
        for row in current['mediciones_reales_recientes']:
            self.assertNotIn('hidratacion_inicial',row)
            self.assertNotIn('nutricion_inicial',row)
        p['project']={'id':'p-1','title':'Investigar hidratación al beber',
                      'reason':'Quiero comparar las variaciones medidas'}
        watered=context_for(s['world'],p,[],'Día 1')
        self.assertEqual(watered['mediciones_reales_recientes'][0]['hidratacion_inicial'],42)
        self.assertEqual(watered['mediciones_reales_recientes'][0]['hidratacion_final'],66)
        self.assertNotIn('nutricion_inicial',watered['mediciones_reales_recientes'][1])
        p['project']={'id':'p-2','title':'Estudiar nutrición al comer','reason':'Medir recuperación'}
        fed=context_for(s['world'],p,[],'Día 1')
        self.assertEqual(fed['mediciones_reales_recientes'][1]['nutricion_inicial'],41)
        self.assertEqual(fed['mediciones_reales_recientes'][1]['nutricion_final'],75)
        self.assertNotIn('hidratacion_inicial',fed['mediciones_reales_recientes'][0])
        self.assertNotIn('valores',fed['necesidades'])


if __name__=='__main__':
    unittest.main()
