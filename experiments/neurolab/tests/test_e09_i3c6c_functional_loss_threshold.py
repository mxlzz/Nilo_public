"""Original C1 feedback functional gate: change CHEM vs suppress loss."""
import unittest

from experiments.neurolab.e09_i3c6c_functional_loss_threshold import evaluate


class OriginalLossInhibitionThresholdTests(unittest.TestCase):
    def test_both_historical_gene_pairs_identical_functional_threshold(self):
        result=evaluate()
        self.assertEqual(set(result["pairs"]),{"124","125"})
        self.assertEqual(result["receptor_change_locus_threshold"],3)
        self.assertEqual(result["functional_antiatrophy_locus_threshold"],18)
        for pair in result["pairs"].values():
            self.assertEqual(len(pair["curve"]),33)
            self.assertEqual(pair["first_strength_loss_inhibition"],18)

    def test_chemical_change_at_three_does_not_prevent_atrophy(self):
        for pair in evaluate()["pairs"].values():
            rows=pair["curve"]
            for x in (0,1,2,3,4,17):
                self.assertEqual(rows[x]["strength_after_tick5"],3)
                self.assertFalse(rows[x]["loss_inhibited"])
            self.assertEqual(rows[3]["decision_chem_value"],15)
            self.assertEqual(rows[17]["decision_chem_value"],1)

    def test_zero_chem_eighteen_stops_loss_but_not_guarantee_learning(self):
        result=evaluate()
        for pair in result["pairs"].values():
            self.assertEqual(pair["curve"][18]["decision_chem_value"],0)
            self.assertEqual(pair["curve"][18]["strength_after_tick5"],4)
            self.assertTrue(pair["curve"][18]["loss_inhibited"])
            self.assertEqual(pair["curve"][32]["strength_after_tick5"],4)
        self.assertEqual(result["G05_G09_G00H"],"OPEN")

    def test_reduced_class_capacity_below_eighteen_and_replay(self):
        a=evaluate()
        self.assertEqual(a,evaluate())
        self.assertEqual(
            a["reduced_class_capacities"]["fixed_eight_synapses"]["max_class_loose"],2
        )
        self.assertEqual(
            a["reduced_class_capacities"]["dynamic_four_synapses"]["max_class_loose"],1
        )
        self.assertEqual(a["historical_decision_class_capacity"],128)


if __name__=="__main__":
    unittest.main()
