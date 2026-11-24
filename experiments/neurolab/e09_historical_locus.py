"""E09h.4: conditional, isolated C1 receptor locus -> lobe CHEM0..3 adapter.

The *documented* C1 receiver locus map 13..16 -> CHEM0..3 is checked
against independent historical guides. This code DOES NOT establish the
EXE's actual pointer linking, update order, or brain snapshot semantics.
Do not integrate into an autonomous brain before G-H4-X86 closes.

Source documentation:
https://lisdude.com/cdn/76.html (LCUS receptor-locus table)
https://zenzoa.com/creatures/c1-brains.html (CHEM opcodes and table)
"""
from __future__ import annotations

from collections.abc import Iterable

from .e09_historical_receptor import Receptor, receptor_value


def route_brain_chem_loci(
    receptors: Iterable[Receptor],
    pool: tuple[int, ...],
    lobe: int,
    initial: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    """Route receptors to one lobe's four CHEM values under documented map.

    Missing genes preserve supplied values; this does not assert the game's
    initialization policy. Duplicate bindings are rejected rather than
    guessing the original conflict precedence.
    """
    if type(lobe) is not int or not 0 <= lobe <= 255:
        raise ValueError("lobe must be byte")
    if (not isinstance(initial, tuple) or len(initial) != 4
            or any(type(x) is not int or not 0 <= x <= 255 for x in initial)):
        raise ValueError("initial must have four byte values")
    if (not isinstance(pool, tuple) or len(pool) != 256
            or any(type(x) is not int or not 0 <= x <= 255 for x in pool)):
        raise ValueError("pool must have 256 byte concentrations")

    chem = list(initial)
    seen: set[int] = set()
    for receptor in receptors:
        if not isinstance(receptor, Receptor):
            raise TypeError("Receptor required")
        if receptor.organ != 0 or receptor.lobe != lobe:
            continue
        if not 13 <= receptor.locus <= 16 or receptor.chemical == 0:
            continue
        channel = receptor.locus - 13
        if channel in seen:
            raise ValueError("duplicate receptor CHEM binding: precedence unknown")
        seen.add(channel)
        output = receptor_value(receptor, pool)
        assert output is not None  # chemical zero explicitly skipped
        chem[channel] = output
    return tuple(chem)  # type: ignore[return-value]



def initialize_brain_chem_loci(
    receptors: Iterable[Receptor],
    lobe: int,
    initial: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> tuple[int, int, int, int]:
    """Isolated gene-loading nominal write, now observed at C1 x86 0x421acf.

    With a successfully bound brain locus pointer, the C1 receptor loader
    copies nominal at gene offset +5 into that locus before chemical ticks.
    Existing NeuroLab duplicate policy is intentionally conservative and
    rejects clashes (the original loader appears to reuse a record and
    overwrite on later genes). Does not simulate all genome loading.
    """
    if type(lobe) is not int or not 0 <= lobe <= 255:
        raise ValueError("lobe must be byte")
    if (not isinstance(initial, tuple) or len(initial) != 4
            or any(type(x) is not int or not 0 <= x <= 255 for x in initial)):
        raise ValueError("initial must have four byte values")
    result = list(initial)
    seen: set[int] = set()
    for receptor in receptors:
        if not isinstance(receptor, Receptor):
            raise TypeError("Receptor required")
        if receptor.organ != 0 or receptor.lobe != lobe:
            continue
        if not 13 <= receptor.locus <= 16:
            continue
        channel = receptor.locus - 13
        if channel in seen:
            raise ValueError("duplicate nominal CHEM binding")
        seen.add(channel)
        result[channel] = receptor.nominal
    return tuple(result)  # type: ignore[return-value]
