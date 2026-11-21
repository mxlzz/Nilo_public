"""E09g.6 paired holdout diagnostics: immutable interventions and parity."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_context_protocol import (
    MAPPING_A, ZERO, blocks, evaluate_brain, train_brain,
)
from experiments.neurolab.e09_context_reset_diagnostics import (
    MODES, _intervene, evaluate_variant, run_seed, run_all,
)


class ContextResetDiagnosticsTests(unittest.TestCase):
    def test_immutable_factorial_interventions(self):
        brain = C1ContextBrain(2)
        state = brain.initial()
        outcomes = {mode: _intervene(state, 1, mode) for mode in MODES}
        for after in outcomes.values():
            self.assertEqual(after.dendrites, state.dendrites)
            self.assertEqual(after.tick, state.tick)
        self.assertIs(outcomes["C"], state)
        self.assertEqual(outcomes["N"].neuron_states, (80, 80))
        self.assertEqual(outcomes["N"].neuron_outputs, (0, 0))
        self.assertEqual(outcomes["W"].concept_outputs, (0, 126))
        self.assertEqual(outcomes["W"].neuron_states, state.neuron_states)
        self.assertEqual(outcomes["NW"].concept_outputs, (0, 126))
        self.assertEqual(state.concept_outputs, (0, 0))

    def test_invalid_mode_rejected(self):
        brain = C1ContextBrain(0)
        with self.assertRaises(ValueError):
            _intervene(brain.initial(), 0, "BAD")
        with self.assertRaises(ValueError):
            evaluate_variant(brain, brain.initial(), (0, 1), MAPPING_A, "BAD")

    def test_continuous_control_exactly_matches_g5(self):
        brain = C1ContextBrain(4)
        state, _ = train_brain(brain, brain.initial(), ZERO, blocks(4, 10000, 32),
                               MAPPING_A, learn=True)
        holdout = blocks(4, 30000, 16)
        actual = evaluate_variant(brain, state, holdout, MAPPING_A, "C")
        original = evaluate_brain(brain, state, holdout, MAPPING_A)
        for key in ("steady", "early", "overall"):
            self.assertAlmostEqual(actual[key], original[key])
        self.assertEqual(len(actual["by_position"]), 8)
        self.assertEqual(len(actual["by_context"]), 2)

    def test_seed_replay_is_deterministic(self):
        self.assertEqual(run_seed(16), run_seed(16))

    def test_20_seed_output_never_relabels_failed_g5(self):
        result = run_all()
        self.assertEqual(result["original_g5_good_both"], 12)
        self.assertEqual(result["original_g5_failing_seeds"], [0,2,3,4,8,16,17,19])
        self.assertEqual(result["n_seeds"], 20)
        for phase in ("first", "reversed"):
            self.assertEqual(set(result["mean"][phase]), set(MODES))
            self.assertEqual(set(result["paired_contrasts"][phase]), {"N", "W", "NW"})
            for mode in MODES:
                self.assertEqual(len(result["mean"][phase][mode]["by_position"]), 8)
        self.assertIn("does not fix g5", result["scope"])


if __name__ == "__main__":
    unittest.main()
