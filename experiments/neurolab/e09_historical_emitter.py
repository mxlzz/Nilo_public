"""E09h.5: isolated C1 chemical emitter tick inferred from original x86.

Not a complete brain or scheduler. No copyrighted game files distributed.
The verified x86 path at 0x421E83..0x421F5B samples an emitter's bound
locus, applies sample gating and threshold, adds to a byte chemical pool
and optionally clears the source locus. Not equivalent to a live Norn.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Emitter:
    gene_index: int
    organ: int
    lobe: int
    locus: int
    chemical: int
    threshold: int
    sample_rate: int
    gain: int
    flags: int

    def __post_init__(self) -> None:
        if type(self.gene_index) is not int or self.gene_index < 0:
            raise ValueError("gene_index must be nonnegative int")
        for attr in ("organ", "lobe", "locus", "chemical",
                     "threshold", "sample_rate", "gain", "flags"):
            n = getattr(self, attr)
            if type(n) is not int or not 0 <= n <= 255:
                raise ValueError(f"{attr} must be a byte")
        if self.sample_rate == 0:
            raise ValueError("zero sample_rate would divide by zero in C1")


@dataclass(frozen=True)
class EmitterResult:
    pool: tuple[int, ...]
    source: int
    eligible: bool
    calculated_amount: int
    added_to_pool: int


def emitter_tick(
    gene: Emitter,
    pool: tuple[int, ...],
    source: int,
    tick: int,
) -> EmitterResult:
    """One emitter, WITHOUT writing the caller's pool or neuron in place.

    Chemical zero still clears the source when eligible and flags&1:
    0x421EEF/0x421F24 jump to reset at 0x421F4F. This differs from the
    initial E09h.5 preregistered hypothesis and is preserved as errata.
    """
    if not isinstance(gene, Emitter):
        raise TypeError("Emitter gene required")
    if (not isinstance(pool, tuple) or len(pool) != 256 or any(
            type(x) is not int or not 0 <= x <= 255 for x in pool)):
        raise ValueError("pool must be tuple of 256 byte concentrations")
    if type(source) is not int or not 0 <= source <= 255:
        raise ValueError("source byte required")
    if type(tick) is not int or not 0 <= tick <= 0xFFFFFFFF:
        raise ValueError("unsigned C1 tick required")

    observed = 255 - source if gene.flags & 4 else source
    if (observed == 0 or tick % gene.sample_rate != 0
            or observed <= gene.threshold):
        return EmitterResult(pool, source, False, 0, 0)

    available = observed - gene.threshold
    amount = gene.gain if gene.flags & 2 else (available * gene.gain) >> 8
    after = list(pool)
    added = 0
    if gene.chemical != 0:
        old = after[gene.chemical]
        after[gene.chemical] = min(255, old + amount)
        added = after[gene.chemical] - old
    new_source = 0 if gene.flags & 1 else source
    return EmitterResult(tuple(after), new_source, True, amount, added)
