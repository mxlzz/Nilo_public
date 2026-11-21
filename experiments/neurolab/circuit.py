"""E02: circuito de seis neuronas sin aprendizaje ni conductas predefinidas.

Dos entradas E0/E1, dos patrones C0/C1, dos posibles decisiones D0/D1.
El generador elige pesos concept→decisión por semilla; NO codifica
etiquetas de respuesta correcta. La selección WTA es una proyección
externa de la actividad, no una ley física ni un script de acción.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Literal, Sequence

from .kernel import Brain, BrainState, NeuronSpec, SynapseSpec


@dataclass(frozen=True)
class Choice:
    action: str | None
    status: Literal["winner", "tie", "inactive"]
    scores: tuple[tuple[str, int], ...]


def choose_action(
    state: BrainState, candidates: Sequence[str] = ("D0", "D1"),
    tie_policy: Literal["first", "abstain"] = "abstain",
) -> Choice:
    """WTA determinista sin modificar estados neuronales.

    Con 0 señales, no decide. En empates se abstiene salvo que se seleccione
    explícitamente first (orden fijo de candidates).
    """
    if tie_policy not in ("first", "abstain") or not candidates:
        raise ValueError("política WTA inválida")
    if len(set(candidates)) != len(candidates):
        raise ValueError("candidatos repetidos")
    scores = tuple((name, state.neurons[name].output) for name in candidates)
    peak = max(value for _, value in scores)
    if peak == 0:
        return Choice(None, "inactive", scores)
    winners = [name for name, value in scores if value == peak]
    if len(winners) > 1 and tie_policy == "abstain":
        return Choice(None, "tie", scores)
    return Choice(winners[0], "winner" if len(winners) == 1 else "tie", scores)


def make_six_neuron(seed: int) -> Brain:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("semilla entera requerida")
    rng = random.Random(seed)
    neurons = [
        NeuronSpec("E0", kind="input", decay=255),
        NeuronSpec("E1", kind="input", decay=255),
        NeuronSpec("C0", decay=255),
        NeuronSpec("C1", decay=255),
        NeuronSpec("D0", decay=255),
        NeuronSpec("D1", decay=255),
    ]
    synapses = [SynapseSpec("E0", "C0", 255), SynapseSpec("E1", "C1", 255)]
    for concept in ("C0", "C1"):
        for decision in ("D0", "D1"):
            synapses.append(SynapseSpec(concept, decision, rng.randint(40, 220)))
    return Brain(neurons, synapses)


def run_episode(
    brain: Brain,
    stimulus: tuple[int, int],
    state: BrainState | None = None,
) -> tuple[BrainState, tuple[BrainState, ...], Choice]:
    """3 ticks para propagación E→C→D, sin refuerzo ni cambio de sinapsis."""
    if len(stimulus) != 2:
        raise ValueError("se requieren dos entradas")
    s0 = brain.initial() if state is None else state
    s1 = brain.step(s0, {"E0": stimulus[0], "E1": stimulus[1]})
    s2 = brain.step(s1, {})
    s3 = brain.step(s2, {})
    return s3, (s1, s2, s3), choose_action(s3)
