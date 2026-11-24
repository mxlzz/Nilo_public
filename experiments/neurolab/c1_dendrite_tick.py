"""E09.02f.3: verified subset of a C1 dendrite tick.

Source: static disassembly of user-supplied Creatures.exe, PE 1.0.0.1
SHA-256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7.
Specific x86 ranges: 0x4042C9..0x40451B, 0x419E40 and 0x419E90.

This isolates susceptibility, reinforcement effect, STW relaxation, LTW
step. It does NOT yet model the SVRule's chemical inputs, strength, atrophy,
migration, brain-wide timing, or Norn behavior. No executable is included.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from .c1_decay_math import decay, relax, ltw_toward


def _byte(v: int, label: str) -> int:
    if type(v) is not int or not 0 <= v <= 255:
        raise ValueError(f"{label} requiere entero 0..255")
    return v


@dataclass(frozen=True)
class DendriteRates:
    susceptibility_decay: int = 48
    stw_relax: int = 80
    ltw_rate: int = 128

    def __post_init__(self):
        for key in ("susceptibility_decay", "stw_relax", "ltw_rate"):
            _byte(getattr(self, key), key)


@dataclass(frozen=True)
class DendriteState:
    susceptibility: int = 0
    stw: int = 0
    ltw: int = 0

    def __post_init__(self):
        for key in ("susceptibility", "stw", "ltw"):
            _byte(getattr(self, key), key)


@dataclass(frozen=True)
class DendriteTrace:
    before: DendriteState
    after: DendriteState
    tick: int
    susceptibility_rule_output: int
    reinforcement_rule_output: int
    reinforcement_effect: int
    stw_after_reinforcement: int
    stw_after_relaxation: int


def transition(
    state: DendriteState,
    *,
    rates: DendriteRates = DendriteRates(),
    tick: int,
    susceptibility_rule_output: int,
    reinforcement_rule_output: int,
) -> DendriteTrace:
    if not isinstance(state, DendriteState) or not isinstance(rates, DendriteRates):
        raise TypeError("Se requieren DendriteState y DendriteRates")
    if type(tick) is not int or tick < 0:
        raise ValueError("tick entero no negativo")
    goal = _byte(susceptibility_rule_output, "susceptibility_rule_output")
    chem = _byte(reinforcement_rule_output, "reinforcement_rule_output")

    if goal > state.susceptibility:
        # mov bl; add bl,4; mov [ebp],bl: explicit 8-bit wrap in x86.
        sus = (state.susceptibility + 4) & 255
    else:
        sus = decay(state.susceptibility, rates.susceptibility_decay, tick)

    effect = (sus * chem) >> 8 if sus > 0 else 0
    stw = state.stw
    if effect > 0 and effect > state.stw - state.ltw:
        stw = min(255, state.ltw + effect)
    stw_after_reinforcement = stw

    if stw != state.ltw:
        stw = relax(stw, rates.stw_relax, state.ltw, tick)

    ltw = ltw_toward(state.ltw, stw, rates.ltw_rate, tick)
    result = DendriteState(sus, stw, ltw)
    return DendriteTrace(
        before=state, after=result, tick=tick,
        susceptibility_rule_output=goal,
        reinforcement_rule_output=chem,
        reinforcement_effect=effect,
        stw_after_reinforcement=stw_after_reinforcement,
        stw_after_relaxation=stw,
    )


def checkpoint(state: DendriteState, rates: DendriteRates, next_tick: int) -> str:
    if not isinstance(state, DendriteState) or not isinstance(rates, DendriteRates):
        raise TypeError("estado/tasas incorrectas")
    if type(next_tick) is not int or next_tick < 0:
        raise ValueError("next_tick inválido")
    return json.dumps({
        "model": "C1-DENDRITE-F3-v1", "state": asdict(state),
        "rates": asdict(rates), "next_tick": next_tick,
    }, sort_keys=True, separators=(",", ":"))


def restore(blob: str) -> tuple[DendriteState, DendriteRates, int]:
    record = json.loads(blob)
    if not isinstance(record, dict) or set(record) != {"model", "state", "rates", "next_tick"}:
        raise ValueError("checkpoint sináptico inválido")
    if record["model"] != "C1-DENDRITE-F3-v1":
        raise ValueError("versión de sinapsis no compatible")
    state = DendriteState(**record["state"])
    rates = DendriteRates(**record["rates"])
    tick = record["next_tick"]
    if type(tick) is not int or tick < 0:
        raise ValueError("tick de checkpoint inválido")
    return state, rates, tick
