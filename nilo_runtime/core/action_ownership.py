"""Propiedad de evidencia física por decisión, sin dependencias circulares.

Cada paso conserva un dueño explícito de proyecto o None. Una marca ausente
representa los planes de saves/replays antiguos y mantiene su proyección.
El módulo no importa ni proyectos, ni agenda, ni física.
"""
from __future__ import annotations


def active_project_for_action(person, step):
    """Retornar solo el proyecto activo al que pertenece este paso.

    Un proyecto retirado jamás recibe avances por una acción posterior. Si el
    LLM decidió 'sin_proyecto' mientras otro proyecto está abierto, la marca
    _decision_project_id=None impide atribuciones por coincidencia temporal.
    """
    current = person.get("project")
    if "_decision_project_id" not in step:
        return current
    if current and step["_decision_project_id"] == current.get("id"):
        return current
    return None
