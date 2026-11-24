"""I3b.3: prove genuine existing migration cannot rewire saturated C0/C1."""
import unittest

from experiments.neurolab.e09_i3b3_migration_feasibility import (
    verify_structural_feasibility,
)
from experiments.neurolab.c1_migration import (
    SourceNeuron,Dendrite,MigrationState,MigrationConfig,
    RandStream,decision_migrate,
)


class FeasibilityTests(unittest.TestCase):
    def test_registered_two_source_four_class_exhaustion(self):
        result=verify_structural_feasibility()
        self.assertEqual(result["n_brain_units"],6)
        self.assertEqual(result["n_synapses"],8)
        self.assertEqual(result["n_concept_sources_per_decision_class"],2)
        self.assertEqual(result["n_dendrites_per_decision_class"],2)
        self.assertFalse(result["can_migrate_under_current_two_source_topology"])
        self.assertEqual(len(result["rejection_cases"]),8)
        self.assertTrue(all(
            x["result"]=="duplicate_source" and not x["migrated"]
            for x in result["rejection_cases"]))

    def test_three_source_only_fixture_can_migrate(self):
        result=verify_structural_feasibility()
        self.assertEqual(len(result["positive_control_three_source_synthetic"]),4)
        self.assertTrue(all(
            x["migrated"] and x["result"]=="accepted"
            for x in result["positive_control_three_source_synthetic"]
        ))
        self.assertTrue(result["no_neurons_or_synapses_added_to_microbrain"])

    def test_inactive_recipient_is_distinct_from_duplicate_source(self):
        state=MigrationState((
            Dendrite(0x1000,0,0,0),
            Dendrite(0x2000,0,0,2),
        ))
        sources=(SourceNeuron(0x1000),SourceNeuron(0x2000))
        cfg=MigrationConfig(0,0,1,1)
        no_act=decision_migrate(
            state,sources,cfg,RandStream(()),recipient_output=0
        )
        active=decision_migrate(
            state,sources,cfg,RandStream((0,)),recipient_output=255
        )
        self.assertEqual(no_act.reason,"inactive_recipient")
        self.assertEqual(active.reason,"duplicate_source")
        self.assertEqual(no_act.random.cursor,0)
        self.assertEqual(active.random.cursor,1)

    def test_an_unoccupied_source_is_required_but_not_sufficient_on_its_own(self):
        state=MigrationState((
            Dendrite(0x1000,0,0,0),
            Dendrite(0x2000,0,0,2),
        ))
        cfg=MigrationConfig(0,0,1,1)
        sources=(SourceNeuron(0x1000),SourceNeuron(0x2000),
                 SourceNeuron(0x3000))
        # Even with an unoccupied source, one random draw can STILL pick
        # an occupied source; this control rejects an overstrong claim.
        fail=decision_migrate(
            state,sources,cfg,RandStream((0,)),recipient_output=255
        )
        ok=decision_migrate(
            state,sources,cfg,RandStream((2,0,0)),recipient_output=255
        )
        self.assertFalse(fail.migrated)
        self.assertEqual(fail.reason,"duplicate_source")
        self.assertTrue(ok.migrated)
        self.assertEqual(ok.state.dendrites[0].source_pointer,0x3000)


if __name__=="__main__":
    unittest.main()
