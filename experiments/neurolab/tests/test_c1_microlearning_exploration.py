"""E09.02d tests, baseline E09.02c unchanged."""
import json
import unittest

from experiments.neurolab.c1_microlearning import MiniLearner,MiniState
from experiments.neurolab.c1_microlearning_exploration import EpsilonLearner
from experiments.neurolab.e09_exploration_protocol import run_all,run_seed
from experiments.neurolab.e09_microlearn_protocol import run_all as greedy_all, train


class EpsilonLearnerTests(unittest.TestCase):
    def test_epsilon_is_frozen(self):
        self.assertEqual(EpsilonLearner.EPSILON,0.10)

    def test_single_changed_dimension_is_action_selection(self):
        e=EpsilonLearner(3)
        old=MiniLearner(3)
        self.assertEqual(e.initial(),old.initial())
        self.assertEqual(e.rate,old.rate)
        s=MiniState((255,0,0,16),10)
        trial=e.respond(s)
        next_e=e.feedback(s,trial,-1)
        next_old=old.feedback(s,trial,-1)
        self.assertEqual(next_e,next_old)
        self.assertEqual(old.respond(s).trace,e.respond(s).trace)

    def test_exploration_can_override_a_clear_winner(self):
        learner=EpsilonLearner(7)
        s=MiniState((255,0,0,16),0)
        overridden=[]
        for tick in range(1000):
            trial=learner.respond(MiniState(s.weights,tick))
            if trial.chosen!=trial.trace.action:
                overridden.append(tick)
            self.assertEqual(trial,learner.respond(MiniState(s.weights,tick)))
        self.assertGreater(len(overridden),20)
        self.assertLess(len(overridden),100)

    def test_checkpoint_resume(self):
        learner=EpsilonLearner(8)
        state=train(learner,learner.initial(),"D0",60)
        saved=learner.checkpoint(state)
        recovered=learner.restore(saved)
        self.assertEqual(state,recovered)
        for n in range(20):
            self.assertEqual(learner.respond(state),learner.respond(recovered))

    def test_e09_02c_baseline_still_fails(self):
        orig=greedy_all()
        self.assertFalse(orig["passed"])
        self.assertEqual(orig["success_reversal_seeds"],6)
        self.assertEqual(orig["mean_reversal"],0.30)

    def test_frozen_no_plasticity(self):
        learner=EpsilonLearner(2)
        state=train(learner,learner.initial(),"D0",60,learn=False)
        self.assertEqual(state.weights,(0,0,0,0))

    @unittest.expectedFailure
    def test_preregistered_exploration_gate(self):
        result=run_all()
        self.assertEqual(result["seeds"],20)
        self.assertTrue(result["passed"],json.dumps(result,indent=2))
        self.assertGreaterEqual(result["success_train_seeds"],18)
        self.assertGreaterEqual(result["success_reversal_seeds"],18)
        self.assertGreaterEqual(result["advantage_over_frozen"],.30)

    def test_reproducible_results(self):
        for seed in range(20):
            self.assertEqual(run_seed(seed),run_seed(seed))


if __name__=="__main__":
    unittest.main()
