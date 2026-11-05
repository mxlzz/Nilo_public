"""Condiciones de resguardo del mundo: hechos físicos, no rótulos.

El territorio de origen contiene una celda 'h' de refugio preexistente,
identificada por topología. Las obras construidas tienen geometría 2.5D
sin un modelo de cubierta/aislamiento comprobable: su beneficio corporal
todavía es no evaluable, aun si se llaman "refugio" o "habitáculo".
No modifica el mundo, ni el personaje, ni registros de observación.
"""
from __future__ import annotations

from nilo_runtime.worlds.island import valid


def shelter_properties(world, position):
    """Evaluación independiente de category, name y purpose."""
    try:
        x,y,z=position
        if type(x) is not int or type(y) is not int or type(z) is not int:
            raise ValueError("Posición inválida")
        if not valid(x,y):
            raise ValueError("Posición fuera del mapa")
        grid=world["levels"][str(z)]
        terrain=grid[y][x]
    except (TypeError,ValueError,IndexError,KeyError):
        return {"sheltered":False,"status":"no_evaluable",
                "reason":"Posición o terreno inaccesible para evaluar cubierta.",
                "source":"none"}
    # La celda original h es un hecho del generador, no una clase adjudicada
    # por palabras. No extrapolarlo a otras estructuras edificadas.
    if terrain=="h":
        return {"sheltered":True,"status":"verified",
                "reason":"Refugio inicial existente en la topología del mundo.",
                "source":"terrain"}
    built=[]
    for obj in world.get("structures",[]):
        if not isinstance(obj,dict):
            continue
        if tuple(obj.get("pos",()))==(x,y,z):
            built.append(str(obj.get("id","")))
    if built:
        return {"sheltered":False,"status":"no_evaluable",
                "reason":"La geometría de la obra no representa todavía cubierta ni aislamiento medibles.",
                "source":"structures","structure_ids":built}
    return {"sheltered":False,"status":"open_air",
            "reason":"No hay resguardo físico verificable en la casilla.",
            "source":"terrain"}


def sheltered(world, position):
    """Contrato booleano usado por reloj y mediciones, sin efectos."""
    return shelter_properties(world,position)["sheltered"]
