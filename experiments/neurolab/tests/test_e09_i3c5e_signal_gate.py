"""Post hoc I3c.5e numerical oracles; no change to C1 model or reward."""
import unittest

from experiments.neurolab.e09_i3c5e_signal_gate import (
    evaluate_gate, reference_fixture, _probe_decision_score,
)


class MicroEffectPropagationOracles(unittest.TestCase):
    def test_frozen_original_evidence_has_all_twenty_sha(self):
        evidence=reference_fixture()
        self.assertEqual(len(evidence["per_seed_sha256"]),20)
        self.assertEqual(evidence["max_effect_per_synapse_per_tick"],1)
        self.assertEqual(evidence["readout_action_changes_vs_N"],
             {"D0":{"9":0,"16":0,"128":0},
              "D3":{"9":0,"16":0,"128":0}})

    def test_concept_output_and_exact_positive_conduction_threshold(self):
        r=evaluate_gate()
        self.assertEqual(r["concept_source_output"],126)
        self.assertEqual(r["min_positive_decision_class_signal_stw"],5)
        self.assertEqual(r["signal_for_stw_0"],0)
        self.assertEqual(r["signal_for_stw_1"],0)
        self.assertGreater(r["signal_for_stw_threshold"],0)

    def test_fixed_score_readout_ignores_unit_weight(self):
        r=evaluate_gate()
        self.assertEqual(r["score_fixture_no_learning"]["0"],
                         r["score_fixture_no_learning"]["1"])
        self.assertGreater(r["score_fixture_no_learning"]["5"][0],
                           r["score_fixture_no_learning"]["0"][0])
        self.assertEqual(_probe_decision_score(1,126),
                         _probe_decision_score(0,126))

    def test_tick7_relaxation_erases_unit_effect_on_that_tick(self):
        r=evaluate_gate()
        self.assertEqual(r["synthetic_effect_stw1_tick6"],
                         {"numeric_effect":1,"before_relax":1,"after_relax":1})
        self.assertEqual(r["synthetic_effect_stw1_tick7"],
                         {"numeric_effect":1,"before_relax":1,"after_relax":0})

    def test_tick10_strength_loss_clears_unit_stw(self):
        r=evaluate_gate()
        self.assertEqual(r["synthetic_strength1_tick9"],
                         {"lost_connection":False,"strength":1,"stw":1})
        self.assertEqual(r["synthetic_strength1_tick10"],
                         {"lost_connection":True,"strength":0,"stw":0})

    def test_learning_gates_remain_open_and_replay_is_exact(self):
        a=evaluate_gate()
        b=evaluate_gate()
        self.assertEqual(a,b)
        self.assertEqual(a["G05_G09_G00H"],"OPEN")
        self.assertEqual(a["original_n_branches"],240)


if __name__=="__main__":
    unittest.main()
