"""Persistencia de checkpoints físicos de Nilo; no importa replay ni UI.

La tabla y el contenido JSON binario son idénticos a 0.6.4/etapa 04.
Esta capa no necesita iniciar simulaciones o recorrer sesiones históricas.
"""
from __future__ import annotations
import hashlib
import json
import random
import time
import zlib

FORMAT = "nilo-history-v1"
MAX_DECOMPRESSED = 100 * 1024 * 1024


def _tuples(value):
    if isinstance(value, list):
        return tuple(_tuples(x) for x in value)
    return value


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _decompress(data):
    decoder = zlib.decompressobj()
    raw = decoder.decompress(data, MAX_DECOMPRESSED + 1)
    if len(raw) > MAX_DECOMPRESSED or decoder.unconsumed_tail:
        raise ValueError("El checkpoint supera el tamaño máximo de seguridad.")
    raw += decoder.flush(MAX_DECOMPRESSED + 1 - len(raw))
    if len(raw) > MAX_DECOMPRESSED or not decoder.eof:
        raise ValueError("Checkpoint truncado o demasiado grande.")
    return json.loads(raw)


class TimelineStore:
    def __init__(self, conn):
        self.conn = conn
        self.conn.execute("""CREATE TABLE IF NOT EXISTS timeline_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL CHECK(kind IN ('decision','action')),
            clock_minutes REAL NOT NULL,
            day_label TEXT NOT NULL,
            engine_version TEXT NOT NULL,
            history_seq INTEGER NOT NULL,
            source TEXT NOT NULL,
            operation TEXT,
            decision_json TEXT,
            trace_call_id TEXT,
            blob BLOB NOT NULL,
            blob_sha256 TEXT NOT NULL,
            created_real REAL NOT NULL
        )""")
        # Migración compatible con mundos que ya tienen checkpoints.
        columns={row[1] for row in self.conn.execute("PRAGMA table_info(timeline_checkpoints)")}
        if "trace_call_id" not in columns:
            self.conn.execute("ALTER TABLE timeline_checkpoints ADD COLUMN trace_call_id TEXT")
        self.conn.execute("CREATE INDEX IF NOT EXISTS timeline_by_clock ON timeline_checkpoints(clock_minutes,id)")
        # Solo índice técnico: no forma parte del estado, cuaderno o percepción.
        self.conn.execute("""CREATE TABLE IF NOT EXISTS lab_journal_trace (
            journal_id TEXT PRIMARY KEY,
            trace_call_id TEXT NOT NULL,
            decision_checkpoint_id INTEGER
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS lab_action_links (
            action_checkpoint_id INTEGER PRIMARY KEY,
            journal_id TEXT NOT NULL,
            trace_call_id TEXT NOT NULL
        )""")
        self.conn.execute("""CREATE INDEX IF NOT EXISTS lab_action_links_by_call
            ON lab_action_links(trace_call_id,action_checkpoint_id)""")

    def link_journal(self, journal_id, trace_call_id, decision_checkpoint_id=None):
        """Vincular la nota real del plan con el intento LLM aceptado.

        Una misma nota del cuaderno puede alimentar varias operaciones; las
        operaciones automáticas que no tengan esa nota quedan sin atribución.
        """
        if not isinstance(journal_id,str) or not journal_id:
            raise ValueError("Nota sin ID de origen")
        if (not isinstance(trace_call_id,str) or len(trace_call_id)!=32
                or any(c not in "0123456789abcdef" for c in trace_call_id)):
            raise ValueError("Identificador de llamada inválido")
        self.conn.execute("""INSERT OR IGNORE INTO lab_journal_trace (
            journal_id,trace_call_id,decision_checkpoint_id) VALUES (?,?,?)""",
            (journal_id,trace_call_id,decision_checkpoint_id))

    def record(self, kind, state, rng, *, source="", action=None, decision=None,
               engine_version="", entropy=None, trace_call_id=None):
        if kind not in ("decision", "action"):
            raise ValueError("Tipo de punto histórico desconocido.")
        body = {"format": FORMAT, "state": state,
                "rng_state": rng.getstate(),
                "global_rng_state": random.getstate()}
        if entropy is not None:
            # Checkpoints modernos guardan la identidad de la operación,
            # además del RNG del agente. Los checkpoints previos no se tocan.
            body["entropy_state"] = entropy.to_record(agent_rng=rng)
        raw = _json(body).encode("utf-8")
        # Un checkpoint enorme no debe detener la vida de Nilo: registrar un
        # error observacional fuera de esta ruta si se supera el presupuesto.
        if len(raw) > MAX_DECOMPRESSED:
            return None
        packed = zlib.compress(raw, level=3)
        row = self.conn.execute("SELECT COALESCE(MAX(seq),0) FROM history").fetchone()
        minute = float(state["person"]["clock_minutes"])
        day = int(minute // 1440) + 1
        hh = int(minute % 1440) // 60
        mm = int(minute % 60)
        c = self.conn.execute("""INSERT INTO timeline_checkpoints(
            kind, clock_minutes, day_label, engine_version, history_seq,
            source, operation, decision_json, trace_call_id, blob, blob_sha256, created_real
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            kind, minute, f"Día {day} · {hh:02d}:{mm:02d}", engine_version or "sin_version",
            int(row[0]), source or "", (action or {}).get("op"),
            _json(decision if decision is not None else action) if decision is not None or action is not None else None,
            trace_call_id if kind=="decision" else None,
            packed, hashlib.sha256(packed).hexdigest(), time.time()
        ))
        ident=int(c.lastrowid)
        if kind=="action" and isinstance(action,dict):
            # Solo las operaciones que pertenecen explícitamente al cuaderno
            # del plan LLM, no las acciones de agenda/rutina/motor/espera.
            journal=action.get("_journal_id")
            origin=action.get("_origin","llm")
            if (isinstance(journal,str) and journal
                    and origin not in ("agenda","rutina","motor","espera")
                    and source not in ("agenda","rutina","motor","espera")):
                self.conn.execute("""INSERT OR IGNORE INTO lab_action_links (
                    action_checkpoint_id,journal_id,trace_call_id)
                    SELECT ?,journal_id,trace_call_id FROM lab_journal_trace
                    WHERE journal_id=?""",(ident,journal))
        return ident


