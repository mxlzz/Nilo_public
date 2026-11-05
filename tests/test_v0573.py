"""Regresiones de escritura ×2 frente a aceleración seleccionada."""
import tempfile
import unittest
from pathlib import Path

from nilo import Simulation
from timing import effective_speed, writing_tick


class WritingSpeed(unittest.TestCase):
    def test_speed_policy(self):
        self.assertEqual(effective_speed(1,'write'),1)
        self.assertEqual(effective_speed(10,'write'),2)
        self.assertEqual(effective_speed(60,'write'),2)
        self.assertEqual(effective_speed(60,'explore'),60)
        self.assertEqual(effective_speed(10,None),10)

    def test_exact_boundary_resumes_selected_speed_in_same_tick(self):
        # Quedan 8 segundos base de escritura, a x2 termina en 4 reales.
        simulated, remaining=writing_tick(5,8,60)
        self.assertEqual(remaining,0)
        self.assertEqual(simulated,68)  # 8 al escribir y 60 durante el último segundo.

    def test_base_duration_does_not_depend_on_selected_speed(self):
        for speed in (1,10,60):
            delta,remain=writing_tick(2,12,speed)
            self.assertEqual(remain,12-2*effective_speed(speed,'write'))
            self.assertAlmostEqual(delta,12-remain)

    def test_real_simulation_writing_and_pause(self):
        for speed in (1,10,60):
            with self.subTest(speed=speed), tempfile.TemporaryDirectory() as directory:
                sim=Simulation(db_path=Path(directory)/'sim.sqlite')
                try:
                    sim.s['planning']=True  # impedir deliberación durante la prueba
                    sim.change_speed(speed=speed)
                    entry=sim.journal('Estoy escribiendo una entrada de prueba para medir el tiempo.')
                    original=sim.s['person']['pending']['total_real']
                    start=sim.s['person']['clock_minutes']
                    sim.tick(2)
                    pending=sim.s['person']['pending']
                    self.assertAlmostEqual(
                        pending['remaining_real'],original-2*effective_speed(speed,'write'))
                    self.assertAlmostEqual(
                        sim.s['person']['clock_minutes']-start,
                        2*effective_speed(speed,'write')/60)
                    visible=sim.public_state()
                    self.assertEqual(visible['effective_speed'],effective_speed(speed,'write'))
                    self.assertAlmostEqual(visible['remaining_write_base_seconds'],
                        pending['remaining_real'])
                    sim.change_speed(paused=True)
                    paused=sim.s['person']['clock_minutes']
                    left=pending['remaining_real']
                    sim.tick(5)
                    self.assertEqual(sim.s['person']['clock_minutes'],paused)
                    self.assertEqual(pending['remaining_real'],left)
                    sim.change_speed(paused=False)
                    sim.tick(left/effective_speed(speed,'write'))
                    self.assertIsNone(sim.s['person']['pending'])
                    self.assertEqual(sim.s['speed'],speed)
                    self.assertAlmostEqual(sim.s['person']['clock_minutes']-start,
                                           original/60,places=5)
                finally:
                    sim.conn.close()

    def test_change_speed_while_writing_does_not_restore_old_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            sim=Simulation(db_path=Path(directory)/'sim.sqlite')
            try:
                sim.s['planning']=True
                sim.change_speed(speed=60)
                sim.journal('El tiempo de escritura debe respetar una nueva selección.')
                start=sim.s['person']['pending']['remaining_real']
                sim.tick(1)
                sim.change_speed(speed=1)
                sim.tick(1)
                self.assertAlmostEqual(sim.s['person']['pending']['remaining_real'],start-3)
                self.assertEqual(sim.s['speed'],1)
                self.assertEqual(sim.public_state()['effective_speed'],1)
            finally:
                sim.conn.close()


if __name__=='__main__':
    unittest.main()
