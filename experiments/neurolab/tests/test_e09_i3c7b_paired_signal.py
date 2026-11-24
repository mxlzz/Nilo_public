"""I3c.7b prereg: fixed cohort, one evaluator decision, four independent arms."""
import unittest

from experiments.neurolab.e09_i3c7b_paired_signal import (
    SEEDS,RESERVED_CONFIRMATION_SEEDS,MAPS,MODES,
    TRUNK_TICK,END_TICK,READOUT_TICKS,
    initial_trunk,run_episode,run_seed,run_all,
)
from experiments.neurolab.e09_i3_metabolic_protocol import selected_genes
from experiments.neurolab.e09_context_protocol import REWARD,PUNISHMENT


class SensitivityContracts(unittest.TestCase):
    def test_frozen_parameters_and_unconsumed_holdout(self):
        self.assertEqual(SEEDS,tuple(range(1500,1520)))
        self.assertEqual(RESERVED_CONFIRMATION_SEEDS,tuple(range(1400,1420)))
        self.assertTrue(set(SEEDS).isdisjoint(RESERVED_CONFIRMATION_SEEDS))
        self.assertEqual(MODES,("N","M","C","F"))
        self.assertEqual((TRUNK_TICK,END_TICK),(4,128))
        self.assertEqual(READOUT_TICKS,(7,9,16,128))
        self.assertEqual(set(MAPS),{"A","B"})
        with self.assertRaises(ValueError):
            run_episode(1400,0,"A")
        with self.assertRaises(ValueError):
            run_episode(1300,0,"A")
        with self.assertRaises(ValueError):
            run_episode(1520,0,"A")
        with self.assertRaises(ValueError):
            run_episode(1500,2,"A")
        with self.assertRaises(ValueError):
            run_episode(1500,0,"C")

    def test_trunk_is_live_at_tick4(self):
        receptors,reactions=selected_genes()
        brain,trunk,action=initial_trunk(1500,0,receptors,reactions)
        self.assertEqual((trunk.brain.tick,trunk.chemistry.tick),(4,4))
        self.assertEqual(len(trunk.brain.dendrites),8)
        self.assertEqual(sum(d.strength>0 for d in trunk.brain.dendrites),8)
        self.assertIn(action,("D0","D1",None))
        self.assertEqual(brain.seed,1500)

    def test_exactly_matched_chemical_trajectories_and_direct_pulse(self):
        ep=run_episode(1500,0,"A")
        arms=ep["arms"]
        self.assertEqual(set(arms),set(MODES))
        self.assertEqual(arms["M"]["chemical_trajectory_sha256"],
                         arms["F"]["chemical_trajectory_sha256"])
        self.assertEqual(arms["N"]["chemical_trajectory_sha256"],
                         arms["C"]["chemical_trajectory_sha256"])
        self.assertEqual(arms["N"]["delivered"],0)
        self.assertEqual(arms["M"]["delivered"],
                         int(ep["original_action"] is not None))
        self.assertEqual(arms["C"]["delivered"],
                         int(ep["original_action"] is not None))
        self.assertEqual(arms["F"]["delivered"],
                         int(ep["original_action"] is not None))
        for mode,arm in arms.items():
            self.assertEqual(len(arm["frames"]),124)
            self.assertEqual([x["tick"] for x in arm["frames"][:3]],[5,6,7])
            self.assertEqual(arm["frames"][-1]["tick"],128)
            self.assertEqual(set(arm["readouts"]),{"7","9","16","128"})
            self.assertEqual(len(arm["effect_by_slot"]),8)
            for tick in READOUT_TICKS:
                self.assertIn(arm["readouts"][str(tick)]["correct"],(0,1))
        self.assertEqual(arms["F"]["total_effect"],0)
        self.assertEqual(arms["N"]["chem_auc"],[0,0])
        self.assertEqual(arms["N"]["frames"][2]["chem_read"][:2],[0,0])
        self.assertEqual(arms["C"]["frames"][2]["chem_read"],
                         list(REWARD if ep["initial_correct"] else PUNISHMENT))
        self.assertEqual(arms["C"]["frames"][2]["chem_from_pool"][:2],[0,0])
        self.assertEqual(arms["M"]["frames"][2]["chem_read"],
                         arms["M"]["frames"][2]["chem_from_pool"])
        self.assertEqual(arms["N"]["different_score_ticks_vs_N"],0)
        self.assertEqual(arms["N"]["different_type_ticks_vs_N"],0)

    def test_original_decision_does_not_depend_on_mapping_truth(self):
        row=run_seed(1501)
        self.assertEqual(len(row["episodes"]),4)
        for target in (0,1):
            a,b=[x for x in row["episodes"] if x["target"]==target]
            self.assertEqual(a["trunk_sha256"],b["trunk_sha256"])
            self.assertEqual(a["original_action"],b["original_action"])
            self.assertEqual(a["initial_correct"],not b["initial_correct"])

    def test_deterministic_data_and_seed_grouped_confidence(self):
        a=run_all((1502,))
        self.assertEqual(a,run_all((1502,)))
        self.assertEqual(a["n_physical_trunks"],2)
        self.assertEqual(a["n_mapping_coordinates"],4)
        self.assertEqual(a["n_branches"],16)
        self.assertEqual(len(a["per_seed_sha256"]),1)
        self.assertEqual(set(a["paired_contrasts"]),
             {"C_minus_N","M_minus_N","C_minus_M","M_minus_F"})
        self.assertEqual(a["gates"]["G05"],"OPEN")
        self.assertEqual(a["gates"]["sensitivity"],"DESCRIPTIVE_ONLY")
        self.assertIn("NOT matched",a["comparison_limits"])

    def test_fail_closed_on_duplicates_or_seed_leakage(self):
        for cohort in ((1500,1500),(1400,),(1520,),(),[1500]):
            with self.subTest(cohort=cohort):
                with self.assertRaises(ValueError):
                    run_all(cohort)


if __name__=="__main__":
    unittest.main()
