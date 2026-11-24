"""E09.02f.4: strength growth/atrophy observed in C1 x86 executable.

Source SHA256: 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7
x86 VA: 0x40451e..0x4047e2.
This module models only numeric gain/loss and clearing a lost connection,
NOT the engine's subsequent dendrite migration or neuron pointer updates.
No binary distributed, no game executed.
"""
from __future__ import annotations

from dataclasses import dataclass

from .c1_dendrite_tick import DendriteState


def _byte(v: int, name: str) -> int:
    if type(v) is not int or not 0 <= v <= 255:
        raise ValueError(f"{name}: entero 0..255 requerido")
    return v


@dataclass(frozen=True)
class StrengthState:
    dendrite: DendriteState
    strength: int

    def __post_init__(self):
        if not isinstance(self.dendrite, DendriteState):
            raise TypeError("Se requiere estado de dendrita")
        _byte(self.strength, "strength")


@dataclass(frozen=True)
class StrengthTrace:
    before: StrengthState
    after: StrengthState
    tick: int
    did_gain: bool
    did_lose: bool
    lost_connection: bool


def update_strength(
    state: StrengthState,
    *,
    tick: int,
    gain_rate: int,
    gain_rule_output: int,
    lose_rate: int,
    lose_rule_output: int,
) -> StrengthTrace:
    if not isinstance(state, StrengthState):
        raise TypeError("Se requiere StrengthState")
    if type(tick) is not int or tick < 0:
        raise ValueError("tick entero no negativo")
    gain_rate = _byte(gain_rate, "gain_rate")
    gain_output = _byte(gain_rule_output, "gain_rule_output")
    lose_rate = _byte(lose_rate, "lose_rate")
    lose_output = _byte(lose_rule_output, "lose_rule_output")

    strength = state.strength
    did_gain = False
    did_lose = False
    lost_connection = False
    dendrite = state.dendrite

    if gain_rate > 0 and strength < 255 and tick % gain_rate == 0:
        if gain_output > strength:
            strength = gain_output
            did_gain = True

    if lose_rate > 0 and strength > 0 and tick % lose_rate == 0:
        if lose_output != 0:
            strength -= 1
            did_lose = True
            if strength == 0:
                lost_connection = True
                dendrite = DendriteState(0, 0, 0)

    after = StrengthState(dendrite, strength)
    return StrengthTrace(
        before=state, after=after, tick=tick, did_gain=did_gain,
        did_lose=did_lose, lost_connection=lost_connection,
    )
