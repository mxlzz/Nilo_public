"""Registro técnico SQLite local de cuerpos HTTP UTF-8 para el laboratorio.

Sidecar separado de la partida: nunca expone estas cadenas al estado de Nilo.
Su consulta posterior es solo para herramientas locales explícitas, no para
el contexto LLM ni los endpoints existentes de la interfaz pública.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import secrets
import sqlite3
import threading

from nilo_runtime.agent.provenance_codec import encode_metadata, decode_metadata

MAX_RECORDS = 5000  # Retención FIFO por base; sin límite de días que borre sesiones.
_STATUSES = frozenset((
    "transport_attempted", "response_received", "accepted", "rejected",
    "http_error", "transport_error", "invalid_http_response",
))


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class RequestTraceStore:
    """Registro local a prueba de fallos: la captura es mejor-esfuerzo.

    SQLite de historia y SQLite de trazas no comparten transacción: una caída
    entre ambos commits puede dejar un intento sin decisión vinculada.
    """

    def __init__(self, path: Path):
        self.path = Path(path).resolve()
        self._lock = threading.RLock()
        self.capture_errors = 0

    @classmethod
    def for_world(cls, world_path):
        if str(world_path) == ":memory:":
            return None
        file = Path(world_path).resolve()
        return cls(file.with_name(file.stem + ".llm_requests.sqlite3"))

    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Nunca modificar permisos heredados de una carpeta de terceros.
        if not self.path.exists():
            try:
                import os
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
            except FileExistsError:
                pass
        db = sqlite3.connect(self.path, timeout=0.35)
        db.execute("PRAGMA busy_timeout=350")
        db.execute("""CREATE TABLE IF NOT EXISTS llm_requests (
            attempt_id TEXT PRIMARY KEY,
            call_id TEXT NOT NULL,
            session_id INTEGER,
            purpose TEXT NOT NULL,
            source_id TEXT,
            simulated_at TEXT,
            attempt_ordinal INTEGER NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            started_utc TEXT NOT NULL,
            finished_utc TEXT,
            status TEXT NOT NULL,
            error_http_code INTEGER,
            body BLOB NOT NULL,
            body_sha256 TEXT NOT NULL,
            body_bytes INTEGER NOT NULL
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS llm_requests_call
                      ON llm_requests(call_id, attempt_ordinal)""")
        # Migración aditiva de la base sidecar. No modifica la SQLite del mundo.
        db.execute("""CREATE TABLE IF NOT EXISTS llm_request_provenance (
            attempt_id TEXT PRIMARY KEY,
            metadata_json TEXT NOT NULL
        )""")
        db.commit()
        return db

    def begin(self, *, body, call_id, session_id, purpose, source_id,
              simulated_at, ordinal, provider, model, provenance=None):
        """Un intento HTTP = una copia literal de los bytes serializados."""
        if type(body) is not bytes:
            raise TypeError("El cuerpo de transporte debe ser bytes")
        if purpose not in ("deliberacion", "chat"):
            raise ValueError("Propósito de captura desconocido")
        if provider not in ("gemini", "groq", "openai_compatible"):
            raise ValueError("Proveedor de captura desconocido")
        attempt_id = secrets.token_hex(16)
        try:
            with self._lock, closing(self._connect()) as db:
                db.execute("""INSERT INTO llm_requests (
                    attempt_id, call_id, session_id, purpose, source_id,
                    simulated_at, attempt_ordinal, provider, model,
                    started_utc, status, body, body_sha256, body_bytes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                    attempt_id, call_id, session_id, purpose, source_id,
                    simulated_at, ordinal, provider, model, _utc(),
                    "transport_attempted", sqlite3.Binary(body),
                    hashlib.sha256(body).hexdigest(), len(body),
                ))
                # Mantener el historial más reciente por mundo. No afecta a
                # la partida ni a decisiones; las copias antiguas son privadas.
                if provenance is not None:
                    # Solo metadatos: ningún valor interno anterior al payload.
                    encoded = encode_metadata(provenance)
                    db.execute("""INSERT INTO llm_request_provenance
                                  (attempt_id,metadata_json) VALUES (?,?)""",
                               (attempt_id,encoded))
                db.execute("""DELETE FROM llm_requests WHERE rowid IN (
                    SELECT rowid FROM llm_requests ORDER BY rowid DESC
                    LIMIT -1 OFFSET ?)""", (MAX_RECORDS,))
                db.execute("""DELETE FROM llm_request_provenance
                    WHERE attempt_id NOT IN (SELECT attempt_id FROM llm_requests)""")
                db.commit()
        except (OSError, sqlite3.Error):
            self.capture_errors += 1
            raise
        return attempt_id

    def finish(self, attempt_id, status, *, code=None, only_if=None):
        if status not in _STATUSES or status == "transport_attempted":
            raise ValueError("Estado de captura inválido")
        try:
            with self._lock, closing(self._connect()) as db:
                condition = " AND status=?" if only_if is not None else ""
                params = [_utc(), status, code, attempt_id]
                if only_if is not None:
                    params.append(only_if)
                db.execute("""UPDATE llm_requests
                              SET finished_utc=?,status=?,error_http_code=?
                              WHERE attempt_id=?""" + condition, params)
                db.commit()
        except (OSError, sqlite3.Error):
            self.capture_errors += 1
            raise

    def recent(self, limit=20):
        """Consulta local; no abrir a través de HTTP hasta la etapa 05."""
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("Límite de lectura inválido")
        if not self.path.is_file():
            return []
        with self._lock, closing(sqlite3.connect(
                f"{self.path.as_uri()}?mode=ro", uri=True, timeout=0.5)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("""SELECT * FROM llm_requests
                                 ORDER BY rowid DESC LIMIT ?""", (limit,)).fetchall()
        values = [dict(row) for row in rows]
        for row in values:
            body = row["body"]
            if hashlib.sha256(body).hexdigest() != row["body_sha256"]:
                raise ValueError("La solicitud archivada no coincide con su SHA256")
            if len(body) != row["body_bytes"]:
                raise ValueError("Longitud del cuerpo de solicitud alterada")
        return values

    def provenance_for(self, attempt_id):
        """Lectura local, sin exportar ni reconstituir contexto omitido."""
        if (not isinstance(attempt_id,str) or len(attempt_id)!=32
                or any(c not in "0123456789abcdef" for c in attempt_id)):
            raise ValueError("Identificador de intento inválido")
        if not self.path.is_file():
            return None
        with self._lock, closing(sqlite3.connect(
                f"{self.path.as_uri()}?mode=ro", uri=True, timeout=0.5)) as db:
            try:
                row = db.execute("""SELECT p.metadata_json, r.body,
                                    r.body_sha256,r.body_bytes
                                    FROM llm_request_provenance p
                                    JOIN llm_requests r USING (attempt_id)
                                    WHERE p.attempt_id=?""",
                                 (attempt_id,)).fetchone()
            except sqlite3.OperationalError as exc:
                if "no such table" in str(exc):
                    return None  # Sidecar heredada sin tabla de etapa 04.
                raise
        if row is None:
            return None
        metadata, body, expected_hash, expected_size = row
        if hashlib.sha256(body).hexdigest()!=expected_hash or len(body)!=expected_size:
            raise ValueError("Cuerpo de solicitud con integridad alterada")
        return decode_metadata(metadata)
