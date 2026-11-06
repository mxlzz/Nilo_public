"""Persistencia SQLite v5: escritura atómica del snapshot, historia y RNG.

Los repositorios no mutan el mundo ni crean una versión nueva del save.
La conexión pertenece a SessionLifecycle. Cualquier fallo descarta todo el
trabajo sin commit, incluidos los índices temporales de sincronización.
"""
from __future__ import annotations

import json
import sqlite3
import time

from nilo_runtime.core.state import validate_current_state
from nilo_runtime.storage.entropy import persist_entropy


class SnapshotRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def current_payload(self):
        row=self.conn.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()
        return row[0] if row else None

    def persist(self, state, *, entropy, rng, archive, sessions):
        """Una transacción para sesión, archivo, RNG y snapshot.

        La caché de History no es SQLite; solo se adelanta provisionalmente
        y se restaura si fallan serialización, índice, RNG o commit.
        """
        validate_current_state(state)
        missing=object()
        old_updated=state.get("updated",missing)
        old_seen=set(archive._sync_seen_static)
        old_digest=dict(archive._sync_digest)
        old_cursors=dict(getattr(archive,"_static_cursors",{}))
        try:
            self.conn.execute("SAVEPOINT nilo_snapshot")
            state["updated"]=time.time()
            sessions.touch(state["person"]["clock_minutes"])
            with entropy.bind():
                archive.sync(state)
            payload=json.dumps(state,ensure_ascii=False,allow_nan=False)
            persist_entropy(self.conn,entropy,rng,snapshot_payload=payload)
            self.conn.execute(
                "INSERT INTO snapshot (id,payload) VALUES (1,?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",(payload,))
            self.conn.execute("RELEASE SAVEPOINT nilo_snapshot")
            self.conn.commit()
        except BaseException:
            # Rollback de TODA la unidad de trabajo, también eventos y lecturas
            # pendientes en la conexión, para que nunca queden writes colgados.
            self.conn.rollback()
            archive._sync_seen_static=old_seen
            archive._sync_digest=old_digest
            archive._static_cursors=old_cursors
            if old_updated is missing:
                state.pop("updated",None)
            else:
                state["updated"]=old_updated
            raise
        return payload
