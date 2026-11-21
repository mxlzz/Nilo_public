"""I3c.5b-H: static x86 provenance audit of *user-provided* Creatures.exe.

No game execution, disassembly dependency, file upload, or EXE redistribution.
Use: python -m experiments.neurolab.e09_i3c5b_exe_static_audit --exe /local/Creatures.exe
Report only SHA, anchored opcode fingerprints and manually decoded control flow.
Signatures establish this exact PE build, not all possible Creatures 1 versions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

SOURCE_SHA256 = "548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7"
SOURCE_SIZE = 387072
# Exact byte windows manually decoded from PE32 x86 in the original EXE.
# Do NOT infer conclusions from signatures alone without reviewing jump targets.
ANCHORS = (
    # Loop: source neuron output [edi+2] and STW [esi+7], no strength [esi+9] check.
    ("signal_loop", 0x403F2F,
     "8b3e33c08a47028bf885ff740f33c08a46070fafc7c1e80803d0eb0233db"),
    # Strength [esi+9] == 0 increments loose counter, but no jump over SVRule.
    ("zero_strength_entry", 0x4041A1,
     "8a460984c0884c2450885c245288542453884424557504ff442430"),
    # Entry for susceptibility rule following both strength==0/nonzero paths.
    ("susceptibility_rule_entry", 0x4041BC, "8a57268d4f2632c041"),
    # Gating at 0x404306 is on susceptibility [ebp+0], not strength [esi+9].
    ("plasticity_susceptibility_gate", 0x404306,
     "8a450084c00f84900100008a5730"),
    # Optional reinforcement math accesses STW [esi+7], LTW [esi+8].
    ("plasticity_stw_ltw", 0x404451, "8a560733db8a5e088bca"),
    # Upon strength reaching0, clears susceptibility, STW, LTW and neuron bytes.
    ("strength_reaches_zero_cleanup", 0x4047B9,
     "84c074258ac3fec8884609751c8b44243cc6450000c6460700c6460800c6400200c6400300"),
    # Type1 migration call is after WTA and tests active recipient output.
    ("post_wta_type1_caller", 0x404939,
     "8a460284c074118b9424fc0000005553528bcee82f010000"),
)

INTERPRETATION = {
    "signal_loop": "For each connected source pointer, reads source output byte [edi+2] and weight STW [esi+7]; tested block does not read strength [esi+9].",
    "zero_strength_entry": "Reads strength [esi+9], tests zero; zero increments exhausted counter via 0x4041b8; both paths converge at susceptibility SVRule 0x4041bc, rather than skipping numeric synapse update.",
    "susceptibility_rule_entry": "Common path after zero-strength counter enters susceptibility SVRule.",
    "plasticity_susceptibility_gate": "Observed branch into STW update is conditioned on susceptibility [ebp], not strength.",
    "plasticity_stw_ltw": "Read of STW [esi+7], LTW [esi+8] in numeric reinforcement.",
    "strength_reaches_zero_cleanup": "After decrement to zero, clears susceptibility, STW, LTW, and owner neuron state/output; subsequent ticks are separate.",
    "post_wta_type1_caller": "Later migration invoker checks recipient output; this is not a proof of global scheduler or actual mutation at a particular tick.",
}


def pe_text(data: bytes) -> tuple[int, bytes]:
    """Only static parse of image base and .text bounds from a PE32 image."""
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ValueError("missing DOS header")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if pe + 24 > len(data) or data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("missing PE signature")
    count = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    if opt + opt_size > len(data) or struct.unpack_from("<H", data, opt)[0] != 0x10B:
        raise ValueError("not PE32 optional header")
    base = struct.unpack_from("<I", data, opt + 28)[0]
    start = opt + opt_size
    for i in range(count):
        at = start + 40 * i
        if at + 40 > len(data):
            raise ValueError("section table exceeds file")
        if data[at:at + 8].split(b"\0", 1)[0] != b".text":
            continue
        virtual_size, rva, raw_size, raw_ptr = struct.unpack_from("<IIII", data, at + 8)
        if raw_ptr + raw_size > len(data) or virtual_size < 1:
            raise ValueError("invalid .text bounds")
        return base + rva, data[raw_ptr:raw_ptr + raw_size]
    raise ValueError(".text section not found")


def inspect(physical: bytes, *, identity_required: bool = True) -> dict:
    """Fail closed for wrong version, missing anchor or altered basic block."""
    if not isinstance(physical, bytes):
        raise TypeError("raw PE bytes required")
    checksum = hashlib.sha256(physical).hexdigest()
    if identity_required and (len(physical) != SOURCE_SIZE or checksum != SOURCE_SHA256):
        raise ValueError("not authenticated exact user-provided C1 PE32 build")
    text_va, section = pe_text(physical)
    proof = []
    for label, va, fingerprint in ANCHORS:
        expected = bytes.fromhex(fingerprint)
        offset = va - text_va
        if not 0 <= offset <= len(section) - len(expected):
            raise ValueError(f"{label}: outside .text")
        observed = section[offset:offset + len(expected)]
        if observed != expected:
            raise ValueError(f"{label}: x86 anchor bytes mismatch")
        proof.append({
            "label": label,
            "virtual_address": hex(va),
            "anchor_length": len(expected),
            "anchor_sha256": hashlib.sha256(expected).hexdigest(),
            "manual_interpretation": INTERPRETATION[label],
        })
    return {
        "protocol": "NL-EXP-I3c5b-H-v1",
        "source": "user-provided Creatures.exe, inspected statically; never redistributed",
        "exe_sha256": checksum,
        "exe_length": len(physical),
        "text_virtual_base": hex(text_va),
        "anchors_valid": len(proof),
        "anchored_blocks": proof,
        "historical_strength0_signal_gate": (
            "In inspected original C1 x86 loop, STW signal contribution has NO "
            "strength guard; a slot with strength=0 and STW>0 would contribute "
            "when source output is nonzero and it remains in the class."
        ),
        "historical_strength0_numeric_flow": (
            "Strength=0 increments exhausted counter but falls through into "
            "susceptibility and numeric update; strength-at-zero alone does not "
            "skip these operations in this loop."
        ),
        "historical_loss_reset": (
            "When strength decrements to zero, susceptibility/STW/LTW are "
            "cleared immediately. Later plasticity can require regenerated "
            "susceptibility/chemical input, and migration may replace the link."
        ),
        "limit": (
            "Static opcode and local control-flow evidence for one EXE only. "
            "No dynamic C1 replay, full-game timing or proof of sustained memory."
        ),
        "G_I3c5b_H_local_control_flow": "VERIFIED_STATIC",
        "G05_G09_G00H": "OPEN — autonomous learning/full historical model not proven",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = inspect(args.exe.read_bytes())
    blob = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(blob, encoding="utf-8")
    print(blob, end="")


if __name__ == "__main__":
    main()
