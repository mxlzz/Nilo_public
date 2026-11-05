"""Regresiones críticas detectadas en las auditorías externas."""
import unittest, sqlite3, random, tempfile, json
from pathlib import Path
import nilo
from world import new_world, resolve_go, reveal, tile_key, execute_action
from physics import properties
from brain import compact_context
from archive import History
from validar_escenarios import run

class MapPrivacy(unittest.TestCase):
    def test_unknown_destinations_do_not_reveal_geology(self):
        w=new_world();p=nilo.initial_state()['person']
        a=resolve_go(w,p,{'op':'go','x':0,'y':2})
        b=resolve_go(w,p,{'op':'go','x':5,'y':2})
        self.assertEqual(a,b)
        self.assertIn('No conozco',a[2])

    def test_known_destinations_still_navigable(self):
        w=new_world();p=nilo.initial_state()['person']
        self.assertEqual(resolve_go(w,p,{'op':'go','x':15,'y':11})[0],(15,11))

class Materials(unittest.TestCase):
    def test_compound_physics_survives_multiple_properties(self):
        w=new_world();p=nilo.initial_state()['person']
        p['inventory'].update({'arcilla':2,'fibra':2})
        _,_,ok,_=execute_action(w,p,{'op':'combine','materials':['arcilla','fibra'], 'method':'mezclar'},random.Random(1))
        self.assertTrue(ok)
        name='compuesto mezclar (arcilla + fibra)'
        self.assertIn(name,p['materials'])
        expected=p['materials'][name]
        self.assertAlmostEqual(properties(name,p['materials'])['permeability'],expected['permeability'])
        self.assertAlmostEqual(properties(name,p['materials'])['density'],expected['density'])

class ContextBudget(unittest.TestCase):
    def test_compact_keeps_core_project_and_conclusions(self):
        core={'proyecto_actual':{'id':'p1','title':'Investigar agua','progress':25},
              'conclusiones_verificadas':[{'text':'Medí retención','id':'c1'}],
              'percepción_local':[{'text':'pasto'*500} for _ in range(10)]}
        result=compact_context(core,150)
        self.assertEqual(result['proyecto_actual']['id'],'p1')
        self.assertEqual(result['conclusiones_verificadas'][0]['id'],'c1')

class HistoryBatch(unittest.TestCase):
    def test_batch_seq_and_read_respects_category(self):
        db=sqlite3.connect(':memory:');h=History(db)
        a=h.add('journal',{'id':'j1','when':'T','text':'a'});b=h.add('news',{'id':'n1','when':'T','text':'b'})
        h.mark_one_read('journal',a)
        meta,read=h.recent_meta()
        self.assertEqual(meta['journal']['j1'],a)
        self.assertEqual(meta['news']['n1'],b)
        self.assertIn(('journal',a),read)
        self.assertNotIn(('news',b),read)
        db.close()

class Replay(unittest.TestCase):
    def test_scenario_fingerprint_stable(self):
        self.assertEqual(run(7321),run(7321))
        self.assertTrue(run(7321)['passed'])
        self.assertNotEqual(run(7321)['fingerprint'],run(7322)['fingerprint'])

class StateLayers(unittest.TestCase):
    def test_surface_and_cave_are_independent_of_current_position(self):
        with tempfile.TemporaryDirectory() as td:
            old=nilo.DB;nilo.DB=Path(td)/'test.sqlite3'
            try:
                sim=nilo.Simulation()
                state=sim.public_state()
                self.assertIn('0',state['maps']);self.assertIn('-1',state['maps'])
                self.assertEqual(state['maps']['0'][10][15],'@')
                self.assertEqual(state['maps']['-1'][10][15],' ')
                sim.conn.close()
            finally:nilo.DB=old

if __name__=='__main__':unittest.main()
