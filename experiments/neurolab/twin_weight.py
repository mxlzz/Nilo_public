"""NeuroLab E04: sinapsis con STW/LTW de dos velocidades.

Es un modelo propio para contrastar plasticidad rápida y consolidación
lenta, NO la ecuación exacta ni las tasas del genoma original C1.
Pre-registro: docs/neurolab/E04_PRE_REGISTRO.md
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json


def _byte(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise ValueError(f"{label} debe ser entero entre 0 y 255")
    return value


def _clamp(x: int) -> int:
    return max(0, min(255, x))


def _delta_toward(current: int, target: int, max_delta: int) -> int:
    if current < target:
        return min(max_delta, target - current)
    if current > target:
        return -min(max_delta, current - target)
    return 0


@dataclass(frozen=True)
class TwinSynapse:
    stw: int = 128
    ltw: int = 128

    def __post_init__(self) -> None:
        _byte(self.stw, "stw")
        _byte(self.ltw, "ltw")

    def step(self, reward: int = 0) -> "TwinSynapse":
        if isinstance(reward, bool) or not isinstance(reward, int) or reward not in (-1, 0, 1):
            raise ValueError("reward debe ser -1, 0 o +1")
        fast = _clamp(self.stw + 32 * reward)
        slow = self.ltw + _delta_toward(self.ltw, fast, 1)
        fast += _delta_toward(fast, slow, 6)
        return TwinSynapse(_clamp(fast), _clamp(slow))

    def to_json(self) -> str:
        return json.dumps({"model": "E04-twin-v1", **asdict(self)}, sort_keys=True)

    @staticmethod
    def from_json(blob: str) -> "TwinSynapse":
        payload = json.loads(blob)
        if payload.get("model") != "E04-twin-v1":
            raise ValueError("checkpoint STW/LTW incompatible")
        if set(payload) != {"model", "stw", "ltw"}:
            raise ValueError("campos de checkpoint no previstos")
        return TwinSynapse(stw=payload["stw"], ltw=payload["ltw"])


def simple_weight_step(weight: int, reward: int = 0) -> int:
    """Baseline de un peso sin relajación, misma escala de refuerzo."""
    _byte(weight, "weight")
    if isinstance(reward, bool) or not isinstance(reward, int) or reward not in (-1, 0, 1):
        raise ValueError("reward inválido")
    return _clamp(weight + 32 * reward)
