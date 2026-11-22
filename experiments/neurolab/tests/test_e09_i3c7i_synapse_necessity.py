"""I3c.7i: per-synapse STW lesions only after original checkpoint SHAs."""
import unittest
from dataclasses import replace

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_i3c7i_synapse_necessity import (
    SEEDS,PROTOCOL,N_SLOTS,PROBE_TICKS,MANIFEST_PATH,
    load_original_manifest,checkpoint_replay,clone_stw_mask,
    microprobe,slot_classification,one_checkpoint_context,
    run_seed,run_all,
)


class LocalCausalNecessityContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row=run_seed(1800)

    def test_only_existing_development_seeds_not_confirmation(self):
        self.assertEqual(PROTOCOL,"NL-AUDIT-I3c7i-v1")
        self.assertEqual(SEEDS,tuple(range(1800,1820)))
        self.assertTrue(MANIFEST_PATH.exists())
        self.assertEqual((N_SLOTS,PROBE_TICKS),(8,8))
        with self.assertRaises(ValueError):
            run_seed(1400)
        with self.assertRaises(ValueError):
            run_seed(1820)
        self.assertEqual(len(load_original_manifest()["per_seed_sha256"]),20)

    def test_stw_mask_is_single_dendrite_only_and_typed(self):
        b=C1ContextBrain(1800)
        state=b.initial()
        # Artificial fixture changes only one STW; NOT an experimental learner.
        syn=state.dendrites[0]
        edited=replace(
            state,dendrites=(replace(
                syn,dendrite=replace(syn.dendrite,stw=7)
            ),)+state.dendrites[1:]
        )
        victim=clone_stw_mask(edited,(0,))
        self.assertEqual(victim.dendrites,state.dendrites)
        self.assertEqual(victim.neuron_states,edited.neuron_states)
        self.assertEqual(victim.neuron_outputs,edited.neuron_outputs)
        self.assertEqual(victim.concept_outputs,edited.concept_outputs)
        self.assertEqual(victim.tick,edited.tick)
        self.assertEqual(victim.dendrites[0].strength,2)
        self.assertEqual(victim.dendrites[0].dendrite.ltw,0)
        for invalid in ((0,0),(-1,),(8,),(True,)):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    clone_stw_mask(edited,invalid)

    def test_replay_exact_source_sha_and_original_checkpoint_hashes(self):
        self.assertEqual(self.row["seed"],1800)
        self.assertEqual(len(self.row["verified_original_I3c7h_sha256"]),64)
        for phase in ("first","reversed"):
            self.assertEqual(set(self.row["phases"][phase]),{"B","P"})
            for mode in ("B","P"):
                self.assertEqual(len(self.row["phases"][phase][mode]["observations"]),2)
        with self.assertRaises(ValueError):
            checkpoint_replay(1400)

    def test_sham_and_already_zero_synapse_have_no_action_effect(self):
        for phase in ("first","reversed"):
            for mode in ("B","P"):
                data=self.row["phases"][phase][mode]
                self.assertEqual(data["summary"]["n_probe_steady_ticks"],12)
                self.assertEqual(data["summary"]["n_lesions"],16)
                self.assertEqual(data["summary"]["n_lesion_steady_ticks"],96)
                for obs in data["observations"]:
                    self.assertTrue(obs["sham_identical"])
                    self.assertEqual(len(obs["reference"]),8)
                    self.assertEqual(len(obs["all_zero"]),8)
                    self.assertEqual(len(obs["lesions"]),8)
                    for lesion in obs["lesions"]:
                        if lesion["original_stw"]==0:
                            self.assertEqual(lesion["probe"],obs["reference"])
                        self.assertLessEqual(lesion["action_changed_steady"],6)
                        self.assertEqual(
                            lesion["base_correct_steady"]-lesion["altered_correct_steady"],
                            lesion["lost_correct_steady"]-lesion["gained_correct_steady"],
                        )

    def test_aligned_role_classification_exact(self):
        mapping=("D0","D1")
        self.assertTrue(slot_classification(0,0,mapping)[
            "aligned_to_current_mapping"])
        self.assertFalse(slot_classification(1,0,mapping)[
            "aligned_to_current_mapping"])
        self.assertFalse(slot_classification(4,0,mapping)[
            "aligned_to_current_mapping"])
        self.assertTrue(slot_classification(5,0,mapping)[
            "aligned_to_current_mapping"])
        with self.assertRaises(ValueError):
            slot_classification(8,0,mapping)
        for phase in ("first","reversed"):
            for mode in ("B","P"):
                groups=self.row["phases"][phase][mode]["summary"]["per_alignment"]
                self.assertEqual(groups["True"]["n_lesions"],4)
                self.assertEqual(groups["False"]["n_lesions"],12)

    def test_integral_design_counts_and_statistical_seed_unit(self):
        d=run_all((1801,))
        self.assertEqual(d["n_seeds"],1)
        self.assertEqual(d["n_microblocks"],40)
        self.assertEqual(d["n_single_lesion_microblocks"],32)
        self.assertEqual(d["n_total_probe_steps"],320)
        self.assertEqual(len(d["per_seed_sha256"]),1)
        self.assertIsNone(d["gate_allzero_effective"])
        self.assertIsNone(d["gate_baseline_informative"])
        self.assertEqual(d["gates"]["G05"],"OPEN")
        for phase in ("first","reversed"):
            for contrast in d["paired_B_minus_P"][phase].values():
                self.assertEqual(contrast["n_seeds"],1)
                self.assertEqual(contrast["ci95"],[contrast["mean"],contrast["mean"]])

    def test_invalid_duplicated_and_reserved_cohorts(self):
        for group in ((),(1800,1800),(1400,),(1820,),[1800]):
            with self.subTest(group=group):
                with self.assertRaises(ValueError):
                    run_all(group)


if __name__=="__main__":
    unittest.main()
