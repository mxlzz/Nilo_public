"""I3b2a strength/connection loss witness, preserving original I3b2."""
import unittest

from experiments.neurolab.e09_i3b2a_strength_witness import (
    classify_ltw_change,replay_episode,run_all
)


class StrengthLossWitnessTests(unittest.TestCase):
    def test_off_gate_ltw_drop_must_have_lost_connection(self):
        with self.assertRaisesRegex(AssertionError,"without connection loss"):
            classify_ltw_change(
                old=2,numeric=2,final=0,
                lost_connection=False,tick=130)
        with self.assertRaisesRegex(AssertionError,"outside update gate"):
            classify_ltw_change(
                old=2,numeric=1,final=1,
                lost_connection=False,tick=130)
        out=classify_ltw_change(
            old=2,numeric=2,final=0,
            lost_connection=True,tick=130)
        self.assertEqual(out["ltw_cleared_by_strength_units"],2)
        self.assertEqual(out["ltw_lost_positive"],1)

    def test_no_atrophy_no_ltw_clear(self):
        x=classify_ltw_change(
            old=2,numeric=2,final=2,
            lost_connection=False,tick=130)
        self.assertEqual(x["ltw_cleared_by_strength_units"],0)
        with self.assertRaisesRegex(AssertionError,"did not reset"):
            classify_ltw_change(
                old=2,numeric=2,final=2,
                lost_connection=True,tick=130)

    def test_one_episode_replays_original_stw_ltw_and_strength(self):
        row=replay_episode(400,0,"A")
        self.assertTrue(row["reproduced_all_original_brain_transitions"])
        self.assertEqual(set(row["modes"]),{"N","E1","L1","E4","L4"})
        for mode,x in row["modes"].items():
            self.assertEqual(x["ltw_final_128"]-x["ltw_final_136"],
                             x["ltw_reset_units_129_to_136"])
            self.assertEqual([t["tick"] for t in x["ticks"]],list(range(125,137)))
            self.assertEqual(len(x["ticks"][0]["all_synapses"]),8)

    def test_new_observer_only_reuses_existing_cohort(self):
        d=run_all((400,))
        self.assertEqual(d["seeds"],[400])
        self.assertEqual(d["episode_count"],4)
        self.assertTrue(d["all_absent_gate_drops_accounted"])
        self.assertIn("posthoc",d["type"])
        self.assertEqual(d["totals"]["N"]["ltw_final_128"],0)


if __name__=="__main__":
    unittest.main()
