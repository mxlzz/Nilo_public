"""Topología y generación de isla_v1, extraídas de world.py de Nilo 0.6.4.

Preserva EXACTAMENTE el orden de llamadas RNG, celdas, sitios, depósitos,
campos JSON y secuencia de revelado inicial. No importa física cognitiva,
LLM, actor, navegación ni servidor. El mapa sólo es verdad del entorno.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any

from catalogo import TERRAINS, YIELDS, PASSABLE as CATALOG_PASSABLE
from nilo_runtime.worlds.contracts import WorldDefinition

W, H = 37, 21
DIRS = [(0,-1),(1,0),(0,1),(-1,0)]
# Antes world.py usaba una COPIA de este conjunto, no el set mutable del
# catálogo. Conservar ese aislamiento mientras se toma del catálogo la verdad.
PASSABLE = set(CATALOG_PASSABLE)
# Esta lista procede del catálogo validado; antes world.py la reescribía
# con una cadena literal equivalente. Conservar identidad y semántica.
ISLAND_DEFINITION = WorldDefinition(
    environment_id="isla_v1",
    generator_version=1,
    width=W,
    height=H,
    levels=("0", "-1"),
    terrain_symbols=frozenset(TERRAINS),
    passable_symbols=frozenset(PASSABLE),
    resource_symbols=frozenset(YIELDS),
    site_positions=(
        ("refugio", 15, 10, 0),
        ("cueva", 23, 7, 0),
        ("ruinas", 12, 7, 0),
    ),
)

def tile_key(x,y,z): return f"{x},{y},{z}"

def valid(x,y): return 0 <= x < W and 0 <= y < H

def tile(world,x,y,z=0):
    if not valid(x,y): return "#"
    return world["levels"][str(z)][y][x]

def set_tile(world,x,y,z,ch):
    line=list(world["levels"][str(z)][y]); line[x]=ch
    world["levels"][str(z)][y]=''.join(line)


def new_world(seed=7321):
    rng=random.Random(seed)
    surface=[]; underground=[]
    for y in range(H):
        sr=[]; cr=[]
        for x in range(W):
            noise = math.sin(x*.27)+ math.cos(y*.47) + math.sin((x+y)*.22)
            if x in (0,W-1) or y in (0,H-1): sr.append('~' if y in (0,H-1) else '^'); cr.append('#');continue
            if x>30 and y<7: ch='~' if noise<1.1 else 's'
            elif x<6 and y<6: ch='^' if rng.random()<.75 else '.'
            elif x>25 and y>13: ch='^' if rng.random()<.5 else 's'
            else: ch=rng.choices(['.',',','T','s','^'],[39,25,20,10,6])[0]
            sr.append(ch)
            cr.append('#' if rng.random()<.72 else ':')
        surface.append(''.join(sr)); underground.append(''.join(cr))
    w={"seed":seed,"levels":{"0":surface,"-1":underground},"visited":{},"revealed":[],"deposits":{},"structures":[],"excavation":{},"sites":{},"findings":[],"trail":[]}
    for (x,y,ch) in [(15,10,'h'),(15,11,'='),(16,11,'='),(17,11,'='),(23,7,'c'),(12,7,'r'),(28,10,'o'),(7,15,'o'),(30,17,'v')]:
        set_tile(w,x,y,0,ch)
    # Pasillo accesible hacia la entrada a la cueva.
    for x in range(17,24):
        set_tile(w,x,10,0,'=')
    for y in range(7,11): set_tile(w,23,y,0, 'c' if y==7 else '=')
    set_tile(w,23,7,-1,'e')
    for y in range(7,15):
        for x in range(17,31):
            if rng.random()>.25 or x in range(21,26): set_tile(w,x,y,-1,':')
    set_tile(w,23,7,-1,'e')  # Aplicar tras excavar las galerías, para no sobrescribir la salida.
    for (x,y,ch) in [(20,11,'o'),(27,9,'v'),(29,13,'r'),(18,8,'o'),(25,13,'v')]: set_tile(w,x,y,-1,ch)
    for z, rows in w['levels'].items():
        for y,row in enumerate(rows):
            for x,ch in enumerate(row):
                if ch in YIELDS: w['deposits'][tile_key(x,y,int(z))]=rng.randint(2,6)
    w['sites']={"refugio":{"x":15,"y":10,"z":0},"cueva":{"x":23,"y":7,"z":0},"ruinas":{"x":12,"y":7,"z":0}}
    reveal(w,15,10,0,3)
    return w


def reveal(w,x,y,z,r=2):
    known=set(w['revealed']); newly=[]
    for yy in range(max(0,y-r),min(H,y+r+1)):
        for xx in range(max(0,x-r),min(W,x+r+1)):
            if (xx-x)**2+(yy-y)**2 <= (r+.5)**2:
                k=tile_key(xx,yy,z)
                if k not in known:
                    known.add(k);newly.append((xx,yy,tile(w,xx,yy,z)))
    # Preservar la secuencia de descubrimiento. list(set(...)) usa un orden
    # variable entre procesos y alteraba decisiones aleatorias posteriores.
    w['revealed'].extend(tile_key(xx,yy,z) for xx,yy,_ in newly)
    return newly

class WorldTopologyError(ValueError):
    """Topología nueva malformada: no confundir con una partida histórica."""


def validate_generated_world(world: dict[str, Any]) -> None:
    """Valida una generación NUEVA, sin reescribir ni revelar celdas.

    No se usa para migrar saves existentes, que pueden tener excavaciones,
    estructuras, depósitos agotados y niveles de generaciones anteriores.
    """
    d = ISLAND_DEFINITION
    if not isinstance(world, dict) or not isinstance(world.get("levels"), dict):
        raise WorldTopologyError("Mundo sin niveles válidos.")
    if tuple(world["levels"]) != d.levels:
        raise WorldTopologyError("Capas de la isla ausentes o fuera de orden.")
    for level in d.levels:
        rows = world["levels"][level]
        if (not isinstance(rows, list) or len(rows) != d.height or
                any(not isinstance(row, str) or len(row) != d.width for row in rows)):
            raise WorldTopologyError(f"Dimensiones incorrectas de capa {level}.")
        if any(symbol not in d.terrain_symbols for row in rows for symbol in row):
            raise WorldTopologyError(f"Terreno no catalogado en capa {level}.")
    sites = world.get("sites")
    if not isinstance(sites, dict):
        raise WorldTopologyError("Sitios topológicos ausentes.")
    for name, x, y, z in d.site_positions:
        if sites.get(name) != {"x": x, "y": y, "z": z}:
            raise WorldTopologyError(f"Sitio {name} distinto del contrato de isla.")
    if world["levels"]["0"][7][23] != "c" or world["levels"]["-1"][7][23] != "e":
        raise WorldTopologyError("Entrada/salida de cueva desalineada.")
    deposits = world.get("deposits")
    if not isinstance(deposits, dict):
        raise WorldTopologyError("Depósitos de recursos inválidos.")
    # Cada fuente de la generación inicial tiene un depósito, incluso si
    # más tarde el agente lo agota. Esta comprobación no se aplica a saves.
    expected_sources = {
        tile_key(x, y, int(z))
        for z, rows in world["levels"].items()
        for y, row in enumerate(rows)
        for x, ch in enumerate(row) if ch in YIELDS
    }
    if set(deposits) != expected_sources:
        raise WorldTopologyError("Depósitos iniciales ausentes o no catalogados.")
    for position, count in deposits.items():
        try:
            x, y, z = (int(part) for part in position.split(","))
            ch = world["levels"][str(z)][y][x]
        except (ValueError, KeyError, IndexError, AttributeError, TypeError):
            raise WorldTopologyError("Depósito fuera del mapa o mal formado.") from None
        if not 0 <= x < d.width or not 0 <= y < d.height or ch not in YIELDS:
            raise WorldTopologyError("Depósito en celda sin recurso catalogado.")
        if type(count) is not int or not 2 <= count <= 6:
            raise WorldTopologyError("Cantidad de recurso inicial fuera de 2 a 6.")
    revealed = world.get("revealed")
    if not isinstance(revealed, list) or len(revealed) != len(set(revealed)):
        raise WorldTopologyError("Celdas inicialmente reveladas repetidas o inválidas.")
    for position in revealed:
        try:
            x, y, z = (int(part) for part in position.split(","))
        except (ValueError, AttributeError, TypeError):
            raise WorldTopologyError("Coordenada revelada inválida.") from None
        if not 0 <= x < d.width or not 0 <= y < d.height or str(z) not in d.levels:
            raise WorldTopologyError("Revelación fuera de los límites.")


@dataclass(frozen=True, slots=True)
class IslandWorldGenerator:
    """Generador específico de isla_v1; otro mundo implementa WorldGenerator."""

    @property
    def definition(self) -> WorldDefinition:
        return ISLAND_DEFINITION

    def generate(self, seed: int = 7321) -> dict[str, Any]:
        result = new_world(seed)
        validate_generated_world(result)
        return result


ISLAND_GENERATOR = IslandWorldGenerator()
