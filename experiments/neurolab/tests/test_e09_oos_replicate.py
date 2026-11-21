"""E09g9 replication: no seed overlap, paired bootstrap and reuse of g8."""
import unittest

from experiments.neurolab.e09_oos_replicate import (
    SEEDS, paired_bootstrap_interval,
)
from experiments.neurolab.e09_paired_pulse_protocol import run_seed


class IndependentReplicationTests(unittest.TestCase):
    def test_seed_partition_is_locked_and_disjoint(self):
        self.assertEqual(SEEDS, tuple(range(20, 100)))
        self.assertEqual(set(SEEDS).intersection(range(20)), set())

    def test_bootstrap_of_constant_paired_differences(self):
        self.assertEqual(paired_bootstrap_interval([0.0]*20), (0.0,0.0))
        lo, hi = paired_bootstrap_interval([0.25]*20)
        self.assertAlmostEqual(lo, .25)
        self.assertAlmostEqual(hi, .25)

    def test_bootstrap_fixed_seed_deterministic(self):
        values = [-.1, .0, .1, .2, .3]
        self.assertEqual(paired_bootstrap_interval(values),
                         paired_bootstrap_interval(values))

    def test_bad_bootstrap_inputs_rejected(self):
        with self.assertRaises(ValueError):
            paired_bootstrap_interval([])
        with self.assertRaises(ValueError):
            paired_bootstrap_interval([1.0], replicates=20)

    def test_reuses_frozen_g8_unseen_seed_deterministically(self):
        self.assertEqual(run_seed(20), run_seed(20))


if __name__ == "__main__":
    unittest.main()
