"""Construye artefactos verificables de referencia para la reestructuración 0.7.

Sólo opera sobre copias del código, SQLite de prueba en --output y un directorio
temporal. No abre la partida real y jamás recopila config.env ni claves API.

Uso:
python tools/congelar_baseline_064.py --reference-root sources/v064 \
    --legacy-root sources/v060 --legacy-root sources/v05942 --output baseline_07
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

PINNED_VERSION = "0.6.4"
PINNED_COMMIT = "a8b72d664e9f29d8307ff5866d8ff4a7773368f0"
RELEASE_ZIP_SHA256 = "2da332eac1933648cf5e0b7220ea0580c91650d2a9eaf833d6f272d6f7fb6517"
EXPECTED_REPLAY = "9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24"
WORLD_SEED = 7321
RNG_SEED = 9821

# Mismo procedimiento básico que tests/test_historical_lab.py en 0.6.4.
# Se ejecuta dentro del checkout de la versión seleccionada.
CREATE_SAVE = r"""
import json
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from nilo import Simulation
from brain import normalize_decision

db = Path(sys.argv[2])
progressed = sys.argv[3] == 'progressed'
sim = Simulation(db_path=db, world_seed=7321, rng_seed=9821)
try:
    if progressed:
        sim.think = lambda: None
        sim.s['speed'] = 60
        sim.s['paused'] = False
        sim.s['mode'] = 'demo'
        decision = normalize_decision({
            'objetivo': 'Registrar una espera reproducible',
            'cuaderno': 'Ensayo de compatibilidad de archivo.',
            'motivo': 'Prueba sintética para el desarrollo',
            'accion_proyecto': 'sin_proyecto',
            'plan': [{'op': 'wait', 'minutes': 30}],
            'revisar_en_minutos': 90,
        })
        sim.plan_ready(decision, 'llm', {})
        for _ in range(50):
            sim.tick(3.0)
            if not sim.s['person'].get('pending') and not sim.s['person'].get('plan'):
                break
    sim.write()
finally:
    sim.conn.close()
"""

# El backup y restore usan la misma API real de gestionar_partidas.py,
# redirigida a una instalación totalmente sintética en --output.
CHECK_BACKUP = r"""
import hashlib
import json
import pathlib
import shutil
import sqlite3
import sys
import gc
from contextlib import closing
sys.path.insert(0, sys.argv[1])
import gestionar_partidas as gp

synthetic = pathlib.Path(sys.argv[2])
synthetic.mkdir(parents=True, exist_ok=True)
shutil.copy2(sys.argv[3], synthetic / "nilo_mundo.sqlite3")
gp.HERE = synthetic
gp.DB = synthetic / "nilo_mundo.sqlite3"
gp.CONFIG = synthetic / "config.env"
gp.BACKUPS = synthetic / "backups"
gp.VERSION = sys.argv[4]

def state(path):
    gp.check_db(path)
    with closing(sqlite3.connect(path)) as db:
        value = json.loads(db.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()[0])
    # El check_db heredado usa "with sqlite3.connect" (transacción) pero no
    # cierra explícitamente la conexión. En una prueba de WAL, recolectarla
    # antes del restore evita interpretar una lectura recién hecha como Nilo activo.
    gc.collect()
    return value

before = state(gp.DB)
backup_folder = gp.backup()
copy = backup_folder / "nilo_mundo.sqlite3"
assert state(copy) == before
assert not (backup_folder / 'config.env').exists()
db = sqlite3.connect(gp.DB)
try:
    db.execute("UPDATE snapshot SET payload = '{}' WHERE id=1")
    db.commit()
finally:
    db.close()  # Cerrar antes de restore evita detectar WAL abierto.
assert state(gp.DB) != before
gc.collect()
# Sin escrituras pendientes: hacer checkpoint y cerrar, sin borrar archivos WAL a mano.
with closing(sqlite3.connect(gp.DB)) as checkpoint:
    checkpoint.execute("PRAGMA wal_checkpoint(TRUNCATE)")
gc.collect()
import contextlib
import io
with contextlib.redirect_stdout(io.StringIO()):
    gp.restore(backup_folder, restore_config=False)
assert state(gp.DB) == before
assert len(gp.available_backups()) == 2  # Backup inicial + backup automático al restaurar
print(json.dumps({"restored": True, "backup_integrity": True,
                  "state_preserved": True, "configuration_copied": False,
                  "created_backup_count": len(gp.available_backups())}))
