"""E09h.4: static C1 receptor pointer -> lobe CHEM -> SVRule audit.

This tool never executes the game. A CI test using synthetic memory verifies
the *auditor*, not the original executable. Authentic evidence requires a
hash-verified user-owned Creatures.exe supplied by --exe, never committed.

The specific 1997 PE32 build was studied; do not extrapolate offsets to other
editions or claim that a live game trace was observed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from .e09_historical_timing_audit import PE32, EXE_SHA256

# Tiny opcode signatures located independently by objdump -D -M intel.
SIGNATURES = {
    0x401788: "c746042c304300",          # CBrain+4 vtable=0x43302c
    0x40AF89: "8986182c0000",            # Norn+0x2c18 <- brain*
    0x421A09: "8b89182c0000",            # lookup brain* from Norn
    0x421A0F: "83c104",                  # brain+4 (locus API subobject)
    0x421A12: "8b01",                    # subobject vptr
    0x421A14: "52536a00ff10",            # push locus,lobe,0; virtual call
    0x4030E0: "8b442408",                # brain locus resolver
    0x4030EA: "f7b9840c0000",            # modulo brain number of lobes
    0x4030FD: "8d0480",                  # lobe * 5
    0x403100: "8d0480",                  # lobe * 25
    0x403103: "8d44c104",                # base=brain+4+200*lobe+4
    0x403107: "8b4c2404",                # selects locus kind
    0x403128: "8a914c324000",            # locus jump index
    0x40312E: "ff249500324000",          # jump table
    0x421A6F: "894708",                  # resolved locus pointer stored
    0x421AC6: "8b5708",                  # fetch bound pointer
    0x421ACC: "8a4705",                  # genetic nominal
    0x421ACF: "8802",                    # initialize locus to nominal
    0x421F87: "8d8f0b020000",            # receptor record offset +3
    0x42200C: "8b5105",                  # read receptor bound pointer (+8)
    0x42200F: "8802",                    # write computed receptor value
    0x403E2C: "8a8bc4000000",            # lobe CHEM1
    0x403E38: "8a83c3000000",            # lobe CHEM0
    0x403E42: "8a8bc6000000",            # lobe CHEM3
    0x403E4C: "8a83c5000000",            # lobe CHEM2
    0x403E3E: "884c2446",                # stack byte 0x46: opcode6
    0x403E48: "88442445",                # stack byte 0x45: opcode5
    0x403E52: "884c2448",                # stack byte 0x48: opcode8
    0x403E59: "88442447",                # stack byte 0x47: opcode7
    0x403FC2: "80fa16",                  # SVRule load opcode < 22
    0x403FD1: "8a441440",                # stack[0x40+opcode]
}

LOCUS_JUMPS = {
    13: (0x403183, 0xC3),
    14: (0x40318B, 0xC4),
    15: (0x403193, 0xC5),
    16: (0x40319B, 0xC6),
}


def verify_link(read_text, read_rdata) -> dict:
    """Verify actual bytes or synthetic memory (caller identifies source)."""
    for va, raw in SIGNATURES.items():
        expected = bytes.fromhex(raw)
        if read_text(va, len(expected)) != expected:
            raise AssertionError(f"instruction mismatch at {va:#x}")
    vtable_method = struct.unpack("<I", read_rdata(0x43302C, 4))[0]
    if vtable_method != 0x4030E0:
        raise AssertionError("brain+4 vtable does not dispatch to locus resolver")

    bindings = []
    for locus, (expected_target, expected_offset) in LOCUS_JUMPS.items():
        index = read_text(0x40324C + locus, 1)[0]
        target = struct.unpack("<I", read_text(0x403200 + index * 4, 4))[0]
        if target != expected_target:
            raise AssertionError(f"locus {locus}: unexpected dispatch target")
        op = read_text(target, 8)
        if (op[0] != 0x05 or op[5:] != bytes.fromhex("c20c00")
                or struct.unpack("<I", op[1:5])[0] != expected_offset):
            raise AssertionError(f"locus {locus}: unexpected byte offset")
        bindings.append({
            "genetic_receptor_locus": locus,
            "svrule_name": f"CHEM{locus-13}",
            "svrule_opcode": locus - 8,
            "lobe_relative_byte_offset": hex(expected_offset),
            "resolver_case_va": hex(target),
        })
    return {
        "locus_resolver": "0x4030e0",
        "locus_resolver_vtable": "0x43302c",
        "initial_write": "0x421acf",
        "receptor_write": "0x42200f",
        "snapshot_reads": ["0x403e38", "0x403e2c", "0x403e4c", "0x403e42"],
        "snapshot_to_svrule": "0x403fd1",
        "verified_instruction_signatures": len(SIGNATURES),
        "validated_bindings": bindings,
        "loader_duplicate_behavior": (
            "0x421a26..0x421a5d searches by resolved pointer and reuses "
            "the record; later fields are overwritten, unlike the defensive "
            "NeuroLab adapter which rejects duplicates"
        ),
    }


def rdata_at(pe: PE32, va: int, size: int) -> bytes:
    rva = va - pe.image_base
    for name, start, _virtual, raw, file_off in pe.sections:
        if name == ".rdata" and start <= rva and rva + size <= start + raw:
            return pe.data[file_off + rva - start:file_off + rva - start + size]
    raise ValueError(f"unmapped .rdata address {va:#x}")


def audit(exe: bytes) -> dict:
    observed_hash = hashlib.sha256(exe).hexdigest()
    if observed_hash != EXE_SHA256:
        raise ValueError("wrong build or corrupt original C1 EXE")
    pe = PE32(exe)
    if pe.image_base != 0x400000:
        raise AssertionError("unexpected C1 image base")
    verified = verify_link(pe.at, lambda va, n: rdata_at(pe, va, n))
    return {
        "protocol": "E09_H_04_ENLACE_LOCI_PRE_REGISTRO-v1",
        "source": {"exe_sha256": observed_hash, "exe_bytes": len(exe)},
        "static_evidence": verified,
        "status": "G-H4-X86 static linkage verified for this exact EXE build",
        "limitations": ("no runtime trace; alternate scheduling pathways, "
                        "continuous biochemical effects, and complete C1 "
                        "simulation remain unverified"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.exe.read_bytes())
    result_json = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result_json, encoding="utf-8")
    print(result_json, end="")


if __name__ == "__main__":
    main()
