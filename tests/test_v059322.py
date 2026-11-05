"""Autonomía corporal v0.5.9.3.22: pruebas sin LLM."""
import unittest
import tempfile
from pathlib import Path
from bodily_policy import rest_minutes, fatigue_multiplier
from survival import update_needs, ensure_needs
from habits import choose_wait_action, _safe_preference
from agenda import normalize_task, safe_step, choose_agenda_step
from brain import normalize_decision
from nilo import initial_state, Simulation


class AutonomyContracts(unittest.TestCase):
    def person(self, energia=70, hidratacion=45, nutricion=45):
        p=initial_state(7321)['person']
        ensure_needs(p).update(energia=energia,hidratacion=hidratacion,nutricion=nutricion)
        p['inventory']['alimento']=2
        p['waiting_preferences']=[]
        p['agenda']=[]
        return p

    def test_physiology_does_not_eat_or_drink_by_threshold(self):
        p=self.person(hidratacion=45,nutricion=45)
        previous=p['inventory']['alimento']
        update_needs(p,{},60,near_water=True)
        self.assertEqual(p['inventory']['alimento'],previous)
        self.assertLess(p['needs']['hidratacion'],45)
        self.assertLess(p['needs']['nutricion'],45)

    def test_old_autocare_only_when_replay_requests_it(self):
        p=self.person(hidratacion=45,nutricion=45)
        update_needs(p,{},60,near_water=True,legacy_autocare=True)
        self.assertEqual(p['inventory']['alimento'],1)
        self.assertGreater(p['needs']['hidratacion'],45)

    def test_wait_never_invents_care_or_stocks(self):
        p=self.person(energia=9,hidratacion=9,nutricion=9)
        self.assertIsNone(choose_wait_action({},p))

    def test_explicit_rest_preference_keeps_minutes_at_high_energy(self):
        p=self.person(energia=95)
        p['waiting_preferences']=[_safe_preference({'op':'rest','minutes':120})]
        operation,_=choose_wait_action({},p)
        self.assertEqual(operation,{'op':'rest','minutes':120})

    def test_duration_is_validated_in_llm_and_agenda(self):
        self.assertEqual(rest_minutes({'op':'rest'}),30)
        self.assertEqual(rest_minutes({'minutes':120}),120)
        for invalid in (0,1441,True,float('nan'),float('inf'),'invalid'):
            self.assertIsNone(rest_minutes({'minutes':invalid}))
        decision=normalize_decision({'cuaderno':'Descansar por elección propia.',
                                    'accion_proyecto':'sin_proyecto',
                                    'plan':[{'op':'rest','minutes':120}]})
        self.assertEqual(decision['plan'][0]['minutes'],120)
        task=normalize_task({'titulo':'Descanso delegado',
                             'pasos':[{'op':'rest','minutes':120}]},0)
        self.assertEqual(task['pasos'][0]['minutes'],120)

    def test_agenda_rest_allowed_despite_global_wellbeing_thresholds(self):
        p=self.person(energia=80,hidratacion=20,nutricion=10)
        task=normalize_task({'titulo':'Descanso delegado',
                             'pasos':[{'op':'rest','minutes':120}]},0)
        p['agenda']=[task]
        self.assertTrue(safe_step({},p,task['pasos'][0]))
        selected=choose_agenda_step({},p)
        self.assertIsNotNone(selected)
        self.assertEqual(selected[0]['minutes'],120)

    def test_fatigue_is_shared_between_actions_and_travel(self):
        self.assertEqual(fatigue_multiplier({'energia':85,'hidratacion':85}),1)
        self.assertEqual(fatigue_multiplier({'energia':35,'hidratacion':90}),1.35)
        self.assertEqual(fatigue_multiplier({'energia':70,'hidratacion':19}),1.7)


class SimulationAutonomy(unittest.TestCase):
    def engine(self, folder):
        sim=Simulation(db_path=Path(folder)/'autonomia.sqlite3')
        sim.think=lambda: self.fail('No corresponde deliberar durante esta prueba.')
        sim.s['auto_wait_frozen']=False
        sim.s['planning']=True  # Las pruebas no contactan proveedores.
        return sim

    def test_voluntary_rest_uses_actual_minutes(self):
        with tempfile.TemporaryDirectory() as folder:
            sim=self.engine(folder)
            try:
                p=sim.s['person']
                p['plan']=[{'op':'rest','minutes':120}]
                sim._tick_slice(0)
                self.assertEqual(p['pending']['total'],120)
                self.assertEqual(p['pending']['step']['minutes'],120)
                self.assertFalse(p.get('unconscious',False))
            finally:
                sim.conn.close()

    def test_collapse_stops_current_action_without_consuming_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            sim=self.engine(folder)
            try:
                p=sim.s['person']
                p['needs']['energia']=5
                before=dict(p['inventory'])
                p['plan']=[{'op':'gather','target':'madera'}]
                p['pending']={'step':{'op':'inspect','target':'suelo'},
                              'remaining':8,'total':9}
                sim._tick_slice(0)
                self.assertTrue(p['unconscious'])
                self.assertIsNone(p['pending'])
                self.assertEqual(p['plan'],[])
                self.assertEqual(p['inventory'],before)
                self.assertEqual(p['interrupted_by_collapse']['op'],'inspect')
                self.assertIn('Inconsciente',sim.public_state()['activity'])
                p['needs']['energia']=39.99
                sim._tick_slice(20)
                self.assertFalse(p['unconscious'])
            finally:
                sim.conn.close()

    def test_travel_time_reflects_same_fatigue_as_other_actions(self):
        from world import tile_key,set_tile
        with tempfile.TemporaryDirectory() as folder:
            sim=self.engine(folder)
            try:
                p=sim.s['person']
                w=sim.s['world']
                x,y,z=p['pos']
                set_tile(w,x+1,y,z,'.')
                key=tile_key(x+1,y,z)
                if key not in w['revealed']:
                    w['revealed'].append(key)
                p['needs']['energia']=35
                p['needs']['hidratacion']=85
                p['plan']=[{'op':'go','x':x+1,'y':y}]
                sim._tick_slice(0)
                pending=p['pending']
                self.assertIsNotNone(pending)
                self.assertIn('navigation',pending)
                self.assertAlmostEqual(pending['travel_minutes_per_tile'],3*1.35)
                self.assertAlmostEqual(pending['total'],len(pending['navigation']['route'])*3*1.35)
            finally:
                sim.conn.close()


if __name__=='__main__':
    unittest.main()
