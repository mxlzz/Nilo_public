"""I3c7e: exact E09g5 D0, six arms, loss16 sourced from receptor."""
import unittest

from experiments.neurolab.e09_i3c7e_loss_factorial import (
    SEEDS,UNUSED_CONFIRMATION_SEEDS,MODES,SPECS,PHASES,READOUTS,
    ArmState,_input_neural,run_seed,run_all,
)
from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_coupled_brain import initial_coupled
from experiments.neurolab.e09_i3_metabolic_protocol import selected_genes
from experiments.neurolab.e09_context_protocol import REWARD


class FactorialLossControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.one=run_seed(1600)

    def test_cohort_and_arms_frozen_before_data(self):
        self.assertEqual(SEEDS,tuple(range(1600,1620)))
        self.assertEqual(UNUSED_CONFIRMATION_SEEDS,tuple(range(1400,1420)))
        self.assertTrue(set(SEEDS).isdisjoint(UNUSED_CONFIRMATION_SEEDS))
        self.assertEqual(MODES,("D0","D16","M0","M16","FD","FM"))
        self.assertEqual(len(SPECS),6)
        self.assertEqual(len(PHASES),2)
        self.assertEqual(READOUTS,("frozen","active_no_new_reward"))

    def test_direct_loss16_uses_receptor_not_zeroed_pending_pulse(self):
        receptors,_=selected_genes()
        brain=C1ContextBrain(1600)
        state=ArmState(initial_coupled(brain,receptors),REWARD)
        self.assertEqual(_input_neural(state,"D0"),(255,0,0,0))
        self.assertEqual(_input_neural(state,"D16"),(255,0,16,16))
        self.assertEqual(_input_neural(state,"FD"),(255,0,16,16))
        self.assertEqual(_input_neural(state,"M0"),(0,0,0,0))
        self.assertEqual(_input_neural(state,"M16"),(0,0,16,16))
        self.assertEqual(_input_neural(state,"FM"),(0,0,16,16))

    def test_exact_existing_e09g5_golden_at_both_phases(self):
        for phase in ("first","reversed"):
            p=self.one[phase]
            self.assertTrue(p["golden_e09g5_neural_equal"])
            self.assertTrue(p["golden_e09g5_frozen_metrics_equal"])
            self.assertEqual(set(p["arms"]),set(MODES))
            self.assertEqual(len(p["train_blocks"]),32)
            self.assertEqual(len(p["holdout_blocks"]),16)
            for mode in MODES:
                info=p["arms"][mode]
                self.assertEqual(info["training"]["n_ticks"],256)
                self.assertEqual(set(info["readouts"]),set(READOUTS))
                self.assertEqual(info["readouts"]["frozen"]["n_ticks"],128)
                self.assertEqual(info["readouts"]["active_no_new_reward"]["n_ticks"],128)
                self.assertEqual(
                    info["readouts"]["frozen"]["new_feedback_events"],0
                )
                self.assertEqual(
                    info["readouts"]["active_no_new_reward"]["new_feedback_events"],0
                )
                self.assertEqual(len(info["training"]["frames"]),256)

    def test_frozen_controls_never_train_synapses(self):
        for phase in ("first","reversed"):
            for mode in ("FD","FM"):
                tr=self.one[phase]["arms"][mode]["training"]
                self.assertEqual(tr["synapse_events"],
                     {"effect":0,"gain":0,"lose":0,"lost_connection":0})
                self.assertEqual(tr["final_neural"]["strengths"],[2]*8)
                self.assertEqual(tr["final_neural"]["stw"],[0]*8)

    def test_holdout_is_cloned_not_an_extra_training_period(self):
        for phase in ("first","reversed"):
            for mode in MODES:
                tr=self.one[phase]["arms"][mode]["training"]
                for readout in READOUTS:
                    ev=self.one[phase]["arms"][mode]["readouts"][readout]
                    self.assertEqual(ev["n_ticks"],128)
                    self.assertGreater(ev["final_neural"]["tick"],
                                       tr["final_neural"]["tick"])
                    self.assertEqual(ev["chemical_input_auc"][0]>=0,True)
                    self.assertTrue(0<=ev["steady"]<=1)

    def test_result_gates_and_seed_clustering(self):
        r=run_all((1601,))
        self.assertEqual(r["n_seeds"],1)
        self.assertEqual(r["seeds"],[1601])
        self.assertEqual(r["train_ticks_per_phase"],256)
        self.assertEqual(r["holdout_ticks_per_readout"],128)
        self.assertEqual(len(r["per_seed_sha256"]),1)
        self.assertEqual(r["gates"]["G05"],"OPEN")
        self.assertIn("NOT equivalent",r["equal_dose_caveat"])
        within=r["paired_contrasts"]["first"][
            "frozen_minus_active_within_each_mode"]["M16"]
        self.assertEqual(within["n_seeds"],1)
        self.assertEqual(within["ci95"],[within["mean"],within["mean"]])
        self.assertEqual(set(r["paired_contrasts"]["first"]),{
            "D0_minus_D16","M0_minus_M16","D0_minus_M0","D16_minus_M16",
            "D16_minus_FD","M16_minus_FM",
            "frozen_minus_active_within_each_mode",
        })

    def test_invalid_seed_duplication_and_holdout_leak_rejected(self):
        for bad in ((1600,1600),(1400,),(1620,),(),[1600]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    run_all(bad)
        with self.assertRaises(ValueError):
            run_seed(1400)


if __name__=="__main__":
    unittest.main()
