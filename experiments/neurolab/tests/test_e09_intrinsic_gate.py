"""E09g10a tests: internal history only; no block/oracle in step function."""
from dataclasses import replace
import inspect
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_context_protocol import ZERO, REWARD
from experiments.neurolab.e09_intrinsic_gate import (
    InternalCreditState, step_intrinsic, run_seed, run_all,
)


class IntrinsicCreditTests(unittest.TestCase):
    def test_step_signature_has_no_boundary_or_target(self):
        args = set(inspect.signature(step_intrinsic).parameters)
        self.assertEqual(args, {"brain", "state", "current_sensory", "pending_chemistry"})

    def test_mismatch_suppresses_pulse_using_previous_decision_input(self):
        brain = C1ContextBrain(100)
        base = replace(brain.initial(), concept_outputs=(0, 126))
        state = InternalCreditState(base, last_choice_concepts=(126, 0))
        got = step_intrinsic(brain, state, current_sensory=1, pending_chemistry=REWARD)
        self.assertTrue(got.suppressed)
        self.assertEqual(got.applied_pulse, ZERO)
        no_chem = brain.step(base, 1, ZERO, learn=True)
        self.assertEqual(got.neural.after, no_chem.after)

    def test_same_context_keeps_pulse(self):
        brain = C1ContextBrain(100)
        base = replace(brain.initial(), concept_outputs=(0, 126))
        state = InternalCreditState(base, last_choice_concepts=(0, 126))
        got = step_intrinsic(brain, state, current_sensory=1, pending_chemistry=REWARD)
        self.assertFalse(got.suppressed)
        self.assertEqual(got.applied_pulse, REWARD)

    def test_unknown_or_ambiguous_sources_dont_suppress(self):
        brain = C1ContextBrain(100)
        base = replace(brain.initial(), concept_outputs=(0, 126))
        for values in (None, (0, 0), (126, 126)):
            got = step_intrinsic(brain, InternalCreditState(base, values), 1, REWARD)
            self.assertFalse(got.suppressed)

    def test_zero_pulse_cannot_be_suppressed(self):
        brain = C1ContextBrain(100)
        base = replace(brain.initial(), concept_outputs=(0, 126))
        got = step_intrinsic(brain, InternalCreditState(base, (126, 0)), 1, ZERO)
        self.assertFalse(got.suppressed)

    def test_memory_bytes_validation(self):
        brain = C1ContextBrain(100)
        with self.assertRaises(ValueError):
            InternalCreditState(brain.initial(), (300, 0))
        with self.assertRaises(ValueError):
            InternalCreditState(brain.initial(), (126,))

    def test_two_unseen_seeds_exactly_equal_oracle_in_both_phases(self):
        for seed in (100, 119):
            with self.subTest(seed=seed):
                row = run_seed(seed)
                for phase in ("first", "reversed"):
                    self.assertEqual(row[phase]["metrics"]["G"], row[phase]["metrics"]["IG"])
                    self.assertEqual(row[phase]["intrinsic_suppressed"],
                                     row[phase]["external_suppressed"])
                    self.assertTrue(row[phase]["exact_brain_state_match"])

    def test_replay_deterministic(self):
        self.assertEqual(run_seed(101), run_seed(101))


if __name__ == "__main__":
    unittest.main()
