"""E09.02g.5: two-context six-neuron tests and tabular control.

The preregistered gate is an observable statistic, NOT a required
unit-test success. A scientific failure must remain in CI output.
"""
import random
import unittest

from experiments.neurolab.c1_context_brain import (
    C1ContextBrain,ContextBrainState,
)
from experiments.neurolab.e09_context_protocol import (
    BLOCK_TICKS,TRAIN_BLOCKS,TEST_BLOCKS,ZERO,MAPPING_A,MAPPING_B,
    blocks,train_brain,evaluate_brain,tabular_step_choice,
    train_tabular,evaluate_tabular,run_all,run_seed,
)


class TwoConceptBrainTests(unittest.TestCase):
    def test_six_units_and_exactly_eight_plastic_dendrites(self):
        brain=C1ContextBrain(2)
        state=brain.initial()
        self.assertEqual(len(state.dendrites),8)
        self.assertEqual(state.neuron_states,(80,80))
        self.assertEqual(state.concept_outputs,(0,0))
        self.assertTrue(all(d.dendrite.stw==0 and d.strength==2
                            for d in state.dendrites))

    def test_first_tick_context_only_appears_after_decision(self):
        brain=C1ContextBrain(2)
        first=brain.step(brain.initial(),0,ZERO)
        self.assertEqual(first.old_concepts,(0,0))
        self.assertEqual(first.scores,(80,80))
        self.assertEqual(first.after.concept_outputs,(126,0))
        second=brain.step(first.after,1,ZERO)
        self.assertEqual(second.old_concepts,(126,0))
        self.assertEqual(second.after.concept_outputs,(0,126))

    def test_symmetric_concept_detection_one_dendrite_each(self):
        brain=C1ContextBrain(2)
        first=brain.step(brain.initial(),1,ZERO)
        self.assertEqual(first.after.concept_outputs,(0,126))
        self.assertEqual(first.after.tick,1)
        second=brain.step(first.after,0,ZERO)
        self.assertEqual(second.old_concepts,(0,126))
        self.assertEqual(second.after.concept_outputs,(126,0))

    def test_blind_ablation_removes_context_information(self):
        brain=C1ContextBrain(2,blind=True)
        a=brain.step(brain.initial(),0,ZERO,learn=False)
        b=brain.step(brain.initial(),1,ZERO,learn=False)
        self.assertEqual(a.seen_context,0)
        self.assertEqual(b.seen_context,0)
        self.assertEqual(a.after,b.after)
        self.assertEqual(a.after.concept_outputs,(126,0))

    def test_balanced_blocks_are_seeded_and_nonperiodic(self):
        for seed in range(20):
            seq=blocks(seed,10000,TRAIN_BLOCKS)
            self.assertEqual(seq.count(0),16)
            self.assertEqual(seq.count(1),16)
            self.assertEqual(seq,blocks(seed,10000,TRAIN_BLOCKS))
            self.assertEqual(len(blocks(seed,30000,TEST_BLOCKS)),16)
        self.assertNotEqual(blocks(0,10000,TRAIN_BLOCKS),
                            tuple(i%2 for i in range(TRAIN_BLOCKS)))

    def test_training_chemicals_are_delayed_and_not_in_brain(self):
        brain=C1ContextBrain(3)
        state=brain.initial()
        self.assertEqual(set(vars(brain)),{"seed","blind"})
        self.assertFalse(hasattr(brain,"correct_action"))
        self.assertFalse(hasattr(brain,"target"))
        learned,pulse=train_brain(brain,state,ZERO,(0,),MAPPING_A,learn=True)
        self.assertEqual(learned.tick,BLOCK_TICKS)
        self.assertEqual(len(pulse),4)
        self.assertIn(pulse,((255,0,0,0),(0,255,0,0)))
        self.assertNotEqual(learned.dendrites,state.dendrites)

    def test_frozen_and_holdout_leave_original_memory_unchanged(self):
        brain=C1ContextBrain(5)
        start=brain.initial()
        frozen,pulse=train_brain(brain,start,ZERO,
                                 blocks(5,10000,TRAIN_BLOCKS),
                                 MAPPING_A,learn=False)
        self.assertEqual(start.dendrites,frozen.dendrites)
        self.assertEqual(frozen.tick,256)
        original=frozen
        result=evaluate_brain(brain,frozen,blocks(5,30000,TEST_BLOCKS),MAPPING_A)
        self.assertEqual(frozen,original)
        self.assertEqual(result["total_ticks"],128)
        self.assertEqual(result["steady_ticks"],96)

    def test_table_updates_only_delayed_context_action(self):
        q=[[0.,0.],[0.,0.]]
        learned,pending,tick=train_tabular(
            q,None,(0,),MAPPING_A,seed=3,tick=0
        )
        self.assertEqual(tick,8)
        self.assertEqual(len(pending),3)
        self.assertTrue(any(x!=0.0 for x in learned[0]))
        self.assertEqual(learned[1],[0.,0.])
        # The lookup only reads context, not an external correct label.
        self.assertEqual(len(tabular_step_choice(q,0,seed=3,tick=9,explore=False)),2)

    def test_tabular_holdout_does_not_change_weights(self):
        q=[[1.,-1.],[-1.,1.]]
        before=[list(x) for x in q]
        outcome=evaluate_tabular(q,blocks(0,30000,TEST_BLOCKS),
                                 MAPPING_A,seed=0,start_tick=256)
        self.assertEqual(q,before)
        self.assertEqual(outcome["overall"],1.0)
        self.assertEqual(outcome["steady"],1.0)

    def test_checkpoint_roundtrip_preserves_context_and_synapses(self):
        brain=C1ContextBrain(6)
        seq=blocks(6,10000,TRAIN_BLOCKS)
        full,_=train_brain(brain,brain.initial(),ZERO,seq,MAPPING_A,learn=True)
        half,pending=train_brain(brain,brain.initial(),ZERO,seq[:12],
                                 MAPPING_A,learn=True)
        restored=brain.restore(brain.checkpoint(half))
        resumed,_=train_brain(brain,restored,pending,seq[12:],
                              MAPPING_A,learn=True)
        self.assertEqual(resumed,full)
        with self.assertRaises(ValueError):
            C1ContextBrain(7).restore(brain.checkpoint(full))

    def test_validation_rejects_illegal_sensory_or_chemical_inputs(self):
        brain=C1ContextBrain(0)
        for bad in (-1,2,True,.5):
            with self.assertRaises(ValueError):
                brain.step(brain.initial(),bad,ZERO)
        with self.assertRaises(ValueError):
            brain.step(brain.initial(),0,(256,0,0,0))
        with self.assertRaises(ValueError):
            ContextBrainState((brain.initial().dendrites[0],))

    def test_full_results_include_both_contexts_and_every_control(self):
        result=run_all()
        self.assertEqual(result["n_seeds"],20)
        self.assertEqual(result["n_units"],6)
        self.assertEqual(result["n_plastic_dendrites"],8)
        self.assertEqual(result["train_ticks_per_phase"],256)
        self.assertEqual(result["holdout_ticks_per_phase"],128)
        for phase in ("first","reversed"):
            for name in ("neural","frozen","blind","tabular"):
                with self.subTest(phase=phase,name=name):
                    self.assertTrue(0<=result["mean_steady"][name][phase]<=1)
                    self.assertTrue(0<=result["mean_overall"][name][phase]<=1)
        self.assertEqual(result["passed"],(
            result["good_both"]>=18
            and result["advantage_first_vs_frozen"]>=.25
            and result["advantage_first_vs_blind"]>=.20
        ))
        self.assertEqual([x["seed"] for x in result["per_seed"]],list(range(20)))
        self.assertTrue(all(x["neural_after_reversal"]["tick"]==512
                            and len(x["neural_after_reversal"]["synapses"])==8
                            for x in result["per_seed"]))

    def test_seeded_reproducibility(self):
        a=run_seed(2)
        b=run_seed(2)
        self.assertEqual(a,b)


if __name__=="__main__":
    unittest.main()
