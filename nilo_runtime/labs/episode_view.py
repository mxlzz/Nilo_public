"""Recorrido histórico y ficha de episodio, siempre en lectura local.

Reutiliza el catálogo de checkpoints, el archivo de solicitudes HTTP y las
uniones *exactas* de etapa 02. La proximidad horaria jamás crea una relación.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from historical_lab import catalog, select_event
from nilo_runtime.labs.episode_links import (
    inspect_episode, valid_planned_action_checkpoint,
)
from nilo_runtime.storage.llm_requests import RequestTraceStore

_EVENT = re.compile(r"(?:cp|hist):[0-9]{1,14}\Z")
_CALL = re.compile(r"call:[0-9a-f]{32}\Z")
_MAX_ATTEMPTS = 20
_MAX_ITEMS = 12000


def _readonly(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro",
                         uri=True, timeout=1)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    return db


def _table(db, name):
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)).fetchone() is not None


def _columns(db, table):
    return {row[1] for row in db.execute("PRAGMA table_info(" + table + ")")}


def _requests_db(world):
    sidecar = RequestTraceStore.for_world(world).path
    if not sidecar.is_file():
        return None
    return _readonly(sidecar)


def _calls(world):
    """Metadatos mínimos por intento, no se devuelven cuerpos aquí."""
    with closing(_requests_db(world)) if RequestTraceStore.for_world(world).path.is_file() else _null_db() as db:
        if db is None or not _table(db, "llm_requests"):
            return []
        rows = db.execute(
            """SELECT call_id,attempt_id,attempt_ordinal,purpose,provider,model,
                      simulated_at,started_utc,status,body_bytes
               FROM llm_requests
               WHERE purpose='deliberacion' ORDER BY rowid"""
        ).fetchall()
        return [dict(row) for row in rows]


class _null_db:
    def __enter__(self):
        return None
    def __exit__(self, *args):
        return False


def list_episodes(world, *, limit=_MAX_ITEMS):
    """Lista de episodios: deliberación, actividad independiente y huérfanos.

    Una acción con lab_action_links se muestra dentro de su deliberación.
    Un evento sin unión exacta queda independiente; no se inventa su causa.
    """
    if type(limit) is not int or not 1 <= limit <= _MAX_ITEMS:
        raise ValueError("Límite de episodios inválido")
    world = Path(world).resolve()
    original = catalog(world, limit=limit)
    action_links = []
    traced_calls = set()
    checkpoint_calls = set()
    archived_decisions = []
    with closing(_readonly(world)) as db:
        if (_table(db,"lab_action_links") and
                _table(db,"timeline_checkpoints")):
            action_links = list(db.execute(
                """SELECT l.action_checkpoint_id,l.trace_call_id,
                          l.journal_id,t.source,t.decision_json
                   FROM lab_action_links l
                   JOIN timeline_checkpoints t
                     ON t.id=l.action_checkpoint_id
                   WHERE t.kind='action'"""))
        if _table(db, "timeline_checkpoints") and (
                "trace_call_id" in _columns(db, "timeline_checkpoints")):
            checkpoint_calls.update(
                row[0] for row in db.execute(
                    "SELECT trace_call_id FROM timeline_checkpoints "
                    "WHERE kind='decision' AND trace_call_id IS NOT NULL")
            )
            traced_calls.update(checkpoint_calls)
        if _table(db, "history"):
            for row in db.execute(
                    "SELECT seq,simulated_at,payload FROM history "
                    "WHERE category='llm_decision' ORDER BY seq"):
                try:
                    data = json.loads(row[2])
                except (TypeError, ValueError):
                    continue
                if not isinstance(data,dict):
                    continue
                call = data.get("trace_call_id")
                if isinstance(call,str):
                    traced_calls.add(call)
                archived_decisions.append((int(row[0]),row[1],data,call))

    linked_action_ids = {int(row[0]) for row in action_links
                         if row[1] in traced_calls
                         and valid_planned_action_checkpoint(
                             row[3],row[4],row[2])}
    entries = []
    for item in original["entries"]:
        kind, number = item["id"].split(":", 1)
        if item["kind"] in ("decision", "llm_decision"):
            is_llm = (item["kind"]=="llm_decision"
                      or item.get("source")=="llm")
            entries.append({**item,
                            "episode_kind": "deliberation" if is_llm else "independent_decision",
                            "relation": "recorded_decision"})
        elif item["kind"] == "action":
            if int(number) in linked_action_ids:
                continue
            entries.append({**item, "episode_kind": "independent",
                            "relation": "no_exact_llm_link"})
        elif kind == "hist":
            # Registros anteriores al primer checkpoint: no ocultar una
            # anomalía por ausencia de infraestructura.
            entries.append({**item, "episode_kind": "legacy",
                            "relation": "legacy_record_without_checkpoint"})

    # Algunos registros se archivan ANTES de crear el checkpoint; si la
    # aplicación se interrumpe entre ambos commits la decisión es auténtica
    # aunque el historial restaurable no tenga un punto equivalente.
    # Mostrarla sin fingir que existe un snapshot anterior.
    visible = {item["id"] for item in entries}
    for seq,stamp,archive,call in archived_decisions:
        ident = "hist:" + str(seq)
        if ident in visible or (isinstance(call,str) and call in checkpoint_calls):
            continue
        decision = archive.get("decision")
        title = (decision.get("objetivo") or decision.get("pregunta")
                 or "Decisión archivada sin checkpoint") if isinstance(decision,dict) else (
                 "Decisión archivada sin checkpoint")
        entries.append({
            "id":ident,
            "kind":"llm_decision",
            "episode_kind":"deliberation",
            "relation":"archived_without_decision_checkpoint",
            "op":"decisión LLM",
            "title":str(title)[:110],
            "label":stamp,
            "replayable":False,
            "timeline_position":"archive_sequence_verified",
        })

    # Los checkpoints llevan el secuencial del historial justo antes de
    # capturar el estado; los registros hist:seq llevan su propio secuencial.
    # Este orden es verificable y permite intercalar archivos sin checkpoint.
    # Consultas sin ancla se agregan después, sin inventar posición temporal.
    def history_order(item):
        ident=item["id"]
        if ident.startswith("hist:"):
            return (int(ident.split(":",1)[1]), 0, 0)
        if ident.startswith("cp:"):
            seq=item.get("history_seq")
            return (int(seq) if isinstance(seq,int) else 10**15,
                    1,int(ident.split(":",1)[1]))
        return (10**15,2,0)
    entries.sort(key=history_order)

    grouped = {}
    for attempt in _calls(world):
        call_id = attempt["call_id"]
        if not isinstance(call_id, str) or not re.fullmatch(r"[0-9a-f]{32}", call_id):
            continue
        grouped.setdefault(call_id, []).append(attempt)
    # Una consulta sin decisión no puede ordenarse con certeza dentro del
    # reloj simulado: se muestra como episodio sin posición verificada.
    for call_id, attempts in grouped.items():
        if call_id in traced_calls:
            continue
        last = attempts[-1]
        entries.append({
            "id": "call:" + call_id,
            "kind": "llm_request",
            "episode_kind": "unlinked_call",
            "relation": "no_archived_decision",
            "label": last["simulated_at"] or last["started_utc"],
            "title": "Consulta al LLM sin decisión archivada",
            "op": "consulta LLM",
            "replayable": False,
            "attempt_count": len(attempts),
            "timeline_position": "not_verified",
            "failed": all(a["status"] not in ("accepted", "response_received")
                          for a in attempts),
        })

    return {
        "entries": entries[-limit:],
        "history_rows": original["history_rows"],
        "checkpoint_count": original["checkpoint_count"],
        "has_snapshots": original["has_snapshots"],
        "source": original["source"],
        "sidecar_available": RequestTraceStore.for_world(world).path.is_file(),
        "limitations": [
            "Los intentos sin decisión archivada no tienen ubicación temporal "
            "verificada dentro de los checkpoints.",
            "Las acciones sin unión exacta se muestran por separado; "
            "no significa que nunca hayan sido deliberadas.",
            "Una reproducción utiliza el motor instalado y no garantiza "
            "la respuesta original del proveedor.",
        ],
    }


def _attempts_for(world, call_id):
    result = []
    with closing(_requests_db(world)) if RequestTraceStore.for_world(world).path.is_file() else _null_db() as db:
        if db is None or not _table(db, "llm_requests"):
            return result, False
        rows = db.execute(
            """SELECT attempt_id,attempt_ordinal,status,provider,model,
                      body_sha256,body_bytes,body,started_utc,simulated_at
               FROM llm_requests WHERE purpose='deliberacion' AND call_id=?
               ORDER BY attempt_ordinal LIMIT ?""", (call_id, _MAX_ATTEMPTS + 1)
        ).fetchall()
    truncated = len(rows) > _MAX_ATTEMPTS
    store = RequestTraceStore.for_world(world)
    for row in rows[:_MAX_ATTEMPTS]:
        body = row["body"]
        if (hashlib.sha256(body).hexdigest() != row["body_sha256"]
                or len(body) != row["body_bytes"]):
            raise ValueError("La solicitud HTTP no supera su control de integridad")
        item = {key:row[key] for key in row.keys() if key!="body"}
        response = store.response_for(item["attempt_id"])
        item["response"] = response
        item["matched_by"] = "call_id"
        result.append(item)
    return result, truncated


def get_episode(world, identifier, *, viewer_world=None):
    """Ficha progresiva; nunca abre una ruta elegida por el navegador."""
    if not isinstance(identifier, str) or not (
            _EVENT.fullmatch(identifier) or _CALL.fullmatch(identifier)):
        raise ValueError("Identificador de episodio inválido")
    world = Path(world).resolve()
    event = None
    trace_id = None
    if identifier.startswith("call:"):
        trace_id = identifier[5:]
    else:
        event = select_event(world, identifier)
        if identifier.startswith("cp:"):
            cp_id = int(identifier.split(":", 1)[1])
            with closing(_readonly(world)) as db:
                if (_table(db, "timeline_checkpoints") and
                        "trace_call_id" in _columns(db, "timeline_checkpoints")):
                    row = db.execute(
                        "SELECT trace_call_id FROM timeline_checkpoints WHERE id=?",
                        (cp_id,)).fetchone()
                    trace_id = row[0] if row is not None else None
                if trace_id is None and _table(db, "lab_action_links"):
                    row = db.execute(
                        """SELECT l.trace_call_id,l.journal_id,
                                  t.source,t.decision_json
                           FROM lab_action_links l
                           JOIN timeline_checkpoints t
                             ON t.id=l.action_checkpoint_id
                           WHERE l.action_checkpoint_id=?
                             AND t.kind='action'""",
                        (cp_id,)).fetchone()
                    if row and valid_planned_action_checkpoint(
                            row[2],row[3],row[1]):
                        trace_id = row[0]
        elif event["kind"] == "llm_decision":
            payload = event.get("historical")
            if isinstance(payload, dict):
                trace_id = payload.get("trace_call_id")
    if trace_id is not None and not re.fullmatch(r"[0-9a-f]{32}", trace_id):
        trace_id = None
    linked = inspect_episode(world, trace_id) if trace_id else None
    attempts, attempt_limit = _attempts_for(world, trace_id) if trace_id else ([], False)
    if identifier.startswith("call:") and not attempts and not (
            linked and linked["archived_decisions"]):
        raise ValueError("Consulta no encontrada en esta partida")
    if event and event["kind"] == "decision":
        decision = event.get("command")
    elif event and event["kind"] == "llm_decision":
        decision = (event.get("historical") or {}).get("decision")
    elif linked and linked["archived_decisions"]:
        decision = linked["archived_decisions"][-1]["decision"]
    else:
        decision = None
    if event and event["kind"] == "action":
        op = event.get("op")
        kind = "action"
    elif decision is not None or trace_id:
        op = "deliberación"
        kind = "deliberation"
    else:
        op = event.get("kind") if event else "sin registro"
        kind = "legacy"
    related = linked.get("related_records") if linked else None
    limits = list(linked.get("limitations", [])) if linked else [
        "No hay un ID de deliberación comprobado para este evento"]
    if attempt_limit:
        limits.append("Límite de intentos mostrados alcanzado")
    if trace_id and not attempts:
        limits.append("El cuerpo HTTP original no está disponible en la sidecar")
    if event and event["kind"] == "action" and trace_id is None:
        limits.append("El origen de la acción no está vinculado a una deliberación específica")
    same_world = (viewer_world is not None and
                  Path(viewer_world).resolve() == world)
    return {
        "id": identifier, "kind": kind, "label": (
            event.get("label") if event else
            attempts[0].get("simulated_at") or attempts[0].get("started_utc")
            if attempts else ""),
        "operation": op,
        "trace_call_id": trace_id,
        "recorded_event": event,
        "decision": decision,
        "attempts": attempts,
        "open_in_llm_viewer": same_world,
        "linked": linked,
        "related": related,
        "limitations": list(dict.fromkeys(limits)),
        "fidelity": {
            "recorded": "Datos originales archivados; ausencia no equivale a un hecho negativo",
            "interpretation": "La secuencia observada no demuestra causalidad del razonamiento del LLM",
            "next_turn": "Evidencia registrada no implica que se haya entregado al siguiente prompt",
        },
    }
