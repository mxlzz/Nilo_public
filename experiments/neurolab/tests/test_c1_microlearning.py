"""E09.02c: tests de aprendizaje local con dos canales, sin etiquetas."""
import json
import unittest

from experiments.neurolab.c1_microlearning import MiniLearner,MiniState
from experiments.neurolab.e09_microlearn_protocol import (
    evaluate,run_all,run_seed,train,
)


class MicroLearningTests(unittest.TestCase):
    def test_reward_updates_only_selected_excitatory(self):
        learner=MiniLearner(4)
        state=learner.initial()
        trial=learner.respond(state)
        after=learner.feedback(state,trial,+1)
        expected=(16,0,0,0) if trial.chosen=="D0" else (0,0,16,0)
        self.assertEqual(after.weights,expected)
        self.assertEqual(after.trials,1)

    def test_punishment_updates_only_selected_inhibitory(self):
        learner=MiniLearner(4)
        state=learner.initial()
        trial=learner.respond(state)
        after=learner.feedback(state,trial,-1)
        expected=(0,16,0,0) if trial.chosen=="D0" else (0,0,0,16)
        self.assertEqual(after.weights,expected)

    def test_concept_inactive_blocks_association(self):
        learner=MiniLearner(8)
        state=learner.initial()
        trial=learner.respond(state,(255,0))
        self.assertEqual(trial.trace.concept,0)
        after=learner.feedback(state,trial,+1)
        self.assertEqual(after.weights,state.weights)

    def test_frozen_control_unchanged(self):
        learner=MiniLearner(2)
        state=train(learner,learner.initial(),"D0",60,learn=False)
        self.assertEqual(state.weights,(0,0,0,0))
        self.assertEqual(state.trials,60)

    def test_holdout_does_not_mutate_state(self):
        learner=MiniLearner(1)
        state=train(learner,learner.initial(),"D0",60)
        copy=state
        score=evaluate(learner,state,"D0",80)
        self.assertEqual(state,copy)
        self.assertTrue(0<=score<=1)

    def test_feedback_cannot_be_reused(self):
        learner=MiniLearner(3)
        start=learner.initial()
        trial=learner.respond(start)
        nxt=learner.feedback(start,trial,-1)
        with self.assertRaises(ValueError):
            learner.feedback(nxt,trial,+1)

    def test_checkpoint_resume_exact(self):
        learner=MiniLearner(5)
        full=train(learner,learner.initial(),"D0",60)
        mid=train(learner,learner.initial(),"D0",25)
        restored=learner.restore(learner.checkpoint(mid))
        continuation=train(learner,restored,"D0",35)
        self.assertEqual(continuation,full)
        with self.assertRaises(ValueError):
            MiniLearner(6).restore(learner.checkpoint(mid))

    def test_no_labels_are_coded_into_agent(self):
        learner=MiniLearner(11)
        self.assertEqual(set(vars(learner)),{"seed","rate"})
        self.assertFalse(hasattr(learner,"correct_action"))
        self.assertFalse(hasattr(learner,"reward_map"))

    def test_inputs_and_rate_validation(self):
        for bad in (-1,0,256,True,1.5):
            with self.assertRaises(ValueError):
                MiniLearner(0,rate=bad)
        for bad in (True,-2,0,1.5):
            with self.assertRaises(ValueError):
                MiniState(weights=(bad,0,0,0))
        with self.assertRaises(ValueError):
            learner=MiniLearner(0)
            trial=learner.respond(learner.initial())
            learner.feedback(learner.initial(),trial,0)

    def test_determinism(self):
        for seed in range(20):
            self.assertEqual(run_seed(seed),run_seed(seed))

    def test_preregistered_gate(self):
        result=run_all()
        self.assertEqual(result["seeds"],20)
        self.assertTrue(result["passed"],json.dumps(result,indent=2))
        self.assertGreaterEqual(result["success_train_seeds"],18)
        self.assertGreaterEqual(result["success_reversal_seeds"],18)
        self.assertGreaterEqual(result["advantage_over_frozen"],.30)


if __name__=="__main__":
    unittest.main()
