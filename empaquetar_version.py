"""Generar un ZIP versionado de Nilo sin incluir datos del usuario.

Uso: python empaquetar_version.py
Salida: dist/Nilo-<VERSION>.zip, carpeta interna Nilo-<VERSION>/.
Solo bibliotecas estándar; funciona tanto desde un clon como desde el ZIP de GitHub.
"""
from __future__ import annotations

import re
import json
import hashlib
import zipfile
import os
import subprocess
from pathlib import Path


SKIP_DIRS = {
    ".git", ".github", ".venv", ".pytest_cache", "__pycache__", "venv",
    "node_modules", "python", "dist", "backups", "respaldos",
}
SKIP_NAMES = {"config.env", ".env", ".nilo_primera_ejecucion"}
BLOCKED_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".zip", ".log"}


def package_files(root: Path):
    """Solo archivos que el manifiesto del repositorio identifica como fuentes."""
    manifest = json.loads((root / "MANIFIESTO_SHA256.json").read_text(encoding="utf-8"))
    for name in sorted(set(manifest["files"]) | {"MANIFIESTO_SHA256.json"}):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Ruta insegura en manifiesto: {name}")
        if any(part.casefold() in SKIP_DIRS for part in relative.parts[:-1]):
            continue
        if relative.name.casefold() in SKIP_NAMES or relative.suffix.casefold() in BLOCKED_SUFFIXES:
            continue
        path = root / relative
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root):
            continue
        if not path.is_file():
            raise FileNotFoundError(f"Falta archivo del manifiesto: {relative}")
        yield path, relative


def _build_commit(root: Path) -> str | None:
    """SHA del checkout fuente, incluido dentro del ZIP portable sin .git."""
    sha = os.environ.get("GITHUB_SHA", "").strip().lower()
    if re.fullmatch(r"[0-9a-f]{40}", sha):
        return sha
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=3, check=False)
        if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root:
            result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                                    capture_output=True, text=True, timeout=3, check=False)
            sha = result.stdout.strip().lower()
            if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha):
                return sha
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def build_package(root: Path, output_dir: Path | None = None) -> Path:
    root = root.resolve()
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    manifest = json.loads((root / "MANIFIESTO_SHA256.json").read_text(encoding="utf-8"))
    if manifest.get("version") != version:
        raise ValueError("La versión del manifiesto y la de VERSION son diferentes.")
    if not re.fullmatch(r"\d+(?:\.\d+){2,5}", version):
        raise ValueError(f"Versión inesperada en VERSION: {version!r}")
    for required in ("INICIAR_NILO.bat", "primer_inicio.py", "nilo.py", "config.env.example"):
        if not (root / required).is_file():
            raise FileNotFoundError(f"Falta un archivo esencial del paquete: {required}")
    name = f"Nilo-{version}"
    target_dir = (output_dir or root / "dist").resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{name}.zip"
    # El manifiesto fuente identifica rutas; los hashes del artefacto se
    # calculan a partir de los bytes realmente incluidos. Así cada release
    # deja de arrastrar checksums históricos de versiones anteriores.
    entries=[]
    hashes={}
    for path, relative in package_files(root):
        if relative.as_posix()=="MANIFIESTO_SHA256.json":
            continue
        data=path.read_bytes()
        entries.append((relative.as_posix(),data))
        hashes[relative.as_posix()]=hashlib.sha256(data).hexdigest()
    commit = _build_commit(root)
    build_info = {
        "product": "Nilo",
        "version": version,
        "code_commit": commit,
        "provenance": "git_sha" if commit else "sin_commit_verificable",
    }
    build_info_bytes = (json.dumps(build_info, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    entries.append(("BUILD_INFO.json", build_info_bytes))
    hashes["BUILD_INFO.json"] = hashlib.sha256(build_info_bytes).hexdigest()
    actual_manifest=json.dumps({"version":version,"files":hashes},
                               indent=2,ensure_ascii=False).encode("utf-8")+b"\n"
    entries.append(("MANIFIESTO_SHA256.json",actual_manifest))
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative,content in sorted(entries):
            info = zipfile.ZipInfo(f"{name}/{relative}", (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"Paquete listo: {target}")
    return target


if __name__ == "__main__":
    build_package(Path(__file__).resolve().parent)
