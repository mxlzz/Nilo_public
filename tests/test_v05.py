import unittest,sys,os,tempfile,shutil,json,sqlite3,random
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent/'nilo'
sys.path.insert(0,str(HERE))
from nilo import Simulation, initial_state
from survival import update_needs,ensure_needs
from inventions import register_design, record_design_test, submit_proposal, review_proposal, ensure_records
from mechanics import create_assembly,test_assembly
from world import new_world,execute_action

class V05Test(unittest.TestCase):
    def person(self):
        return initial_state()['person']
    def test_survival(self):
        p=self.person();ensure_needs(p)
        a=p['needs']['hidratacion'];update_needs(p,{},60,False,False,True)
        self.assertLess(p['needs']['hidratacion'],a)
        p['needs']['hidratacion']=48;p['inventory']['alimento']=2;p['needs']['nutricion']=44
        update_needs(p,{},60,False,False,False)
        self.assertLess(p['needs']['nutricion'],44)
        self.assertEqual(p['inventory']['alimento'],2)
        # Un replay anterior conserva la ingesta automática histórica.
        update_needs(p,{},60,False,False,False,legacy_autocare=True)
        self.assertGreater(p['needs']['nutricion'],44)
        self.assertEqual(p['inventory']['alimento'],1)
    def test_design_versions_and_verified_evidence(self):
        p=self.person();ensure_records(p)
        step={'name':'Polea','purpose':'elevar una carga','principle':'rotación sobre eje',
              'expected_test':'transmitir_movimiento', 'components':[{'name':'disco','material':'madera','function':'girar'}]}
        yes,msg=register_design(p,step,'Día 1');self.assertTrue(yes)
        d=p['designs'][0];self.assertFalse(d['verified'])
        record_design_test(p,{'op':'craft','design_id':d['id']},True,['hecha'],'Día 2')
        self.assertFalse(d['verified'])
        record_design_test(p,{'op':'use','method':'transmitir_movimiento','design_id':d['id']},True,['transmite movimiento'],'Día 2')
        # Un éxito narrado sin objeto y ensayo físico asociados no verifica la función.
        self.assertFalse(d['verified'])
        self.assertEqual(d['tests'],[])
        step['design_id']=d['id'];yes,msg=register_design(p,step,'Día 3')
        self.assertTrue(yes);self.assertEqual(len(d['versions']),2);self.assertFalse(d['verified'])
    def test_proposal_review_does_not_implement_physics(self):
        p=self.person();x={'phenomenon':'presion de gases','rationale':'quiero evaluar vapor',
             'experiment':'comprobar movimiento de una pieza','missing_capability':'temperatura y presion'}
        success,_=submit_proposal(p,x,'Día 1',('flotacion',));self.assertTrue(success)
        success,_=submit_proposal(p,x,'Día 2',('flotacion',));self.assertFalse(success)
        proposal=p['proposals'][0];review_proposal(p,proposal['id'],'aprobar','Incorporar principio general','Día 2')
        self.assertEqual(proposal['status'],'aceptada_pendiente_de_motor')
        self.assertFalse(proposal['engine_ready'])
    def test_assemble_mechanical_test(self):
        p=self.person();p['inventory']['madera']=3
        step={'name':'Rueda y eje','parts':[{'name':'rueda','material':'madera','shape':'rueda'},
                      {'name':'eje','material':'madera','shape':'eje'}],
                      'joints':[{'a':0,'b':1,'type':'articulada'}]}
        yes,_=create_assembly(p,step);self.assertTrue(yes)
        self.assertEqual(p['inventory']['madera'],1)
        yes,text=test_assembly(p,p['items'][0],'transmitir_movimiento',{'input_energy':3})
        self.assertTrue(yes);self.assertIn('salida',text)
        yes,_=test_assembly(p,p['items'][0],'generar_presion',{})
        self.assertFalse(yes)
    def test_food_real_deposit(self):
        s=initial_state();w=s['world'];p=s['person'];p['pos']=[15,10,0]
        # exact terrain set, deterministic finite 3 per tile
        from world import set_tile
        set_tile(w,15,10,0,'T')
        for i in range(3):
            _,_,ok,_=execute_action(w,p,{'op':'forage'},random.Random(1));self.assertTrue(ok)
        # More spots in range might exist; ensure own source exhausted.
        self.assertEqual(w['forage_deposits']['15,10,0'],0)
        self.assertGreaterEqual(p['inventory']['alimento'],3)
    def test_migrate_old_snapshot(self):
        import nilo
        tmp=tempfile.TemporaryDirectory();old=nilo.DB;nilo.DB=Path(tmp.name)/'test.sqlite3'
        conn=sqlite3.connect(nilo.DB)
        s=initial_state();s['version']=4;s['person'].pop('needs',None)
        s['journal']=[{'id':'note','text':'Observé un cuenco','when':'Día 3'}]
        conn.execute('create table snapshot(id INTEGER PRIMARY KEY,payload TEXT NOT NULL)')
        conn.execute('insert into snapshot values (?,?)',(1,json.dumps(s)))
        conn.commit();conn.close()
        try:
            sim=Simulation();self.assertEqual(sim.s['journal'][0]['text'],'Observé un cuenco')
            self.assertIn('needs',sim.s['person']);self.assertIn('designs',sim.s['person'])
            self.assertIn('proposals',sim.public_state())
            sim.s['paused']=True;sim.write();sim.conn.close()
            sim2=Simulation();self.assertEqual(sim2.s['version'],5);sim2.conn.close()
        finally:
            nilo.DB=old;tmp.cleanup()
    def test_llm_context_and_plan(self):
        from brain import context_for,normalize_decision
        s=initial_state();p=s['person'];w=s['world']
        ctx=context_for(w,p,[],'Día 1')
        self.assertIn('necesidades',ctx);self.assertIn('inventos_documentados',ctx)
        dec=normalize_decision({'plan':[{'op':'design'}], 'cuaderno':'Quiero experimentar'})
        self.assertEqual(dec['plan'][0]['op'],'design')
