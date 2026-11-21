"""E09h.6b: independent synthetic timer IAT, message map, and call tests."""
from __future__ import annotations

import struct
import unittest

from experiments.neurolab.e09_historical_timer_audit import (
    SIGNATURES, DIRECT_CALLS, MESSAGE_MAP, imported_function, verify, audit,
)


class FakePE:
    image_base = 0x400000

    def __init__(self):
        self.code = {va:bytes.fromhex(raw) for va,raw in SIGNATURES.items()}
        self.calls=dict(DIRECT_CALLS)
        self.sections=[
            (".rdata",0x33000,0x1200,0x1200,0x500),
            (".idata",0x40000,0x1B00,0x1B00,0x2000),
        ]
        raw = bytearray(0x4000)
        struct.pack_into("<I",raw,0x3C,0x80)
        struct.pack_into("<II",raw,0x80+24+104,0x40000,0x40)
        def store(rva,data):
            for _,base,_virtual,size,offset in self.sections:
                if base<=rva and rva+len(data)<=base+size:
                    raw[offset+rva-base:offset+rva-base+len(data)]=data
                    return
            raise AssertionError("outside synthetic PE section")
        for va,val in MESSAGE_MAP.items():
            store(va-self.image_base,struct.pack("<I",val))
        store(0x40000,struct.pack("<IIIII",0x40884,0,0,0x40200,0x410E4))
        store(0x40200,b"USER32.dll\x00")
        store(0x41502,b"Other\x00")
        store(0x41522,b"KillTimer\x00")
        store(0x41542,b"SetTimer\x00")
        for i in range(27):
            ptr = (0x41520 if i==24 else 0x41540 if i==26 else 0x41500)
            store(0x40884+4*i,struct.pack("<I",ptr))
        self.data = bytes(raw)

    def at(self,va,n):
        value=self.code[va]
        if len(value)!=n:
            raise AssertionError("unexpected requested length")
        return value

    def direct_call(self,va):
        return self.calls[va]


class TimerAuditTests(unittest.TestCase):
    def test_synthetic_complete_timer_proof(self):
        result=verify(FakePE())
        self.assertEqual(result["instruction_signatures_verified"],len(SIGNATURES))
        self.assertEqual(result["direct_calls_verified"],len(DIRECT_CALLS))
        self.assertEqual(result["message_map_fields_verified"],len(MESSAGE_MAP))
        self.assertEqual(result["timer"]["requested_period_ms"],90)
        self.assertEqual(result["timer"]["timer_id"],1)
        self.assertEqual(result["other_timer"]["period_ms"],500)
        self.assertIn("scheduling",result["limits"])

    def test_import_lookup_exact_function_names(self):
        fake=FakePE()
        self.assertEqual(imported_function(fake,0x44114C),("USER32.dll","SetTimer"))
        self.assertEqual(imported_function(fake,0x441144),("USER32.dll","KillTimer"))

    def test_changed_timer_interval_fails(self):
        fake=FakePE()
        fake.code[0x411F5E]=bytes.fromhex("6a64")
        with self.assertRaisesRegex(AssertionError,"timer instruction"):
            verify(fake)

    def test_changed_wm_timer_handler_fails(self):
        fake=FakePE()
        raw=bytearray(fake.data)
        # .rdata file offset 0x500, VA 0x43399c => RVA 0x3399c
        offset=0x500+(0x3399C-0x33000)
        struct.pack_into("<I",raw,offset,0x418970)
        fake.data=bytes(raw)
        with self.assertRaisesRegex(AssertionError,"WM_TIMER map"):
            verify(fake)

    def test_wrong_world_callback_fails(self):
        fake=FakePE()
        fake.calls[0x418966]=0x421E70
        with self.assertRaisesRegex(AssertionError,"target mismatch"):
            verify(fake)

    def test_wrong_user32_import_name_fails(self):
        fake=FakePE()
        raw=bytearray(fake.data)
        off=0x2000+(0x41542-0x40000)
        raw[off:off+8]=b"NoTimer\x00"
        fake.data=bytes(raw)
        with self.assertRaisesRegex(AssertionError,"unexpected import"):
            verify(fake)

    def test_binary_hash_required(self):
        with self.assertRaisesRegex(ValueError,"wrong or altered"):
            audit(b"MZ"+bytes(512))


if __name__=="__main__":
    unittest.main()
