"""E09g10b integrity tests: stimulus timing, causal Q, frozen synapses, replay."""
import unittest
from unittest.mock import Mock
from types import SimpleNamespace

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_context_protocol import ZERO, REWARD, MAPPING_A
from experiments.neurolab.e09_intrinsic_gate import InternalCreditState
from experiments.neurolab.e09_delayed_distractors_protocol import (
    SEEDS, MODES, TRAIN_REPEATS, HOLDOUT_REPEATS, trials,
    neural_phase, train_tabular_q, run_seed,
)


class DelayedDistractorTests(unittest.TestCase):
    def test_disjoint_seed_partition(self):
        self.assertEqual(SEEDS, tuple(range(120, 160)))
        self.assertFalse(set(SEEDS).intersection(range(120)))

    def test_exact_balanced_context_delay_combinations(self):
        from collections import Counter
        for salt, repeats in ((50000, TRAIN_REPEATS), (70000, HOLDOUT_REPEATS)):
            schedule = trials(120, salt, repeats)
            self.assertEqual(len(schedule), 6 * repeats)
            self.assertEqual(set(Counter(schedule).values()), {repeats})
            self.assertEqual(schedule, trials(120, salt, repeats))
        self.assertNotEqual(trials(120, 50000, TRAIN_REPEATS),
                            trials(120, 60000, TRAIN_REPEATS))

    def test_exact_reward_tick_and_single_scored_target(self):
        brain = C1ContextBrain(120)
        state = brain.initial()
        calls = []
        def captured(current, context, chemicals, *, learn):
            calls.append((context, chemicals, learn))
            return SimpleNamespace(after=current, action="D0")
        brain.step = Mock(side_effect=captured)
        _, metrics = neural_phase(brain, state, ((0, 2),), MAPPING_A, "C", learn=True)
        self.assertEqual(calls, [(0, ZERO, True)]*4 +
                         [(1, ZERO, True)]*2 + [(1, REWARD, True)])
        self.assertEqual(metrics["target_choices"], 1)
        self.assertEqual(metrics["overall"], 1.0)
        self.assertEqual(metrics["delivered_nonzero_pulses"], 1)
        self.assertEqual(metrics["neural_ticks"], 7)

    def test_holdout_has_no_plasticity_or_reward(self):
        brain = C1ContextBrain(120)
        initial = brain.initial()
        after, metrics = neural_phase(brain, initial, ((1, 3),), MAPPING_A,
                                      "C", learn=False)
        self.assertEqual(initial, brain.initial())
        self.assertEqual(after.dendrites, initial.dendrites)
        self.assertEqual(metrics["delivered_nonzero_pulses"], 0)
        self.assertEqual(after.tick, 8)

    def test_intrinsic_holdout_preserves_memorized_history(self):
        brain = C1ContextBrain(120)
        initial = InternalCreditState(brain.initial())
        after, metrics = neural_phase(brain, initial, ((0, 1),), MAPPING_A,
                                      "IG", learn=False)
        self.assertEqual(initial.brain.tick, 0)
        self.assertEqual(after.brain.dendrites, initial.brain.dendrites)
        self.assertEqual(after.brain.tick, 6)
        self.assertEqual(metrics["suppressed_nonzero_pulses"], 0)

    def test_tabular_credit_only_changes_original_target(self):
        q = [[0.0, 0.0], [0.0, 0.0]]
        after, tick, log = train_tabular_q(q, ((0, 3),), MAPPING_A,
                                            seed=120, choice_tick=0)
        self.assertEqual(tick, 1)
        self.assertEqual(log["updates"], 1)
        self.assertEqual(log["causal_provenance"][0][:3], (0, 3, 0))
        self.assertEqual(after[1], [0, 0])
        self.assertEqual(sum(x != 0 for x in after[0]), 1)

    def test_replay_and_frozen_invariant_two_phases(self):
        a = run_seed(120)
        b = run_seed(120)
        self.assertEqual(a, b)
        for phase in ("first", "reversed"):
            for mode in MODES:
                self.assertEqual(a[phase]["holdout"][mode]["target_choices"], 36)
            self.assertEqual(a[phase]["training"]["Q"]["updates"], 60)
            self.assertEqual(a[phase]["training"]["F"]
                             ["delivered_nonzero_pulses"], 0)

    def test_reversal_is_not_reset_between_phases(self):
        result = run_seed(121)
        for mode in ("C", "IG", "F"):
            self.assertEqual(result["first"]["training"][mode]["neural_ticks"],
                             result["reversed"]["training"][mode]["neural_ticks"])
            self.assertEqual(result["first"]["training"][mode]["neural_ticks"],
                             60 * 7)
        self.assertTrue(0 <= result["reversed"]["holdout"]["C"]["overall"] <= 1)


if __name__ == "__main__":
    unittest.main()
