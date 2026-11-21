"""I3b.1 checks pre-registered matching without asserting learning."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_coupled_brain import initial_coupled
from experiments.neurolab.e09_i3_metabolic_protocol import selected_genes,metabolic_step
from experiments.neurolab.e09_i3b1_forks import (
    SEEDS, MODES, WARMUP, GAIN, run_episode, witness_step,
    common_trunk, paired_bootstrap, run_all,
)


class I3bPairedForkTests(unittest.TestCase):
    def test_gain1_step_equal_to_unmodified_i3(self):
        rs,rx=selected_genes()
        brain=C1ContextBrain(300)
        state=initial_coupled(brain,rs)
        reference,action,_=metabolic_step(
            brain,state,0,rs,rx,plasticity=True)
        observed,observed_action=witness_step(
            brain,state,0,rs,rx,gain=1)
        self.assertEqual(reference,observed)
        self.assertEqual(action,observed_action)

    def test_cohort_and_untouched_protocol_constants(self):
        self.assertEqual(SEEDS,tuple(range(300,320)))
        self.assertEqual(MODES,("N","E1","L1","E4","L4"))
        self.assertEqual(GAIN["E1"],1)
        self.assertEqual(GAIN["E4"],4)
        self.assertEqual(len(WARMUP),32)

    def test_one_episodic_fork_same_action_one_precursor_per_arm(self):
        episode=run_episode(300,0,1,"A")
        self.assertEqual(episode["reference_tick"],36)
        self.assertEqual(episode["horizon"],10)
        self.assertEqual(episode["branches"]["N"]["delivered_events"],0)
        self.assertEqual(episode["branches"]["E1"]["delivered_events"],1)
        self.assertEqual(episode["branches"]["E4"]["delivered_events"],1)
        self.assertEqual(episode["branches"]["L1"]["delivered_events"],1)
        self.assertEqual(episode["branches"]["L4"]["delivered_events"],1)
        self.assertEqual(episode["branches"]["E1"]["injected_at_post_target_tick"],0)
        self.assertEqual(episode["branches"]["L1"]["injected_at_post_target_tick"],1)
        self.assertTrue(episode["chemical_trajectories_matched_for_gain"])
        for mode in MODES:
            self.assertEqual(episode["branches"][mode]["end_tick"],46)
            self.assertEqual(episode["branches"][mode]["synapse_samples"],80)
            self.assertEqual(
                episode["branches"][mode]["effect_total"],
                episode["branches"][mode]["effect_target_source"]+
                episode["branches"][mode]["effect_distractor_source"],
            )
        self.assertEqual(episode,run_episode(300,0,1,"A"))

    def test_two_mappings_change_only_feedback_sign(self):
        left=run_episode(301,1,2,"A")
        right=run_episode(301,1,2,"B")
        self.assertEqual(left["reference_action"],right["reference_action"])
        self.assertEqual(left["reference_tick"],right["reference_tick"])
        self.assertNotEqual(left["reference_correct"],right["reference_correct"])
        self.assertEqual(left["branches"]["N"],right["branches"]["N"])

    def test_reject_unknown_conditions(self):
        for args in ((300,2,1,"A"),(300,1,4,"A"),(300,0,1,"BAD")):
            with self.assertRaises(ValueError):
                run_episode(*args)
        rs,rx=selected_genes()
        brain=C1ContextBrain(300)
        state=initial_coupled(brain,rs)
        with self.assertRaises(ValueError):
            witness_step(brain,state,0,rs,rx,gain=5)

    def test_cluster_bootstrap_not_pseudoreplication(self):
        # Synthetic paired differences; two observations from seed1
        # are ONE cluster, seed2 has one observation.
        def episode(seed,x,y):
            return {"seed":seed,
                    "branches":{"E4":{"effect_candidate":x},
                                "E1":{"effect_candidate":y}}}
        rows=[episode(1,10,0),episode(1,20,0),episode(2,0,0)]
        result=paired_bootstrap(rows,"E4","E1","effect_candidate",
                                replicas=100,seed=60513)
        self.assertEqual(result["paired_episodes"],3)
        self.assertEqual(result["n_seeds"],2)
        self.assertEqual(result["mean"],7.5)
        self.assertEqual(result["per_seed"],{"1":15,"2":0})

    def test_small_run_no_claim_of_learning(self):
        result=run_all((300,))
        self.assertEqual(result["episode_count"],12)
        self.assertEqual(len(result["per_episode"]),12)
        self.assertEqual(result["n_units"],6)
        self.assertEqual(result["rates_synthetic"],40)
        self.assertEqual(result["dose"],80)
        self.assertEqual(result["gate_behavioral_G05_G09"],
                         "NOT EVALUATED; I3 remains negative")
        self.assertEqual(result["gate_wiring"],
                         "PASS: witness and full upstream chemistry equality asserted")
        self.assertEqual(result,run_all((300,)))


if __name__=="__main__":
    unittest.main()
