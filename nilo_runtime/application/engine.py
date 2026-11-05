"""Motor de simulación reutilizable sin importar ni iniciar HTTP/UI.

Simulation es una fachada de aplicación pequeña compuesta por casos de uso;
la API física antigua permanece en los adaptadores de entorno.
"""
from __future__ import annotations
from .session import SessionLifecycle
from .records import RecordsUseCases
from .decisions import DecisionUseCases
from .clockwork import ClockUseCases


class Simulation(SessionLifecycle, RecordsUseCases, DecisionUseCases, ClockUseCases):
    """API única de mundo, deliberación, actividad, archivo y estado observable."""
    pass
