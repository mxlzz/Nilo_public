"""Capacidad instalada: manejo conservativo de contenido de recipientes.

Las cantidades son unidades abstractas del motor, NO litros. Solo un material
por recipiente y ninguna reacción, evaporación, potabilización o charco.
"""
from __future__ import annotations
import math

from physics import body_physics, evaluate_containment
from construction import find_object
from survival import ensure_needs
from nilo_runtime.worlds.resources import ResourceBalanceError, transfer_units


def capacity(obj,person,material="agua"):
    """Límite físico representable; no confundir volumen con retención eficaz."""
    body=body_physics(obj.get("materials",[]),obj.get("geometry") or {},person.get("materials",{}))
    if body["shape"]!="hueco":
        return 0.0
    if material=="agua":
        return evaluate_containment(obj,"agua",person.get("materials",{}))["quantity"]
    return round(body["capacity"],2)


def _quantity(raw,default=None,*,integer=False):
    if raw is None:
        return default
    if isinstance(raw,bool):
        return None
    try:
        v=float(raw)
    except (TypeError,ValueError,OverflowError):
        return None
    if not math.isfinite(v) or v<=0 or v>100 or (integer and not v.is_integer()):
        return None
    measured=int(v) if integer else round(v,2)
    return measured if measured>0 else None


def _accessible(world,person,identity):
    kind,obj=find_object(world,person,identity)
    if not obj:
        return None
    if kind=="structure":
        pos=obj.get("pos",[])
        here=person["pos"]
        if len(pos)!=3 or pos[2]!=here[2] or abs(pos[0]-here[0])+abs(pos[1]-here[1])>1:
            return None
    if obj.get("durability",100)<=0:
        return None
    return obj


def _contents(obj):
    contents=obj.get("contents") or {}
    if not isinstance(contents,dict):
        return "",0.0
    try:
        quantity=float(contents.get("quantity") or 0)
    except (TypeError,ValueError,OverflowError):
        quantity=0
    if not math.isfinite(quantity):
        quantity=0
    return str(contents.get("material") or ""),max(0.0,quantity)


def _set_contents(obj,material,quantity,person,origin):
    qty=round(max(0.,quantity),2)
    obj["contents"]=({"material":material,"quantity":qty,"unit":"unidad_abstracta",
                      "revision":obj.get("revision",1),
                      "origin":origin,"at_minute":round(person.get("clock_minutes",0),2)}
                     if qty>0 else {})


def _record(person,step,kind,source,destination,material,quantity,before,after):
    entry={"op":"interact","method":kind,"capability":"contenidos",
           "version":"1.0.0","source_id":source,"destination_id":destination,
           "material":material,"quantity":quantity,"before":before,"after":after,
           "clock_minutes":round(person.get("clock_minutes",0),2)}
    person["_last_capability_evidence"]=entry
    return entry


def _fail(message):
    return 5,[message],False,False


