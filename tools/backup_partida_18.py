"""Backups de Nilo 0.7 desde consola, sin sobrescribir partidas.

Ejemplos:
    python tools/backup_partida_18.py inspeccionar nilo_mundo.sqlite3
    python tools/backup_partida_18.py respaldar nilo_mundo.sqlite3 copia.sqlite3
    python tools/backup_partida_18.py restaurar copia.sqlite3 partida_recuperada.sqlite3

Cada destino debe ser NUEVO. La aplicación puede permanecer abierta durante
un respaldo online porque SQLite backup() incluye las páginas del WAL.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import sqlite3

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from nilo_runtime.storage.backups import (
    BackupError, backup_file, inspect_backup, restore_as_copy,
)
from nilo_runtime.core.state import StateSchemaError


def run(args):
    if args.action=="inspeccionar":
        info=inspect_backup(args.source)
    elif args.action=="respaldar":
        info=backup_file(args.source,args.destination)
    else:
        info=restore_as_copy(args.source,args.destination)
    return {"operacion":args.action,
            "origen":str(Path(args.source).resolve()),
            "destino":(str(Path(args.destination).resolve())
                       if args.destination is not None else None),
            "resultado":info}


def main(argv=None):
    parser=argparse.ArgumentParser(
        description="Inspeccionar, respaldar y recuperar partidas SQLite de Nilo.")
    parser.add_argument("action",
        choices=("inspeccionar","respaldar","restaurar"))
    parser.add_argument("source",help="Ruta de SQLite de origen.")
    parser.add_argument("destination",nargs="?",
                        help="Ruta de un archivo NUEVO de destino.")
    args=parser.parse_args(argv)
    if args.action!="inspeccionar" and not args.destination:
        parser.error("Respaldar/restaurar requiere un destino nuevo.")
    if args.action=="inspeccionar" and args.destination:
        parser.error("Inspeccionar no utiliza destino.")
    try:
        print(json.dumps(run(args),ensure_ascii=False,indent=2))
        return 0
    except (BackupError,StateSchemaError,FileExistsError,sqlite3.Error) as exc:
        print("No se modificó el archivo de origen: "+str(exc),file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
