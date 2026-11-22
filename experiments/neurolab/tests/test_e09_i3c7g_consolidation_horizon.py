"""I3c.7g contract: C1 LTW gates only, exact nested sequences and original controls."""
import unittest

from experiments.neurolab.e09_i3c7g_consolidation_horizon import (
    SEEDS,CONFIRMATION_SEEDS,MODES,PHASE_B_SHORT_BLOCKS,PHASE_B_LONG_BLOCKS,
    sequences,run_seed,run_all,
)


class ConsolidationHorizonContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row=run_seed(1700)

    def test_new_cohort_and_precommitted_reversal_budgets(self):
        self.assertEqual(SEEDS,tuple(range(1700,1720)))
        self.assertTrue(set(SEEDS).isdisjoint(CONFIRMATION_SEEDS))
        self.assertEqual(MODES,("M0","M16","D0","FM"))
        self.assertEqual((PHASE_B_SHORT_BLOCKS,PHASE_B_LONG_BLOCKS),(32,80))
        with self.assertRaises(ValueError):
            run_seed(1400)
        with self.assertRaises(ValueError):
            run_seed(1620)
        with self.assertRaises(ValueError):
            run_seed(1720)

    def test_short_is_identical_prefix_of_long_and_balanced(self):
        a,a_hold,short,extension,long,b_hold=sequences(1700)
        self.assertEqual(len(a),32)
        self.assertEqual(len(a_hold),16)
        self.assertEqual(len(short),32)
        self.assertEqual(len(extension),48)
        self.assertEqual(len(long),80)
        self.assertEqual(len(b_hold),16)
        self.assertEqual(tuple(long[:32]),tuple(short))
        self.assertEqual((short.count(0),short.count(1)),(16,16))
        self.assertEqual((extension.count(0),extension.count(1)),(24,24))
        self.assertEqual((long.count(0),long.count(1)),(40,40))
        self.assertEqual(tuple(long),tuple(self.row["source_sequence_b_long"]))

    def test_exact_e09g5_short_and_same_A_checkpoint(self):
        row=self.row
        self.assertTrue(row["D0_e09g5_exact_reference"])
        for mode in MODES:
            a=row["modes"][mode]["first"]
            short=row["modes"][mode]["short"]
            long=row["modes"][mode]["long"]
            self.assertEqual(a["end_weights"]["tick"],256)
            self.assertEqual(short["end_weights"]["tick"],512)
            self.assertEqual(long["end_weights"]["tick"],896)
            self.assertEqual(
                short["after_training_sha256"],
                long["initial_short_prefix_sha256"],
            )
            self.assertEqual(short["training"]["n_ticks"],256)
            self.assertEqual(long["training"]["n_ticks"],640)
            for key in ("frozen","active_no_new_reward"):
                self.assertEqual(short["readouts"][key]["n_ticks"],128)
                self.assertEqual(long["readouts"][key]["n_ticks"],128)
                self.assertEqual(short["readouts"][key]["new_feedback_events"],0)
                self.assertEqual(long["readouts"][key]["new_feedback_events"],0)
                self.assertEqual(a["readouts"][key]["new_feedback_events"],0)

    def test_ltw_rate128_mathematical_bound_short_and_frozen_negative(self):
        for mode in MODES:
            short=self.row["modes"][mode]["short"]["end_weights"]
            long=self.row["modes"][mode]["long"]["end_weights"]
            self.assertTrue(all(x<=4 for x in short["ltws"]))
            self.assertTrue(all(x<=7 for x in long["ltws"]))
            self.assertEqual(short["n_live_ltw_ge5"],0)
        self.assertEqual(self.row["modes"]["FM"]["short"]["end_weights"]["ltws"],[0]*8)
        self.assertEqual(self.row["modes"]["FM"]["long"]["end_weights"]["ltws"],[0]*8)

    def test_result_seed_cluster_and_all_gates_open(self):
        result=run_all((1701,))
        self.assertEqual(result["n_seeds"],1)
        self.assertEqual(result["phaseB_short_ticks"],256)
        self.assertEqual(result["phaseB_long_ticks"],640)
        self.assertEqual(result["post_reversal_LTW_gates"]["long"],
                         [384,512,640,768,896])
        self.assertEqual(len(result["per_seed_sha256"]),1)
        self.assertEqual(set(result["paired_long_minus_short"]),set(MODES))
        self.assertEqual(result["gates"]["G05"],"OPEN")
        self.assertIn("Extra practice",result["limitations"])
        self.assertEqual(
            result["paired_long_minus_short"]["M0"]["active_no_new_reward"]["n_seeds"],1
        )

    def test_invalid_seed_multiplicity_rejected(self):
        for invalid in ((1700,1700),(),[1700],(1400,),(1720,)):
            with self.subTest(cohort=invalid):
                with self.assertRaises(ValueError):
                    run_all(invalid)


if __name__=="__main__":
    unittest.main()
