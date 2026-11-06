"""Esquema de estado tipado, conservador y sin efectos secundarios (save v5).

El formato JSON y los valores de los campos existentes SON el contrato: no se
agregan claves, no se normalizan flotantes ni se regeneran IDs. Las dataclasses
son una vista de solo lectura, no una segunda fuente de estado.

Motor/versionado comercial, esquema de save y catálogo de acciones tienen ciclos
de versión distintos. La migración de save corresponde a storage (paso 18).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any

SAVE_SCHEMA_VERSION = 5
MIN_LEGACY_SCHEMA_VERSION = 0
# El estado antiguo no siempre declaraba versión; el parser de entrada lo admite.


class StateSchemaError(Exception):
    """Incompatibilidad o corrupción de estado; no permitir reseteo silencioso."""


def _fail(path: str, expected: str) -> None:
    raise StateSchemaError(f"Estado incompatible en {path}: se esperaba {expected}.")


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(k, str) for k in value):
        _fail(path, "objeto con claves de texto")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(path, "lista")
    return value


def _integer(value: Any, path: str, *, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        _fail(path, "entero válido" if minimum is None else f"entero >= {minimum}")
    return value


def _number(value: Any, path: str, *, minimum: float | None = None) -> float:
    if type(value) not in (int, float):
        _fail(path, "número finito")
    try:
        n = float(value)
    except (OverflowError, ValueError):
        _fail(path, "número finito")
    if not math.isfinite(n) or (minimum is not None and n < minimum):
        _fail(path, "número finito" if minimum is None else f"número finito >= {minimum}")
    return n


def validate_loaded_envelope(raw: Any) -> None:
    """Frontera *antes* de migrar. Acepta campos faltantes del legado, no futuro.

    No muta ni inventa campos. Rechaza un esquema posterior antes de que el
    viejo migrate() lo sobrescriba con 5 y lo pueda corromper.
    """
    state = _mapping(raw, "state")
    version = state.get("version", MIN_LEGACY_SCHEMA_VERSION)
    _integer(version, "state.version", minimum=MIN_LEGACY_SCHEMA_VERSION)
    if version > SAVE_SCHEMA_VERSION:
        raise StateSchemaError(
            f"Partida con esquema {version}; este motor solo entiende hasta "
            f"{SAVE_SCHEMA_VERSION}. Conservá el archivo y abrilo con la versión indicada."
        )
    _mapping(state.get("world"), "state.world")
    _mapping(state.get("person"), "state.person")


def validate_current_state(raw: Any, *, strict_physics: bool = False) -> None:
    """Valida estructura sin normalizar campos ni suplantar el diagnóstico.

    La carga/escritura normal tolera invariantes físicos deliberadamente rotos,
    para que inspect_invariants emita su evidencia. strict_physics=True sólo en
    creación/QA: rechaza cantidad negativa y reloj regresivo. No impone el
    mapa de isla_v1 a escenarios alternativos de prueba.
    """
    state = _mapping(raw, "state")
    _integer(state.get("version"), "state.version", minimum=MIN_LEGACY_SCHEMA_VERSION)
    if state["version"] != SAVE_SCHEMA_VERSION:
        _fail("state.version", f"versión de save {SAVE_SCHEMA_VERSION}")
    # El save v1 podía no tener scenario_id; la migración añade el default
    # al reabrirlo. Es legítimo conservar una copia sin modificar esos bytes.
    if "scenario_id" in state and (
        not isinstance(state["scenario_id"], str) or not state["scenario_id"]
    ):
        _fail("state.scenario_id", "nombre de escenario")
    world = _mapping(state.get("world"), "state.world")
    actor = _mapping(state.get("person"), "state.person")
    if "seed" in world:
        _integer(world["seed"], "state.world.seed")
    # Los niveles/celdas/depósitos pertenecen a la isla, NO al contrato genérico
    # de Environment. Comprobar su estructura únicamente cuando están presentes.
    if "levels" in world:
        layers = _mapping(world["levels"], "state.world.levels")
        if not layers:
            _fail("state.world.levels", "al menos un nivel")
        for level, rows in layers.items():
            _list(rows, f"state.world.levels.{level}")
            if any(not isinstance(row, str) for row in rows):
                _fail(f"state.world.levels.{level}", "lista de filas de texto")
    for key in ("revealed", "structures"):
        if key in world:
            _list(world[key], f"state.world.{key}")
    for i, structure in enumerate(world.get("structures", ())):
        _mapping(structure, f"state.world.structures[{i}]")
    if "deposits" in world:
        _mapping(world["deposits"], "state.world.deposits")

    if not isinstance(actor.get("name"), str) or not actor["name"]:
        _fail("state.person.name", "nombre")
    pos = actor.get("pos")
    if not isinstance(pos, (list, tuple)) or len(pos) != 3:
        _fail("state.person.pos", "tres coordenadas")
    for i, coord in enumerate(pos):
        _integer(coord, f"state.person.pos[{i}]")
    _number(actor.get("clock_minutes"), "state.person.clock_minutes",
            minimum=0 if strict_physics else None)
    inventory = _mapping(actor.get("inventory"), "state.person.inventory")
    for name, quantity in inventory.items():
        _integer(quantity, f"state.person.inventory.{name}",
                 minimum=0 if strict_physics else None)
    for key in ("materials", "knowledge"):
        _mapping(actor.get(key), f"state.person.{key}")
    for key in ("plan", "projects", "research", "items", "observations"):
        _list(actor.get(key), f"state.person.{key}")
    for key in ("measurements", "conclusions"):
        if key in actor:
            _list(actor[key], f"state.person.{key}")
    for key in ("events", "journal"):
        _list(state.get(key), f"state.{key}")
    for key in ("project", "pending"):
        if actor.get(key) is not None:
            _mapping(actor[key], f"state.person.{key}")
    _number(state.get("speed"), "state.speed", minimum=0)
    if type(state.get("paused")) is not bool:
        _fail("state.paused", "booleano")


def _freeze(value: Any) -> Any:
    # Sin deepcopy del motor: se crea una copia estructural con los valores
    # actuales; el lector no puede modificarla ni alterarla a posteriori.
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


@dataclass(frozen=True, slots=True)
class WorldState:
    """Hechos modelados por el motor, no creencias del personaje."""

    seed: int | None
    levels: Mapping[str, tuple[str, ...]]
    revealed: tuple[str, ...]
    structures: tuple[Mapping[str, Any], ...]
    data: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ActorState:
    """Agente y registros cognitivos separados por procedencia."""

    name: str
    position: tuple[int, int, int]
    clock_minutes: float
    inventory: Mapping[str, int]
    observations: tuple[Any, ...]  # observaciones, no «hechos universales»
    research: tuple[Any, ...]      # hipótesis/experimentos registrados
    knowledge: Mapping[str, Any]   # interpretación y conocimientos del actor
    measurements: tuple[Any, ...]  # datos/ensayos registrados en la partida
    projects: tuple[Any, ...]
    current_project: Any
    data: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class GameState:
    """Instantánea de lectura, con el mismo contenido del save original."""

    schema_version: int
    scenario_id: str | None
    world: WorldState
    actor: ActorState
    data: Mapping[str, Any]

    def to_legacy(self) -> dict[str, Any]:
        """Devuelve un dict NUEVO, JSON-equivalente al original; nunca una vista viva."""
        return _thaw(self.data)


def snapshot_state(raw: Mapping[str, Any]) -> GameState:
    """Produce una vista realmente inmutable y conserva claves extendidas."""
    validate_current_state(raw)
    data = _freeze(raw)
    w, p = data["world"], data["person"]
    return GameState(
        schema_version=data["version"],
        scenario_id=data.get("scenario_id"),
        world=WorldState(
            seed=w.get("seed"),
            levels=w.get("levels", MappingProxyType({})),
            revealed=w.get("revealed", ()),
            structures=w.get("structures", ()),
            data=w,
        ),
        actor=ActorState(
            name=p["name"],
            position=p["pos"],
            clock_minutes=p["clock_minutes"],
            inventory=p["inventory"],
            observations=p["observations"],
            research=p["research"],
            knowledge=p["knowledge"],
            measurements=p.get("measurements", ()),
            projects=p["projects"],
            current_project=p["project"],
            data=p,
        ),
        data=data,
    )
