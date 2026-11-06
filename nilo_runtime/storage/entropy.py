"""Sidecar transaccional de secuencias aleatorias por partida.

Almacena estado PRNG de movimiento y generación de IDs en la MISMA SQLite del
snapshot v5, sin alterar el JSON del mundo ni la huella de replays históricos.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3

from nilo_runtime.core.identity import EntropyError, EntropySession

_MAX_STATE_BYTES = 100_000


def load_entropy(conn: sqlite3.Connection, *, world_seed: int,
                 rng_seed: int, original_snapshot: bool,
                 snapshot_payload: str | None = None,
                 allow_legacy_reimport: bool = False) -> tuple[EntropySession, str]:
    """Retorna (secuencia, origen), sin resembrar una sesión existente.

    Un save anterior a 0.7 no tiene estado PRNG: sólo es posible aplicar la
    fórmula de resembrado heredada. No se inventa su secuencia pasada.
    """
    conn.execute("""CREATE TABLE IF NOT EXISTS runtime_entropy (
        id INTEGER PRIMARY KEY CHECK(id=1),
        payload TEXT NOT NULL
    )""")
    row = conn.execute("SELECT payload FROM runtime_entropy WHERE id=1").fetchone()
    if row is None:
        return EntropySession(world_seed, rng_seed), (
            "legacy_seeded_without_history" if original_snapshot else "new_seeded"
        )
    payload = row[0]
    if not isinstance(payload, str) or len(payload) > _MAX_STATE_BYTES:
        raise EntropyError("Checkpoint RNG ilegible o demasiado grande")
    try:
        data = json.loads(payload)
    except (ValueError, TypeError) as exc:
        raise EntropyError(
            "Checkpoint RNG dañado; conservá la partida original"
        ) from exc
    hash_matches = (snapshot_payload is not None and
        data.get("snapshot_sha256") == hashlib.sha256(
            snapshot_payload.encode("utf-8")
        ).hexdigest())
    if not hash_matches:
        if allow_legacy_reimport:
            # Un fixture/save explícitamente anterior a las marcas de migración
            # puede reemplazar al snapshot anterior dentro de la misma SQLite.
            # No reclamar continuidad de un PRNG cuyo estado ya no existe.
            return EntropySession(world_seed, rng_seed), "legacy_reimported_without_history"
        raise EntropyError(
            "El snapshot cambió sin actualizar su checkpoint RNG. "
            "Guardá una copia y revisá qué versión lo modificó."
        )
    return EntropySession.from_record(data, world_seed=world_seed), "restored_exact"


def persist_entropy(conn: sqlite3.Connection, entropy: EntropySession, agent_rng,
                    *, snapshot_payload: str) -> None:
    """No hace commit: comparte transacción con el INSERT del snapshot."""
    record = entropy.to_record(agent_rng=agent_rng)
    record['snapshot_sha256'] = hashlib.sha256(snapshot_payload.encode('utf-8')).hexdigest()
    encoded = json.dumps(
        record, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    )
    if len(encoded) > _MAX_STATE_BYTES:
        raise EntropyError("Estado PRNG fuera de límite: no se guardó la partida")
    conn.execute(
        "INSERT INTO runtime_entropy (id,payload) VALUES (1,?) "
        "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
        (encoded,),
    )
