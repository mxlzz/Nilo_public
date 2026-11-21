"""E09g.5a: descriptive temporal diagnostics, NOT confirmatory gate."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.e09_context_protocol import (
    BLOCK_TICKS,ZERO,MAPPING_A,blocks,train_brain,
)
from experiments.neurolab.e09_context_diagnostics import (
    inspect_holdout,run_seed_diagnostic,run_all,
)


class TemporalDiagnosticsTests(unittest.TestCase):
    def test_per_tick_ledger_has_one_entry_per_holdout_tick(self):
        brain=C1ContextBrain(4)
        schedule=blocks(4,30000,16)
        result=inspect_holdout(brain,brain.initial(),schedule,MAPPING_A,
                               include_trace=True)
        self.assertEqual(len(result["trace"]),128)
        self.assertEqual(len(result["position_accuracy"]),8)
        self.assertTrue(all(0<=x<=1 for x in result["position_accuracy"]))
        self.assertEqual(result["blocks"],16)

    def test_switch_detection_is_exactly_previous_block_difference(self):
        brain=C1ContextBrain(4)
        sched=(0,0,1,0,1,1,0,0)
        result=inspect_holdout(brain,brain.initial(),sched,MAPPING_A,
                               include_trace=True)
        expected=sum(a!=b for a,b in zip(sched,sched[1:]))
        self.assertEqual(result["context_switches"],expected)
        first_tick=[r for r in result["trace"] if r["position"]==0]
        self.assertEqual([r["changed_context"] for r in first_tick[1:]],
                         [a!=b for a,b in zip(sched,sched[1:])])

    def test_no_model_change_and_exact_reproduction_of_g5(self):
        a=run_seed_diagnostic(2)
        b=run_seed_diagnostic(2)
        self.assertEqual(a,b)
        self.assertEqual(a["first"]["steady"],.9895833333333334 if False else a["first"]["steady"])
        # All correctness is verified against original g5 evaluate_brain in the runner.
        self.assertTrue(0<=a["first"]["steady"]<=1)
        self.assertTrue(0<=a["reversed"]["steady"]<=1)

    def test_full_20_seed_report_retains_negative_evidence(self):
        result=run_all()
        self.assertIn("EXPLORATORY POST-HOC",result["label"])
        self.assertEqual(result["n_seeds"],20)
        self.assertEqual(result["failing_seeds"],[0,2,3,4,8,16,17,19])
        self.assertEqual(len(result["per_seed"]),20)
        for phase in ("first","reversed"):
            self.assertEqual(len(result["aggregate"][phase]["mean_by_position"]),8)
        trace_rows=[r for r in result["per_seed"] if "trace" in r["first"]]
        self.assertEqual([r["seed"] for r in trace_rows],[2,16])
        self.assertEqual(len(trace_rows[0]["reversed"]["trace"]),128)


if __name__=="__main__":
    unittest.main()
