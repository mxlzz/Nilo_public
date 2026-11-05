"""Pruebas de geometría orientativa y obras modificables. Sin acceso a LLM."""
import json, random, sqlite3, tempfile, unittest
from pathlib import Path
import nilo
from world import execute_action, classify_structure
from brain import context_for, normalize_decision
from construction import ensure_object

class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.state=nilo.initial_state()
        self.w=self.state['world'];self.p=self.state['person']
        self.p['inventory'].update({'madera':12,'fibra':8,'piedra':8,'arcilla':4})
        self.rng=random.Random(7)

    def act(self, op, **kwargs):return execute_action(self.w,self.p,{'op':op,**kwargs},self.rng)

    def build(self):
        result=self.act('build',name='Refugio de prueba',purpose='Dormir y guardar provisiones',
                        materials=['madera']*4+['fibra']*2,
                        layout={'width_m':3,'length_m':4,'entrance':'S','zones':['dormir','guardar']})
        self.assertTrue(result[2],result)
        obj=self.w['structures'][-1];return obj

    def test_build_has_real_id_and_ascii_plan_independent_of_map(self):
        obj=self.build()
        self.assertEqual(obj['revision'],1)
        self.assertEqual(len(obj['components']),6)
        self.assertLessEqual(obj['space']['area_m2'],len(obj['materials'])*1.7)
        diagram=obj['revisions'][0]['schematic']
        self.assertIn('PLANTA',diagram)
        self.assertIn('DORMIR',diagram)
        self.assertIn('GUARDAR',diagram)
        self.assertIn('no tabiques comprobados',diagram)
        self.assertEqual(self.w['levels']['0'][10][15],'h')

    def test_add_changes_same_building_and_keeps_revision(self):
        obj=self.build();original_id=obj['id'];before=obj['revisions'][0]['schematic'];n=self.p['inventory']['madera']
        result=self.act('modify',item=obj['id'],mode='add',materials=['madera'],layout={
            'width_m':2.6,'length_m':4.3,'entrance':'O','zones':['dormir','almacenar']})
        self.assertTrue(result[2],result)
        self.assertEqual(self.p['inventory']['madera'],n-1)
        self.assertEqual(len(self.w['structures']),1)
        self.assertEqual(obj['id'],original_id)
        self.assertEqual(obj['revision'],2)
        self.assertEqual(len(obj['components']),7)
        self.assertEqual(obj['revisions'][0]['schematic'],before)
        self.assertNotEqual(obj['revisions'][1]['schematic'],before)
        self.assertIn('Modificada',obj['status'])

    def test_cannot_make_duplicate_refuge_same_place(self):
        obj=self.build();n=len(self.w['structures']);inv=dict(self.p['inventory'])
        result=self.act('build',name='Refugio ampliado',purpose='Dormir',materials=['madera','fibra'])
        self.assertFalse(result[2]);self.assertEqual(len(self.w['structures']),n)
        self.assertEqual(self.p['inventory'],inv)
        self.assertIn(obj['id'],result[1][0])

    def test_requires_component_to_remove_and_materials_to_replace(self):
        obj=self.build();original=json.dumps(obj,sort_keys=True)
        fail=self.act('modify',item=obj['id'],mode='replace',component='inexistente',materials=['piedra'])
        self.assertFalse(fail[2]);self.assertEqual(json.dumps(obj,sort_keys=True),original)
        component=obj['components'][0]['id']
        ok=self.act('modify',item=obj['id'],mode='replace',component=component,materials=['piedra'])
        self.assertTrue(ok[2]);self.assertNotIn(component,[v['id'] for v in obj['components']])
        self.assertIn('piedra',obj['materials'])
        self.assertEqual(len(obj['components']),6)
        self.assertLessEqual(self.p['inventory']['madera'],12-4+1)

    def test_dismantle_preserves_history_without_material_creation(self):
        obj=self.build();before=dict(self.p['inventory']);original_id=obj['id']
        ok=self.act('dismantle',item=original_id,all=True)
        self.assertTrue(ok[2]);self.assertFalse(self.w['structures'])
        history=self.w['retired_structures'][0]
        self.assertEqual(history['id'],original_id)
        self.assertEqual(history['status'],'Desmontada')
        self.assertEqual(len(history['revisions']),2)
        self.assertLessEqual(self.p['inventory']['madera'],before['madera']+4)
        self.assertLessEqual(self.p['inventory']['fibra'],before['fibra']+2)

    def test_removing_sole_piece_retires_object_and_no_negative_inventory(self):
        item=self.act('craft',name='Pico',purpose='Golpear',materials=['madera'])
        self.assertTrue(item[2])
        tool=self.p['items'][0];item_id=tool['id'];part=tool['components'][0]['id']
        removed=self.act('modify',item=item_id,mode='remove',component=part)
        self.assertTrue(removed[2]);self.assertFalse(self.p['items'])
        self.assertEqual(self.p['retired_items'][0]['status'],'Desmontada')
        self.assertEqual(len(tool['materials']),0)

    def test_repair_needs_wear_and_consumes_real_material(self):
        self.act('craft',name='Mazo',purpose='Golpear muestras',materials=['madera','piedra'])
        tool=self.p['items'][0];cid=tool['components'][0]['id']
        unchanged=json.dumps(tool,sort_keys=True)
        fail=self.act('modify',item=tool['id'],mode='repair',component=cid,materials=['madera'])
        self.assertFalse(fail[2]);self.assertEqual(json.dumps(tool,sort_keys=True),unchanged)
        tool['components'][0]['condition']=.5;tool['durability']=50
        count=self.p['inventory']['madera']
        fixed=self.act('modify',item=tool['id'],mode='repair',component=cid,materials=['madera'])
        self.assertTrue(fixed[2]);self.assertEqual(self.p['inventory']['madera'],count-1)
        self.assertGreater(tool['components'][0]['condition'],.5)

    def test_object_further_than_one_tile_cannot_be_modified(self):
        obj=self.build();self.p['pos']=[25,17,0]
        result=self.act('modify',item=obj['id'],mode='add',materials=['piedra'])
        self.assertFalse(result[2]);self.assertEqual(obj['revision'],1)

    def test_assembly_replacement_preserves_connection_and_addition_must_be_connected(self):
        from mechanics import create_assembly,test_assembly
        self.p['inventory']['madera']=6
        ok,_=create_assembly(self.p,{'name':'Mecanismo de rueda','parts':[
            {'name':'rueda','material':'madera','shape':'rueda'},
            {'name':'eje','material':'madera','shape':'eje'}],
            'joints':[{'a':0,'b':1,'type':'articulada'}]})
        self.assertTrue(ok)
        item=self.p['items'][-1]
        self.assertTrue(test_assembly(self.p,item,'transmitir_movimiento',{'input_energy':10})[0])
        cid=item['components'][0]['id']
        ok=self.act('modify',item=item['id'],mode='replace',component=cid,materials=['piedra'])
        self.assertTrue(ok[2])
        self.assertTrue(test_assembly(self.p,item,'transmitir_movimiento',{'input_energy':10})[0])
        ok=self.act('modify',item=item['id'],mode='add',materials=['madera'])
        self.assertTrue(ok[2])
        self.assertFalse(test_assembly(self.p,item,'transmitir_movimiento',{'input_energy':10})[0])

    def test_existing_old_structure_migrates_without_fictional_rooms(self):
        old={'id':'legacy','name':'Cabaña','purpose':'dormir','pos':[15,10,0],
             'category':'habitaculo','materials':['madera','fibra'],'resistance':4}
        ensure_object(old,structure=True)
        self.assertEqual(old['revision'],1)
        self.assertIn('PLANTA',old['revisions'][0]['schematic'])
        self.assertNotIn('DORMIR',old['revisions'][0]['schematic'])
        self.assertEqual(len(old['components']),2)

    def test_brain_knows_actions_and_component_ids(self):
        obj=self.build()
        context=context_for(self.w,self.p,[],'Día 1')
        self.assertEqual(context['construcciones_fijas'][0]['id'],obj['id'])
        self.assertTrue(context['construcciones_fijas'][0]['piezas'][0]['id'].startswith('cmp-'))
        dec=normalize_decision({'cuaderno':'Mejorar el refugio','plan':[{'op':'modify','item':obj['id'],'mode':'add','materials':['madera']} ]})
        self.assertEqual(dec['plan'][0]['op'],'modify')

