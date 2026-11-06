"""0.5.9.3.34 · Sensaciones, delegaciones finitas y memoria contextual."""
import copy
import json
import unittest
from unittest.mock import patch

from survival import needs_summary, perceived_needs, update_needs
from habits import (choose_wait_action, record_wait_selection,
                    set_wait_preferences)
from brain import compact_context, build_deliberation_request
from prompt_budget import bounded_context, context_stats


def person(**values):
    p={'needs':{'hidratacion':94.,'nutricion':82.,'energia':90.,
                'abrigo':80.,'seguridad':68.},'inventory':{'alimento':2},
       'pos':[8,9,0],'clock_minutes':0}
    p.update(values)
    return p


class Sensations(unittest.TestCase):
    def test_sed_hambre_interval_boundaries(self):
        samples=[(100,'ninguna'),(90,'ninguna'),(89.99,'normal_sin_urgencia'),
                 (82,'normal_sin_urgencia'),(60,'normal_sin_urgencia'),
                 (59.99,'progresiva'),(30,'progresiva'),(29.99,'intensa'),
                 (15,'intensa'),(14.99,'critica'),(0,'critica')]
        for reserve,level in samples:
            with self.subTest(reserve=reserve):
                p=person()
                p['needs']['hidratacion']=reserve
                p['needs']['nutricion']=reserve
                before=copy.deepcopy(p['needs'])
                summary=needs_summary(p)
                self.assertEqual(summary['sensaciones']['sed'],level)
                self.assertEqual(summary['sensaciones']['hambre'],level)
                self.assertEqual(p['needs'],before)
        self.assertEqual(needs_summary(person())['sensaciones']['sed'],'ninguna')
        self.assertEqual(needs_summary(person())['sensaciones']['hambre'],'normal_sin_urgencia')

    def test_cansancio_respects_fatigue_strain_and_unconscious(self):
        expected=[(100,'ninguna'),(90,'ninguna'),(89.9,'normal_sin_urgencia'),
                  (60,'normal_sin_urgencia'),(59.9,'progresiva'),
                  (30,'progresiva'),(29.9,'intensa'),(12,'intensa'),
                  (11.99,'tension_corporal'),(5.01,'tension_corporal'),
                  (5,'inconsciente')]
        for value,level in expected:
            with self.subTest(value=value):
                p=person()
                p['needs']['energia']=value
                self.assertEqual(needs_summary(p)['sensaciones']['cansancio'],level)
        self.assertEqual(needs_summary(person(unconscious=True))['sensaciones']['cansancio'],'inconsciente')

    def test_no_auto_consume_and_physical_needs_unchanged(self):
        p=person()
        p['needs']['hidratacion']=44
        p['needs']['nutricion']=44
        original_inventory=dict(p['inventory'])
        update_needs(p,{},60,active=True)
        self.assertEqual(p['inventory'],original_inventory)
        self.assertLess(p['needs']['hidratacion'],44)
        self.assertLess(p['needs']['nutricion'],44)

    def test_critical_state_is_not_intense(self):
        p=person()
        p['needs'].update(hidratacion=24,nutricion=14,energia=11)
        s=needs_summary(p)
        self.assertEqual(s['sensaciones']['sed'],'intensa')
        self.assertEqual(s['sensaciones']['hambre'],'critica')
        self.assertIn('nutricion',s['criticas'])
        self.assertNotIn('hidratacion',s['criticas'])
        self.assertNotIn('energia',s['criticas'])


class Delegations(unittest.TestCase):
    def test_rest_once_by_default_and_explicit_three_times(self):
        p=person()
        set_wait_preferences(p,[{'op':'rest','minutes':30}], 'día 1')
        choice=choose_wait_action({},p)
        self.assertIsNotNone(choice)
        a=dict(choice[0])
        record_wait_selection(p,a)
        self.assertNotIn('_wait_preference_index',a)
        self.assertIsNone(choose_wait_action({},p))
        set_wait_preferences(p,[{'op':'rest','minutes':30,'veces':3}], 'día 2')
        for _ in range(3):
            step,reason=choose_wait_action({},p)
            record_wait_selection(p,step)
        self.assertIsNone(choose_wait_action({},p))

    def test_rest_threshold_only_when_nilo_requests_it(self):
        p=person()
        set_wait_preferences(p,[{'op':'rest','minutes':40,'veces':3,
                                 'menor_que':60}],'día 1')
        self.assertIsNone(choose_wait_action({},p))
        p['needs']['energia']=55
        self.assertIsNotNone(choose_wait_action({},p))

    def test_delegated_drink_and_eat_are_finite_not_automatic(self):
        p=person()
        # Etapa 17: la función ejecutable pertenece a autonomy.habits;
        # el módulo raíz habits solo conserva un import compatible.
        with patch('nilo_runtime.autonomy.habits._near_water',return_value=True):
            self.assertIsNone(choose_wait_action({},p)) # no delegation
            set_wait_preferences(p,[{'op':'drink'}], 'día 1')
            step,_=choose_wait_action({},p)
            record_wait_selection(p,step)
            self.assertIsNone(choose_wait_action({},p))
        set_wait_preferences(p,[{'op':'eat'}], 'día 2')
        step,_=choose_wait_action({},p)
        record_wait_selection(p,step)
        self.assertIsNone(choose_wait_action({},p))
        # La elección consciente del LLM sigue pudiendo volver a delegar.
        set_wait_preferences(p,[{'op':'eat'}], 'día 3')
        self.assertIsNotNone(choose_wait_action({},p))


