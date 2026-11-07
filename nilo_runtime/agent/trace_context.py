"""Correlación de intentos de LLM sin depender del mundo ni de la UI.

ContextVar aísla cada hilo de deliberación/chat. No consume RNG de Simulation,
no modifica contexto/prompts y no almacena secretos ni payloads por sí mismo.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
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
    snapshots: list = field(default_factory=list)


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
    from nilo_runtime.agent.provenance import build_metadata
    try:
        meta = build_metadata(scope.snapshots, body, str(provider), scope.purpose)
    except Exception:
        # Keep the literal body even when metadata cannot be produced. Never
        # archive exception text: it may contain values from a hidden context.
        meta = {"schema_version": 1, "trace_status": "unavailable",
                "reason": "metadata_capture_failed",
                "payload_verification": "no_verificado_con_el_payload"}
    scope.current_id = _try(
        scope.store.begin,
        body=body,
        provenance=meta,
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


def response_text_received(text: str):
    """Observación de texto devuelto por el proveedor, no de HTTP completo.

    Solo corre bajo captura real, best-effort y sin afectar parseo o RNG.
    """
    scope = _ACTIVE.get()
    if scope is not None and scope.current_id is not None:
        _try(scope.store.record_response, scope.current_id, text)


def response_phase(phase: str):
    """Etiquetar una fase sin conservar mensajes de excepción no confiables."""
    scope = _ACTIVE.get()
    if scope is not None and scope.current_id is not None:
        _try(scope.store.mark_response_phase, scope.current_id, phase)


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
        scope.snapshots.clear()


def observe_context(stage, context):
    """Guardar únicamente una copia efímera bajo un intento realmente activo.

    El observador no puede cambiar el contexto original, y el contenido
    intermedio no se persiste: solo cambios por ruta y referencias al código.
    """
    scope = _ACTIVE.get()
    if scope is None:
        return
    from nilo_runtime.agent.provenance import snapshot_context
    copied = _try(snapshot_context, context)
    if copied is not None:
        scope.snapshots.append((stage, copied))
