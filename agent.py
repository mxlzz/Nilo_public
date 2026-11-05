"""Identidad, memoria inicial y equipamiento del agente, sin crear un mundo.

Los datos posteriores de memoria/proyectos siguen perteneciendo al agente incluso
si se introduce otro escenario. No se borran al cargar una partida.
"""
from __future__ import annotations

from copy import deepcopy


def initial_agent(*, name, spawn, inventory, materials, knowledge_profile, mood):
    """Crear un agente nuevo; los valores provienen del escenario y entorno."""
    if len(spawn) != 3 or any(not isinstance(x, int) for x in spawn):
        raise ValueError("La posición inicial debe tener 3 coordenadas enteras.")
    if any(not isinstance(v,int) or v < 0 for v in inventory.values()):
        raise ValueError("Inventario inicial inválido.")
    return {
        "name": name,
        "pos": list(spawn),
        "inventory": deepcopy(inventory),
        "materials": deepcopy(materials),
        "knowledge": {},
        "research": [],
        "projects": [],
        "project": None,
        "plan": [],
        "items": [],
        "observations": [],
        "clock_minutes": 0.0,
        "pending": None,
        "mood": mood,
        "knowledge_profile": knowledge_profile,
        "vehicle_id": None,
    }
