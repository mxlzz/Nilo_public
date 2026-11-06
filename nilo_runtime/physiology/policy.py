"""Contratos corporales compartidos para acciones y agenda."""
import math


def rest_minutes(step, default=30):
    if not isinstance(step, dict):
        return None
    value=step.get('minutes',default)
    if isinstance(value,bool):
        return None
    try:
        duration=float(value)
    except (ValueError,TypeError,OverflowError):
        return None
    return duration if math.isfinite(duration) and 1 <= duration <= 1440 else None


def wait_minutes(step, default=30):
    """Mismo intervalo validado que rest, sin compartir su efecto fisiológico."""
    return rest_minutes(step, default)


def fatigue_multiplier(needs):
    try:
        values=(float(needs.get('energia',100)),float(needs.get('hidratacion',100)))
    except (TypeError,ValueError,OverflowError):
        return 1.7
    if not all(math.isfinite(v) for v in values):
        return 1.7
    minimum=min(values)
    return 1.7 if minimum<20 else (1.35 if minimum<40 else 1.0)


COLLAPSE_ENERGY=5.0
AWAKE_ENERGY=40.0


def should_collapse(energy):
    return float(energy)<=COLLAPSE_ENERGY


def can_wake(energy):
    return float(energy)>=AWAKE_ENERGY


def body_strained(needs):
    return (float(needs["hidratacion"])<15 or
            float(needs["nutricion"])<12 or
            float(needs["energia"])<12)
