"""0.5.9.3.7 — aceleración, pausas, escritura y marcas visuales."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from nilo import Simulation
from timing import effective_speed, writing_tick

ROOT = Path(__file__).resolve().parent.parent


class ClockPolicy(unittest.TestCase):
    def test_speed_modes(self):
        for speed in (1, 10, 60, 80):
            self.assertEqual(effective_speed(speed, planning=True), 1)
            self.assertEqual(effective_speed(speed, frozen=True), 0)
            self.assertEqual(effective_speed(speed, paused=True), 0)
            self.assertEqual(effective_speed(speed, 'explore'), speed)
        self.assertEqual(effective_speed(60, 'write'), 2)
        self.assertEqual(effective_speed(80, 'write'), 2)

    def test_fast_writing_keeps_simulated_duration(self):
        simulated, left = writing_tick(.2, 90, 80)
        self.assertAlmostEqual(simulated, .4)
        self.assertAlmostEqual(left, 89.6)


class SimulationClock(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.sim = Simulation(db_path=Path(self.folder.name) / 'world.sqlite')

    def tearDown(self):
        self.sim.conn.close()
        self.folder.cleanup()

    def test_speed_persisted(self):
        for speed in (60, 80):
            self.sim.change_speed(speed=speed)
            self.assertEqual(self.sim.s['speed'], speed)
        self.sim.change_speed(speed=600)
        self.assertEqual(self.sim.s['speed'], 80)

    def test_llm_call_is_one_x_even_if_selected_80(self):
        s = self.sim
        s.change_speed(speed=80)
        s.s['planning'] = True
        s.s['person']['plan'] = []
        s.s['person']['pending'] = None
        before = s.s['person']['clock_minutes']
        s.tick(15)
        self.assertAlmostEqual(s.s['person']['clock_minutes']-before, 15/60, places=5)
        self.assertEqual(s.public_state()['effective_speed'], 1)
        self.assertEqual(s.s['speed'], 80)

    def test_cooldown_freezes_when_no_work(self):
        s = self.sim
        s.change_speed(speed=80)
        s.s['mode'] = 'llm'
        s.s['next_deliberation_real'] = time.time() + 60
        p = s.s['person']
        p['plan'] = []
        p['pending'] = None
        p['waiting_preferences'] = []
        p['inventory'].update({'alimento':12,'madera':12,'piedra':12})
        p['needs'].update({'energia':100,'hidratacion':100,'nutricion':100})
        with patch('nilo.available',return_value=True):
            s.tick(1)
            self.assertTrue(s.s['auto_wait_frozen'])
            stopped = p['clock_minutes']
            s.tick(10)
            self.assertEqual(p['clock_minutes'], stopped)
        self.assertEqual(s.public_state()['effective_speed'], 0)

    def test_two_short_actions_respect_sequential_clock(self):
        s = self.sim
        s.change_speed(speed=80)
        s.s['next_deliberation_real'] = time.time() + 600
        s.s['person']['plan'] = [
            {'op':'inspect', 'target':'suelo'},
            {'op':'inspect', 'target':'suelo'}]
        before=s.s['person']['clock_minutes']
        # Aislar la medición de reloj de los hábitos elegidos durante una
        # espera de API: esas tareas se prueban en tests independientes.
        with patch('nilo.available',return_value=False):
            s.tick(20)
            s.tick(2.5)
        self.assertEqual(s.s['person']['plan'], [])
        self.assertIsNone(s.s['person']['pending'])
        self.assertAlmostEqual(s.s['person']['clock_minutes']-before, 30, places=4)
        recent=[m for m in s.s['person'].get('measurements',[]) if m.get('op')=='inspect']
        self.assertGreaterEqual(len(recent), 2)

    def test_fast_journal_shows_full_text_with_world_duration(self):
        s = self.sim
        s.change_speed(speed=80)
        s.s['planning'] = True
        entry=s.journal('Registro breve que debería mostrarse instantáneamente.')
        original=entry['duration_seconds']
        start=s.s['person']['clock_minutes']
        self.assertTrue(s.public_state()['journal'][0]['writing'])
        s.tick(1)
        self.assertIsNotNone(s.s['person']['pending'])
        self.assertGreater(s.s['person']['clock_minutes'],start)
        self.assertEqual(s.s['speed'],80)


class Interface(unittest.TestCase):
    def test_buttons_and_unread_skill_highlight(self):
        html=(ROOT/'interfaz.html').read_text('utf-8')
        for speed in (1,10,60,80):
            self.assertIn(f'data-speed="{speed}"',html)
        self.assertNotIn('data-speed="300"',html)
        self.assertIn("[data-skill-index].new-record",html)
        self.assertIn("effective-speed-label",html)


if __name__ == '__main__':
    unittest.main()
