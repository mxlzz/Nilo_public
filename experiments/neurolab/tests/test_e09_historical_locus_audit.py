"""E09h.4 historical static pointer audit: synthetic tests; no proprietary EXE."""
from __future__ import annotations

import struct
import unittest

from experiments.neurolab.e09_historical_locus_audit import (
    SIGNATURES, LOCUS_JUMPS, audit, verify_link, rdata_at,
)
from experiments.neurolab.e09_historical_timing_audit import PE32


def synthetic_memory():
    """The test deliberately constructs all bytes independently of the EXE."""
    memory = {
        (va, len(bytes.fromhex(raw))): bytes.fromhex(raw)
        for va, raw in SIGNATURES.items()
    }
    memory[(0x43302C, 4)] = struct.pack("<I", 0x4030E0)
    for locus, (target, offset) in LOCUS_JUMPS.items():
        index = locus
        memory[(0x40324C+locus, 1)] = bytes((index,))
        memory[(0x403200 + 4*index, 4)] = struct.pack("<I", target)
        memory[(target, 8)] = b"\x05" + struct.pack("<I",offset) + b"\xc2\x0c\x00"
    return memory


def readers(memory):
    def at(va, size):
        if (va, size) not in memory:
            raise AssertionError(f"missing synthetic address {va:#x}")
        return memory[(va,size)]
    return at, at


class C1LocusLinkAuditTests(unittest.TestCase):
    def test_complete_synthetic_dispatch_contract(self):
        memory=synthetic_memory()
        proof=verify_link(*readers(memory))
        self.assertEqual(proof["verified_instruction_signatures"],len(SIGNATURES))
        self.assertEqual(
            [(x["genetic_receptor_locus"],x["lobe_relative_byte_offset"],
              x["svrule_opcode"]) for x in proof["validated_bindings"]],
            [(13,"0xc3",5),(14,"0xc4",6),
             (15,"0xc5",7),(16,"0xc6",8)],
        )

    def test_one_changed_dispatch_target_fails(self):
        memory=synthetic_memory()
        memory[(0x403200 + 13*4,4)] = struct.pack("<I",0x403135)
        with self.assertRaisesRegex(AssertionError,"dispatch"):
            verify_link(*readers(memory))

    def test_one_changed_byte_offset_fails(self):
        memory=synthetic_memory()
        memory[(0x403183,8)]=b"\x05"+struct.pack("<I",0xC2)+b"\xc2\x0c\x00"
        with self.assertRaisesRegex(AssertionError,"offset"):
            verify_link(*readers(memory))

    def test_one_changed_c1_instruction_fails(self):
        memory=synthetic_memory()
        addr=0x421ACF
        memory[(addr,2)]=b"\x90\x90"
        with self.assertRaisesRegex(AssertionError,"instruction mismatch"):
            verify_link(*readers(memory))

    def test_wrong_vtable_fails(self):
        memory=synthetic_memory()
        memory[(0x43302C,4)]=struct.pack("<I",0x4032E0)
        with self.assertRaisesRegex(AssertionError,"vtable"):
            verify_link(*readers(memory))

    def test_original_hash_gate_precedes_pe_parse(self):
        with self.assertRaisesRegex(ValueError,"wrong build"):
            audit(b"MZ" + bytes(256))

    def test_no_rdata_in_fake_text_only_pe(self):
        from experiments.neurolab.tests.test_e09_historical_timing_audit import synthetic_pe
        with self.assertRaises(ValueError):
            rdata_at(PE32(synthetic_pe()),0x43302C,4)


if __name__ == "__main__":
    unittest.main()
