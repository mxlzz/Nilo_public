"""E09h.1: auditoría estática PE32 x86 del C1 original, sin redistribuir binarios.

Se requieren archivos del usuario por CLI. Un CI verde sin originales verifica
solo la herramienta y sus fixtures; NO reanaliza el ejecutable propietario.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

EXE_SHA256 = "548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7"
GEN_SHA256 = "e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4"

# Fragmentos pequeños y localizables, NO una copia del binario.
SIGNATURES = {
    0x403BBD: "bd05000000",       # cinco lóbulos iniciales
    0x403BC2: "8dbed0000000",     # brain+0xd0
    0x403BD1: "81c7c8000000",     # incremento por lóbulo de 0xc8
    0x403C84: "8d4e08",           # brain+8
    0x403C9B: "8daeb8040000",     # brain+0x4b8
    0x421E83: "8b878c120000",     # emisor, count+0x128c
    0x421F4B: "88444f08",         # emisor escribe químico
    0x421F77: "8b8788120000",     # receptor, count+0x1288
    0x421F9A: "8a544708",         # receptor lee químico
    0x42200F: "8802",             # receptor escribe locus
    0x422023: "8b8790120000",     # reacción, count+0x1290
    0x4221D0: "bf00010000",       # decay de 256 concentraciones
}

CALL_GROUPS = {
    "world_main": [(0x424884, 0x407540)],
    "regular_creature_tick": [
        (0x407583, 0x403BB0), (0x407595, 0x421E70),
        (0x4075A6, 0x40A4B0),
    ],
    "brain_lobe_pipeline": [
        (0x403BCC, 0x403CD0), (0x403C87, 0x403CD0),
        (0x403CA5, 0x403E00),
    ],
    "chemistry_decay": [(0x4221ED, 0x419E40)],
    "alternate_event_path": [
        (0x405D32, 0x421E70), (0x405DAF, 0x403BB0),
    ],
}


class PE32:
    """Mapear exclusivamente secciones .text del encabezado PE32."""
    def __init__(self, data: bytes):
        if len(data) < 0x100 or data[:2] != b"MZ":
            raise ValueError("missing DOS MZ")
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        if pe + 24 > len(data) or data[pe:pe+4] != b"PE\x00\x00":
            raise ValueError("invalid PE header")
        if struct.unpack_from("<H", data, pe+4)[0] != 0x14C:
            raise ValueError("not i386")
        count = struct.unpack_from("<H", data, pe+6)[0]
        optional = struct.unpack_from("<H", data, pe+20)[0]
        end = pe+24+optional+40*count
        if end > len(data):
            raise ValueError("truncated section table")
        if struct.unpack_from("<H", data, pe+24)[0] != 0x10B:
            raise ValueError("not PE32")
        self.image_base = struct.unpack_from("<I", data, pe+24+28)[0]
        self.data = data
        self.sections = []
        for i in range(count):
            off = pe+24+optional+i*40
            name = data[off:off+8].split(b"\x00")[0].decode("ascii")
            size, rva, raw_size, file_offset = struct.unpack_from("<IIII",data,off+8)
            if file_offset+raw_size > len(data):
                raise ValueError("section exceeds file bounds")
            self.sections.append((name, rva, size, raw_size, file_offset))

    def at(self, va: int, size: int) -> bytes:
        if size <= 0:
            raise ValueError("positive size required")
        rva = va-self.image_base
        for name, start, virtual_size, raw_size, file_start in self.sections:
            if start <= rva and rva+size <= start+raw_size:
                if name != ".text":
                    raise ValueError("address outside .text")
                off = file_start+(rva-start)
                return self.data[off:off+size]
        raise ValueError(f"unmapped code VA {hex(va)}")

    def direct_call(self, va: int) -> int:
        op = self.at(va, 5)
        if op[0] != 0xE8:
            raise ValueError(f"{hex(va)} not an E8 direct call")
        return va+5+struct.unpack("<i",op[1:])[0]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(exe: bytes, genome: bytes) -> dict:
    if sha256(exe) != EXE_SHA256 or sha256(genome) != GEN_SHA256:
        raise ValueError("unverified C1 executable/genome")
    pe = PE32(exe)
    if pe.image_base != 0x400000:
        raise AssertionError("unexpected PE image base")
    for va, hex_data in SIGNATURES.items():
        expected = bytes.fromhex(hex_data)
        if pe.at(va, len(expected)) != expected:
            raise AssertionError(f"signature mismatch at {hex(va)}")
    calls = {}
    for group, entries in CALL_GROUPS.items():
        if any(entries[i][0] >= entries[i+1][0] for i in range(len(entries)-1)):
            raise AssertionError(f"unordered call sites {group}")
        calls[group] = []
        for site, expected in entries:
            actual = pe.direct_call(site)
            if actual != expected:
                raise AssertionError(f"{group}: {hex(site)} target {hex(actual)} expected {hex(expected)}")
            calls[group].append({"site": hex(site), "target": hex(actual)})
    return {
        "protocol": "E09_H_01_ORDEN_CEREBRO_QUIMICA_PRE_REGISTRO-v1",
        "source": {
            "exe_sha256": sha256(exe), "exe_bytes": len(exe),
            "genome_sha256": sha256(genome), "genome_bytes": len(genome),
        },
        "evidence": {
            "instruction_signatures_verified": len(SIGNATURES),
            "direct_calls_verified": sum(len(v) for v in CALL_GROUPS.values()),
            "calls": calls,
            "chemical_stage_boundaries": [
                {"name": "emitter_loop", "first_va": "0x421e83"},
                {"name": "receptor_loop", "first_va": "0x421f77"},
                {"name": "reaction_loop", "first_va": "0x422023"},
                {"name": "decay_256", "first_va": "0x4221d0"},
            ],
            "lobe_order": "brain indices 1..5, aggregate into lobe0, update 0, then indices 6..num_lobes-1",
            "regular_tick_order": "brain, chemistry, behavior selection; branch-conditioned",
            "alternate_path": "other call path performs chemistry before brain",
        },
        "limits": "Static code order only; no dynamic scheduling frequency, concentration traces or whole-Norn fidelity",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--genome", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.exe.read_bytes(), args.genome.read_bytes())
    output = json.dumps(result, indent=2, sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
