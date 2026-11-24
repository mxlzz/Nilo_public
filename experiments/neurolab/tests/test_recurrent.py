"""E08 tests of deterministic internal dynamics; never psychological claims."""
import random
import unittest
from experiments.neurolab.kernel import NeuronState
from experiments.neurolab.recurrent import make_recurrent, trajectory, run_all


class RecurrentTests(unittest.TestCase):
    def test_no_connections_goes_quiet(self):
        self.assertEqual(trajectory(make_recurrent(weight=None),120,0,4),
                         ((0,0),(0,0),(0,0),(0,0)))

    def test_two_node_period_two_exact_oracle(self):
        self.assertEqual(trajectory(make_recurrent(weight=255),120,0,6),
                         ((0,120),(120,0),(0,120),(120,0),(0,120),(120,0)))

    def test_perturbation_changes_phase_values(self):
        self.assertEqual(trajectory(make_recurrent(weight=255),120,50,4),
                         ((50,120),(120,50),(50,120),(120,50)))

    def test_attenuated_eventually_quiet(self):
        trace=trajectory(make_recurrent(weight=200),120,0,64)
        self.assertEqual(trace[-1],(0,0))
        self.assertTrue(all(max(b)<=max(a) for a,b in zip(trace,trace[1:])))
        self.assertNotEqual(trace[0],trace[-1])

    def test_determinism_and_bounds_twenty_seeds(self):
        for seed in range(20):
            rng=random.Random(seed)
            a,b=rng.randint(0,255),rng.randint(0,255)
            first=trajectory(make_recurrent(weight=255),a,b,50)
            second=trajectory(make_recurrent(weight=255),a,b,50)
            self.assertEqual(first,second)
            self.assertTrue(all(0<=x<=255 for pair in first for x in pair))

    def test_checkpoint_roundtrip(self):
        brain=make_recurrent(weight=255)
        initial=brain.initial({"A":NeuronState(0,120),"B":NeuronState(0,50)})
        start=brain.step(brain.step(initial))
        recovered=brain.restore(brain.checkpoint(start))
        self.assertEqual(start,recovered)
        for _ in range(10):
            start=brain.step(start)
            recovered=brain.step(recovered)
        self.assertEqual(start,recovered)

    def test_non_recurrent_configuration_distinct(self):
        self.assertNotEqual(make_recurrent(weight=255).configuration_hash,
                            make_recurrent(weight=200).configuration_hash)
        self.assertNotEqual(make_recurrent(weight=255).configuration_hash,
                            make_recurrent(weight=None).configuration_hash)

    def test_preregistered_gate(self):
        outcome=run_all()
        self.assertTrue(outcome["passed"])
        self.assertEqual(outcome["random_seeds"],20)
        self.assertEqual(outcome["damped_last"],(0,0))


if __name__=="__main__":
    unittest.main()
