"""I3c.6a: SHA-pinned read-only original C1 Decision atrophy feedback writer.

PREREG: docs/neurolab/E09_02I_I3C6A_REALIMENTACION_ATROFIA_PRE_REGISTRO.md
Inspect original user-provided PE32 only. This is LOCAL static-flow evidence,
not a C1 game execution or proof of a complete endogenous chemical cycle.

Source byte sections are never redistributed; report only VA/length/SHA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .e09_i3c5b_exe_static_audit import pe_text, SOURCE_SHA256, SOURCE_SIZE

# Fixed windows actually extracted and disassembled from the original PE32.
# Each one contains complete instruction sequences, no generated assumptions.
ANCHORS = (
    ("lobe_counter_reset", 0x403E76,
     "8993b00000008893c20000008893c1000000"),
    ("type1_minimum_sentinel", 0x403E8F,
     "7507c683c1000000ff807b6c017507c683c2000000ff"),
    ("per_neuron_counter_reset", 0x40416A,
     "8b4c243c8b44242c8b54247c895c24308b748104"),
    ("exhausted_dendrite_counter", 0x4041A1,
     "8a460984c0884c2450885c245288542453884424557504ff442430"),
    ("loss_reset_and_counter", 0x4047C6,
     "8b44243cc6450000c6460700c6460800c6400200c6400300ff442430"),
    ("type1_class_gate", 0x404803,
     "807f0c0175228b4c242c8b7424348b44243033d2"),
    ("type1_minimum_writer", 0x404817,
     "8a9431c10000003bc27d43888431c1000000eb3a"),
    ("type2_nonzero_gate", 0x40482B,
     "8b4424308b4c242c85c0742e8b542434"),
    ("type2_saturating_increment", 0x40483B,
     "8a8411c10000003cff7309fec0888411c1000000"),
    ("next_class_iteration", 0x404865,
     "8d410183c73c83f8028944242c0f8cf0f8ffff"),
)
DESCRIPTION = {
    "lobe_counter_reset":
        "Zeroes lobe +C1/+C2 and +B0 before processing; these are not CHEM0/1.",
    "type1_minimum_sentinel":
        "If dendrite migration type is1, initialize respective class-locus byte to FF.",
    "per_neuron_counter_reset":
        "Resets local exhausted-dendrite counter esp+30 before iterating one class of one neuron.",
    "exhausted_dendrite_counter":
        "If strength [esi+9] is zero, increment the local count; nonzero path skips increment.",
    "loss_reset_and_counter":
        "After a transition to strength0, clears susceptibility/STW/LTW and increments local count.",
    "type1_class_gate":
        "Tests migration type1 at [edi+0C], loads class pointer and local exhausted count.",
    "type1_minimum_writer":
        "Reads lobe+0xC1+class; if local count < stored byte, writes low byte of count. "
        "This is a MINIMUM over visited neuron/class counters, not their sum.",
    "type2_nonzero_gate":
        "For non-Type1 class, tests count>0 before any locus write.",
    "type2_saturating_increment":
        "For non-Type1 class with any exhausted dendrite, increments lobe+0xC1+class "
        "once (unless already FF); NOT the number of exhausted dendrites.",
    "next_class_iteration":
        "Advance class index then jump back to class-processing block until two classes visited.",
}


def inspect(original: bytes, *, require_provenance: bool = True) -> dict:
    if not isinstance(original, bytes):
        raise TypeError("original PE bytes required")
    digest=hashlib.sha256(original).hexdigest()
    if require_provenance and (
        digest != SOURCE_SHA256 or len(original) != SOURCE_SIZE
    ):
        raise ValueError("different EXE: original C1 SHA and size required")
    base, text=pe_text(original)
    records=[]
    for label, va, original_hex in ANCHORS:
        expected=bytes.fromhex(original_hex)
        offset=va-base
        if not 0<=offset<=len(text)-len(expected):
            raise ValueError(f"{label}: outside .text section")
        if text[offset:offset+len(expected)] != expected:
            raise ValueError(f"{label}: original x86 bytes mismatch")
        records.append({
            "name":label,
            "va":hex(va),
            "n_bytes":len(expected),
            "sha256":hashlib.sha256(expected).hexdigest(),
            "interpretation":DESCRIPTION[label],
        })
    if len(records)!=10:
        raise AssertionError("partial x86 feedback writer evidence")
    return {
        "protocol":"NL-EXP-I3c6a-v1",
        "sha256":digest,
        "file_length":len(original),
        "text_base_va":hex(base),
        "anchor_count":len(records),
        "records":records,
        "type1_locus_rule":
            "Starts FF per lobe/class and updates to MIN(local loose count) "
            "across visited neuron/class records. If any visited count=0, "
            "locus0 can suppress subsequent emitter sampling.",
        "type2_locus_rule":
            "Increments one (up to FF) for each visited neuron/class that "
            "has at least one loose dendrite; not raw dendrite count.",
        "local_counter_sources":
            "Both previously strength0 contacts and strength newly lost "
            "during the tick contribute to local esp+30.",
        "emitter_path":
            "Previously verified E09h5: source lobe+0xC1/+0xC2 -> "
            "emitter genes124/125 chemicals53/70 -> E09h4 "
            "inverted Decision receptors127/128 CHEM2/CHEM3.",
        "provenance_status":
            "ORIGINAL_EXE_VERIFIED_STATIC" if require_provenance
            else "SYNTHETIC_FIXTURE_ONLY",
        "historical_limits":
            "Only locally decoded branch for this PE32 SHA. Does not prove "
            "all scheduler paths, actual active neurons, emitter amounts or "
            "autonomous C1 behavioral effects.",
        "G05_G09_G00H":"OPEN",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--exe",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=inspect(args.exe.read_bytes())
    blob=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(blob,encoding="utf-8")
    print(blob,end="")


if __name__=="__main__":
    main()
