"""I3c7f audit is read-only, post hoc and anchored to original 20-seed SHA."""
from copy import deepcopy
import unittest

from experiments.neurolab.e09_i3c7e_loss_factorial import run_seed
from experiments.neurolab.e09_i3c7f_weight_persistence_audit import (
    EXPECTED_PER_SEED_SHA256,EXPECTED_SEEDS,QUARTERS,
    _digest,_first_or_none,_one_seed_window,validate_source,
)


class FunctionalMemoryAuditContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row=run_seed(1600)

    def test_preserve_original_seed_coverage_and_short_fixed_windows(self):
        self.assertEqual(EXPECTED_SEEDS,tuple(range(1600,1620)))
        self.assertEqual(len(EXPECTED_PER_SEED_SHA256),64)
        self.assertEqual(QUARTERS,((1,32),(33,64),(65,96),(97,128)))
        self.assertEqual(sum(b-a+1 for a,b in QUARTERS),128)

    def test_window_metrics_match_raw_neural_states_and_context_denominators(self):
        f=self.row["reversed"]["arms"]["M16"]["readouts"][
            "active_no_new_reward"]["frames"]
        self.assertEqual(len(f),128)
        summaries=[_one_seed_window(f,a,b) for a,b in QUARTERS]
        self.assertEqual(sum(s["n_ticks"] for s in summaries),128)
        self.assertEqual(sum(s["correct"] for s in summaries),
                         sum(x["correct"] for x in f))
        self.assertEqual(
            sum(sum(s["context_n"].values()) for s in summaries),128)
        for summary in summaries:
            self.assertTrue(0<=summary["accuracy"]<=1)
            self.assertTrue(0<=summary["mean_live"]<=8)
            self.assertTrue(0<=summary["mean_live_stw_ge5"]<=8)
            self.assertTrue(0<=summary["mean_live_ltw_positive"]<=8)
            self.assertLessEqual(summary["mean_live_stw_ge5"],summary["mean_live"])
            self.assertLessEqual(summary["mean_live_ltw_positive"],summary["mean_live"])

    def test_raw_frames_have_no_new_evaluator_feedback(self):
        for phase in ("first","reversed"):
            for mode in ("D0","D16","M0","M16","FD","FM"):
                for readout in ("frozen","active_no_new_reward"):
                    obs=self.row[phase]["arms"][mode]["readouts"][readout]
                    self.assertEqual(obs["new_feedback_events"],0)
                    self.assertTrue(all(
                        f["external_feedback_created"] is False
                        for f in obs["frames"]
                    ))

    def test_first_event_is_not_claimed_irreversible(self):
        f=self.row["reversed"]["arms"]["M16"]["readouts"][
            "active_no_new_reward"]["frames"]
        first=_first_or_none(f,lambda z:z["n_live"]==0)
        if first is not None:
            self.assertTrue(1<=first<=128)
        else:
            self.assertTrue(all(z["n_live"]>0 for z in f))
        self.assertIsNone(_first_or_none(f,lambda _:False))

    def test_reject_partially_recovered_cohort_without_full_digest(self):
        row=self.row
        synthetic={
            "protocol":"NL-EXP-I3c7e-v1",
            "seeds":[1600],"n_seeds":1,
            "modes":["D0","D16","M0","M16","FD","FM"],
            "phases":["first","reversed"],
            "readouts":["frozen","active_no_new_reward"],
            "holdout_ticks_per_readout":128,
            "gates":{"G05":"OPEN"},
            "per_seed":[row],
            "per_seed_sha256":{"1600":_digest(row)},
        }
        with self.assertRaisesRegex(AssertionError,"experiment contract"):
            validate_source(synthetic)
        synthetic["seeds"]=list(EXPECTED_SEEDS)
        synthetic["n_seeds"]=20
        with self.assertRaisesRegex(AssertionError,"not all original"):
            validate_source(synthetic)


if __name__=="__main__":
    unittest.main()
