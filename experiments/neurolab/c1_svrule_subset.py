"""NeuroLab E09.02a — intérprete de tres SVRules del dad1.gen original.

Reglas de GEN verificadas:
  Decision:  09 17 0C 18 0D 00 00 00 -> STATE + TYPE0 - TYPE1
  Attention: 09 17 0C 17 0D 00 00 00 -> STATE + TYPE0 + TYPE1
  Concept:   0E 00 00 00 00 00 00 00 -> ANDTYPE0

Este módulo reproduce SOLO la expresión aritmética de esas reglas.
La saturación final y el cálculo de ANDTYPE0 son convenciones de
laboratorio hasta verificar en el ejecutable C1 el orden exacto, la
normalización y el tratamiento de límites.
No es una mente integrada ni usa un LLM, mundo o cuerpo.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

DECISION_RULE = bytes((9, 23, 12, 24, 13, 0, 0, 0))
ATTENTION_RULE = bytes((9, 23, 12, 23, 13, 0, 0, 0))
CONCEPT_RULE = bytes((14, 0, 0, 0, 0, 0, 0, 0))
_ALLOWED = {
    DECISION_RULE: "decision",
    ATTENTION_RULE: "attention",
    CONCEPT_RULE: "concept",
}


def byte(value: int, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError(f"{name}: entero 0..255 esperado")
    return value


def clip(value: int) -> int:
    return max(0, min(255, value))


@dataclass(frozen=True)
class SVInputs:
    state: int = 0
    type0: int = 0
    type1: int = 0
    and_type0: int = 0

    def __post_init__(self):
        for name in ("state", "type0", "type1", "and_type0"):
            byte(getattr(self, name), name)


def evaluate(rule: bytes, inputs: SVInputs) -> int:
    """Convención propia: evaluar expresión genética y saturar al final."""
    if not isinstance(rule, bytes) or len(rule) != 8:
        raise ValueError("regla de C1 requiere ocho bytes")
    if rule not in _ALLOWED:
        raise ValueError("SVRule no documentada en E09.02a")
    if not isinstance(inputs, SVInputs):
        raise TypeError("inputs debe ser SVInputs")
    kind = _ALLOWED[rule]
    if kind == "decision":
        return clip(inputs.state + inputs.type0 - inputs.type1)
    if kind == "attention":
        return clip(inputs.state + inputs.type0 + inputs.type1)
    return inputs.and_type0


def anded_type0(
    outputs: Sequence[int], weights: Sequence[int],
) -> int:
    """Señal AND de un detector de Concept.

    En la interpretación de la guía C1, ANDTYPE0 es cero si una de las
    dendritas de clase 0 tiene source output=0; de lo contrario es la
    suma limitada de señales ponderadas. El factor /255 y truncado entero
    son convenciones de laboratorio y NO se certifican byte a byte.
    """
    if not outputs or len(outputs) != len(weights):
        raise ValueError("cada dendrita requiere salida y peso")
    for v in outputs:
        byte(v, "output")
    for w in weights:
        byte(w, "weight")
    if any(v == 0 for v in outputs):
        return 0
    return clip(sum((v * w) // 255 for v, w in zip(outputs, weights)))
