"""I3c.2 falsifiable synthetic x86 migration caller tests."""
import unittest
from experiments.neurolab.e09_i3c2_migration_callsite_audit import (
    SIGNATURES,CALLS,verify,audit
)

class FakePE:
    def __init__(self):
        self.code={addr:bytes.fromhex(raw) for addr,raw in SIGNATURES.items()}
        self.calls=dict(CALLS)
    def at(self,addr,size):
        data=self.code[addr]
        assert len(data)==size
        return data
    def direct_call(self,addr):
        return self.calls[addr]


class MigrationCallerTests(unittest.TestCase):
    def test_both_classes_and_calls_are_recorded(self):
        r=verify(FakePE())
        self.assertEqual(r["signatures_verified"],len(SIGNATURES))
        self.assertEqual(r["direct_calls_verified"],2)
        self.assertEqual(r["type1"]["call"],"0x40494c -> 0x404a80")
        self.assertEqual(r["type2"]["call"],"0x4049c2 -> 0x404b90")

    def test_type1_zero_output_gate_change_fails(self):
        p=FakePE()
        p.code[0x40493E]=bytes.fromhex("7511")
        with self.assertRaisesRegex(AssertionError,"signature mismatch"):
            verify(p)

    def test_type2_selection_sentinel_change_fails(self):
        p=FakePE()
        p.code[0x40499D]=bytes.fromhex("83ff00")
        with self.assertRaisesRegex(AssertionError,"signature mismatch"):
            verify(p)

    def test_type2_wrong_target_fails(self):
        p=FakePE()
        p.calls[0x4049C2]=0x404A80
        with self.assertRaisesRegex(AssertionError,"call target mismatch"):
            verify(p)

    def test_unverified_executable_rejected(self):
        with self.assertRaisesRegex(ValueError,"unknown or altered"):
            audit(b"MZ"+bytes(512))


if __name__=="__main__":
    unittest.main()
