"""Catálogo tipado, versionado y de confianza del entorno isla_v1.

Datos desde JSON distribuidos CON el motor. Nunca carga rutas ni código
propuesto por el agente o contenido de una partida. Los valores internos no
son conocimientos transmitidos automáticamente a Nilo.

Esta etapa extrae definiciones de world/physics/construction/mechanics;
la instalación dinámica de nuevas capacidades pertenece a otro hito (#62).
"""
from __future__ import annotations

import json
import math
from pathlib import Path


_ROOT = Path(__file__).resolve().parent / "catalog"
_SCHEMAS = ("materiales", "terrenos", "objetos")


def _read(name):
    path = _ROOT / (name + ".json")
    # El nombre viene de un conjunto fijo, nunca de una entrada externa.
    if name not in _SCHEMAS:
        raise ValueError("Catálogo no reconocido.")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Clave duplicada en {name}: {key}")
            result[key] = value
        return result
    raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    if not isinstance(raw, dict) or type(raw.get("schema")) is not int or raw["schema"] != 1:
        raise ValueError(f"Esquema de catálogo incompatible: {name}")
    return raw


def _number(value, name, lower=0, upper=100):
    if type(value) not in (float, int) or not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError(f"Valor físico inválido: {name}")
    return value


def _text_list(values, name):
    if not isinstance(values, list) or not values or any(not isinstance(x, str) or not x for x in values):
        raise ValueError(f"Lista del catálogo inválida: {name}")
    if len(values) != len(set(values)):
        raise ValueError(f"Elementos duplicados: {name}")
    return values


def _validated_materials(raw):
    source = raw.get("materials")
    if not isinstance(source, dict) or not source:
        raise ValueError("No hay materiales definidos.")
    conventional, physics, salvage = {}, {}, {}
    world_keys = {"dureza", "resistencia", "peso", "combustible", "brillo"}
    for name, attributes in source.items():
        if not isinstance(name, str) or not name or not isinstance(attributes, dict):
            raise ValueError("Material no identificable.")
        w = attributes.get("world")
        p = attributes.get("physics")
        if not isinstance(w, dict) or set(w) != world_keys:
            raise ValueError(f"Propiedades del mundo incompletas: {name}")
        if not isinstance(p, dict) or set(p) != {"density", "permeability"}:
            raise ValueError(f"Propiedades físicas incompletas: {name}")
        for key, value in w.items():
            _number(value, name + ":" + key)
        _number(p["density"], name + ":density", .001, 100)
        _number(p["permeability"], name + ":permeability", 0, 1)
        recovered = _number(attributes.get("recoverability"), name + ":recoverability", 0, 1)
        conventional[name] = dict(w)
        physics[name] = dict(p)
        salvage[name] = recovered
    return conventional, physics, salvage


def _validated_terrain(raw, materials):
    labels = raw.get("labels")
    if not isinstance(labels, dict) or not labels:
        raise ValueError("Terrenos sin símbolos.")
    if any(not isinstance(symbol, str) or len(symbol) != 1 or
           not isinstance(label, str) or not label for symbol, label in labels.items()):
        raise ValueError("Símbolo de terreno inválido.")
    yields = {}
    for symbol, entry in raw.get("yields", {}).items():
        if symbol not in labels or not isinstance(entry, list) or len(entry) != 2:
            raise ValueError(f"Yacimiento mal definido: {symbol}")
        material, quantity = entry
        if material not in materials or type(quantity) is not int or quantity <= 0:
            raise ValueError(f"Yacimiento inválido: {symbol}")
        yields[symbol] = (material, quantity)
    sources = raw.get("gather_sources", {})
    if not isinstance(sources, dict):
        raise ValueError("Fuentes de recolección inválidas.")
    for material, symbols in sources.items():
        if material not in materials or not isinstance(symbols, str) or not symbols:
            raise ValueError("Material sin fuentes físicas válidas.")
        if any(symbol not in labels for symbol in symbols):
            raise ValueError("Símbolo de recolección no definido.")
    aliases = raw.get("gather_aliases", {})
    inspected = raw.get("inspect_aliases", {})
    for name, group in (("gather_aliases", aliases), ("inspect_aliases", inspected)):
        if not isinstance(group, dict) or any(not isinstance(a, str) or
               not isinstance(b, str) or not a or not b for a, b in group.items()):
            raise ValueError(f"Alias inválidos: {name}")
    if any(target not in materials for target in aliases.values()):
        raise ValueError("Alias de recolección referencia material inexistente.")
    passable = raw.get("passable")
    if not isinstance(passable, str) or not passable or any(ch not in labels for ch in passable):
        raise ValueError("Terrenos transitables no definidos.")
    return dict(labels), yields, dict(sources), dict(aliases), dict(inspected), set(passable)


def _validated_objects(raw):
    portable = _text_list(raw.get("portable_words"), "portable_words")
    forms = raw.get("forms")
    if not isinstance(forms, dict) or not forms:
        raise ValueError("No hay formas registradas.")
    forms = {name: tuple(_text_list(words, name)) for name, words in forms.items()
             if isinstance(name, str) and name}
    shapes = set(_text_list(raw.get("shapes"), "shapes"))
    joints = set(_text_list(raw.get("joints"), "joints"))
    return tuple(portable), forms, shapes, joints


_materials, _terrain, _objects = (_read(name) for name in _SCHEMAS)
MATERIALS, MATERIAL_PHYSICS, RECOVERABILITY = _validated_materials(_materials)
(TERRAINS, YIELDS, GATHER_SOURCES, GATHER_ALIASES,
 INSPECT_ALIASES, PASSABLE) = _validated_terrain(_terrain, MATERIALS)
PORTABLE_WORDS, FORMS, SHAPES, JOINTS = _validated_objects(_objects)


def clone_materials():
    """Partidas independientes: sus materiales pueden evolucionar sin mutar el catálogo."""
    return {name: dict(properties) for name, properties in MATERIALS.items()}
