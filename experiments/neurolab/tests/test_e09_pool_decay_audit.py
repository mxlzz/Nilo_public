"""E09.02i-I1b: synthetic regression for hash-gated x86 loop auditor."""
import unittest

from experiments.neurolab.e09_pool_decay_audit import (
    SIGNATURES,CALLS,audit,verify,
)


class FakePE:
    def __init__(self):
        self.code={va:bytes.fromhex(raw) for va,raw in SIGNATURES.items()}
        self.calls=dict(CALLS)
    def at(self,va,size):
        data=self.code[va]
        if len(data)!=size:
            raise ValueError("wrong synthetic instruction length")
        return data
    def direct_call(self,va):
        return self.calls[va]


class ChemicalDecayAuditTests(unittest.TestCase):
    def test_synthetic_loop_contract(self):
        result=verify(FakePE())
        self.assertEqual(result["slots"],256)
        self.assertEqual(result["slot_stride_bytes"],2)
        self.assertEqual(result["slot_byte_offsets"],{
            "concentration":0,"rate":1
        })
        self.assertEqual(result["signatures_verified"],15)
        self.assertEqual(result["helper"],"0x419e40")

    def test_changed_slot_stride_fails(self):
        pe=FakePE()
        pe.code[0x4221F7]=bytes.fromhex("83c603")
        with self.assertRaisesRegex(AssertionError,"instruction mismatch"):
            verify(pe)

    def test_changed_loop_count_fails(self):
        pe=FakePE()
        pe.code[0x4221D0]=bytes.fromhex("bf00020000")
        with self.assertRaisesRegex(AssertionError,"instruction mismatch"):
            verify(pe)

    def test_wrong_helper_target_fails(self):
        pe=FakePE()
        pe.calls[0x4221ED]=0x419E90
        with self.assertRaisesRegex(AssertionError,"decay function"):
            verify(pe)

    def test_wrong_executable_hash_rejected(self):
        with self.assertRaises(ValueError):
            audit(b"MZ"+bytes(256))


if __name__=="__main__":
    unittest.main()
