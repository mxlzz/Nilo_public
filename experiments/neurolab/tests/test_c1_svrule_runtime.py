"""E09.02f.6: fixed oracles for original C1 SVRule interpreter."""
import random
import unittest

from experiments.neurolab.c1_svrule_runtime import (
    C1SVTable, evaluate, evaluate_trace,
)


def rule(*ops):
    if len(ops)>=8:
        raise ValueError("fixtures require terminator")
    return bytes((*ops, *(0 for _ in range(8-len(ops)))))


class C1SVRuleRuntimeTests(unittest.TestCase):
    def test_output_true_input(self):
        r=rule(10,22,16)
        self.assertEqual(evaluate(r,C1SVTable(output=80,input=127)),127)
        stopped=evaluate_trace(r,C1SVTable(output=0,input=127))
        self.assertEqual(stopped.result,0)
        self.assertTrue(stopped.gated)
        self.assertEqual(tuple(step.opcode for step in stopped.trace),(10,22))

    def test_gain_strength_requires_all_gates(self):
        r=rule(18,22,5,22,19)
        self.assertEqual(evaluate(r,C1SVTable(susceptibility=4,chem0=255,stw=30)),30)
        self.assertEqual(evaluate(r,C1SVTable(susceptibility=0,chem0=255,stw=30)),0)
        self.assertEqual(evaluate(r,C1SVTable(susceptibility=4,chem0=0,stw=30)),0)
        self.assertEqual(evaluate(r,C1SVTable(susceptibility=4,chem0=255,stw=0)),0)

    def test_concept_gain_uses_output_and_chemical(self):
        r=rule(10,22,5)
        self.assertEqual(evaluate(r,C1SVTable(output=90,chem0=51)),51)
        self.assertEqual(evaluate(r,C1SVTable(output=0,chem0=51)),0)

    def test_loss_strength_chemical_2(self):
        self.assertEqual(evaluate(rule(7),C1SVTable(chem2=45)),45)

    def test_decision_sequential_saturation(self):
        self.assertEqual(
            evaluate(rule(9,23,12,24,13),C1SVTable(
                state=80,type0=240,type1=200,
            )),55
        )
        self.assertEqual(evaluate(rule(14),C1SVTable(and_type0=253)),253)

    def test_times_and_saturated_increment_decrement(self):
        self.assertEqual(evaluate(rule(4,25,4),C1SVTable()),254)
        self.assertEqual(evaluate(rule(3,23,4),C1SVTable()),255)
        self.assertEqual(evaluate(rule(1,27),C1SVTable()),0)
        self.assertEqual(evaluate(rule(4,26),C1SVTable()),255)

    def test_all_operand_indices_are_exactly_mapped(self):
        values=C1SVTable(
            chem0=5,chem1=6,chem2=7,chem3=8,
            state=9,output=10,threshold=11,
            type0=12,type1=13,and_type0=14,and_type1=15,
            input=16,conduct=17,susceptibility=18,stw=19,
            ltw=20,strength=21,
        )
        self.assertEqual(values.values(),
                         (0,0,1,64,255,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21))
        for operand in range(1,22):
            self.assertEqual(evaluate(rule(operand),values),values.values()[operand])

    def test_captured_old_values_not_overwritten_mid_tick(self):
        # At the start of the tick SUSCEPT=0, STW=0. Reinforcement can
        # produce 4 and 3, but the gain rule still sees OLD zero snapshot.
        gain=rule(18,22,5,22,19)
        captured=C1SVTable(susceptibility=0,stw=0,chem0=255)
        self.assertEqual(evaluate(gain,captured),0)
        new_next_tick=C1SVTable(susceptibility=4,stw=3,chem0=255)
        self.assertEqual(evaluate(gain,new_next_tick),3)
        self.assertEqual(captured.susceptibility,0)

    def test_true_with_nonzero_passes_through(self):
        output=evaluate_trace(rule(9,22),C1SVTable(state=80))
        self.assertEqual(output.result,80)
        self.assertFalse(output.gated)
        self.assertEqual(tuple(x.opcode for x in output.trace),(9,22))

    def test_invalid_or_unterminated_input(self):
        for invalid in (-1,256,True,1.25):
            with self.assertRaises(ValueError):
                C1SVTable(state=invalid)
        for invalid in (b"",bytes([9]*8),rule(9,23),rule(9,23,0),rule(9,23,22)):
            with self.subTest(rule=invalid), self.assertRaises(ValueError):
                evaluate(invalid,C1SVTable())
        with self.assertRaises(ValueError):
            evaluate(rule(28),C1SVTable())
        with self.assertRaises(TypeError):
            evaluate(rule(9),{"state":80})

    def test_determinism_with_twenty_seeds(self):
        def run(seed):
            rng=random.Random(seed)
            rr=rule(9,23,12,24,13)
            return tuple(
                evaluate(rr,C1SVTable(state=rng.randrange(256),
                                      type0=rng.randrange(256),
                                      type1=rng.randrange(256)))
                for _ in range(150)
            )
        for seed in range(20):
            self.assertEqual(run(seed),run(seed))


if __name__=="__main__":
    unittest.main()
