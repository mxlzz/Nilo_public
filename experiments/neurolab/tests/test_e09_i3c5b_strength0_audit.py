"""I3c.5b read-only model audit: do not convert this to C1 historical proof."""
import unittest

from experiments.neurolab.e09_i3c5b_strength0_audit import audit


class ExhaustedSynapseWitnessTests(unittest.TestCase):
    def test_strength0_stw_nonzero_enters_signal_and_decision_input(self):
        result = audit()
        self.assertEqual(result["strength_before_signal"], 0)
        self.assertEqual(result["stw_before_signal"], 255)
        self.assertEqual(result["signal_at_strength0_with_stw0"], 0)
        self.assertGreater(result["signal_at_strength0_with_stw255"], 0)
        self.assertTrue(result["model_strength0_transmits_signal"])
        self.assertTrue(result["class_signal_propagates_to_WTA_input"])

    def test_zero_strength_numerical_transition_is_observed_not_assumed(self):
        result = audit()
        self.assertEqual(result["numerical_synapse_strength_before"], 0)
        self.assertIs(type(result["numerical_weight_changed_while_exhausted"]), bool)
        self.assertGreaterEqual(result["numerical_synapse_stw_after_tick1"], 0)
        self.assertGreaterEqual(result["numeric_reinforcement_effect_tick1"], 0)

    def test_do_not_close_historical_or_learning_gates(self):
        result = audit()
        self.assertIn("NOT VERIFIED", result["historical_strength0_input_gate"])
        self.assertEqual(result["G05_G09_G00H"], "OPEN")
        self.assertIn("Python reduction", result["limitations"])
        self.assertEqual(result, audit())


if __name__ == "__main__":
    unittest.main()
