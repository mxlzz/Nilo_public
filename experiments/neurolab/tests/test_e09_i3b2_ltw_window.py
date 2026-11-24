"""I3b2 gate128 synaptic eligibility: preregistered mechanistic tests."""
import unittest

from experiments.neurolab.c1_decay_math import ltw_toward
from experiments.neurolab.c1_synapse_integrated import (
    DECISION_EXCITATORY_GENE, DECISION_INHIBITORY_GENE,
)
from experiments.neurolab.e09_i3b2_ltw_window import (
    SEEDS, PREP_TICKS, BASE_TICK, LTW_GATE_TICK, END_TICK,
    run_episode, run_all,
)


class LTWBoundaryTests(unittest.TestCase):
    def test_existing_c1_rate_has_exact_logical_gate(self):
        self.assertEqual(DECISION_EXCITATORY_GENE.rates.ltw_rate,128)
        self.assertEqual(DECISION_INHIBITORY_GENE.rates.ltw_rate,128)
        self.assertEqual(ltw_toward(0,100,128,127),0)
        self.assertEqual(ltw_toward(0,100,128,128),1)
        self.assertEqual(ltw_toward(0,100,128,129),0)
        self.assertEqual(ltw_toward(0,100,128,256),1)

    def test_new_cohort_and_timing_locked(self):
        self.assertEqual(SEEDS,tuple(range(400,420)))
        self.assertEqual(PREP_TICKS,120)
        self.assertEqual(BASE_TICK,124)
        self.assertEqual(LTW_GATE_TICK,128)
        self.assertEqual(END_TICK,136)

    def test_one_episode_shows_exact_injection_timing_and_match(self):
        row=run_episode(400,0,"A")
        self.assertEqual(row["base_tick"],124)
        self.assertTrue(row["upstream_chem_same_at_fixed_timing"])
        self.assertEqual(row["modes"]["N"]["delivered_events"],0)
        for mode in ("E1","L1","E4","L4"):
            self.assertEqual(row["modes"][mode]["delivered_events"],1)
        self.assertEqual(row["modes"]["E1"]["event_absolute_tick"],125)
        self.assertEqual(row["modes"]["E4"]["event_absolute_tick"],125)
        self.assertEqual(row["modes"]["L1"]["event_absolute_tick"],128)
        self.assertEqual(row["modes"]["L4"]["event_absolute_tick"],128)
        self.assertEqual(row["last_measured_plastic_tick"],136)
        for mode in ("N","E1","L1","E4","L4"):
            ticks=[x["tick"] for x in row["modes"][mode]["trace_ticks_125_136"]]
            self.assertEqual(ticks,list(range(125,137)))
            self.assertEqual(row["modes"][mode]["tick127_ltw_sum_abs"],0)
            self.assertEqual(row["modes"][mode]["tick127_ltw_changed"],0)
        self.assertEqual(row,run_episode(400,0,"A"))

    def test_mappings_change_only_outcome_label_not_initial_action(self):
        first=run_episode(401,1,"A")
        reversed_=run_episode(401,1,"B")
        self.assertEqual(first["reference_action"],reversed_["reference_action"])
        self.assertNotEqual(first["reference_correct"],reversed_["reference_correct"])
        self.assertEqual(
            first["modes"]["N"]["trace_ticks_125_136"],
            reversed_["modes"]["N"]["trace_ticks_125_136"],
        )

    def test_one_seed_diagnostic_not_learning_claim(self):
        record=run_all((400,))
        self.assertEqual(record["episode_count"],4)
        self.assertEqual(record["base_tick"],124)
        self.assertEqual(record["early_injection_tick"],125)
        self.assertEqual(record["late_injection_tick"],128)
        self.assertEqual(record["gate_behavioral_G05_G09"],
                         "NOT EVALUATED; I3 remains negative")
        self.assertEqual(record["contrasts"]["gate128_ltw_E4_minus_L4"]["n_seeds"],1)


if __name__=="__main__":
    unittest.main()
