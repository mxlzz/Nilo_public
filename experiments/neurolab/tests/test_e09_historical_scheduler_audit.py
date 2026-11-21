"""E09h.6a: falsifiable static branch/round-robin assertions.

All tests use synthetic byte slices; no C1 proprietary content in CI.
"""
from __future__ import annotations

import struct
import unittest

from experiments.neurolab.e09_historical_scheduler_audit import (
    SIGNATURES, DIRECT_CALLS, verify, audit,
)


class FakePE:
    def __init__(self):
        self.signatures = {
            va: bytes.fromhex(raw) for va, raw in SIGNATURES.items()
        }
        self.calls = dict(DIRECT_CALLS)

    def at(self, va, size):
        value=self.signatures.get(va)
        if value is None or len(value) != size:
            raise AssertionError(f"unknown synthetic address {va:#x}")
        return value

    def direct_call(self, va):
        return self.calls[va]


class HistoricalSchedulerAuditTests(unittest.TestCase):
    def test_valid_synthetic_control_flow_contract(self):
        answer=verify(FakePE())
        self.assertEqual(answer["verified_instruction_signatures"],len(SIGNATURES))
        self.assertEqual(answer["verified_direct_calls"],len(DIRECT_CALLS))
        self.assertEqual(answer["world"]["regular_phase_range"],"0..4")
        self.assertEqual(answer["world"]["phase_stride"],4)
        self.assertEqual(answer["regular"]["shared_pre_increment_norn_counter"],
                         "norn+0x2c20")
        self.assertEqual(answer["alternate"]["caller"],
                         "0x40764b in 0x4075c0")
        self.assertIn("Hz",answer["limits"])

    def test_one_modified_condition_rejected(self):
        fake=FakePE()
        fake.signatures[0x407555]=bytes.fromhex("7431")
        with self.assertRaisesRegex(AssertionError,"signature mismatch"):
            verify(fake)

    def test_one_modified_world_phase_step_rejected(self):
        fake=FakePE()
        fake.signatures[0x42488E]=bytes.fromhex("83c605")
        with self.assertRaisesRegex(AssertionError,"signature mismatch"):
            verify(fake)

    def test_one_wrong_alternate_call_rejected(self):
        fake=FakePE()
        fake.calls[0x40764B]=0x403BB0
        with self.assertRaisesRegex(AssertionError,"call at"):
            verify(fake)

    def test_original_hash_required(self):
        with self.assertRaisesRegex(ValueError,"unverified"):
            audit(b"MZ"+bytes(300))


if __name__ == "__main__":
    unittest.main()
