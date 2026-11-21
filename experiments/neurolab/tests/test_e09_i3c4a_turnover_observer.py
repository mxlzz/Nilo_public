"""I3c4a: read-only original-result hash verification and turnover accounting."""
import unittest

from experiments.neurolab.e09_i3c4a_turnover_observer import (
    PHASES, MODES, golden_hashes, observe_seed, run_all
)


class YokedTurnoverWitnessTests(unittest.TestCase):
    def test_all_frozen_original_seed_hashes_have_correct_provenance(self):
        hashes=golden_hashes()
        self.assertEqual(len(hashes),20)
        self.assertEqual(set(hashes),{str(i) for i in range(900,920)})
        self.assertTrue(all(len(v)==64 for v in hashes.values()))

    def test_one_seed_exactly_reproduces_original_experiment(self):
        row=observe_seed(900,golden_hashes())
        self.assertTrue(row["observed_original_exactly"])
        self.assertEqual(row["seed"],900)
        self.assertEqual(set(row["modes"]),set(MODES))
        for mode in MODES:
            for phase in PHASES:
                stats=row["modes"][mode][phase]
                self.assertGreaterEqual(
                    stats["accepted_contact_events"],
                    stats["migration_active_ticks"],
                )
                self.assertEqual(stats["accepted_contact_events"],
                                 stats["reasons"].get("accepted",0))
                self.assertEqual(
                    stats["accepted_contact_events"],
                    len(stats["events"]),
                )
                if mode in ("B","F"):
                    self.assertEqual(stats["accepted_contact_events"],0)

    def test_falsified_original_hash_must_abort(self):
        data=golden_hashes()
        data["900"]="0"*64
        with self.assertRaisesRegex(AssertionError,"immutable original CI"):
            observe_seed(900,data)

    def test_aggregates_are_observational_not_confirmatory(self):
        doc=run_all((900,))
        self.assertEqual(doc["n_seeds"],1)
        self.assertTrue(doc["original_hashes_verified"])
        self.assertTrue(doc["all_original_outputs_identical"])
        self.assertEqual(doc["G05_G09"],"OPEN")
        for mode in MODES:
            for phase in PHASES:
                stats=doc["totals"][mode][phase]
                self.assertGreaterEqual(
                    stats["accepted_contact_events"],
                    stats["migration_active_ticks"],
                )
        with self.assertRaises(ValueError):
            run_all((900,900))
        with self.assertRaises(ValueError):
            run_all((800,))


if __name__=="__main__":
    unittest.main()
