"""Verifica importación de partidas históricas sintéticas en Nilo 0.6.4.

Trabaja SIEMPRE con copias temporales. El archivo histórico original
de referencia debe mantener su SHA-256 idéntico. No consume API LLM.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import os

OPEN_WITH_REFERENCE = r"""
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from nilo import Simulation
sim = Simulation(db_path=Path(sys.argv[2]), world_seed=7321, rng_seed=9821)
try:
    sim.write()
finally:
    sim.conn.close()
"""


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def info(path):
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        snap = db.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()
        assert snap is not None
        s = json.loads(snap[0])
        hist = db.execute(
            "SELECT COUNT(*) FROM history"
        ).fetchone()[0]
    return {
        "version": s.get("version"),
        "scenario_id": s.get("scenario_id"),
        "person_clock_minutes": s["person"]["clock_minutes"],
        "world_seed": s["world"].get("seed"),
        "history_rows": hist,
    }


def validate(source_root, reference_root, result):
    source_hash = digest(source_root)
    before = info(source_root)
    with tempfile.TemporaryDirectory(prefix="nilo-07-import-") as temp:
        copy = Path(temp) / "migrated.sqlite3"
        shutil.copy2(source_root, copy)
        env = dict(os.environ)
        for key in list(env):
            if any(word in key.upper() for word in
                   ("API_KEY", "GEMINI", "GROQ", "OPENAI", "ANTHROPIC", "TOKEN", "SECRET")):
                env.pop(key, None)
        p = subprocess.run(
            [sys.executable, "-c", OPEN_WITH_REFERENCE,
             str(reference_root), str(copy)],
            cwd=str(reference_root), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=90)
        if p.returncode:
            raise RuntimeError("Importación falló: " + p.stderr[-3000:])
        after = info(copy)
        assert after["scenario_id"] == before["scenario_id"]
        assert after["person_clock_minutes"] == before["person_clock_minutes"]
        assert after["world_seed"] == before["world_seed"]
        assert after["history_rows"] >= before["history_rows"]
        assert digest(source_root) == source_hash, "¡Se modificó la partida original!"
        result["cases"].append({
            "original": str(source_root.parent.name + "/" + source_root.name),
            "source_sha256_unchanged": source_hash,
            "before": before, "after": after,
            "migrated_copy_sha256": digest(copy),
            "status": "pass",
        })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    args = parser.parse_args()
    base = args.baseline.resolve(strict=True)
    ref = args.reference_root.resolve(strict=True)
    result = {
        "format": "nilo-07-migration-probe-v1",
        "reference_version": (ref / "VERSION").read_text(encoding="utf-8").strip(),
        "cases": [],
    }
    for directory in sorted(base.glob("v*")):
        for db in sorted(directory.glob("partida_*.sqlite3")):
            validate(db, ref, result)
    if len(result["cases"]) < 6:
        raise AssertionError("Se esperaban seis partidas de prueba (tres versiones x dos estados).")
    destination = base / "migration_probe.json"
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(result["cases"]), "all_passed": True},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
