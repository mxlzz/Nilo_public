"""E09.05-TAB2 tests: exact original E03 3-tick reset vs independent 2x2 table."""
import unittest

from experiments.neurolab.plasticity import PlasticLearner, PlasticState
from experiments.neurolab.e09_binary_tabular_equivalence import (
    IndependentBinaryTable, BinaryTableState, check_full_legal_domain, run_all
)


class TestE09BinaryTabularEquivalence(unittest.TestCase):
    def test_original_20_seeds_training_holdouts_reversal(self):
        d = run_all()
        self.assertEqual(d["protocol"], "E09.05-TAB2-v1")
        self.assertEqual(d["seeds"], list(range(20)))
        self.assertTrue(d["all_equal"])
        self.assertEqual(d["discrepancies"], 0)
        self.assertEqual(d["two_input_comparisons"], 10480)
        self.assertEqual(d["holdout_comparisons"], 3200)
        self.assertEqual(d["online_updates"], 5200)
        self.assertFalse(d["confirmatory_cohort_used"])
        for r in d["per_seed"]:
            self.assertEqual(r["final_trials"], 260)

    def test_reset_three_tick_manual_score_identity(self):
        learner = PlasticLearner(4)
        table = IndependentBinaryTable(4)
        self.assertEqual(check_full_legal_domain(learner, learner.initial(),
                                                table, table.initial_state), 2)

    def test_tie_abstention_positive_tie_and_saturation(self):
        learner = PlasticLearner(4)
        table = IndependentBinaryTable(4)
        for w, reward, expected_action, expected_first in (
            ((0, 0, 60, 30), +1, None, 0),
            ((255, 255, 60, 30), +1, "D0", 255),
            ((16, 0, 60, 30), -1, "D0", 0),
        ):
            ls, ts = PlasticState(w), BinaryTableState(w)
            self.assertEqual(check_full_legal_domain(learner, ls, table, ts), 2)
            x, y = learner.respond(ls, (255, 0)), table.respond(ts, (255, 0))
            self.assertEqual(x.action, expected_action)
            self.assertEqual(y.action, expected_action)
            ls = learner.update(ls, x, reward)
            ts = table.update(ts, y, reward)
            self.assertEqual(ls.weights, ts.weights)
            self.assertEqual(ls.weights[0], expected_first)

    def test_non_e03_inputs_are_explicitly_excluded(self):
        table = IndependentBinaryTable(0)
        for x in ((0, 0), (255, 255), (128, 0), (0, 128), (True, 0)):
            with self.subTest(input=x):
                with self.assertRaises(ValueError):
                    table.respond(table.initial_state, x)


if __name__ == "__main__":
    unittest.main()
