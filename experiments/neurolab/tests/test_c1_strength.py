"""E09.02f.4: manually pre-registered strength and loss oracles."""
import random
import unittest

from experiments.neurolab.c1_dendrite_tick import DendriteState
from experiments.neurolab.c1_strength import (
    StrengthState, update_strength,
)


def step(strength, tick, gain_rate=0, gain=0, lose_rate=0, loss=0,
         dendrite=DendriteState()):
    return update_strength(
        StrengthState(dendrite, strength), tick=tick,
        gain_rate=gain_rate, gain_rule_output=gain,
        lose_rate=lose_rate, lose_rule_output=loss,
    )


class C1StrengthTests(unittest.TestCase):
    def test_gain_sets_maximum_to_rule_output(self):
        active=step(2,2,gain_rate=2,gain=80)
        idle=step(2,1,gain_rate=2,gain=80)
        self.assertEqual(active.after.strength,80)
        self.assertTrue(active.did_gain)
        self.assertEqual(idle.after.strength,2)
        self.assertFalse(idle.did_gain)

    def test_loss_decrements_one_unit_only_when_rule_nonzero(self):
        t3=step(10,3,lose_rate=3,loss=255)
        t2=step(10,2,lose_rate=3,loss=255)
        self.assertEqual(t3.after.strength,9)
        self.assertTrue(t3.did_lose)
        self.assertEqual(t2.after.strength,10)
        self.assertFalse(t2.did_lose)

    def test_gain_precedes_loss_same_tick(self):
        result=step(2,6,gain_rate=2,gain=80,lose_rate=3,loss=1)
        self.assertEqual(result.after.strength,79)
        self.assertTrue(result.did_gain)
        self.assertTrue(result.did_lose)

    def test_exhaustion_clears_synaptic_memory(self):
        dendrite=DendriteState(8,6,2)
        result=step(1,1,lose_rate=1,loss=1,dendrite=dendrite)
        self.assertEqual(result.after,StrengthState(DendriteState(),0))
        self.assertTrue(result.did_lose)
        self.assertTrue(result.lost_connection)
        self.assertEqual(result.before.dendrite,dendrite)

    def test_no_loss_when_rule_zero(self):
        dendrite=DendriteState(8,6,2)
        result=step(1,1,lose_rate=1,loss=0,dendrite=dendrite)
        self.assertEqual(result.after,StrengthState(dendrite,1))
        self.assertFalse(result.lost_connection)
        self.assertFalse(result.did_lose)

    def test_maximum_strength_only_blocks_gain(self):
        result=step(255,1,gain_rate=1,gain=255,lose_rate=1,loss=1)
        self.assertEqual(result.after.strength,254)
        self.assertFalse(result.did_gain)
        self.assertTrue(result.did_lose)

    def test_zero_rates_disable_operations(self):
        result=step(2,0,gain_rate=0,gain=255,lose_rate=0,loss=255)
        self.assertEqual(result.after.strength,2)
        self.assertFalse(result.did_gain)
        self.assertFalse(result.did_lose)

    def test_byte_validation_and_purity(self):
        for invalid in (-1,256,True,2.5):
            with self.assertRaises(ValueError):
                StrengthState(DendriteState(),invalid)
            with self.assertRaises(ValueError):
                step(2,5,gain_rate=invalid)
            with self.assertRaises(ValueError):
                step(2,5,loss=invalid)
        for invalid in (-1,True,0.5):
            with self.assertRaises(ValueError):
                step(2,invalid)
        initial=StrengthState(DendriteState(4,3,0),2)
        result=update_strength(initial,tick=2,gain_rate=2,gain_rule_output=80,
                               lose_rate=0,lose_rule_output=0)
        self.assertEqual(initial.strength,2)
        self.assertEqual(result.after.strength,80)

    def test_bounds_and_reproducibility_across_twenty_seeds(self):
        for seed in range(20):
            def replay():
                rng=random.Random(seed)
                state=StrengthState(DendriteState(12,40,20),4)
                sequence=[]
                for tick in range(160):
                    trace=update_strength(
                        state,tick=tick,
                        gain_rate=rng.randrange(256),
                        gain_rule_output=rng.randrange(256),
                        lose_rate=rng.randrange(256),
                        lose_rule_output=rng.randrange(256),
                    )
                    state=trace.after
                    sequence.append((state,trace.lost_connection))
                    self.assertTrue(0<=state.strength<=255)
                return sequence
            self.assertEqual(replay(),replay())

    def test_zero_strength_does_not_fake_migration(self):
        result=step(0,0,gain_rate=0,gain=0,lose_rate=1,loss=255)
        self.assertFalse(result.lost_connection)
        self.assertEqual(result.after.strength,0)
        self.assertFalse(hasattr(result,"new_source_neuron"))


if __name__=="__main__":
    unittest.main()
