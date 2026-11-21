"""Synthetic PE/anchor tests only; the proprietary original EXE is not in CI."""
import struct
import unittest

from experiments.neurolab.e09_i3c5b_exe_static_audit import (
    ANCHORS, SOURCE_SHA256, inspect, pe_text,
)


def fake_pe():
    size = 0x4800
    blob = bytearray(size)
    blob[:2] = b"MZ"
    struct.pack_into("<I", blob, 0x3C, 0x80)
    blob[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", blob, 0x86, 1)
    struct.pack_into("<H", blob, 0x94, 224)
    struct.pack_into("<H", blob, 0x98, 0x10B)
    struct.pack_into("<I", blob, 0x98 + 28, 0x400000)
    sec = 0x98 + 224
    blob[sec:sec+8] = b".text\0\0\0"
    struct.pack_into("<IIII", blob, sec+8, 0x4000, 0x1000, 0x4000, 0x200)
    for _, va, signature in ANCHORS:
        offset = 0x200 + va - 0x401000
        match = bytes.fromhex(signature)
        blob[offset:offset + len(match)] = match
    return bytes(blob)


class HistoricalStaticAuditTests(unittest.TestCase):
    def test_synthetic_pe_has_all_seven_anchored_signatures(self):
        fixture = fake_pe()
        self.assertEqual(pe_text(fixture)[0], 0x401000)
        result = inspect(fixture, identity_required=False)
        self.assertEqual(result["anchors_valid"], 7)
        self.assertEqual(len(result["anchored_blocks"]), 7)
        self.assertNotEqual(result["exe_sha256"], SOURCE_SHA256)
        self.assertEqual(result["G05_G09_G00H"].split()[0], "OPEN")

    def test_wrong_original_hash_fails_closed(self):
        with self.assertRaises(ValueError):
            inspect(fake_pe())
        with self.assertRaises(ValueError):
            inspect(b"MZ")

    def test_mutated_signal_or_fortaleza_basic_block_fails(self):
        fixture = fake_pe()
        for name in ("signal_loop", "zero_strength_entry",
                     "strength_reaches_zero_cleanup"):
            _, va, _ = next(x for x in ANCHORS if x[0] == name)
            data = bytearray(fixture)
            index = 0x200 + va - 0x401000
            data[index] ^= 0x01
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, name):
                inspect(bytes(data), identity_required=False)

    def test_bad_section_metadata_rejected(self):
        data = bytearray(fake_pe())
        data[0x98+224:0x98+224+5] = b".xyz\0"
        with self.assertRaises(ValueError):
            pe_text(bytes(data))


if __name__ == "__main__":
    unittest.main()
