"""Punto de entrada y compatibilidad de Nilo 0.7.

El núcleo vive en nilo_runtime.application.engine y puede importarse sin
cargar HTTP/UI. Esta fachada conserva la API pública de Nilo 0.6.4:
Simulation, DB, Handler, initial_state, funciones de tipiado y main().
"""
from __future__ import annotations
from nilo_runtime.application.deps import *
from nilo_runtime.application.engine import Simulation as EngineSimulation
from nilo_runtime.web.http import Handler, HTML_FILE, main as _serve_http


class Simulation(EngineSimulation):
    """Adaptador de legado para DB y proveedores que antes eran globales.

    La inyección se hace por llamada, no al importar: así funcionan clientes
    y tests históricos que parchean nilo.DB, nilo.config, nilo.available o
    nilo.route. EngineSimulation directo no depende de estos globales ni de UI.
    """
    def __init__(self, db_path=None, world_seed=7321, rng_seed=None,
                 scenario_id="territorio_desconocido"):
        services=RuntimeServices(
            config=lambda: config(),
            available=lambda cfg: available(cfg),
            route=lambda *args, **kwargs: route(*args, **kwargs),
        )
        super().__init__(
            db_path=DB if db_path is None else db_path,
            world_seed=world_seed,
            rng_seed=rng_seed,
            scenario_id=scenario_id,
            services=services,
        )


def main():
    """Iniciar interfaz local solamente al ejecutar nilo.py explícitamente."""
    return _serve_http(Simulation)


if __name__=="__main__":
    main()
