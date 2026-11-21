"""E09h.2: isolated C1 chemical reaction arithmetic from PE x86, no Norn engine.

Source: user-provided Creatures.exe SHA256 548a8388..., reaction loop
0x42203f..0x4221cd and parser/loader 0x421c9c..0x421d52.
Serialized gene order: qtyA,chemA,qtyB,chemB,qtyC,chemC,qtyD,chemD,rate.
Runtime record moves rate to offset +4. No receptor/emitter/whole pool decay.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
from pathlib import Path

from .c1_decay_math import decay
from .c1_reaction_inspector import Reaction, parse_reactions

GEN_SHA256 = "e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4"
POOL_SIZE = 256


@dataclass(frozen=True)
class ReactionEvent:
    gene_index: int
    capacity: int
    residual: int
    reacted_units: int
    reactants: tuple[tuple[int, int], ...]
    products: tuple[tuple[int, int], ...]


def pool_with(**named) -> tuple[int, ...]:
    """Convenience test input; IDs supplied as named string keys."""
    pool = [0] * POOL_SIZE
    for key, value in named.items():
        chemical = int(key.removeprefix("c"))
        if chemical not in range(1, POOL_SIZE) or type(value) is not int or not 0 <= value <= 255:
            raise ValueError("invalid chemical ID or value")
        pool[chemical] = value
    return tuple(pool)


def _validate(pool: tuple[int, ...], tick: int) -> None:
    if not isinstance(pool, tuple) or len(pool) != POOL_SIZE:
        raise ValueError("pool must contain 256 concentrations")
    if any(type(value) is not int or not 0 <= value <= 255 for value in pool):
        raise ValueError("concentrations must be bytes")
    if type(tick) is not int or tick < 0:
        raise ValueError("tick must be a nonnegative integer")


def reaction_step(
    pool: tuple[int, ...], reaction: Reaction, tick: int
) -> tuple[tuple[int, ...], ReactionEvent]:
    """Execute precisely ONE ordered C1 reaction using the existing C1 decay.

    Computes limiting reactant capacity, time-gated decay of capacity,
    saturating subtraction of each reactant, saturating addition of products.
    Returns a new pool. Does not implement emitters/receptors/chemical half-life.
    """
    _validate(pool, tick)
    if not isinstance(reaction, Reaction):
        raise TypeError("Reaction from C1 genome inspector required")
    capacity = 255
    inputs = ((reaction.coefficient_a, reaction.chemical_a),
              (reaction.coefficient_b, reaction.chemical_b))
    outputs = ((reaction.coefficient_c, reaction.chemical_c),
               (reaction.coefficient_d, reaction.chemical_d))
    for count, chemical in inputs:
        if chemical:
            if count <= 0:
                raise ValueError("nonzero reagent ID with zero coefficient")
            capacity = min(capacity, pool[chemical] // count)
    residual = decay(capacity, reaction.rate, tick) if capacity else 0
    reacted = capacity - residual
    next_pool = list(pool)
    for count, chemical in inputs:
        if chemical:
            next_pool[chemical] = max(0, next_pool[chemical] - count * reacted)
    for count, chemical in outputs:
        if chemical:
            next_pool[chemical] = min(255, next_pool[chemical] + count * reacted)
    return tuple(next_pool), ReactionEvent(
        gene_index=reaction.gene_index, capacity=capacity, residual=residual,
        reacted_units=reacted,
        reactants=tuple((chemical, count) for count, chemical in inputs if chemical),
        products=tuple((chemical, count) for count, chemical in outputs if chemical),
    )


def process_reactions(
    pool: tuple[int, ...], reactions: tuple[Reaction, ...], tick: int
) -> tuple[tuple[int, ...], tuple[ReactionEvent, ...]]:
    """Sequentially apply each reaction to the MODIFIED pool of its predecessor."""
    _validate(pool, tick)
    if not isinstance(reactions, tuple):
        raise TypeError("ordered tuple of reactions required")
    events = []
    current = pool
    for reaction in reactions:
        current, event = reaction_step(current, reaction, tick)
        events.append(event)
    return current, tuple(events)


def original_fixtures(genome: bytes) -> dict:
    if hashlib.sha256(genome).hexdigest() != GEN_SHA256:
        raise ValueError("not verified original C1 genome")
    reactions = parse_reactions(genome)
    if len(reactions) != 58:
        raise AssertionError("C1 reaction count unexpectedly changed")
    by_index = {r.gene_index: r for r in reactions}
    samples = {}
    for index in (57, 71, 111, 112):
        samples[str(index)] = asdict(by_index[index])
    one = pool_with(c33=10, c1=15)
    after_a, ea = reaction_step(one, by_index[71], 0)
    after_chain, events = process_reactions(one, (by_index[71], by_index[111]), 0)
    after_reverse, reverse_events = process_reactions(one, (by_index[111], by_index[71]), 0)
    twenty = pool_with(c49=20)
    after_111, e111 = reaction_step(twenty, by_index[111], 0)
    return {
        "protocol": "E09_H_02_REACCIONES_QUIMICAS_PRE_REGISTRO-v1",
        "genome_sha256": GEN_SHA256,
        "reactions": len(reactions),
        "selected_genes": samples,
        "scenario_gene_71": {"extent": ea.reacted_units, "c33": after_a[33],
                             "c1": after_a[1], "c49": after_a[49]},
        "scenario_gene_111": {"extent": e111.reacted_units, "c49": after_111[49],
                              "c51": after_111[51], "c54": after_111[54]},
        "scenario_71_then_111": {"extents": [x.reacted_units for x in events],
                                 "c49": after_chain[49], "c51": after_chain[51],
                                 "c54": after_chain[54]},
        "scenario_111_then_71": {"extents": [x.reacted_units for x in reverse_events],
                                 "c49": after_reverse[49], "c51": after_reverse[51],
                                 "c54": after_reverse[54]},
        "scope": "isolated ordered reaction stage; not whole C1 biochemistry",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--genome",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    args = parser.parse_args()
    doc = original_fixtures(args.genome.read_bytes())
    content = json.dumps(doc,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(content,encoding="utf-8")
    print(content,end="")


if __name__ == "__main__":
    main()
