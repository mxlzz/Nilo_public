"""Backups SQLite consistentes, verificables y restaurables como NUEVA copia.

Nunca se lee el archivo vivo con copyfile: la base opera en WAL. backup()
incluye un snapshot consistente incluso si hay páginas en el WAL.
No existe una operación destructiva que sobrescriba la partida de origen.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile
from urllib.parse import quote

from nilo_runtime.core.state import validate_loaded_envelope

class BackupError(RuntimeError):
    """Se impidió una operación que podía perder una partida."""


def _readonly(path):
    uri="file:"+quote(str(Path(path).resolve()),safe="/")+ "?mode=ro"
    return sqlite3.connect(uri,uri=True,timeout=15)


def inspect_backup(path):
    """Inspeccionar sin mutar. Incluye estado, identidades RNG y cardinalidad."""
    path=Path(path)
    if not path.is_file():
        raise BackupError("No existe el archivo de partida.")
    with closing(_readonly(path)) as conn:
        errors=conn.execute("PRAGMA quick_check").fetchall()
        if errors != [("ok",)]:
            raise BackupError("SQLite falló quick_check: no se puede restaurar.")
        try:
            stored=conn.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()
        except sqlite3.DatabaseError as exc:
            raise BackupError("No existe una tabla de snapshot válida.") from exc
        if stored is None:
            raise BackupError("La partida no contiene snapshot.")
        encoded=stored[0]
        try:
            state=json.loads(encoded)
            validate_loaded_envelope(state)
        except (ValueError,TypeError) as exc:
            raise BackupError("Snapshot corrupto; no se generó un backup restaurable.") from exc
        # StateSchemaError es una incompatibilidad legítima, no se reescribe.
        checksum=hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        try:
            record=conn.execute(
                "SELECT payload FROM runtime_entropy WHERE id=1").fetchone()
        except sqlite3.OperationalError:
            record=None   # Backups anteriores a la instrumentación RNG.
        if record is not None:
            try:
                entropy=json.loads(record[0])
            except (ValueError,TypeError) as exc:
                raise BackupError("Checkpoint de entropía ilegible.") from exc
            if entropy.get("snapshot_sha256")!=checksum:
                raise BackupError(
                    "Snapshot y estado RNG no corresponden a la misma transacción.")
        def count(table):
            try:
                return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            except sqlite3.OperationalError:
                return 0
        return {"snapshot_sha256":checksum,
                "schema_version":state.get("version",0),
                "simulated_minutes":state["person"].get("clock_minutes"),
                "history_records":count("history"),
                "history_revisions":count("history_revisions"),
                "relations":count("record_links"),
                "timeline_checkpoints":count("timeline_checkpoints"),
                "entropy_bound":record is not None}


def backup_to_new_path(source_conn, destination):
    """Congelar conexión COMMITIDA y publicar backup solo si destino no existe.

    La creación se hace en temporal del mismo directorio y se publica
    mediante hard link sin reemplazar un archivo ajeno; ante fallo se borra.
    """
    if source_conn.in_transaction:
        raise BackupError(
            "Hay cambios sin confirmar; guardá la partida antes de respaldarla.")
    target=Path(destination)
    if target.exists():
        raise FileExistsError("El archivo destino ya existe; no se sobrescribe.")
    target.parent.mkdir(parents=True,exist_ok=True)
    handle,temp=tempfile.mkstemp(prefix=".nilo-backup-",suffix=".sqlite3",
                                dir=target.parent)
    os.close(handle)
    tmp=Path(temp)
    try:
        with closing(sqlite3.connect(tmp)) as destination_conn:
            source_conn.backup(destination_conn)
            destination_conn.commit()
        manifest=inspect_backup(tmp)
        # No usar os.replace: reemplazaría un save existente en POSIX.
        os.link(tmp,target)
        return manifest
    finally:
        tmp.unlink(missing_ok=True)


def restore_as_copy(source, destination):
    """Restauración no destructiva: conserva el backup y crea OTRO archivo."""
    source=Path(source).resolve()
    if source==Path(destination).resolve():
        raise BackupError("El backup y su restauración no pueden ser el mismo archivo.")
    before=inspect_backup(source)
    with closing(_readonly(source)) as conn:
        after=backup_to_new_path(conn,destination)
    if after!=before:
        # No exponer como restauración correcta una copia parcial.
        # El destino sólo se creó por esta función, nunca existía antes.
        Path(destination).unlink(missing_ok=True)
        raise BackupError("La copia no coincide con el backup de origen.")
    return after


def backup_file(source, destination):
    """Backup online de una partida SQLite en WAL, incluso con Nilo abierto.

    Se usa una conexión nueva en modo lectura. No exigimos igualdad temporal
    con un SELECT previo: la simulación puede confirmar otro estado mientras
    se ejecuta el backup. La copia resultante sí se valida internamente.
    """
    source=Path(source).resolve()
    inspect_backup(source)
    if source==Path(destination).resolve():
        raise BackupError("Origen y destino no pueden coincidir.")
    with closing(_readonly(source)) as conn:
        return backup_to_new_path(conn,destination)