class ContextSelection(unittest.TestCase):
    def test_relevance_rank_keeps_best_not_last(self):
        ctx={'momento':'día 3','posición':[3,6,0],
             'necesidades':{'valores':{},'sensaciones':{}},
             'memorias_relevantes':[{'id':'mejor','hecho':'a'},
                                    {'id':'segunda','hecho':'b'},
                                    {'id':'tercera','hecho':'c'},
                                    {'id':'cuarta','hecho':'d'},
                                    {'id':'quinta','hecho':'e'},
                                    {'id':'sexta','hecho':'f'}],
             'regla':'La física la determina el motor.'}
        compact=compact_context(ctx,char_budget=18000)
        self.assertEqual([x['id'] for x in compact['memorias_relevantes']],
                         ['mejor','segunda','tercera','cuarta','quinta'])
        smaller=bounded_context(compact,byte_budget=460)
        self.assertEqual(smaller.get('memorias_relevantes',[{}])[0].get('id'),'mejor')

    def test_inventory_and_bodily_sensations_survive_groq(self):
        ctx={'momento':'Día 4','posición':[3,6,0],
             'necesidades':perceived_needs(person()),
             'inventario_materiales':{'madera':3,'piedra':2},
             'proyecto_actual':{'id':'pr-42','title':'Investigar la piedra','reason':'',
                               'state':'observando','progress':10},
             'proyectos_reanudables':[],
             'preferencias_en_espera':[{'op':'rest','veces':1}],
             'regla':'Hechos verificados por el motor.',
             'memorias_relevantes':[{'id':'best','hecho':'Un ensayo anterior permitió comprobar un filo.'},
                                    {'id':'other','hecho':'Una observación diferente.'}],
             'herramientas_que_llevo':[{'id':'obj-1','nombre':'hacha'}],
             'investigaciones_activas':[{'id':1,'question':'investigar'}]}
        before=copy.deepcopy(ctx)
        for cfg in ({'PROVIDER':'groq','MODEL':'openai/gpt-oss-20b','GROQ_API_KEY':'dummy'},
                    {'PROVIDER':'gemini','MODEL':'gemini-3.1-flash-lite','GEMINI_API_KEY':'dummy'}):
            _,payload,_=build_deliberation_request(cfg,ctx)
            if cfg['PROVIDER']=='groq':
                sent=json.loads(payload['messages'][1]['content'])
                self.assertLessEqual(len(json.dumps(payload,ensure_ascii=False).encode()),14500)
            else:
                sent=json.loads(payload['contents'][0]['parts'][0]['text'].split('SITUACIÓN REAL: ',1)[1])
            self.assertEqual(sent['necesidades']['hidratacion'],'bien hidratado')
            self.assertNotIn('valores',sent['necesidades'])
            self.assertEqual(sent['inventario_materiales']['madera'],3)
            self.assertEqual(sent['preferencias_en_espera'][0]['op'],'rest')
            self.assertEqual(sent['memorias_relevantes'][0]['id'],'best')
            self.assertEqual(sent['proyecto_actual']['id'],'pr-42')
            stats=context_stats(ctx,sent,cfg['PROVIDER'],payload)
            self.assertGreater(stats['solicitud_bytes'],stats['contexto_enviado_bytes'])
            self.assertIn('bytes_por_seccion',stats)
            self.assertNotIn('secret',str(stats))
        self.assertEqual(ctx,before)

    def test_water_sources_deemphasized_without_disallowing_future_planning(self):
        ctx={'momento':'ahora','necesidades':perceived_needs(person()),
             'proyecto_actual':{'id':'p','title':'Investigar herramientas'},
             'orillas_agua_conocidas_alcanzables':[{'orilla':i} for i in range(5)]}
        selected=compact_context(ctx,char_budget=18000)
        self.assertEqual(len(selected['orillas_agua_conocidas_alcanzables']),1)
        ctx['proyecto_actual']['title']='Conseguir agua para la exploración'
        self.assertEqual(len(compact_context(ctx,char_budget=18000)['orillas_agua_conocidas_alcanzables']),3)


if __name__=='__main__':unittest.main()
