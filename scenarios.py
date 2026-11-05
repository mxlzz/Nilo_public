"""Escenarios: condiciones iniciales, no reglas físicas ni inteligencia.

Un escenario combina un entorno registrado con un agente inicial. No configura
secretamente sus leyes ni le concede conocimientos no comprobados.
"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class Scenario:
    id: str
    environment_id: str
    name: str
    spawn: tuple[int,int,int]
    starting_inventory: tuple[tuple[str,int],...]
    knowledge_profile: str
    mood: str
    introduction: str
    world_rule: str


UNKNOWN_LAND_INTRO=(
    "Acabo de llegar a un territorio desconocido. Antes de fabricar por rutina, "
    "conviene orientarme y reconocer vías de retorno; la incertidumbre no "
    "equivale a peligro verificado."
)
UNKNOWN_LAND_RULE=(
    "La verdad física proviene del motor. Para acceder al agua basta una orilla "
    "alcanzable: no se puede entrar caminando en casillas acuáticas. Arena y "
    "arboledas sí son transitables; las rocas no. No inventar obstáculos ni "
    "acceso por cueva. Excavar requiere punta. No repitas preguntas equivalentes."
)

SCENARIOS=MappingProxyType({
    "territorio_desconocido": Scenario(
        "territorio_desconocido","isla_v1","Nilo",(15,10,0),
        (("madera",1),("piedra",1)),"contemporaneo","curioso",
        UNKNOWN_LAND_INTRO,UNKNOWN_LAND_RULE),
    "territorio_sin_equipo": Scenario(
        "territorio_sin_equipo","isla_v1","Nilo",(15,10,0),
        (), "contemporaneo","curioso",
        "Estoy en un territorio desconocido sin materiales en mi inventario. "
        "Tengo que reconocer los recursos cercanos y comprobar cuáles puedo conseguir.",
        UNKNOWN_LAND_RULE),
})


def get_scenario(scenario_id="territorio_desconocido"):
    try: return SCENARIOS[scenario_id]
    except KeyError as exc:
        raise ValueError(f"Escenario desconocido: {scenario_id!r}") from exc
