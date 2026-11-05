"""Regresiones .29: diseños documentados y prototipos materiales."""
import random
import unittest

from inventions import register_design, record_design_test
from nilo import initial_state
from world import execute_action


def design(person, name, parts):
    ok, message = register_design(person, {
        'op':'design', 'name':name, 'purpose':'ensayar una función',
        'principle':'Comprobar piezas materiales',
        'components':[{'name':label, 'material':mat, 'connection':'fija'}
                      for label,mat in parts]
    }, 'Día 1')
    assert ok, message
    return person['designs'][-1]


class DesignMaterialConsistency(unittest.TestCase):
    def setUp(self):
        state=initial_state()
        self.p,self.w=state['person'],state['world']
        self.p['inventory']['madera']=12
        self.p['inventory']['mineral oscuro']=4

    def test_refuge_mismatch_does_not_consume_materials(self):
        d=design(self.p,'refugio',[('poste','madera')])
        original=dict(self.p['inventory'])
        step={'op':'build','name':'refugio','purpose':'abrigo',
              'materials':['madera']*4,'design_id':d['id']}
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(1))
        self.assertFalse(success)
        self.assertIn('madera ×1',facts[0])
        self.assertIn('madera ×4',facts[0])
        self.assertEqual(self.p['inventory'],original)
        self.assertFalse(self.w['structures'])
        self.assertNotIn('_built_object_id',step)

    def test_refuge_revised_plan_has_matching_version_without_verifying_function(self):
        d=design(self.p,'refugio',[('poste','madera')])
        ok,_=register_design(self.p,{'op':'design','design_id':d['id'],
            'name':'refugio','purpose':'proteger del clima',
            'principle':'Usar cuatro soportes',
            'components':[{'name':f'poste {n}', 'material':'madera'} for n in range(4)]},'Día 1')
        self.assertTrue(ok)
        step={'op':'build','name':'refugio','purpose':'abrigo',
              'materials':['madera']*4,'design_id':d['id']}
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(1))
        self.assertTrue(success,facts)
        self.assertEqual(self.w['structures'][0]['design_version'],2)
        self.assertEqual(step['_built_object_id'],self.w['structures'][0]['id'])
        record_design_test(self.p,step,True,facts,'Día 1',measurement_id='med-b',
                           measurement={'success':True},world=self.w)
        self.assertEqual(d['status'],'prototipo construido')
        self.assertFalse(d['verified'])

    def test_tool_mismatch_cannot_claim_documented_parts(self):
        d=design(self.p,'punta',[('cabeza','mineral oscuro'),('mango','madera')])
        original=dict(self.p['inventory'])
        step={'op':'craft','name':'punta','form':'punta',
              'materials':['madera','madera'],'design_id':d['id']}
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(2))
        self.assertFalse(success)
        self.assertEqual(original,self.p['inventory'])
        self.assertFalse(self.p['items'])
        step.pop('design_id')
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(2))
        self.assertTrue(success,facts)
        self.assertNotIn('design_id',self.p['items'][-1])

    def test_assembly_creates_real_bidirectional_design_link(self):
        d=design(self.p,'mecanismo',[('eje','madera'),('rueda','madera')])
        step={'op':'assemble','name':'mecanismo','purpose':'movimiento',
              'parts':[{'name':'eje','material':'madera','shape':'eje'},
                       {'name':'rueda','material':'madera','shape':'rueda'}],
              'joints':[{'a':0,'b':1,'type':'articulada'}],
              'design_id':d['id']}
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(2))
        self.assertTrue(success,facts)
        item=self.p['items'][-1]
        self.assertEqual(item['design_id'],d['id'])
        self.assertEqual(item['design_version'],1)
        self.assertEqual(step['_built_object_id'],item['id'])
        record_design_test(self.p,step,True,facts,'Día 1',measurement_id='med-a',
                           measurement={'success':True},world=self.w)
        self.assertEqual(d['status'],'prototipo construido')
        self.assertEqual(d['linked_object_ids'],[item['id']])
        self.assertFalse(d['verified'])

    def test_assembly_wrong_components_is_atomic(self):
        d=design(self.p,'mecanismo',[('pieza','mineral oscuro')])
        step={'op':'assemble','name':'mecanismo',
              'parts':[{'name':'eje','material':'madera','shape':'eje'},
                       {'name':'rueda','material':'madera','shape':'rueda'}],
              'joints':[{'a':0,'b':1,'type':'articulada'}],
              'design_id':d['id']}
        before=dict(self.p['inventory'])
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(2))
        self.assertFalse(success)
        self.assertEqual(self.p['inventory'],before)
        self.assertFalse(self.p['items'])

    def test_unknown_design_id_is_rejected(self):
        step={'op':'craft','name':'herramienta','materials':['madera'],
              'design_id':'inv-inexistente'}
        before=dict(self.p['inventory'])
        _,facts,success,_=execute_action(self.w,self.p,step,random.Random(2))
        self.assertFalse(success)
        self.assertIn('No existe una ficha',facts[0])
        self.assertEqual(self.p['inventory'],before)


if __name__=='__main__':
    unittest.main()
