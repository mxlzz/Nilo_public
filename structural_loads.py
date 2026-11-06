"""Capacidad 0.6: cargas verificables sobre construcciones fijas.

Modelo abstracto de soporte estático, no ingeniería estructural ni clima. El
límite deriva de componentes, material, condición y tamaño, nunca del nombre o
categoría narrativa. Las unidades son lotes abstractos del mundo de Nilo.
"""
from __future__ import annotations
from nilo_runtime.worlds.resources import transfer_units, ResourceBalanceError

import math
from physics import properties
from construction import find_object


METHODS = ("depositar_carga", "recuperar_carga", "probar_carga")
VERSION = "1.0.0"


def _positive_int(value, default=1):
    if value is None:
        return default
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number) or not number.is_integer() or not 1 <= number <= 100:
        return None
    return int(number)


def _strength(material, person):
    data = person.get("materials", {}).get(material) or {}
    return max(0., float(data.get("resistencia", 0)))


def _mass(material, person):
    return float(properties(material, person.get("materials", {}))["density"])


def load_limit(structure, person, components=None):
    """Capacidad de carga, escala abstracta; solo se revela tras probarla.

    Una superficie amplia sin apoyos adicionales no recibe resistencia gratis.
    Las obras anteriores sin geometría siguen teniendo una capacidad conservadora.
    """
    parts = components if components is not None else structure.get("components")
    if not isinstance(parts, list) or not parts:
        parts = [{"material": m, "condition": 1.0}
                 for m in structure.get("materials", [])] if components is None else []
    if not parts:
        return 0.
    geometry = structure.get("geometry") or {}
    shape = geometry.get("shape", "macizo")
    factor = {"plataforma": 1.0, "macizo": .55, "hueco": .35}.get(shape, .55)
    raw_size = geometry.get("size", len(parts))
    try:
        size = float(raw_size)
    except (TypeError, ValueError, OverflowError):
        size = float(len(parts))
    if not math.isfinite(size) or size <= 0:
        size = float(len(parts))
    span = min(1.0, max(.45, len(parts) / size))
    strength = 0.
    for piece in parts:
        material = piece.get("material", "")
        condition = piece.get("condition", 1.)
        try:
            condition = float(condition)
        except (TypeError, ValueError, OverflowError):
            condition = 0.
        if not math.isfinite(condition):
            condition = 0.
        strength += _strength(material, person) * min(1., max(0., condition))
    return round(strength * factor * span, 3)


def stored_load(structure, person):
    cargo = structure.get("cargas_almacenadas") or {}
    if not isinstance(cargo, dict):
        return 0.
    return round(sum(_mass(m, person) * n for m, n in cargo.items()
                     if isinstance(n, int) and not isinstance(n, bool) and n > 0), 3)


def _accessible(world, person, requested):
    kind, obj = find_object(world, person, requested)
    if kind != "structure" or not obj:
        return None
    pos, here = obj.get("pos", []), person.get("pos", [])
    if len(pos) != 3 or len(here) != 3 or pos[2] != here[2]:
        return None
    if abs(pos[0]-here[0])+abs(pos[1]-here[1]) > 1:
        return None
    return obj


def _record(person, method, structure, material, quantity, before, after, **details):
    person["_last_capability_evidence"] = {
        "op": "interact", "method": method, "capability": "cargas_estructurales",
        "version": VERSION, "source_id": structure["id"],
        "destination_id": structure["id"], "revision": structure.get("revision", 1),
        "material": material, "quantity": quantity, "before": before, "after": after,
        "clock_minutes": round(person.get("clock_minutes", 0), 2), **details,
    }