class PersistenceTests(unittest.TestCase):
    def test_migrates_and_archives_revisions_in_sqlite(self):
        with tempfile.TemporaryDirectory() as td:
            old=nilo.DB;nilo.DB=Path(td)/'sim.sqlite3'
            try:
                sim=nilo.Simulation();p=sim.s['person'];w=sim.s['world'];p['inventory'].update({'madera':8,'fibra':3})
                _,_,ok,_=execute_action(w,p,{'op':'build','name':'Refugio','materials':['madera']*4+['fibra'],
                    'purpose':'Cubrirme','layout':{'zones':['descansar']}},random.Random(1))
                self.assertTrue(ok)
                obj=w['structures'][-1];oid=obj['id']
                _,_,ok,_=execute_action(w,p,{'op':'modify','item':oid,'mode':'add','materials':['madera']},random.Random(1))
                self.assertTrue(ok)
                sim.write();sim.conn.close()
                sim2=nilo.Simulation()
                self.assertEqual(sim2.s['world']['structures'][-1]['id'],oid)
                self.assertEqual(len(sim2.s['world']['structures'][-1]['revisions']),2)
                rows=sim2.conn.execute('SELECT COUNT(*) FROM history_revisions WHERE category="construction" AND item_id=?',(oid,)).fetchone()[0]
                self.assertGreaterEqual(rows,1)
                sim2.conn.close()
            finally:nilo.DB=old

if __name__=='__main__':unittest.main()
