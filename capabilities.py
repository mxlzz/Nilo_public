"""Registro cerrado de capacidades físicas revisadas (no carga plugins arbitrarios).

La operación genérica 'interact' es el único punto de despacho: incorporar otra
capacidad no requiere modificar world, brain ni el reloj. La validación física
sigue dentro del módulo y su resultado conserva el contrato histórico de 4-tuple.
"""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Capability:
    identifier: str
    version: str
    methods: tuple
    execute: Callable
    schema: str = "nilo.capability.v1"
    environments: tuple = ("isla_v1",)


_REGISTRY = {}


def register(capability):
    if not isinstance(capability, Capability) or not capability.identifier or not capability.methods:
        raise ValueError("Capacidad inválida.")
    if capability.identifier in _REGISTRY or any(method in offered_methods() for method in capability.methods):
        raise ValueError("Capacidad o método duplicado.")
    _REGISTRY[capability.identifier] = capability


def offered_methods():
    return frozenset(m for c in _REGISTRY.values() for m in c.methods)


def manifest():
    return [{"id": c.identifier, "version": c.version, "schema": c.schema,
             "methods": list(c.methods), "environments": list(c.environments)}
            for c in _REGISTRY.values()]


def resolve(method):
    return next((c for c in _REGISTRY.values() if method in c.methods), None)


def dispatch(world, person, step, rng):
    method = str(step.get("method") or "").strip().casefold()
    spec = resolve(method)
    if spec is None:
        from phenomena import record_unmodeled, no_model_message
        missing={"phenomenon":method or "método no identificado",
                 "missing_capability":"No hay módulo físico instalado para esta operación.",
                 "missing_effect_or_metric":method,
                 "known_available_measures":[],
                 "scope":"método no instalado; no implica fracaso de un objeto",
                 "test":"Definir una operación medible y revisar su módulo antes de activarla."}
        entry=record_unmodeled(person,step,missing,f"Minuto {person.get('clock_minutes',0):.2f}")
        return 5,[no_model_message(entry)],False,False
    versions = world.get("capability_versions") or {}
    installed = versions.get(spec.identifier)
    if installed is not None and installed != spec.version:
        return 5, [f"El mundo requiere la capacidad {spec.identifier} v{installed}; esta instalación ofrece v{spec.version}. No ejecuté la operación."], False, False
    if spec.identifier in world.get("disabled_capabilities", []):
        return 5, [f"La capacidad {spec.identifier} está deshabilitada para esta partida."], False, False
    # La versión se registra al ejecutar la primera operación del módulo,
    # incluso si sus precondiciones fallaron sin efectos.
    person.pop("_last_capability_diagnostic", None)
    result = spec.execute(world, person, step, rng)
    if not result[2]:
        person["_last_capability_diagnostic"]={
            "status":"precondition_failed","scope":method,
            "capability":spec.identifier,"version":spec.version}
    world.setdefault("capability_versions", {})[spec.identifier] = spec.version
    return result


# Los únicos módulos habilitados son los importados por el paquete auditado.
from vessels import interact as _vessels_interact

register(Capability("contenidos", "1.0.0",
    ("llenar", "rellenar", "transferir", "descargar", "beber", "guardar", "retirar"),
    _vessels_interact))

# Segundo módulo independiente: la física depende de piezas y geometría,
# nunca del nombre de la construcción. No modifica el despacho de world.py.
from structural_loads import interact as _structural_interact, METHODS as _structural_methods
register(Capability("cargas_estructurales", "1.0.0",
    _structural_methods, _structural_interact))
