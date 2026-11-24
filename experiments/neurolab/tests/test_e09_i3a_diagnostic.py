"""I3a post-hoc observational replay must not change I3 original trajectories."""
import unittest

from experiments.neurolab.e09_i3a_diagnostic import (
    FIELDS,new_counters,run_seed,run_all,
)


class MetabolicMechanisticDiagnosticTests(unittest.TestCase):
    def test_one_seed_matches_reference_full_state_each_phase(self):
        doc=run_seed(200)
        self.assertEqual(doc["seed"],200)
        for phase in ("first","reversed"):
            counts=doc[phase]
            self.assertEqual(counts["delivered_precursors"]
                             +counts["missing_target_choices"],60)
            self.assertGreater(counts["synapse_samples"],0)
            self.assertEqual(counts["synapse_samples"],sum(
                counts["by_class"][mode]["samples"]
                for mode in ("excitatory","inhibitory")))
            self.assertLessEqual(counts["effect_positive"],counts["chem_positive"])
            self.assertLessEqual(counts["chem_and_suscept_positive"],counts["chem_positive"])
            self.assertLessEqual(counts["max_effect"],255)

    def test_no_parameter_changes_and_retrospective_marker(self):
        doc=run_all((200,))
        self.assertEqual(doc["seeds"],[200])
        self.assertEqual(doc["rates_lab"],40)
        self.assertEqual(doc["precursor_dose"],80)
        self.assertEqual(doc["scientific_gate"],"not evaluated; I3 remains negative")
        self.assertEqual(doc["replay_equivalence"],
                         "all 8 synapses each tick and final phase state")
        self.assertEqual(
            doc["totals"]["first"]["synapse_samples"],
            doc["per_seed"][0]["first"]["synapse_samples"],
        )

    def test_counters_explicit(self):
        values=new_counters()
        for key in FIELDS:
            self.assertEqual(values[key],0)
        self.assertEqual(values["by_class"]["excitatory"]["effect_positive"],0)


if __name__=="__main__":
    unittest.main()
