"""Inspección C1 de los genes de lóbulos, sin ejecutar ni distribuir el juego.

Uso local (Python 3.10+, sin dependencias):
    python -m experiments.neurolab.c1_genome_inspector ruta/dad1.gen
    python -m experiments.neurolab.c1_genome_inspector original/dad1.gen --compare parche/dad1.gen

SOLO identifica genes de lóbulos C1 (0/0), con 122 bytes y estructuras
validadas en la muestra aportada. No decodifica todo el genoma ni el motor.
Referencia: docs/neurolab/E00_GENOMA_ORIGINAL_COMPARACION.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

NAMES = ("Perception", "Drive", "Source", "Verb", "Noun",
         "General Sense", "Decision", "Attention", "Concept")
OPCODES = (
    "END", "CONST0", "CONST1", "CONST64", "CONST255",
    "CHEM0", "CHEM1", "CHEM2", "CHEM3", "STATE", "OUTPUT",
    "THRESHOLD", "TYPE0", "TYPE1", "ANDTYPE0", "ANDTYPE1",
    "INPUT", "CONDUCT", "SUSCEPT", "STW", "LTW", "STRENGTH",
    "TRUE", "PLUS", "MINUS", "TIMES", "INCR", "DECR",
)


def markers(genome: bytes) -> list[int]:
    """En C1 observado la secuencia ASCII gene delimita cada registro."""
    offsets: list[int] = []
    pos = 0
    while (pos := genome.find(b"gene", pos)) >= 0:
        offsets.append(pos)
        pos += 4
    return offsets


def decode_rule(raw: bytes) -> list[str]:
    if len(raw) != 8:
        raise ValueError("SVRule C1 tiene 8 bytes")
    output = []
    for op in raw:
        if op == 0:
            break
        output.append(OPCODES[op] if op < len(OPCODES) else f"UNKNOWN_{op}")
    return output


def decode_dendrite(raw: bytes) -> dict:
    if len(raw) != 47:
        raise ValueError("Definición de clase dendrítica C1 debe ocupar 47 bytes")
    return {
        "source_lobe": raw[0],
        "min_count": raw[1],
        "max_count": raw[2],
        "spread": raw[3],
        "fan_width": raw[4],
        "initial_ltw": list(raw[5:7]),
        "initial_strength": list(raw[7:9]),
        "migration_type": raw[9],
        "susceptibility_decay": raw[10],
        "stw_decay": raw[11],
        "ltw_rate": raw[12],
        "gain_strength_rate": raw[13],
        "gain_strength_rule": decode_rule(raw[14:22]),
        "lose_strength_rate": raw[22],
        "lose_strength_rule": decode_rule(raw[23:31]),
        "susceptibility_rule": decode_rule(raw[31:39]),
        "reinforcement_rule": decode_rule(raw[39:47]),
    }


def decode_lobe_record(record: bytes, lobe_id: int, offset: int) -> dict:
    if not (len(record) == 122 and record[:6] == b"gene" + bytes((0, 0))):
        raise ValueError("El registro no es un lóbulo C1 de 122 bytes")
    body = record[10:]
    x, y, width, height = body[:4]
    if not (width and height and x + width <= 64 and y + height <= 48):
        raise ValueError("Coordenadas de lóbulo inválidas para grilla C1")
    return {
        "lobe_id": lobe_id,
        "name": NAMES[lobe_id] if 0 <= lobe_id < len(NAMES) else f"LOBE_{lobe_id}",
        "offset": offset,
        "gene_sequence": record[6],
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "neurons_nominal": width * height,
        "perceptible_flag": body[4],
        "threshold": body[5],
        "decay_rate": body[6],
        "rest_state": body[7],
        "attenuation": body[8],
        "state_rule": decode_rule(body[9:17]),
        "neuron_flags": body[17],
        "dendrites": [
            decode_dendrite(body[18:65]),
            decode_dendrite(body[65:112]),
        ],
    }


def inspect(data: bytes) -> dict:
    offs = markers(data)
    candidates = []
    for i, offset in enumerate(offs):
        if data[offset+4:offset+6] != b"\x00\x00":
            continue
        end = offs[i+1] if i+1 < len(offs) else len(data)
        candidates.append(decode_lobe_record(data[offset:end], len(candidates), offset))
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "file_bytes": len(data),
        "marker_gene_count": len(offs),
        "lobe_count": len(candidates),
        "neurons_nominal": sum(r["neurons_nominal"] for r in candidates),
        "lobes": candidates,
    }


def compare(a: bytes, b: bytes) -> dict:
    ai, bi = inspect(a), inspect(b)
    differences = [p for p in range(min(len(a), len(b))) if a[p] != b[p]]
    ao, bo = markers(a), markers(b)
    return {
        "original": {"sha256": ai["sha256"], "bytes": len(a)},
        "other": {"sha256": bi["sha256"], "bytes": len(b)},
        "gene_marker_positions_identical": ao == bo,
        "different_offsets_shared_length": differences,
        "lobes_bytes_identical": (
            len(ai["lobes"]) == len(bi["lobes"])
            and all(
                a[r["offset"]:r["offset"]+122] == b[s["offset"]:s["offset"]+122]
                for r, s in zip(ai["lobes"], bi["lobes"])
            )
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspeccionar lóbulos cerebrales de GEN de Creatures 1")
    ap.add_argument("genome", type=Path)
    ap.add_argument("--compare", type=Path, default=None)
    args = ap.parse_args()
    data = args.genome.read_bytes()
    output = inspect(data)
    if args.compare:
        output["comparison"] = compare(data, args.compare.read_bytes())
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
