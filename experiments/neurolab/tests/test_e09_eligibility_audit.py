"""E09g10c: susceptibility rule, pulse counterfactual, g10b replay."""
import unittest

from experiments.neurolab.c1_context_brain import C1ContextBrain
from experiments.neurolab.c1_synapse_integrated import DECISION_EXCITATORY_GENE
from experiments.neurolab.c1_svrule_runtime import C1SVTable, evaluate
from experiments.neurolab.e09_context_protocol import REWARD
from experiments.neurolab.e09_eligibility_audit import (
    _syn_index, _counterfactual_event, trace_seed, _aggregate,
)


class EligibilityAuditTests(unittest.TestCase):
    def test_genetic_rule_is_local_coactivity_not_action_id(self):
        self.assertEqual(DECISION_EXCITATORY_GENE.susceptibility_rule[:3],
                         bytes((10,22,16)))
        rule = DECISION_EXCITATORY_GENE.susceptibility_rule
        self.assertEqual(evaluate(rule, C1SVTable(output=100, input=126)), 126)
        self.assertEqual(evaluate(rule, C1SVTable(output=0, input=126)), 0)
        self.assertEqual(evaluate(rule, C1SVTable(output=100, input=0)), 0)

    def test_dendrite_indices_are_exactly_8(self):
        self.assertEqual(
            [_syn_index(owner, source, typ)
             for owner in (0,1) for source in (0,1) for typ in (0,1)],
            list(range(8)),
        )

    def test_pulse_counterfactual_does_not_modify_source_snapshot(self):
        brain = C1ContextBrain(120)
        before = brain.initial()
        after, event = _counterfactual_event(
            brain, before, target=0, delay=1,
            selected_action="D0", pulse=REWARD, seed=120, phase="first",
        )
        self.assertEqual(before, brain.initial())
        self.assertEqual(after.tick, 1)
        self.assertEqual(event["pulse"], "reward")
        self.assertIsInstance(event["sus_target"], int)
        self.assertIsInstance(event["delta_target"], int)
        self.assertEqual(event["target"], 0)

    def test_replay_g10b_training_one_seed_and_group_balance(self):
        row = trace_seed(120)
        self.assertEqual(len(row["events"]), 120)
        self.assertEqual(row["seed"], 120)
        for phase in ("first","reversed"):
            selected = [x for x in row["events"] if x["phase"] == phase]
            self.assertEqual(len(selected), 60)
            self.assertEqual(
                [sum(x["delay"] == d for x in selected) for d in (1,2,3)],
                [20,20,20],
            )
        result = _aggregate([row])
        for phase in ("first","reversed"):
            for delay in ("1","2","3"):
                self.assertEqual(
                    result[phase][delay]["pulses"] +
                    result[phase][delay]["missing_pulses"], 20,
                )

    def test_fixed_seed_replay_is_deterministic(self):
        self.assertEqual(trace_seed(121), trace_seed(121))


if __name__ == "__main__":
    unittest.main()
