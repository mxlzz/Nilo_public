"""I3c7k only uses fixed I3c7g development seeds and original C1 readouts."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_coupled_brain import initial_coupled
from experiments.neurolab.e09_i3_metabolic_protocol import selected_genes
from experiments.neurolab.e09_i3c7e_loss_factorial import ArmState
from experiments.neurolab.e09_i3c7k_transfer_stw_to_ltw import (
    PROTOCOL,SEEDS,SOURCE_SEEDS,MODES,load_manifest,
    copy_weights,run_seed,run_all,
)


class TransferCapacityOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row=run_seed(1700)

    def test_prior_source_hashes_and_cohort_not_new_confirmatory(self):
        self.assertEqual(PROTOCOL,"NL-AUDIT-I3c7k-v1")
        self.assertEqual(SEEDS,tuple(range(1700,1720)))
        self.assertEqual(SEEDS,SOURCE_SEEDS)
        self.assertTrue(set(SEEDS).isdisjoint(set(range(1400,1420))))
        self.assertEqual(MODES,("S","C","X"))
        self.assertEqual(len(load_manifest()["per_seed_sha256"]),20)
        with self.assertRaises(ValueError):
            run_seed(1400)

    def test_typed_single_field_intervention_and_equal_magnitude_swap(self):
        receptors,_=selected_genes()
        base=ArmState(initial_coupled(C1ContextBrain(1700),receptors))
        old=base.coupled.brain.dendrites
        c=copy_weights(base,"C")
        x=copy_weights(base,"X")
        self.assertEqual([s.dendrite.stw for s in old],[0]*8)
        self.assertEqual([s.dendrite.ltw for s in c.coupled.brain.dendrites],[0]*8)
        self.assertEqual([s.dendrite.ltw for s in x.coupled.brain.dendrites],[0]*8)
        self.assertEqual(c.coupled.chemistry,base.coupled.chemistry)
        self.assertEqual(x.coupled.chemistry,base.coupled.chemistry)
        self.assertEqual(copy_weights(base,"S"),base)
        with self.assertRaises(ValueError):
            copy_weights(base,"unknown")
        with self.assertRaises(TypeError):
            copy_weights(None,"C")

    def test_exact_original_long_training_and_no_ltw_frozen_cheating(self):
        row=self.row
        self.assertEqual(row["seed"],1700)
        self.assertEqual(len(row["I3c7g_original_seed_sha256"]),64)
        self.assertEqual(len(row["original_long_checkpoint_sha256"]),64)
        self.assertTrue(row["frozen_actions_identical_under_all_LTW_variants"])
        self.assertEqual(set(row["branches"]),set(MODES))
        baseline=row["branches"]["S"]
        copied=row["branches"]["C"]
        swapped=row["branches"]["X"]
        self.assertEqual(baseline["initial"]["tick"],896)
        self.assertEqual(baseline["initial"]["stw"],copied["initial"]["stw"])
        self.assertEqual(baseline["initial"]["stw"],swapped["initial"]["stw"])
        self.assertEqual(baseline["initial"]["strengths"],copied["initial"]["strengths"])
        self.assertEqual(baseline["initial"]["strengths"],swapped["initial"]["strengths"])
        self.assertEqual(copied["initial"]["ltw"],baseline["initial"]["stw"])
        self.assertEqual(swapped["initial"]["ltw"],[
            baseline["initial"]["stw"][(i+4)%8] for i in range(8)
        ])
        self.assertEqual(
            sorted(swapped["initial"]["ltw"]),
            sorted(copied["initial"]["ltw"]),
        )
        for mode in MODES:
            r=row["branches"][mode]
            self.assertEqual(r["active"]["new_feedback_events"],0)
            self.assertEqual(r["frozen"]["new_feedback_events"],0)
            self.assertEqual(r["frozen"]["steady"],baseline["frozen"]["steady"])
            self.assertEqual(r["frozen"]["overall"],baseline["frozen"]["overall"])
            self.assertEqual(len(r["active"]["quarter_accuracy"]),4)
            self.assertEqual(len(r["active"]["actions"]),128)

    def test_statistical_seed_is_one_run_not_128_ticks(self):
        d=run_all((1701,))
        self.assertEqual(d["n_seeds"],1)
        self.assertEqual(len(d["per_seed_sha256"]),1)
        self.assertEqual(set(d["paired_contrasts"]),{
            "C_minus_S","C_minus_X","S_minus_X",
        })
        self.assertEqual(d["gates"]["G05"],"OPEN")
        self.assertFalse(d["precommitted_capacity_gate"])
        for v in d["paired_contrasts"].values():
            self.assertEqual(v["n_seeds"],1)
            self.assertEqual(v["ci95"],[v["mean"],v["mean"]])
        self.assertIn("artificial",d["limitations"])

    def test_reject_reserved_duplicate_or_non_original_seeds(self):
        for samples in ((),(1700,1700),(1400,),(1720,),[1700]):
            with self.subTest(samples=samples):
                with self.assertRaises(ValueError):
                    run_all(samples)


if __name__=="__main__":
    unittest.main()
