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
    minimum=min(float(needs.get('energia',100)),float(needs.get('hidratacion',100)))
    return 1.7 if minimum<20 else (1.35 if minimum<40 else 1.0)
