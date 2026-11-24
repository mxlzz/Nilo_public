"""Tests E09.02f.1: oráculos extraídos por análisis estático del C1 x86.

Fixtures numéricos independientes, nunca ejecutan el archivo Creatures.exe.
"""
import random
import unittest

from experiments.neurolab.c1_runtime_math import (
    ATTENTION_RULE, CONCEPT_RULE, DECISION_RULE, RuleInputs,
    decr, dendrite_signal, evaluate, incr, minus, neuron_output, plus, times,
)
from experiments.neurolab.c1_svrule_subset import (
    SVInputs, evaluate as earlier_experimental_evaluate,
)


class C1RuntimeMathTests(unittest.TestCase):
    def test_plus_saturates_immediately(self):
        self.assertEqual(plus(80, 240), 255)
        self.assertEqual(plus(10, 20), 30)
        self.assertEqual(plus(255, 255), 255)

    def test_minus_saturates_immediately(self):
        self.assertEqual(minus(80, 130), 0)
        self.assertEqual(minus(255, 200), 55)
        self.assertEqual(minus(0, 255), 0)

    def test_times_uses_binary_fixed_point_256(self):
        self.assertEqual(times(255, 255), 254)
        self.assertEqual(times(128, 128), 64)
        self.assertEqual(times(1, 255), 0)

    def test_increment_decrement_do_not_wrap(self):
        self.assertEqual(incr(255), 255)
        self.assertEqual(incr(0), 1)
        self.assertEqual(decr(0), 0)
        self.assertEqual(decr(255), 254)

    def test_decision_operator_order_differs_from_old_model(self):
        inputs=RuleInputs(state=80, type0=240, type1=200)
        self.assertEqual(evaluate(DECISION_RULE, inputs), 55)
        self.assertEqual(earlier_experimental_evaluate(
            DECISION_RULE, SVInputs(state=80,type0=240,type1=200)),120)
        self.assertEqual(evaluate(DECISION_RULE,
                                  RuleInputs(state=80,type0=110,type1=30)),160)

    def test_attention_and_concept_rules(self):
        self.assertEqual(evaluate(ATTENTION_RULE,
                                  RuleInputs(state=250,type0=30,type1=30)),255)
        self.assertEqual(evaluate(CONCEPT_RULE,RuleInputs(and_type0=89)),89)

    def test_dendrite_signal_uses_256_not_255(self):
        r=dendrite_signal((100,80),(128,128),attenuation=255)
        self.assertEqual((r.accumulated,r.type_value,r.and_value),(90,89,89))
        r=dendrite_signal((255,255),(128,128),attenuation=255)
        self.assertEqual((r.accumulated,r.type_value,r.and_value),(254,253,253))

    def test_one_silent_source_masks_anded_value(self):
        r=dendrite_signal((100,0),(128,128),attenuation=255)
        self.assertEqual((r.accumulated,r.type_value,r.and_value),(50,49,0))

    def test_accumulated_sum_saturates_before_attenuation(self):
        r=dendrite_signal((255,255,255),(255,255,255),attenuation=255)
        self.assertEqual((r.accumulated,r.type_value,r.and_value),(255,254,254))

    def test_neuron_output_post_calculation_subtracts_threshold(self):
        self.assertEqual(neuron_output(80,24),56)
        self.assertEqual(neuron_output(10,24),0)
        self.assertEqual(neuron_output(255,0),255)

    def test_rejects_out_of_range_bytes_and_unsupported_rules(self):
        for invalid in (-1,256,True,1.25):
            with self.subTest(invalid=repr(invalid)),self.assertRaises(ValueError):
                plus(invalid,0)
        with self.assertRaises(ValueError):
            dendrite_signal((),(),attenuation=255)
        with self.assertRaises(ValueError):
            dendrite_signal((255,),(),attenuation=255)
        with self.assertRaises(ValueError):
            evaluate(bytes((9,0,0,0,0,0,0,0)),RuleInputs())
        with self.assertRaises(TypeError):
            evaluate(DECISION_RULE,{"state":80})

    def test_deterministic_twenty_seeds(self):
        def run(seed):
            gen=random.Random(seed)
            return [evaluate(DECISION_RULE, RuleInputs(
                gen.randrange(256),gen.randrange(256),gen.randrange(256)))
                for _ in range(200)]
        for seed in range(20):
            self.assertEqual(run(seed),run(seed))


if __name__=="__main__":
    unittest.main()
