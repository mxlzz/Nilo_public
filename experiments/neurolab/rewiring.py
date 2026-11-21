"""NeuroLab E07: capacity-limited concept slots with optional rewiring.

Inspired by C1 strength=0 → dendrite migration, but atrophy-by-nonuse
and pattern replacement are explicit NeuroLab rules, NOT historical C1
bytecode. See docs/neurolab/E07_PRE_REGISTRO.md.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import random
from typing import Literal

Mode = Literal["fixed", "migratory", "lru"]
PAIRS = ((0, 2), (0, 3), (1, 2), (1, 3))


@dataclass(frozen=True)
class Slot:
    pattern: tuple[int, int] | None
    strength: int
    weights: tuple[int, int]
    last_used: int = 0

    def __post_init__(self):
        if self.pattern is not None and self.pattern not in PAIRS:
            raise ValueError("fuentes fuera del mismo conjunto C1 experimental")
        if isinstance(self.strength, bool) or not 0 <= self.strength <= 3:
            raise ValueError("fuerza fuera de rango")
        if len(self.weights) != 2 or any(not isinstance(v,int) or isinstance(v,bool) or not 0 <= v <= 255 for v in self.weights):
            raise ValueError("pesos inválidos")


@dataclass(frozen=True)
class WiringState:
    slots: tuple[Slot, Slot]
    time: int = 0

    def __post_init__(self):
        if len(self.slots) != 2 or self.time < 0:
            raise ValueError("capacidad fija de 2 slots")
        patterns = [s.pattern for s in self.slots if s.pattern is not None]
        if len(patterns) != len(set(patterns)):
            raise ValueError("dos slots duplican el mismo concepto")


@dataclass(frozen=True)
class WiringChoice:
    action: str
    slot_index: int | None


class WiringModel:
    def __init__(self, seed: int, mode: Mode):
        if mode not in ("fixed", "migratory", "lru"):
            raise ValueError("modo inválido")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed inválida")
        self.seed = seed
        self.mode = mode

    def _fresh(self, pattern: tuple[int,int], slot_index: int, time: int) -> Slot:
        rng = random.Random(f"{self.seed}:{slot_index}:{time}:{pattern}")
        return Slot(pattern, 3, (rng.randint(40,220), rng.randint(40,220)), time)

    def initial(self) -> WiringState:
        return WiringState((
            self._fresh((0,2), 0, 0),
            self._fresh((1,3), 1, 0),
        ))

    def choose(self, state: WiringState, pattern: tuple[int,int],
               *, structural: bool = True) -> tuple[WiringState, WiringChoice]:
        if pattern not in PAIRS:
            raise ValueError("patrón inválido")
        slots = list(state.slots)
        active_idx = next((i for i,s in enumerate(slots) if s.pattern == pattern), None)
        if active_idx is None and structural and self.mode == "lru":
            idx = min(range(2), key=lambda i: (slots[i].last_used, i))
            slots[idx] = self._fresh(pattern, idx, state.time)
            active_idx = idx
        if active_idx is None:
            return WiringState(tuple(slots), state.time), WiringChoice("D0", None)
        weights = slots[active_idx].weights
        choice = "D0" if weights[0] >= weights[1] else "D1"
        return WiringState(tuple(slots), state.time), WiringChoice(choice, active_idx)

    def update(self, state: WiringState, choice: WiringChoice,
               pattern: tuple[int,int], reward: int,
               *, learning: bool = True) -> WiringState:
        if not isinstance(reward, int) or isinstance(reward,bool) or reward not in (-1,1):
            raise ValueError("reward inválido")
        if pattern not in PAIRS:
            raise ValueError("patrón inválido")
        slots = list(state.slots)
        if choice.slot_index is not None:
            i = choice.slot_index
            if i not in (0,1) or slots[i].pattern != pattern:
                raise ValueError("elección no corresponde al patrón")
            if learning:
                weights = list(slots[i].weights)
                j = 0 if choice.action == "D0" else 1
                weights[j] = min(255, max(0, weights[j] + 16 * reward))
                slots[i] = replace(slots[i], weights=tuple(weights), last_used=state.time+1)
        if learning and self.mode == "migratory":
            for i,slot in enumerate(slots):
                if slot.pattern == pattern:
                    slots[i] = replace(slot, strength=3, last_used=state.time+1)
                elif slot.pattern is not None:
                    remaining = max(0, slot.strength - 1)
                    slots[i] = replace(slot, pattern=None if remaining == 0 else slot.pattern,
                                       strength=remaining)
            if not any(slot.pattern == pattern for slot in slots):
                free = next((i for i,slot in enumerate(slots) if slot.pattern is None), None)
                if free is not None:
                    slots[free] = self._fresh(pattern, free, state.time+1)
        return WiringState(tuple(slots), state.time+1)
