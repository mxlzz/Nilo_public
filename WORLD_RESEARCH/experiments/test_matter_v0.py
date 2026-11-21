import random
import unittest
from matter_v0 import Material, MatterGrid


class MatterTests(unittest.TestCase):
    def setUp(self):
        self.materials={'A':Material('A',2.0),'B':Material('B',1.0)}
        self.grid=MatterGrid(3,2,self.materials)

    def test_material_density_controls_derived_volume(self):
        self.grid.add_initial((0,0),'A',1.0)
        self.grid.add_initial((1,0),'B',1.0)
        self.assertAlmostEqual(self.grid.volume_at((0,0)),0.5)
        self.assertAlmostEqual(self.grid.volume_at((1,0)),1.0)

    def test_multiple_materials_share_capacity_without_converting(self):
        self.grid.add_initial((0,0),'A',1.0)  # ocupa 0.5
        self.grid.add_initial((0,0),'B',0.5)  # ocupa 0.5
        self.assertAlmostEqual(self.grid.volume_at((0,0)),1.0)
        self.assertEqual(self.grid.mass_by_material(),{'A':1.0,'B':0.5})
        with self.assertRaises(ValueError):
            self.grid.add_initial((0,0),'B',0.01)

    def test_transfer_conserves_mass_of_each_component(self):
        self.grid.add_initial((0,0),'A',1.0)
        self.grid.add_initial((1,0),'B',0.25)
        before=self.grid.mass_by_material()
        self.grid.transfer((0,0),(1,0),'A',0.5)
        self.assertEqual(before,self.grid.mass_by_material())
        self.assertAlmostEqual(self.grid.volume_at((1,0)),0.5)

    def test_reject_overfill_without_mutating_state(self):
        self.grid.add_initial((0,0),'A',2.0)
        self.grid.add_initial((1,0),'B',1.0)
        before=self.grid.snapshot()
        with self.assertRaises(ValueError):
            self.grid.transfer((0,0),(1,0),'A',0.5)
        self.assertEqual(before,self.grid.snapshot())

    def test_reject_missing_mass_without_mutating_state(self):
        self.grid.add_initial((0,0),'A',0.25)
        before=self.grid.snapshot()
        with self.assertRaises(ValueError):
            self.grid.transfer((0,0),(1,0),'A',0.5)
        self.assertEqual(before,self.grid.snapshot())

    def test_reject_invalid_materials_mass_coords(self):
        for material in (lambda:Material('x',0),lambda:Material('x',float('nan')),
                         lambda:Material('x',-1)):
            with self.assertRaises(ValueError):material()
        with self.assertRaises(ValueError):self.grid.add_initial((7,0),'A',1)
        with self.assertRaises(ValueError):self.grid.add_initial((0,0),'C',1)
        with self.assertRaises(ValueError):self.grid.add_initial((0,0),'A',-1)

    def test_snapshot_roundtrip_and_version_validation(self):
        self.grid.add_initial((0,0),'A',1)
        self.grid.transfer((0,0),(1,0),'A',0.25)
        restored=MatterGrid.from_snapshot(self.grid.snapshot())
        self.assertEqual(self.grid.snapshot(),restored.snapshot())
        with self.assertRaises(ValueError):MatterGrid.from_snapshot('{"version":2}')

    def test_replay_reproducible_and_invariants_under_many_transfers(self):
        def run(seed):
            g=MatterGrid(5,5,self.materials)
            g.add_initial((0,0),'A',2)
            g.add_initial((4,4),'B',1)
            initial=g.mass_by_material()
            rng=random.Random(seed)
            for _ in range(200):
                src=(rng.randrange(5),rng.randrange(5))
                dst=(rng.randrange(5),rng.randrange(5))
                material_id=rng.choice(('A','B'))
                try:g.transfer(src,dst,material_id,0.25)
                except ValueError:pass
                self.assertTrue(all(0<=g.volume_at((x,y))<=1+1e-10 for x in range(5) for y in range(5)))
            self.assertEqual(initial,g.mass_by_material())
            return g.snapshot()
        self.assertEqual(run(7321),run(7321))


if __name__=='__main__':unittest.main()
