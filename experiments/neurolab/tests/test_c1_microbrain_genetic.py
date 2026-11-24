"""E09.02g.2: 5-neuron gene-derived microbrain, four timing/tie controls."""
import json
import unittest

from experiments.neurolab.c1_microbrain_genetic import (
    MicroBrainState,MicroC1Brain,
)
from experiments.neurolab.e09_microbrain_genetic_protocol import (
    CONDITIONS,evaluate,run_all,run_seed,train,
)


class GeneticMicroBrainTests(unittest.TestCase):
    def _brain(self,timing="post_wta_gated",tie_mode="first_index"):
        return MicroC1Brain(3,timing=timing,tie_mode=tie_mode)

    def test_concept_uses_real_byte_256_scale(self):
        brain=self._brain()
        choice=brain.respond(brain.initial())
        self.assertEqual(choice.concept,253)
        self.assertEqual(choice.decision_scores,(80,80))
        self.assertTrue(choice.tie)
        self.assertEqual(choice.action,"D0")

    def test_wta_gated_first_reward_only_updates_winner_excitation(self):
        brain=self._brain()
        start=brain.initial()
        choice=brain.respond(start)
        result=brain.feedback(start,choice,(255,0,0,0))
        self.assertEqual(result.owner_outputs,(80,0))
        after=result.after
        self.assertEqual(after.dendrites[0].dendrite.susceptibility,4)
        self.assertEqual(after.dendrites[0].dendrite.stw,3)
        self.assertEqual(after.dendrites[0].dendrite.ltw,0)
        self.assertEqual(after.dendrites[2].dendrite.susceptibility,0)
        self.assertEqual(after.dendrites[2].dendrite.stw,0)
        self.assertTrue(all(s.strength==2 for s in after.dendrites))

    def test_pre_wta_updates_both_even_if_only_one_won(self):
        brain=self._brain("pre_wta_all")
        start=brain.initial()
        choice=brain.respond(start)
        result=brain.feedback(start,choice,(255,0,0,0))
        self.assertEqual(result.owner_outputs,(80,80))
        self.assertEqual(result.after.dendrites[0].dendrite.susceptibility,4)
        self.assertEqual(result.after.dendrites[2].dendrite.susceptibility,4)
        self.assertEqual(result.after.dendrites[0].dendrite.stw,3)
        self.assertEqual(result.after.dendrites[2].dendrite.stw,3)

    def test_punishment_from_evaluator_travels_in_inhibitory_class(self):
        brain=self._brain()
        start=brain.initial()
        choice=brain.respond(start)
        result=brain.feedback(start,choice,(0,255,0,0))
        self.assertEqual(result.after.dendrites[1].dendrite.stw,3)
        self.assertEqual(result.after.dendrites[0].dendrite.stw,0)

    def test_random_ties_are_reproducible_without_hidden_prng(self):
        brain=self._brain("post_wta_gated","random_tie")
        first=brain.respond(brain.initial())
        second=brain.respond(brain.initial())
        self.assertEqual(first,second)
        self.assertIn(first.action,("D0","D1"))

    def test_freeze_never_updates_any_dendrite(self):
        brain=self._brain()
        state=train(brain,brain.initial(),"D0",60,learn=False)
        self.assertEqual(state.dendrites,brain.initial().dendrites)
        self.assertEqual(state.trials,60)
        original=state
        evaluate(brain,state,"D0",80)
        self.assertEqual(state,original)

    def test_checkpoint_resume_without_hidden_state(self):
        brain=self._brain(tie_mode="random_tie")
        full=train(brain,brain.initial(),"D0",60)
        halfway=train(brain,brain.initial(),"D0",25)
        restored=brain.restore(brain.checkpoint(halfway))
        resumed=train(brain,restored,"D0",35)
        self.assertEqual(full,resumed)
        other=self._brain("pre_wta_all","random_tie")
        with self.assertRaises(ValueError):
            other.restore(brain.checkpoint(full))

    def test_stale_choice_and_invalid_chemicals_rejected(self):
        brain=self._brain()
        state=brain.initial()
        choice=brain.respond(state)
        changed=brain.feedback(state,choice,(255,0,0,0)).after
        with self.assertRaises(ValueError):
            brain.feedback(changed,choice,(255,0,0,0))
        with self.assertRaises(ValueError):
            brain.feedback(state,choice,(255,0,0))
        with self.assertRaises(ValueError):
            brain.feedback(state,choice,(256,0,0,0))

    def test_no_internal_answer_mapping(self):
        brain=self._brain()
        self.assertEqual(set(vars(brain)),{"seed","timing","tie_mode"})
        self.assertFalse(hasattr(brain,"target"))
        self.assertFalse(hasattr(brain,"correct_action"))
        self.assertFalse(hasattr(brain,"reward_map"))

    def test_per_seed_determinism(self):
        for seed in range(20):
            self.assertEqual(run_seed(seed,"post_wta_gated","random_tie"),
                             run_seed(seed,"post_wta_gated","random_tie"))

    def test_all_preregistered_conditions_are_reported_without_hiding_failures(self):
        result=run_all()
        self.assertEqual(result["seeds_per_condition"],20)
        self.assertEqual(len(result["conditions"]),4)
        self.assertEqual(set(result["conditions"]),set(f"{a}/{b}" for a,b in CONDITIONS))
        for key,data in result["conditions"].items():
            with self.subTest(condition=key):
                self.assertEqual(len(data["per_seed"]),20)
                self.assertEqual(data["passed"],(
                    data["seeds_train_at_least_90pct"]>=18
                    and data["seeds_reversal_at_least_90pct"]>=18
                    and data["advantage_vs_frozen"]>=.30
                ))
                self.assertTrue(0<=data["mean_train"]<=1)
                self.assertTrue(0<=data["mean_reversal"]<=1)
                self.assertTrue(all(len(row["after_train"])==4
                                    and len(row["after_reversal"])==4
                                    for row in data["per_seed"]))
        # Scientific acceptance gates are data, not test pass assertions.
        # A negative result must still be reproducible, green CI and
        # explicitly documented as "passed":false.

    def test_validation_of_modes(self):
        for args in ((-1,"post_wta_gated","first_index"),
                     (0,"invalid","first_index"),
                     (0,"post_wta_gated","invalid")):
            with self.assertRaises(ValueError):
                MicroC1Brain(args[0],timing=args[1],tie_mode=args[2])


if __name__=="__main__":
    unittest.main()
