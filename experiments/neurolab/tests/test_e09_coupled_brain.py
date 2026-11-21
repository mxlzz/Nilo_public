"""E09.02i-I2 one-way brain/chem temporal contract and exact replay.

No dataset targets, desired actions or reward labels are passed into the
brain/chem integration. This verifies wiring, not a G05/G09 learning gate.
"""
from dataclasses import replace
import inspect
import json
from pathlib import Path
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_coupled_brain import (
    CoupledState, coupled_tick, initial_coupled, checkpoint, restore,
)
from experiments.neurolab.e09_chemical_bridge import SourcePort
from experiments.neurolab.e09_historical_emitter import Emitter
from experiments.neurolab.tests.test_e09_chemical_bridge import (
    original_receptors, original_reaction, pool,
)


class CoupledBrainTests(unittest.TestCase):
    def test_brain_reads_prior_chemical_snapshot_never_current_reaction(self):
        brain=C1ContextBrain(9)
        rs=original_receptors()
        gen111=original_reaction(111)
        initial=initial_coupled(brain,rs,pool=pool(c49=20))
        first=coupled_tick(brain,initial,0,(),rs,(gen111,))
        self.assertEqual(first.read_chem,(0,0,16,16))
        self.assertEqual(first.next_chem,(19,0,16,16))
        self.assertEqual(first.chemical_trace.after.concept_chem[0],0)
        self.assertEqual(first.brain_trace,brain.step(initial.brain,0,
                                                      (0,0,16,16)))
        self.assertEqual(first.chemical_trace.after.pool[51],12)
        next_tick=coupled_tick(brain,first.after,1,(),rs,(gen111,))
        self.assertEqual(next_tick.read_chem[0],19)
        self.assertEqual(next_tick.next_chem[0],7)
        self.assertEqual(next_tick.chemical_trace.after.concept_chem[0],11)
        self.assertEqual(next_tick.after.brain.tick,2)
        self.assertEqual(next_tick.after.chemistry.tick,2)

    def test_no_magic_brain_to_source_port_mapping(self):
        brain=C1ContextBrain(2)
        rs=original_receptors()
        emitter=Emitter(124,0,6,1,53,0,1,255,1)
        initial=initial_coupled(brain,rs,ports=(SourcePort(6,1,80),))
        first=coupled_tick(brain,initial,0,(emitter,),rs,())
        self.assertEqual(first.after.chemistry.ports,(SourcePort(6,1,0),))
        self.assertEqual(first.after.chemistry.pool[53],79)
        # Brain responds but does not secretly replenish the external port.
        second=coupled_tick(brain,first.after,1,(emitter,),rs,())
        self.assertEqual(second.after.chemistry.pool[53],79)
        self.assertFalse(second.chemical_trace.emitter_results[0].eligible)

    def test_freeze_learning_does_not_freeze_chemistry(self):
        brain=C1ContextBrain(3)
        rs=original_receptors()
        state=initial_coupled(brain,rs,pool=pool(c49=20))
        old=state.brain.dendrites
        trace=coupled_tick(brain,state,0,(),rs,(original_reaction(111),),
                           learn=False)
        self.assertEqual(trace.after.brain.dendrites,old)
        self.assertNotEqual(trace.after.chemistry.pool,state.chemistry.pool)
        self.assertEqual(trace.after.brain.tick,1)

    def test_full_checkpoint_replay_of_continuous_states(self):
        brain=C1ContextBrain(4)
        rs=original_receptors()
        rx=(original_reaction(111),)
        em=(Emitter(124,0,6,1,53,0,1,255,1),)
        start=initial_coupled(brain,rs,pool=pool(c49=20),
                               ports=(SourcePort(6,1,80),))
        states=[start]
        for context in (0,1,0):
            states.append(coupled_tick(brain,states[-1],context,em,rs,rx).after)
        saved=checkpoint(brain,states[-1])
        restored=restore(brain,saved)
        self.assertEqual(restored,states[-1])
        contexts=(1,1,0,0,1,0)
        left=states[-1]
        right=restored
        for context in contexts:
            a=coupled_tick(brain,left,context,em,rs,rx)
            b=coupled_tick(brain,right,context,em,rs,rx)
            self.assertEqual(a,b)
            left,right=a.after,b.after
        self.assertEqual(checkpoint(brain,left),checkpoint(brain,right))
        self.assertEqual(start.brain.tick,0)

    def test_mismatched_tick_rejected(self):
        brain=C1ContextBrain(7)
        state=initial_coupled(brain,original_receptors())
        mismatch=replace(state.chemistry,tick=5)
        with self.assertRaisesRegex(ValueError,"ticks must match"):
            CoupledState(state.brain,mismatch)

    def test_strict_checkpoint_schema_and_seed(self):
        brain=C1ContextBrain(1)
        data=checkpoint(brain,initial_coupled(brain,original_receptors()))
        with self.assertRaises(ValueError):
            restore(C1ContextBrain(2),data)
        obj=json.loads(data)
        obj["extra"]="forbidden"
        with self.assertRaisesRegex(ValueError,"schema"):
            restore(brain,json.dumps(obj))
        obj.pop("extra")
        obj["chemistry"].pop("tick")
        with self.assertRaisesRegex(ValueError,"chemical checkpoint"):
            restore(brain,json.dumps(obj))

    def test_integrator_does_not_take_correct_action_or_reward_input(self):
        allowed=set(inspect.signature(coupled_tick).parameters)
        self.assertEqual(allowed,{
            "brain","state","context","emitters","receptors","reactions","learn",
        })
        self.assertFalse({"correct_action","reward","target","oracle"} & allowed)

    def test_repeated_seed_deterministic_without_mutating_state(self):
        rs=original_receptors()
        for seed in (0,1,7,101):
            brain=C1ContextBrain(seed)
            state=initial_coupled(brain,rs,pool=pool(c49=12))
            a=coupled_tick(brain,state,seed%2,(),rs,())
            b=coupled_tick(brain,state,seed%2,(),rs,())
            self.assertEqual(a,b)
            self.assertEqual(state.brain.tick,0)
            self.assertEqual(state.chemistry.pool[49],12)


if __name__=="__main__":
    unittest.main()
