"""Proyecciones de isla_v1: la percepción observa, nunca muta el mundo.

Las coordenadas, obras y el terreno de celdas no reveladas son información
interna del motor, incluso cuando se conoce su posición en el generador.
La interfaz y el agente comparten el filtro espacial, pero no el payload.
"""
from __future__ import annotations

from copy import deepcopy
from catalogo import TERRAINS
from nilo_runtime.worlds.island import DIRS, H, W, tile, tile_key, valid
from nilo_runtime.worlds.objects import enrich_structure, structure_symbol
from nilo_runtime.worlds.shelter import sheltered


def visible_structures(world):
    """Copias de las estructuras observadas, en su orden original.

    Ni el ID ni el nombre de una estructura desconocida pueden filtrarse
    al JSON público o a la deliberación a través de metadatos separados.
    """
    known = set(world.get("revealed", ()))
    result = []
    for obj in world.get("structures", ()):
        if not isinstance(obj, dict):
            continue
        pos = obj.get("pos")
        if not isinstance(pos, (tuple, list)) or len(pos) != 3:
            continue
        x, y, z = pos
        if (type(x) is not int or type(y) is not int or
                type(z) is not int or not valid(x, y)):
            continue
        if tile_key(x, y, z) in known:
            result.append(deepcopy(obj))
    return result


def adjacent_terrain(world, agent):
    """Vecinos accesibles visualmente: ' ' indica terreno no observado."""
    x, y, z = agent["pos"]
    known = set(world.get("revealed", ()))
    return [{"x": x + dx, "y": y + dy,
             "tipo": tile(world, x + dx, y + dy, z)
             if tile_key(x + dx, y + dy, z) in known else " "}
            for dx, dy in DIRS if valid(x + dx, y + dy)]


def world_view(world, person):
    """Hitos del área observada; nunca consulta la apariencia de lo oculto."""
    x, y, z = person["pos"]
    known = set(world.get("revealed", ()))
    near = []
    for yy in range(max(0, y - 4), min(H, y + 5)):
        for xx in range(max(0, x - 4), min(W, x + 5)):
            if tile_key(xx, yy, z) not in known:
                continue
            ch = tile(world, xx, yy, z)
            if ch in "Tocersv^~":
                near.append({"pos": [xx, yy], "tipo": TERRAINS.get(ch, ch),
                             "simbolo": ch, "distancia": abs(xx - x) + abs(yy - y)})
    near.sort(key=lambda v: v["distancia"])
    return near[:18]


def survival_conditions(world, agent):
    """Condiciones físicas locales; no proyecta el mapa ni cambia fisiología."""
    x, y, z = agent["pos"]
    grid = world["levels"][str(z)]
    adjacent_water = z == 0 and any(
        valid(x + dx, y + dy) and grid[y + dy][x + dx] == "~"
        for dx, dy in DIRS if valid(x + dx, y + dy)
    )
    return sheltered(world, agent["pos"]), adjacent_water


def map_snapshot(world, agent):
    """Vista de UI: dos niveles, solo casillas y estructuras descubiertas.

    Los campos históricos se enriquecen en copias; jamás se completan
    ni se sobrescriben sobre world["structures"].
    """
    x, y, z = agent["pos"]
    known = set(world.get("revealed", ()))
    by_level = {"0": {}, "-1": {}}
    for structure in visible_structures(world):
        sx, sy, sz = structure["pos"]
        if str(sz) not in by_level:
            continue
        projected = enrich_structure(structure)
        by_level[str(sz)].setdefault(f"{sx},{sy}", []).append(projected)

    all_layers, structures_layers, cells_layers = {}, {}, {}
    for level in (0, -1):
        by_pos = by_level[str(level)]
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
        if key not in known:
            continue
        try:
            tx, ty, tz = map(int, key.split(","))
        except (ValueError, AttributeError):
            continue
        if str(tz) in trail_by_layer:
            trail_by_layer[str(tz)].append({"x": tx, "y": ty, "age": idx})
    return {
        "level": "Superficie" if z == 0 else "Subsuelo",
        "map": all_layers[str(z)],
        "w": W,
        "h": H,
        "legend": dict(TERRAINS),
        "structure_cells": structures_layers[str(z)],
        "trail": trail_by_layer[str(z)],
        "maps": all_layers,
        "structure_layers": structures_layers,
        "structure_cell_lists": cells_layers,
        "trail_layers": trail_by_layer,
    }
