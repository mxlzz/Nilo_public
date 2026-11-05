"""Descripciones sensoriales de objetos; los scores del motor son privados."""
from __future__ import annotations

import math


def desgaste_observable(value):
    """Umbrales históricos, sin porcentaje numérico ni valores no finitos."""
    if (not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(value)):
        return "estado de desgaste desconocido"
    if value <= 0:
        return "inutilizable"
    if value < 35:
        return "muy desgastado"
    if value < 70:
        return "desgaste apreciable"
    if value < 95:
        return "desgaste leve"
    return "sin desgaste apreciable"
