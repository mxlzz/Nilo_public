"""Regresión vertical 0.5.9.3.25: fabricación, módulos, contenido y diagnóstico."""
import random
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from action_contracts import classify, before
from capabilities import Capability, manifest, resolve
from construction import apply_intervention
from environments import get_environment
from island_planning import IslandPlanner
from nilo import Simulation, initial_state
from survival import update_needs, ensure_needs
from world import execute_action, make_item, set_tile


class ModulePhysicalTests(unittest.TestCase):
    def setUp(self):
        s=initial_state(7321)
        self.w=s['world']
        self.p=s['person']
        self.p['pos']=[15,10,0]
        self.p['items']=[]
        self.p['inventory']={'madera':5,'piedra':6,'alimento':2}
        self.rng=random.Random(7321)
        ensure_needs(self.p)['hidratacion']=50
        self.p['materials']['blando']={'resistencia':1,'dureza':1,'peso':1,
                                       'density':.2,'permeability':.3}
        self.p['inventory']['blando']=2

    def vessel(self,id,qty=0,material='agua',materials=None,geometry=None):
        mats=materials or ['piedra','piedra','piedra']
        obj={'id':id,'name':id,'form':'recipiente','materials':mats,
             'geometry':geometry or {'shape':'hueco','size':3},
             'durability':100,'revision':1,'resistance':5,'hardness':5}
        if qty:
            obj['contents']={'material':material,'quantity':qty}
        else:
            obj['contents']={}
        self.p['items'].append(obj)
        return obj

    def interact(self,method,**args):
        step={'op':'interact','method':method,**args}
        result=get_environment('isla_v1').perform_result(self.w,self.p,step,self.rng)
        return result

    def test_duplicate_fabrication_creates_two_unique_objects(self):
        step={'op':'craft','materials':['blando'],'name':'vaso blando',
              'form':'recipiente','geometry':{'shape':'hueco','size':1}}
        first=execute_action(self.w,self.p,step,self.rng)
        second=execute_action(self.w,self.p,step,self.rng)
        self.assertTrue(first[2],first[1])
        self.assertTrue(second[2],second[1])
        self.assertEqual(len(self.p['items']),2)
        self.assertNotEqual(self.p['items'][0]['id'],self.p['items'][1]['id'])
        self.assertEqual(self.p['inventory']['blando'],0)
        self.assertLess(self.p['items'][0]['resistance'],3)
        self.p['items'][0]['durability']=31
        self.assertNotEqual(self.p['items'][0]['durability'],self.p['items'][1]['durability'])

    def test_planner_does_not_remove_equivalent_manufacture(self):
        step={'op':'craft','materials':['piedra'],'name':'cuenco',
              'form':'recipiente'}
        execute_action(self.w,self.p,step,self.rng)
        planner=IslandPlanner(get_environment('isla_v1'),self.w,self.p,lambda x:None,lambda *a:None)
        self.assertEqual(planner.improve_plan([step,step]),[step,step])

    def test_transfer_conserves_exact_amount_and_provenance(self):
        a=self.vessel('A',.8)
        b=self.vessel('B',.2)
        result=self.interact('transferir',source='A',destination='B',quantity=.4)
        self.assertEqual(result.status,'verified_success')
        self.assertEqual(a['contents']['quantity'],.4)
        self.assertEqual(b['contents']['quantity'],.6)
        self.assertEqual(result.physical['kind'],'capability')
        self.assertEqual(result.physical['conditions']['version'],'1.0.0')
        self.assertEqual(result.physical['conditions']['before'],{'source':.8,'destination':.2})
        self.assertEqual(result.physical['conditions']['after'],{'source':.4,'destination':.6})
        contract=classify(self.w,self.p,{'op':'interact','method':'transferir'},
                          before(self.w,self.p,{}),result)
        self.assertEqual(contract['status'],'conforme')
        self.assertEqual(self.w['capability_versions']['contenidos'],'1.0.0')
        self.assertNotIn('_last_capability_evidence',self.p)

    def test_capacity_and_invalid_quantities_are_atomic(self):
        a=self.vessel('A',.8)
        b=self.vessel('B',.4)
        before=(deepcopy(a['contents']),deepcopy(b['contents']))
        for qty in (99,0,-1,.001,float('nan'),float('inf'),'abc',True):
            result=self.interact('transferir',source='A',destination='B',quantity=qty)
            self.assertEqual(result.status,'precondition_failed',qty)
            self.assertEqual((a['contents'],b['contents']),before,qty)
        self.assertIsNone(resolve('metodo_inexistente'))
        # Una operación sin módulo no es una prueba física negativa.
        self.assertEqual(self.interact('metodo_inexistente').status,'no_evaluable')

    def test_water_recharge_partial_and_no_duplicate_water(self):
        set_tile(self.w,16,10,0,'~')
        a=self.vessel('A',.3)
        result=self.interact('rellenar',destination='A',quantity=.2)
        self.assertEqual(result.status,'verified_success',result.facts)
        self.assertEqual(a['contents']['quantity'],.5)
        self.assertEqual(self.interact('rellenar',destination='A',quantity=50).status,'precondition_failed')
        self.assertEqual(a['contents']['quantity'],.5)

    def test_voluntary_drink_consumes_once_with_no_automatic_rule(self):
        a=self.vessel('A',.36)
        self.assertEqual(self.interact('beber',source='A').status,'verified_success')
        self.assertEqual(a['contents']['quantity'],.18)
        self.assertEqual(self.p['needs']['hidratacion'],77)
        update_needs(self.p,self.w,60)
        self.assertEqual(a['contents']['quantity'],.18)
        step={'op':'drink','item':'A'}
        result=get_environment('isla_v1').perform_result(self.w,self.p,step,self.rng)
        self.assertEqual(result.status,'verified_success')
        self.assertEqual(a['contents'],{})
        self.assertGreater(self.p['needs']['hidratacion'],77)

    def test_store_and_withdraw_solids_without_double_inventory(self):
        a=self.vessel('A')
        self.p['inventory']['madera']=3
        result=self.interact('guardar',destination='A',material='madera',quantity=1)
        self.assertEqual(result.status,'verified_success',result.facts)
        self.assertEqual(self.p['inventory']['madera'],2)
        self.assertEqual(a['contents']['quantity'],1)
        self.assertEqual(self.interact('retirar',source='A',quantity=1).status,'verified_success')
        self.assertEqual(self.p['inventory']['madera'],3)
        self.assertEqual(a['contents'],{})

    def test_discharge_is_explicit_and_removes_only_source_reserve(self):
        a=self.vessel('A',.8)
        result=self.interact('descargar',source='A',quantity=.3)
        self.assertEqual(result.status,'verified_success')
        self.assertEqual(a['contents']['quantity'],.5)
        self.assertEqual(result.physical['conditions']['destination_id'],'ambiente_sin_reserva')

    def test_dismantle_or_shrink_full_vessel_fails_without_loss(self):
        a=self.vessel('A',.9,materials=['piedra','piedra','piedra'],
                      geometry={'shape':'hueco','size':3})
        # El inventario y el objeto deben permanecer sin cambios ante el rechazo.
        initial_inv=deepcopy(self.p['inventory'])
        result=apply_intervention(self.w,self.p,{'op':'dismantle','item':'A'})
        self.assertFalse(result[2])
        self.assertIn('contenido',result[1][0])
        self.assertIn(a,self.p['items'])
        self.assertEqual(self.p['inventory'],initial_inv)
        # Primero vaciar, luego desmontar físicamente.
        self.assertEqual(self.interact('descargar',source='A').status,'verified_success')
        self.assertTrue(apply_intervention(self.w,self.p,
                        {'op':'dismantle','item':'A'})[2])

    def test_shrinking_a_full_vessel_requires_removing_its_contents_first(self):
        a=self.vessel('A',2.5,materials=['piedra','piedra','piedra'],
                      geometry={'shape':'hueco','size':5})
        from vessels import capacity
        self.assertGreaterEqual(capacity(a,self.p),2.5)  # Estado inicial posible
        from construction import ensure_object
        ensure_object(a)
        old_inv=deepcopy(self.p['inventory'])
        component=a['components'][0]['id']
        old_rev=a['revision']
        result=apply_intervention(self.w,self.p,{'op':'modify','item':'A',
                                                 'mode':'remove','component':component})
        self.assertFalse(result[2])
        self.assertEqual(a['contents']['quantity'],2.5)
        self.assertEqual(a['revision'],old_rev)
        self.assertEqual(self.p['inventory'],old_inv)

    def test_version_mismatch_or_disabled_module_rejects_without_effect(self):
        self.vessel('A',.5)
        self.vessel('B',0)
        self.w['capability_versions']={'contenidos':'0.9.0'}
        self.assertFalse(execute_action(self.w,self.p,
                  {'op':'interact','method':'transferir','source':'A','destination':'B','quantity':.2},self.rng)[2])
        self.assertEqual(self.p['items'][0]['contents']['quantity'],.5)
        self.assertEqual(self.w['capability_versions']['contenidos'],'0.9.0')
        self.w['capability_versions']={'contenidos':'1.0.0'}
        self.w['disabled_capabilities']=['contenidos']
        self.assertFalse(execute_action(self.w,self.p,
                  {'op':'interact','method':'transferir','source':'A','destination':'B','quantity':.2},self.rng)[2])
        self.assertEqual(self.p['items'][0]['contents']['quantity'],.5)

    def test_missing_sample_is_typed_precondition_during_execution(self):
        step={'op':'experiment','target':'material inexistente','method':'condensar'}
        result=get_environment('isla_v1').perform_result(self.w,self.p,step,self.rng)
        self.assertEqual(result.status,'precondition_failed')
        self.assertFalse(self.p.get('unmodeled_attempts'))
        self.assertEqual(classify(self.w,self.p,step,before(self.w,self.p,step),result)['status'],
                         'uso_incorrecto')

    def test_no_model_is_separate_from_precondition_and_real_failure(self):
        a=self.vessel('A',.5)
        step={'op':'use','item':'A','method':'purificar','target':'agua'}
        result=get_environment('isla_v1').perform_result(self.w,self.p,step,self.rng)
        self.assertEqual(result.status,'no_evaluable')
        self.assertTrue(self.p['unmodeled_attempts'])
        entry=self.p['unmodeled_attempts'][-1]
        self.assertEqual(entry['result'],'no_evaluable')
        self.assertEqual(entry['requested_method'],'purificar')
        self.assertTrue(entry['missing_effect_or_metric'])
        contract=classify(self.w,self.p,step,before(self.w,self.p,step),result)
        self.assertEqual(contract['status'],'limitacion')
        self.assertEqual(contract['evidence_id'],entry['id'])
        # Un recipiente inexistente NO acredita incapacidad física.
        missing=get_environment('isla_v1').perform_result(self.w,self.p,
                    {'op':'interact','method':'beber','source':'desconocido'},self.rng)
        self.assertEqual(missing.status,'precondition_failed')
        self.assertEqual(classify(self.w,self.p,{'op':'interact','method':'beber'},
                                 before(self.w,self.p,{}),missing)['status'],'uso_incorrecto')


