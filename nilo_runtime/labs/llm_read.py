"""Lectura local, paginada y estrictamente read-only del visor LLM.

Esta API NO abre rutas enviadas por el navegador: la fuente es exclusivamente
la partida asociada a LabHub, y su sidecar de capturas. Sin crear tablas,
reconstruir prompts históricos ni alterar la partida en ejecución.
"""
from __future__ import annotations

from contextlib import closing
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import parse_qs

from nilo_runtime.labs.literal_segments import index_saved_attempt
from nilo_runtime.storage.llm_requests import RequestTraceStore

_ATTEMPT = re.compile(r"[0-9a-f]{32}\Z")
_PROVIDERS = ("gemini", "groq", "openai_compatible")
_PURPOSES = ("deliberacion", "chat")
_STATUSES = ("transport_attempted", "response_received", "accepted",
             "rejected", "http_error", "transport_error", "invalid_http_response")
_MAX_BODY = 1024 * 1024
_DEFAULT_LIMIT = 25
_MAX_LIMIT = 100


class ReadError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _params(raw, allowed):
    try:
        values = parse_qs(raw, keep_blank_values=True, max_num_fields=9)
    except ValueError as exc:
        raise ReadError("Parámetros inválidos") from exc
    if not set(values) <= set(allowed):
        raise ReadError("Parámetro no admitido")
    if any(len(entries) != 1 for entries in values.values()):
        raise ReadError("Parámetro repetido")
    if any(len(entries[0]) > 64 for entries in values.values()):
        raise ReadError("Parámetro demasiado largo")
    return {key: entries[0] for key, entries in values.items()}


def _positive_int(value, *, field, maximum):
    if (not isinstance(value, str) or not value.isascii()
            or not value.isdecimal() or len(value) > 19):
        raise ReadError("Parámetro inválido: " + field)
    number = int(value)
    if number <= 0 or number > maximum:
        raise ReadError("Parámetro fuera de rango: " + field)
    return number


def _metadata(row, *, has_provenance):
    return {
        "attempt_id": row["attempt_id"],
        "call_id": row["call_id"],
        "session_id": row["session_id"],
        "source_id": row["source_id"],
        "purpose": row["purpose"],
        "attempt_ordinal": row["attempt_ordinal"],
        "provider": row["provider"],
        "model": row["model"],
        "simulated_at": row["simulated_at"],
        "started_utc": row["started_utc"],
        "finished_utc": row["finished_utc"],
        "status": row["status"],
        "error_http_code": row["error_http_code"],
        "body_sha256": row["body_sha256"],
        "body_bytes": row["body_bytes"],
        "has_provenance": bool(has_provenance),
    }


