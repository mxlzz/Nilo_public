"""Etapa 24: cobertura explícita del paquete distribuible, sin tocar partidas."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ("assets", "catalog", "nilo_runtime")
DOCS = {
    "docs/NOTAS_VERSION_070.md", "docs/CAMBIOS.md",
    "docs/LABORATORIO_ESCENARIOS.md", "docs/LABORATORIO_HISTORICO.md",
}


def inspect(root: Path = ROOT) -> dict:
    version = (root / "VERSION").read_text("utf-8").strip()
    manifest = json.loads((root / "MANIFIESTO_SHA256.json").read_text("utf-8"))
    files = manifest.get("files", {})
    declared = set(files)
    required = {
        p.relative_to(root).as_posix()
        for p in root.glob("*.py") if p.is_file()
    }
    required.update(p.relative_to(root).as_posix()
                    for directory in STATIC
                    for p in (root / directory).rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts
                    and p.suffix.lower() not in (".pyc", ".pyo"))
    required.update(DOCS)
    required.update(("VERSION", "README.md", "INICIAR_NILO.bat",
                     "PREPARAR_ENTORNO.bat", "OBTENER_PYTHON.ps1",
                     "LEEME_PRIMERO.txt", "LEEME_PORTABLE.txt",
                     "config.env.example", "primer_inicio.py"))
    errors = []
    if manifest.get("version") != version:
        errors.append("VERSION y MANIFIESTO_SHA256.json no coinciden")
    if version != "0.7.0":
        errors.append("Se esperaba preparar Nilo 0.7.0")
    missing = sorted(required - declared)
    if missing:
        errors.append("Faltan archivos de ejecución en manifiesto: " + ", ".join(missing))
    for path in sorted(declared):
        relative = Path(path)
        if (relative.is_absolute() or ".." in relative.parts
                or path.startswith((".github/", "tests/", "tools/"))
                or path in ("config.env", ".env")
                or relative.suffix.lower() in (".sqlite", ".sqlite3", ".db", ".zip")):
            errors.append("Archivo impropio del ZIP: " + path)
        elif not (root / relative).is_file():
            errors.append("Archivo inexistente del manifiesto: " + path)
    legacy_facades = []
    for p in root.glob("*.py"):
        text = p.read_text("utf-8-sig")[:240].lower()
        if "fachada compatible" in text or "fachada de compatibilidad" in text:
            legacy_facades.append(p.name)
    return {
        "version": version,
        "files_in_package_manifest": len(declared),
        "runtime_files_required": len(required),
        "legacy_compatibility_facades": sorted(legacy_facades),
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    outcome = inspect()
    if args.json:
        print(json.dumps(outcome, ensure_ascii=False, indent=2))
    else:
        print(f"Release {outcome['version']}: {outcome['files_in_package_manifest']} archivos "
              f"({len(outcome['legacy_compatibility_facades'])} fachadas de compatibilidad)")
        for error in outcome["errors"]:
            print("ERROR:", error)
    return 1 if outcome["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
