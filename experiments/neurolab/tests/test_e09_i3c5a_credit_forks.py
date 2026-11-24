"""I3c.5a preregistered scientific and software contracts."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_coupled_brain import initial_coupled
from experiments.neurolab.e09_i3_metabolic_protocol import selected_genes
from experiments.neurolab.e09_i3c5a_credit_forks import (
    SEEDS, MODES, TRUNK_TICK, END_TICK, initial_trunk,
    optional_precursor, inspect_synapses, run_episode, run_all,
)


class CreditForkTests(unittest.TestCase):
    def test_frozen_unseen_cohort_and_fixed_design(self):
        self.assertEqual(SEEDS, tuple(range(1200, 1220)))
        self.assertEqual(MODES, ("N", "D0", "D1", "D2", "D3"))
        self.assertEqual((TRUNK_TICK, END_TICK), (124, 256))
        for bad in (100, 300, 800, 900, 1199, 1220):
            with self.assertRaises(ValueError):
                run_episode(bad, 0, "A")
        with self.assertRaises(ValueError):
            run_episode(1200, 2, "A")
        with self.assertRaises(ValueError):
            run_episode(1200, 0, "X")

    def test_no_action_cannot_inject_or_modify_chemistry(self):
        receptors, _ = selected_genes()
        brain = C1ContextBrain(1200)
        before = initial_coupled(brain, receptors)
        after, deliveries = optional_precursor(before, None, None)
        self.assertIs(after, before)
        self.assertEqual(deliveries, 0)
        with self.assertRaises(ValueError):
            optional_precursor(before, "INVALID", True)

    def test_forks_share_identical_pre_feedback_trunk(self):
        receptors, reactions = selected_genes()
        b, before, action = initial_trunk(1200, 1, receptors, reactions)
        clone, other, other_action = initial_trunk(1200, 1, receptors, reactions)
        self.assertEqual(before, other)
        self.assertEqual(action, other_action)
        self.assertEqual(b.checkpoint(before.brain),
                         clone.checkpoint(other.brain))
        self.assertEqual((before.brain.tick, before.chemistry.tick),
                         (TRUNK_TICK, TRUNK_TICK))
        witness, effects, sus = inspect_synapses(before)
        self.assertEqual(len(witness), 8)
        self.assertEqual(len(effects), 8)
        self.assertEqual(len(sus), 8)

    def test_one_episode_has_no_leak_and_replayed_witness(self):
        row = run_episode(1200, 0, "A")
        self.assertEqual(row["trunk_tick"], TRUNK_TICK)
        self.assertEqual(set(row["branches"]), set(MODES))
        for mode, branch in row["branches"].items():
            self.assertEqual(len(branch["frames"]), END_TICK-TRUNK_TICK)
            self.assertEqual(branch["frames"][0]["tick"], TRUNK_TICK+1)
            self.assertEqual(branch["frames"][-1]["tick"], END_TICK)
            self.assertEqual(set(branch["gates"]), {"128", "256"})
            self.assertEqual(branch["delivered"],
                             int(mode != "N" and row["action"] is not None))
            self.assertGreaterEqual(branch["chemical_auc"][0], 0)
            self.assertGreaterEqual(branch["chemical_auc"][1], 0)
        self.assertIsNone(row["branches"]["N"]["target_fraction_attributed"])
        self.assertEqual(row["branches"]["N"]["effect_attributed_target"], 0)
        self.assertEqual(row["branches"]["N"]["effect_attributed_distractor"], 0)

    def test_same_seed_replays_and_partial_summary(self):
        one = run_all((1201,))
        other = run_all((1201,))
        self.assertEqual(one, other)
        self.assertEqual((one["n_trunks"], one["n_branches"]), (4, 20))
        self.assertEqual(len(one["per_seed_sha256"]), 1)
        self.assertEqual(len(one["per_seed"][0]["episodes"]), 4)
        self.assertEqual(set(one["timing_contrasts"]),
                         {"D0_minus_D1", "D0_minus_D2", "D0_minus_D3"})
        self.assertTrue(one["G05_G09_G00H"].startswith("OPEN"))
        for invalid in ((1200, 1200), (900,), [], (1220,)):
            with self.assertRaises(ValueError):
                run_all(invalid)


if __name__ == "__main__":
    unittest.main()
