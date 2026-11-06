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
            blob BLOB NOT NULL,
            blob_sha256 TEXT NOT NULL,
            created_real REAL NOT NULL
        )""")
        self.conn.execute("CREATE INDEX IF NOT EXISTS timeline_by_clock ON timeline_checkpoints(clock_minutes,id)")

    def record(self, kind, state, rng, *, source="", action=None, decision=None,
               engine_version="", entropy=None):
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
            source, operation, decision_json, blob, blob_sha256, created_real
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
            kind, minute, f"Día {day} · {hh:02d}:{mm:02d}", engine_version or "sin_version",
            int(row[0]), source or "", (action or {}).get("op"),
            _json(decision if decision is not None else action) if decision is not None or action is not None else None,
            packed, hashlib.sha256(packed).hexdigest(), time.time()
        ))
        return int(c.lastrowid)


