"""NeuroLab E09.02f.2: rate-based C1 decay/relax from x86 executable.

Confirmed locations for SHA256
548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7:
- 0x419E40: decay
- 0x419E90: relax
- 0x43A0E8: factor table
- 0x43A168: mask table
- 0x4044EF: LTW steps +1/-1 on tick % rate == 0

The original EXE is NOT included or executed. This is a mathematical
translation of isolated routines, NOT a full C1 brain tick.
"""
from __future__ import annotations

FACTORS: tuple[int, ...] = (
    0x0000, 0x32A5, 0x71DD, 0xAABB,
    0xD110, 0xE758, 0xF35C, 0xF999,
) + (0xF999,) * 23 + (0xFFFF,)
MASKS: tuple[int, ...] = (0,) * 8 + tuple((1 << (i - 7)) - 1 for i in range(8, 32))
assert len(FACTORS) == len(MASKS) == 32


def _byte(value: int, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError(f"{name}: entero entre 0 y 255 requerido")
    return value


def _tick(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("tick debe ser un entero no negativo")
    return value


def _rate_config(rate: int) -> tuple[int, int]:
    rate = _byte(rate, "rate")
    index = rate >> 3
    return FACTORS[index], MASKS[index]


def decay(current: int, rate: int, tick: int) -> int:
    """Decay C1: current * factor >>16 when tick matches mask."""
    current = _byte(current, "current")
    tick = _tick(tick)
    factor, mask = _rate_config(rate)
    if (tick & mask) != mask:
        return current
    return (current * factor) >> 16


def relax(current: int, rate: int, target: int, tick: int) -> int:
    """C1 relax: retain fraction of signed distance toward target."""
    current = _byte(current, "current")
    target = _byte(target, "target")
    tick = _tick(tick)
    factor, mask = _rate_config(rate)
    if (tick & mask) != mask:
        return current
    residual = (abs(current - target) * factor) >> 16
    return target + residual if current > target else target - residual


def ltw_toward(ltw: int, stw: int, rate: int, tick: int) -> int:
    """Isolated observed LTW one-unit shift (0x4044EF-0x40451B).

    Rate=0 inhibits update; this avoids division-by-zero in Python and
    corresponds to C1's branch when no LTW update is configured.
    """
    ltw = _byte(ltw, "ltw")
    stw = _byte(stw, "stw")
    rate = _byte(rate, "ltw_rate")
    tick = _tick(tick)
    if rate == 0 or ltw == stw or tick % rate != 0:
        return ltw
    return ltw + 1 if stw > ltw else ltw - 1
