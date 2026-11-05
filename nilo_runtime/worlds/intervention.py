"""Etapa 12: validación y confirmación aislada de reformas y desmontajes.

La operación física se ejecuta sobre copias pequeñas del objeto y de las
reservas afectadas. No se duplica el mapa: se intercambian únicamente las
referencias a la entidad intervenida y los lotes de inventario verificados.
El código específico de la obra se inyecta como callback: este módulo no
importa construction.py, world.py ni la aplicación.
"""
from __future__ import annotations

from copy import deepcopy
from nilo_runtime.worlds.resources import (
    ResourceBalanceError, material_counts, check_materials,
)


def _fail(text):
    return 5,[text],False,False


def _preflight(world, person, step, kind, obj, physical_materials,
               check_contents, check_loads):
    op=str(step.get("op","")).lower()
    if kind=="structure":
        pos=obj.get("pos",[]);here=person["pos"]
        if len(pos)!=3 or pos[2]!=here[2] or abs(pos[0]-here[0])+abs(pos[1]-here[1])>1:
            return _fail("Para modificar esa obra primero debo acercarme a ella.")
    if op=="modify":
        mode=str(step.get("mode","add")).lower()
        if mode not in ("add","replace","remove","repair"):
            return _fail("Modificación inválida: usar add, replace, remove o repair.")
    elif op=="dismantle":
        mode="all" if step.get("all",True) else "remove"
    else:
        return _fail("Operación de intervención no reconocida.")

    raw=step.get("materials",[])
    raw=raw if isinstance(raw,list) else []
    mats=[str(m).strip().lower() for m in raw[:8]]
    try:
        costs=material_counts(mats)
    except ResourceBalanceError:
        return _fail("La intervención contiene materiales inválidos.")
    if mode in ("add","replace","repair"):
        if not mats:
            return _fail("Para esa intervención necesito indicar materiales nuevos que voy a consumir.")
        if any(m not in person.get("materials",{}) for m in costs):
            return _fail("Uno de los materiales propuestos no existe como material constructivo conocido.")
        try:
            sufficient=check_materials(person["inventory"],costs)
        except ResourceBalanceError:
            sufficient=False
        if not sufficient:
            return _fail("No tengo suficientes materiales para intervenir el objeto.")

    preview=deepcopy(obj)
    if not isinstance(preview.get("components"),list):
        preview["components"]=[
            {"id":f"_previo_{i}","material":m,"condition":1.0}
            for i,m in enumerate(physical_materials(obj))]
    comps=preview["components"]
    identifier=str(step.get("component","")).strip().casefold()
    chosen=next((c for c in comps if str(c.get("id","")).casefold()==identifier),
                None) if identifier else None
    if chosen is None and identifier:
        matches=[c for c in comps if str(c.get("material","")).casefold()==identifier]
        if len(matches)==1:chosen=matches[0]
    if mode in ("replace","remove","repair") and chosen is None:
        if mode=="remove":
            return _fail("Para desmontar parcialmente necesito indicar una pieza concreta.")
        return _fail("Debo indicar el ID de un componente existente para intervenirlo.")
    if mode=="repair":
        try:
            intact=float(chosen.get("condition",1))>=.95
        except (TypeError,ValueError,OverflowError):
            intact=True
        if intact:
            return _fail("Esa pieza no presenta desgaste que justifique repararla.")
    if mode=="add" and len(comps)+len(mats)>40:
        return _fail("La ampliación supera el máximo de componentes que puedo representar.")
    issue=check_contents(person,preview,mode,chosen,mats)
    if issue:return _fail(issue)
    if kind=="structure":
        issue=check_loads(person,preview,mode,chosen,mats)
        if issue:return _fail(issue)
    return None


def execute_prepared(world,person,step,find_object,physical_materials,
                     perform,check_contents,check_loads):
    """Devuelve el contrato de cuatro campos y confirma solo si result[2]."""
    kind,obj=find_object(world,person,step.get("item") or
                         step.get("target") or step.get("object"))
    if not obj:
        return _fail("No identifico un objeto existente; necesito su ID o nombre exacto.")
    refused=_preflight(world,person,step,kind,obj,physical_materials,
                       check_contents,check_loads)
    if refused is not None:return refused

    candidate=deepcopy(obj)
    temporary_world=dict(world)
    temporary_person=dict(person)
    temporary_world["structures"]=[candidate if x is obj else x
                                   for x in world.get("structures",[])]
    temporary_world["retired_structures"]=list(world.get("retired_structures",[]))
    temporary_person["items"]=[candidate if x is obj else x
                               for x in person.get("items",[])]
    temporary_person["retired_items"]=list(person.get("retired_items",[]))
    temporary_person["inventory"]=dict(person["inventory"])
    try:
        result=perform(temporary_world,temporary_person,step)
    except (ResourceBalanceError,TypeError,ValueError,KeyError,IndexError,OverflowError):
        return _fail("El objeto no admite una intervención físicamente consistente; no modifiqué reservas ni piezas.")
    if not result[2]:return result

    # Mantener las referencias existentes (UI, cuaderno, mundo) y aplicar el
    # resultado del borrador completo. Un fallo nunca alcanza este punto.
    for key in tuple(obj):
        if key not in candidate:obj.pop(key,None)
    obj.update(candidate)
    inventory=person["inventory"]
    for key in tuple(inventory):
        if key not in temporary_person["inventory"]:inventory.pop(key,None)
    inventory.update(temporary_person["inventory"])
    if kind=="structure":
        world.setdefault("structures",[])[:]=[
            obj if x is candidate else x for x in temporary_world["structures"]]
        retired=temporary_world["retired_structures"]
        if retired!=world.get("retired_structures",[]):
            world.setdefault("retired_structures",[])[:]=[
                obj if x is candidate else x for x in retired]
    else:
        person.setdefault("items",[])[:]=[
            obj if x is candidate else x for x in temporary_person["items"]]
        retired=temporary_person["retired_items"]
        if retired!=person.get("retired_items",[]):
            person.setdefault("retired_items",[])[:]=[
                obj if x is candidate else x for x in retired]
    return result
