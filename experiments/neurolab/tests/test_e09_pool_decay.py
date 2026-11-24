"""E09.02i-I1b: 256-slot decay, actual C1 helper and phase order.

All concentrations/rates in these tests are synthetic. C1 GEN
half-life rate provenance remains explicitly unresolved.
"""
import unittest

from experiments.neurolab.e09_pool_decay import (
    decay_pool, chemical_bridge_tick_with_decay,
)
from experiments.neurolab.e09_chemical_bridge import (
    initial_bridge, chemical_bridge_tick,
)
from experiments.neurolab.tests.test_e09_chemical_bridge import (
    original_receptors, original_reaction, pool,
)


def rates(**named):
    values=[0]*256
    for key,value in named.items():
        values[int(key[1:])]=value
    return tuple(values)


class GlobalChemicalDecayTests(unittest.TestCase):
    def test_existing_historical_decay_oracles_6_and_7(self):
        initial=pool(c49=200,c54=30)
        cfg=rates(c49=80,c54=255)
        t6=decay_pool(initial,cfg,6)
        t7=decay_pool(initial,cfg,7)
        self.assertEqual(t6[49],200)
        self.assertEqual(t7[49],194)
        self.assertEqual(t7[54],30)
        self.assertEqual(initial[49],200)
        self.assertEqual(len(t7),256)

    def test_receptor_samples_before_reaction_and_decay(self):
        receptors=original_receptors()
        state=initial_bridge(receptors,pool=pool(c49=20,c51=0))
        reaction=original_reaction(111)
        original=chemical_bridge_tick(state,(),receptors,(reaction,))
        self.assertEqual(original.after.pool[51],12)
        new=chemical_bridge_tick_with_decay(
            state,(),receptors,(reaction,),rates=rates(c51=0,c54=0,c49=255)
        )
        self.assertEqual(new.core.concept_at_receptors[0],0)
        self.assertEqual(new.core.decision_at_receptors[0],19)
        self.assertEqual(new.core.after.pool[51],12)
        self.assertEqual(new.after.pool[51],0)
        self.assertIn(51,new.modified_ids)
        self.assertNotEqual(original.after.pool,new.after.pool)
        self.assertEqual(state.pool[49],20)

    def test_receptors_can_see_old_chemical_before_end_of_tick_decay(self):
        receptors=original_receptors()
        state=initial_bridge(receptors,pool=pool(c51=20))
        out=chemical_bridge_tick_with_decay(
            state,(),receptors,(),rates=rates()
        )
        self.assertEqual(out.core.concept_at_receptors[0],19)
        self.assertEqual(out.after.concept_chem[0],19)
        self.assertEqual(out.after.pool[51],0)
        next_tick=chemical_bridge_tick_with_decay(
            out.after,(),receptors,(),rates=rates()
        )
        self.assertEqual(next_tick.after.concept_chem[0],0)

    def test_invalid_shape_types_and_ticks_rejected(self):
        for bad in ((0,),list((0,)*256),tuple([0]*255+[256])):
            with self.subTest(bad_type=type(bad).__name__):
                with self.assertRaises(ValueError):
                    decay_pool(pool(),bad,1)
        with self.assertRaises(ValueError):
            decay_pool((0,),rates(),0)
        with self.assertRaises(ValueError):
            decay_pool(pool(),rates(),-1)
        with self.assertRaises(ValueError):
            decay_pool(pool(),rates(),True)

    def test_replay_pure_function(self):
        data=pool(c49=200)
        cfg=rates(c49=80)
        self.assertEqual(decay_pool(data,cfg,7),decay_pool(data,cfg,7))
        self.assertEqual(data[49],200)
        self.assertEqual(cfg[49],80)


if __name__=="__main__":
    unittest.main()
