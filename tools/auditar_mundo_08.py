"""Etapa 08: fronteras de generación/terreno y propietario único de la semilla.

Se inspeccionan módulos sin ejecutar el motor ni conectar proveedores LLM.
Uso: python tools/auditar_mundo_08.py
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))

from catalogo import PASSABLE as CATALOG_PASSABLE, TERRAINS, YIELDS
from nilo_runtime.worlds.island import ISLAND_GENERATOR, ISLAND_DEFINITION
from nilo_runtime.worlds.contracts import WorldGenerator

FORBIDDEN={
    "nilo", "brain", "cognition", "island_planning", "environments",
    "island_views", "survival", "physics", "mechanics", "construction",
    "inventions", "habits", "agenda", "project_progress", "world",
    "nilo_runtime.web", "nilo_runtime.application", "providers",
}
GENERATION_METHODS={"new_world","tile_key","valid","tile","set_tile","reveal"}


def inspect_worlds() -> list[str]:
    problems=[]
    files=sorted((ROOT/"nilo_runtime"/"worlds").glob("*.py"))
    if len(files)<3:
        problems.append("Faltan contratos o generador específico de la isla")
    for file in files:
        tree=ast.parse(file.read_text(encoding="utf-8-sig"),filename=str(file))
        for node in ast.walk(tree):
            imports=(
                [a.name for a in node.names]
                if isinstance(node,ast.Import) else
                [node.module or ""] if isinstance(node,ast.ImportFrom) else []
            )
            for module in imports:
                if any(module==banned or module.startswith(banned+".")
                       for banned in FORBIDDEN):
                    problems.append(
                        f"{file.name}:{node.lineno}: import prohibido de {module}"
                    )
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                x=node.func
                if isinstance(x.value,ast.Name) and x.value.id=="random" and (
                        x.attr=="seed" or x.attr=="random" or x.attr=="randint"
                        or x.attr=="choices"):
                    problems.append(
                        f"{file.name}:{node.lineno}: RNG global prohibido: random.{x.attr}"
                    )
    root=ROOT/"world.py"
    tree=ast.parse(root.read_text(encoding="utf-8-sig"),filename=str(root))
    duplicate=sorted(GENERATION_METHODS & {
        node.name for node in tree.body if isinstance(node,ast.FunctionDef)
    })
    if duplicate:
        problems.append("world.py tiene definiciones de generación duplicadas: "+
                        ",".join(duplicate))
    if not isinstance(ISLAND_GENERATOR,WorldGenerator):
        problems.append("Generador de isla no cumple WorldGenerator")
    if ISLAND_DEFINITION.environment_id!="isla_v1":
        problems.append("Generador de isla con entorno incorrecto")
    if set(ISLAND_DEFINITION.passable_symbols)!=CATALOG_PASSABLE:
        problems.append("El generador no toma passabilidad desde el catálogo")
    if ISLAND_DEFINITION.resource_symbols!=frozenset(YIELDS):
        problems.append("Símbolos de recursos del generador no coinciden con catálogo")
    if not ISLAND_DEFINITION.terrain_symbols==frozenset(TERRAINS):
        problems.append("Catálogo de terrenos del generador no coincide")
    if not set(YIELDS)<=set(TERRAINS):
        problems.append("Hay recursos sobre terrenos no definidos")
    return problems


if __name__=="__main__":
    failures=inspect_worlds()
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print("Etapa 08: generación única en worlds/island, topología catalogada, sin RNG global ni dependencias cognitivas.")
