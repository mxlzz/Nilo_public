"""E09g7: audit ledger invariants, counts, and g5 training parity."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_context_protocol import (
    ZERO, MAPPING_A, blocks, train_brain,
)
from experiments.neurolab.e09_causal_ledger import (
    source_of, ledger_train, run_seed, summarize, run_all,
)


class CausalLedgerTests(unittest.TestCase):
    def test_unambiguous_decision_source_only(self):
        self.assertIsNone(source_of((0, 0)))
        self.assertIsNone(source_of((126, 126)))
        self.assertEqual(source_of((126, 0)), 0)
        self.assertEqual(source_of((0, 126)), 1)

    def test_instrumented_training_matches_uninstrumented_exactly(self):
        brain = C1ContextBrain(4)
        schedule = blocks(4, 10000, 32)
        initial = brain.initial()
        state, pulse, previous, events = ledger_train(
            brain, initial, ZERO, None, schedule, MAPPING_A, "first"
        )
        original_state, original_pulse = train_brain(
            brain, initial, ZERO, schedule, MAPPING_A, learn=True
        )
        self.assertEqual((state, pulse), (original_state, original_pulse))
        self.assertEqual(len(events), 256)
        self.assertEqual({x["phase"] for x in events}, {"first"})
        self.assertEqual(events[0]["position"], 0)
        self.assertIsNone(events[0]["source_mismatch"])
        self.assertIsNotNone(previous)
        self.assertEqual(sum(x["position"] == 1 for x in events), 32)

    def test_mismatch_only_when_both_sources_known_and_pulse_nonzero(self):
        data = run_seed(16)
        for event in data["first"] + data["reversed"]:
            if event["source_mismatch"] is not None:
                self.assertTrue(event["comparable"])
                self.assertIn(event["pulse"], ("reward", "punishment"))
                self.assertIn(event["plasticity_source"], (0,1))
                self.assertIn(event["previous_action_decision_source"], (0,1))
                self.assertEqual(event["source_mismatch"],
                                 event["plasticity_source"] !=
                                 event["previous_action_decision_source"])
        self.assertEqual(len(data["first"]), 256)
        self.assertEqual(len(data["reversed"]), 256)

    def test_full_report_has_exact_event_count_and_accounting(self):
        data = run_all()
        totals = data["total"]
        self.assertEqual(data["n_seeds"], 20)
        self.assertEqual(totals["ticks"], 20 * 2 * 32 * 8)
        self.assertEqual(totals["pulses"],
                         totals["comparable"] + totals["unknown_source_pulses"])
        self.assertLessEqual(totals["discordant_with_stw_change"],
                             totals["discordant"])
        self.assertLessEqual(totals["discordant_with_ltw_change"],
                             totals["discordant"])
        self.assertTrue(any(x["discordant"] > 0
                            for x in data["by_phase_boundary_position"].values()))
        self.assertEqual(len(data["per_seed"]), 20)


if __name__ == "__main__":
    unittest.main()
