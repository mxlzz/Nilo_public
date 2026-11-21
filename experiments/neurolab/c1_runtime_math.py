"""NeuroLab E09.02f.1: aritmética de SVRules constatada en Creatures.exe.

La semántica de PLUS/MINUS/TIMES, sumas dendríticas y salida respecto al
umbral se dedujo de desensamblado estático de la versión PE 1.0.0.1 de C1
(archivo del usuario; no está incluido ni se ejecuta). No presupone que
las reglas completas de aprendizaje químico estén reconstruidas.

Referencias con direcciones y oráculos:
docs/neurolab/E09_02F_EJECUTABLE_C1_PRE_REGISTRO.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .c1_svrule_subset import ATTENTION_RULE, CONCEPT_RULE, DECISION_RULE


def _byte(x: int, name: str) -> int:
    if type(x) is not int or not 0 <= x <= 255:
        raise ValueError(f"{name} requiere entero 0..255")
    return x


def plus(a: int, b: int) -> int:
    return min(255, _byte(a, "a") + _byte(b, "b"))


def minus(a: int, b: int) -> int:
    return max(0, _byte(a, "a") - _byte(b, "b"))


def times(a: int, b: int) -> int:
    return (_byte(a, "a") * _byte(b, "b")) >> 8


def incr(a: int) -> int:
    return min(255, _byte(a, "a") + 1)


def decr(a: int) -> int:
    return max(0, _byte(a, "a") - 1)


@dataclass(frozen=True)
class RuleInputs:
    state: int = 0
    type0: int = 0
    type1: int = 0
    and_type0: int = 0

    def __post_init__(self):
        for key in ("state", "type0", "type1", "and_type0"):
            _byte(getattr(self, key), key)


@dataclass(frozen=True)
class DendriteSignal:
    accumulated: int
    type_value: int
    and_value: int


def dendrite_signal(
    sources: Sequence[int], weights: Sequence[int], *, attenuation: int
) -> DendriteSignal:
    """Subcálculo de señal observado en VA 0x403f2f–0x403f8f.

    Cada dendrita contribuye (source.output*stw)>>8. Se satura la suma a
    255, aplica atenuación como >>8, y se anula AND si source.output=0.
    La conectividad y reglas de activación de nodos NO se infieren aquí.
    """
    _byte(attenuation, "attenuation")
    if not sources or len(sources) != len(weights):
        raise ValueError("se requieren dendritas observables emparejadas")
    for value in sources:
        _byte(value, "source")
    for weight in weights:
        _byte(weight, "stw")
    accumulated = min(255, sum((s * w) >> 8 for s, w in zip(sources, weights)))
    value = (accumulated * attenuation) >> 8
    return DendriteSignal(accumulated, value, value if all(s > 0 for s in sources) else 0)


def evaluate(rule: bytes, inputs: RuleInputs) -> int:
    """Interpreta solo las tres reglas completas de genes C1 inspeccionados.

    Operadores secuenciales con saturación *en cada paso*, no al final.
    """
    if not isinstance(rule, bytes) or len(rule) != 8:
        raise ValueError("SVRule binaria requiere ocho bytes")
    if not isinstance(inputs, RuleInputs):
        raise TypeError("Se espera RuleInputs")
    if rule == DECISION_RULE:
        return minus(plus(inputs.state, inputs.type0), inputs.type1)
    if rule == ATTENTION_RULE:
        return plus(plus(inputs.state, inputs.type0), inputs.type1)
    if rule == CONCEPT_RULE:
        return inputs.and_type0
    raise ValueError("SVRule no verificada en E09.02f.1")


def neuron_output(state: int, threshold: int) -> int:
    """Salida posterior al estado (0x4040cc–0x404110). Sin decay aquí."""
    return minus(state, threshold)
