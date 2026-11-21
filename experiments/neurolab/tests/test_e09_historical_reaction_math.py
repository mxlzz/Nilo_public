"""E09h.2 — isolated reaction arithmetic with synthetic genes, no original bin in CI."""
import unittest

from experiments.neurolab.c1_reaction_inspector import Reaction
from experiments.neurolab.e09_historical_reaction_math import (
    reaction_step, process_reactions, original_fixtures, pool_with,
)

R71 = Reaction(71,0,1,33,1,1,1,49,1,0,8)
R111 = Reaction(111,0,1,49,1,0,1,51,1,54,16)
R112 = Reaction(112,0,1,50,1,0,1,51,1,55,16)


class HistoricalReactionTests(unittest.TestCase):
    def test_drive_decrease_produces_reward_from_original_gene_fixture(self):
        before = pool_with(c33=10,c1=15)
        after,trace = reaction_step(before,R71,0)
        self.assertEqual(trace.capacity,10)
        self.assertEqual(trace.residual,1)
        self.assertEqual(trace.reacted_units,9)
        self.assertEqual((after[33],after[1],after[49]),(1,6,9))
        self.assertEqual((before[33],before[1],before[49]),(10,15,0))

    def test_reward_to_reinforcement_and_echo(self):
        after,event = reaction_step(pool_with(c49=20),R111,0)
        self.assertEqual(event.capacity,20)
        self.assertEqual(event.residual,8)
        self.assertEqual(event.reacted_units,12)
        self.assertEqual((after[49],after[51],after[54]),(8,12,12))

    def test_punishment_to_reinforcement_and_echo(self):
        after,event = reaction_step(pool_with(c50=20),R112,0)
        self.assertEqual((after[50],after[51],after[55]),(8,12,12))

    def test_sequential_reactions_can_chain_within_same_tick(self):
        initial=pool_with(c33=10,c1=15)
        after,events=process_reactions(initial,(R71,R111),0)
        self.assertEqual([ev.reacted_units for ev in events],[9,5])
        self.assertEqual((after[49],after[51],after[54]),(4,5,5))
        reversed_after,_=process_reactions(initial,(R111,R71),0)
        self.assertEqual((reversed_after[49],reversed_after[51],reversed_after[54]),
                         (9,0,0))

    def test_partial_supply_limits_extent(self):
        state=pool_with(c33=1,c1=15)
        after,ev=reaction_step(state,R71,0)
        self.assertEqual(ev.capacity,1)
        self.assertEqual(ev.reacted_units,1)
        self.assertEqual((after[33],after[1],after[49]),(0,14,1))

    def test_invalid_state_and_unverified_genome(self):
        with self.assertRaises(ValueError):
            reaction_step((0,0),R71,0)
        with self.assertRaises(ValueError):
            reaction_step(tuple([0]*255+[-1]),R71,0)
        with self.assertRaises(ValueError):
            reaction_step(pool_with(),R71,-1)
        with self.assertRaises(ValueError):
            original_fixtures(b"some C1 bytes")

    def test_deterministic_and_inputs_immutable(self):
        state=pool_with(c33=10,c1=15)
        first=process_reactions(state,(R71,R111),0)
        second=process_reactions(state,(R71,R111),0)
        self.assertEqual(first,second)
        self.assertEqual(state[49],0)


if __name__ == "__main__":
    unittest.main()
