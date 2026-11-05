"""Contratos temporales puros del motor: minuto simulado, fases y medición.

Diferencia cronología real (s), reloj del mundo (min), duración planificada,
tiempo de viaje/trabajo, y duración declarada por un handler. No decide
consecuencias físicas ni convierte una intención en una acción ejecutada.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

SECONDS_PER_MINUTE = 60.0
MAX_REAL_TICK_SECONDS = 20.0
TIME_CONTRACT_VERSION = 1


def finite_nonnegative(value: Any, *, name: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name}: se esperaba tiempo numérico")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name}: se esperaba tiempo finito y no negativo")
    return result


def clamp_real_elapsed(seconds: float) -> float:
    """Recorte deliberado de atrasos del proceso; no cuenta tiempo desconectado."""
    return min(MAX_REAL_TICK_SECONDS,
               finite_nonnegative(seconds, name="tiempo real"))


@dataclass(frozen=True)
class TimePlan:
    operation: str
    planned_travel_minutes: float
    planned_work_minutes: float
    planned_total_minutes: float

    def to_pending(self) -> dict[str, Any]:
        return {
            "schema_version": TIME_CONTRACT_VERSION,
            "planned_travel_minutes": self.planned_travel_minutes,
            "planned_work_minutes": self.planned_work_minutes,
            "planned_total_minutes": self.planned_total_minutes,
            "phase": "travel" if self.planned_travel_minutes > 0 else "work",
        }


def plan_time(operation: str, work_minutes: float, travel_minutes: float = 0,
              *, travel_is_only_phase: bool = False) -> TimePlan:
    """Viaje y trabajo suman; las operaciones solo de viaje no agregan trabajo.

    El tiempo de un handler ejecutado DESPUÉS del trabajo no se suma
    retroactivamente: se conserva únicamente como duración declarada.
    """
    work = finite_nonnegative(work_minutes, name="trabajo previsto")
    travel = finite_nonnegative(travel_minutes, name="viaje previsto")
    if travel_is_only_phase and travel > 0:
        work = 0.0
    return TimePlan(
        str(operation), travel, work, travel + work
    )


def phase_progress(pending: Mapping[str, Any]) -> dict[str, Any] | None:
    """Lectura de la fase, sin modificar progreso o estado físico.

    Se basa en total/remaining persistidos, no en hora real ni en un evento
    narrativo. Para saves legacy sin timing retorna None.
    """
    timing = pending.get("timing")
    if not isinstance(timing, Mapping) or timing.get("schema_version") != TIME_CONTRACT_VERSION:
        return None
    travel = finite_nonnegative(timing.get("planned_travel_minutes"), name="viaje")
    work = finite_nonnegative(timing.get("planned_work_minutes"), name="trabajo")
    total = finite_nonnegative(timing.get("planned_total_minutes"), name="total")
    if not math.isclose(total, travel + work, abs_tol=1e-7, rel_tol=0):
        raise ValueError("Plan temporal incoherente: el total no coincide con sus fases")
    remaining = finite_nonnegative(pending.get("remaining"), name="restante")
    elapsed = max(0.0, min(total, total - remaining))
    travelled = min(elapsed, travel)
    worked = min(work, max(0.0, elapsed - travel))
    phase = ("travel" if elapsed + 1e-7 < travel else
             "work" if elapsed + 1e-7 < total else "ready")
    return {
        "phase": phase,
        "planned_travel_minutes": travel,
        "planned_work_minutes": work,
        "planned_total_minutes": total,
        "elapsed_travel_minutes": travelled,
        "elapsed_work_minutes": worked,
        "elapsed_total_minutes": elapsed,
        "remaining_total_minutes": max(0.0, total - elapsed),
    }


def completion_contract(pending: Mapping[str, Any], *,
                        measured_minutes: float | None,
                        declared_handler_minutes: float,
                        interrupted: bool = False,
                        blocked: bool = False) -> dict[str, Any] | None:
    """Transcribe duraciones que no deben sumarse ni tratarse como equivalentes."""
    progress = phase_progress(pending)
    if progress is None:
        return None
    recorded = (None if measured_minutes is None else
                finite_nonnegative(measured_minutes, name="duración medida"))
    declared = finite_nonnegative(declared_handler_minutes, name="duración declarada")
    status = ("interrupted" if interrupted else
              "blocked" if blocked else "completed")
    return {
        "schema_version": TIME_CONTRACT_VERSION,
        "status": status,
        **progress,
        "measured_elapsed_minutes": recorded,
        "handler_declared_minutes": declared,
        # "complete" describe el tiempo de procesamiento, NO el éxito del handler.
        "work_phase_completed": (not interrupted and not blocked
                                 and progress["elapsed_work_minutes"] + 1e-7 >=
                                 progress["planned_work_minutes"]),
    }
