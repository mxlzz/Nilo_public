"""0.5.9.3.3: contratos operativos, diagnóstico comprobable, sin manual redundante."""
import random
import unittest
from action_contracts import ACTION_GUIDE, SUPPORTED_OPERATIONS, instructions, before, classify, spec_for
from action_results import ActionResult
from diagnostics import record_contract_issue
from brain import normalize_decision, ACTIONS
from world import new_world,execute_action

def reply(op,ok=True,unmodeled=False):
    return ActionResult.from_legacy({'op':op},['resultado motor'],ok,False,no_evaluable=unmodeled)

class Contracts(unittest.TestCase):
    def setUp(self):
        self.world=new_world()
        self.person={'pos':[15,10,0],'inventory':{'piedra':2},
                     'items':[],'materials':{},'knowledge':{},'clock_minutes':0}
        self.world['structures'].append({'id':'obra-1','name':'Mi refugio','pos':[15,10,0],
            'status':'prototipo','materials':['madera'],'category':'habitaculo'})
    
    def test_single_source_and_no_manual_action(self):
        self.assertEqual(set(ACTION_GUIDE),SUPPORTED_OPERATIONS)
        self.assertEqual(ACTIONS,instructions())
        self.assertNotIn('manual',SUPPORTED_OPERATIONS)
        self.assertEqual(len(ACTION_GUIDE),26)  # 24 primitivas + interact + wait
        self.assertIn('interact',SUPPORTED_OPERATIONS)
        self.assertIsNotNone(spec_for('inspect')['contrato'])
        with self.assertRaises(ValueError):
            normalize_decision({'cuaderno':'consultar','plan':[{'op':'manual','target':'inspect'}]})
    
    def test_inspect_contract_success(self):
        step={'op':'inspect','target':'obra-1'}
        initial=before(self.world,self.person,step)
        duration,facts,success,_=execute_action(self.world,self.person,step,random.Random(1))
        self.assertTrue(success)
        diagnostic=classify(self.world,self.person,step,initial,reply('inspect',success))
        self.assertEqual(diagnostic['status'],'conforme')
    
    def test_inspect_contract_detects_contradiction_with_traceable_evidence(self):
        step={'op':'inspect','target':'obra-1'}
        initial=before(self.world,self.person,step)
        mismatch=classify(self.world,self.person,step,initial,reply('inspect',False))
        self.assertEqual(mismatch['status'],'posible_error')
        p={'proposals':[]}
        outcome={'id':'act-abc','op':'inspect','success':False,
                 'facts':['No identifico obra-1'],'when':'Día 2'}
        issue=record_contract_issue(p,mismatch,outcome,'Día 2','isla_v1')
        self.assertIsNotNone(issue)
        self.assertEqual(issue['evidence'][0]['id'],'act-abc')
        self.assertEqual(issue['status'],'pendiente')
        self.assertEqual(issue['origin'],'motor')
        self.assertIsNone(record_contract_issue(p,mismatch,outcome,'Día 2','isla_v1'))
    
    def test_expected_inspect_rejection_is_not_bug(self):
        step={'op':'inspect','target':'obra-desconocida'}
        diagnostic=classify(self.world,self.person,step,before(self.world,self.person,step),
                             reply('inspect',False))
        self.assertEqual(diagnostic['status'],'uso_incorrecto')
    
    def test_gather_success_without_material_is_bug(self):
        step={'op':'gather','target':'piedra'}
        diagnostic=classify(self.world,self.person,step,before(self.world,self.person,step),
                             reply('gather',True))
        self.assertEqual(diagnostic['status'],'posible_error')
        self.assertEqual(diagnostic['code'],'recoleccion_inconsistente')

    def test_gather_failure_no_bug(self):
        step={'op':'gather','target':'piedra'}
        diagnostic=classify(self.world,self.person,step,before(self.world,self.person,step),
                             reply('gather',False))
        self.assertNotEqual(diagnostic['status'],'posible_error')
    
    def test_unmodeled_is_a_limitation_not_a_bug(self):
        step={'op':'use','item':'tool-imaginario','method':'evaporar'}
        diag=classify(self.world,self.person,step,before(self.world,self.person,step),
                      reply('use',False,unmodeled=True))
        self.assertEqual(diag['status'],'limitacion')

    def test_physical_failure_is_not_bug(self):
        self.person['items']=[{'id':'tool-1','name':'Punta','form':'punta',
                             'materials':['piedra'],'durability':50}]
        step={'op':'use','item':'tool-1','method':'golpear','target':'piedra'}
        diag=classify(self.world,self.person,step,before(self.world,self.person,step),
                      reply('use',False))
        self.assertEqual(diag['status'],'no_verificado')

    def test_build_and_modify_postconditions(self):
        step={'op':'build','name':'estructura','materials':['piedra']}
        earlier=before(self.world,self.person,step)
        diag=classify(self.world,self.person,step,earlier,reply('build',True))
        self.assertEqual(diag['status'],'posible_error')
        self.world['structures'].append({'id':'obra-2','name':'estructura','pos':[15,10,0]})
        self.assertEqual(classify(self.world,self.person,step,earlier,reply('build',True))['status'],'conforme')
        modify={'op':'modify','item':'obra-1','mode':'add','materials':['piedra']}
        previous=before(self.world,self.person,modify)
        self.assertEqual(classify(self.world,self.person,modify,previous,reply('modify',True))['status'],'posible_error')
        self.world['structures'][0]['revision']=2
        self.assertEqual(classify(self.world,self.person,modify,previous,reply('modify',True))['status'],'conforme')

    def test_documentation_does_not_require_simulated_action(self):
        _,facts,success,_=execute_action(self.world,self.person,
                                         {'op':'manual','target':'inspect'},random.Random(1))
        self.assertFalse(success)
        self.assertIn('No conozco la operación física',facts[0])

if __name__=='__main__':unittest.main()
