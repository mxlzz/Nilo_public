"""0.5.9.3.33 · Presupuesto integral y diagnósticos de fallback LLM."""
import copy
import json
import threading
import unittest
from unittest.mock import patch

from action_contracts import SUPPORTED_OPERATIONS
from brain import build_deliberation_request
from prompt_budget import SHORT_OPERATIONS, bounded_context, brief_actions
from providers import ProviderFailure, candidate_configs, route


def long_context():
    return {
        'momento':'Día 3 · 12:00','posición':[7,19,0],
        'necesidades':{'hidratacion':60,'energia':85,'nutricion':74},
        'proyecto_actual':{'id':'pro-17','title':'Comprobar contención de agua',
                           'state':'Ensayo pendiente','progress':65,
                           'verified_results':[]},
        'ultimo_cierre_rechazado':{'estado_verificacion':'criterio_no_instrumentado',
                                  'reason':'No hay medida de potabilidad.'},
        'proyectos_reanudables':[{'id':'pro-4','titulo':'Piedra','motivo_pausa':'Faltaba muestra'}],
        'regla':'El motor verifica toda la física.',
        'memorias_relevantes':[{'id':'exp-'+str(i),
                                'accion_id':'act-'+str(i),
                                'hecho':'Material sometido a carga mecánica '+('comprobada '*100)}
                               for i in range(100)],
        'mediciones_reales_recientes':[{'id':'med-'+str(i),'op':'use',
                                         'resultado':'Se probó la pieza '+('largo '*150)}
                                        for i in range(70)],
        'diagnosticos_operativos_recientes':[{'id':'diag-'+str(i),'reason':'fallo '*200}
                                             for i in range(45)],
        'herramientas_que_llevo':[{'id':'obj-'+str(i),'name':'hacha '*80}
                                  for i in range(20)],
        'investigaciones_activas':[{'id':i,'question':'Lorem '*100} for i in range(100)],
        'conclusiones_verificadas':[{'id':'c-'+str(i),'text':'Concluí '+('dato '*100)}
                                    for i in range(40)]
    }


class PromptBudget(unittest.TestCase):
    def setUp(self):
        self.context=long_context()
        self.original=copy.deepcopy(self.context)

    def test_all_operations_represented(self):
        self.assertEqual(set(SHORT_OPERATIONS),set(SUPPORTED_OPERATIONS))
        for op in SUPPORTED_OPERATIONS:
            self.assertIn('- '+op+':',brief_actions())

    def test_groq_total_payload_and_core_evidence_survive(self):
        cfg={'PROVIDER':'groq','GROQ_API_KEY':'fake-test-only','MODEL':'openai/gpt-oss-20b'}
        url,payload,headers=build_deliberation_request(cfg,self.context)
        self.assertIn('api.groq.com',url)
        self.assertLessEqual(len(json.dumps(payload,ensure_ascii=False).encode('utf-8')),14500)
        self.assertLess(len(payload['messages'][0]['content']),9000)
        sent=json.loads(payload['messages'][1]['content'])
        self.assertEqual(sent['proyecto_actual']['id'],'pro-17')
        self.assertEqual(sent['proyectos_reanudables'][0]['id'],'pro-4')
        self.assertEqual(sent['ultimo_cierre_rechazado']['estado_verificacion'],
                         'criterio_no_instrumentado')
        self.assertEqual(self.context,self.original)
        self.assertIn('json_object',str(payload['response_format']))

    def test_gemini_reduces_context_without_rewriting_world(self):
        cfg={'PROVIDER':'gemini','MODEL':'gemini-3.5-flash-lite',
             'GEMINI_API_KEY':'fake-test-only'}
        _,payload,_=build_deliberation_request(cfg,self.context)
        content=payload['contents'][0]['parts'][0]['text']
        sent=json.loads(content.split('SITUACIÓN REAL: ',1)[1])
        self.assertEqual(sent['proyecto_actual']['id'],'pro-17')
        self.assertEqual(sent['ultimo_cierre_rechazado']['estado_verificacion'],
                         'criterio_no_instrumentado')
        self.assertLessEqual(len(json.dumps(sent,ensure_ascii=False,separators=(',',':')).encode()),9100)
        self.assertEqual(self.context,self.original)

    def test_budget_compression_never_slices_evidence_ids(self):
        result=bounded_context(self.context,3500)
        self.assertEqual(result['proyecto_actual']['id'],'pro-17')
        self.assertTrue(all(isinstance(m.get('id'),str) for m in
                            result.get('memorias_relevantes',[])))
        self.assertLessEqual(len(json.dumps(result,ensure_ascii=False,
                                separators=(',',':')).encode()),3500)

    def test_groq_new_profile_does_not_reuse_413_from_prior_build(self):
        cfg={'PROVIDER':'gemini','MODEL':'gemini-3.1-flash-lite',
             'GEMINI_API_KEY':'gemini-test','GROQ_API_KEY':'groq-test',
             'BACKUP_PROVIDER':'groq'}
        configs=candidate_configs(cfg)
        groq=[v for name,v in configs if name=='groq']
        self.assertEqual(len(groq),1)
        self.assertIn('compact-v1',groq[0]['_health_key'])
        self.assertNotEqual(groq[0]['_health_key'],'groq')

    def test_invalid_decision_reason_without_echoing_model_text(self):
        cfg={'PROVIDER':'groq','GROQ_API_KEY':'groq-test'}
        state={}
        def malformed(_):
            raise ValueError('El modelo no propuso acciones utilizables.')
        with self.assertRaises(Exception) as raised:
            route(cfg,state,threading.RLock(),malformed,sleep=lambda x:None)
        self.assertIn('sin acciones utilizables',str(raised.exception))
        self.assertNotIn('El modelo no propuso',str(raised.exception))
        self.assertEqual(list(state['provider_health'].values())[0]['last_status'],0)


if __name__=='__main__':
    unittest.main()
