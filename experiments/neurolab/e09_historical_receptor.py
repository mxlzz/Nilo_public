"""E09h.3: isolated C1 chemical receptor transfer from x86 0x421f8d..0x422011.

Does not emulate emitter/reaction/brain wiring. GEN original not distributed.
The receptor returns a locus BYTE, not a chemical pool mutation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
from pathlib import Path

from .c1_genome_inspector import markers

ORIGINAL_SHA256 = "e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4"


@dataclass(frozen=True)
class Receptor:
    gene_index: int
    organ: int
    lobe: int
    locus: int
    chemical: int
    threshold: int
    nominal: int
    gain: int
    flags: int

    def __post_init__(self):
        for field in ("organ", "lobe", "locus", "chemical",
                      "threshold", "nominal", "gain", "flags"):
            v = getattr(self, field)
            if type(v) is not int or not 0 <= v <= 255:
                raise ValueError(f"{field} must be a byte")


def parse_receptors(genome: bytes) -> tuple[Receptor, ...]:
    if not isinstance(genome, bytes):
        raise TypeError("genome must be bytes")
    offsets = markers(genome)
    result = []
    for index, pos in enumerate(offsets):
        if genome[pos+4:pos+6] != bytes((1,0)):
            continue
        stop = offsets[index+1] if index+1 < len(offsets) else genome.find(b"gend",pos+10)
        if stop < 0 or stop-pos != 18:
            raise ValueError(f"invalid C1 receptor gene at {index}")
        raw = genome[pos+10:stop]
        result.append(Receptor(index,*raw))
    return tuple(result)


def receptor_value(rec: Receptor, pool: tuple[int, ...]) -> int | None:
    """Calculate a single brain/body locus value from the current chemical pool.

    No emulated internal pointer linking, enzyme reaction, or mutation.
    """
    if not isinstance(rec, Receptor):
        raise TypeError("C1 Receptor required")
    if not isinstance(pool, tuple) or len(pool) != 256 or any(
        type(x) is not int or not 0 <= x <= 255 for x in pool
    ):
        raise ValueError("256 byte concentrations required")
    if rec.chemical == 0:
        return None  # no receptor chemical ID: original loop skips
    available = max(0, pool[rec.chemical] - rec.threshold)
    if not available:
        effect = 0
    elif rec.flags & 2:
        effect = rec.gain
    else:
        effect = (available * rec.gain) >> 8
    return (max(0, rec.nominal-effect) if rec.flags & 1 else
            min(255, rec.nominal+effect))


def original_fixtures(genome: bytes) -> dict:
    if hashlib.sha256(genome).hexdigest() != ORIGINAL_SHA256:
        raise ValueError("genome is not verified C1 CD dad1.gen")
    records = parse_receptors(genome)
    if len(records) != 43:
        raise AssertionError("receptor count changed")
    selected = {r.gene_index:r for r in records}
    candidates = [88,89,126,127,128,129]
    if any(i not in selected for i in candidates):
        raise AssertionError("missing brain receptor")
    pool = [0]*256
    pool[49] = pool[50] = pool[53] = 12
    pool[52] = 5
    return {
        "protocol": "E09_H_03_RECEPTORES_QUIMICOS_PRE_REGISTRO-v1",
        "genome_sha256": ORIGINAL_SHA256,
        "receptor_count": len(records),
        "brain_receptors": [asdict(selected[i]) for i in candidates],
        "example_pool": {"49":12,"50":12,"53":12,"52":5},
        "locus_values": {str(i):receptor_value(selected[i],tuple(pool)) for i in candidates},
        "limitations": "isolated transfer; no original linked locus pointer or full C1 tick",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--genome",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=original_fixtures(args.genome.read_bytes())
    content=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(content,encoding="utf-8")
    print(content,end="")


if __name__ == "__main__":
    main()