def interact(world, person, step, rng=None):
    method = str(step.get("method") or "").strip().casefold()
    person.pop("_last_capability_evidence", None)
    requested = step.get("item") or step.get("target") or step.get("destination") or step.get("source")
    obj = _accessible(world, person, requested)
    if not obj:
        return 5, ["Necesito una construcción fija identificada por ID y a una casilla de distancia como máximo."], False, False
    material = str(step.get("material") or "").strip().casefold()
    quantity = _positive_int(step.get("quantity"))
    if not material or material not in person.get("materials", {}) or quantity is None:
        return 5, ["Indicá un material conocido y una cantidad entera positiva (1–100)."], False, False
    inventory = person.get("inventory", {})
    current = dict(obj.get("cargas_almacenadas") or {})
    existing = current.get(material, 0)
    limit = load_limit(obj, person)
    applied = stored_load(obj, person)
    sample_mass = round(quantity * _mass(material, person), 3)

    if method == "probar_carga":
        if inventory.get(material, 0) < quantity:
            return 5, ["Para ensayar una carga necesito las muestras materiales reales en mi inventario."], False, False
        supported = applied + sample_mass <= limit + 1e-9
        obj.setdefault("ensayos_de_carga", []).append({
            "revision": obj.get("revision", 1), "material": material,
            "quantity": quantity, "load": sample_mass,
            "limit": limit, "stored_before": applied, "supported": supported,
            "at_minute": round(person.get("clock_minutes", 0), 2),
        })
        obj["ensayos_de_carga"] = obj["ensayos_de_carga"][-24:]
        _record(person, method, obj, material, quantity,
                {"stored_mass": applied}, {"stored_mass": applied},
                irreversible=False, supported=supported,
                load=sample_mass, limit=limit)
        verdict = "soportó" if supported else "no soportó"
        return 20, [
            f"Ensayé temporalmente {quantity} lotes de {material} sobre {obj['id']}; "
            f"la estructura {verdict} la carga. Masa adicional {sample_mass}, "
            f"carga existente {applied}, límite estático medido {limit} (unidades abstractas).",
            "Retiré las muestras del ensayo: el inventario y la carga almacenada no cambiaron.",
        ], True, True

    if method == "depositar_carga":
        if inventory.get(material, 0) < quantity:
            return 5, ["No llevo suficientes lotes de ese material para depositarlos."], False, False
        if applied + sample_mass > limit + 1e-9:
            return 5, [
                f"La carga propuesta superaría el límite estático de esta estructura. "
                "Primero puedo ensayarla o reforzar sus componentes."
            ], False, False
        # Transferencia física de los lotes: ambas reservas se validan
        # y se actualizan en una sola operación conservativa.
        try:
            transfer_units(inventory,material,current,material,quantity)
        except ResourceBalanceError:
            return 5,["La reserva no permite depositar esa carga sin perder unidades."],False,False
        obj["cargas_almacenadas"] = current
        after = round(applied + sample_mass, 3)
        _record(person, method, obj, material, quantity,
                {"source": inventory[material]+quantity, "destination": existing,
                 "stored_mass": applied},
                {"source": inventory[material], "destination": current[material],
                 "stored_mass": after}, load=sample_mass, limit=limit)
        return 15, [
            f"Deposité {quantity} lotes de {material} sobre {obj['id']}; "
            f"el inventario disminuyó y la carga almacenada pasó de {applied} a {after}."
        ], True, True

    if method == "recuperar_carga":
        if not isinstance(existing, int) or quantity > existing:
            return 5, ["No hay esa cantidad de material almacenada en la construcción."], False, False
        old_inventory = inventory.get(material, 0)
        try:
            receipt=transfer_units(current,material,inventory,material,quantity)
        except ResourceBalanceError:
            return 5,["El balance de materiales almacenados es inválido; no se recuperó carga."],False,False
        if receipt.source_after==0:
            current.pop(material,None)
        obj["cargas_almacenadas"] = current
        after = round(applied - sample_mass, 3)
        _record(person, method, obj, material, quantity,
                {"source": existing, "destination": old_inventory, "stored_mass": applied},
                {"source": current.get(material, 0), "destination": inventory[material],
                 "stored_mass": after}, load=sample_mass, limit=limit)
        return 12, [
            f"Recuperé {quantity} lotes de {material} desde {obj['id']}; "
            "regresaron a mi inventario, sin crear material."
        ], True, True

    return 5, [f"El método {method!r} no pertenece a cargas estructurales."], False, False


def preflight_intervention(person, structure, mode, chosen, materials):
    """No permitir que la reforma/desmontaje haga desaparecer carga depositada."""
    if not structure.get("cargas_almacenadas"):
        return None
    if mode == "all":
        return "Hay materiales almacenados en la obra. Debo recuperar toda la carga antes de desmontarla."
    parts = list(structure.get("components", []))
    if mode in ("remove", "replace") and chosen in parts:
        parts.remove(chosen)
    if mode in ("add", "replace"):
        parts.extend({"material": m, "condition": 1.0} for m in materials)
    if mode == "repair" and chosen in parts:
        parts = [dict(piece, condition=min(1., piece.get("condition", 1.) + .25 * len(materials)))
                 if piece is chosen else piece for piece in parts]
    proposed_limit = load_limit(structure, person, parts)
    required = stored_load(structure, person)
    if required > proposed_limit + 1e-9:
        return (f"La modificación dejaría una capacidad de {proposed_limit}, "
                f"menor que la carga existente {required}. Recuperar materiales o reforzar antes.")
    return None
