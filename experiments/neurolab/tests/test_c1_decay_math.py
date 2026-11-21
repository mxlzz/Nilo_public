"""E09.02f.2: test manual-oracle cases based on C1 x86 code / rate tables."""
import random
import unittest

from experiments.neurolab.c1_decay_math import (
    FACTORS, MASKS, decay, relax, ltw_toward,
)


class C1DecayTests(unittest.TestCase):
    def test_exact_tables_and_spot_checks(self):
        self.assertEqual(len(FACTORS), 32)
        self.assertEqual(len(MASKS), 32)
        self.assertEqual(FACTORS[:8], (0,0x32A5,0x71DD,0xAABB,0xD110,
                                       0xE758,0xF35C,0xF999))
        self.assertEqual(FACTORS[8:31], (0xF999,)*23)
        self.assertEqual(FACTORS[31], 0xFFFF)
        self.assertEqual(MASKS[:8], (0,)*8)
        self.assertEqual(MASKS[8:12], (1,3,7,15))
        self.assertEqual(MASKS[31], 0xFFFFFF)

    def test_suscept_decay_rate48_every_tick(self):
        self.assertEqual(decay(200,48,0),190)
        self.assertEqual(decay(200,48,101),190)

    def test_stw_decay_rate80_every_eighth_tick(self):
        self.assertEqual(decay(200,80,6),200)
        self.assertEqual(decay(200,80,7),194)
        self.assertEqual(decay(200,80,8),200)
        self.assertEqual(decay(200,80,15),194)

    def test_stw_relax_to_zero_in_binary_steps(self):
        self.assertEqual(relax(255,80,0,6),255)
        self.assertEqual(relax(255,80,0,7),248)

    def test_stw_relax_toward_higher_target(self):
        self.assertEqual(relax(0,48,200,0),10)
        self.assertEqual(relax(0,48,200,255),10)
        self.assertEqual(relax(180,48,180,99),180)

    def test_ltw_moves_one_on_matching_tick(self):
        self.assertEqual(ltw_toward(120,200,128,127),120)
        self.assertEqual(ltw_toward(120,200,128,128),121)
        self.assertEqual(ltw_toward(120,50,128,128),119)
        self.assertEqual(ltw_toward(120,50,128,129),120)
        self.assertEqual(ltw_toward(120,200,0,128),120)

    def test_rate_zero_and_max255(self):
        self.assertEqual(decay(255,0,0),0)
        self.assertEqual(relax(200,0,50,0),50)
        self.assertEqual(decay(255,255,0),255)
        self.assertEqual(decay(255,255,0xFFFFFF),254)
        self.assertEqual(relax(255,255,0,0xFFFFFF),254)

    def test_bounds_and_invalid_values(self):
        for bad in (-1,256,True,0.5):
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                decay(bad,48,0)
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                relax(100,bad,0,0)
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                ltw_toward(100,100,bad,0)
        for bad in (-1,True,0.5):
            with self.assertRaises(ValueError):
                decay(100,48,bad)

    def test_numerical_invariants_across_all_rates(self):
        for rate in range(256):
            for value in (0,1,64,128,254,255):
                tick = MASKS[rate>>3]
                result = decay(value,rate,tick)
                self.assertTrue(0 <= result <= value)
                self.assertTrue(0 <= relax(value,rate,255,tick) <= 255)
                self.assertTrue(0 <= relax(value,rate,0,tick) <= 255)

    def test_twenty_reproducible_sequences(self):
        def one_run(seed):
            rng=random.Random(seed)
            value=128
            result=[]
            for tick in range(200):
                rate=rng.randrange(256)
                target=rng.randrange(256)
                value=relax(value,rate,target,tick)
                result.append(value)
            return result
        for seed in range(20):
            self.assertEqual(one_run(seed),one_run(seed))


if __name__ == "__main__":
    unittest.main()
