"""NeuroLab E01 — oráculos calculados de forma independiente.

E01 no implementa un cerebro histórico C1: las fórmulas de NeuroLab
están declaradas en docs/neurolab/E00_INFORME_HISTORICO_01.md.
Ejecutar: python -m unittest discover -s experiments/neurolab/tests -v
"""
import json
import random
import unittest

from experiments.neurolab.kernel import (
    Brain, BrainState, NeuronSpec, NeuronState, SynapseSpec, neuron_step
)


class ManualOracles(unittest.TestCase):
    def test_threshold_above(self):
        n = NeuronSpec("n", threshold=40)
        self.assertEqual(
            neuron_step(NeuronState(30, 0), n, excitation=20),
            NeuronState(state=50, output=10)
        )

    def test_inhibition(self):
        n = NeuronSpec("n", threshold=20)
        self.assertEqual(
            neuron_step(NeuronState(120, 0), n, inhibition=50),
            NeuronState(state=70, output=50)
        )

    def test_relax_half(self):
        n = NeuronSpec("n", threshold=40, rest=0, decay=128)
        self.assertEqual(
            neuron_step(NeuronState(150, 0), n),
            NeuronState(state=75, output=110)
        )

    def test_paper_vs_guide_conflict(self):
        a = NeuronSpec("n", threshold=40, output_mode="full_state")
        b = NeuronSpec("n", threshold=40, output_mode="above_threshold")
        s = NeuronState(160, 0)
        self.assertEqual(neuron_step(s, a).output, 160)
        self.assertEqual(neuron_step(s, b).output, 120)

    def test_equal_threshold_not_firing(self):
        self.assertEqual(
            neuron_step(NeuronState(40, 0), NeuronSpec("n", threshold=40)).output, 0
        )

    def test_saturates_state_and_stimulus_input(self):
        compute = NeuronSpec("c")
        inp = NeuronSpec("i", kind="input", threshold=10)
        self.assertEqual(
            neuron_step(NeuronState(250, 0), compute, excitation=100).state, 255
        )
        self.assertEqual(
            neuron_step(NeuronState(3, 0), compute, inhibition=100).state, 0
        )
        self.assertEqual(
            neuron_step(NeuronState(150, 150), inp, stimulus=80),
            NeuronState(80, 70)
        )

    def test_rest_both_directions(self):
        n = NeuronSpec("n", threshold=0, rest=100, decay=128)
        self.assertEqual(neuron_step(NeuronState(20, 0), n).state, 60)
        self.assertEqual(neuron_step(NeuronState(180, 0), n).state, 140)

    def test_inputs_require_int_not_bool_nan_float(self):
        n = NeuronSpec("n", kind="input")
        for value in (-1, 256, 1.0, True, float("nan")):
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                neuron_step(NeuronState(), n, stimulus=value)

    def test_invalid_types_and_ranges(self):
        for args in ({"decay": -1}, {"threshold": 256},
                     {"rest": True}, {"output_mode": "made_up"}, {"kind": "alien"}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                NeuronSpec("bad", **args)
        for args in ({"weight": -1}, {"weight": 256}, {"sign": "neutral"}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                SynapseSpec("x", "y", **({"weight": 50} | args))
        with self.assertRaises(ValueError):
            NeuronState(256, 0)


class BrainSemantics(unittest.TestCase):
    def setUp(self):
        self.brain = Brain(
            [NeuronSpec("input", kind="input"), NeuronSpec("compute"),
             NeuronSpec("inhibited", threshold=0)],
            [SynapseSpec("input", "compute", weight=255),
             SynapseSpec("input", "inhibited", weight=255, sign="inh")],
        )

    def test_synchronous_previous_output_only(self):
        prev = self.brain.initial()
        first = self.brain.step(prev, {"input": 100})
        self.assertEqual(first.tick, 1)
        self.assertEqual(first.neurons["input"].output, 100)
        self.assertEqual(first.neurons["compute"].output, 0)
        second = self.brain.step(first, {"input": 0})
        self.assertEqual(second.neurons["compute"].output, 100)
        self.assertEqual(second.neurons["input"].output, 0)
        third = self.brain.step(second, {"input": 0})
        self.assertEqual(third.neurons["compute"].output, 100)

    def test_inhibition_from_old_signal(self):
        starting = self.brain.initial(
            {"inhibited": NeuronState(150, 0)}
        )
        before = self.brain.step(starting, {"input": 100})
        self.assertEqual(before.neurons["inhibited"].state, 150)
        after = self.brain.step(before)
        self.assertEqual(after.neurons["inhibited"].state, 50)

    def test_weight_128_out_of_255(self):
        brain = Brain([NeuronSpec("i", kind="input"), NeuronSpec("c")],
                      [SynapseSpec("i", "c", 128)])
        s = brain.step(brain.initial(), {"i": 200})
        s = brain.step(s)
        self.assertEqual(s.neurons["c"].output, 100)

    def test_determinism_by_replay(self):
        r = random.Random(42)
        seq = [{"input": r.randint(0, 255)} for _ in range(48)]
        def run():
            state = self.brain.initial()
            trace = []
            for stim in seq:
                state = self.brain.step(state, stim)
                trace.append(self.brain.checkpoint(state))
            return trace
        self.assertEqual(run(), run())

    def test_checkpoint_roundtrip_and_uninterrupted_trace(self):
        stimuli = [{"input": x} for x in (40, 100, 5, 200, 80, 0, 0, 77)]
        uninterrupted = self.brain.initial()
        for stim in stimuli:
            uninterrupted = self.brain.step(uninterrupted, stim)
        split = self.brain.initial()
        for stim in stimuli[:4]:
            split = self.brain.step(split, stim)
        save = self.brain.checkpoint(split)
        recovered = self.brain.restore(save)
        self.assertEqual(split, recovered)
        for stim in stimuli[4:]:
            recovered = self.brain.step(recovered, stim)
        self.assertEqual(uninterrupted, recovered)

    def test_checkpoint_rejects_other_topology(self):
        state = self.brain.initial()
        other = Brain([NeuronSpec("different")])
        with self.assertRaises(ValueError):
            other.restore(self.brain.checkpoint(state))
        bad = json.loads(self.brain.checkpoint(state))
        bad["neurons"]["unknown"] = {"state": 0, "output": 0}
        with self.assertRaises(ValueError):
            self.brain.restore(json.dumps(bad))

    def test_config_sha_stable_and_sensitive(self):
        same = Brain(list(self.brain.neurons), list(self.brain.synapses))
        self.assertEqual(self.brain.configuration_hash, same.configuration_hash)
        alt = Brain([NeuronSpec("input", kind="input"),
                     NeuronSpec("compute", decay=1),
                     NeuronSpec("inhibited", threshold=0)], self.brain.synapses)
        self.assertNotEqual(self.brain.configuration_hash, alt.configuration_hash)

    def test_does_not_mutate_old_state_or_weights(self):
        old = self.brain.initial()
        original_synapses = self.brain.synapses
        nxt = self.brain.step(old, {"input": 255})
        self.assertEqual(old, self.brain.initial())
        self.assertEqual(self.brain.synapses, original_synapses)
        self.assertNotEqual(nxt.tick, old.tick)

    def test_invalid_graph_and_stimuli(self):
        with self.assertRaises(ValueError):
            Brain([NeuronSpec("dup"), NeuronSpec("dup")])
        with self.assertRaises(ValueError):
            Brain([NeuronSpec("input", kind="input")],
                  [SynapseSpec("input", "input", 255)])
        with self.assertRaises(ValueError):
            Brain([NeuronSpec("x")], [SynapseSpec("x", "missing", 255)])
        with self.assertRaises(ValueError):
            self.brain.step(self.brain.initial(), {"compute": 1})
        with self.assertRaises(ValueError):
            self.brain.step(BrainState(0, {"unknown": NeuronState()}))
        with self.assertRaises(ValueError):
            self.brain.step(self.brain.initial(), {"input": float("nan")})

    def test_many_steps_finite_bounded(self):
        state = self.brain.initial()
        for k in range(20000):
            state = self.brain.step(state, {"input": k % 256})
        self.assertEqual(state.tick, 20000)
        for n in state.neurons.values():
            self.assertTrue(0 <= n.state <= 255)
            self.assertTrue(0 <= n.output <= 255)


if __name__ == "__main__":
    unittest.main()
