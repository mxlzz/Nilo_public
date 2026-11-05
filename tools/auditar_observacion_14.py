"""Nilo 0.7 · Integridad del dueño perceptivo y límites de información (etapa 14).

Auditoría estática: las pruebas de comportamiento y concurrencia viven en
tests/test_observacion_14.py. No abre partidas ni consulta proveedores.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def defs(text):
    return {n.name for n in ast.parse(text).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def inspect():
    errors = []
    owner = source("nilo_runtime/perception/island.py")
    facade = source("island_views.py")
    engine = source("world.py")
    brain = source("brain.py")
    records = source("nilo_runtime/application/records.py")
    tools = source("nilo_runtime/perception/objects.py")
    required = {"visible_structures", "world_view", "adjacent_terrain",
                "map_snapshot", "survival_conditions"}
    missing = required - defs(owner)
    if missing:
        errors.append("Faltan funciones perceptivas: " + repr(sorted(missing)))
    if {"world_view", "map_snapshot", "survival_conditions"} & defs(facade):
        errors.append("La fachada isla conserva una segunda implementación")
    if "world_view" in defs(engine):
        errors.append("world.py conserva un segundo observador espacial")
    if "visible_structures(world)" not in owner or "tile_key(x, y, z) in known" not in owner:
        errors.append("Se omitió el filtro de estructuras por revelación")
    if "for structure in visible_structures(world):" not in owner:
        errors.append("El render lee estructuras sin pasar por el filtro perceptivo")
    if "enrich_structure(structure)" not in owner:
        errors.append("Falta enriquecimiento sobre copia de estructura")
    if ("adjacent_terrain(w,p)" not in brain or
            "for v in visible_structures(w)[-12:]" not in brain):
        errors.append("El agente recibe vecinos u obras directamente del estado interno")
    if ("seen_structures=visible_structures(w)" not in records or
            "'structures':seen_structures[-30:][::-1]" not in records):
        errors.append("La interfaz publica estructuras no observadas")
    if "desgaste_observable" not in defs(tools) or "Desgaste observable:" not in engine:
        errors.append("La inspección entrega una puntuación no percibida")
    if "def test_parallel_and_repeated_reading_leaves_exact_state" not in source(
            "tests/test_observacion_14.py"):
        errors.append("Falta prueba concurrente de pureza")
    if "from nilo_runtime.perception.island import map_snapshot, survival_conditions" not in facade:
        errors.append("No se preserva la API de island_views")
    return errors


if __name__ == "__main__":
    problems = inspect()
    if problems:
        raise SystemExit("\n".join(problems))
    print("Etapa 14: proyecciones sin fuentes duplicadas ni lectura de estructuras ocultas.")
