"""E06: detectores de pares y decisiones aprendidas, sin elegibilidad E05.

Los patrones de dos señales se definen a priori; NO se aprenden ni
migran. Solo se modifican sus asociaciones sinápticas con decisiones.
El evaluador de XOR está en e06_protocol.py, nunca aquí.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Literal

PairMode = Literal["pair", "singleton"]
PAIR_FEATURES = ((0, 2), (0, 3), (1, 2), (1, 3))
SINGLETON_FEATURES = ((0,), (1,), (2,), (3,))


@dataclass(frozen=True)
class ConceptWeights:
    edges: tuple[tuple[int, int], ...]
    trials: int = 0

    def __post_init__(self) -> None:
        if len(self.edges) != 4:
            raise ValueError("se requieren cuatro detectores")
        if any(
            len(pair) != 2 or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 or v > 255 for v in pair)
            for pair in self.edges
        ):
            raise ValueError("peso fuera de rango")
        if isinstance(self.trials, bool) or not isinstance(self.trials, int) or self.trials < 0:
            raise ValueError("contador inválido")


@dataclass(frozen=True)
class ConceptChoice:
    action: str | None
    active: tuple[int, ...]
    scores: tuple[int, int]
    weights_at_choice: tuple[tuple[int, int], ...]
    trial: int


class ConceptLearner:
    def __init__(self, seed: int, *, mode: PairMode = "pair", rate: int = 16):
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("semilla debe ser entera")
        if mode not in ("pair", "singleton"):
            raise ValueError("modo inválido")
        if isinstance(rate, bool) or not isinstance(rate, int) or not 1 <= rate <= 255:
            raise ValueError("rate fuera de rango")
        self.mode = mode
        self.rate = rate
        rng = random.Random(seed)
        self._initial = ConceptWeights(tuple((rng.randint(40,220), rng.randint(40,220)) for _ in range(4)))

    def initial(self) -> ConceptWeights:
        return self._initial

    def _detect(self, bits: tuple[int, ...]) -> tuple[int, ...]:
        if not isinstance(bits, tuple) or len(bits) != 5 or any(x not in (0, 1) or isinstance(x, bool) for x in bits):
            raise ValueError("señal: cinco bits 0/1")
        features = PAIR_FEATURES if self.mode == "pair" else SINGLETON_FEATURES
        return tuple(i for i, members in enumerate(features) if all(bits[j] == 1 for j in members))

    def respond(self, state: ConceptWeights, bits: tuple[int, ...]) -> ConceptChoice:
        active = self._detect(bits)
        scores = tuple(sum(state.edges[i][j] for i in active) for j in range(2))
        action = None if not active else ("D0" if scores[0] >= scores[1] else "D1")
        return ConceptChoice(action, active, (scores[0], scores[1]), state.edges, state.trials)

    def update(self, state: ConceptWeights, choice: ConceptChoice, reward: int, *, learn: bool = True) -> ConceptWeights:
        if isinstance(reward, bool) or reward not in (-1, 1) or not isinstance(reward, int):
            raise ValueError("reward debe ser +1 o -1")
        if choice.trial != state.trials or choice.weights_at_choice != state.edges:
            raise ValueError("elección antigua")
        weights = [list(pair) for pair in state.edges]
        if learn and choice.action is not None:
            pos = 0 if choice.action == "D0" else 1
            for i in choice.active:
                weights[i][pos] = max(0, min(255, weights[i][pos] + self.rate * reward))
        return ConceptWeights(tuple(tuple(p) for p in weights), state.trials + 1)
