"""E06 tests: pair-detection and holdout XOR with frozen baselines."""
import json
import unittest

from experiments.neurolab.concepts import ConceptLearner, ConceptWeights, PAIR_FEATURES
from experiments.neurolab.e06_protocol import (
    PATTERNS, TARGET, encode, evaluate, memory_baseline, run_all, run_seed,
    sequence, train,
)


class ConceptTests(unittest.TestCase):
    def test_exactly_one_pair_detected_and_context_ignored(self):
        learner = ConceptLearner(1, mode="pair")
        state = learner.initial()
        for i, pattern in enumerate(PATTERNS):
            bare = learner.respond(state, encode(pattern, 0))
            contextual = learner.respond(state, encode(pattern, 1))
            self.assertEqual(bare.active, (i,))
            self.assertEqual(contextual.active, (i,))
            self.assertEqual(bare.scores, contextual.scores)
            self.assertEqual(bare.action, contextual.action)
        self.assertEqual(len(PAIR_FEATURES), 4)

    def test_no_response_mapping_in_model(self):
        learner = ConceptLearner(2)
        self.assertNotIn("TARGET", vars(learner))
        self.assertFalse(hasattr(learner, "correct_action"))
        self.assertEqual(set(TARGET.values()), {"D0", "D1"})

    def test_feedback_only_selected_weight(self):
        learner = ConceptLearner(3)
        state = learner.initial()
        choice = learner.respond(state, encode((0, 2), 0))
        after = learner.update(state, choice, -1)
        changed = [(i, j) for i in range(4) for j in range(2)
                   if state.edges[i][j] != after.edges[i][j]]
        self.assertLessEqual(len(changed), 1)
        if changed:
            self.assertEqual(changed[0], (0, 0 if choice.action == "D0" else 1))
        self.assertEqual(after.trials, 1)

    def test_frozen_weights_stay_frozen(self):
        learner = ConceptLearner(4)
        start = learner.initial()
        after = train(learner, start, sequence(4, context=0, repetitions=30, salt=6000),
                      context=0, learn=False)
        self.assertEqual(start.edges, after.edges)
        self.assertEqual(after.trials, 120)

    def test_exact_memory_fails_on_new_context(self):
        train_seq = sequence(5, context=0, repetitions=30, salt=6000)
        test_seq = sequence(5, context=1, repetitions=20, salt=7000)
        self.assertEqual(memory_baseline(train_seq, test_seq), .5)

    def test_balanced_holdout_and_no_plasticity(self):
        learner = ConceptLearner(6)
        state = learner.initial()
        holdout = sequence(6, context=1, repetitions=20, salt=7000)
        self.assertEqual(len(holdout), 80)
        before = state
        evaluate(learner, state, holdout, context=1)
        self.assertEqual(state, before)

    def test_invalid_inputs_and_feedback(self):
        learner = ConceptLearner(7)
        state = learner.initial()
        for bits in ((1, 0, 1), (1, 0, 1, 0, True), (1, 0, 1, 0, 2)):
            with self.assertRaises(ValueError):
                learner.respond(state, bits)
        with self.assertRaises(ValueError):
            learner.update(state, learner.respond(state, encode((0, 2), 0)), 0)
        with self.assertRaises(ValueError):
            ConceptLearner(7, mode="invalid")
        with self.assertRaises(ValueError):
            ConceptWeights(((0,0),(0,0)))

    def test_stale_choice_cannot_be_updated(self):
        learner = ConceptLearner(8)
        state = learner.initial()
        choice = learner.respond(state, encode((0, 2), 0))
        updated = learner.update(state, choice, +1)
        with self.assertRaises(ValueError):
            learner.update(updated, choice, +1)

    def test_seed_deterministic(self):
        self.assertEqual(run_seed(9), run_seed(9))

    def test_preregistered_gate(self):
        data = run_all()
        self.assertEqual(data["n_seeds"], 20)
        self.assertTrue(data["passed"], json.dumps(data, indent=2))
        self.assertGreaterEqual(data["at_least_90_percent"], 18)
        self.assertGreaterEqual(data["advantage_vs_memory"], .20)
        self.assertGreaterEqual(data["advantage_vs_singleton"], .15)


if __name__ == "__main__":
    unittest.main()
