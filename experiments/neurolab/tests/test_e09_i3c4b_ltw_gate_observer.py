"""I3c4b: original-hash invariants and per-synapse LTW gate witness."""
import unittest
from experiments.neurolab.e09_i3c4b_ltw_gate_observer import (
    PERIOD,observe_seed,run_all,
)
from experiments.neurolab.e09_i3c4a_turnover_observer import golden_hashes


class GateLTWWitnessTests(unittest.TestCase):
    def test_128_period_does_not_change(self):
        self.assertEqual(PERIOD,128)

    def test_observational_replay_one_seed(self):
        result=observe_seed(900,golden_hashes())
        self.assertTrue(result["sha_verified"])
        self.assertEqual(result["seed"],900)
        for mode in ("B","Y","P","F"):
            for phase in ("first","reversed"):
                row=result["modes"][mode][phase]
                self.assertEqual(
                    row["synapse_samples"],4*row["gate_ticks"])
                for gate in row["per_gate"]:
                    self.assertEqual(gate["tick"]%128,0)
                    self.assertEqual(len(gate["rows"]),4)
                    for syn in gate["rows"]:
                        self.assertGreaterEqual(syn["erased_by_strength"],0)
                        if syn["final_LTW"]!=syn["post_strength_LTW"]:
                            self.assertTrue(syn["migrated"])
        for phase in ("first","reversed"):
            self.assertEqual(result["modes"]["F"][phase]["gate_ticks"],0)

    def test_falsified_original_digest_aborts(self):
        changed=golden_hashes()
        changed["900"]="f"*64
        with self.assertRaisesRegex(AssertionError,"frozen original"):
            observe_seed(900,changed)

    def test_total_is_read_only_not_learning_gate(self):
        doc=run_all((900,))
        self.assertTrue(doc["all_original_per_seed_sha_verified"])
        self.assertEqual(doc["G05_G09"],"OPEN")
        self.assertEqual(doc["gate_period"],128)
        self.assertEqual(doc["seeds"],[900])
        with self.assertRaises(ValueError):
            run_all((900,900))
        with self.assertRaises(ValueError):
            run_all((200,))


if __name__=="__main__":
    unittest.main()
