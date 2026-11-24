"""E09h.1: self-contained PE32 fixture tests; no C1 proprietary binaries in CI."""
from __future__ import annotations

import struct
import unittest

from experiments.neurolab.e09_historical_timing_audit import (
    PE32, audit, SIGNATURES, CALL_GROUPS, EXE_SHA256, GEN_SHA256,
)


def synthetic_pe() -> bytes:
    """Make a minimal fake PE with .text RVA0x1000, no copyrighted bytes."""
    data = bytearray(0x400)
    data[:2] = b"MZ"
    struct.pack_into("<I",data,0x3C,0x80)
    data[0x80:0x84] = b"PE\x00\x00"
    struct.pack_into("<H",data,0x84,0x14C)  # i386
    struct.pack_into("<H",data,0x86,1)      # single section
    struct.pack_into("<H",data,0x94,0xE0)   # optional header length
    struct.pack_into("<H",data,0x98,0x10B)  # PE32 magic
    struct.pack_into("<I",data,0x98+28,0x400000)
    section = 0x80+24+0xE0
    data[section:section+8] = b".text\x00\x00\x00"
    struct.pack_into("<IIII",data,section+8,0x80,0x1000,0x80,0x200)
    data[0x210:0x215] = bytes.fromhex("e805000000")
    return bytes(data)


class HistoricalTimingAuditTests(unittest.TestCase):
    def test_fake_pe_maps_va_to_raw_file(self):
        image = PE32(synthetic_pe())
        self.assertEqual(image.image_base,0x400000)
        self.assertEqual(image.at(0x401010,5),bytes.fromhex("e805000000"))
        self.assertEqual(image.direct_call(0x401010),0x40101A)

    def test_falsification_non_call_or_invalid_address(self):
        image = PE32(synthetic_pe())
        with self.assertRaises(ValueError):
            image.direct_call(0x401000)
        with self.assertRaises(ValueError):
            image.at(0x402000,1)
        with self.assertRaises(ValueError):
            image.at(0x401000,0)

    def test_corrupt_headers_rejected(self):
        for corrupted in (b"",b"\x00"*0x400):
            with self.assertRaises(ValueError):
                PE32(corrupted)
        bad = bytearray(synthetic_pe())
        bad[0x80:0x84] = b"NOPE"
        with self.assertRaises(ValueError):
            PE32(bytes(bad))

    def test_invalid_original_hash_does_not_produce_evidence(self):
        with self.assertRaises(ValueError):
            audit(synthetic_pe(),b"not a genome")

    def test_static_contract_has_ordered_independent_stages(self):
        self.assertEqual(len(SIGNATURES),12)
        self.assertEqual(sum(map(len,CALL_GROUPS.values())),10)
        for entries in CALL_GROUPS.values():
            self.assertEqual(entries, sorted(entries))
        self.assertEqual(
            [dest for _,dest in CALL_GROUPS["regular_creature_tick"]],
            [0x403BB0,0x421E70,0x40A4B0],
        )
        self.assertEqual(
            [dest for _,dest in CALL_GROUPS["alternate_event_path"]],
            [0x421E70,0x403BB0],
        )
        self.assertEqual(len(EXE_SHA256),64)
        self.assertEqual(len(GEN_SHA256),64)


if __name__ == "__main__":
    unittest.main()
