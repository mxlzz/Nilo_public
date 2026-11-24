"""E09.02i-I1b: audit the C1 global chemical decay loop in original PE32.

Verifies the 256-slot two-byte pool layout, the conditional helper call,
byte store and loop stride. No game execution, proprietary binary in CI,
or claim that original per-chemical rate values were recovered.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .e09_historical_timing_audit import PE32, EXE_SHA256


SIGNATURES = {
    0x4221CD: "8d7708",       # start of concentration/rate slots at pool +8
    0x4221D0: "bf00010000",   # 256 iterations
    0x4221D5: "8a4601",       # rate at slot+1
    0x4221DC: "8a06",         # concentration at slot+0
    0x4221DE: "84c0",         # check concentration
    0x4221E0: "7413",         # skip helper on zero
    0x4221E2: "8b4c2434",   # loop tick
    0x4221E6: "8b54242c",   # rate value
    0x4221EA: "51",
    0x4221EB: "52",
    0x4221EC: "56",         # concentration pointer
    0x4221F5: "8806",       # update concentration
    0x4221F7: "83c602",   # next [concentration, rate]
    0x4221FA: "4f",         # decrease loop counter
    0x4221FB: "75d8",      # repeat until 256 visited
}
CALLS = {0x4221ED:0x419E40}


def verify(pe: PE32) -> dict:
    for site,signature in SIGNATURES.items():
        expected=bytes.fromhex(signature)
        if pe.at(site,len(expected)) != expected:
            raise AssertionError(f"global chemical decay instruction mismatch {site:#x}")
    for site,expected in CALLS.items():
        if pe.direct_call(site)!=expected:
            raise AssertionError(f"decay function not bound at {site:#x}")
    return {
        "signatures_verified":len(SIGNATURES),
        "direct_calls_verified":len(CALLS),
        "slots":256,
        "slot_byte_offsets":{"concentration":0,"rate":1},
        "slot_stride_bytes":2,
        "helper":"0x419e40",
        "call_site":"0x4221ed",
        "pool_loop_range":"0x4221cd..0x4221fd",
        "chemical_order":"emitters -> receptors -> reactions -> global decay",
        "limits":"Rate values and observed real-time concentrations NOT inferred from this loop",
    }


def audit(exe: bytes) -> dict:
    sha=hashlib.sha256(exe).hexdigest()
    if sha!=EXE_SHA256:
        raise ValueError("wrong EXE build")
    pe=PE32(exe)
    if pe.image_base!=0x400000:
        raise AssertionError("unexpected image base")
    return {
        "protocol":"E09_02I_1B_POOL_DECAY_PRE_REGISTRO-v1",
        "source":{"exe_sha256":sha,"bytes":len(exe)},
        "static_evidence":verify(pe),
        "gate":"G-I1b-X86 static loop confirmed, GEN rate provenance pending",
    }


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--exe",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    data=json.dumps(audit(args.exe.read_bytes()),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(data,encoding="utf-8")
    print(data,end="")


if __name__=="__main__":
    main()
