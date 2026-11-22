"""Original C1 gene-pair math, isolated zero-pool, not game-level learning."""
import unittest

from experiments.neurolab.e09_i3c6b_feedback_threshold import (
    EMITTER_GENES, RECEPTOR_IDS, LOCUS_VALUES,
    authentic_receptors, capacities, audit,
)


class EndogenousAtrophyFeedbackThresholdTests(unittest.TestCase):
    def test_original_receptors_and_emitters_are_paired(self):
        receptor=authentic_receptors()
        self.assertEqual(RECEPTOR_IDS,(127,128))
        self.assertEqual(tuple(e.chemical for e in EMITTER_GENES),(53,70))
        self.assertEqual(tuple(receptor[i].chemical for i in RECEPTOR_IDS),
                         (53,70))
        self.assertEqual(tuple(receptor[i].nominal for i in RECEPTOR_IDS),
                         (16,16))
        self.assertEqual(LOCUS_VALUES,tuple(range(17)))

    def test_both_historical_paths_have_identical_two_stage_threshold(self):
        result=audit()
        self.assertEqual(set(result["pairs"]),{"124","125"})
        for pair in result["pairs"].values():
            self.assertEqual(pair["threshold_first_receptor_drop"],3)
            self.assertEqual(len(pair["samples"]),17)
            self.assertEqual([
                (x["source_locus"],x["emitter_pool_amount"],x["receptor_value"])
                for x in pair["samples"][:5]],
                [(0,0,16),(1,0,16),(2,1,16),(3,2,15),(4,3,14)]
            )
            self.assertTrue(all(x["source_after_emitter"]==0
                                for x in pair["samples"]))

    def test_microbrain_class_counts_use_existing_structures(self):
        sizes=capacities()
        self.assertEqual(
            list(sizes["fixed_eight_synapses"]["class_counts"].values()),
            [2,2,2,2],
        )
        self.assertEqual(
            list(sizes["dynamic_four_synapses"]["class_counts"].values()),
            [1,1,1,1],
        )
        self.assertLess(sizes["fixed_eight_synapses"]["max_class_loose"],3)
        self.assertLess(sizes["dynamic_four_synapses"]["max_class_loose"],3)

    def test_stated_scope_is_isolated_not_complete_C1(self):
        r=audit()
        self.assertTrue(r["gates"]["NUMERIC"].startswith("PASS"))
        self.assertEqual(r["gates"]["G05"],"OPEN")
        self.assertEqual(r["gates"]["G09"],"OPEN")
        self.assertIn("zero-pool",r["limitations"])
        self.assertEqual(r,audit())


if __name__=="__main__":
    unittest.main()
