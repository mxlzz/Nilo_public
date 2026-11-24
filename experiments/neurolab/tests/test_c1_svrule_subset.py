"""E09.02a: oráculos independientes del genoma C1, sin archivos de terceros."""
import random
import unittest
from experiments.neurolab.c1_svrule_subset import (
    DECISION_RULE, ATTENTION_RULE, CONCEPT_RULE, SVInputs,
    evaluate, anded_type0,
)


class C1SVRuleSubsetTests(unittest.TestCase):
    def test_decision_plus_exc_minus_inh_manual(self):
        self.assertEqual(evaluate(DECISION_RULE,SVInputs(80,110,30)),160)

    def test_decision_signed_intermediate_clamped_final(self):
        self.assertEqual(evaluate(DECISION_RULE,SVInputs(80,20,130)),0)
        self.assertEqual(evaluate(DECISION_RULE,SVInputs(80,240,0)),255)

    def test_attention_additive_manual(self):
        self.assertEqual(evaluate(ATTENTION_RULE,SVInputs(0,50,30)),80)
        self.assertEqual(evaluate(ATTENTION_RULE,SVInputs(250,30,30)),255)

    def test_concept_rule_returns_anded_type0(self):
        self.assertEqual(evaluate(CONCEPT_RULE,SVInputs(type0=120,and_type0=90)),90)
        self.assertEqual(evaluate(CONCEPT_RULE,SVInputs(type0=90,and_type0=0)),0)

    def test_type0_conjunction_requires_every_source_active(self):
        self.assertEqual(anded_type0((100,80),(128,128)),90)
        self.assertEqual(anded_type0((100,0),(128,128)),0)
        self.assertEqual(anded_type0((255,255,255),(255,255,255)),255)

    def test_rejects_unknown_rules_instead_of_guessing(self):
        with self.assertRaises(ValueError):
            evaluate(bytes((9,23,12,0,0,0,0,0)),SVInputs())
        with self.assertRaises(ValueError):
            evaluate(b"short",SVInputs())
        with self.assertRaises(TypeError):
            evaluate(DECISION_RULE,{"state":80})

    def test_input_bounds_and_missing_dendrites(self):
        for kwargs in ({"state":True}, {"type0":256}, {"and_type0":-1},
                       {"type1":1.5}):
            with self.assertRaises(ValueError):
                SVInputs(**kwargs)
        with self.assertRaises(ValueError):
            anded_type0((),())
        with self.assertRaises(ValueError):
            anded_type0((1,2),(255,))
        with self.assertRaises(ValueError):
            anded_type0((255,256),(255,255))

    def test_deterministic_twenty_random_sequences(self):
        def replay(seed):
            rng=random.Random(seed)
            return [evaluate(DECISION_RULE,SVInputs(
                rng.randrange(256),rng.randrange(256),rng.randrange(256)
            )) for _ in range(50)]
        for seed in range(20):
            self.assertEqual(replay(seed),replay(seed))


if __name__=="__main__":
    unittest.main()
