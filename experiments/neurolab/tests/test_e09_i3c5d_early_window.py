"""I3c.5d: no tuning, timing fork and independent numeric witnesses."""
import unittest

from experiments.neurolab.e09_i3c5d_early_window import (
    SEEDS, MAPS, MODES, TRUNK_TICK, END_TICK, SNAPSHOTS,
    shared_trunk, run_episode, run_seed, run_all,
)
from experiments.neurolab.e09_i3_metabolic_protocol import selected_genes


class EarlyWindowContracts(unittest.TestCase):
    def test_unseen_development_cohort_and_timing_are_frozen(self):
        self.assertEqual(SEEDS,tuple(range(1300,1320)))
        self.assertEqual(set(MAPS),{"A","B"})
        self.assertEqual(MODES,("N","D0","D3"))
        self.assertEqual((TRUNK_TICK,END_TICK),(4,128))
        self.assertEqual(SNAPSHOTS,(4,5,6,8,9,10,16,128))
        for bad in (1299,1320,900,1200,1400):
            with self.assertRaises(ValueError):
                run_episode(bad,0,"A")
        with self.assertRaises(ValueError):
            run_episode(1300,2,"A")
        with self.assertRaises(ValueError):
            run_episode(1300,0,"not-a-mapping")

    def test_strength_is_positive_before_any_feedback(self):
        receptors,reactions=selected_genes()
        brain,trunk,action=shared_trunk(1300,0,receptors,reactions)
        self.assertEqual((trunk.brain.tick,trunk.chemistry.tick),(4,4))
        self.assertEqual(len(trunk.brain.dendrites),8)
        self.assertEqual(sum(s.strength>0 for s in trunk.brain.dendrites),8)
        self.assertIn(action,("D0","D1",None))
        self.assertEqual(brain.seed,1300)

    def test_three_branches_one_action_and_strict_same_clock(self):
        ep=run_episode(1300,0,"A")
        self.assertEqual(set(ep["branches"]),set(MODES))
        self.assertEqual(ep["trunk"]["strength_positive"],8)
        for mode in MODES:
            info=ep["branches"][mode]
            self.assertEqual(len(info["frames"]),124)
            self.assertEqual(info["frames"][0]["tick"],5)
            self.assertEqual(info["frames"][-1]["tick"],128)
            self.assertEqual(set(info["snapshots"]),set(map(str,SNAPSHOTS)))
            self.assertEqual(set(info["readouts"]),{"9","16","128"})
            self.assertEqual(info["delivered"],int(mode!="N" and
                                      ep["reference_action"] is not None))
            self.assertEqual(len(info["effect_trace"]),124)
            for t in ("9","16","128"):
                self.assertEqual(info["readouts"][t]["end_tick"],int(t)+4)
                self.assertIn(info["readouts"][t]["correct"],(0,1))
        self.assertEqual(ep["branches"]["N"]["effect_incremental_total"],0)
        self.assertEqual(ep["branches"]["N"]["chem_auc"],[0,0])
        self.assertIsNone(ep["branches"]["N"]["first_chem_positive_tick"])

    def test_evaluator_mappings_never_change_original_trunk(self):
        by_seed=run_seed(1301)
        self.assertEqual(len(by_seed["episodes"]),4)
        for target in (0,1):
            a,b=[x for x in by_seed["episodes"] if x["target"]==target]
            self.assertEqual(
                a["trunk_checkpoint_sha256"],
                b["trunk_checkpoint_sha256"],
            )
            self.assertEqual(a["reference_action"],b["reference_action"])

    def test_replay_and_hashes_are_deterministic(self):
        a=run_all((1302,))
        b=run_all((1302,))
        self.assertEqual(a,b)
        self.assertEqual((a["n_unique_trunks"],a["n_mapping_coordinates"],
                         a["n_branches"]),(2,4,12))
        self.assertEqual(len(a["per_seed_sha256"]),1)
        self.assertEqual(set(a["paired_contrasts"]),
                         {"D0_minus_N","D3_minus_N","D0_minus_D3"})
        self.assertEqual(a["gates"]["G05"],"OPEN")
        self.assertTrue(a["no_extra_gain_or_migration"])

    def test_reject_duplicate_or_borrowed_cohort(self):
        for invalid in ((1300,1300),(1200,),(),(1320,),[1300]):
            with self.assertRaises(ValueError):
                run_all(invalid)


if __name__=="__main__":
    unittest.main()
