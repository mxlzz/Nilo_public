"""E09.02g.4: preregistered robustness tests for 5-node continuous C1 brain.

All six experiments use the same brain architecture, rates and
20 seeds. Negative scientific results are recorded, not test failures.
"""
import random
import unittest

from experiments.neurolab.c1_continuous_brain import C1ContinuousBrain
from experiments.neurolab.e09_continuous_protocol import run_seed as g3_run_seed
from experiments.neurolab.e09_robustness_protocol import (
    ZERO,REWARD,PUNISHMENT,ORDERS,STRESSORS,
    pulse_from_action,train_with_queue,run_seed,run_all,
)


class RobustnessTests(unittest.TestCase):
    def test_clean_one_tick_pulses_match_previous_g3_protocol(self):
        # Exact parity is a non-negotiable regression oracle.
        for seed in (0,1,5,11):
            baseline=g3_run_seed(seed,"random_tie")
            now=run_seed(seed,"D0","D1",noise=0.0,delay=1)
            self.assertEqual(now["train"],baseline["train"])
            self.assertEqual(now["frozen"],baseline["frozen"])
            self.assertEqual(now["reversal"],baseline["reversal"])
            self.assertEqual(now["after_first"],baseline["after_train"])
            self.assertEqual(now["after_reversal"],baseline["after_reversal"])

    def test_counterbalanced_orders_are_not_silently_swapped(self):
        a=run_seed(2,"D0","D1",noise=0.0,delay=1)
        b=run_seed(2,"D1","D0",noise=0.0,delay=1)
        self.assertEqual(a["order"],"D0->D1")
        self.assertEqual(b["order"],"D1->D0")
        self.assertEqual(a["after_first"]["tick"],60)
        self.assertEqual(b["after_reversal"]["tick"],180)

    def test_delay_three_starts_with_three_empty_pulses(self):
        brain=C1ContinuousBrain(3,tie_mode="random_tie")
        state=brain.initial()
        first=brain.step(state,ZERO,learn=True)
        self.assertIsNotNone(first.action)
        expected=REWARD if first.action=="D0" else PUNISHMENT
        one,queue,_=train_with_queue(
            brain,state,(ZERO,ZERO,ZERO),"D0",1,
            noise=0.0,seed=3,learn=True,
        )
        self.assertEqual(one,first.after)
        self.assertEqual(queue,(ZERO,ZERO,expected))
        second,pending,_=train_with_queue(
            brain,one,queue,"D0",2,
            noise=0.0,seed=3,learn=True,
        )
        self.assertEqual(second.tick,3)
        # All three initial ticks had zero-arrival chemistry;
        # tick four will receive the first emission.
        self.assertEqual(pending[0],expected)
        self.assertTrue(all(d.dendrite.stw==0 for d in second.dendrites))

    def test_pending_pulses_are_carried_across_reversal_boundary(self):
        brain=C1ContinuousBrain(1,tie_mode="random_tie")
        one,queue,_=train_with_queue(
            brain,brain.initial(),(ZERO,)*3,"D0",60,
            noise=0.0,seed=1,learn=True,
        )
        self.assertEqual(len(queue),3)
        self.assertTrue(any(p!=ZERO for p in queue))
        next_state,next_queue,_=train_with_queue(
            brain,one,queue,"D1",1,
            noise=0.0,seed=1,learn=True,
        )
        self.assertEqual(next_state.tick,61)
        self.assertEqual(next_queue[:2],queue[1:])
        self.assertEqual(len(next_queue),3)

    def test_noise_flips_pulse_not_brain_action(self):
        cases=[pulse_from_action("D0","D0",noise=0.10,seed=0,tick=t)
               for t in range(1,501)]
        self.assertTrue(any(flip for _,flip in cases))
        self.assertTrue(any(not flip for _,flip in cases))
        self.assertTrue(all((pulse==PUNISHMENT if flip else pulse==REWARD)
                            for pulse,flip in cases))
        self.assertEqual(pulse_from_action("D0","D1",noise=0.0,seed=1,tick=1),
                         (PUNISHMENT,False))
        self.assertEqual(pulse_from_action(None,"D0",noise=0.10,seed=1,tick=1),
                         (ZERO,False))

    def test_noise_schedule_is_deterministic_by_tick(self):
        for seed in (0,4,12):
            for tick in (1,7,42,61,180):
                a=pulse_from_action("D0","D0",noise=0.10,seed=seed,tick=tick)
                b=pulse_from_action("D0","D0",noise=0.10,seed=seed,tick=tick)
                self.assertEqual(a,b)

    def test_frozen_baseline_cannot_change_dendrites_even_with_noise(self):
        brain=C1ContinuousBrain(3,tie_mode="random_tie")
        start=brain.initial()
        final,queue,flips=train_with_queue(
            brain,start,(ZERO,)*3,"D1",60,
            noise=0.10,seed=3,learn=False,
        )
        self.assertEqual(start.dendrites,final.dendrites)
        self.assertEqual(final.tick,60)
        self.assertTrue(0<=flips<=60)
        self.assertEqual(len(queue),3)

    def test_holdout_is_non_mutating_and_separate_from_training(self):
        old=run_seed(5,"D1","D0",noise=0.10,delay=3)
        self.assertEqual(old,run_seed(5,"D1","D0",noise=0.10,delay=3))
        self.assertEqual(old["after_first"]["tick"],60)
        self.assertEqual(old["after_reversal"]["tick"],180)
        self.assertEqual(len(old["pending_at_reversal"]),3)

    def test_illegal_conditions_are_not_allowed(self):
        with self.assertRaises(ValueError):
            run_seed(1,"D0","D0",noise=0.0,delay=1)
        with self.assertRaises(ValueError):
            run_seed(1,"D0","D1",noise=0.0,delay=2)
        with self.assertRaises(ValueError):
            pulse_from_action("D0","D1",noise=.15,seed=1,tick=1)
        with self.assertRaises(ValueError):
            pulse_from_action("D0","D1",noise=0.0,seed=1,tick=0)
        with self.assertRaises(ValueError):
            train_with_queue(C1ContinuousBrain(1,tie_mode="random_tie"),
                             C1ContinuousBrain(1,tie_mode="random_tie").initial(),
                             (ZERO,ZERO),"D0",60,
                             noise=0.0,seed=1,learn=True)

    def test_six_conditions_and_same_seeds_reported(self):
        result=run_all()
        self.assertEqual(result["n_conditions"],6)
        self.assertEqual(result["seeds_per_condition"],20)
        expected={f"{a}_to_{b}/{name}" for a,b in ORDERS for name,_,_ in STRESSORS}
        self.assertEqual(set(result["conditions"]),expected)
        for key,condition in result["conditions"].items():
            with self.subTest(condition=key):
                rows=condition["per_seed"]
                self.assertEqual(len(rows),20)
                self.assertEqual([r["seed"] for r in rows],list(range(20)))
                both=sum(r["train"]>=.90 and r["reversal"]>=.90 for r in rows)
                self.assertEqual(condition["good_both"],both)
                self.assertEqual(condition["passed"],both>=18
                                 and condition["advantage_vs_frozen"]>=.30)
                self.assertTrue(0<=condition["mean_train"]<=1)
                self.assertTrue(0<=condition["mean_reversal"]<=1)


if __name__=="__main__":
    unittest.main()
