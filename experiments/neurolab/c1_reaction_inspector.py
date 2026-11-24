"""Read-only C1 reaction gene inspector. No original game binaries included.

Only reaction type/subtype 1/2 with nine payload bytes are decoded.
Fields: A quantity/chem, B quantity/chem, C quantity/chem,
D quantity/chem, rate. Does NOT simulate chemical kinetics.
Usage: python -m experiments.neurolab.c1_reaction_inspector path/to/dad1.gen
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import json
import sys

from .c1_genome_inspector import markers


@dataclass(frozen=True)
class Reaction:
    gene_index: int
    offset: int
    coefficient_a: int
    chemical_a: int
    coefficient_b: int
    chemical_b: int
    coefficient_c: int
    chemical_c: int
    coefficient_d: int
    chemical_d: int
    rate: int

    @property
    def source_ids(self):
        return tuple(x for x, n in ((self.chemical_a,self.coefficient_a),
                                    (self.chemical_b,self.coefficient_b))
                     if n != 0 and x != 0)

    @property
    def target_ids(self):
        return tuple(x for x, n in ((self.chemical_c,self.coefficient_c),
                                    (self.chemical_d,self.coefficient_d))
                     if n != 0 and x != 0)


def parse_reactions(data: bytes) -> tuple[Reaction,...]:
    """Return parsed reaction genes; reject ambiguous/truncated records."""
    if not isinstance(data, bytes):
        raise TypeError("C1 genome must be bytes")
    positions=markers(data)
    result=[]
    for idx, start in enumerate(positions):
        if data[start+4:start+6] != bytes((1,2)):
            continue
        if idx + 1 < len(positions):
            end=positions[idx+1]
        else:
            end=data.find(b"gend", start+10)
            if end<0:
                raise ValueError("último gen sin terminador")
        record=data[start:end]
        if len(record)!=19:
            raise ValueError(f"gen de reacción #{idx}: longitud incorrecta {len(record)}")
        payload=record[10:]
        result.append(Reaction(idx,start,*payload))
    return tuple(result)


def summary(data: bytes) -> dict:
    reactions=parse_reactions(data)
    relevant=tuple(r for r in reactions if set(r.source_ids+r.target_ids)
                   & {49,50,51,52,53,70})
    return {
        "source_sha256":sha256(data).hexdigest(),
        "source_bytes":len(data),
        "reaction_gene_count":len(reactions),
        "learning_reaction_count":len(relevant),
        "learning_reactions":[asdict(r) for r in relevant],
    }


def main() -> None:
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python -m experiments.neurolab.c1_reaction_inspector dad1.gen")
    print(json.dumps(summary(Path(sys.argv[1]).read_bytes()),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
