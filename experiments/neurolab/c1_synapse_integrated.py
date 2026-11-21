"""E09.02g.1 — a complete isolated dendrite tick with C1 gene rules.

Uses original dad1.gen lobe-gene fields (Decision class 0/1, Concept
class 0), generic C1 SVRule interpreter, observed C1 dendrite numeric
transition and atrophy code. No original binary is distributed.

This is a single synapse within an EXTERNALLY supplied chemical/neuronal
state. It does not implement the biochemical world, whole brain timing,
the decision winner-takes-all scheduler, or migration after exhaustion.
"""
from __future__ import annotations

from dataclasses import dataclass

from .c1_dendrite_tick import (
    DendriteRates, DendriteState, DendriteTrace, transition,
)
from .c1_strength import StrengthState, StrengthTrace, update_strength
from .c1_svrule_runtime import C1SVTable, evaluate


def _byte(value: int, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError(f"{name} debe ser un byte")
    return value


def _rule(*operands: int) -> bytes:
    if len(operands) >= 8:
        raise ValueError("SVRule genómica no terminada")
    return bytes((*operands, *(0 for _ in range(8 - len(operands)))))


@dataclass(frozen=True)
class C1DendriteGene:
    source_lobe: int
    migration_type: int
    rates: DendriteRates
    gain_rate: int
    lose_rate: int
    susceptibility_rule: bytes
    reinforcement_rule: bytes
    gain_rule: bytes
    lose_rule: bytes

    def __post_init__(self):
        _byte(self.source_lobe, "source_lobe")
        _byte(self.migration_type, "migration_type")
        _byte(self.gain_rate, "gain_rate")
        _byte(self.lose_rate, "lose_rate")
        if not isinstance(self.rates, DendriteRates):
            raise TypeError("DendriteRates requerido")
        for label in ("susceptibility_rule","reinforcement_rule","gain_rule","lose_rule"):
            value=getattr(self,label)
            if not isinstance(value, bytes) or len(value) != 8:
                raise ValueError(f"{label}: ocho bytes necesarios")


# Literal data derived from dad1.gen lobe genes 120 and 122:
# Decision: source lobe 8, migration 1, decay 48, STW relax 80,
# LTW rate 128, strength gain 3, loss 5.
# Concept: source lobe 0, migration 2, no susceptibility/weight plasticity,
# strength gain 2, loss 3.
DECISION_EXCITATORY_GENE = C1DendriteGene(
    8, 1, DendriteRates(48,80,128), 3, 5,
    _rule(10,22,16),_rule(5),_rule(18,22,5,22,19),_rule(7),
)
DECISION_INHIBITORY_GENE = C1DendriteGene(
    8, 1, DendriteRates(48,80,128), 3, 5,
    _rule(10,22,16),_rule(6),_rule(18,22,6,22,19),_rule(8),
)
CONCEPT_GENE = C1DendriteGene(
    0, 2, DendriteRates(0,0,0), 2, 3,
    _rule(),_rule(),_rule(10,22,5),_rule(6),
)


@dataclass(frozen=True)
class C1SynapseState:
    dendrite: DendriteState
    strength: int

    def __post_init__(self):
        if not isinstance(self.dendrite, DendriteState):
            raise TypeError("DendriteState requerido")
        _byte(self.strength, "strength")


@dataclass(frozen=True)
class C1SynapticInput:
    source_output: int
    owner_state: int
    owner_output: int
    threshold: int = 0
    chemicals: tuple[int,int,int,int] = (0,0,0,0)
    type0: int = 0
    type1: int = 0
    and_type0: int = 0
    and_type1: int = 0
    conduct: int = 0

    def __post_init__(self):
        for label in ("source_output","owner_state","owner_output","threshold",
                      "type0","type1","and_type0","and_type1","conduct"):
            _byte(getattr(self,label),label)
        if (not isinstance(self.chemicals,tuple) or len(self.chemicals)!=4):
            raise ValueError("exactamente cuatro concentraciones químicas")
        for chem in self.chemicals:
            _byte(chem,"chemical")


@dataclass(frozen=True)
class C1IntegratedSynapseTrace:
    before: C1SynapseState
    after: C1SynapseState
    snapshot: C1SVTable
    susceptibility_rule_output: int
    reinforcement_rule_output: int
    gain_strength_rule_output: int
    lose_strength_rule_output: int
    numeric: DendriteTrace
    strength: StrengthTrace
    owner_neuron_cleared: bool


def _make_snapshot(state: C1SynapseState, inputs: C1SynapticInput) -> C1SVTable:
    s=state.dendrite
    return C1SVTable(
        chem0=inputs.chemicals[0],chem1=inputs.chemicals[1],
        chem2=inputs.chemicals[2],chem3=inputs.chemicals[3],
        state=inputs.owner_state,output=inputs.owner_output,
        threshold=inputs.threshold,type0=inputs.type0,type1=inputs.type1,
        and_type0=inputs.and_type0,and_type1=inputs.and_type1,
        input=inputs.source_output,conduct=inputs.conduct,
        susceptibility=s.susceptibility,stw=s.stw,ltw=s.ltw,
        strength=state.strength,
    )


def update_c1_synapse(
    before: C1SynapseState, gene: C1DendriteGene,
    inputs: C1SynapticInput, *, tick: int,
) -> C1IntegratedSynapseTrace:
    if not isinstance(before,C1SynapseState) or not isinstance(gene,C1DendriteGene):
        raise TypeError("Estado y gen C1 tipados requeridos")
    if not isinstance(inputs,C1SynapticInput):
        raise TypeError("Entradas sinápticas tipadas requeridas")

    snapshot=_make_snapshot(before,inputs)
    # All four rules see the same OLD variables captured at dendrite entry.
    goal=evaluate(gene.susceptibility_rule,snapshot)
    chemical=evaluate(gene.reinforcement_rule,snapshot)
    gain=evaluate(gene.gain_rule,snapshot)
    loss=evaluate(gene.lose_rule,snapshot)

    numeric=transition(
        before.dendrite,rates=gene.rates,tick=tick,
        susceptibility_rule_output=goal,
        reinforcement_rule_output=chemical,
    )
    strength=update_strength(
        StrengthState(numeric.after,before.strength),
        tick=tick,gain_rate=gene.gain_rate,gain_rule_output=gain,
        lose_rate=gene.lose_rate,lose_rule_output=loss,
    )
    return C1IntegratedSynapseTrace(
        before=before,
        after=C1SynapseState(strength.after.dendrite,strength.after.strength),
        snapshot=snapshot,
        susceptibility_rule_output=goal,
        reinforcement_rule_output=chemical,
        gain_strength_rule_output=gain,
        lose_strength_rule_output=loss,
        numeric=numeric,strength=strength,
        owner_neuron_cleared=strength.lost_connection,
    )
