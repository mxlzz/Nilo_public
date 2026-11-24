"""E09h.5 source emitter x86 auditor: synthetic instruction memory only."""
import struct
import unittest

from experiments.neurolab.e09_historical_emitter_audit import (
    SIGNATURES, LOBE_LOCI, verify_emitter_link, audit,
)


def fake_bytes():
    data={(site,len(bytes.fromhex(raw))):bytes.fromhex(raw)
          for site,raw in SIGNATURES.items()}
    data[(0x43302C,4)]=struct.pack("<I",0x4030E0)
    for locus,(target,offset) in LOBE_LOCI.items():
        data[(0x403284+locus,1)]=bytes((locus,))
        data[(0x403270+locus*4,4)]=struct.pack("<I",target)
        data[(target,8)]=bytes((5,))+struct.pack("<I",offset)+bytes.fromhex("c20c00")
    return data


def read_fake(data):
    def reader(site,size):
        if (site,size) not in data:
            raise ValueError("unknown synthetic memory")
        return data[(site,size)]
    return reader,reader


class HistoricalEmitterAuditTests(unittest.TestCase):
    def test_synthetic_branch_contract(self):
        verified=verify_emitter_link(*read_fake(fake_bytes()))
        self.assertEqual(verified["instruction_signatures_verified"],len(SIGNATURES))
        self.assertEqual(
            [(b["gene_locus"],b["lobe_offset"]) for b in verified["source_locus_destinations"]],
            [(1,"0xc1"),(2,"0xc2")],
        )
        self.assertIn("chemical=0",verified["chemical_zero_note"])

    def test_changed_locus_table_fails(self):
        data=fake_bytes()
        data[(0x403270+4,4)]=struct.pack("<I",0x4031D0)
        with self.assertRaisesRegex(AssertionError,"resolver target"):
            verify_emitter_link(*read_fake(data))

    def test_changed_lobe_offset_fails(self):
        data=fake_bytes()
        data[(0x4031D8,8)]=bytes((5,))+struct.pack("<I",0xC2)+bytes.fromhex("c20c00")
        with self.assertRaisesRegex(AssertionError,"resolver offset"):
            verify_emitter_link(*read_fake(data))

    def test_changed_source_reset_instruction_fails(self):
        data=fake_bytes()
        data[(0x421F58,3)]=bytes((0x90,0x90,0x90))
        with self.assertRaisesRegex(AssertionError,"emitter signature"):
            verify_emitter_link(*read_fake(data))

    def test_wrong_original_sha_rejected(self):
        with self.assertRaises(ValueError):
            audit(b"MZ"+bytes(300))


if __name__=="__main__":
    unittest.main()
