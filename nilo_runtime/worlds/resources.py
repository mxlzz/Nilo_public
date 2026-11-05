"""Operaciones conservativas de recursos de isla_v1 (Nilo 0.7 / etapa 10).

Único dueño de extracción de depósitos, forraje y transferencia de unidades
enteras. Las consultas no mutan mapas ni inventarios. No importa el agente,
la aplicación, los proveedores o world.py. Los recursos ambientales renovables
solo aparecen conforme a la regla explícita de rebrote, nunca por narración.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import MutableMapping

from catalogo import GATHER_SOURCES, GATHER_ALIASES, TERRAINS, YIELDS
from nilo_runtime.worlds.island import DIRS, valid, tile, tile_key
from nilo_runtime.worlds.navigation import NavigationIndex, passable, move


class ResourceBalanceError(ValueError):
    """Cantidad imposible, reserva corrupta o transferencia no conservativa."""


@dataclass(frozen=True)
class StockTransfer:
    material: str
    quantity: int
    source_before: int
    source_after: int
    destination_before: int
    destination_after: int


def stock_units(store: MutableMapping, key: str) -> int:
    value = store.get(key, 0)
    if type(value) is not int or value < 0:
        raise ResourceBalanceError(f"Reserva inválida para {key!r}; no se modifica.")
    return value


def transfer_units(source: MutableMapping, source_key: str,
                   destination: MutableMapping, destination_key: str,
                   quantity: int, *, maximum: int | None = None) -> StockTransfer:
    """Validar ambos extremos ANTES de mutar; conservación y no-negatividad.

    Las cantidades materiales del inventario y los yacimientos son enteras.
    Un fallo deja ambos diccionarios intactos; no se corrige ni oculta un saldo
    negativo leído de un archivo histórico.
    """
    if source is destination and source_key == destination_key:
        raise ResourceBalanceError("El origen y destino son la misma reserva.")
    if type(quantity) is not int or quantity <= 0:
        raise ResourceBalanceError("La transferencia requiere unidades enteras positivas.")
    before_source = stock_units(source, source_key)
    before_destination = stock_units(destination, destination_key)
    if before_source < quantity:
        raise ResourceBalanceError("El origen no contiene suficientes unidades.")
    if maximum is not None:
        if type(maximum) is not int or maximum < 0:
            raise ResourceBalanceError("Capacidad de destino inválida.")
        if before_destination + quantity > maximum:
            raise ResourceBalanceError("El destino no dispone de capacidad suficiente.")
    after_source = before_source - quantity
    after_destination = before_destination + quantity
    # Todas las validaciones terminaron: estos dos valores forman una transacción.
    source[source_key] = after_source
    destination[destination_key] = after_destination
    return StockTransfer(destination_key, quantity, before_source,
                         after_source, before_destination, after_destination)


def consume_units(inventory: MutableMapping, material: str, quantity: int) -> int:
    """Consumo físico de unidades enteras: sin débito parcial ni saldo negativo."""
    if type(quantity) is not int or quantity <= 0:
        raise ResourceBalanceError("Consumo no entero o no positivo.")
    before=stock_units(inventory,material)
    if before < quantity:
        raise ResourceBalanceError("No hay reservas suficientes para consumir.")
    inventory[material] = before-quantity
    return before-quantity


def gather_material(target):
    name = " ".join(str(target or "").casefold().split())
    return name if name in GATHER_SOURCES else GATHER_ALIASES.get(name)


def nearest_known(w, person, chars):
    """Depósito REVELADO con stock y lugar de trabajo alcanzable por BFS.

    Respeta el desempate histórico distancia, depósito, posición de trabajo.
    No incorpora terreno oculto ni altera inventario/depósitos.
    """
    x, y, z = person["pos"]
    routes = NavigationIndex(w, (x, y, z), known_only=True)
    opts = []
    for key in w["revealed"]:
        tx, ty, tz = map(int, key.split(","))
        if tz != z or tile(w, tx, ty, z) not in chars:
            continue
        try:
            available=stock_units(w["deposits"], key)
        except ResourceBalanceError:
            continue  # Stock histórico inválido: jamás habilita recolección.
        if available <= 0:
            continue
        candidates = [(tx, ty)] if passable(w, tx, ty, z) else []
        candidates += [(tx + dx, ty + dy) for dx, dy in DIRS
                       if passable(w, tx + dx, ty + dy, z)]
        for cx, cy in candidates:
            distance = routes.distance((cx, cy))
            if distance is not None:
                opts.append((distance, tx, ty, cx, cy))
    if not opts:
        return None
    _, tx, ty, cx, cy = min(opts)
    return tx, ty, cx, cy


def forage_source(w, person):
    """Fuente vegetal cercana, consultada sin aplicar rebrote ni consumo."""
    x, y, z = person["pos"]
    spots = [(x + dx, y + dy) for dx, dy in [(0, 0)] + DIRS
             if valid(x + dx, y + dy) and tile(w, x + dx, y + dy, z) in ("T", ",")]
    growth = w.get("forage_growth", {})
    deposits = w.get("forage_deposits", {})
    clock = person.get("clock_minutes", 0)
    for sx, sy in spots:
        key = tile_key(sx, sy, z)
        last = growth.get(key, clock)
        cycles = int(max(0, clock - last) // 2880)
        amount = min(3, stock_units(deposits, key) + cycles) if cycles else stock_units(deposits, key) if key in deposits else 3
        if amount > 0:
            return sx, sy
    return None


def _mature_forage(w, person):
    """Aplica únicamente crecimiento por ciclos existentes (48 h), máximo 3."""
    x, y, z = person["pos"]
    spots = [(x + dx, y + dy) for dx, dy in [(0, 0)] + DIRS
             if valid(x + dx, y + dy) and tile(w, x + dx, y + dy, z) in ("T", ",")]
    # Validar todas las fuentes ANTES de acreditar cualquier rebrote:
    # una reserva histórica corrupta no puede dejar rebrote parcial.
    growth = w.get("forage_growth", {})
    deposits = w.get("forage_deposits", {})
    updates = []
    for sx, sy in spots:
        key = tile_key(sx, sy, z)
        current = stock_units(deposits, key) if key in deposits else 3
        last = growth.get(key, person.get("clock_minutes", 0))
        cycles = int(max(0, person.get("clock_minutes", 0) - last) // 2880)
        if cycles:
            updates.append((key,min(3,current+cycles),last+cycles*2880))
    if updates:
        dst_growth = w.setdefault("forage_growth", {})
        dst_deposits = w.setdefault("forage_deposits", {})
        for key, new_amount, new_stamp in updates:
            dst_deposits[key] = new_amount
            dst_growth[key] = new_stamp


def forage_action(w, person):
    """Una porción obtenida del stock vegetal, sin inventario negativo."""
    inv = person["inventory"]
    try:
        held = stock_units(inv, "alimento")
    except ResourceBalanceError:
        return 5, ["La reserva de alimentos es inválida; no se acredita ningún recurso."], False, False
    if held >= 12:
        return 3, [f"Tengo {inv['alimento']} porciones guardadas; no necesito recolectar más ahora. "
                   "Puedo consumir reservas o dedicarme a otra actividad."], False, False
    try:
        _mature_forage(w, person)
        source = forage_source(w, person)
    except ResourceBalanceError:
        return 5, ["La reserva vegetal contiene un saldo inválido; no se acredita ningún recurso."], False, False
    if source is None:
        return 8, ["No encontré frutos o vegetación comestible disponible en las casillas cercanas."], False, False
    sx, sy = source
    key = tile_key(sx, sy, person["pos"][2])
    deposits = w.setdefault("forage_deposits", {})
    # Depósito virtual de tres porciones antes del primer consumo.
    if key not in deposits:
        deposits[key] = 3
    try:
        transfer_units(deposits, key, inv, "alimento", 1)
    except ResourceBalanceError:
        return 8, ["La reserva vegetal no permite extraer alimento."], False, False
    w.setdefault("forage_growth", {}).setdefault(key, person.get("clock_minutes", 0))
    return 18, [f"Recolecté una porción experimental de alimento vegetal en ({sx},{sy}); tengo {inv['alimento']}."], True, True


def source_material(kind: str, requested: str):
    material = YIELDS[kind][0] if kind in YIELDS else None
    if requested == "hongo luminoso" and kind == "v":
        return requested
    return material


def harvest_at(w, person, requested: str, position):
    """Extrae del sitio físico indicado, solo si es conocido y está al alcance.

    No busca otra fuente si la reservada para una actividad se agotó o cambió.
    Retorna la duración física y el mismo contrato histórico de resultado.
    """
    try:
        tx, ty, tz = position
        if any(type(v) is not int for v in (tx, ty, tz)):
            raise ValueError
    except (TypeError, ValueError):
        return 5, ["El depósito de trabajo tiene coordenadas inválidas."], False, False
    x, y, z = person["pos"]
    if tz != z or not valid(tx, ty) or abs(tx - x) + abs(ty - y) > 1:
        return 5, ["No estoy junto al depósito elegido: no extraje materiales a distancia."], False, False
    key = tile_key(tx, ty, tz)
    if key not in set(w.get("revealed", ())):
        return 5, ["Todavía no observé ese depósito: no puedo extraer recursos de terreno oculto."], False, False
    kind = tile(w, tx, ty, tz)
    actual = source_material(kind, requested)
    if kind not in GATHER_SOURCES.get(requested, "") or actual != requested:
        return 5, [f"El depósito indicado no produce {requested}; no extraje nada."], False, False
    try:
        amount = stock_units(w["deposits"], key)
    except ResourceBalanceError:
        return 5, [f"La reserva de {requested} tiene un saldo inválido; no extraje materiales."], False, False
    if amount <= 0:
        return 8, [f"La fuente de {requested} en ({tx},{ty}) está agotada."], False, False
    quantity = min(2, amount)
    try:
        receipt = transfer_units(w["deposits"], key, person["inventory"], requested, quantity)
    except ResourceBalanceError as exc:
        return 5, [f"No pude conservar el balance de {requested}: {exc}"], False, False
    facts = [f"Recogí {quantity} {'unidad' if quantity == 1 else 'unidades'} de {requested} del "
             f"{TERRAINS[kind]} en ({tx},{ty}). Ahora tengo {receipt.destination_after}."]
    depleted = receipt.source_after == 0
    if depleted:
        facts.append("Agoté el recurso de este lugar.")
    return 12 + quantity * 5, facts, True, depleted


def cut_wood(w, person, tx, ty, z):
    """Extracción física mediante filo, conservando el stock de arboleda."""
    key = tile_key(tx, ty, z)
    try:
        if tile(w, tx, ty, z) != "T":
            return False
        if stock_units(w["deposits"], key) <= 0:
            return False
        transfer_units(w["deposits"], key, person["inventory"], "madera", 1)
        return True
    except ResourceBalanceError:
        return False


def gather_action(w,p,step,describe_findings):
    """Ejecución física de gather, misma ruta de trabajo para handler directo.

    La navegación por fases del orquestador pasa _resource_at solo tras llegar.
    Jamás sustituye un depósito reservado por otro; ningún efecto remoto antes
    de terminar la fase de extracción.
    """
    target=str(step.get('target','')).strip().lower()[:70]
    x,y,z=p['pos']
    facts=[];notable=False
    requested=gather_material(target)
    if requested is None:
        return 5,[f"No reconozco '{target}' como material o fuente de recolección. "
                  "Puedo solicitar piedra (roca), madera (arboleda), mineral oscuro "
                  "(afloramiento mineral), arcilla, fibra, cristal u hongo luminoso."],False,False
    # El motor puede fijar el depósito al comenzar el viaje. Un pin solo
    # permite una fuente revelada, compatible y físicamente adyacente.
    pin=step.get('_resource_at')
    if pin is not None:
        if not isinstance(pin,(list,tuple)) or len(pin)!=3:
            return 5,["La referencia del depósito de trabajo es inválida."],False,False
        try:
            tx,ty,tz=(int(v) if type(v) is int else None for v in pin)
        except (ValueError,TypeError):
            return 5,["La referencia del depósito de trabajo es inválida."],False,False
        if None in (tx,ty,tz):
            return 5,["La referencia del depósito de trabajo es inválida."],False,False
        if tz!=z or not valid(tx,ty) or abs(tx-x)+abs(ty-y)>1:
            return 5,["No estoy junto al depósito reservado; no extraje materiales."],False,False
        nearest=(tx,ty,x,y)
    else:
        try:
            nearest=nearest_known(w,p,GATHER_SOURCES[requested])
        except ResourceBalanceError:
            return 5,["Hay un depósito con reserva inválida; no extraje materiales."],False,False
    if nearest is None:
        return 5,[f"No tengo localizada una fuente accesible y con recursos de {requested}."],False,False
    tx,ty,wx,wy=nearest
    travel=0
    if (x,y)!=(wx,wy) and abs(tx-x)+abs(ty-y)>1:
        travel,discovered=move(w,p,(wx,wy),10)
        facts.append(f"Me acerqué {travel} tramos a la fuente de {requested} en ({tx},{ty}).")
        other=describe_findings(w,discovered)
        if other:facts.append('En el trayecto vi: '+', '.join(other)+'.');notable=True
        if tuple(p['pos'][:2])!=(wx,wy):
            facts.append(f"Todavía no llegué al depósito de {requested} y no recogí material.")
            return max(5,travel*3),facts,False,notable
    elapsed,result,worked,interesting=harvest_at(w,p,requested,(tx,ty,z))
    facts.extend(result)
    if not worked:return elapsed,facts,False,notable
    notable=notable or interesting
    duration=max(0,travel*3)+elapsed
    return duration,facts,True,notable