class LocalLLMReadAPI:
    """Una instancia ligada a una partida del laboratorio, nunca a una URL."""

    def __init__(self, world_path):
        if world_path is None:
            self.world = None
            self.sidecar = None
        else:
            self.world = Path(world_path).resolve()
            self.sidecar = RequestTraceStore.for_world(self.world).path

    def _db(self):
        if self.sidecar is None or not self.sidecar.is_file():
            return None
        db = sqlite3.connect(self.sidecar.as_uri() + "?mode=ro",
                             uri=True, timeout=1)
        try:
            db.execute("PRAGMA query_only=ON")
            db.row_factory = sqlite3.Row
            return db
        except Exception:
            db.close()
            raise

    @staticmethod
    def _has_table(db, name):
        return db.execute("""SELECT 1 FROM sqlite_master
                             WHERE type='table' AND name=?""", (name,)).fetchone() is not None

    def list_attempts(self, raw_query=""):
        q = _params(raw_query, ("limit", "before", "provider", "purpose",
                                "status", "date", "session"))
        limit = _positive_int(q.get("limit", str(_DEFAULT_LIMIT)),
                              field="limit", maximum=_MAX_LIMIT)
        before = (_positive_int(q["before"], field="before", maximum=2**63-1)
                  if "before" in q else None)
        for name, options in (("provider", _PROVIDERS),
                              ("purpose", _PURPOSES), ("status", _STATUSES)):
            if name in q and q[name] not in options:
                raise ReadError("Filtro inválido: " + name)
        if "date" in q:
            value = q["date"]
            if len(value) != 10 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ReadError("Fecha inválida")
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ReadError("Fecha inválida") from exc
        session = (_positive_int(q["session"], field="session", maximum=2**63-1)
                   if "session" in q else None)
        filters = []
        args = []
        if before is not None:
            filters.append("r.rowid < ?")
            args.append(before)
        for key in ("provider", "purpose", "status"):
            if key in q:
                filters.append("r." + key + " = ?")
                args.append(q[key])
        if "date" in q:
            filters.append("substr(r.started_utc,1,10) = ?")
            args.append(q["date"])
        if session is not None:
            filters.append("r.session_id = ?")
            args.append(session)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        db = self._db()
        if db is None:
            return {"attempts": [], "next_before": None,
                    "available": False, "source": "local"}
        with closing(db):
            if not self._has_table(db, "llm_requests"):
                return {"attempts": [], "next_before": None,
                        "available": False, "source": "local"}
            has_prov = self._has_table(db, "llm_request_provenance")
            join = (" LEFT JOIN llm_request_provenance p"
                    " ON p.attempt_id=r.attempt_id" if has_prov else "")
            columns = "p.attempt_id AS trace_id" if has_prov else "NULL AS trace_id"
            rows = db.execute(
                "SELECT r.rowid AS ordinal_key, r.attempt_id, r.call_id,"
                " r.session_id, r.source_id, r.purpose, r.attempt_ordinal,"
                " r.provider, r.model, r.simulated_at, r.started_utc,"
                " r.finished_utc, r.status, r.error_http_code,"
                " r.body_sha256, r.body_bytes, " + columns +
                " FROM llm_requests r" + join + where +
                " ORDER BY r.rowid DESC LIMIT ?",
                (*args, limit + 1),
            ).fetchall()
        has_more = len(rows) > limit
        visible = rows[:limit]
        return {
            "attempts": [_metadata(r, has_provenance=r["trace_id"])
                         for r in visible],
            "next_before": visible[-1]["ordinal_key"] if visible and has_more else None,
            "available": True,
            "source": "local",
        }

    def _linked_record(self, *, call_id, purpose, source_id):
        """Encontrar el registro archivado de la misma partida, si existe.

        El enlace solo afirma identidad cuando coincide exactamente el ID.
        No reconstruye decisiones fallidas ni expone texto de chat/cuerpo.
        """
        if self.world is None or not self.world.is_file():
            return None
        target = call_id if purpose == "deliberacion" else source_id
        if not target:
            return None
        try:
            with closing(sqlite3.connect(self.world.as_uri()+"?mode=ro",
                                         uri=True, timeout=0.7)) as db:
                db.execute("PRAGMA query_only=ON")
                if not self._has_table(db, "history"):
                    return None
                category = "llm_decision" if purpose == "deliberacion" else "chat"
                rows = db.execute(
                    """SELECT seq,simulated_at,payload FROM history
                       WHERE category=? AND instr(payload,?)>0
                       ORDER BY seq DESC LIMIT 12""", (category, target)).fetchall()
        except sqlite3.Error:
            return None
        for seq,stamp,payload in rows:
            try:
                record=json.loads(payload)
            except (TypeError, ValueError):
                continue
            if not isinstance(record,dict):
                continue
            key = "trace_call_id" if purpose == "deliberacion" else "id"
            if record.get(key) != target:
                continue
            if purpose == "chat" and record.get("role") != "user":
                continue
            return {
                "category": category, "seq": seq, "simulated_at": stamp,
                "record_id": record.get("id"), "matched_by": key,
            }
        return None

    def get_attempt(self, raw_query=""):
        q = _params(raw_query, ("id",))
        ident = q.get("id", "")
        if not _ATTEMPT.fullmatch(ident):
            raise ReadError("Identificador de intento inválido")
        db = self._db()
        if db is None:
            raise ReadError("No hay capturas en esta partida", 404)
        with closing(db):
            if not self._has_table(db, "llm_requests"):
                raise ReadError("No hay capturas en esta partida", 404)
            has_prov = self._has_table(db, "llm_request_provenance")
            join = (" LEFT JOIN llm_request_provenance p"
                    " ON p.attempt_id=r.attempt_id" if has_prov else "")
            column = "p.metadata_json AS metadata_json" if has_prov else "NULL AS metadata_json"
            row = db.execute(
                "SELECT r.*, " + column +
                " FROM llm_requests r" + join + " WHERE r.attempt_id=?",
                (ident,),
            ).fetchone()
        if row is None:
            raise ReadError("Intento no encontrado", 404)
        entry = dict(row)
        body = entry["body"]
        if len(body) != entry["body_bytes"] or hashlib.sha256(body).hexdigest() != entry["body_sha256"]:
            raise ReadError("La captura no supera la comprobación de integridad", 409)
        if len(body) > _MAX_BODY:
            raise ReadError("Solicitud demasiado grande para consulta HTTP", 413)
        try:
            segments = index_saved_attempt(entry)
        except (UnicodeError, ValueError, KeyError, TypeError, RecursionError) as exc:
            # No confundir formatos no admitidos o corruptos con ausencia.
            raise ReadError("El contenido capturado no pudo indexarse", 422) from exc
        try:
            metadata = json.loads(entry["metadata_json"]) if entry["metadata_json"] else None
        except (ValueError, TypeError) as exc:
            raise ReadError("La procedencia almacenada no es válida", 409) from exc
        if metadata is not None and (
                not isinstance(metadata, dict) or metadata.get("schema_version") != 1):
            raise ReadError("Versión de procedencia incompatible", 409)
        result = _metadata(entry, has_provenance=metadata is not None)
        result.update({
            "body_utf8": body.decode("utf-8"),
            "messages": segments["messages"],
            "provenance": metadata,
            "provenance_status": (
                "available" if metadata is not None else "not_recorded"),
            "source": "local",
            "linked_record": self._linked_record(
                call_id=entry["call_id"], purpose=entry["purpose"],
                source_id=entry["source_id"]),
        })
        return result
