"""Tests E03: feedback solo después de elección, sin etiquetas en Learner."""
import json
import unittest

from experiments.neurolab.plasticity import PlasticLearner, PlasticState
from experiments.neurolab.e03_protocol import (
    ORIGINAL, REVERSED, encode, evaluate, experiment_for_seed, run_all,
    sequence, train,
)


class PlasticityTests(unittest.TestCase):
    def test_feedback_changes_only_chosen_active_edge(self):
        learner = PlasticLearner(5, rate=16)
        state = learner.initial()
        trial = learner.respond(state, (255, 0))
        self.assertEqual(trial.active_concepts, ("C0",))
        next_state = learner.update(state, trial, -1)
        changes = [i for i, (before, after) in enumerate(zip(
            state.weights, next_state.weights
        )) if before != after]
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], 0 if trial.action == "D0" else 1)
        self.assertEqual(next_state.trials, 1)

    def test_positive_negative_reward_only(self):
        learner = PlasticLearner(3)
        trial = learner.respond(learner.initial(), (255, 0))
        for invalid in (0, 2, 1.0, True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                learner.update(learner.initial(), trial, invalid)

    def test_cannot_replay_feedback_on_changed_state(self):
        learner = PlasticLearner(1)
        state = learner.initial()
        trial = learner.respond(state, (255, 0))
        updated = learner.update(state, trial, -1)
        with self.assertRaises(ValueError):
            learner.update(updated, trial, +1)

    def test_frozen_control_not_learning(self):
        learner = PlasticLearner(8)
        state = learner.initial()
        initial_weights = state.weights
        for event in sequence(8, n_per_class=50, salt=1000):
            trial = learner.respond(state, encode(event))
            reward = +1 if trial.action == ORIGINAL[event] else -1
            state = learner.update(state, trial, reward, learning=False)
        self.assertEqual(state.weights, initial_weights)
        self.assertEqual(state.trials, 100)

    def test_holdout_evaluation_never_modifies_state(self):
        learner = PlasticLearner(11)
        state = learner.initial()
        before = state
        evaluate(learner, state, sequence(11, n_per_class=40, salt=2000), ORIGINAL)
        self.assertEqual(state, before)

    def test_checkpoint_continuation(self):
        learner = PlasticLearner(15)
        events = sequence(15, n_per_class=50, salt=1000)
        first = train(learner, learner.initial(), events, ORIGINAL, learning=True)
        mid = train(learner, learner.initial(), events[:40], ORIGINAL, learning=True)
        checkpoint = learner.checkpoint(mid)
        resumed = learner.restore(checkpoint)
        second = train(learner, resumed, events[40:], ORIGINAL, learning=True)
        self.assertEqual(first, second)
        incompatible = PlasticLearner(16)
        with self.assertRaises(ValueError):
            incompatible.restore(checkpoint)

    def test_stimulus_encode_not_a_target_label(self):
        learner = PlasticLearner(6)
        before = learner.initial()
        action = learner.respond(before, encode("A")).action
        # El resultado previo a recibir feedback no depende del diccionario externo.
        self.assertEqual(action, learner.respond(before, encode("A")).action)
        self.assertNotIn("target", vars(learner))
        self.assertEqual(encode("A"), (255, 0))
        self.assertEqual(encode("B"), (0, 255))
        with self.assertRaises(ValueError):
            encode("Z")

    def test_seed_determinism(self):
        self.assertEqual(experiment_for_seed(7), experiment_for_seed(7))

    def test_pre_registered_gate_all_twenty_seeds(self):
        result = run_all()
        self.assertEqual(result["n_seeds"], 20)
        self.assertTrue(result["passed"], json.dumps(result, indent=2))
        self.assertGreaterEqual(result["seeds_train_at_least_0_9"], 18)
        self.assertGreaterEqual(result["seeds_reversal_at_least_0_9"], 18)
        self.assertGreaterEqual(result["mean_delta"], 0.30)

    def test_finite_fixed_weights(self):
        learner = PlasticLearner(0)
        state = learner.initial()
        for k in range(200):
            trial = learner.respond(state, encode("A"))
            state = learner.update(state, trial, 1 if k % 3 == 0 else -1)
        self.assertTrue(all(0 <= w <= 255 for w in state.weights))


if __name__ == "__main__":
    unittest.main()
