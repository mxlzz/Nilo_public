"""Correlación de intentos de LLM sin depender del mundo ni de la UI.

ContextVar aísla cada hilo de deliberación/chat. No consume RNG de Simulation,
no modifica contexto/prompts y no almacena secretos ni payloads por sí mismo.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from secrets import token_hex


_ACTIVE: ContextVar["TraceCall | None"] = ContextVar("nilo_llm_trace", default=None)


@dataclass
class TraceCall:
    store: object
    call_id: str
    session_id: int | None
    purpose: str
    simulated_at: str | None
    source_id: str | None
    ordinal: int = 0
    provider: str = ""
    model: str = ""
    current_id: str | None = None


@contextmanager
def capture_call(store, *, purpose, session_id=None, simulated_at=None,
                 source_id=None):
    """Activa observación solo dentro de una solicitud real.

    Un laboratorio que construye vistas previas no activa este contexto.
    """
    if store is None:
        yield None
        return
    scope = TraceCall(store, token_hex(16), session_id, purpose,
                      simulated_at, source_id)
    token = _ACTIVE.set(scope)
    try:
        yield scope
    finally:
        _ACTIVE.reset(token)


@contextmanager
def capture_candidate(provider, model):
    """Identifica el candidato/réplica real elegido por providers.route."""
    scope = _ACTIVE.get()
    if scope is None:
        yield
        return
    previous = (scope.provider, scope.model, scope.current_id)
    scope.provider, scope.model, scope.current_id = str(provider), str(model), None
    try:
        yield
    finally:
        scope.provider, scope.model, scope.current_id = previous


def _try(func, *args, **kwargs):
    # El observador nunca convierte un fallo de disco en una acción de Nilo.
    try:
        return func(*args, **kwargs)
    except Exception:
        return None


def transport_started(body: bytes, provider: str):
    """Registrar EXACTAMENTE los bytes pasados a urllib.request.Request."""
    scope = _ACTIVE.get()
    if scope is None:
        return None
    scope.ordinal += 1
    scope.current_id = _try(
        scope.store.begin,
        body=body,
        call_id=scope.call_id,
        session_id=scope.session_id,
        purpose=scope.purpose,
        simulated_at=scope.simulated_at,
        source_id=scope.source_id,
        ordinal=scope.ordinal,
        provider=str(provider),
        model=scope.model,
    )
    return scope.current_id


def transport_finished(status: str, *, code: int | None = None):
    scope = _ACTIVE.get()
    if scope is not None and scope.current_id is not None:
        _try(scope.store.finish, scope.current_id, status, code=code)


def candidate_finished(accepted: bool):
    """Finalizar solamente intentos que YA recibieron una respuesta HTTP.

    Si falló el transporte se conserva el error de red/HTTP; si falló la
    validación posterior queda una respuesta recibida, pero rechazada.
    """
    scope = _ACTIVE.get()
    if scope is not None and scope.current_id is not None:
        _try(scope.store.finish, scope.current_id,
             "accepted" if accepted else "rejected",
             only_if="response_received")

def choose_candidate(provider, model):
    """Establecer candidato antes de invocar el handler del router."""
    scope = _ACTIVE.get()
    if scope is not None:
        scope.provider, scope.model, scope.current_id = (
            str(provider), str(model), None
        )
