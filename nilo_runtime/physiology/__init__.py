"""Fisiología determinista y decisiones voluntarias separadas."""
from .needs import (
    NEEDS_DEFAULT, ensure_needs, update_needs, needs_summary, perceived_needs,
)
from .policy import (
    rest_minutes, wait_minutes, fatigue_multiplier,
    should_collapse, can_wake, body_strained,
)
