"""E07 tests, including constrained rewiring and simple LRU baseline."""
import json
import unittest

from experiments.neurolab.rewiring import (
    PAIRS, Slot, WiringChoice, WiringModel, WiringState,
)
from experiments.neurolab.e07_protocol import (
    NEW, OLD, accuracy, run_all, run_seed, training_order, train,
)


class WiringTests(unittest.TestCase):
    def test_budget_and_initial_patterns(self):
        for mode in ("fixed", "migratory", "lru"):
            state = WiringModel(2, mode).initial()
            self.assertEqual(len(state.slots), 2)
            self.assertEqual(tuple(s.pattern for s in state.slots), ((0,2),(1,3)))

    def test_migration_after_strength_zero(self):
        model = WiringModel(2, "migratory")
        state = model.initial()
        for _ in range(3):
            state, choice = model.choose(state, (0,3))
            state = model.update(state, choice, (0,3), -1)
        self.assertEqual(sum(s.pattern == (0,3) for s in state.slots), 1)
        self.assertEqual(len({s.pattern for s in state.slots if s.pattern is not None}),
                         sum(s.pattern is not None for s in state.slots))
        self.assertEqual(len(state.slots), 2)

    def test_fixed_does_not_rewire(self):
        model = WiringModel(2, "fixed")
        state = train(model, model.initial(), training_order(2, NEW, 30))
        self.assertEqual(tuple(s.pattern for s in state.slots), ((0,2),(1,3)))

    def test_lru_replaces_for_new_pair_immediately(self):
        model = WiringModel(3, "lru")
        after, choice = model.choose(model.initial(), (0,3), structural=True)
        self.assertEqual(choice.slot_index, 0)
        self.assertEqual(after.slots[0].pattern, (0,3))
        self.assertEqual(len(after.slots), 2)

    def test_training_changes_only_used_weights(self):
        model = WiringModel(5, "fixed")
        state = model.initial()
        prepared, choice = model.choose(state, (0,2))
        after = model.update(prepared, choice, (0,2), -1)
        self.assertEqual(after.slots[1].weights, state.slots[1].weights)
        self.assertEqual(after.time, state.time + 1)

    def test_holdout_does_not_modify_memory(self):
        model = WiringModel(9, "migratory")
        state = train(model, model.initial(), training_order(9, NEW, 30))
        old = state
        accuracy(model, state, training_order(9, OLD, 40))
        self.assertEqual(state, old)

    def test_reproducibility(self):
        self.assertEqual(run_seed(4), run_seed(4))
        self.assertEqual(training_order(4, OLD, 30), training_order(4, OLD, 30))

    def test_invalid_states(self):
        with self.assertRaises(ValueError):
            Slot((0,0), 3, (120,130))
        with self.assertRaises(ValueError):
            Slot((0,2), 4, (120,130))
        with self.assertRaises(ValueError):
            WiringState((Slot((0,2),3,(120,130)), Slot((0,2),3,(120,130))))
        with self.assertRaises(ValueError):
            WiringModel(1, "unknown")
        with self.assertRaises(ValueError):
            WiringModel(1, "fixed").choose(WiringModel(1,"fixed").initial(), (0,1))

    def test_missing_concept_has_no_direct_weight_update(self):
        model = WiringModel(3, "fixed")
        initial = model.initial()
        before, choice = model.choose(initial, (0,3))
        self.assertIsNone(choice.slot_index)
        next_state = model.update(before, choice, (0,3), -1)
        self.assertEqual(tuple(s.weights for s in initial.slots),
                         tuple(s.weights for s in next_state.slots))

    def test_preregistered_capacity_gate(self):
        result = run_all()
        self.assertEqual(result["n_seeds"], 20)
        self.assertTrue(result["passed"], json.dumps(result, indent=2))
        self.assertGreaterEqual(result["new_90_percent_seeds"], 18)
        self.assertGreaterEqual(result["migration_vs_fixed_new"], .30)


if __name__ == "__main__":
    unittest.main()
