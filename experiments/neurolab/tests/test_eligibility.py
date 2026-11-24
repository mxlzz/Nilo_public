"""E05: pruebas preregistradas y caso negativo de atribución causal.

Los tests distinguen corrección del algoritmo diseñado de utilidad causal.
G05 NO se supera si el distractor correlacionado recibe crédito indebido.
"""
import random
import unittest

from experiments.neurolab.eligibility import EligibleSynapse


def delayed_reward(delay: int, *, initial_weight: int = 128):
    item = EligibleSynapse(weight=initial_weight).mark_used()
    for _ in range(delay):
        item = item.advance_tick()
    return item.apply_reward(+1)


class EligibilityTests(unittest.TestCase):
    def test_delay_monotone_t01(self):
        delays = (0, 1, 3, 5, 10)
        weights = [delayed_reward(k).weight for k in delays]
        self.assertEqual(weights[0], 160)
        self.assertTrue(all(a >= b for a, b in zip(weights, weights[1:])))
        self.assertGreater(weights[0], weights[-1])
        self.assertGreater(weights[-1], 128)

    def test_never_used_stays_stable_t02_t03(self):
        item = EligibleSynapse()
        for tick in range(30):
            item = item.advance_tick().apply_reward(1 if tick % 2 == 0 else -1)
        self.assertEqual(item.weight, 128)
        self.assertEqual(item.eligibility, 0)
        self.assertEqual(EligibleSynapse(0, 0).apply_reward(-1).weight, 0)

    def test_manual_three_quarters_t01(self):
        item = EligibleSynapse(128, 0).mark_used()
        self.assertEqual(item.eligibility, 255)
        item = item.advance_tick()
        self.assertEqual(item.eligibility, 191)
        self.assertEqual(item.apply_reward(+1).weight, 151)  # floor(32*191/255)=23
        item = item.advance_tick()
        self.assertEqual(item.eligibility, 143)

    def test_balanced_uncorrelated_distractor_t04(self):
        # Igual estado elegible y feedback +1/-1: sin saturación el cambio neto es 0.
        b = EligibleSynapse().mark_used().advance_tick()
        b = b.apply_reward(+1).apply_reward(-1)
        self.assertEqual(b.weight, 128)
        self.assertEqual(b.eligibility, 191)

    def test_correlated_distractor_receives_more_credit_t05(self):
        # Causalidad externa conocida: A produce un refuerzo que llega después.
        # B fue activado más recientemente, pero NO lo causó.
        a = EligibleSynapse().mark_used()
        a = a.advance_tick().advance_tick()
        b = EligibleSynapse().mark_used()
        a, b = a.advance_tick(), b.advance_tick()
        self.assertEqual(a.eligibility, 107)
        self.assertEqual(b.eligibility, 191)
        result_a = a.apply_reward(+1)
        result_b = b.apply_reward(+1)
        self.assertEqual(result_a.weight, 141)
        self.assertEqual(result_b.weight, 151)
        self.assertGreater(result_b.weight - 128, result_a.weight - 128)
        # Esta prueba confirma una LIMITACIÓN del método, no una solución causal.

    def test_saturation_and_reward_sign_t06(self):
        positive = EligibleSynapse(250, 255).apply_reward(+1)
        negative = EligibleSynapse(5, 255).apply_reward(-1)
        self.assertEqual(positive.weight, 255)
        self.assertEqual(negative.weight, 0)
        self.assertEqual(EligibleSynapse(128, 255).apply_reward(0).weight, 128)

    def test_random_states_never_overflow_t06(self):
        rng = random.Random(112358)
        for _ in range(20):
            item = EligibleSynapse(rng.randint(0, 255), rng.randint(0, 255))
            for _ in range(400):
                action = rng.randrange(3)
                if action == 0:
                    item = item.mark_used()
                elif action == 1:
                    item = item.advance_tick()
                else:
                    item = item.apply_reward(rng.choice((-1, 0, 1)))
                self.assertTrue(0 <= item.weight <= 255)
                self.assertTrue(0 <= item.eligibility <= 255)

    def test_checkpoint_roundtrip_and_continuation_t07(self):
        item = EligibleSynapse(80, 0).mark_used()
        for _ in range(3):
            item = item.advance_tick()
        recovered = EligibleSynapse.from_json(item.to_json())
        self.assertEqual(recovered, item)
        for reward in (-1, 1, 1, 0):
            recovered = recovered.advance_tick().apply_reward(reward)
            item = item.advance_tick().apply_reward(reward)
        self.assertEqual(recovered, item)

    def test_input_validation_t06(self):
        for arg in (True, 1.5, -2, 2):
            with self.subTest(reward=repr(arg)), self.assertRaises(ValueError):
                EligibleSynapse().apply_reward(arg)
        for arg in (-1, 256, True, 1.5):
            with self.subTest(weight=repr(arg)), self.assertRaises(ValueError):
                EligibleSynapse(weight=arg)
        for text in ('{"model":"unknown","weight":128,"eligibility":0}',
                     '{"model":"E05-eligibility-v1","weight":128}',
                     'null'):
            with self.subTest(data=text), self.assertRaises(ValueError):
                EligibleSynapse.from_json(text)

    def test_no_causal_metadata_or_label_leakage(self):
        item = EligibleSynapse()
        self.assertEqual(set(vars(item)), {"weight", "eligibility"})
        self.assertFalse(hasattr(item, "cause_id"))
        self.assertFalse(hasattr(item, "correct_action"))


if __name__ == "__main__":
    unittest.main()
