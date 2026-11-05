"""Benchmark reproducible de archivado incremental y WAL de Nilo 0.7.

No incorpora umbrales dependientes del hardware ni escribe partidas reales.
Mide en una SQLite temporal la primera sincronización, lecturas sin cambios,
append de 20 registros, tamaño y tiempo de backup/restauración.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import sys

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from archive import History
from nilo_runtime.storage.backups import backup_to_new_path,restore_as_copy


def fixture(n):
    """Historia con IDs explícitos y esquemas compatibles sin motor externo."""
    state={"journal":[{"id":f"j-{i}","when":"Día 1",
                       "text":f"Observación física {i}"} for i in range(n)],
           "news":[],"events":[],"chat":[],
           "world":{"structures":[],"retired_structures":[]},
           "person":{"research":[],"projects":[],"project":None,
                     "designs":[],"proposals":[],"action_outcomes":[],
                     "prediction_log":[],"measurements":[],"conclusions":[],
                     "waiting_history":[],"experience_summary":[],
                     "decision_history":[],"observations":[],"items":[],
                     "retired_items":[]}}
    return state


def run(count=2500):
    if count<200 or count>50000:
        raise ValueError("La cantidad de registros debe estar entre 200 y 50000.")
    with tempfile.TemporaryDirectory(prefix="nilo-bench-storage-") as td:
        root=Path(td)
        src=root/"bench.sqlite3"
        conn=sqlite3.connect(src)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE snapshot (id INTEGER PRIMARY KEY, payload TEXT)")
        # El backup exige un snapshot válido; para benchmark de archivos
        # no hace falta arrancar la simulación ni inventar física.
        sample={"version":5,"world":{},"person":{"clock_minutes":0}}
        conn.execute("INSERT INTO snapshot VALUES(1,?)",(json.dumps(sample),))
        history=History(conn)
        state=fixture(count)
        tic=time.perf_counter()
        history.sync(state)
        conn.commit()
        initial=time.perf_counter()-tic
        rows0=conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        tic=time.perf_counter()
        for _ in range(5):
            history.sync(state)
        conn.commit()
        repeat=(time.perf_counter()-tic)/5
        state["journal"].extend(
            {"id":f"j-new-{i}","when":"Día 2","text":"Registro físico añadido"}
            for i in range(20))
        tic=time.perf_counter()
        history.sync(state)
        conn.commit()
        incremental=time.perf_counter()-tic
        rows1=conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        tic=time.perf_counter()
        info=backup_to_new_path(conn,root/"backup.sqlite3")
        backup_seconds=time.perf_counter()-tic
        tic=time.perf_counter()
        restore_as_copy(root/"backup.sqlite3",root/"restaurado.sqlite3")
        restore_seconds=time.perf_counter()-tic
        result={
            "records_base":count,"records_after_append":rows1,
            "rows_initial":rows0,
            "first_sync_seconds":round(initial,6),
            "unchanged_sync_avg_seconds":round(repeat,6),
            "append_20_seconds":round(incremental,6),
            "backup_seconds":round(backup_seconds,6),
            "restore_seconds":round(restore_seconds,6),
            "sqlite_bytes":src.stat().st_size,
            "backup_bytes":(root/"backup.sqlite3").stat().st_size,
            "ids_preserved":rows0==count and rows1==count+20,
            "backup_rows_preserved":info["history_records"]==count+20,
        }
        conn.close()
        if not result["ids_preserved"] or not result["backup_rows_preserved"]:
            raise AssertionError("El benchmark detectó pérdida o duplicación de IDs.")
        return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--count",type=int,default=2500)
    args=parser.parse_args()
    print(json.dumps(run(args.count),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
