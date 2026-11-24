"""Synthetic integrity controls: do not require or run C1 files."""
import struct
import unittest
from experiments.neurolab.h08a_static_audit import PE, parse_disassembly, literal_pointer_offsets, TARGETS


def fake_pe() -> bytes:
    b = bytearray(0x400)
    b[:2] = b'MZ'
    struct.pack_into('<I', b, 0x3C, 0x80)
    b[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<HH', b, 0x84, 0x14C, 1)
    struct.pack_into('<H', b, 0x94, 0xE0)
    struct.pack_into('<H', b, 0x98, 0x10B)
    struct.pack_into('<I', b, 0x98+28, 0x400000)
    header = 0x80+24+0xE0
    b[header:header+8] = b'.text\0\0\0'
    struct.pack_into('<IIII', b, header+8, 0x100, 0x1000, 0x100, 0x200)
    b[0x200:0x205] = b'\xe8\x0b\x00\x00\x00'
    return bytes(b)

class AuditTests(unittest.TestCase):
    def test_dos_or_pe_invalid(self):
        with self.assertRaisesRegex(ValueError, 'DOS'):
            PE(b'abc')
        invalid=bytearray(fake_pe())
        invalid[0x80:0x84] = b'BAD!'
        with self.assertRaisesRegex(ValueError, 'PE header'):
            PE(bytes(invalid))
    def test_truncated_section(self):
        invalid=bytearray(fake_pe())
        struct.pack_into('<I',invalid,0x80+24+0xE0+8+12,0x350)
        with self.assertRaisesRegex(ValueError, 'truncated section'):
            PE(bytes(invalid))
    def test_direct_call_little_endian(self):
        pe=PE(fake_pe())
        self.assertEqual(pe.direct_call(0x401000),0x401010)
        with self.assertRaisesRegex(ValueError, 'outside'):
            pe.at(0x402000,5)
        invalid=bytearray(fake_pe())
        invalid[0x200]=0x90
        with self.assertRaisesRegex(ValueError, 'no E8'):
            PE(bytes(invalid)).direct_call(0x401000)
    def test_objdump_line_crossvalidation(self):
        s='  407595:\te8 d6 a8 01 00       \tcall   0x421e70\n'
        z=parse_disassembly(s)
        self.assertEqual(z[0x421E70],[0x407595])
        self.assertFalse(any(z[t] for t in TARGETS if t!=0x421E70))
        bad=s.replace('e8 d6 a8','e8 d7 a8')
        with self.assertRaises(AssertionError):
            parse_disassembly(bad)
    def test_literal_pointer_is_only_literal(self):
        b=b'Z'+struct.pack('<I',0x403BB0)+b'X'+struct.pack('<I',0x403BB0)
        self.assertEqual(literal_pointer_offsets(b,0x403BB0),[1,6])

if __name__ == '__main__': unittest.main()