class AppIntegrationTests(unittest.TestCase):
    def test_capability_manifest_only_enables_approved_methods(self):
        entries=manifest()
        self.assertEqual([c['id'] for c in entries],['contenidos','cargas_estructurales'])
        self.assertIn('transferir',entries[0]['methods'])
        self.assertIn('probar_carga',entries[1]['methods'])

    def test_transfer_survives_real_tick_and_sqlite_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'mundo.sqlite3'
            sim=Simulation(db_path=db)
            try:
                sim.think=lambda: self.fail('No corresponde llamar al LLM.')
                sim.s['planning']=True
                p=sim.s['person']
                p['items']=[
                    {'id':'jarra-a','name':'Jarra A','form':'recipiente',
                     'materials':['piedra']*3,
                     'geometry':{'shape':'hueco','size':3},
                     'durability':100,'revision':1,
                     'contents':{'material':'agua','quantity':.8}},
                    {'id':'jarra-b','name':'Jarra B','form':'recipiente',
                     'materials':['piedra']*3,
                     'geometry':{'shape':'hueco','size':3},
                     'durability':100,'revision':1,'contents':{}},
                ]
                p['plan']=[{'op':'interact','method':'transferir',
                            'source':'jarra-a','destination':'jarra-b','quantity':.4}]
                sim._tick_slice(0)
                self.assertEqual(p['pending']['step']['op'],'interact')
                # _tick_slice acepta segundos reales (máximo 20 por llamada).
                # A velocidad x60 equivalen a 20 minutos simulados.
                sim.s['planning']=False
                sim.s['speed']=60
                sim.think=lambda:None  # sin llamadas LLM durante la prueba
                sim._tick_slice(20)
                self.assertIsNone(p['pending'])
                self.assertEqual(p['items'][0]['contents']['quantity'],.4)
                self.assertEqual(p['items'][1]['contents']['quantity'],.4)
                self.assertEqual(sim.s['world']['capability_versions']['contenidos'],'1.0.0')
                sim.write()
            finally:
                sim.conn.close()
            resumed=Simulation(db_path=db)
            try:
                p2=resumed.s['person']
                self.assertEqual(p2['items'][0]['contents']['quantity'],.4)
                self.assertEqual(p2['items'][1]['contents']['quantity'],.4)
                self.assertEqual(resumed.s['world']['capability_versions']['contenidos'],'1.0.0')
                self.assertTrue(resumed.public_state()['installed_capabilities'])
            finally:
                resumed.conn.close()

    def test_simulation_initializes_and_exposes_capability_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            sim=Simulation(db_path=Path(folder)/'capacidad.sqlite3')
            try:
                state=sim.public_state()
                self.assertIn('installed_capabilities',state)
                self.assertIn('active_intervention',state)
            finally:
                sim.conn.close()


if __name__=='__main__':
    unittest.main()
