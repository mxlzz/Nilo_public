"""Servicios compartidos del motor Nilo (sin HTTP, HTML ni UI)."""
from __future__ import annotations
import json, sqlite3, threading, time, random, os, sys, traceback, difflib, uuid, collections, hashlib
from pathlib import Path
from datetime import datetime
from world import (new_world, world_view, execute_action, MATERIALS,
                   migrate_portable_structures, prepare_navigation, advance_navigation, navigation_result, TRAVEL_MINUTES_PER_TILE,
                   infer_form, is_portable, item_effects, tile, valid, DIRS, resolve_go)
from brain import config, available, context_for, normalize_decision, request_llm, demo_decision, request_chat
from providers import route, ProvidersUnavailable, public_info, routing_signature
from physics import geometry_from_step, human_knowledge
from cognition import consolidate_research, register_research
from survival import ensure_needs, update_needs, needs_summary, NEEDS_DEFAULT
from construction import ensure_object
from habits import (ensure_habits, bootstrap_skills, record_skill, set_wait_preferences,
                    choose_wait_action, record_wait_result, record_wait_selection)
from inventions import (ensure_records,register_design,record_design_test,
                        submit_proposal,review_proposal,record_personal_experience,
                        submit_debug_report,record_action_outcome)
from archive import History
from review_store import ReviewStore, TABS
from observer import pending_sources
from experiment_log import capture, measure, compare_rest, closure_status, topic as research_topic, link_conclusion, observational_conclusion
from physical_links import snapshot as physical_snapshot, entities_for_action
from phenomena import missing_physics
from laboratory import compare as compare_physical
from motivation import record_maintenance, maintenance_summary
from behavior import record_behavior, behavior_summary
from strategy_review import semantic_signature, evidence_snapshot, detect_repetition
from project_progress import discovered_during_action, advance_evidence, repeated_methods
from agenda import ensure_agenda, set_agenda, choose_agenda_step, record_agenda_result, awaken_reminders, acknowledge_reminders
from goals import verified_simple_goal
from timing import effective_speed, writing_tick, SUPPORTED_SPEEDS, deliberation_interval_seconds
from nilo_runtime.application.bootstrap import initial_state
from nilo_runtime.application.operation_dispatch import execute_document
from nilo_runtime.core.state import (
    SAVE_SCHEMA_VERSION, StateSchemaError, validate_loaded_envelope,
    validate_current_state, snapshot_state,
)
from scenarios import get_scenario
from environments import get_environment
from nilo_runtime.core.outcomes import ActionResult, causal_event_from_measurement
from nilo_runtime.core.operations import (ACTION_DURATIONS, get_spec)
from nilo_runtime.core.clock import (clamp_real_elapsed, plan_time,
                                     phase_progress, completion_contract)
from nilo_runtime.core.identity import new_uuid, entropy_scoped, EntropySession, EntropyError
from nilo_runtime.storage.entropy import load_entropy, persist_entropy
from run_history import RunHistory
from diagnostics import inspect_invariants, record_invariant_issue, record_contract_issue, review_packet
from action_contracts import before as contract_before, classify as classify_contract
from research_cycle import begin_prediction, finish_prediction
from project_lifecycle import completion_evidence, project_needs_review, retire_project, closure_diagnostic
from bodily_policy import rest_minutes, fatigue_multiplier
from intervention import active_intervention

HERE=Path(__file__).resolve().parents[2]
DB=HERE/'nilo_mundo.sqlite3'
# Referencia de compatibilidad; la tabla pertenece al registro de operaciones.

# Ritmo aproximado de una persona que escribe fluidamente en un teclado:
# unas 60-70 palabras por minuto, con pausas naturales tras puntuación.
# Compartir estas mismas constantes con interfaz.html para la animación local.
def typing_step(ch: str) -> float:
    return 0.11 if ch in ' \t' else 0.17


def typing_pause(ch: str) -> float:
    if ch in '.!?…': return 0.38
    if ch in ',;:': return 0.20
    if ch == '\n': return 0.42
    return 0.0


def typing_duration(text: str) -> float:
    total = 0.0
    for i, ch in enumerate(text):
        total += typing_step(ch)
        if i < len(text) - 1:
            total += typing_pause(ch)
    return round(max(1.0, total), 3)


def typing_visible_chars(text: str, elapsed_seconds: float) -> int:
    t = 0.0
    for i, ch in enumerate(text):
        t += typing_step(ch)
        if t > elapsed_seconds + 1e-6:
            return i
        if i < len(text) - 1:
            t += typing_pause(ch)
    return len(text)



def highlight_key(text):
    q=str(text).strip().lower()
    if q.startswith(('observé por primera vez:', 'apareció en mi campo de visión:')):
        if 'agua' in q and not any(m in q for m in ('cueva','ruina','cristal','mineral oscuro')):
            return 'primer-contacto-agua'
        if 'cueva' in q:return 'primer-contacto-cueva'
    return None


def is_newsworthy(text, kind):
    """Hitos basados en hechos del motor, no en prosa espontánea del LLM.

    La lista de raíces filtra rutinarios; no pretende resumir narrativamente
    todos los eventos ni sustituye el cuaderno.
    """
    q=str(text).strip().lower()
    if kind=='decision':
        return any(v in q for v in ('finaliz', 'terminad', 'cerrad', 'nuevo proyecto', 'investigaci'))
    if kind in ('accion','resultado'):
        strong=('fabriqué ', 'construí ', 'abrí un ', 'abrí paso', 'excavé ',
                'utilicé ', 'descubrí:', 'descendí ', 'regresé ', 'llené ',
                'corté madera ', 'se hunde ', 'flota ', 'flotó ', 'navegar ',
                'probé ', 'completé ', 'intervine ', 'desmonté completamente ')
        if q.startswith(strong):return True
        if q.startswith(('observé por primera vez:', 'apareció en mi campo de visión:')):
            return any(word in q for word in ('cueva','ruina','mineral oscuro','cristal','agua'))
    return False




from dataclasses import dataclass
from typing import Callable, Any

@dataclass(frozen=True)
class RuntimeServices:
    """Puerto para config/proveedor; inyectable sin iniciar ningún servidor."""
    config: Callable[[], dict] = config
    available: Callable[[dict], bool] = available
    route: Callable[..., Any] = route
