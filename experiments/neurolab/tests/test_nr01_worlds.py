"""Software-only smoke tests for NR01 evaluator world preregistration.

Uses toy seeds 0,1,42 ONLY. Never opens development/confirmation.
"""
import unittest

from experiments.neurolab.nr01_worlds import (
    counts, legal_latents, make_tape, seed_for, tape_digest,
    target_for_evaluator,
)


class TestNR01Worlds(unittest.TestCase):
    def test_A_balanced_train_and_holdout_disjoint(self):
        train = make_tape("A", 42, "unsupervised")
        test = make_tape("A", 42, "test")
        self.assertEqual(len(train), 1200)
        self.assertEqual(len(test), 160)
        self.assertEqual(set(counts(train)), set(legal_latents("A", test=False)))
        self.assertEqual(set(counts(test)), set(legal_latents("A", test=True)))
        self.assertTrue(all(n == 100 for n in counts(train).values()))
        self.assertTrue(all(n == 40 for n in counts(test).values()))
        self.assertTrue(set(counts(train)).isdisjoint(set(counts(test))))

    def test_B_balanced_train_and_holdout_disjoint(self):
        train = make_tape("B", 1, "unsupervised")
        test = make_tape("B", 1, "test")
        self.assertEqual(len(train), 1200)
        self.assertEqual(len(test), 120)
        self.assertEqual(len(counts(train)), 24)
        self.assertEqual(len(counts(test)), 12)
        self.assertTrue(all(n == 50 for n in counts(train).values()))
        self.assertTrue(all(n == 10 for n in counts(test).values()))
        self.assertTrue(set(counts(train)).isdisjoint(set(counts(test))))

    def test_reproducibility_and_independent_noise(self):
        x = make_tape("A", 0, "feedback")
        y = make_tape("A", 0, "feedback")
        different_stage = make_tape("A", 0, "feedback", stage=1)
        self.assertEqual(tape_digest(x), tape_digest(y))
        self.assertNotEqual(tape_digest(x), tape_digest(different_stage))
        self.assertEqual(len(x), 64)
        self.assertTrue(all(len(z.observation) == 16
                            and all(0.0 <= v <= 1.0 for v in z.observation)
                            for z in x))

    def test_64_feedback_prefix_is_fixed_for_all_budgets(self):
        cases = make_tape("B", 1, "feedback")
        self.assertEqual(len(cases), 64)
        for n in (8, 16, 32):
            self.assertEqual(cases[:n], make_tape("B", 1, "feedback")[:n])
        self.assertEqual(len(make_tape("A", 0, "reversal")), 64)
        self.assertEqual(len(make_tape("B", 0, "feedback_b2")), 64)
        with self.assertRaises(ValueError):
            make_tape("A", 0, "feedback_b2")
        with self.assertRaises(ValueError):
            make_tape("B", 0, "reversal")

    def test_evaluator_target_not_in_observation(self):
        # This is a contract check: the caller must pass only observation.
        a = make_tape("A", 42, "feedback")[0]
        self.assertEqual(type(a.observation), tuple)
        self.assertEqual(len(a.observation), 16)
        self.assertEqual(target_for_evaluator("A", (0, 3), task="original"), "D0")
        self.assertEqual(target_for_evaluator("A", (0, 3), task="reversed"), "D1")
        self.assertEqual(target_for_evaluator("B", (0, 1, 2), task="B1"), "D0")
        self.assertEqual(target_for_evaluator("B", (0, 1, 2), task="B2"), "D1")

    def test_reserved_seeds_guard(self):
        for seed in (1400, 1419, 24000, 24019):
            with self.subTest(seed=seed):
                with self.assertRaises(ValueError):
                    make_tape("A", seed, "feedback")
        with self.assertRaises(ValueError):
            make_tape("A", 1400, "feedback", allow_confirmation=True)
        # Deliberately DO NOT use allow_confirmation=True on 24000..24019.

    def test_unknown_params_rejected(self):
        for invalid in ("C", None):
            with self.assertRaises(ValueError):
                legal_latents(invalid, test=False)
        with self.assertRaises(ValueError):
            seed_for(0, "A", "unknown")
        with self.assertRaises(ValueError):
            seed_for(0, "A", "parameters", -1)


if __name__ == "__main__":
    unittest.main()
