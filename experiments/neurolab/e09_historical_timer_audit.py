"""E09h.6b: C1 90ms nominal WM_TIMER → world update static audit.

The requested Win32 timer period is NOT a measured real-time frequency.
No user-owned EXE is executed or distributed. CI verifies this auditor on
synthetic memory and import data, not the original third-party binary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from .e09_historical_timing_audit import PE32, EXE_SHA256

SIGNATURES = {
    0x411F50: "a18cf04300",       # timer owner from global 0x43f08c
    0x411F5C: "6a00",             # NULL callback; messages via HWND
    0x411F5E: "6a5a",             # 90 ms requested
    0x411F60: "6a01",             # timer ID =1
    0x411F62: "50",               # HWND, object+0x20
    0x411F63: "ff154c114400",     # USER32.SetTimer IAT
    0x411F70: "a18cf04300",       # corresponding cancel wrapper
    0x411F7C: "6a01",             # timer ID =1
    0x411F7F: "ff1544114400",     # USER32.KillTimer
    0x418960: "8b0d88f04300",     # WM_TIMER method loads world object
    0x424C88: "8b1584f04300",     # alternate caller guarded
    0x426884: "8b1584f04300",     # alternate caller guarded
    0x40D06E: "6a00",             # separate UI 500ms timer
    0x40D070: "68f4010000",
    0x40D075: "6a01",
    0x40D077: "52",
    0x40D078: "ff154c114400",
}

DIRECT_CALLS = {
    0x418966: 0x4247B0,          # message handler → world
    0x424C98: 0x4247B0,          # second explicit caller, gated
    0x426894: 0x4247B0,          # third explicit caller, gated
    0x424C4A: 0x411F70,          # cancel on state transition
    0x424CD9: 0x411F50,          # install on state transition
    0x426846: 0x411F70,          # cancel on state transition
    0x4268C9: 0x411F50,          # install on state transition
}

MESSAGE_MAP = {
    0x433988: 0x113,             # WM_TIMER
    0x43398C: 0x0,               # nCode
    0x433990: 0x0,               # id
    0x433994: 0x0,               # lastId
    0x433998: 0xD,               # MFC signature; not interpreted further
    0x43399C: 0x418960,          # handler
}


def read_rva(pe: PE32, rva: int, n: int) -> bytes:
    if n <= 0:
        raise ValueError("positive length required")
    for _name, start, _virtual, raw, off in pe.sections:
        if start <= rva and rva + n <= start + raw:
            return pe.data[off+rva-start:off+rva-start+n]
    raise ValueError(f"unmapped PE RVA {rva:#x}")


def imported_function(pe: PE32, iat_va: int) -> tuple[str, str]:
    """Resolve one IAT slot through PE import descriptors, no guessing APIs."""
    header = struct.unpack_from("<I",pe.data,0x3C)[0]
    directory_rva, _size = struct.unpack_from("<II",pe.data,header+24+104)
    if directory_rva == 0:
        raise ValueError("no PE import directory")

    def asciz(rva: int) -> str:
        chars = bytearray()
        for i in range(160):
            byte = read_rva(pe,rva+i,1)[0]
            if byte == 0:
                return chars.decode("ascii")
            chars.append(byte)
        raise ValueError("unterminated import name")

    sought = iat_va-pe.image_base
    for i in range(100):
        oft, _timestamp, _chain, name_rva, ft = struct.unpack(
            "<IIIII",read_rva(pe,directory_rva+20*i,20)
        )
        if oft == ft == name_rva == 0:
            break
        dll = asciz(name_rva)
        lookup = oft or ft
        for j in range(512):
            entry_rva = lookup + 4*j
            entry = struct.unpack("<I",read_rva(pe,entry_rva,4))[0]
            if entry == 0:
                break
            if ft+4*j == sought:
                if entry & 0x80000000:
                    raise ValueError("ordinal-only import")
                return dll,asciz(entry+2)
    raise AssertionError(f"IAT address not resolved {iat_va:#x}")


def verify(pe: PE32) -> dict:
    for va, sig in SIGNATURES.items():
        expected = bytes.fromhex(sig)
        if pe.at(va,len(expected)) != expected:
            raise AssertionError(f"wrong timer instruction at {va:#x}")
    for site, expected in DIRECT_CALLS.items():
        if pe.direct_call(site) != expected:
            raise AssertionError(f"timer call target mismatch {site:#x}")
    for va, expected in MESSAGE_MAP.items():
        actual=struct.unpack("<I",read_rva(pe,va-pe.image_base,4))[0]
        if actual != expected:
            raise AssertionError(f"WM_TIMER map mismatch at {va:#x}")
    for va, api in ((0x44114C,"SetTimer"),(0x441144,"KillTimer")):
        dll, actual = imported_function(pe,va)
        if dll.upper()!="USER32.DLL" or actual!=api:
            raise AssertionError(f"unexpected import at {va:#x}: {dll}.{actual}")
    return {
        "instruction_signatures_verified": len(SIGNATURES),
        "direct_calls_verified": len(DIRECT_CALLS),
        "message_map_fields_verified": len(MESSAGE_MAP),
        "api_imports_verified": ["USER32.SetTimer","USER32.KillTimer"],
        "timer": {
            "settimer_site":"0x411f63","killtimer_site":"0x411f7f",
            "requested_period_ms":90,"timer_id":1,"callback":"NULL",
            "hwnd_source":"object at global 0x43f08c +0x20",
        },
        "message": {
            "id":"0x113 WM_TIMER",
            "handler":"0x418960","world_call":"0x418966 → 0x4247b0",
            "secondary_call_sites":["0x424c98","0x426894"]
        },
        "other_timer": {
            "site":"0x40d078","period_ms":500,
            "scope":"different HWND/context; do not conflate with 90ms world timer"
        },
        "limits": (
            "90ms is requested Windows timer interval; OS scheduling, "
            "message coalescing, pause, multiple call routes, and "
            "round-robin phase select actual per-Norn event spacing"
        )
    }


def audit(exe: bytes) -> dict:
    digest = hashlib.sha256(exe).hexdigest()
    if digest != EXE_SHA256:
        raise ValueError("wrong or altered C1 executable")
    pe=PE32(exe)
    if pe.image_base!=0x400000:
        raise AssertionError("unexpected image base")
    return {
        "protocol":"E09_H_06B_CADENCIA_PRE_REGISTRO-v1",
        "source":{"exe_sha256":digest,"bytes":len(exe)},
        "evidence":verify(pe),
        "gate":"G-H6-CLOCK-NOMINAL satisfied; G-H6-CLOCK effective open",
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--exe",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    result=json.dumps(audit(a.exe.read_bytes()),indent=2,sort_keys=True)+"\n"
    if a.output:
        a.output.write_text(result,encoding="utf-8")
    print(result,end="")


if __name__=="__main__":
    main()
