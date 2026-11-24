"""E09g8: preregistered omission schedule, matched counts, g5 parity."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_context_protocol import (
    ZERO, MAPPING_A, MAPPING_B, blocks, train_brain,
)
from experiments.neurolab.e09_paired_pulse_protocol import (
    MODES, train_variant, run_seed, run_all,
)


class PairedPulseTests(unittest.TestCase):
    def test_original_c_matches_g5_states_and_pending_across_phases(self):
        seed = 16
        brain = C1ContextBrain(seed)
        ref = brain.initial()
        mine = brain.initial()
        ref_pending = mine_pending = ZERO
        last_context = None
        for salt, mapping in ((10000, MAPPING_A), (20000, MAPPING_B)):
            schedule = blocks(seed, salt, 32)
            ref, ref_pending = train_brain(brain, ref, ref_pending,
                                            schedule, mapping, learn=True)
            mine, mine_pending, last_context, suppression = train_variant(
                brain, mine, mine_pending, last_context,
                schedule, mapping, mode="C",
            )
            self.assertEqual(mine, ref)
            self.assertEqual(mine_pending, ref_pending)
            self.assertEqual(suppression["scheduled_omissions"], 0)

    def test_suppression_positions_have_equal_opportunities(self):
        schedule = (0, 0, 1, 1, 0, 0)
        counts = {}
        for mode in MODES:
            brain = C1ContextBrain(3)
            _, _, _, counts[mode] = train_variant(
                brain, brain.initial(), ZERO, None,
                schedule, MAPPING_A, mode=mode,
            )
        self.assertEqual(counts["C"]["scheduled_omissions"], 0)
        self.assertEqual(counts["G"]["scheduled_omissions"], 2)
        self.assertEqual(counts["S"]["scheduled_omissions"], 2)
        self.assertEqual(counts["G"]["nonzero_omissions"],
                         counts["S"]["nonzero_omissions"])

    def test_invalid_mode_rejected(self):
        brain = C1ContextBrain(0)
        with self.assertRaises(ValueError):
            train_variant(brain, brain.initial(), ZERO, None, (0, 1),
                          MAPPING_A, mode="BAD")

    def test_per_seed_is_deterministic(self):
        self.assertEqual(run_seed(2), run_seed(2))

    def test_twenty_seed_baseline_and_matched_controls(self):
        result = run_all()
        self.assertEqual(result["n_seeds"], 20)
        self.assertEqual(result["g5_like_joint_steady_ge_0_90"]["C"], 12)
        for phase in ("first", "reversed"):
            self.assertEqual(result["suppression_counts"][phase]["G"],
                             result["suppression_counts"][phase]["S"])
            self.assertEqual(result["suppression_counts"][phase]["C"]
                             ["nonzero_omissions"], 0)
            self.assertEqual(len(result["paired_steady_deltas"][phase]
                                 ["G_minus_S"]), 20)
        self.assertIsInstance(result["primary_practical_indicator"]["met"], bool)


if __name__ == "__main__":
    unittest.main()
