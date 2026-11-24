"""E09h.6a: verify C1 conditional brain/chem paths and round-robin scheduler.

This is a STATIC proof for one hash-verified executable, not a measured
clock frequency. CI uses synthetic PE and confirms the auditor only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .e09_historical_timing_audit import PE32, EXE_SHA256

SIGNATURES = {
    0x407543: "8b86bc2c0000",  # Norn+2cbc gate: skip regular
    0x40754B: "7564",
    0x40754D: "8a86cc2c0000",  # Norn+2ccc brain/behavior gate
    0x407555: "7531",
    0x407576: "8b96202c0000",  # same tick passed to brain
    0x407588: "8b86202c0000",  # and chemistry
    0x40759A: "8a86cc2c0000",
    0x4075A2: "7507",
    0x4075AB: "ff86202c0000",  # counter increment
    0x4075C6: "8b86bc2c0000",  # alternate only when 2cbc!=0
    0x4075CE: "0f8415010000",
    0x4075F9: "8b96202c0000",  # alternate counter
    0x407620: "8b86202c0000",
    0x407657: "8b86202c0000",
    0x40765E: "8986202c0000",  # alternate counter increment
    0x4247B9: "33db",          # EBX=0; compare inactive flag with BL
    0x424867: "8b35acea4300",  # global phase index
    0x424874: "7d25",
    0x42487C: "8b0cb1",        # active entity from array+4*index
    0x42488E: "83c604",        # next index in phase
    0x42489D: "46",            # increment phase
    0x42489E: "83fa04",        # wrap when previous phase ==4
    0x4248A9: "891dacea4300",  # zero phase
    0x4249F9: "a3b0bb4300",   # world update counter
}

DIRECT_CALLS = {
    0x407583: 0x403BB0,  # regular brain
    0x407595: 0x421E70,  # regular biochemistry
    0x4075A6: 0x40A4B0,  # behavior
    0x40764B: 0x405D20,  # alternate branch dispatch
    0x405D32: 0x421E70,  # alternate: chemistry first
    0x405DAF: 0x403BB0,  # alternate: brain second
    0x424884: 0x407540,  # round-robin regular update
    0x4248C3: 0x4075C0,  # separate pass over all creatures
}


def verify(static_pe: PE32) -> dict:
    for va, hex_expected in SIGNATURES.items():
        expected = bytes.fromhex(hex_expected)
        if static_pe.at(va, len(expected)) != expected:
            raise AssertionError(f"signature mismatch at {va:#x}")
    for site, target in DIRECT_CALLS.items():
        found = static_pe.direct_call(site)
        if found != target:
            raise AssertionError(f"call at {site:#x} -> {found:#x}; expected {target:#x}")
    return {
        "verified_instruction_signatures": len(SIGNATURES),
        "verified_direct_calls": len(DIRECT_CALLS),
        "regular": {
            "branch_entry": "0x407540",
            "skip_if_norn_2cbc_nonzero": "0x40754b -> 0x4075b1",
            "skip_brain_and_behavior_if_2ccc_nonzero": [
                "0x407555 -> 0x407588", "0x4075a2 -> 0x4075ab"
            ],
            "shared_pre_increment_norn_counter": "norn+0x2c20",
            "normal_order": ["brain", "chemistry", "behavior", "increment norn counter"],
            "2ccc_nonzero_order": ["chemistry", "increment norn counter"],
        },
        "alternate": {
            "caller": "0x40764b in 0x4075c0",
            "entered_only_when_norn_2cbc_nonzero": "0x4075ce",
            "order": ["chemistry", "brain"],
            "counter_increment_branches": [
                "0x407620..0x407627", "0x407657..0x40765e"
            ],
            "qualified": "stateful alternative path; not additional regular tick",
        },
        "world": {
            "function": "0x4247b0",
            "regular_list_pass": "0x424867..0x4248af",
            "regular_phase_range": "0..4",
            "phase_stride": 4,
            "regular_skip_when_creature_flag_4c_zero": "0x424882",
            "separate_all_creatures_pass": "0x4248af..0x4248d2",
            "all_creatures_call": "0x4248c3 -> 0x4075c0",
            "global_counter_increment": "0x4249f1..0x4249fe",
        },
        "limits": (
            "No real-time cadence in seconds/Hz; no exhaustive indirect caller "
            "analysis, no dynamic trace, no equivalence with full original game"
        ),
    }


def audit(exe: bytes) -> dict:
    sha256 = hashlib.sha256(exe).hexdigest()
    if sha256 != EXE_SHA256:
        raise ValueError("unverified Creatures C1 EXE")
    pe = PE32(exe)
    if pe.image_base != 0x400000:
        raise AssertionError("unexpected PE32 base")
    return {
        "protocol": "E09_H_06_SCHEDULER_PRE_REGISTRO-v1",
        "source": {"sha256": sha256, "bytes": len(exe)},
        "evidence": verify(pe),
        "gate": "G-H6-FLOW static subset verified, G-H6-CLOCK open",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True, type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    payload = json.dumps(audit(args.exe.read_bytes()), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
