"""E05: crédito temporal mediante elegibilidad sináptica experimental.

La sinapsis no conoce la causa real del refuerzo. Esto permite aprendizaje
retardado y también asignación espuria de crédito a distractores recientes.
No representa los parámetros exactos del cerebro de Creatures 1.

Pre-registro: docs/neurolab/E05_PRE_REGISTRO.md
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json


def _byte(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 255):
        raise ValueError(f"{label} debe ser entero entre 0 y 255")
    return value


@dataclass(frozen=True)
class EligibleSynapse:
    weight: int = 128
    eligibility: int = 0

    def __post_init__(self) -> None:
        _byte(self.weight, "weight")
        _byte(self.eligibility, "eligibility")

    def mark_used(self) -> "EligibleSynapse":
        """La conexión participó: elegibilidad máxima."""
        return EligibleSynapse(self.weight, 255)

    def advance_tick(self) -> "EligibleSynapse":
        """Olvido discreto: floor(e*3/4), independiente del refuerzo."""
        return EligibleSynapse(self.weight, (self.eligibility * 3) // 4)

    def apply_reward(self, reward: int) -> "EligibleSynapse":
        if isinstance(reward, bool) or not isinstance(reward, int) or reward not in (-1, 0, 1):
            raise ValueError("reward debe ser -1, 0 o +1")
        amount = (32 * self.eligibility) // 255
        weight = max(0, min(255, self.weight + reward * amount))
        return EligibleSynapse(weight, self.eligibility)

    def to_json(self) -> str:
        return json.dumps({"model": "E05-eligibility-v1", **asdict(self)}, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> "EligibleSynapse":
        record = json.loads(payload)
        if not isinstance(record, dict) or set(record) != {"model", "weight", "eligibility"}:
            raise ValueError("checkpoint con campos inválidos")
        if record["model"] != "E05-eligibility-v1":
            raise ValueError("versión incompatible")
        return cls(weight=record["weight"], eligibility=record["eligibility"])
