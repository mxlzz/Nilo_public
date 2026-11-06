"""Compatibilidad: propietario de la física en nilo_runtime.physics.materials.

No contiene copias de reglas. Imports históricos siguen disponibles.
"""
from nilo_runtime.physics.materials import (
    MATERIAL_PHYSICS, PERSON_MASS, WATER_DENSITY, _number, properties,
    geometry_from_step, body_physics, evaluate_buoyancy,
    evaluate_containment, human_knowledge,
)
