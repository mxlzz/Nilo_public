"""E09.02b: cinco unidades (P0,P1,C,D0,D1), SVRules extraídas de C1.

Se implementa la dependencia P→Concept(ANDTYPE0)→Decision(TYPE0-TYPE1)
en un único ensayo estacionario, SIN mundo, aprendizaje ni química.
No reproduce los 128+128 enlaces ni el reloj hardcoded de Creatures.
Los pesos de decisión son un ejemplo para mostrar activación/inhibición,
no valores de nacimiento de un Norn.
"""
from __future__ import annotations

from dataclasses import dataclass
from .c1_svrule_subset import (
    CONCEPT_RULE, DECISION_RULE, SVInputs, anded_type0, byte, evaluate,
)


@dataclass(frozen=True)
class MicroWeights:
    perception_to_concept: tuple[int,int] = (128,128)
    d0_exc: int = 255
    d0_inh: int = 0
    d1_exc: int = 0
    d1_inh: int = 255
    decision_rest: int = 80

    def __post_init__(self):
        if len(self.perception_to_concept)!=2:
            raise ValueError("C requiere dos dendritas")
        for i,w in enumerate(self.perception_to_concept):
            byte(w,f"concept dendrite {i}")
        for label in ("d0_exc","d0_inh","d1_exc","d1_inh","decision_rest"):
            byte(getattr(self,label),label)


@dataclass(frozen=True)
class MicroTrace:
    p0: int
    p1: int
    concept: int
    d0: int
    d1: int
    action: str | None

    @property
    def neuron_count(self)->int:
        return 5


def run_once(p0: int, p1: int, *, weights: MicroWeights | None = None) -> MicroTrace:
    p0=byte(p0,"P0")
    p1=byte(p1,"P1")
    cfg=MicroWeights() if weights is None else weights
    if not isinstance(cfg,MicroWeights):
        raise TypeError("weights debe ser MicroWeights")
    concept_signal=anded_type0((p0,p1),cfg.perception_to_concept)
    concept=evaluate(CONCEPT_RULE,SVInputs(and_type0=concept_signal))

    def decision(exc:int,inh:int)->int:
        return evaluate(DECISION_RULE,SVInputs(
            state=cfg.decision_rest,
            type0=(concept*exc)//255,
            type1=(concept*inh)//255,
        ))
    d0=decision(cfg.d0_exc,cfg.d0_inh)
    d1=decision(cfg.d1_exc,cfg.d1_inh)
    action="D0" if d0>d1 else ("D1" if d1>d0 else None)
    return MicroTrace(p0,p1,concept,d0,d1,action)
