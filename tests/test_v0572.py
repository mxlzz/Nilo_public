"""Pruebas de reproducción completa de plan_ready + tick sin cuota LLM."""
from __future__ import annotations
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nilo
from reproducir import ReplayError, run_replay

CASE = Path(__file__).parent / "fixtures" / "replay_basico.json"


class ReplayIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = json.loads(CASE.read_text(encoding="utf-8"))

    def test_same_decisions_seed_clock_produce_identical_full_state(self):
        first = run_replay(self.case)
        second = run_replay(self.case)
        self.assertEqual(first, second)
        self.assertEqual(first["decisions_consumed"], 2)
        self.assertEqual(len(first["state_sha256"]), 64)
        self.assertEqual(len(first["archive_sha256"]), 64)
        self.assertTrue(first["trace"])
        self.assertLess(first["ticks"], self.case["max_ticks"])

    def test_world_seed_changes_replay(self):
        changed = copy.deepcopy(self.case)
        changed.pop("expected_fingerprint", None)
        changed["world_seed"] += 1
        self.assertNotEqual(
            run_replay(self.case)["fingerprint"], run_replay(changed)["fingerprint"]
        )

    def test_decision_change_changes_replay(self):
        changed = copy.deepcopy(self.case)
        changed.pop("expected_fingerprint", None)
        changed["decisions"][0]["cuaderno"] = "Texto distinto con efectos en el diario."
        self.assertNotEqual(
            run_replay(self.case)["fingerprint"], run_replay(changed)["fingerprint"]
        )

    def test_expected_hash_rejects_unexpected_state(self):
        changed = copy.deepcopy(self.case)
        changed.pop("expected_fingerprint", None)
        changed["expected_fingerprint"] = "0" * 64
        with self.assertRaisesRegex(ReplayError, "Divergencia"):
            run_replay(changed)

    def test_replay_does_not_create_real_database(self):
        with tempfile.TemporaryDirectory() as directory:
            real_db = Path(directory) / "no-tocar.sqlite3"
            with patch.object(nilo, "DB", real_db):
                run_replay(self.case)
            self.assertFalse(real_db.exists())

    def test_rejects_invalid_or_runaway_scenarios(self):
        for changes in (
            {"seconds_per_tick": 25},
            {"max_ticks": 0},
            {"decisions": []},
            {"format": "no-replay"},
        ):
            case = {**self.case, **changes}
            with self.subTest(changes=changes), self.assertRaises(ReplayError):
                run_replay(case)

    def test_budget_exhaustion_is_not_reported_as_success(self):
        changed = copy.deepcopy(self.case)
        changed.pop("expected_fingerprint", None)
        changed["max_ticks"] = 1
        with self.assertRaisesRegex(ReplayError, "max_ticks"):
            run_replay(changed)


if __name__ == "__main__":
    unittest.main()
