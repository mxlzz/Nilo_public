"""I3c3a preregistered stress: no reward or learning claims."""
import unittest

from experiments.neurolab.e09_i3c3a_migration_stress import (
    SEEDS,TICKS,TAPE_LENGTH,scripted_context,
    scripted_chemicals,explicit_wiring,tape_from_local_generator,
    run_seed,run_all,
)


class NaturalMigrationStressTests(unittest.TestCase):
    def test_fixed_schedule_and_balanced_initial_wiring(self):
        self.assertEqual(SEEDS,tuple(range(800,820)))
        self.assertEqual(TICKS,256)
        self.assertEqual(TAPE_LENGTH,4096)
        self.assertEqual(scripted_context(0),0)
        self.assertEqual(scripted_context(7),0)
        self.assertEqual(scripted_context(8),1)
        self.assertEqual(scripted_context(16),0)
        self.assertEqual(scripted_chemicals(0),(24,0,0,0))
        self.assertEqual(scripted_chemicals(8),(0,24,0,0))
        self.assertEqual(scripted_chemicals(16),(24,0,0,0))
        self.assertEqual(
            explicit_wiring(800),(0x1000,0x2000,0x2000,0x1000))
        self.assertEqual(
            explicit_wiring(801),(0x2000,0x1000,0x1000,0x2000))
        for method in (scripted_context,scripted_chemicals):
            with self.assertRaises(ValueError):
                method(256)

    def test_random_stream_is_declared_reproducible_and_bounded(self):
        a=tape_from_local_generator(800)
        self.assertEqual(len(a),4096)
        self.assertEqual(a,tape_from_local_generator(800))
        self.assertNotEqual(a,tape_from_local_generator(801))
        self.assertTrue(all(type(x) is int and 0<=x<=32767 for x in a))
        with self.assertRaises(ValueError):
            tape_from_local_generator(799)

    def test_one_seed_has_exact_replay_and_no_unwitnessed_change(self):
        record=run_seed(800)
        self.assertEqual(record["seed"],800)
        self.assertTrue(record["no_pre_migration_neural_divergence"])
        self.assertEqual(set(record["branches"]),{"B","B+"})
        for name in ("B","B+"):
            branch=record["branches"][name]
            self.assertEqual(len(branch["per_tick"]),256)
            self.assertTrue(branch["checkpoint_replay_full_transitions"])
            self.assertEqual(branch["n_ticks"],256)
            self.assertEqual(branch["rng_tape_size"],4096)
        b=record["branches"]["B"]
        bp=record["branches"]["B+"]
        self.assertEqual(b["random_cursor_final"],0)
        self.assertEqual(b["accepted_total"],0)
        self.assertEqual(b["initial_wiring"],bp["initial_wiring"])
        self.assertEqual(b["rng_tape_digest"],bp["rng_tape_digest"])
        assert bp["first_accepted_tick"] is None or (
            record["first_neural_divergence"] is None
            or record["first_neural_divergence"]>=bp["first_accepted_tick"]
        )

    def test_two_runs_are_identical_without_global_rng(self):
        a=run_seed(801)
        b=run_seed(801)
        self.assertEqual(a,b)

    def test_aggregates_and_no_fabricated_learning_gate(self):
        doc=run_all((800,))
        self.assertEqual(doc["n_seeds"],1)
        self.assertEqual(doc["ticks_per_seed"],256)
        self.assertEqual(doc["gate_G05_G09"],"NOT TESTED")
        self.assertEqual(doc["totals"]["B"]["accepted"],0)
        self.assertEqual(doc["totals"]["B"]["draws_consumed"],0)
        self.assertEqual(
            doc["totals"]["B+"]["accepted"],
            doc["per_seed"][0]["branches"]["B+"]["accepted_total"],
        )
        with self.assertRaises(ValueError):
            run_all((800,800))
        with self.assertRaises(ValueError):
            run_all((500,))


if __name__=="__main__":
    unittest.main()
