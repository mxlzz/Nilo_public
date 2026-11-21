"""E09.02i-I3c.2 static x86 migration callsite/gating audit.

Source: user-provided C1 Creatures.exe SHA256 548a8388..., 387072 bytes.
Only a bounded direct-call control-flow slice after WTA is examined.
Synthetic PE memory in CI; real EXE is neither executed nor redistributed.
Prereg: docs/neurolab/E09_02I_I3C2_INVOCADOR_MIGRACION_PRE_REGISTRO.md
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from .e09_historical_timing_audit import PE32,EXE_SHA256

SIGNATURES={
    0x4048CC:"f6432201",      # WTA branch gate
    0x4048F8:"c6400200",      # output clear of nonwinner
    0x404911:"8b842480000000",# migration iteration stage starts
    0x404922:"803901",        # class migration type1
    0x404925:"7538",          # skip type1 if !=1
    0x404939:"8a4602",        # output byte of candidate neuron
    0x40493C:"84c0",
    0x40493E:"7411",          # skip migration for output=0
    0x404947:"55",
    0x404948:"53",
    0x404949:"52",
    0x404951:"8b83a4000000",# neuron iteration count
    0x404963:"45",            # class loop
    0x404967:"83fd02",        # two class types
    0x404992:"803a02",        # class migration type2
    0x404997:"8b442438",      # selection index source
    0x40499D:"83ffff",        # sentinel -1 = no selected recipient
    0x4049A0:"7509",
    0x4049BD:"c1e104",        # index scaled by 16-byte neuron record
    0x4049C0:"03c8",          # add offset to neuron records
    0x4049C7:"897d00",        # persist recipient index
    0x4049DC:"83fe02",        # class loop
}
CALLS={0x40494C:0x404A80,0x4049C2:0x404B90}


def verify(pe:PE32)->dict:
    for site,raw in SIGNATURES.items():
        if pe.at(site,len(bytes.fromhex(raw))) != bytes.fromhex(raw):
            raise AssertionError(f"migration gating signature mismatch {site:#x}")
    for site,target in CALLS.items():
        if pe.direct_call(site)!=target:
            raise AssertionError(f"migration call target mismatch {site:#x}")
    return {
        "signatures_verified":len(SIGNATURES),
        "direct_calls_verified":len(CALLS),
        "wta_before_migration":"0x4048cc..0x404911",
        "type1":{
            "class_gate":"0x404922 checks class type=1",
            "neuron_output_gate":"0x404939..0x40493e skips if output=0",
            "call":"0x40494c -> 0x404a80",
            "class_iteration":"0x404963..0x40496a, 2 classes",
        },
        "type2":{
            "class_gate":"0x404992 checks class type=2",
            "selected_recipient_sentinel":"0x40499d rejects -1 index",
            "record_stride":"0x4049bd index<<4, 16 bytes",
            "call":"0x4049c2 -> 0x404b90",
        },
        "scope":"Original C1 direct callsites and subset of gates only; no global CRT rand(), recipient activity statistics, whole scheduler, migration frequency or Norn runtime traces",
    }


def audit(exe:bytes)->dict:
    digest=hashlib.sha256(exe).hexdigest()
    if digest!=EXE_SHA256:
        raise ValueError("unknown or altered Creatures C1 executable")
    pe=PE32(exe)
    if pe.image_base!=0x400000:
        raise AssertionError("wrong PE image base")
    return {
        "protocol":"E09_02I_I3C2_INVOCADOR_MIGRACION_PRE_REGISTRO-v1",
        "source":{"exe_sha256":digest,"bytes":len(exe)},
        "evidence":verify(pe),
        "gate":"G-I3c2-CALLSITE verified static subset, full historical scheduler remains open"
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--exe",required=True,type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    payload=json.dumps(audit(args.exe.read_bytes()),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(payload,encoding="utf-8")
    print(payload,end="")


if __name__=="__main__":
    main()
