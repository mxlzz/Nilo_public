"""E09.02f.3 — manual oracles of the statically disassembled C1 dendrite tick."""
import random
import unittest

from experiments.neurolab.c1_dendrite_tick import (
    DendriteRates, DendriteState, checkpoint, restore, transition,
)
from experiments.neurolab.twin_weight import TwinSynapse


def next_state(state, tick, target=255, chem=255, rates=DendriteRates()):
    return transition(
        state, rates=rates, tick=tick,
        susceptibility_rule_output=target,
        reinforcement_rule_output=chem,
    ).after


class C1DendriteTickTests(unittest.TestCase):
    def test_initial_chemical_reinforcement_manual(self):
        first=transition(
            DendriteState(),tick=1,
            susceptibility_rule_output=255,reinforcement_rule_output=255,
        )
        self.assertEqual(first.after,DendriteState(4,3,0))
        self.assertEqual(first.reinforcement_effect,3)
        self.assertEqual(first.stw_after_reinforcement,3)

    def test_second_pulse_and_masked_stw_relaxation(self):
        result=transition(
            DendriteState(4,3,0),tick=7,
            susceptibility_rule_output=255,reinforcement_rule_output=255,
        )
        self.assertEqual(result.reinforcement_effect,7)
        self.assertEqual(result.stw_after_reinforcement,7)
        self.assertEqual(result.stw_after_relaxation,6)
        self.assertEqual(result.after,DendriteState(8,6,0))

    def test_no_chemical_still_decays_and_relaxes(self):
        result=transition(
            DendriteState(8,6,0),tick=7,
            susceptibility_rule_output=0,reinforcement_rule_output=0,
        )
        self.assertEqual(result.after,DendriteState(7,5,0))
        self.assertEqual(result.reinforcement_effect,0)

    def test_ltw_periodicity_from_real_rates(self):
        before=DendriteState(0,200,100)
        t127=next_state(before,127,target=0,chem=0)
        self.assertEqual(t127,DendriteState(0,197,100))
        t128=next_state(t127,128,target=0,chem=0)
        self.assertEqual(t128,DendriteState(0,197,101))

    def test_susceptibility_x86_byte_wrap_is_not_clamped(self):
        s=next_state(DendriteState(253,5,5),tick=1,target=255,chem=0)
        self.assertEqual(s.susceptibility,1)
        self.assertEqual(s.stw,5)
        self.assertEqual(s.ltw,5)

    def test_no_chemical_cannot_create_reinforcement(self):
        for prior in (DendriteState(0,0,0),DendriteState(250,0,0),
                      DendriteState(128,140,80)):
            result=transition(prior,tick=7,susceptibility_rule_output=255,
                              reinforcement_rule_output=0)
            self.assertEqual(result.reinforcement_effect,0)
            self.assertLessEqual(result.after.stw,max(prior.stw,prior.ltw))

    def test_ltw_plus_chemical_cannot_overflow(self):
        s=DendriteState(200,250,250)
        t=transition(s,tick=1,susceptibility_rule_output=255,
                     reinforcement_rule_output=255)
        self.assertEqual(t.reinforcement_effect,(204*255)>>8)
        self.assertEqual(t.after.stw,255)
        self.assertEqual(t.after.ltw,250)

    def test_checkpoint_continuation(self):
        rates=DendriteRates()
        states=[]
        original=DendriteState()
        generator=random.Random(101)
        inputs=[(generator.randrange(256),generator.randrange(256))
                for _ in range(250)]
        for tick,(target,chem) in enumerate(inputs[:80]):
            original=next_state(original,tick,target,chem,rates)
        blob=checkpoint(original,rates,80)
        saved,r2,next_tick=restore(blob)
        self.assertEqual((saved,r2,next_tick),(original,rates,80))
        for tick,(target,chem) in enumerate(inputs[80:],start=80):
            original=next_state(original,tick,target,chem,rates)
            saved=next_state(saved,tick,target,chem,r2)
        self.assertEqual(original,saved)
        with self.assertRaises(ValueError):
            restore(blob.replace("C1-DENDRITE-F3-v1","invalid"))

    def test_validation_and_zero_rates(self):
        for bad in (-1,256,True,2.5):
            with self.assertRaises(ValueError):
                DendriteState(susceptibility=bad)
            with self.assertRaises(ValueError):
                DendriteRates(ltw_rate=bad)
            with self.assertRaises(ValueError):
                next_state(DendriteState(),1,target=bad)
        for invalid_tick in (-1,True,0.5):
            with self.assertRaises(ValueError):
                next_state(DendriteState(),invalid_tick)
        self.assertEqual(next_state(DendriteState(),0,rates=DendriteRates(0,0,0)),
                         DendriteState(4,0,0))

    def test_determinism_and_bounded_states_twenty_seeds(self):
        for seed in range(20):
            def replay():
                rng=random.Random(seed)
                state=DendriteState()
                snapshots=[]
                rates=DendriteRates(
                    rng.randrange(256),rng.randrange(256),rng.randrange(256)
                )
                for tick in range(180):
                    state=next_state(
                        state,tick,rng.randrange(256),rng.randrange(256),rates,
                    )
                    self.assertTrue(0<=state.susceptibility<=255)
                    self.assertTrue(0<=state.stw<=255)
                    self.assertTrue(0<=state.ltw<=255)
                    snapshots.append(state)
                return snapshots
            self.assertEqual(replay(),replay())

    def test_experimental_twin_model_remains_independent(self):
        # Earlier E04 model and its equations are intentionally untouched.
        self.assertEqual(TwinSynapse(128,128).step(+1),TwinSynapse(154,129))
        self.assertNotEqual(
            next_state(DendriteState(),1),
            DendriteState(0,26,1),
        )


if __name__=="__main__":
    unittest.main()
