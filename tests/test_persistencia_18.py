"""Nilo 0.7 etapa 18: transacciones, backups y save v5 histórico.

No se utiliza una partida personal ni una API; cada archivo es temporal.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch

from nilo import Simulation
from nilo_runtime.core.state import StateSchemaError, SAVE_SCHEMA_VERSION
from nilo_runtime.storage.backups import (
    BackupError, inspect_backup, backup_to_new_path, restore_as_copy,
    backup_file,
)
from nilo_runtime.storage.migrations import migration_path


class Storage18(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-storage-18-")
        self.root=Path(self.temp.name)
        self.file=self.root/"partida.sqlite3"
        self.sim=Simulation(db_path=self.file,world_seed=7321,rng_seed=9252)

    def tearDown(self):
        try:self.sim.conn.close()
        finally:self.temp.cleanup()

    def payload(self):
        with sqlite3.connect(self.file) as db:
            return db.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]

    def test_snapshot_entropy_and_history_uses_one_commit(self):
        p=self.sim.s["person"]
        p["research"].append({
            "id":"inv-integridad","question":"¿Resiste la piedra?",
            "hypothesis":"Podría ser dura","state":"abierta","evidence":[]})
        self.sim.write()
        original=self.payload()
        manifest=inspect_backup(self.file)
        self.assertEqual(manifest["snapshot_sha256"],
                         hashlib.sha256(original.encode("utf-8")).hexdigest())
        self.assertEqual(manifest["schema_version"],SAVE_SCHEMA_VERSION)
        self.assertTrue(manifest["entropy_bound"])
        self.assertIsNotNone(self.sim.archive.get("research","inv-integridad"))

    def test_failed_entropy_update_rolls_back_every_sql_write(self):
        saved=self.payload()
        prior_update=self.sim.s.get("updated")
        old_cache=set(self.sim.archive._sync_seen_static)
        old_digest=dict(self.sim.archive._sync_digest)
        note={"id":"jour-transaction","text":"Esta entrada se generó antes del fallo.",
              "when":"Día 1","origin":"llm"}
        self.sim.s["journal"].append(note)
        with patch("nilo_runtime.storage.repository.persist_entropy",
                   side_effect=RuntimeError("checkpoint roto")):
            with self.assertRaisesRegex(RuntimeError,"checkpoint roto"):
                self.sim.write()
        self.assertEqual(self.payload(),saved)
        self.assertEqual(self.sim.s.get("updated"),prior_update)
        self.assertEqual(self.sim.archive._sync_seen_static,old_cache)
        self.assertEqual(self.sim.archive._sync_digest,old_digest)
        self.assertFalse(self.sim.conn.in_transaction)
        self.assertIsNone(self.sim.archive.get("journal","jour-transaction"))
        # La caché no adelanta el historial tras el rollback: reintentar guarda.
        self.sim.write()
        self.assertIsNotNone(self.sim.archive.get("journal","jour-transaction"))

    def test_non_finite_extra_value_does_not_leave_ghost_history(self):
        before=self.payload()
        self.sim.s["metadata_extra"]={"sin_instrumentar":float("nan")}
        with self.assertRaises(ValueError):
            self.sim.write()
        self.assertEqual(before,self.payload())
        self.sim.s.pop("metadata_extra")
        self.sim.write()

    def test_multiple_writes_do_not_repeat_mutable_revisions(self):
        project={"id":"pr-archive","title":"Ensayar la piedra","status":"activo",
                 "progress":15,"verified_results":[]}
        self.sim.s["person"]["projects"].append(project)
        self.sim.write()
        with sqlite3.connect(self.file) as db:
            def revisions():
                return db.execute(
                    "SELECT COUNT(*) FROM history_revisions "
                    "WHERE category='project' AND item_id='pr-archive'").fetchone()[0]
            self.assertEqual(revisions(),1)
            self.sim.write()
            self.assertEqual(revisions(),1)
            project["progress"]=25
            self.sim.write()
            self.assertEqual(revisions(),2)
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM history WHERE category='project' "
                "AND item_id='pr-archive'").fetchone()[0],1)

    def test_static_journal_incremental_sync_keeps_ids(self):
        notes=self.sim.s["journal"]
        for i in range(60):
            notes.append({"id":f"j-{i}","when":"Día 1","text":f"Nota {i}"})
        self.sim.write()
        cursor=self.sim.archive._static_cursors["journal"]
        self.assertEqual(cursor[1],60)
        first_count=self.sim.archive.max_seq("journal")
        self.sim.write()
        self.assertEqual(first_count,self.sim.archive.max_seq("journal"))
        notes.append({"id":"j-extra","when":"Día 2","text":"Nueva nota"})
        self.sim.write()
        self.assertEqual(self.sim.archive.max_seq("journal"),first_count+1)

    def test_static_list_replacement_does_not_skip_new_interior_id(self):
        notes=self.sim.s["journal"]
        notes.extend([
            {"id":"j-a","when":"Día 1","text":"Primera"},
            {"id":"j-b","when":"Día 1","text":"Segunda"},
            {"id":"j-c","when":"Día 1","text":"Tercera"},
        ])
        self.sim.write()
        self.sim.s["journal"]=[
            notes[0],{"id":"j-middle","when":"Día 1","text":"Reemplazo"},notes[2]
        ]
        self.sim.write()
        self.assertIsNotNone(self.sim.archive.get("journal","j-middle"))

    def test_archive_references_persist_over_reopens(self):
        p=self.sim.s["person"]
        p["research"].append({"id":"r-owned","question":"¿Qué dureza tiene?",
                              "hypothesis":"Resistente","state":"abierta",
                              "evidence":[]})
        p["project"]={"id":"pr-owned","title":"Analizar un material",
                      "status":"activo","progress":0}
        p["agenda"].append({"id":"tar-owned","proyecto_id":"pr-owned",
                            "modo":"recordatorio","estado":"pendiente",
                            "cuando":{"tipo":"ahora"},"pasos":[]})
        self.sim.write()
        before=json.loads(self.payload())
        self.sim.conn.close()
        self.sim=Simulation(db_path=self.file)
        reopened=self.sim.s["person"]
        self.assertEqual(reopened["research"][-1]["id"],"r-owned")
        self.assertEqual(reopened["project"]["id"],"pr-owned")
        self.assertEqual(reopened["agenda"][-1]["id"],"tar-owned")
        self.assertGreaterEqual(len(self.sim.archive.recent("project",10)),1)
        self.assertGreaterEqual(len(self.sim.archive.recent("research",10)),1)
        self.assertEqual(self.sim.entropy_origin,"restored_exact")

    def test_migration_path_read_only_and_rejects_future_schema(self):
        current=deepcopy(self.sim.s)
        before=deepcopy(current)
        plan=migration_path(current)
        self.assertEqual(current,before)
        self.assertEqual(plan["origen"],SAVE_SCHEMA_VERSION)
        old=deepcopy(current)
        old["version"]=3
        self.assertEqual(migration_path(old)["destino"],5)
        self.assertTrue(migration_path(old)["reescritura_de_esquema"])
        future=deepcopy(current)
        future["version"]=6
        with self.assertRaises(StateSchemaError):
            migration_path(future)

    def test_uncommitted_review_tables_are_rolled_back_on_failed_migration(self):
        before=self.payload()
        self.sim.conn.close()
        # Simular una copia v5 con archivo de lecturas todavía no instalado.
        with sqlite3.connect(self.file) as db:
            for name in ("reviewed_entries","review_meta","observer_summaries"):
                db.execute(f"DROP TABLE {name}")
        with sqlite3.connect(self.file) as db:
            tables_before={r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        with patch("nilo_runtime.storage.migrations.migrate_state",
                   side_effect=RuntimeError("no migró")):
            with self.assertRaisesRegex(RuntimeError,"no migró"):
                Simulation(db_path=self.file)
        with sqlite3.connect(self.file) as db:
            tables_after={r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            payload=db.execute(
                "SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
        self.assertEqual(tables_before,tables_after)
        self.assertEqual(payload,before)
        self.sim=Simulation(db_path=self.file)

    def test_migration_failure_rolls_back_schema_and_snapshot(self):
        before=self.payload()
        with sqlite3.connect(self.file) as db:
            old_tables={row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        self.sim.conn.close()
        with patch("nilo_runtime.storage.migrations.migrate_state",
                   side_effect=RuntimeError("migración interrumpida")):
            with self.assertRaisesRegex(RuntimeError,"migración interrumpida"):
                Simulation(db_path=self.file)
        with sqlite3.connect(self.file) as db:
            self.assertEqual(before,db.execute(
                "SELECT payload FROM snapshot WHERE id=1").fetchone()[0])
            self.assertEqual(old_tables,{row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")})
        self.sim=Simulation(db_path=self.file)


class Backups18(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="nilo-backup-18-")
        self.root=Path(self.temp.name)
        self.db=self.root/"live.sqlite3"
        self.sim=Simulation(db_path=self.db,rng_seed=123)

    def tearDown(self):
        self.sim.conn.close()
        self.temp.cleanup()

    def test_wal_backup_has_exact_latest_snapshot_and_rng(self):
        self.sim.s["person"]["clock_minutes"]=37
        self.sim.s["person"]["knowledge"]["piedra"]= "Roca observada."
        self.sim.write()
        with sqlite3.connect(self.db) as conn:
            live=conn.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
        destination=self.root/"backup.sqlite3"
        actual=backup_to_new_path(self.sim.conn,destination)
        self.assertTrue(destination.exists())
        self.assertEqual(actual,inspect_backup(destination))
        with sqlite3.connect(destination) as conn:
            payload=conn.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
        self.assertEqual(live,payload)
        self.assertEqual(actual["simulated_minutes"],37)
        self.assertTrue(actual["entropy_bound"])

    def test_backup_does_not_overwrite_existing_file(self):
        target=self.root/"ya-existe.sqlite3"
        target.write_bytes(b"INTOCABLE")
        with self.assertRaises(FileExistsError):
            backup_to_new_path(self.sim.conn,target)
        self.assertEqual(target.read_bytes(),b"INTOCABLE")
        self.assertFalse(list(self.root.glob(".nilo-backup-*")))

    def test_reject_backup_with_pending_transactions(self):
        self.sim.conn.execute("INSERT OR IGNORE INTO read_items(category,seq) "
                              "VALUES ('journal',12345)")
        with self.assertRaises(BackupError):
            backup_to_new_path(self.sim.conn,self.root/"unsafe.sqlite3")
        self.sim.conn.rollback()
        self.assertFalse((self.root/"unsafe.sqlite3").exists())

    def test_restore_as_new_copy_keeps_source_and_references(self):
        source=self.root/"backup.sqlite3"
        backup_to_new_path(self.sim.conn,source)
        manifest_before=inspect_backup(source)
        restored=self.root/"restore.sqlite3"
        recovered=restore_as_copy(source,restored)
        self.assertEqual(recovered,manifest_before)
        self.assertEqual(inspect_backup(source),manifest_before)
        sim=Simulation(db_path=restored)
        try:
            self.assertEqual(sim.entropy_origin,"restored_exact")
            self.assertEqual(sim.s["world"]["seed"],self.sim.s["world"]["seed"])
        finally:sim.conn.close()

    def test_restore_cannot_overwrite_source_or_existing_destination(self):
        backup=self.root/"backup.sqlite3"
        backup_to_new_path(self.sim.conn,backup)
        existing=self.root/"private.sqlite3"
        existing.write_bytes(b"KEEP")
        with self.assertRaises(BackupError):
            restore_as_copy(backup,backup)
        with self.assertRaises(FileExistsError):
            restore_as_copy(backup,existing)
        self.assertEqual(existing.read_bytes(),b"KEEP")

    def test_online_backup_from_readonly_wal_connection(self):
        self.sim.s["person"]["clock_minutes"]=49
        self.sim.write()
        target=self.root/"respaldo-online.sqlite3"
        report=backup_file(self.db,target)
        self.assertEqual(report["simulated_minutes"],49)
        self.assertEqual(inspect_backup(target),report)
        self.assertFalse(self.sim.conn.in_transaction)

    def test_console_backup_and_restore_are_safe(self):
        tool=Path(__file__).resolve().parent.parent/"tools/backup_partida_18.py"
        backup=self.root/"desde-cli.sqlite3"
        restored=self.root/"desde-cli-restaurado.sqlite3"
        for action,args in (
            ("respaldar",[str(self.db),str(backup)]),
            ("inspeccionar",[str(backup)]),
            ("restaurar",[str(backup),str(restored)]),
        ):
            with self.subTest(action=action):
                p=subprocess.run([sys.executable,str(tool),action,*args],
                                 capture_output=True,text=True,timeout=25)
                self.assertEqual(p.returncode,0,p.stderr)
                result=json.loads(p.stdout)
                self.assertEqual(result["operacion"],action)
                self.assertEqual(result["resultado"]["schema_version"],5)
        self.assertEqual(inspect_backup(backup),inspect_backup(restored))
        denied=subprocess.run(
            [sys.executable,str(tool),"restaurar",str(backup),str(restored)],
            capture_output=True,text=True,timeout=25)
        self.assertNotEqual(denied.returncode,0)
        self.assertIn("No se modificó",denied.stderr)

    def test_unicode_and_space_path_uses_portable_sqlite_uri(self):
        backup=self.root/"Mi partida de Nilo — año 2026.sqlite3"
        result=backup_file(self.db,backup)
        self.assertTrue(backup.exists())
        self.assertEqual(inspect_backup(backup),result)
        other=self.root/"Partida restaurada ñ.sqlite3"
        self.assertEqual(restore_as_copy(backup,other),result)

    def test_corrupt_snapshot_detected_before_restore(self):
        copy=self.root/"corrupt.sqlite3"
        backup_to_new_path(self.sim.conn,copy)
        with sqlite3.connect(copy) as conn:
            conn.execute("UPDATE snapshot SET payload='{}' WHERE id=1")
        with self.assertRaises((BackupError,StateSchemaError)):
            inspect_backup(copy)
        dest=self.root/"not-restored.sqlite3"
        with self.assertRaises((BackupError,StateSchemaError)):
            restore_as_copy(copy,dest)
        self.assertFalse(dest.exists())

    def test_entropy_snapshot_mismatch_detected(self):
        copy=self.root/"modified.sqlite3"
        backup_to_new_path(self.sim.conn,copy)
        with sqlite3.connect(copy) as conn:
            original=conn.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0]
            parsed=json.loads(original)
            parsed["speed"]=3
            conn.execute("UPDATE snapshot SET payload=? WHERE id=1",
                         (json.dumps(parsed,ensure_ascii=False),))
        with self.assertRaisesRegex(BackupError,"RNG"):
            inspect_backup(copy)


if __name__=="__main__":
    unittest.main()
