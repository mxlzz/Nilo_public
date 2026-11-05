"""Capa física composicional v0.4.

No hay recetas por nombre de objeto. La forma, la cantidad de materiales,
la densidad y la permeabilidad determinan contención y flotación.
El sistema es intencionalmente pequeño y usa unidades abstractas: no es un CFD
ni demuestra que todas las construcciones imaginables sean posibles.
"""
from __future__ import annotations

from collections import Counter

from catalogo import MATERIAL_PHYSICS

PERSON_MASS = 5.5
WATER_DENSITY = 1.0


def _number(value, default, minimum, maximum):
    try:
        x = float(value)
        if x != x or x in (float('inf'), float('-inf')):
            return default
        return max(minimum, min(maximum, x))
    except (TypeError, ValueError):
        return default


def properties(material: str, known: dict | None = None):
    if material in MATERIAL_PHYSICS:
        return dict(MATERIAL_PHYSICS[material])
    item = (known or {}).get(material, {})
    return {
        'density': _number(item.get('density', item.get('peso', 5) / 3), 1.7, .05, 15),
        'permeability': _number(item.get('permeability', .35), .35, 0, 1),
    }


def geometry_from_step(step: dict, materials: list[str], form: str):
    requested = step.get('geometry', {})
    g = requested if isinstance(requested, dict) else {}
    kind = str(g.get('shape', '')).strip().lower()
    translations = {
        'hollow': 'hueco', 'hueco': 'hueco', 'cuenco': 'hueco',
        'platform': 'plataforma', 'plataforma': 'plataforma',
        'solid': 'macizo', 'macizo': 'macizo',
    }
    kind = translations.get(kind, 'hueco' if form == 'recipiente' else 'macizo')
    # Acotado por los materiales consumidos; una intención no crea volumen infinito.
    max_size = max(1.0, len(materials) * 1.8)
    size = _number(g.get('size', len(materials)), len(materials), .5, max_size)
    return {'shape': kind, 'size': round(size, 2)}


def body_physics(materials: list[str], geometry: dict, known: dict | None = None):
    counts = Counter(materials)
    mass = sum(properties(m, known)['density'] * n for m, n in counts.items())
    permeability = (sum(properties(m, known)['permeability'] * n for m,n in counts.items())
                    / max(1, len(materials)))
    shape = geometry.get('shape', 'macizo')
    size = _number(geometry.get('size'), len(materials), .5, max(1.0, len(materials)*1.8))
    if shape == 'hueco':
        displacement = size * 1.55
        capacity = size * .60
    elif shape == 'plataforma':
        displacement = size * 1.25
        capacity = 0.0
    else:
        displacement = size
        capacity = 0.0
    # Un casco hueco de madera o fibras sueltas infiltra agua; la piedra es poco porosa.
    # La eficiencia se modela como un límite gradual, no una prohibición por nombre.
    effective_displacement = displacement * (1.0 - permeability*.52 if shape == 'hueco' else 1.0)
    return {
        'mass': round(mass, 3), 'displacement': round(effective_displacement, 3),
        'raw_displacement': round(displacement, 3),
        'capacity': round(capacity, 3), 'permeability': round(permeability, 3),
        'shape': shape,
    }


def evaluate_buoyancy(item: dict, passenger=False, known: dict | None = None):
    geometry = item.get('geometry') or {'shape': 'macizo', 'size': len(item.get('materials', []))}
    physical = body_physics(item.get('materials', []), geometry, known)
    mass = physical['mass'] + (PERSON_MASS if passenger else 0)
    # Contenido líquido transportado suma su masa.
    contents = item.get('contents') or {}
    if contents.get('material') == 'agua':
        mass += _number(contents.get('quantity'), 0.0, 0.0, 100.0)
    buoyancy = physical['displacement'] * WATER_DENSITY
    return {'floats': buoyancy >= mass, 'supports_person': buoyancy >= mass if passenger else None,
            'load': round(mass, 2), 'buoyant_capacity': round(buoyancy, 2), **physical}


def evaluate_containment(item: dict, medium='agua', known: dict | None = None):
    body = body_physics(item.get('materials', []), item.get('geometry') or {}, known)
    possible = medium == 'agua' and body['capacity'] > 0
    retained_fraction = max(0.0, 1.0 - body['permeability'] * .75) if possible else 0.0
    quantity = round(body['capacity'] * retained_fraction, 2)
    return {'possible': bool(possible and quantity > 0), 'quantity': quantity,
            'retained_fraction': round(retained_fraction, 2), **body}


def human_knowledge(profile: str = 'contemporaneo'):
    # Para Nilo B: elegir un perfil no reemplaza al modelo de lenguaje ni borra
    # el conocimiento implícito de su entrenamiento. La restricción epistémica
    # debe evaluarse en un experimento separado, con criterios de procedencia.
    if profile == 'contemporaneo':
        return {'persona': 'adulto contemporáneo', 'conceptos_previos':
                ['herramientas', 'refugios', 'recipientes', 'embarcaciones',
                 'palancas', 'cuerdas', 'flotación', 'agua', 'materiales'],
                'habilidades_locales_verificadas': []}
    return {'persona': 'individuo experimental', 'conceptos_previos': [],
            'habilidades_locales_verificadas': []}
