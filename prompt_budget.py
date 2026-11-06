"""Fachada de presupuestos LLM: implementación única en nilo_runtime.agent.budget."""
from nilo_runtime.agent.budget import (
    SHORT_OPERATIONS, GROQ_SYSTEM, brief_actions, _size, _CORE,
    _REDUCE_FIRST, _REMOVE_FIRST, context_focus, context_stats,
    bounded_context, compact_context, _cognitive_needs_context,
)
