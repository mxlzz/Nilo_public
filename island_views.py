"""Presentación y condiciones espaciales específicas de isla_v1.

Aquí termina el conocimiento del formato de mapa 37x21, sus símbolos y la
interpretación de refugios/orillas. No se exponen casillas ocultas al agente.
No cambia reglas físicas ni el orden de revelación.
"""
from __future__ import annotations

from copy import deepcopy

from world import DIRS, H, TERRAINS, W, enrich_structure, structure_symbol, tile_key, valid


def survival_conditions(world, agent):
    """Condiciones observables del lugar que afectan la supervivencia."""
    x, y, z = agent["pos"]
    grid = world["levels"][str(z)]
    adjacent_water = z == 0 and any(
        valid(x + dx, y + dy) and grid[y + dy][x + dx] == "~"
        for dx, dy in DIRS
        if valid(x + dx, y + dy)
    )
    sheltered = bool(
        grid[y][x] == "h"
        or any(
            tuple(structure.get("pos", [])) == (x, y, z)
            and structure.get("category") == "habitaculo"
            and structure.get("shelter_condition") != "insuficiente"
            for structure in world.get("structures", [])
        )
    )
    return sheltered, adjacent_water


def map_snapshot(world, agent):
    """Proyección del mundo para la interfaz, no acceso a la verdad oculta.

    Conserva la salida JSON y la apariencia de obras antiguas, pero su
    enriquecimiento opera sobre COPIAS: consultar el mapa no altera el mundo.
    """
    x, y, z = agent["pos"]
    known = set(world["revealed"])
    all_layers = {}
    structures_layers = {}
    cells_layers = {}
    for level in (0, -1):
        by_pos = {}
        for structure in world.get("structures", []):
            if len(structure.get("pos", [])) == 3 and structure["pos"][2] == level:
                # Una proyección de lectura no completa campos sobre el mundo real.
                # La compatibilidad visual vive en la copia que recibe la UI.
                projected = enrich_structure(deepcopy(structure))
                key = f"{structure['pos'][0]},{structure['pos'][1]}"
                by_pos.setdefault(key, []).append(projected)
        layer = []
        for yy in range(H):
            chars = []
            for xx in range(W):
                cell = f"{xx},{yy}"
                symbol = (world["levels"][str(level)][yy][xx]
                          if tile_key(xx, yy, level) in known else " ")
                if symbol != " " and cell in by_pos:
                    symbol = structure_symbol(by_pos[cell][0])
                if (xx, yy, level) == (x, y, z):
                    symbol = "@"
                chars.append(symbol)
            layer.append("".join(chars))
        all_layers[str(level)] = layer
        cells_layers[str(level)] = by_pos
        structures_layers[str(level)] = {k: v[0] for k, v in by_pos.items()}

    trail_by_layer = {"0": [], "-1": []}
    for idx, key in enumerate(reversed(world.get("trail", []))):
        tx, ty, tz = map(int, key.split(","))
        if str(tz) in trail_by_layer:
            trail_by_layer[str(tz)].append({"x": tx, "y": ty, "age": idx})
    return {
        "level": "Superficie" if z == 0 else "Subsuelo",
        "map": all_layers[str(z)],
        "w": W,
        "h": H,
        "legend": TERRAINS,
        "structure_cells": structures_layers[str(z)],
        "trail": trail_by_layer[str(z)],
        "maps": all_layers,
        "structure_layers": structures_layers,
        "structure_cell_lists": cells_layers,
        "trail_layers": trail_by_layer,
    }
