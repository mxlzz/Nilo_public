"""Pure synthetic fixtures only; no NR01 scientific seeds executed."""
import unittest
from experiments.neurolab.nr01_dev_analysis import bootstrap_ci, summarize, _percentile


class TestNR01DevAnalysis(unittest.TestCase):
    def test_bootstrap_is_stable_and_paired_by_world(self):
        sample = [0.1] * 20
        self.assertEqual(bootstrap_ci(sample), [0.1, 0.1])
        self.assertEqual(bootstrap_ci(list(range(20))),
                         bootstrap_ci(list(range(20))))

    def test_percentile_linear(self):
        self.assertEqual(_percentile([0, 10], .25), 2.5)
        self.assertEqual(_percentile([1, 1, 1], .975), 1)

    def test_reject_incomplete_design(self):
        with self.assertRaises(ValueError):
            summarize([])
        with self.assertRaises(ValueError):
            summarize([{"world_seed": 23000, "family": "A",
                       "kind": "raw", "parameter": None}])

if __name__ == "__main__":
    unittest.main()
