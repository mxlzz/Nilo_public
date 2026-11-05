"""Prueba un paquete portable real de la rama sin publicar un release.

Comprueba el manifiesto, el ZIP y un arranque desde su carpeta extraída:
no alcanza con que los imports funcionen desde el checkout de Git.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

# Un script ejecutado como tools/archivo.py sólo recibe tools/ en sys.path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from empaquetar_version import build_package

REQUIRED = (
    "nilo.py",
    "nilo_runtime/__init__.py",
    "nilo_runtime/core/__init__.py",
    "nilo_runtime/core/state.py",
    "nilo_runtime/core/outcomes.py",
    "nilo_runtime/core/clock.py",
    "nilo_runtime/core/operations.py",
    "nilo_runtime/core/identity.py",
    "nilo_runtime/storage/__init__.py",
    "nilo_runtime/storage/entropy.py",
    "nilo_runtime/storage/timeline.py",
    "nilo_runtime/worlds/__init__.py",
    "nilo_runtime/worlds/contracts.py",
    "nilo_runtime/worlds/island.py",
    "nilo_runtime/worlds/navigation.py",
    "nilo_runtime/worlds/resources.py",
    "nilo_runtime/application/__init__.py",
    "nilo_runtime/application/bootstrap.py",
    "nilo_runtime/application/deps.py",
    "nilo_runtime/application/session.py",
    "nilo_runtime/application/records.py",
    "nilo_runtime/application/decisions.py",
    "nilo_runtime/application/clockwork.py",
    "nilo_runtime/application/engine.py",
    "nilo_runtime/web/__init__.py",
    "nilo_runtime/web/http.py",
    "nilo_runtime/application/operation_dispatch.py",
    "world.py",
    "agent.py",
    "interfaz.html",
)


def verify(root: Path) -> dict:
    manifest = json.loads((root / "MANIFIESTO_SHA256.json").read_text("utf-8"))
    version = (root / "VERSION").read_text("utf-8").strip()
    for item in REQUIRED:
        if item not in manifest["files"]:
            raise AssertionError(f"Falta la ruta en manifiesto: {item}")
    with tempfile.TemporaryDirectory(prefix="nilo-07-portable-") as work:
        temp = Path(work)
        package = build_package(root, output_dir=temp / "dist")
        prefix = "Nilo-" + version + "/"
        with zipfile.ZipFile(package) as archive:
            entries = set(archive.namelist())
            for item in REQUIRED:
                if prefix + item not in entries:
                    raise AssertionError("No se incluyó en ZIP: " + item)
            if any(k.endswith("config.env") or k.endswith(".sqlite3") for k in entries):
                raise AssertionError("El ZIP contiene una partida o configuración privada")
            archive.extractall(temp / "extracted")
        app = temp / "extracted" / f"Nilo-{version}"
        smoke = (
            "from nilo import initial_state, Simulation\n"            "from nilo_runtime.application.engine import Simulation as CoreSimulation\n"
            "assert CoreSimulation.__module__ == 'nilo_runtime.application.engine'\n"

            "from nilo_runtime.core.state import snapshot_state, SAVE_SCHEMA_VERSION\n"            "from nilo_runtime.worlds.island import ISLAND_GENERATOR, validate_generated_world\n"
            "import hashlib,json\n"
            "w=ISLAND_GENERATOR.generate(7321)\n"
            "assert hashlib.sha256(json.dumps(w,ensure_ascii=False,separators=(',',':')).encode()).hexdigest() == 'ae1b04e016a93c1b2bad5ec0ce9297aab78f1ef828fb6fa0df93aab2409d39f9'\n"

            "s=initial_state(7321)\n"
            "v=snapshot_state(s)\n"
            "assert v.to_legacy() == s and SAVE_SCHEMA_VERSION == 5\n"
            "assert v.actor.position == (15,10,0)\n"
            "print('ZIP bootstrap v5 OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", smoke],
            cwd=str(app),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode:
            raise AssertionError(
                "ZIP de Nilo no importable: " + result.stderr[-3000:]
            )
        return {
            "version_label": version,
            "mode": "development_smoke_not_release",
            "paths_verified": len(REQUIRED),
            "zip_import": result.stdout.strip(),
        }


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parent.parent),
                     indent=2, ensure_ascii=False))