"""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_python(code: str, root: Path, *args: str) -> str:
    env = dict(os.environ)
    # Ninguna credencial externa entra a los procesos del baseline.
    for key in list(env):
        if any(word in key.upper() for word in
               ("API_KEY", "GEMINI", "GROQ", "OPENAI", "ANTHROPIC", "TOKEN", "SECRET")):
            env.pop(key, None)
    process = subprocess.run(
        [sys.executable, "-c", code, str(root), *map(str, args)],
        cwd=str(root), env=env, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=90, check=False,
    )
    if process.returncode:
        raise RuntimeError(
            f"Proceso falló en {root.name} (rc={process.returncode}):\n"
            + process.stderr[-3500:]
        )
    return process.stdout.strip()


def describe_db(path: Path) -> dict:
    with sqlite3.connect(path) as db:
        ok = db.execute("PRAGMA integrity_check").fetchone()[0]
        if ok != "ok":
            raise ValueError(f"{path}: integrity_check={ok}")
        tables = [row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        snapshot = db.execute(
            "SELECT payload FROM snapshot WHERE id=1").fetchone()
        if not snapshot:
            raise ValueError("Falta snapshot en " + str(path))
        state = json.loads(snapshot[0])
        counts = {
            "history": db.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            if "history" in tables else None,
            "revisions": db.execute("SELECT COUNT(*) FROM history_revisions").fetchone()[0]
            if "history_revisions" in tables else None,
        }
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "sqlite_integrity": ok,
        "tables": tables,
        "state_version": state.get("version"),
        "scenario_id": state.get("scenario_id"),
        "person_clock_minutes": state.get("person", {}).get("clock_minutes"),
        "world_seed": WORLD_SEED,
        "counts": counts,
    }


def generate_reference_save(root: Path, directory: Path, kind: str) -> dict:
    target = directory / f"partida_{kind}.sqlite3"
    run_python(CREATE_SAVE, root, str(target), kind)
    return describe_db(target)


def run_replay_reference(root: Path, directory: Path) -> dict:
    source = root / "tests" / "fixtures" / "replay_basico.json"
    if not source.exists():
        raise FileNotFoundError(source)
    outputs = []
    for i, hash_seed in enumerate((11, 97)):
        target = directory / f"replay_064_hashseed_{hash_seed}.json"
        env = dict(os.environ)
        for key in list(env):
            if any(word in key.upper() for word in
                   ("API_KEY", "GEMINI", "GROQ", "OPENAI", "ANTHROPIC", "TOKEN", "SECRET")):
                env.pop(key, None)
        env["PYTHONHASHSEED"] = str(hash_seed)
        proc = subprocess.run(
            [sys.executable, str(root / "reproducir.py"), str(source),
             "--diagnostics", "--output", str(target)],
            cwd=str(root), env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=100, check=False,
        )
        if proc.returncode:
            raise RuntimeError("Replay no pasó: " + proc.stderr[-3000:])
        outputs.append(json.loads(target.read_text(encoding="utf-8")))
    fingerprints = [x["fingerprint"] for x in outputs]
    if fingerprints != [EXPECTED_REPLAY, EXPECTED_REPLAY]:
        raise AssertionError(
            f"Replay diverge de huella fijada: {fingerprints} != {EXPECTED_REPLAY}"
        )
    return {
        "fixture": "tests/fixtures/replay_basico.json",
        "hashseeds": [11, 97],
        "fingerprints": fingerprints,
        "state_sha256": outputs[0]["state_sha256"],
        "archive_sha256": outputs[0]["archive_sha256"],
        "ticks": outputs[0]["ticks"],
        "decisions_consumed": outputs[0]["decisions_consumed"],
        "time_minutes": outputs[0]["time_minutes"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--legacy-root", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reference = args.reference_root.resolve(strict=True)
    output = args.output.resolve()
    if output == reference or reference in output.parents:
        raise ValueError("La salida debe estar fuera de la carpeta del release")
    version = (reference / "VERSION").read_text(encoding="utf-8").strip()
    if version != PINNED_VERSION:
        raise ValueError(f"Se esperaba v{PINNED_VERSION}, se encontró {version}")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output ya contiene archivos: {output}")
    output.mkdir(parents=True, exist_ok=True)

    manifest = {
        "format": "nilo-baseline-07-v1",
        "reference_version": PINNED_VERSION,
        "reference_tag": "v0.6.4",
        "reference_commit": PINNED_COMMIT,
        "release_zip_sha256_from_github": RELEASE_ZIP_SHA256,
        "source_manifest_sha256": sha256(reference / "MANIFIESTO_SHA256.json"),
        "world_seed": WORLD_SEED,
        "rng_seed": RNG_SEED,
        "reference": {},
        "legacy": {},
    }
    reference_dir = output / "v0.6.4"
    reference_dir.mkdir()
    for kind in ("initial", "progressed"):
        manifest["reference"][kind] = generate_reference_save(reference, reference_dir, kind)
    manifest["reference"]["replay"] = run_replay_reference(reference, reference_dir)

    for path in args.legacy_root:
        legacy = path.resolve(strict=True)
        old_version = (legacy / "VERSION").read_text(encoding="utf-8").strip()
        if old_version == PINNED_VERSION:
            raise ValueError("Versión histórica duplicada: " + str(legacy))
        legacy_dir = output / f"v{old_version}"
        legacy_dir.mkdir()
        manifest["legacy"][old_version] = {
            kind: generate_reference_save(legacy, legacy_dir, kind)
            for kind in ("initial", "progressed")
        }

    backup_test = json.loads(run_python(
        CHECK_BACKUP, reference, str(output / "restore_test"),
        str(reference_dir / "partida_progressed.sqlite3"), version))
    if not all(backup_test[k] for k in
               ("restored", "backup_integrity", "state_preserved")):
        raise AssertionError("Backup/restore no conservó el snapshot")
    manifest["backup_restore"] = backup_test

    # No incluir artefactos del test de restauración ni configuración sensible.
    shutil.rmtree(output / "restore_test")
    (output / "baseline_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "reference": version, "legacy_versions": sorted(manifest["legacy"]),
        "replay_fingerprint": EXPECTED_REPLAY,
        "backup_restore": "pass",
        "output": str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
