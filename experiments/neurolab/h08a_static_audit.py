"""NeuroLab H-08a: bounded static x86 direct-call audit. Never executes the PE.
Original input is required explicitly and is never embedded in output.
Preregister: docs/neurolab/H08A_PREREGISTRO_RUTAS_EJECUTABLE_20261122.md
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

EXE_SHA = "548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7"
GEN_SHA = "e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4"
TARGETS = {0x403BB0: "brain", 0x421E70: "chemistry", 0x4247B0: "world_tick"}
EXPECTED_CALLS = {
    0x403BB0: (0x405DAF, 0x407583),
    0x421E70: (0x405D32, 0x407595, 0x40B089),
    0x4247B0: (0x418966, 0x424C98, 0x426894),
}
# A few short signatures relevant to the newly noticed third call and causal ordering.
SIGNATURES = {
    0x40B07C: "8b8e202c0000",  # get creature count
    0x40B082: "51",            # pass count
    0x40B083: "8b8e1c2c0000",  # get chemistry object
    0x40B089: "e8e26d0100",    # chemistry tick
    0x40B08E: "8bce",          # get creature object
    0x40B090: "e8abf5ffff",    # following action
    0x40B095: "c786bc2c000001000000", # set creature flag
    0x407543: "8b86bc2c0000",  # check same flag at regular tick
    0x40754B: "7564",          # skip regular if set
    0x407583: "e828c6ffff",    # regular brain
    0x407595: "e8d6a80100",    # regular chemistry
    0x405D32: "e839c10100",    # alternative chemistry
    0x405DAF: "e8fcddffff",    # alternative brain
    0x424884: "e8b72cfeff",    # regular from world
    0x4248C3: "e8f82cfeff",    # alternate from world
}
CALL_RE = re.compile(r"^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+){4}[0-9a-f]{2})\s+call\s+0x([0-9a-f]+)\b", re.I)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PE:
    def __init__(self, blob: bytes):
        if len(blob) < 256 or blob[:2] != b"MZ":
            raise ValueError("invalid DOS header")
        pe = struct.unpack_from("<I", blob, 0x3C)[0]
        if pe + 24 > len(blob) or blob[pe:pe+4] != b"PE\0\0":
            raise ValueError("invalid PE header")
        if struct.unpack_from("<H", blob, pe + 4)[0] != 0x14C:
            raise ValueError("not x86")
        n = struct.unpack_from("<H", blob, pe+6)[0]
        optsize = struct.unpack_from("<H", blob, pe+20)[0]
        if struct.unpack_from("<H", blob, pe+24)[0] != 0x10B:
            raise ValueError("not PE32")
        self.imagebase = struct.unpack_from("<I", blob, pe+24+28)[0]
        self.sections = {}
        if pe + 24 + optsize + n*40 > len(blob):
            raise ValueError("truncated section table")
        for i in range(n):
            off = pe+24+optsize+40*i
            name = blob[off:off+8].split(b"\0")[0].decode("ascii")
            vsize, rva, rawsize, rawptr = struct.unpack_from("<IIII",blob,off+8)
            if rawptr + rawsize > len(blob):
                raise ValueError("truncated section")
            self.sections[name] = (self.imagebase+rva, rawptr, rawsize)
        if ".text" not in self.sections:
            raise ValueError("missing code section")
        self.blob = blob

    def at(self, va: int, n: int) -> bytes:
        base, raw, size = self.sections[".text"]
        if not (0 <= va-base and va-base+n <= size):
            raise ValueError("VA outside .text")
        return self.blob[raw + va-base:raw + va-base+n]

    def direct_call(self, va: int) -> int:
        b = self.at(va,5)
        if b[0] != 0xE8:
            raise ValueError(f"no E8 call at {va:#x}")
        return va + 5 + struct.unpack("<i",b[1:])[0]


def parse_disassembly(s: str) -> dict[int, list[int]]:
    found = {t: [] for t in TARGETS}
    for line in s.splitlines():
        m = CALL_RE.match(line)
        if not m:
            continue
        site, raw, dest = int(m[1],16), bytes.fromhex(m[2]), int(m[3],16)
        if dest in TARGETS:
            if raw[0] != 0xE8 or site+5+struct.unpack("<i",raw[1:])[0] != dest:
                raise AssertionError(f"inconsistent objdump E8 at {site:#x}")
            found[dest].append(site)
    return found


def literal_pointer_offsets(blob: bytes, address: int) -> list[int]:
    out=[]
    needle=struct.pack("<I",address)
    idx=0
    while True:
        idx=blob.find(needle,idx)
        if idx<0:return out
        out.append(idx)
        idx+=1


def audit(exe: bytes, gen: bytes, disassembly: str) -> dict:
    if sha256(exe) != EXE_SHA or sha256(gen) != GEN_SHA:
        raise ValueError("input hashes not equal to verified originals")
    pe=PE(exe)
    if pe.imagebase != 0x400000:
        raise AssertionError("unexpected image base")
    for site, expected in SIGNATURES.items():
        if pe.at(site,len(bytes.fromhex(expected))) != bytes.fromhex(expected):
            raise AssertionError(f"signature mismatch at {site:#x}")
    calls=parse_disassembly(disassembly)
    if any(tuple(calls[target]) != EXPECTED_CALLS[target] for target in TARGETS):
        raise AssertionError(f"direct-call inventory inconsistent: {calls}")
    for target, sites in calls.items():
        for site in sites:
            if pe.direct_call(site) != target:
                raise AssertionError(f"bad target at {site:#x}")
    ctor_start, ctor_end = 0x40ADF0, 0x40B0C7
    assert any(ctor_start <= s < ctor_end for s in calls[0x421E70])
    assert not any(ctor_start <= s < ctor_end for s in calls[0x403BB0])
    return {
        "protocol":"H08a-original-exe-static-routes-v1",
        "source":{"exe_sha256": sha256(exe), "exe_size":len(exe),
                  "gen_sha256":sha256(gen),"gen_size":len(gen)},
        "signature_count":len(SIGNATURES),
        "direct_calls": {TARGETS[target]: [{"site":hex(site),"target":hex(target),
                        "machine_code":pe.at(site,5).hex()} for site in sites]
                        for target,sites in calls.items()},
        "literal_32bit_function_address_file_offsets":
            {TARGETS[a]:[hex(x) for x in literal_pointer_offsets(exe,a)] for a in TARGETS},
        "constructor_like_path":{
            "range_approx": [hex(ctor_start),hex(ctor_end)],
            "chemical_tick_call":"0x40b089",
            "counter_loaded_from_creature_at":"0x40b07c: +0x2c20",
            "chemistry_object_loaded_at":"0x40b083: +0x2c1c",
            "followed_by":"0x40b090: call 0x40a640",
            "state_flag_write":"0x40b095: [creature+0x2cbc]=1",
            "regular_tick_flag_check":"0x407543: [creature+0x2cbc], conditional skip",
            "direct_brain_tick_in_approx_range":False,
            "interpretation":"setup-like function with chemical tick; purpose of state flag inferred, not validated dynamically"},
        "order_checks":{
            "normal":"0x407583 brain before 0x407595 chemistry",
            "alternate":"0x405d32 chemistry before 0x405daf brain",
            "world":"0x424884 regular pass before 0x4248c3 alternate pass"},
        "limitations":"objdump-aligned direct E8 calls only; not exhaustive for virtual, indirect, alternate decoding, runtime callbacks, observed timing or synaptic causal attribution"
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",type=Path,required=True)
    p.add_argument("--genome",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    dis=subprocess.run(["objdump","-d","-M","intel",str(a.exe)],
                       capture_output=True,text=True,check=True).stdout
    result=audit(a.exe.read_bytes(),a.genome.read_bytes(),dis)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"protocol":result["protocol"],"signatures":result["signature_count"],
                      "direct_calls":result["direct_calls"],"third_chemistry":result["constructor_like_path"]},
                      indent=2,sort_keys=True))


if __name__ == "__main__":
    main()
