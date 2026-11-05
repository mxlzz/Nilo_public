"""Política temporal del mundo, independiente de la velocidad del proveedor.

La selección del observador persiste; las transiciones afectan solo el ritmo
efectivo. Nunca aceleran límites, cooldowns ni consultas del LLM.
"""

# Valores compartidos por el controlador del motor y la API HTTP.
SUPPORTED_SPEEDS = (1, 10, 60, 80)


def deliberation_interval_seconds(cfg):
    """Mínimo global de deliberación, separado de cuotas y cooldowns reales.

    Entradas inválidas o extremas no desactivan silenciosamente la protección.
    """
    import math
    try:
        value = float(cfg.get('MIN_REAL_SECONDS_BETWEEN_CALLS', 15))
    except (TypeError, ValueError):
        return 15.0
    return min(300.0, max(10.0, value)) if math.isfinite(value) else 15.0


def effective_speed(selected_speed, pending=None, *, planning=False,
                    frozen=False, paused=False):
    """×0 en pausa, ×1 al consultar LLM, escritura ×2 o rápida ×80 máximo."""
    if paused or frozen:
        return 0.0
    speed = float(selected_speed)
    if isinstance(pending, dict):
        op = pending.get("step", {}).get("op")
    else:
        op = pending
    if op == "write":
        return min(speed, 2.0)
    # Una acción física pendiente tiene prioridad sobre un indicador stale.
    if pending is not None:
        return speed
    if planning:
        return 1.0
    return speed


def writing_tick(real_elapsed, remaining_base_seconds, selected_speed):
    """(avance simulado en segundos, escritura pendiente en segundos base).

    En todas las velocidades la escritura conserva un máximo de ×2,
    mientras las acciones físicas respetan la velocidad seleccionada.
    Si acaba en este tick, el resto vuelve a la velocidad seleccionada.
    """
    elapsed = max(0.0, float(real_elapsed))
    left = max(0.0, float(remaining_base_seconds))
    if left == 0:
        return elapsed * float(selected_speed), 0.0
    writing_speed = effective_speed(selected_speed, "write")
    writing_real = min(elapsed, left / writing_speed)
    remain = max(0.0, left - writing_real * writing_speed)
    return (writing_real * writing_speed +
            (elapsed - writing_real) * float(selected_speed)), remain
