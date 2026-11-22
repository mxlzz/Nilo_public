"""Tests for pre-registered E09.05-TAB1 exact E06 tabular equivalence."""
import unittest

from experiments.neurolab.concepts import ConceptLearner, ConceptWeights
from experiments.neurolab.e06_protocol import PATTERNS, encode
from experiments.neurolab.e09_pair_tabular_equivalence import (
    IndependentPairTable, PairTableState, check_entire_e06_domain, run_all,
)


class TestE09PairTabularEquivalence(unittest.TestCase):
    def test_20_development_seeds_original_train_holdout_reversal(self):
        d = run_all()
        self.assertEqual(d["protocol"], "E09.05-TAB1-v1")
        self.assertEqual(d["seeds"], list(range(20)))
        self.assertTrue(d["all_equal"])
        self.assertEqual(d["discrepancies"], 0)
        self.assertEqual(d["domain_comparisons"], 38720)
        self.assertEqual(d["original_holdout_comparisons"], 1600)
        self.assertEqual(d["learning_updates"], 4800)
        self.assertFalse(d["confirmatory_cohort_used"])
        for r in d["per_seed"]:
            self.assertEqual(r["final_trials"], 240)
            self.assertEqual(len(r["final_weights"]), 4)

    def test_context_bit_irrelevant_and_rows_match(self):
        learner, table = ConceptLearner(8), IndependentPairTable(8)
        cs, ts = learner.initial(), table.initial_state
        self.assertEqual(check_entire_e06_domain(learner, cs, table, ts), 8)
        for pair in PATTERNS:
            a = learner.respond(cs, encode(pair, 0))
            b = learner.respond(cs, encode(pair, 1))
            self.assertEqual(a.action, b.action)
            self.assertEqual(a.scores, b.scores)
            self.assertEqual(table.respond(ts, encode(pair, 0)).row,
                             table.respond(ts, encode(pair, 1)).row)

    def test_tie_and_clamped_weight_updates(self):
        learner, table = ConceptLearner(5), IndependentPairTable(5)
        for value, reward, expected in ((0, -1, 0), (255, +1, 255)):
            arr = tuple((value, value) for _ in range(4))
            cs = ConceptWeights(arr)
            ts = PairTableState(arr)
            self.assertEqual(check_entire_e06_domain(learner, cs, table, ts), 8)
            x = encode(PATTERNS[0], 1)
            c, t = learner.respond(cs, x), table.respond(ts, x)
            self.assertEqual(c.action, "D0")
            self.assertEqual(t.action, "D0")
            cs, ts = learner.update(cs, c, reward), table.update(ts, t, reward)
            self.assertEqual(cs.edges, ts.weights)
            self.assertEqual(cs.edges[0][0], expected)

    def test_out_of_domain_is_not_claimed_equivalent(self):
        table = IndependentPairTable(0)
        with self.assertRaises(ValueError):
            table.respond(table.initial_state, (0, 0, 1, 0, 0))
        with self.assertRaises(ValueError):
            table.respond(table.initial_state, (1, 1, 0, 1, 1))
        with self.assertRaises(ValueError):
            table.respond(table.initial_state, (1, 0, 1, 0, 2))
        with self.assertRaises(ValueError):
            table.respond(table.initial_state, (True, 0, 1, 0, 0))


if __name__ == "__main__":
    unittest.main()
