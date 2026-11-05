"""Auditor estructural de Nilo: sin importar ni ejecutar el motor.

Uso: python tools/auditar_arquitectura.py [--json]
Solo biblioteca estándar. Las excepciones son los ciclos observados en 0.6.4.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

LEGACY_CYCLES = (
    frozenset(("action_contracts", "capabilities", "construction", "inventions",
               "mechanics", "structural_loads", "vessels", "world")),
    frozenset(("brain", "cognitive_projection")),
    frozenset(("historical_lab", "laboratorio_casos", "nilo")),
)

# Dependencias directas permitidas para código NUEVO bajo nilo_runtime/.
LAYER_IMPORTS = {
    "core": {"core"},
    "physics": {"core", "physics"},
    "physiology": {"core", "physiology"},
    "worlds": {"core", "worlds", "physics"},
    "perception": {"core", "worlds", "physics", "perception"},
    "agent": {"core", "agent"},
    "cognition": {"core", "agent", "cognition"},
    "autonomy": {"core", "worlds", "physiology", "cognition", "autonomy"},
    "storage": {"core", "agent", "worlds", "physics", "storage"},
    "audit": {"core", "agent", "worlds", "physics", "audit"},
    "application": {"core", "worlds", "perception", "physics", "physiology", "agent", "cognition",
                    "storage", "audit", "autonomy", "application"},
    "web": {"core", "application", "web"},
    "lab": {"core", "worlds", "physics", "physiology", "agent", "cognition", "storage",
            "audit", "autonomy", "application", "lab"},
}


def discover(root: Path) -> dict[str, Path]:
    found = {p.stem: p for p in root.glob("*.py") if p.is_file()}
    package = root / "nilo_runtime"
    if package.is_dir():
        for p in package.rglob("*.py"):
            rel = p.relative_to(root).with_suffix("")
            parts = rel.parts[:-1] if p.name == "__init__.py" else rel.parts
            if parts:
                found[".".join(parts)] = p
    return found


def dependencies(module: str, path: Path, available: set[str]) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    result = set()

    def add(target: str) -> None:
        # Permite imports de paquetes y submódulos, identificando el más específico.
        candidates = [s for s in available if target == s or target.startswith(s + ".")]
        if candidates:
            chosen = max(candidates, key=len)
            if chosen != module:
                result.add(chosen)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = module.split(".")[:-1]
                if node.level > len(parts):
                    continue
                base = ".".join(parts[:len(parts) - node.level + 1])
                target = ".".join(x for x in (base, node.module) if x)
            else:
                target = node.module or ""
            if target:
                add(target)
            for alias in node.names:
                if alias.name != "*":
                    add(".".join(x for x in (target, alias.name) if x))
    return result


def components(graph: dict[str, set[str]]) -> list[set[str]]:
    index = 0
    visited = {}
    lows = {}
    stack = []
    active = set()
    components_found = []

    def visit(v: str) -> None:
        nonlocal index
        visited[v] = lows[v] = index
        index += 1
        stack.append(v)
        active.add(v)
        for w in sorted(graph[v]):
            if w not in visited:
                visit(w)
                lows[v] = min(lows[v], lows[w])
            elif w in active:
                lows[v] = min(lows[v], visited[w])
        if lows[v] == visited[v]:
            group = set()
            while True:
                w = stack.pop()
                active.remove(w)
                group.add(w)
                if w == v:
                    break
            if len(group) > 1 or v in graph[v]:
                components_found.append(group)

    for name in sorted(graph):
        if name not in visited:
            visit(name)
    return components_found


def inspect(root: Path) -> dict:
    paths = discover(root)
    available = set(paths)
    graph = {name: dependencies(name, path, available) for name, path in paths.items()}
    errors = []

    if (root / "nilo.py").exists() and (root / "nilo" / "__init__.py").exists():
        errors.append("Colisión de import: nilo.py y nilo/__init__.py")

    for name, imports in graph.items():
        if not name.startswith("nilo_runtime."):
            continue
        parts = name.split(".")
        if len(parts) < 2:
            continue
        layer = parts[1]
        if layer not in LAYER_IMPORTS:
            errors.append("Paquete no registrado: " + name)
            continue
        for target in sorted(imports):
            if target.startswith("nilo_runtime."):
                target_layer = target.split(".")[1]
                if target_layer not in LAYER_IMPORTS[layer]:
                    errors.append("Dependencia invertida: " + name + " -> " + target)
            # Imports a módulos raíz son deuda transitoria de migración.
            # No se prohíben hasta que exista una API estable equivalente.

    cycles = components(graph)
    for group in cycles:
        if not all(not x.startswith("nilo_runtime") for x in group):
            errors.append("Ciclo nuevo en paquete: " + ", ".join(sorted(group)))
        elif not any(group <= old for old in LEGACY_CYCLES):
            errors.append("Ciclo nuevo entre módulos heredados: " + ", ".join(sorted(group)))

    return {
        "modules": len(graph),
        "local_edges": sum(map(len, graph.values())),
        "legacy_cycles": [sorted(x) for x in cycles if all(not z.startswith("nilo_runtime") for z in x)],
        "new_cycles": [sorted(x) for x in cycles if any(z.startswith("nilo_runtime") for z in x)],
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = inspect(Path(__file__).resolve().parent.parent)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Arquitectura: {report['modules']} módulos, {report['local_edges']} dependencias")
        print(f"Ciclos heredados: {len(report['legacy_cycles'])}; nuevos: {len(report['new_cycles'])}")
        for error in report["errors"]:
            print("ERROR:", error)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
