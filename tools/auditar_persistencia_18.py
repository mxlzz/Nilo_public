"""Etapa 18: auditor estático de transacciones, migración y backups."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def funcs(filename):
    tree=ast.parse((ROOT/filename).read_text("utf-8"),filename=filename)
    return {x.name for x in tree.body if isinstance(x,ast.FunctionDef)}


def inspect():
    errors=[]
    def check(path, tokens):
        source=(ROOT/path).read_text("utf-8")
        for token in tokens:
            if token not in source:
                errors.append(path+": falta "+token)
        return source

    session=check("nilo_runtime/application/session.py",
        ["BEGIN IMMEDIATE","self.conn.rollback()","migrate_state(","self.repository.persist("])
    repo=check("nilo_runtime/storage/repository.py",
        ["class SnapshotRepository","SAVEPOINT nilo_snapshot",
         "persist_entropy(","archive.sync(state)","self.conn.commit()",
         "self.conn.rollback()","archive._sync_digest=old_digest",
         "archive._static_cursors=old_cursors","allow_nan=False"])
    migrate=check("nilo_runtime/storage/migrations.py",
        ["def migration_path(","def migrate_state(",
         "validate_loaded_envelope(raw)","validate_current_state(state)"])
    archive=check("archive.py",
        ["_static_cursors","pending=records","for item in pending:",
         "self._sync_seen_static","history_revisions",
         "record_links"])
    backup=check("nilo_runtime/storage/backups.py",
        ["def backup_to_new_path(","def restore_as_copy(",
         "def inspect_backup(","source_conn.backup(",
         "source_conn.in_transaction","os.link(tmp,target)",
         "PRAGMA quick_check","snapshot_sha256"])
    if ".commit()" in (ROOT/"archive.py").read_text("utf-8").split("    def add(",1)[0]:
        errors.append("History confirma tablas antes de la migración del snapshot")
    history=(ROOT/"run_history.py").read_text("utf-8")
    if ".commit()" in history.split("    def start(",1)[0]:
        errors.append("RunHistory confirma tablas antes del snapshot")
    review=(ROOT/"review_store.py").read_text("utf-8")
    if ".commit()" in review.split("    def initialized(",1)[0]:
        errors.append("ReviewStore confirma tablas antes de migración")
    from nilo_runtime.core.state import SAVE_SCHEMA_VERSION
    if SAVE_SCHEMA_VERSION!=5:
        errors.append("Se modificó esquema v5 sin migración contractual")
    if "os.replace(" in backup or "shutil.copyfile" in backup:
        errors.append("El backup podría sobrescribir o ignorar páginas WAL")
    if "self.conn.commit()" in session.split("    def domain_snapshot",1)[0]:
        errors.append("El orquestador conserva segunda ruta de commit")
    if {"migration_path","migrate_state"}-funcs("nilo_runtime/storage/migrations.py"):
        errors.append("Migraciones fuera de propietario")
    if not (ROOT/"tests/test_persistencia_18.py").is_file():
        errors.append("Faltan tests focalizados de persistencia")
    if not (ROOT/"tools/benchmark_persistencia_18.py").is_file():
        errors.append("Falta benchmark reproducible")
    return errors


if __name__=="__main__":
    problems=inspect()
    if problems:raise SystemExit("\n".join(problems))
    print("Etapa 18: transacción única, migración v5, respaldo WAL y sincronización incremental.")
