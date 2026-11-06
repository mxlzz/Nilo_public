"""Fachada histórica de necesidades: física pura en nilo_runtime.physiology.

El autocuidado antiguo mantiene sus eventos, fuera del modelo físico.
"""
from nilo_runtime.physiology.needs import (
    NEEDS_DEFAULT, ensure_needs, _clamp, _sensation_level,
    _fatigue_sensation, needs_summary, perceived_needs,
    _HUNGER_WORDS, _THIRST_WORDS, _FATIGUE_WORDS,
    update_needs as _evolve,
)


def update_needs(person, world, elapsed_minutes, at_shelter=False,
                 near_water=False, active=False, resting=False,
                 legacy_energy_cap=False, legacy_autocare=False, *, waiting=False):
    historical_record=None
    if legacy_autocare:
        from motivation import record_maintenance
        historical_record=record_maintenance
    return _evolve(
        person, world, elapsed_minutes, at_shelter, near_water,
        active, resting, legacy_energy_cap, legacy_autocare,
        waiting=waiting, legacy_record=historical_record)
