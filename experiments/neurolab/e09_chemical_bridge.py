"""E09.02i / I1: minimal, immutable brain-chemistry handoff using existing C1 parts.

Scope is the LAB N line, not complete C1 fidelity. One logical chemistry
call follows emitters -> receptors -> reactions, as shown in E09h.1.
The original 256-chemical half-life pass is NOT executed here.
Source values are explicit ports (lobe,locus,value), never inferred from
an action label or provided with evaluator ground truth.

Divergences: port collisions, duplicate receptor destinations and missing
source ports are rejected instead of copying all original loader behavior.
Only brain lobes 6 and 8, CHEM0..3, can be sampled in this minimal bridge.
"""
from __future__ import annotations

from dataclasses import dataclass

from .e09_historical_emitter import Emitter, EmitterResult, emitter_tick
from .e09_historical_receptor import Receptor
from .e09_historical_locus import (
    initialize_brain_chem_loci, route_brain_chem_loci,
)
from .e09_historical_reaction_math import process_reactions, ReactionEvent
from .c1_reaction_inspector import Reaction


def _byte(value: int, name: str) -> None:
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError(f"{name} must be byte 0..255")


@dataclass(frozen=True)
class SourcePort:
    lobe: int
    locus: int
    value: int

    def __post_init__(self) -> None:
        _byte(self.lobe, "port.lobe")
        _byte(self.locus, "port.locus")
        _byte(self.value, "port.value")
        if self.lobe not in (6, 8):
            raise ValueError("only Decision6 and Concept8 source ports supported")


@dataclass(frozen=True)
class ChemicalBridgeState:
    pool: tuple[int, ...]
    ports: tuple[SourcePort, ...]
    decision_chem: tuple[int, int, int, int]
    concept_chem: tuple[int, int, int, int]
    tick: int = 0

    def __post_init__(self) -> None:
        if (not isinstance(self.pool, tuple) or len(self.pool) != 256 or
                any(type(x) is not int or not 0 <= x <= 255 for x in self.pool)):
            raise ValueError("chemical pool must be 256 bytes")
        if not isinstance(self.ports, tuple) or any(
                not isinstance(port, SourcePort) for port in self.ports):
            raise ValueError("source ports must be a tuple of SourcePort")
        addresses = [(p.lobe,p.locus) for p in self.ports]
        if len(set(addresses)) != len(addresses):
            raise ValueError("duplicate source port")
        for name in ("decision_chem","concept_chem"):
            chem = getattr(self,name)
            if not isinstance(chem,tuple) or len(chem) != 4:
                raise ValueError(f"{name} must contain 4 bytes")
            for value in chem:
                _byte(value,name)
        if type(self.tick) is not int or not 0 <= self.tick <= 0xFFFFFFFF:
            raise ValueError("tick must be unsigned 32-bit integer")


@dataclass(frozen=True)
class ChemicalBridgeTrace:
    before: ChemicalBridgeState
    after: ChemicalBridgeState
    pool_after_emitters: tuple[int, ...]
    decision_at_receptors: tuple[int, int, int, int]
    concept_at_receptors: tuple[int, int, int, int]
    emitter_results: tuple[EmitterResult, ...]
    reaction_events: tuple[ReactionEvent, ...]
    skipped_phase: str = "global 256-chemical decay: NOT IMPLEMENTED"


def initial_bridge(
    receptors: tuple[Receptor, ...],
    *,
    pool: tuple[int,...] | None = None,
    ports: tuple[SourcePort,...] = (),
) -> ChemicalBridgeState:
    """Construct a LAB baseline; zeros for pool are NOT claimed C1 genesis."""
    if not isinstance(receptors, tuple) or any(
            not isinstance(r,Receptor) for r in receptors):
        raise ValueError("receptors must be a typed tuple")
    return ChemicalBridgeState(
        pool=tuple(0 for _ in range(256)) if pool is None else pool,
        ports=ports,
        decision_chem=initialize_brain_chem_loci(receptors,6),
        concept_chem=initialize_brain_chem_loci(receptors,8),
    )


def chemical_bridge_tick(
    state: ChemicalBridgeState,
    emitters: tuple[Emitter, ...],
    receptors: tuple[Receptor, ...],
    reactions: tuple[Reaction, ...],
) -> ChemicalBridgeTrace:
    """Strictly ordered 1-call lab chemistry; DOES NOT advance brain."""
    if not isinstance(state,ChemicalBridgeState):
        raise TypeError("ChemicalBridgeState required")
    if not isinstance(emitters,tuple) or any(
            not isinstance(e,Emitter) for e in emitters):
        raise TypeError("typed emitter tuple required")
    if not isinstance(receptors,tuple) or any(
            not isinstance(r,Receptor) for r in receptors):
        raise TypeError("typed receptor tuple required")
    if not isinstance(reactions,tuple) or any(
            not isinstance(r,Reaction) for r in reactions):
        raise TypeError("typed reaction tuple required")
    if state.tick == 0xFFFFFFFF:
        raise ValueError("tick overflow; no wraparound policy verified")

    ports = {(p.lobe,p.locus):p.value for p in state.ports}
    current = state.pool
    results=[]
    for em in emitters:
        if em.organ != 0 or em.lobe not in (6,8):
            raise ValueError("bridge supports only brain emitters")
        address=(em.lobe,em.locus)
        if address not in ports:
            raise ValueError(f"missing source port for emitter {em.gene_index}")
        result=emitter_tick(em,current,ports[address],state.tick)
        ports[address]=result.source
        current=result.pool
        results.append(result)

    after_emitters=current
    decision=route_brain_chem_loci(receptors,current,6,state.decision_chem)
    concept=route_brain_chem_loci(receptors,current,8,state.concept_chem)
    after_reactions,events=process_reactions(current,reactions,state.tick)
    new_ports=tuple(SourcePort(p.lobe,p.locus,ports[p.lobe,p.locus])
                    for p in state.ports)
    after=ChemicalBridgeState(
        after_reactions,new_ports,decision,concept,state.tick+1
    )
    return ChemicalBridgeTrace(
        state,after,after_emitters,decision,concept,tuple(results),events,
    )
