"""E09.02g.3: manual temporal oracles and preregistered continuous clock."""
import json
import unittest

from experiments.neurolab.c1_continuous_brain import (
    C1ContinuousBrain,ContinuousBrainState,
)
from experiments.neurolab.c1_dendrite_tick import DendriteState
from experiments.neurolab.c1_synapse_integrated import C1SynapseState
from experiments.neurolab.e09_continuous_protocol import (
    ZERO,evaluate,run_all,run_seed,train,
)


class ContinuousBrainTests(unittest.TestCase):
    def test_tick1_decision_cannot_see_concept_not_yet_processed(self):
        brain=C1ContinuousBrain(1,tie_mode="first_index")
        initial=brain.initial()
        trace=brain.step(initial,ZERO)
        self.assertEqual(trace.concept_previous,0)
        self.assertEqual(trace.decision_outputs_previous,(0,0))
        self.assertEqual(trace.decision_scores,(80,80))
        self.assertEqual(trace.action,"D0")
        self.assertEqual(trace.winner_outputs,(80,0))
        self.assertEqual(trace.after.concept_output,253)
        self.assertEqual(trace.after.tick,1)
        self.assertTrue(all(d.dendrite.susceptibility==0 for d in trace.after.dendrites))

    def test_tick2_previous_wta_output_gates_reinforcement(self):
        brain=C1ContinuousBrain(1,tie_mode="first_index")
        first=brain.step(brain.initial(),ZERO)
        second=brain.step(first.after,(255,0,0,0))
        self.assertEqual(second.concept_previous,253)
        self.assertEqual(second.decision_outputs_previous,(80,0))
        self.assertEqual(second.decision_scores,(80,80))
        self.assertEqual(second.after.dendrites[0].dendrite.susceptibility,4)
        self.assertEqual(second.after.dendrites[0].dendrite.stw,3)
        self.assertEqual(second.after.dendrites[1].dendrite.stw,0)
        self.assertEqual(second.after.dendrites[2].dendrite.susceptibility,0)
        self.assertEqual(second.after.dendrites[2].dendrite.stw,0)

    def test_tick3_uses_stw_from_prior_tick_not_before(self):
        brain=C1ContinuousBrain(1,tie_mode="first_index")
        first=brain.step(brain.initial(),ZERO)
        second=brain.step(first.after,(255,0,0,0))
        third=brain.step(second.after,ZERO)
        self.assertEqual(third.decision_scores,(81,80))
        self.assertEqual(third.winner_outputs,(81,0))
        self.assertEqual(third.action,"D0")

    def test_neuron_state_persists_and_relaxes_toward_80(self):
        brain=C1ContinuousBrain(1,tie_mode="first_index")
        s=brain.initial()
        changed=list(s.dendrites)
        changed[0]=C1SynapseState(DendriteState(0,200,0),2)
        s=ContinuousBrainState(tuple(changed),(80,80),(80,0),253,2)
        tr=brain.step(s,ZERO,learn=False)
        self.assertEqual(tr.decision_scores[0],178)
        self.assertEqual(tr.after.neuron_states[0],145)
        self.assertNotEqual(tr.after.neuron_states[0],80)

    def test_even_with_reward_on_first_tick_old_output_blocks_susceptibility(self):
        brain=C1ContinuousBrain(1,tie_mode="first_index")
        tr=brain.step(brain.initial(),(255,0,0,0))
        self.assertTrue(all(d.dendrite.stw==0 for d in tr.after.dendrites))

    def test_holdout_advances_neurons_without_mutating_original_state(self):
        brain=C1ContinuousBrain(3,tie_mode="random_tie")
        state,pulse=train(brain,brain.initial(),ZERO,"D0",60)
        before=state
        result=evaluate(brain,state,"D0",80)
        self.assertEqual(state,before)
        self.assertTrue(0<=result<=1)
        self.assertEqual(len(pulse),4)

    def test_checkpoint_and_delayed_pulse_resume(self):
        brain=C1ContinuousBrain(5,tie_mode="random_tie")
        full,pulse_full=train(brain,brain.initial(),ZERO,"D0",60)
        mid,pending=train(brain,brain.initial(),ZERO,"D0",25)
        restored=brain.restore(brain.checkpoint(mid))
        resumed,pulse_resumed=train(brain,restored,pending,"D0",35)
        self.assertEqual(resumed,full)
        self.assertEqual(pulse_resumed,pulse_full)
        with self.assertRaises(ValueError):
            C1ContinuousBrain(6,tie_mode="random_tie").restore(
                brain.checkpoint(full)
            )

    def test_frozen_control_leaves_dendrites_exactly_fixed(self):
        brain=C1ContinuousBrain(0,tie_mode="first_index")
        control,_=train(brain,brain.initial(),ZERO,"D0",60,learn=False)
        self.assertEqual(control.dendrites,brain.initial().dendrites)
        self.assertEqual(control.tick,60)
        self.assertEqual(control.concept_output,253)

    def test_no_internal_target_and_reject_invalid_inputs(self):
        brain=C1ContinuousBrain(0,tie_mode="first_index")
        self.assertEqual(set(vars(brain)),{"seed","tie_mode"})
        self.assertFalse(hasattr(brain,"target"))
        self.assertFalse(hasattr(brain,"reward_map"))
        for bad in ((256,0,0,0),(0,0,0),(0,0,True,0)):
            with self.assertRaises(ValueError):
                brain.step(brain.initial(),bad)
        with self.assertRaises(ValueError):
            C1ContinuousBrain(-1,tie_mode="first_index")

    def test_seeded_pair_reproducibility(self):
        for seed in range(6):
            self.assertEqual(run_seed(seed,"random_tie"),run_seed(seed,"random_tie"))

    def test_preregistered_conditions_report_scientific_failure_as_data(self):
        data=run_all()
        self.assertEqual(set(data["conditions"]),{"first_index","random_tie"})
        self.assertEqual(data["seeds_per_condition"],20)
        for mode,entry in data["conditions"].items():
            with self.subTest(mode=mode):
                self.assertEqual(len(entry["per_seed"]),20)
                self.assertTrue(0<=entry["mean_train"]<=1)
                self.assertTrue(0<=entry["mean_reversal"]<=1)
                self.assertEqual(entry["passed"],
                    entry["good_train"]>=18
                    and entry["good_reversal"]>=18
                    and entry["advantage_vs_frozen"]>=.30
                )
                self.assertTrue(all(x["after_train"]["tick"]==60
                                    and x["after_reversal"]["tick"]==180
                                    for x in entry["per_seed"]))


if __name__=="__main__":
    unittest.main()
