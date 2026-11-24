"""I3c.5c observational reuse of historical I3c.5a cohort, not G05."""
import unittest

from experiments.neurolab.e09_i3c5c_trunk_availability import (
    SEEDS, INPUTS, REFERENCE_SHA, frozen_reference, run_trunk, run_all,
)


class OriginalTrunkReplayTests(unittest.TestCase):
    def test_reference_is_original_complete_cohort(self):
        self.assertEqual(SEEDS, tuple(range(1200,1220)))
        self.assertEqual(len(INPUTS), 120)
        self.assertEqual(len(frozen_reference()), 40)
        self.assertEqual(len(REFERENCE_SHA), 64)
        self.assertEqual(INPUTS[:8], (0,)*8)
        self.assertEqual(INPUTS[8:16], (1,)*8)

    def test_same_trunk_matches_first_original_checkpoint(self):
        expected = frozen_reference()
        t = run_trunk(1200, 0, original=expected)
        self.assertEqual(t["checkpoint_sha256"], expected["1200:0"])
        self.assertEqual(len(t["frames"]), 125)
        self.assertEqual(t["frames"][0]["strength_positive"],8)
        self.assertEqual(t["frames"][-1]["tick"],124)
        self.assertEqual(t["frames"][-1]["strength_zero"],8)

    def test_no_selection_outside_frozen_group(self):
        for seed in (1199, 1220, 300, 800):
            with self.assertRaises(ValueError):
                run_trunk(seed, 0)
        with self.assertRaises(ValueError):
            run_trunk(1200, 2)
        for seeds in ((1200,1200), (1220,), (), [1200]):
            with self.assertRaises(ValueError):
                run_all(seeds)

    def test_replay_reproducible_and_non_confirmatory(self):
        a=run_all((1200,))
        b=run_all((1200,))
        self.assertEqual(a,b)
        self.assertEqual(a["unique_trunks"],2)
        self.assertEqual(a["samples_per_trunk"],125)
        self.assertTrue(a["all_checkpoint_hashes_replayed"])
        self.assertTrue(a["original_cohort_not_independent"])
        self.assertTrue(a["G05_G09_G00H"].startswith("OPEN"))


if __name__ == "__main__":
    unittest.main()
