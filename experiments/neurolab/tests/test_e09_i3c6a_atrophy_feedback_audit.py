"""Synthetic PE x86 signatures only; original game EXE is NOT included in CI."""
import struct
import unittest

from experiments.neurolab.e09_i3c6a_atrophy_feedback_audit import (
    ANCHORS, inspect,
)


def fixture():
    buf=bytearray(0x5000)
    buf[:2]=b"MZ"
    struct.pack_into("<I",buf,0x3c,0x80)
    buf[0x80:0x84]=b"PE\0\0"
    struct.pack_into("<H",buf,0x86,1)
    struct.pack_into("<H",buf,0x94,224)
    struct.pack_into("<H",buf,0x98,0x10b)
    struct.pack_into("<I",buf,0x98+28,0x400000)
    section=0x98+224
    buf[section:section+8]=b".text\0\0\0"
    struct.pack_into("<IIII",buf,section+8,0x4000,0x1000,0x4000,0x200)
    for label,va,signature in ANCHORS:
        start=0x200+va-0x401000
        b=bytes.fromhex(signature)
        buf[start:start+len(b)]=b
    return bytes(buf)


class C1FeedbackWriterStaticTests(unittest.TestCase):
    def test_complete_synthetic_pe_and_ten_anchors(self):
        result=inspect(fixture(),require_provenance=False)
        self.assertEqual(result["anchor_count"],10)
        self.assertEqual(len(result["records"]),10)
        self.assertEqual(result["provenance_status"],"SYNTHETIC_FIXTURE_ONLY")
        self.assertEqual(result["G05_G09_G00H"],"OPEN")
        self.assertIn("MIN",result["type1_locus_rule"])
        self.assertIn("Increments one",result["type2_locus_rule"])

    def test_wrong_original_sha_rejected(self):
        with self.assertRaises(ValueError):
            inspect(fixture())
        with self.assertRaises(ValueError):
            inspect(b"MZ")

    def test_changed_count_or_locus_writer_fails_closed(self):
        original=fixture()
        for name in ("per_neuron_counter_reset","exhausted_dendrite_counter",
                     "type1_minimum_writer","type2_saturating_increment",
                     "loss_reset_and_counter"):
            va=next(v for n,v,_ in ANCHORS if n==name)
            damaged=bytearray(original)
            damaged[0x200+va-0x401000]^=0x01
            with self.subTest(anchor=name):
                with self.assertRaisesRegex(ValueError,name):
                    inspect(bytes(damaged),require_provenance=False)

    def test_class_sentinel_and_control_flow_signatures_locked(self):
        code={n:bytes.fromhex(b) for n,_,b in ANCHORS}
        self.assertEqual(code["type1_minimum_sentinel"][-1],0xff)
        self.assertIn(bytes.fromhex("3bc27d43"),code["type1_minimum_writer"])
        self.assertIn(bytes.fromhex("85c0742e"),code["type2_nonzero_gate"])
        self.assertIn(bytes.fromhex("3cff7309"),code["type2_saturating_increment"])
        self.assertEqual(code["next_class_iteration"][-6:],
                         bytes.fromhex("0f8cf0f8ffff"))


if __name__=="__main__":
    unittest.main()
