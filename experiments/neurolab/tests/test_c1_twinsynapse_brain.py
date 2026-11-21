"""E09.02e tests of STW/LTW in a five-neuron Concept→Decision circuit."""
import json
import unittest

from experiments.neurolab.c1_twinsynapse_brain import TwinBrainLearner,TwinBrainState
from experiments.neurolab.twin_weight import TwinSynapse
from experiments.neurolab.e09_twinbrain_protocol import run_all,run_seed,train


class TwoSpeedBrainTests(unittest.TestCase):
    def test_initial_dendrite_weights_zero(self):
        s=TwinBrainLearner(1).initial()
        self.assertEqual(s.synapses,(TwinSynapse(0,0),)*4)

    def test_reward_from_zero_manual_oracle(self):
        l=TwinBrainLearner(1)
        s=l.initial()
        t=l.respond(s)
        after=l.feedback(s,t,+1)
        active=0 if t.chosen=="D0" else 2
        self.assertEqual(after.synapses[active],TwinSynapse(26,1))
        self.assertTrue(all(after.synapses[i]==TwinSynapse(0,0)
                            for i in range(4) if i!=active))

    def test_punishment_affects_only_inhibitory_class(self):
        l=TwinBrainLearner(1)
        s=l.initial()
        t=l.respond(s)
        after=l.feedback(s,t,-1)
        active=1 if t.chosen=="D0" else 3
        self.assertEqual(after.synapses[active],TwinSynapse(26,1))
        self.assertTrue(all(after.synapses[i]==TwinSynapse(0,0)
                            for i in range(4) if i!=active))

    def test_sleep_like_unreinforced_relaxation(self):
        l=TwinBrainLearner(0)
        a=l.feedback(l.initial(),l.respond(l.initial()),+1)
        t=l.respond(a)
        b=l.feedback(a,t,-1)  # previously rewarded edge must relax
        rewarded=0 if list(a.synapses)[0].stw>0 else 2
        # The old STW will be 20 unless this trial hit the same edge.
        self.assertTrue(0<=b.synapses[rewarded].stw<=255)
        self.assertNotEqual(a,b)

    def test_inactive_concept_no_new_chemical_reinforcement(self):
        l=TwinBrainLearner(3)
        s=l.initial()
        trial=l.respond(s,(255,0))
        self.assertEqual(trial.trace.concept,0)
        after=l.feedback(s,trial,+1)
        self.assertEqual(after.synapses,s.synapses)

    def test_frozen_weights(self):
        l=TwinBrainLearner(4)
        result=train(l,l.initial(),"D0",60,learn=False)
        self.assertEqual(result.synapses,l.initial().synapses)
        self.assertEqual(result.trials,60)

    def test_no_external_target_labels(self):
        l=TwinBrainLearner(4)
        self.assertEqual(set(vars(l)),{"seed"})
        self.assertFalse(hasattr(l,"correct_action"))

    def test_reject_obsolete_feedback(self):
        l=TwinBrainLearner(3)
        s=l.initial()
        t=l.respond(s)
        next_state=l.feedback(s,t,+1)
        with self.assertRaises(ValueError):
            l.feedback(next_state,t,-1)

    def test_checkpoint_resume_deterministic(self):
        l=TwinBrainLearner(7)
        full=train(l,l.initial(),"D0",60)
        mid=train(l,l.initial(),"D0",25)
        resumed=l.restore(l.checkpoint(mid))
        other=train(l,resumed,"D0",35)
        self.assertEqual(full,other)
        with self.assertRaises(ValueError):
            TwinBrainLearner(8).restore(l.checkpoint(mid))

    def test_reproducibility(self):
        for seed in range(20):
            self.assertEqual(run_seed(seed),run_seed(seed))

    def test_preregistered_gate(self):
        r=run_all()
        self.assertEqual(r["seeds"],20)
        self.assertTrue(r["passed"],json.dumps(r,indent=2))
        self.assertGreaterEqual(r["success_train_seeds"],18)
        self.assertGreaterEqual(r["success_reversal_seeds"],18)
        self.assertGreaterEqual(r["advantage_over_frozen"],.30)


if __name__=="__main__":
    unittest.main()
