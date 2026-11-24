"""NeuroLab E02: evidencia de elección, sin aprendizaje."""
import unittest
from experiments.neurolab.kernel import BrainState, NeuronState
from experiments.neurolab.circuit import choose_action, make_six_neuron, run_episode


class ChoiceTests(unittest.TestCase):
    def test_no_signal_abstains(self):
        brain = make_six_neuron(3)
        end, trace, result = run_episode(brain, (0, 0))
        self.assertEqual(result.status, "inactive")
        self.assertIsNone(result.action)
        self.assertEqual(len(trace), 3)
        self.assertEqual(end.tick, 3)

    def test_winner_takes_all(self):
        state = BrainState(3, {"D0": NeuronState(0, 150), "D1": NeuronState(0, 70)})
        result = choose_action(state)
        self.assertEqual(result.action, "D0")
        self.assertEqual(result.status, "winner")
        self.assertEqual(dict(result.scores), {"D0": 150, "D1": 70})
        self.assertEqual(state.neurons["D1"].output, 70)  # WTA no altera la mente.

    def test_tie_explicit_policies(self):
        state = BrainState(3, {"D0": NeuronState(0, 90), "D1": NeuronState(0, 90)})
        self.assertEqual(choose_action(state).status, "tie")
        self.assertIsNone(choose_action(state).action)
        self.assertEqual(choose_action(state, tie_policy="first").action, "D0")
        with self.assertRaises(ValueError):
            choose_action(state, tie_policy="random")
        with self.assertRaises(ValueError):
            choose_action(state, candidates=("D0", "D0"))

    def test_three_tick_causal_delay(self):
        brain = make_six_neuron(1)
        end, trace, choice = run_episode(brain, (200, 0))
        self.assertEqual(trace[0].neurons["E0"].output, 200)
        self.assertEqual(trace[0].neurons["C0"].output, 0)
        self.assertEqual(trace[1].neurons["C0"].output, 200)
        self.assertEqual(trace[1].neurons["D0"].output, 0)
        self.assertGreater(trace[2].neurons["D0"].output, 0)
        self.assertGreater(trace[2].neurons["D1"].output, 0)
        self.assertEqual(trace[2].neurons["C0"].output, 0)
        self.assertIn(choice.action, ("D0", "D1"))
        self.assertEqual(end, trace[-1])

    def test_fixed_seed_reproducibility(self):
        for seed in range(50):
            first = make_six_neuron(seed)
            second = make_six_neuron(seed)
            self.assertEqual(first.configuration_hash, second.configuration_hash)
            for stimulus in ((255, 0), (0, 255), (255, 255), (1, 0), (0, 0)):
                r1 = run_episode(first, stimulus)[2]
                r2 = run_episode(second, stimulus)[2]
                self.assertEqual(r1, r2)

    def test_no_hardcoded_correct_mapping(self):
        # Distintas inicializaciones pueden preferir acciones diferentes ante E0.
        results = {run_episode(make_six_neuron(seed), (255, 0))[2].action
                   for seed in range(50)}
        self.assertEqual(results, {"D0", "D1"})

    def test_scenarios_and_weight_stability(self):
        brain = make_six_neuron(11)
        original_synapses = brain.synapses
        for stim in ((100, 0), (0, 100), (100, 100), (0, 0)):
            state, trace, choice = run_episode(brain, stim)
            self.assertEqual(state.tick, 3)
            self.assertEqual(len(trace), 3)
            self.assertEqual(brain.synapses, original_synapses)
            self.assertEqual(choice.scores, (("D0", state.neurons["D0"].output),
                                             ("D1", state.neurons["D1"].output)))

    def test_partial_signal_stronger_produces_larger_output(self):
        brain = make_six_neuron(12)
        s_low = run_episode(brain, (64, 0))[0]
        s_high = run_episode(brain, (192, 0))[0]
        for name in ("D0", "D1"):
            self.assertGreater(s_high.neurons[name].output, s_low.neurons[name].output)


if __name__ == "__main__":
    unittest.main()
