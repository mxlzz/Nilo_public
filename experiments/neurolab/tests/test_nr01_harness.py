"""NR01 harness contract tests; toy world seeds only (0,1,42)."""
import unittest

from experiments.neurolab.nr01_harness import (
    Arm, _observations_digest, evaluate_read_only, feedback_phase,
    negative_test_permutation, run_world,
)
from experiments.neurolab.nr01_worlds import make_tape


def x(v):
    return (float(v),) * 16


class ToyEncoder:
    """No latent access or labels; visible only on observation tuples."""
    def __init__(self):
        self.values = []
        self.frozen = False
        self.over_budget = False
        self.k = 16
    def observe_unlabelled(self, value):
        assert type(value) is tuple and len(value) == 16
        assert not self.frozen
        self.values.append(value)
    def freeze_encoder(self):
        self.frozen = True
    def encode_read_only(self, value):
        assert self.frozen
        assert type(value) is tuple and len(value) == 16
        return (1.0,) + (0.0,) * 15
    def snapshot(self):
        return repr((self.values, self.frozen)).encode()


class TestHarnessToy(unittest.TestCase):
    def test_identical_unlabelled_observation_exposure(self):
        tape = make_tape("A", 42, "unsupervised")
        a, b = Arm("art", ToyEncoder()), Arm("art", ToyEncoder())
        for case in tape:
            a.observe_unlabelled(case.observation)
            b.observe_unlabelled(case.observation)
        self.assertEqual(a.encoder.values, b.encoder.values)
        self.assertEqual(_observations_digest(tape),
                         _observations_digest(make_tape("A",42,"unsupervised")))
        a.freeze_encoder()
        b.freeze_encoder()
        with self.assertRaises(RuntimeError):
            a.observe_unlabelled(x(.5))
        self.assertEqual(a.choose(x(.2)), b.choose(x(.2)))

    def test_feedback_then_holdout_does_not_mutate_state(self):
        arm = Arm("raw")
        arm.freeze_encoder()
        feedback = make_tape("A", 0, "feedback")
        test = make_tape("A", 0, "test")
        before = arm.snapshot()
        scores = feedback_phase(arm, feedback, test, "A", "original", 0)
        self.assertEqual(set(scores["checkpoints"]), {"8","16","32","64"})
        self.assertNotEqual(before, arm.snapshot())
        unchanged = arm.snapshot()
        evaluated = evaluate_read_only(arm, test, "A", "original")
        self.assertEqual(unchanged, arm.snapshot())
        nc = negative_test_permutation(evaluated["actions"], test, "A",
                                       "original", 0)
        self.assertEqual(nc["original_D0_count"], nc["permuted_D0_count"])
        self.assertEqual(nc["original_D0_count"], 80)

    def test_b_new_decoder_same_encoder_and_read_only(self):
        encoder = ToyEncoder()
        original = Arm("art", encoder)
        original.observe_unlabelled(x(.1))
        original.freeze_encoder()
        original.apply_reward(x(.1), original.choose(x(.1)), -1)
        replacement = original.for_new_task()
        self.assertIs(replacement.encoder, encoder)
        self.assertEqual(replacement.decoder.weights,
                         [0.0] * len(replacement.decoder.weights))
        self.assertNotEqual(original.decoder.weights, replacement.decoder.weights)
        before = replacement.snapshot()
        self.assertEqual(replacement.choose(x(.1)), "D0")
        self.assertEqual(before, replacement.snapshot())

    def test_toy_world_no_scientific_holdout(self):
        r = run_world("A", 1, "raw")
        self.assertEqual(r["status"], "software_executed_not_scientific_gate")
        self.assertEqual(r["original"]["checkpoints"]["32"]["count"], 160)
        self.assertEqual(r["reversed"]["checkpoints"]["32"]["count"], 160)
        b = run_world("B", 1, "knn")
        self.assertIn("B1", b)
        self.assertIn("B2", b)
        for forbidden in (1400, 1419, 24000, 24019):
            with self.assertRaises(ValueError):
                run_world("A", forbidden, "raw")


if __name__ == "__main__":
    unittest.main()
