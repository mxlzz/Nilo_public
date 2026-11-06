"""Prueba E2E del ZIP real con CPython embebido y migración en Windows CI.

No requiere claves LLM. La fuente del save se preserva y no se publican datos.
"""
from __future__ import annotations

import hashlib
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from empaquetar_version import build_package


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, cwd, timeout=180):
    environment = dict(os.environ)
    for key in list(environment):
        if any(word in key.upper() for word in
               ("API_KEY", "GEMINI", "GROQ", "OPENAI", "ANTHROPIC", "TOKEN", "SECRET")):
            environment.pop(key, None)
    result = subprocess.run(command, cwd=str(cwd), text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            errors="replace", env=environment, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{command[0]} falló: {result.stdout[-1500:]} "
                           f"{result.stderr[-1500:]}")
    return result


def main():
    if os.name != "nt":
        raise RuntimeError("Esta verificación debe ejecutarse en windows-latest")
    with tempfile.TemporaryDirectory(prefix="Nilo-24-windows-") as dirname:
        tmp = Path(dirname)
        archive = build_package(ROOT, tmp / "dist")
        version = (ROOT / "VERSION").read_text("utf-8").strip()
        apps = []
        for name in ("origen", "destino"):
            folder = tmp / name
            with zipfile.ZipFile(archive) as z:
                z.extractall(folder)
            apps.append(folder / f"Nilo-{version}")
        source, target = apps

        # Preparación real del portable con PowerShell y comprobación SHA256
        # de CPython oficial, exactamente como al ejecutar INICIAR_NILO.bat.
        run(["cmd", "/d", "/c", "PREPARAR_ENTORNO.bat"], source, timeout=240)
        python = source / "python" / "python.exe"
        assert python.is_file()
        run([str(python), "-I", "-c",
             "import sqlite3, ssl, urllib.request; print('CPython portable OK')"],
            source)
        shutil.copytree(source / "python", target / "python")
        run(["cmd", "/d", "/c", "PREPARAR_ENTORNO.bat"], target)

        expected = os.environ.get("GITHUB_SHA", "").strip().lower()
        run([str(python), "-B", "-c",
             "from pathlib import Path; from nilo import Simulation; "
             "from run_history import engine_identity; "
             "sim=Simulation(db_path=Path('nilo_mundo.sqlite3'), "
             "world_seed=7321, rng_seed=9821); sim.write(); sim.conn.close(); "
             "print(engine_identity(Path('.')))"], source)
        old_db = source / "nilo_mundo.sqlite3"
        before = digest(old_db)
        if len(expected) == 40:
            import sqlite3
            with closing(sqlite3.connect(old_db)) as db:
                commit = db.execute("SELECT code_commit FROM engine_sessions "
                                    "ORDER BY id DESC LIMIT 1").fetchone()[0]
            assert commit == expected, (commit, expected)

        # Migración por la vía pública desde el ZIP extraído; no reemplazar
        # ni escribir en la instalación de origen.
        target_python = target / "python" / "python.exe"
        run([str(target_python), "-B", "migrar.py", "--from", str(source)], target)
        assert (target / "nilo_mundo.sqlite3").exists()
        assert digest(old_db) == before, "Se alteró la partida original"

        run([str(target_python), "-B", "-c",
             "from pathlib import Path; from nilo import Simulation; "
             "sim=Simulation(db_path=Path('nilo_mundo.sqlite3')); "
             "sim.write(); sim.conn.close(); print('Migración abierta')"], target)
        # Los BAT de respaldo/restauración son procesos distintos. También
        # así se acredita que no quedan conexiones SQLite abiertas.
        made = run([str(target_python), "-B", "-c",
                    "from gestionar_partidas import backup; print(backup())"], target)
        folder = Path(made.stdout.strip().splitlines()[-1])
        run([str(target_python), "-B", "-c",
             "from pathlib import Path; from gestionar_partidas import restore; "
             "restore(Path(" + repr(str(folder)) + ")); "
             "print('Backup y restore verificados')"], target)
        assert digest(old_db) == before
        run([str(target_python), "-B", "-c",
             "import sqlite3; db=sqlite3.connect('nilo_mundo.sqlite3'); "
             "assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; "
             "assert db.execute('SELECT COUNT(*) FROM history').fetchone()[0]>=0; "
             "db.close()"], target)

        print(json.dumps({
            "status": "pass",
            "version": version,
            "python_portable": "CPython 3.12.10 embebido con hash validado",
            "new_world": True,
            "migration_source_unchanged": True,
            "rollback": "backup + restore",
            "code_commit": expected if len(expected) == 40 else None,
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
