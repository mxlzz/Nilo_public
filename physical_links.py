"""Identidades físicas asociadas a una acción, sin inferencias por texto libre.

Se almacenan como evidencia de medición y no modifican el mundo.
Las cantidades de inventario son saldos, no objetos físicos nuevos.
"""
from __future__ import annotations


def snapshot(world, person):
    def records(items):
        return {r["id"]: {"name":r.get("name",""),"revision":r.get("revision",1)}
                for r in items if isinstance(r,dict) and isinstance(r.get("id"),str)}
    return {"tool":records(person.get("items",[])),
            "construction":records(world.get("structures",[]))}


def entities_for_action(previous, world, person, step, measurement):
    """Identifica creación/modificación/retiro y uso verificable por ID."""
    if not isinstance(previous,dict):return []
    after=snapshot(world,person)
    effects={}
    for kind in ("tool","construction"):
        earlier=previous.get(kind,{})
        current=after.get(kind,{})
        for id in current.keys()-earlier.keys():
            effects[kind,id]="creada"
        for id in earlier.keys()-current.keys():
            effects[kind,id]="retirada"
        for id in earlier.keys()&current.keys():
            if earlier[id].get("revision")!=current[id].get("revision"):
                effects[kind,id]="modificada"

    # Referencias explícitas a una instancia única. No basta la coincidencia
    # de un nombre en una nota o descripción genérica de la acción.
    op=str(step.get("op",""))
    if op in ("use","inspect","modify","dismantle","experiment","excavate","assemble"):
        for field in ("item","tool_id","construction_id"):
            value=step.get(field)
            if not isinstance(value,str) or not value:continue
            for kind in ("tool","construction"):
                existing=after.get(kind,{})|previous.get(kind,{})
                selected=value if value in existing else None
                if selected is None and measurement.get("success"):
                    matches=[id for id,v in existing.items()
                             if v.get("name","").casefold()==value.casefold()]
                    if len(matches)==1:selected=matches[0]
                if selected is not None and (kind,selected) not in effects:
                    effects[kind,selected]="consultada" if op=="inspect" else "ensayada"
    # Las transferencias no alteran la revisión de un recipiente. Vinculamos
    # SOLO los IDs de objetos incluidos en la evidencia física de esta acción.
    if op in ("interact","drink") and measurement.get("success"):
        physical=measurement.get("physical")
        proof=(physical.get("conditions") if isinstance(physical,dict)
               and physical.get("kind")=="capability" else None)
        if isinstance(proof,dict) and proof.get("capability")=="contenidos":
            role={
                "transferir":("contenido transferido (origen)","contenido transferido (destino)"),
                "llenar":(None,"contenido recargado"),
                "rellenar":(None,"contenido recargado"),
                "beber":("agua consumida de",None),
                "descargar":("contenido descargado",None),
                "guardar":(None,"material almacenado"),
                "retirar":("material retirado",None)
            }.get(proof.get("method"))
            if role:
                for field,relation in zip(("source_id","destination_id"),role):
                    identity=proof.get(field)
                    if not relation or not isinstance(identity,str):continue
                    for kind in ("tool","construction"):
                        existing=after.get(kind,{})|previous.get(kind,{})
                        if identity in existing and (kind,identity) not in effects:
                            effects[kind,identity]=relation
    # Un refugio usado en un descanso se acredita por el registro corporal:
    # misma casilla, categoría habitáculo y medición refugiada.
    if step.get("op")=="rest" and measurement.get("condition")=="refugio":
        origin=measurement.get("start",{}).get("position")
        for building in world.get("structures",[]):
            if (building.get("category")=="habitaculo" and
                    building.get("pos")==origin and isinstance(building.get("id"),str)):
                effects.setdefault(("construction",building["id"]),"descanso_en")
    return [{"category":kind,"id":id,"relation":relation}
            for (kind,id),relation in sorted(effects.items())]
