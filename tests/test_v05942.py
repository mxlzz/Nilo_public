"""0.5.9.4.2 — proyección perceptiva y continuidad cognitiva para todos los LLM."""
from __future__ import annotations

import copy
import json
import unittest

from brain import build_deliberation_request, context_for, compact_context
from cognitive_projection import project_context
from nilo import initial_state
from auditar_contexto_llm import extract_sent_context, PROVIDERS


class CognitiveProjection(unittest.TestCase):
    def setUp(self):
        state=initial_state(world_seed=7321)
        self.w,self.p=state['world'],state['person']
        self.p['project']={
            'id':'p-actual','title':'Investigar refugio de madera',
            'reason':'Comparar versiones y condiciones','status':'activo',
            'progress':95, 'no_progress_steps':12, 'state':'Sin pruebas suficientes',
            'verified_results':[{'measurement_id':'med-obra','action':'modify',
                                 'result':'Agregué una pieza real'}],
        }
        self.p['projects']=[{
            'id':'p-anterior','title':'Investigar refugio de madera',
            'reason':'Inspeccionar cubierta y materiales',
            'state':'No hay prueba climática','status':'pausado',
            'closure_reason':'Las inspecciones no evaluaron el clima',
            'no_progress_steps':9}]
        self.p['research']=[{
            'id':'r-ant','question':'Cómo comprobar refugio de madera',
            'hypothesis':'La cubierta permite abrigo', 'state':'pausada',
            'evidence':[],
            'project_retirement':{'project_id':'p-anterior',
                                  'status':'pausado',
                                  'conclusion_not_verified':True}}]
        self.p['items']=[{
            'id':'herr-test','name':'Punta','form':'punta',
            'revision':1,'components':[{'id':'pieza','material':'madera',
                                       'condition':0.8}],
            'durability':89,'possible_uses':{'excavar':2.8},
            'tests':[], 'geometry':{'shape':'macizo'},
        }]
        self.w['structures']=[{
            'id':'obra-test','name':'Refugio','category':'habitaculo',
            'pos':[17,19,0],'revision':1,'materials':['madera']*4,
            'components':[{'id':'pieza-obra','material':'madera','condition':0.9}],
            'shelter_condition':'cubierto_parcialmente',
            'space':{'representation':'2.5d-schematic','width_m':2},
            'status':'función pendiente de comprobar'
        }]

    def test_sanitizes_internal_scores_but_preserves_measurements(self):
        self.p['measurements']=[{
            'id':'med-rest','op':'rest','duration_minutes':45,
            'condition':'refugio','start':{'needs':{'energia':30}},
            'end':{'needs':{'energia':36}},'energy_per_hour':8,
            'rest_comparable':True,'verified_facts':['Descansé 45 minutos.'],
            'physical':None}]
        raw=context_for(self.w,self.p,[],'Día 2')
        before=copy.deepcopy(raw)
        v=project_context(raw)
        self.assertEqual(before,raw)
        self.assertNotIn('progress',v['proyecto_actual'])
        self.assertNotIn('no_progress_steps',v['proyecto_actual'])
        self.assertEqual(v['proyecto_actual']['resultados_fisicos_registrados'][0]['measurement_id'],'med-obra')
        self.assertNotIn('predisposiciones',v)
        self.assertNotIn('territorio_descubierto_pct',v)
        self.assertEqual(v['inventario_materiales'],raw['inventario_materiales'])
        self.assertEqual(v['mediciones_reales_recientes'][0]['id'],'med-rest')
        # El proyecto elegido no estudia fisiología: sus números no se revelan.
        self.assertNotIn('energia_inicial',v['mediciones_reales_recientes'][0])

    def test_shelter_and_tool_values_are_not_equated_with_proven_function(self):
        c=project_context(context_for(self.w,self.p,[],'Día 2'))
        tools=c['herramientas_que_llevo']
        self.assertEqual(len(tools),1)
        self.assertNotIn('durabilidad',tools[0])
        self.assertNotIn('usos_por_verificar',tools[0])
        self.assertEqual(tools[0]['desgaste_observable'],'desgaste leve')
        self.assertIn('excavar',tools[0]['usos_propuestos_sin_ensayo'])
        self.assertEqual(tools[0]['piezas_observables'][0]['desgaste_observable'],'desgaste leve')
        construction=c['construcciones_fijas'][0]
        self.assertNotIn('condicion_abrigo',construction)
        self.assertIn('no evaluada',construction['proteccion_climatica'])
        self.assertEqual(construction['version'],1)
        self.assertEqual(construction['posicion'],[17,19,0])

    def test_all_providers_use_same_semantic_filter_at_payload_boundary(self):
        raw=context_for(self.w,self.p,[],'Día 2')
        for name,cfg in PROVIDERS.items():
            with self.subTest(name=name):
                original=copy.deepcopy(raw)
                _,payload,_=build_deliberation_request(cfg,raw)
                actual=extract_sent_context(name,payload)
                self.assertEqual(raw,original)
                self.assertNotIn('predisposiciones',actual)
                self.assertNotIn('territorio_descubierto_pct',actual)
                self.assertNotIn('progress',actual.get('proyecto_actual') or {})
                self.assertEqual(actual['proyecto_actual']['id'],'p-actual')
                self.assertNotIn('valores',actual['necesidades'])
                self.assertFalse(any(isinstance(n,(int,float))
                                     for n in actual['necesidades'].values()))

    def test_pause_reason_survives_actual_groq_payload_even_when_crowded(self):
        raw=context_for(self.w,self.p,[],'Día 2')
        raw['resultados_de_acciones']=[{
            'id':f'act-{i}','resultado':['Inspección sin evidencia nueva']*3,
            'operacion':'inspect'} for i in range(100)]
        raw['herramientas_que_llevo']*=12
        for name in ('gemini','groq','openai_compatible'):
            with self.subTest(provider=name):
                _,payload,_=build_deliberation_request(PROVIDERS[name],raw)
                data=extract_sent_context(name,payload)
                self.assertEqual(data['antecedente_relevante']['id'],'p-anterior')
                self.assertEqual(data['antecedente_relevante']['motivo_registrado'],
                                 'Las inspecciones no evaluaron el clima')
                self.assertIn('proyecto_actual',data)
                self.assertNotIn('progress',data['proyecto_actual'])

    def test_nonproject_context_has_no_forced_purpose(self):
        s=initial_state()
        c=project_context(context_for(s['world'],s['person'],[],'Día 1'))
        self.assertIsNone(c.get('proyecto_actual'))
        self.assertNotIn('antecedente_relevante',c)


if __name__=='__main__':
    unittest.main()
