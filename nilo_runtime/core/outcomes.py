"""Contratos puros de ejecución, efectos observados y procedencia.

Sin dependencia de isla, física, prompts, SQLite ni textos narrativos.
Los resultados son afirmaciones de ejecución; las diferencias físicas se
acreditan exclusivamente por mediciones de estado, nunca por facts.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
from typing import Any, Mapping, Optional

RESULT_STATUSES = frozenset((
    "verified_success", "verified_failure", "precondition_failed", "no_evaluable",
))
CAUSAL_EVENT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class LegacyExecution:
    """ÚNICA frontera del viejo retorno (minutos, facts, éxito, notable).

    Sólo se usa mientras world.execute_action conserva el API público. No
    produce evidencia; simplemente valida y estabiliza la forma del retorno.
    """

    duration_minutes: float
    facts: tuple[str, ...]
    success: bool
    notable: bool

    @classmethod
    def parse(cls, value: Any) -> "LegacyExecution":
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            raise TypeError("Ejecución heredada: se esperan exactamente cuatro campos")
        duration, facts, success, notable = value
        if not isinstance(facts, (list, tuple)):
            raise TypeError("Ejecución heredada: facts debe ser lista/tupla")
        if type(success) is not bool or type(notable) is not bool:
            raise TypeError("Ejecución heredada: éxito y relevancia deben ser booleanos")
        try:
            minutes = float(duration)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Ejecución heredada: duración inválida") from exc
        if not math.isfinite(minutes) or minutes < 0:
            raise ValueError("Ejecución heredada: duración no finita o negativa")
        return cls(minutes, tuple(map(str, facts)), success, notable)


@dataclass(frozen=True)
class ActionResult:
    """Resultado de una acción; facts son presentación, no evidencia causal."""

    op: str
    status: str
    success: bool
    notable: bool
    facts: tuple[str, ...]
    duration_minutes: float = 0.0
    physical: Optional[dict] = None

    @classmethod
    def from_legacy(cls, step, facts, success, notable, duration_minutes=0,
                    *, no_evaluable=False, physical=None, status_override=None):
        status = status_override or ("no_evaluable" if no_evaluable else
                  "verified_success" if success else "verified_failure")
        # Las llamadas de tests a ActionResult(...) pueden construir datos
        # inválidos a propósito para probar diagnostics. El adaptador, no el
        # constructor, aplica la consistencia del protocolo en producción.
        if status not in RESULT_STATUSES:
            raise ValueError("Estado de acción desconocido: " + str(status))
        if status == "verified_success" and not success:
            raise ValueError("Resultado exitoso con success=False")
        if status != "verified_success" and success:
            raise ValueError("Resultado no exitoso con success=True")
        if not isinstance(facts, (list, tuple)):
            raise TypeError("facts debe ser una lista o tupla de mensajes")
        minutes = float(duration_minutes)
        if not math.isfinite(minutes) or minutes < 0:
            raise ValueError("Duración de acción no finita o negativa")
        return cls(str(step.get("op", "")), status, bool(success), bool(notable),
                   tuple(map(str, facts)), minutes, physical=deepcopy(physical))

    def as_legacy(self):
        """Compatibilidad temporal para handlers/consumidores no migrados."""
        return self.duration_minutes, list(self.facts), self.success, self.notable

    def to_record(self):
        """Formato histórico: NO agregar campos y alterar replays viejos."""
        return {
            "op": self.op,
            "status": self.status,
            "success": self.success,
            "notable": self.notable,
            "duration_minutes": self.duration_minutes,
            "facts": list(self.facts),
            "physical": deepcopy(self.physical),
        }


@dataclass(frozen=True)
class RecordedEffect:
    """Variación física ya medida. No equivale a una capacidad demostrada."""

    dimension: str
    key: str
    delta: float
    measurement_id: str

    def to_record(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "key": self.key,
            "delta": self.delta,
            "measurement_id": self.measurement_id,
        }


@dataclass(frozen=True)
class CausalActionEvent:
    """Registro vinculado al ID de acción existente; no crea otro UUID."""

    action_id: str
    op: str
    evaluation_status: str
    success: bool
    measurement_id: str | None
    unmodeled_attempt_id: str | None
    effects: tuple[RecordedEffect, ...]
    position_start: tuple[int, ...] | None
    position_end: tuple[int, ...] | None

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": CAUSAL_EVENT_SCHEMA_VERSION,
            "action_id": self.action_id,
            "op": self.op,
            "evaluation_status": self.evaluation_status,
            "success": self.success,
            "measurement_id": self.measurement_id,
            "unmodeled_attempt_id": self.unmodeled_attempt_id,
            "effects": [effect.to_record() for effect in self.effects],
            "position_start": list(self.position_start) if self.position_start is not None else None,
            "position_end": list(self.position_end) if self.position_end is not None else None,
        }


def causal_event_from_measurement(
    action_id: str, result: ActionResult,
    measurement: Mapping[str, Any] | None,
    *, unmodeled_attempt_id: str | None = None,
) -> CausalActionEvent:
    """Construye un hecho causal sólo con resultados y mediciones identificadas.

    Si falta medida, NO afirma variaciones en inventario, necesidades u obras.
    Los deltas no se deducen de facts, título de proyecto o narrativa.
    """
    if not isinstance(action_id, str) or not action_id.strip():
        raise ValueError("La acción necesita el ID real de su registro")
    if result.status not in RESULT_STATUSES:
        raise ValueError("Estado inválido en el resultado")
    if result.success != (result.status == "verified_success"):
        raise ValueError("Éxito contradictorio con el estado de ejecución")
    if unmodeled_attempt_id is not None and (
        result.status != "no_evaluable"
        or not isinstance(unmodeled_attempt_id, str)
        or not unmodeled_attempt_id.strip()
    ):
        raise ValueError("Intento no evaluable sin relación válida")

    mid = None
    effects: list[RecordedEffect] = []
    position_start = position_end = None
    if measurement is not None:
        if not isinstance(measurement, Mapping):
            raise TypeError("La evidencia medida debe ser un objeto")
        mid = measurement.get("id")
        if not isinstance(mid, str) or not mid.strip():
            raise ValueError("Medición sin ID verificable")
        if measurement.get("op") != result.op:
            raise ValueError("La medición pertenece a otra operación")
        # El status del medidor tiene que corresponder al resultado; no puede
        # respaldarse la acción con un ensayo fallido de otro status.
        recorded_status = measurement.get("evaluation_status")
        if recorded_status not in (None, result.status):
            raise ValueError("La medición contradice el status del resultado")
        for dimension, field in (("inventory", "inventory_delta"),
                                 ("needs", "needs_delta")):
            changes = measurement.get(field) or {}
            if not isinstance(changes, Mapping):
                raise TypeError("El registro de diferencias debe ser un objeto")
            for key, raw in sorted(changes.items()):
                if not isinstance(key, str) or type(raw) not in (int, float):
                    raise ValueError("Variación física inválida")
                delta = float(raw)
                if not math.isfinite(delta):
                    raise ValueError("Variación física no finita")
                if delta:
                    effects.append(RecordedEffect(dimension, key, delta, mid))
        for dimension, field in (("objects", "object_delta"),
                                 ("structures", "structure_delta")):
            raw = measurement.get(field, 0)
            if type(raw) not in (int, float) or not math.isfinite(float(raw)):
                raise ValueError("Cantidad física inválida")
            if raw:
                effects.append(RecordedEffect(dimension, "count", float(raw), mid))
        initial = (measurement.get("start") or {}).get("position")
        final = (measurement.get("end") or {}).get("position")
        if initial is not None:
            if not isinstance(initial, (list, tuple)) or len(initial) != 3 or not all(type(x) is int for x in initial):
                raise ValueError("Posición inicial medida inválida")
            position_start = tuple(initial)
        if final is not None:
            if not isinstance(final, (list, tuple)) or len(final) != 3 or not all(type(x) is int for x in final):
                raise ValueError("Posición final medida inválida")
            position_end = tuple(final)
    return CausalActionEvent(
        action_id=action_id, op=result.op,
        evaluation_status=result.status, success=result.success,
        measurement_id=mid, unmodeled_attempt_id=unmodeled_attempt_id,
        effects=tuple(effects),
        position_start=position_start, position_end=position_end,
    )
