"""Construcción de partidas nuevas: composición, sin reglas de mundo duplicadas.

La versión del save sigue siendo 5; la versión del producto va en VERSION.
La disposición exacta de claves de este dict reproduce la de Nilo 0.6.4.
"""
from __future__ import annotations

import time

from agent import initial_agent
from environments import get_environment
from scenarios import get_scenario
from nilo_runtime.core.state import SAVE_SCHEMA_VERSION, validate_current_state


def initial_state(world_seed=7321, scenario_id="territorio_desconocido"):
    """Crea estado v5 compatible; escenario decide condiciones, Nilo decide actos."""
    scenario = get_scenario(scenario_id)
    environment = get_environment(scenario.environment_id)
    state = {
        "version": SAVE_SCHEMA_VERSION,
        "scenario_id": scenario.id,
        "world": environment.make_world(world_seed),
        "person": initial_agent(
            name=scenario.name,
            spawn=scenario.spawn,
            inventory=dict(scenario.starting_inventory),
            materials=environment.materials(),
            knowledge_profile=scenario.knowledge_profile,
            mood=scenario.mood,
        ),
        "events": [], "news": [], "read_marker": None, "journal": [],
        "speed": 1.0, "paused": False, "real_saved": time.time(), "last_llm_real": 0,
        "llm_daily": {}, "llm_total": 0, "last_tokens": {"entrada": 0, "salida": 0},
        "ai_error": "", "planning": False, "last_reason": "", "chat": [],
        "chatting": False, "chat_daily": {}, "chat_error": "",
        "next_deliberation_real": 0.0, "mode": "", "updated": 0,
        "provider_health": {}, "last_provider": "", "last_provider_model": "",
    }
    validate_current_state(state, strict_physics=True)
    return state
