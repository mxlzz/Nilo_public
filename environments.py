"""Contrato del entorno: frontera entre el motor del agente y las reglas del mundo.

La implementación actual (isla_v1) conserva las leyes y geometría originales.
Otros mundos podrán implementar el mismo contrato sin alterar la memoria del
agente. La interfaz actual, migraciones y algunas rutinas aún son específicas
de isla_v1: esta etapa introduce la frontera, no promete mundos arbitrarios.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
import random

from world import (
    MATERIALS, new_world, prepare_navigation, advance_navigation,
    navigation_result, execute_action, resolve_go
)
from brain import context_for
from island_views import map_snapshot, survival_conditions
from island_planning import IslandPlanner
from action_results import evidence_before, result_from_execution
from nilo_runtime.core.operations import get_spec
from nilo_runtime.worlds.island import ISLAND_GENERATOR


class Environment(Protocol):
    environment_id: str

    def make_world(self, seed: int) -> dict: ...
    def materials(self) -> dict: ...
    def perceive(self, world: dict, agent: dict, recent: list, stamp: str, scenario) -> dict: ...
    def validate_destination(self, world: dict, agent: dict, step: dict): ...
    def start_navigation(self, world: dict, agent: dict, step: dict, rng: random.Random): ...
    def move_navigation(self, world: dict, agent: dict, navigation: dict, due: int): ...
    def finish_navigation(self, navigation: dict, agent: dict): ...
    def perform(self, world: dict, agent: dict, step: dict, rng: random.Random): ...
    def perform_result(self, world: dict, agent: dict, step: dict, rng: random.Random): ...
    def surroundings(self, world: dict, agent: dict) -> tuple[bool, bool]: ...
    def render_map(self, world: dict, agent: dict) -> dict: ...
    def validate_plan(self, world: dict, agent: dict, steps: list, remember_strategy, event) -> list: ...
    def improve_plan(self, world: dict, agent: dict, steps: list, remember_strategy, event) -> list: ...


@dataclass(frozen=True)
class IslandEnvironment:
    environment_id: str="isla_v1"

    @property
    def world_definition(self):
        # Metadatos observacionales del entorno, no conocimiento del LLM.
        return ISLAND_GENERATOR.definition

    def make_world(self, seed):
        return ISLAND_GENERATOR.generate(seed)

    def materials(self):
        from catalogo import clone_materials
        return clone_materials()

    def perceive(self, world, agent, recent, stamp, scenario):
        return context_for(world, agent, recent, stamp, scenario=scenario)

    def validate_destination(self, world, agent, step):
        return resolve_go(world,agent,step)

    def start_navigation(self, world, agent, step, rng):
        try:
            spec=get_spec(step.get('op'))
        except ValueError:
            return None
        return prepare_navigation(world,agent,step,rng) if spec.navigable else None

    def move_navigation(self, world, agent, navigation, due):
        return advance_navigation(world,agent,navigation,due)

    def finish_navigation(self, navigation, agent):
        return navigation_result(navigation,agent)

    def perform(self, world, agent, step, rng):
        return execute_action(world,agent,step,rng)

    def perform_result(self, world, agent, step, rng):
        spec=get_spec(step.get('op'))
        if spec.executor != 'physical':
            raise ValueError(
                f"La operación {spec.name!r} se despacha como documento, "
                "nunca como acción física."
            )
        before=evidence_before(agent)
        legacy=self.perform(world,agent,step,rng)
        return result_from_execution(step,legacy,agent,before)

    def surroundings(self, world, agent):
        return survival_conditions(world, agent)

    def render_map(self, world, agent):
        return map_snapshot(world, agent)

    def validate_plan(self, world, agent, steps, remember_strategy, event):
        return IslandPlanner(self, world, agent, remember_strategy, event).validate_plan(steps)

    def improve_plan(self, world, agent, steps, remember_strategy, event):
        return IslandPlanner(self, world, agent, remember_strategy, event).improve_plan(steps)


# Registro cerrado por defecto. No carga plugins ni ejecuta código externo.
_ENVIRONMENTS={"isla_v1":IslandEnvironment()}


def get_environment(environment_id):
    try: return _ENVIRONMENTS[environment_id]
    except KeyError as exc:
        raise ValueError(f"Entorno no registrado: {environment_id!r}") from exc


def register_environment(adapter):
    """Punto de extensión explícito; no reemplaza implementaciones existentes."""
    key=adapter.environment_id
    if not isinstance(key,str) or not key or key in _ENVIRONMENTS:
        raise ValueError("Identificador de entorno inválido o ya registrado.")
    _ENVIRONMENTS[key]=adapter
