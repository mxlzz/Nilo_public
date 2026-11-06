"""Fachada compatible: implementación única en nilo_runtime.autonomy.agenda."""
from nilo_runtime.autonomy.agenda import (
    ALLOWED, NEEDS, STATES, ensure_agenda, normalize_task, set_agenda, condition_met, safe_step, choose_agenda_step, awaken_reminders, acknowledge_reminders, record_agenda_result
)
