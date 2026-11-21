"""E09h.5: static C1 brain emitter-to-chemical pool audit.

Accepts only the user's exact hash-verified Creatures.exe as --exe.
No game execution or proprietary binary redistribution. Synthetic CI tests
verify this auditor, NOT that CI reopens the original game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from .e09_historical_timing_audit import PE32, EXE_SHA256
from .e09_historical_locus_audit import rdata_at

SIGNATURES = {
    0x421B7A: "8b89182c0000",     # norn+2C18 brain*
    0x421B80: "83c104",           # brain locus vtable
    0x421B83: "8b01",
    0x421B85: "52536a01ff10",     # kind=1, lobe, locus
    0x421C17: "894708",           # store bound pointer at emitter+8
    0x4031C3: "8a9184324000",     # lobe locus kind1 switch byte table
    0x4031C9: "ff249570324000",   # jump table base 0x403270
    0x421E83: "8b878c120000",     # emitter count
    0x421E91: "8db70e080000",     # emitter struct+6
    0x421E97: "8a4e01",           # flags
    0x421E9A: "8b4602",           # bound source byte ptr
    0x421E9D: "f6c104",           # flag4 invert
    0x421EA4: "bdff000000",
    0x421EAB: "2bea",
    0x421EB5: "85ed",             # source nonzero gate
    0x421EBD: "8b442434",         # tick
    0x421EC3: "8a5eff",           # sampling interval
    0x421EC8: "f7f3",             # tick modulo interval
    0x421ED4: "8a46fe",           # threshold
    0x421ED7: "2be8",
    0x421EDF: "f6c102",           # flag2 full gain
    0x421EEB: "8a06",             # gain
    0x421F17: "0fafc1",           # x*gain
    0x421F1F: "c1e808",           # >>8
    0x421F26: "8a544f08",         # chemical pool byte stride2
    0x421F4B: "88444f08",         # chemical pool saturated write
    0x421F4F: "f6460101",         # flag1 source reset
    0x421F55: "8b4602",           # reload source pointer
    0x421F58: "c60000",           # write zero
    0x421F77: "8b8788120000",     # next receptor stage
}
LOBE_LOCI = {1:(0x4031D8,0xC1), 2:(0x4031E0,0xC2)}


def verify_emitter_link(read_text, read_rdata) -> dict:
    for va, signature in SIGNATURES.items():
        expected = bytes.fromhex(signature)
        if read_text(va,len(expected)) != expected:
            raise AssertionError(f"emitter signature mismatch at {va:#x}")
    if struct.unpack("<I",read_rdata(0x43302C,4))[0] != 0x4030E0:
        raise AssertionError("unexpected brain locus virtual resolver")
    locus_result=[]
    for locus,(target,offset) in LOBE_LOCI.items():
        idx=read_text(0x403284+locus,1)[0]
        actual=struct.unpack("<I",read_text(0x403270+idx*4,4))[0]
        if actual!=target:
            raise AssertionError(f"emitter locus{locus}: incorrect resolver target")
        body=read_text(target,8)
        if (body[0]!=5 or body[5:]!=bytes.fromhex("c20c00")
                or struct.unpack("<I",body[1:5])[0]!=offset):
            raise AssertionError(f"emitter locus{locus}: incorrect resolver offset")
        locus_result.append({
            "gene_locus":locus,"lobe_offset":hex(offset),
            "case_va":hex(target),"brain_vtable_kind":1,
        })
    return {
        "instruction_signatures_verified":len(SIGNATURES),
        "brain_vtable_method":"0x4030e0",
        "source_locus_destinations":locus_result,
        "tick_entry":"0x421e83",
        "pool_write":"0x421f4b",
        "reset_when_flag1":"0x421f4f..0x421f58",
        "next_receptor_stage":"0x421f77",
        "chemical_zero_note":(
            "both branches jump to 0x421f4f for chemical=0; "
            "eligible flag1 still zeroes source without pool mutation"
        ),
        "limits":"static code path, no live concentration or neuron trace",
    }


def audit(exe: bytes) -> dict:
    source_hash=hashlib.sha256(exe).hexdigest()
    if source_hash!=EXE_SHA256:
        raise ValueError("not verified original C1 executable")
    pe=PE32(exe)
    if pe.image_base!=0x400000:
        raise AssertionError("unexpected image base")
    return {
        "protocol":"E09_H_05_EMISORES_PRE_REGISTRO-v1",
        "source":{"exe_sha256":source_hash,"exe_bytes":len(exe)},
        "static_evidence":verify_emitter_link(
            pe.at,lambda va,n:rdata_at(pe,va,n)
        ),
        "scope":"G-H5-X86 for two documented brain-emitter loci, not full game",
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe",required=True,type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=json.dumps(audit(args.exe.read_bytes()),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(result,encoding="utf-8")
    print(result,end="")


if __name__=="__main__":
    main()
