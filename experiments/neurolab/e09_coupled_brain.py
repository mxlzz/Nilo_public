"""E09.02i / I2: one-way temporal coupling of existing six-node brain and I1.

Explicit NON-FIDELITY constraints:
- Brain step uses Decision CHEM values sampled by the PREVIOUS chemical call.
- Then chemistry runs emitters->receptors->reactions for the NEXT brain step.
- Source emitter ports are external typed state; no invented mapping from
  two winner outputs to C1 brain emitter loci1/2.
- Concept CHEM is tracked for provenance; C1ContextBrain has no Concept
  chemical-strength machinery and never reads it in this experiment.
- No globally integrated chemical decay, real-time 90ms clock, body, world
  or autonomous reward source. No evaluator target or reward label enters.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from .c1_context_brain import C1ContextBrain, ContextBrainState, ContextTick
from .c1_reaction_inspector import Reaction
from .e09_historical_emitter import Emitter
from .e09_historical_receptor import Receptor
from .e09_chemical_bridge import (
    ChemicalBridgeState, ChemicalBridgeTrace, SourcePort,
    initial_bridge, chemical_bridge_tick,
)


@dataclass(frozen=True)
class CoupledState:
    brain: ContextBrainState
    chemistry: ChemicalBridgeState

    def __post_init__(self) -> None:
        if not isinstance(self.brain,ContextBrainState) or not isinstance(
                self.chemistry,ChemicalBridgeState):
            raise TypeError("brain and chemistry typed states required")
        if self.brain.tick != self.chemistry.tick:
            raise ValueError("logical brain and chemistry ticks must match")


@dataclass(frozen=True)
class CoupledTick:
    before: CoupledState
    after: CoupledState
    read_chem: tuple[int, int, int, int]
    next_chem: tuple[int, int, int, int]
    brain_trace: ContextTick
    chemical_trace: ChemicalBridgeTrace


def initial_coupled(
    brain: C1ContextBrain,
    receptors: tuple[Receptor, ...],
    *,
    pool: tuple[int, ...] | None = None,
    ports: tuple[SourcePort, ...] = (),
) -> CoupledState:
    if not isinstance(brain,C1ContextBrain):
        raise TypeError("C1ContextBrain required")
    return CoupledState(
        brain.initial(),initial_bridge(receptors,pool=pool,ports=ports)
    )


def coupled_tick(
    brain: C1ContextBrain,
    state: CoupledState,
    context: int,
    emitters: tuple[Emitter, ...],
    receptors: tuple[Receptor, ...],
    reactions: tuple[Reaction, ...],
    *,
    learn: bool = True,
) -> CoupledTick:
    """Brain-before-chemistry, without access to the evaluator target."""
    if not isinstance(brain,C1ContextBrain) or not isinstance(state,CoupledState):
        raise TypeError("C1ContextBrain and CoupledState required")
    # No chemical results of this invocation can enter this brain call.
    old_decision_chem=state.chemistry.decision_chem
    bt=brain.step(state.brain,context,old_decision_chem,learn=learn)
    ct=chemical_bridge_tick(state.chemistry,emitters,receptors,reactions)
    after=CoupledState(bt.after,ct.after)
    return CoupledTick(
        state,after,old_decision_chem,ct.after.decision_chem,bt,ct
    )


def checkpoint(brain: C1ContextBrain, state: CoupledState) -> str:
    """Save both states, including the exact chemical pool and source ports."""
    if not isinstance(brain,C1ContextBrain) or not isinstance(state,CoupledState):
        raise TypeError("C1ContextBrain and CoupledState required")
    payload={
        "protocol":"E09.02i-I2-v1",
        "brain":brain.checkpoint(state.brain),
        "chemistry":asdict(state.chemistry),
    }
    return json.dumps(payload,sort_keys=True,separators=(",",":"))


def restore(brain: C1ContextBrain, encoded: str) -> CoupledState:
    """Restore only exact known schema. No silent patch or dropped fields."""
    if not isinstance(brain,C1ContextBrain) or not isinstance(encoded,str):
        raise TypeError("C1ContextBrain and JSON string required")
    doc=json.loads(encoded)
    if (not isinstance(doc,dict) or set(doc)!={"protocol","brain","chemistry"}
            or doc["protocol"]!="E09.02i-I2-v1"):
        raise ValueError("unknown coupled checkpoint version/schema")
    raw=doc["chemistry"]
    if not isinstance(raw,dict) or set(raw)!={
            "pool","ports","decision_chem","concept_chem","tick"}:
        raise ValueError("unknown chemical checkpoint schema")
    if not isinstance(raw["ports"],list) or any(
            not isinstance(p,dict) or set(p)!={"lobe","locus","value"}
            for p in raw["ports"]):
        raise ValueError("invalid source port checkpoint")
    chemical=ChemicalBridgeState(
        tuple(raw["pool"]),
        tuple(SourcePort(**p) for p in raw["ports"]),
        tuple(raw["decision_chem"]),
        tuple(raw["concept_chem"]),
        raw["tick"],
    )
    return CoupledState(brain.restore(doc["brain"]),chemical)
