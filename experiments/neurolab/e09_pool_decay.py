"""E09.02i-I1b: C1 biochemical 256-chemical decay, isolated and optional.

EXE 0x4221cd..0x4221fd loops 256 records with concentration byte
and adjacent rate byte. It calls the existing C1 decay helper at
0x419e40 with current tick after receptor and reaction phases.

The caller MUST supply all 256 rates; this module does not invent the
original dad1.gen half-life settings. This is LAB N until rate provenance
and the full chemical scheduler are independently verified.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .c1_decay_math import decay
from .e09_chemical_bridge import (
    ChemicalBridgeState, ChemicalBridgeTrace, chemical_bridge_tick,
)
from .e09_historical_emitter import Emitter
from .e09_historical_receptor import Receptor
from .c1_reaction_inspector import Reaction


def decay_pool(
    pool: tuple[int, ...],
    rates: tuple[int, ...],
    tick: int,
) -> tuple[int, ...]:
    if (not isinstance(pool,tuple) or len(pool)!=256 or
            any(type(v) is not int or not 0<=v<=255 for v in pool)):
        raise ValueError("pool: 256 bytes required")
    if (not isinstance(rates,tuple) or len(rates)!=256 or
            any(type(v) is not int or not 0<=v<=255 for v in rates)):
        raise ValueError("rates: 256 explicit bytes required")
    if type(tick) is not int or not 0<=tick<=0xFFFFFFFF:
        raise ValueError("unsigned C1 tick required")
    return tuple(decay(value,rates[index],tick) if value else 0
                 for index,value in enumerate(pool))


@dataclass(frozen=True)
class ChemicalDecayBridgeTrace:
    core: ChemicalBridgeTrace
    after: ChemicalBridgeState
    modified_ids: tuple[int, ...]
    phase: str = "emitter -> receptor -> reaction -> 256-chemical decay"


def chemical_bridge_tick_with_decay(
    state: ChemicalBridgeState,
    emitters: tuple[Emitter, ...],
    receptors: tuple[Receptor, ...],
    reactions: tuple[Reaction, ...],
    *,
    rates: tuple[int, ...],
) -> ChemicalDecayBridgeTrace:
    """Separate from I1 baseline: no retroactive change to previous tests."""
    core=chemical_bridge_tick(state,emitters,receptors,reactions)
    new_pool=decay_pool(core.after.pool,rates,state.tick)
    final=replace(core.after,pool=new_pool)
    changed=tuple(i for i,(before,after) in enumerate(zip(core.after.pool,new_pool))
                  if before!=after)
    return ChemicalDecayBridgeTrace(core,final,changed)
