"""NR01.03-C toy-only 1-NN-16 contract tests; zero scientific seeds."""
import unittest

from experiments.neurolab.nr01_knn import CaseMemory16


def x(value):
    return (float(value),) * 16


class TestNR01CaseMemory(unittest.TestCase):
    def test_initial_action_and_reward_only_after_choice(self):
        memory = CaseMemory16()
        self.assertEqual(memory.choose(x(0)), "D0")
        initial = memory.snapshot()
        self.assertEqual(memory.choose(x(1)), "D0")
        self.assertEqual(memory.snapshot(), initial)
        memory.apply_reward(x(0), "D0", -1)
        self.assertEqual(memory.choose(x(0)), "D1")
        self.assertEqual(len(memory.cases), 1)

    def test_equal_distance_tie_favors_oldest_case(self):
        memory = CaseMemory16()
        memory.apply_reward(x(0), "D0", -1)  # oldest is D1
        memory.apply_reward(x(1), "D1", -1)  # latest is D0
        self.assertEqual(memory.choose(x(0.5)), "D1")

    def test_fifo_capacity_and_no_test_mutation(self):
        memory = CaseMemory16()
        for i in range(17):
            observed = x(i / 16)
            memory.apply_reward(observed, memory.choose(observed), 1)
        self.assertEqual(len(memory.cases), 16)
        self.assertEqual(memory.cases[0][0], x(1/16))
        unchanged = memory.snapshot()
        for q in (x(0), x(0.3), x(1)):
            memory.choose(q)
        self.assertEqual(memory.snapshot(), unchanged)

    def test_snapshot_restore_deterministic(self):
        original = CaseMemory16()
        for i in range(6):
            obs = x(i / 10)
            original.apply_reward(obs, original.choose(obs), (-1, 1)[i % 2])
        duplicate = CaseMemory16.restore(original.snapshot())
        self.assertEqual(original.snapshot(), duplicate.snapshot())
        for i in range(6, 10):
            obs = x(i / 10)
            for memory in (original, duplicate):
                memory.apply_reward(obs, memory.choose(obs), (-1, 1)[i % 2])
        self.assertEqual(original.snapshot(), duplicate.snapshot())

    def test_reject_invalid_values_and_snapshot_without_mutating(self):
        memory = CaseMemory16()
        old = memory.snapshot()
        for obs, action, reward in [
            ((1.0,), "D0", 1),
            (x(float("nan")), "D0", 1),
            (x(0), "D1", 1),
            (x(0), "D0", 0),
        ]:
            with self.assertRaises(ValueError):
                memory.apply_reward(obs, action, reward)
            self.assertEqual(memory.snapshot(), old)
        for state in (b"{}", b"[]", b'{"schema":"other"}', b"not-json"):
            with self.assertRaises((ValueError, TypeError)):
                CaseMemory16.restore(state)


if __name__ == "__main__":
    unittest.main()
