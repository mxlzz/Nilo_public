import unittest,sys,random,sqlite3,tempfile,json,time
from pathlib import Path
from unittest.mock import patch
HOME=Path(__file__).resolve().parents[1]/'nilo'
sys.path.insert(0,str(HOME))
from nilo import Simulation,initial_state
from world import set_tile, tile_key, execute_action
from habits import ensure_habits,record_skill,set_wait_preferences,choose_wait_action
from brain import normalize_decision,context_for

class HabitsTests(unittest.TestCase):
 def example(self):
  s=initial_state();p=s['person'];w=s['world']
  ensure_habits(p)
  p['pos']=[15,10,0]
  return w,p
 def test_only_physical_success_teaches_skill(self):
  w,p=self.example();before=dict(p['inventory'])
  record_skill(p,{'op':'forage'},True,['Tengo muchos frutos'],'día 1',before)
  self.assertFalse(p['skills'])
  set_tile(w,15,10,0,'T')
  _,facts,ok,_=execute_action(w,p,{'op':'forage'},random.Random(1))
  self.assertTrue(ok)
  record_skill(p,{'op':'forage'},ok,facts,'día 1',before)
  self.assertEqual(p['skills']['forage']['count'],1)
  self.assertTrue(p['skills']['forage']['verified'])
  # Aprender a recolectar no significa elegir reponer reservas.
  self.assertIsNone(choose_wait_action(w,p))
  set_wait_preferences(p,[{'op':'forage','hasta':3,'radio':2}], 'día 1')
  self.assertEqual(choose_wait_action(w,p)[0]['op'],'forage')
 def test_no_skill_no_gather(self):
  w,p=self.example();self.assertIsNone(choose_wait_action(w,p))
 def test_set_preferences_sanitizes_and_explicitly_resets(self):
  _,p=self.example()
  self.assertTrue(set_wait_preferences(p,[{'op':'explore'}, {'op':'gather','target':'madera','hasta':999,'radio':999,'motivo':'a'*400}], 'día 1'))
  self.assertEqual(len(p['waiting_preferences']),1)
  self.assertEqual(p['waiting_preferences'][0]['hasta'],8)
  self.assertEqual(p['waiting_preferences'][0]['radio'],5)
  self.assertFalse(set_wait_preferences(p,None,'día 2'))
  self.assertTrue(set_wait_preferences(p,[],'día 3'))
  self.assertEqual(p['waiting_preferences'],[])
 def test_rest_requires_explicit_preference(self):
  w,p=self.example();p['needs']={'energia':20,'hidratacion':80,'nutricion':80,'abrigo':80,'seguridad':80}
  self.assertIsNone(choose_wait_action(w,p))
  set_wait_preferences(p,[{'op':'rest','minutes':120}], 'día 1')
  self.assertEqual(choose_wait_action(w,p)[0]['minutes'],120)
 def test_wait_cannot_explore_or_new_craft_without_skill(self):
  w,p=self.example();set_wait_preferences(p,[{'op':'craft','target':'lancha','hasta':2}], 'día 1')
  self.assertIsNone(choose_wait_action(w,p))
 def test_decision_habit_and_context(self):
  w,p=self.example()
  q=normalize_decision({'plan':[{'op':'forage'}],'cuaderno':'Quiero comer','actividades_en_espera':[{'op':'forage','hasta':3}]})
  self.assertEqual(q['actividades_en_espera'][0]['op'],'forage')
  self.assertIn('habilidades_verificadas',context_for(w,p,[],'día 1'))

class SimulationTests(unittest.TestCase):
 def setup_sim(self):
  import nilo
  td=tempfile.TemporaryDirectory();orig=nilo.DB;nilo.DB=Path(td.name)/'test.sqlite3'
  sim=Simulation();return sim,td,orig
 def stop(self,sim,td,orig):
  import nilo
  sim.conn.close();nilo.DB=orig;td.cleanup()
 def test_retries_wait_and_does_not_spam(self):
  sim,td,orig=self.setup_sim()
  try:
   p=sim.s['person'];w=sim.s['world'];p['plan']=[];p['pending']=None
   set_tile(w,15,10,0,'T')
   old=dict(p['inventory']);_,facts,ok,_=execute_action(w,p,{'op':'forage'},random.Random(1))
   record_skill(p,{'op':'forage'},ok,facts,'Día 1',old)
   p['inventory']['alimento']=0
   set_wait_preferences(p,[{'op':'forage','hasta':3,'radio':2}], 'Día 1')
   sim.s['mode']='espera';sim.s['next_deliberation_real']=time.time()+1000;sim.s['speed']=60
   with patch('nilo.available',return_value=True),patch('nilo.config',return_value={'MAX_LLM_CALLS_PER_DAY':'100'}):
    sim.tick(1)
    self.assertEqual(len(p['plan']),1)
    self.assertEqual(p['plan'][0]['_origin'],'rutina')
    self.assertEqual(p['plan'][0]['op'],'forage')
    sim.tick(1)
    self.assertEqual(p['pending']['step']['_origin'],'rutina')
    sim.tick(20)
   self.assertEqual(len(p['waiting_history']),1)
   self.assertTrue(p['waiting_history'][0]['success'])
   self.assertEqual(p['inventory']['alimento'],1)
   self.assertGreaterEqual(p['routine_last_minute'],0)
  finally:self.stop(sim,td,orig)
 def test_wait_with_no_skill_chooses_rest_without_actions(self):
  sim,td,orig=self.setup_sim()
  try:
   p=sim.s['person'];sim.s['mode']='limite';sim.s['next_deliberation_real']=time.time()+1000
   with patch('nilo.available',return_value=True),patch('nilo.config',return_value={'MAX_LLM_CALLS_PER_DAY':'100'}):sim.tick(1)
   self.assertEqual(p['waiting_state']['kind'],'inactivo')
   self.assertFalse(p['plan']);self.assertIsNone(p['pending'])
  finally:self.stop(sim,td,orig)
 def test_save_restore_old_db_preserves_history(self):
  sim,td,orig=self.setup_sim()
  try:
   p=sim.s['person'];sim.s['journal']=[{'id':'old','text':'El terreno parece firme','when':'Día 1'}]
   p['waiting_preferences']=[{'op':'rest','target':'','hasta':3,'radio':2,'motivo':'Descansar'}]
   sim.write();sim.conn.close()
   restored=Simulation()
   self.assertEqual(restored.s['journal'][0]['id'],'old')
   self.assertEqual(restored.s['person']['waiting_preferences'][0]['op'],'rest')
   restored.conn.close()
   sim.conn=sqlite3.connect(':memory:')
  finally:self.stop(sim,td,orig)

if __name__=='__main__':unittest.main()
