"""E04: pruebas preregistradas de memoria STW/LTW experimental."""
import random
import unittest

from experiments.neurolab.twin_weight import TwinSynapse, simple_weight_step


class TwinWeightTests(unittest.TestCase):
    def test_manual_positive_oracle_t01(self):
        self.assertEqual(TwinSynapse(128, 128).step(+1), TwinSynapse(154, 129))

    def test_manual_negative_oracle_t02(self):
        self.assertEqual(TwinSynapse(128, 128).step(-1), TwinSynapse(102, 127))

    def test_long_reward_changes_both_t03(self):
        state = TwinSynapse()
        for _ in range(100):
            state = state.step(+1)
        self.assertGreater(state.ltw, 180)
        self.assertGreaterEqual(state.stw, state.ltw)

    def test_short_shock_recovers_from_long_term_t04(self):
        state = TwinSynapse()
        for _ in range(100):
            state = state.step(+1)
        before = state
        for _ in range(2):
            state = state.step(-1)
        shocked = state
        self.assertLessEqual(before.ltw - shocked.ltw, 2)
        for _ in range(20):
            state = state.step(0)
        self.assertGreater(state.stw, shocked.stw)
        self.assertLessEqual(abs(state.stw - state.ltw), 6)

    def test_long_opposite_changes_ltw_t05(self):
        state = TwinSynapse()
        for _ in range(100):
            state = state.step(+1)
        peak = state
        for _ in range(100):
            state = state.step(-1)
        self.assertGreaterEqual(peak.ltw - state.ltw, 40)
        self.assertLess(state.stw, peak.stw)

    def test_single_weight_does_not_recover_without_feedback_t06(self):
        twin = TwinSynapse()
        single = 128
        for _ in range(100):
            twin = twin.step(+1)
            single = simple_weight_step(single, +1)
        for _ in range(2):
            twin = twin.step(-1)
            single = simple_weight_step(single, -1)
        twin_shocked = twin.stw
        single_shocked = single
        for _ in range(20):
            twin = twin.step(0)
            single = simple_weight_step(single, 0)
        self.assertEqual(single, single_shocked)
        self.assertNotEqual(twin.stw, twin_shocked)

    def test_extremes_and_random_states_remain_bounded_t07(self):
        rng = random.Random(1234)
        for initial in (TwinSynapse(0, 0), TwinSynapse(255, 255),
                        TwinSynapse(0, 255), TwinSynapse(255, 0)):
            state = initial
            for _ in range(500):
                state = state.step(rng.choice([-1, 0, 1]))
                self.assertTrue(0 <= state.stw <= 255)
                self.assertTrue(0 <= state.ltw <= 255)
        for _ in range(20):
            state = TwinSynapse(rng.randint(0, 255), rng.randint(0, 255))
            for _ in range(100):
                state = state.step(rng.choice([-1, 0, 1]))
            self.assertTrue(0 <= state.stw <= 255)
            self.assertTrue(0 <= state.ltw <= 255)

    def test_checkpoint_preserves_two_weights_t08(self):
        first = TwinSynapse()
        commands = [1] * 40 + [-1] * 4 + [0] * 30
        for reward in commands[:30]:
            first = first.step(reward)
        reloaded = TwinSynapse.from_json(first.to_json())
        self.assertEqual(reloaded, first)
        for reward in commands[30:]:
            first = first.step(reward)
            reloaded = reloaded.step(reward)
        self.assertEqual(reloaded, first)
        with self.assertRaises(ValueError):
            TwinSynapse.from_json('{"model":"unknown","stw":4,"ltw":4}')

    def test_input_validation(self):
        for x in (True, 1.0, 2, -2):
            with self.assertRaises(ValueError):
                TwinSynapse().step(x)
        for bad in (-1, 256, True):
            with self.assertRaises(ValueError):
                TwinSynapse(bad, 128)
        self.assertEqual(simple_weight_step(128, 0), 128)

    def test_no_target_actions_or_concepts_t09(self):
        state = TwinSynapse()
        self.assertEqual(set(vars(state)), {"stw", "ltw"})
        self.assertFalse(hasattr(state, "target_action"))


if __name__ == "__main__":
    unittest.main()