if __name__=='__main__':unittest.main()

class Integration(unittest.TestCase):
    def test_sim_execution_and_proposal_review(self):
        import nilo
        with tempfile.TemporaryDirectory() as td:
            old=nilo.DB;nilo.DB=Path(td)/'state.sqlite3'
            try:
                sim=nilo.Simulation()
                p=sim.s['person']
                p['plan']=[{'op':'design','name':'Plano de bomba','purpose':'transportar agua',
                    'principle':'fuerza transmite movimiento por articulacion',
                    'components':[{'name':'rueda','material':'madera','function':'girar'}],
                    'expected_test':'transmitir_movimiento'},
                    {'op':'propose','phenomenon':'presion de fluidos','missing_capability':'flujo y valvulas',
                    'rationale':'quiero probar una bomba','experiment':'medir caudal'}]
                sim.s['paused']=False;sim.s['speed']=60
                sim.s['planning']=True  # impide consultas externas al terminar el plan
                for _ in range(7):sim.tick(20)
                self.assertEqual(len(p['designs']),1)
                self.assertEqual(len(p['proposals']),1)
                result=sim.review_rule(p['proposals'][0]['id'],'aprobar','Registrar para ampliar el motor')
                self.assertFalse(result['engine_enabled'])
                self.assertEqual(p['proposals'][0]['status'],'aceptada_pendiente_de_motor')
                sim.conn.close()
            finally:nilo.DB=old
    def test_future_assembly_plan_validation(self):
        import nilo
        with tempfile.TemporaryDirectory() as td:
            old=nilo.DB;nilo.DB=Path(td)/'state.sqlite3'
            try:
                sim=nilo.Simulation();p=sim.s['person'];p['inventory']['madera']=3
                plan=[{'op':'assemble','name':'Eje rueda','parts':[
                        {'name':'eje','material':'madera','shape':'eje'},
                        {'name':'rueda','material':'madera','shape':'rueda'}],
                        'joints':[{'a':0,'b':1,'type':'articulada'}]},
                      {'op':'use','item':'Eje rueda','method':'transmitir_movimiento','input_energy':5}]
                self.assertEqual(len(sim.validate_plan(plan)),2)
                sim.conn.close()
            finally:nilo.DB=old
