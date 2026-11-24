"""E09.02b — pruebas independientes del microcircuito de 5 unidades."""
import unittest

from experiments.neurolab.c1_microcircuit import MicroWeights,run_once


class C1MicroCircuitTests(unittest.TestCase):
    def test_empty_inputs_do_not_invent_an_action(self):
        out=run_once(0,0)
        self.assertEqual((out.concept,out.d0,out.d1,out.action),(0,80,80,None))
        self.assertEqual(out.neuron_count,5)

    def test_one_input_does_not_activate_and_concept(self):
        for p0,p1 in ((255,0),(0,255),(1,0),(0,1)):
            with self.subTest(inputs=(p0,p1)):
                out=run_once(p0,p1)
                self.assertEqual(out.concept,0)
                self.assertEqual(out.action,None)

    def test_manual_conjunctive_oracle(self):
        out=run_once(100,80)
        self.assertEqual((out.p0,out.p1,out.concept,out.d0,out.d1,out.action),
                         (100,80,90,170,0,"D0"))

    def test_saturation_and_inhibition(self):
        out=run_once(255,255)
        self.assertEqual((out.concept,out.d0,out.d1,out.action),(255,255,0,"D0"))

    def test_negative_influence_can_select_d1(self):
        weights=MicroWeights(d0_exc=0,d0_inh=255,d1_exc=255,d1_inh=0)
        out=run_once(100,80,weights=weights)
        self.assertEqual((out.d0,out.d1,out.action),(0,170,"D1"))

    def test_no_learned_weights_or_hidden_reward(self):
        cfg=MicroWeights()
        a=run_once(255,255,weights=cfg)
        b=run_once(255,255,weights=cfg)
        self.assertEqual(a,b)
        self.assertEqual(cfg,MicroWeights())
        self.assertFalse(hasattr(a,"reward"))
        self.assertFalse(hasattr(cfg,"learn"))

    def test_input_validation(self):
        for bad in (-1,256,True,0.5):
            with self.subTest(bad=repr(bad)),self.assertRaises(ValueError):
                run_once(bad,0)
        with self.assertRaises(ValueError):
            MicroWeights(d0_exc=-1)
        with self.assertRaises(ValueError):
            MicroWeights(perception_to_concept=(128,))
        with self.assertRaises(TypeError):
            run_once(1,2,weights={})

    def test_concept_strength_monotone_with_all_inputs_nonzero(self):
        last=None
        for v in range(1,256):
            result=run_once(v,v)
            if last is not None:
                self.assertGreaterEqual(result.concept,last)
            last=result.concept


if __name__=="__main__":
    unittest.main()