def interact(world,person,step,rng=None):
    method=str(step.get("method") or "").strip().casefold()
    person.pop("_last_capability_evidence",None)
    source_id=step.get("source") or step.get("item")
    dest_id=step.get("destination")
    source=_accessible(world,person,source_id) if source_id else None
    dest=_accessible(world,person,dest_id) if dest_id else None
    if method in ("llenar","rellenar"):
        vessel=dest or source
        if not vessel:return _fail("Para llenar necesito un recipiente existente, accesible y utilizable.")
        x,y,z=person["pos"]
        from world import DIRS,valid,tile
        if z!=0 or not any(valid(x+dx,y+dy) and tile(world,x+dx,y+dy,z)=="~" for dx,dy in DIRS):
            return _fail("Para llenar necesito una fuente de agua adyacente y accesible.")
        material,old=_contents(vessel)
        if old>0 and material!="agua":return _fail("Debo retirar el contenido incompatible antes de llenar con agua.")
        limit=capacity(vessel,person,"agua")
        free=round(max(0,limit-old),2)
        if free<=0:return _fail("El recipiente no tiene capacidad libre para almacenar agua.")
        q=_quantity(step.get("quantity"),free)
        if q is None or q>free:return _fail(f"La cantidad solicitada supera el espacio disponible ({free}) o es inválida.")
        _set_contents(vessel,"agua",old+q,person,"fuente_ambiental")
        _record(person,step,method,"agua_ambiental",vessel["id"],"agua",q,
                {"source":None,"destination":old},{"source":None,"destination":round(old+q,2)})
        return 16,[f"Agregué {q} unidades de agua a '{vessel['name']}' ({old} → {round(old+q,2)}; capacidad eficaz {limit}). La fuente ambiental no tiene balance finito modelado; no comprobé potabilidad."],True,True
    if method=="transferir":
        if not source or not dest or source is dest:
            return _fail("Transferir exige dos recipientes existentes, distintos y accesibles.")
        material,old=_contents(source)
        dest_mat,dest_old=_contents(dest)
        if old<=0:return _fail("El recipiente de origen está vacío.")
        if dest_old>0 and material!=dest_mat:return _fail("El destino tiene contenido incompatible.")
        limit=capacity(dest,person,material)
        free=round(max(0,limit-dest_old),2)
        suggested=(min(old,free) if material=="agua" else
                   int(math.floor(min(old,free))))
        q=_quantity(step.get("quantity"),suggested,integer=material!="agua")
        if q is None or q>old or q>free:return _fail(f"No se puede transferir esa cantidad: origen {old}, espacio disponible {free}.")
        # El agua conserva la precisión decimal que ya tenía. Las transferencias
        # de sólidos usan el mismo balance entero del inventario/depósitos.
        if material!="agua":
            if not float(old).is_integer() or not float(dest_old).is_integer():
                return _fail("El contenido sólido existente no tiene unidades enteras válidas.")
            left={material:int(old)}
            right={material:int(dest_old)}
            try:
                receipt=transfer_units(left,material,right,material,int(q),
                                       maximum=int(math.floor(limit)))
            except ResourceBalanceError:
                return _fail("No se puede transferir esa cantidad sin violar el balance.")
            source_after=receipt.source_after
            dest_after=receipt.destination_after
        else:
            source_after=old-q
            dest_after=dest_old+q
        _set_contents(source,material,source_after,person,"transferencia")
        _set_contents(dest,material,dest_after,person,source["id"])
        _record(person,step,method,source["id"],dest["id"],material,q,
                {"source":old,"destination":dest_old},
                {"source":round(old-q,2),"destination":round(dest_old+q,2)})
        return 18,[f"Transferí {q} unidades de {material} de {source['id']} a {dest['id']}. Origen {old} → {round(old-q,2)}; destino {dest_old} → {round(dest_old+q,2)}. No se creó contenido."],True,True
    if method=="beber":
        if not source:return _fail("Beber agua almacenada exige identificar el recipiente accesible.")
        material,old=_contents(source)
        if material!="agua" or old<.18:return _fail("No hay al menos 0,18 unidades de agua almacenada en ese recipiente.")
        n=ensure_needs(person)
        if n["hidratacion"]>=100:return _fail("La hidratación ya está al máximo; no consumí reservas.")
        q=_quantity(step.get("quantity"),.18)
        if q is None or q>old:return _fail("No hay suficiente agua para beber esa cantidad.")
        before=n["hidratacion"]
        n["hidratacion"]=round(min(100.,before+27*q/.18),2)
        _set_contents(source,"agua",old-q,person,"consumo_voluntario")
        _record(person,step,method,source["id"],"persona","agua",q,
                {"source":old,"hidratacion":before},
                {"source":round(old-q,2),"hidratacion":n["hidratacion"]})
        return 8,[f"Bebí voluntariamente {q} unidades de agua de {source['id']}. Reserva {old} → {round(old-q,2)}; hidratación {before} → {n['hidratacion']}. No se comprobó potabilidad."],True,True
    if method=="descargar":
        if not source:return _fail("Descargar exige un recipiente existente y accesible.")
        material,old=_contents(source)
        if material!="agua" or old<=0:return _fail("La descarga ambiental implementada solo acepta agua almacenada.")
        q=_quantity(step.get("quantity"),old)
        if q is None or q>old:return _fail("No hay esa cantidad para descargar.")
        _set_contents(source,"agua",old-q,person,"descarga_ambiental")
        _record(person,step,method,source["id"],"ambiente_sin_reserva","agua",q,
                {"source":old},{"source":round(old-q,2)})
        return 10,[f"Descargué {q} unidades de agua de {source['id']} al entorno. La reserva pasó de {old} a {round(old-q,2)}. No se simula charco ni recuperación posterior."],True,True
    if method=="guardar":
        if not dest:return _fail("Guardar requiere un recipiente identificado y accesible.")
        material=str(step.get("material") or "").strip().casefold()
        if not material or material=="agua":return _fail("Para agua usá llenar o transferir; guardar requiere un sólido del inventario.")
        old_material,old=_contents(dest)
        if old>0 and old_material!=material:return _fail("No se mezclan materiales distintos en un único recipiente.")
        inv=person.get("inventory",{})
        q=_quantity(step.get("quantity"),1,integer=True)
        if q is None or q>inv.get(material,0) or q>round(max(0,capacity(dest,person,material)-old),2):
            return _fail("No hay material sólido suficiente o capacidad libre.")
        if not float(old).is_integer():
            return _fail("El contenido sólido existente no tiene unidades enteras válidas.")
        hold={material:int(old)}
        try:
            receipt=transfer_units(inv,material,hold,material,q,
                                   maximum=int(math.floor(capacity(dest,person,material))))
        except ResourceBalanceError:
            return _fail("No hay material sólido suficiente o capacidad libre.")
        _set_contents(dest,material,receipt.destination_after,person,"inventario")
        _record(person,step,method,"inventario",dest["id"],material,q,
                {"source":receipt.source_before,"destination":old},
                {"source":receipt.source_after,"destination":receipt.destination_after})
        return 12,[f"Guardé {q} unidades de {material} en {dest['id']}; se descontaron del inventario."],True,True
    if method=="retirar":
        if not source:return _fail("Retirar exige un recipiente identificado y accesible.")
        material,old=_contents(source)
        if not material or material=="agua" or old<=0:
            return _fail("Para agua usá transferir o descargar; retirar devuelve sólidos al inventario.")
        q=_quantity(step.get("quantity"),
                    int(old) if float(old).is_integer() else None,
                    integer=True)
        if q is None or q>old:return _fail("La cantidad solicitada no está almacenada.")
        inv=person.setdefault("inventory",{})
        before=inv.get(material,0)
        if not float(old).is_integer():
            return _fail("El contenido sólido existente no tiene unidades enteras válidas.")
        hold={material:int(old)}
        try:
            receipt=transfer_units(hold,material,inv,material,q)
        except ResourceBalanceError:
            return _fail("La reserva de sólidos es inválida; no hubo transferencia.")
        _set_contents(source,material,receipt.source_after,person,"retiro_inventario")
        _record(person,step,method,source["id"],"inventario",material,q,
                {"source":old,"destination":before},
                {"source":receipt.source_after,"destination":receipt.destination_after})
        return 12,[f"Retiré {q} unidades de {material} de {source['id']}; regresaron al inventario."],True,True
    return _fail(f"El método '{method}' no pertenece a esta capacidad.")


def preflight_intervention(person,obj,mode,chosen,materials):
    """Rechaza una modificación que perdería contenido sin destino físico."""
    medium,amount=_contents(obj)
    if amount<=0:
        return None
    if mode=="all":
        return "Antes de desmontar el recipiente debo retirar, transferir o descargar su contenido."
    comps=list(obj.get("components",[]))
    if mode in ("remove","replace") and chosen in comps:
        comps.remove(chosen)
    if mode in ("add","replace"):
        comps.extend({"material":m} for m in materials)
    proposed=[str(c["material"]) for c in comps]
    projected={"materials":proposed,"geometry":obj.get("geometry") or {}}
    effective=capacity(projected,person,medium)
    if amount>effective+1e-8:
        return f"La intervención reduciría la capacidad efectiva a {effective}, por debajo del contenido almacenado ({amount}). Vaciar o transferir primero."
    return None
