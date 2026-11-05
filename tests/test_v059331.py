"""Regresiones 0.5.9.3.31: nombres legibles con referencias físicas intactas."""
import tempfile
import unittest
from pathlib import Path

from nilo import Simulation


class ActivityLabels(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.sim=Simulation(db_path=Path(self.folder.name)/'nilo.sqlite')
        self.p=self.sim.s['person']
        self.p['items'].extend([
            {'id':'obj-a','name':'hacha de piedra'},
            {'id':'obj-b','name':'hacha de piedra'},
        ])

    def tearDown(self):
        self.sim.conn.close()
        self.folder.cleanup()

    def test_use_displays_name_and_method_but_keeps_id_in_step(self):
        step={'op':'use','item':'obj-b','target':'entorno','method':'cortar'}
        self.assertEqual(self.sim.describe_action(step),
                         'Probar herramienta hacha de piedra · cortar')
        self.assertEqual(step['item'],'obj-b')

    def test_unknown_id_remains_visible_instead_of_inventing_name(self):
        step={'op':'use','item':'obj-not-found','method':'cortar'}
        self.assertEqual(self.sim.describe_action(step),
                         'Probar herramienta obj-not-found · cortar')

    def test_legacy_name_reference_not_modified(self):
        step={'op':'use','item':'hacha de piedra','method':'cortar'}
        self.assertEqual(self.sim.describe_action(step),
                         'Probar herramienta hacha de piedra · cortar')

    def test_interface_uses_exact_id_for_rendering_queued_actions(self):
        ui=(Path(__file__).resolve().parents[1]/'interfaz.html').read_text('utf-8')
        self.assertIn('(data?.items||[]).find(tool=>tool.id===rawSubject)',ui)
        self.assertIn('known?.name||rawSubject',ui)


if __name__=='__main__':
    unittest.main()
