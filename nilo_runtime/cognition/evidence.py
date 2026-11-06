"""Referencias verificables de evidencia; clasificación sin inventar conclusiones.

Cada ID señala un registro existente de una fuente concreta. Una medición
archivada fuera de la ventana activa no se convierte en una prueba falsa ni
se declara inexistente: se marca como referencia histórica no resuelta.
Los metadatos proyectados son copias; no escriben en el mundo ni en SQLite.
"""
from __future__ import annotations
from copy import deepcopy

SOURCES = (
    ("medicion", "measurements", "med-"),
    ("accion", "action_outcomes", "act-"),
    ("prediccion", "prediction_log", "pred-"),
    ("conclusion", "conclusions", "con-"),
    ("investigacion", "research", ""),
)
DERIVED_OPERATIONS = frozenset((
    "conclude", "compare", "manual", "write", "design",
    "propose", "report_issue",
))
CONCLUSION_TYPES = {
    "observacion_comprobada": "observacion",
    "observacion_no_evaluable": "limite_del_modelo",
    "comparacion_medida": "comparacion_descriptiva",
    "comprobada": "conclusion_con_mediciones",
}

def _records(person, source):
    rows=person.get(source,[]) if isinstance(person,dict) else []
    return rows if isinstance(rows,list) else []

def reference_index(person):
    """Índice transitorio sin mutación ni entradas obtenidas por similitud textual."""
    index={}
    for kind, source, prefix in SOURCES:
        for row in _records(person,source):
            if not isinstance(row,dict):continue
            rid=row.get("id")
            # Saves legados admiten IDs sin prefijo (p. ej. "m1").
            # La procedencia procede de la colección tipada, no del nombre.
            if not isinstance(rid,str) or not rid:
                continue
            if rid in index:
                # El primer registro de la fuente de mayor autoridad permanece.
                continue
            index[rid]={"id":rid,"tipo":kind,"registro":row}
    return index

def reference(person, rid, *, expected=None):
    """Resolver ID exacto; ninguna coincidencia por título crea procedencia."""
    if not isinstance(rid,str) or not rid:
        return {"id":rid if isinstance(rid,str) else None,
                "tipo":expected or "desconocido","trazabilidad":"id_invalido"}
    found=reference_index(person).get(rid)
    if found is None:
        return {"id":rid,"tipo":expected or "historico",
                "trazabilidad":"fuera_de_memoria_activa"}
    if expected is not None and found["tipo"]!=expected:
        return {"id":rid,"tipo":found["tipo"],"trazabilidad":"tipo_incompatible"}
    result={"id":rid,"tipo":found["tipo"],"trazabilidad":"registro_disponible"}
    row=found["registro"]
    if found["tipo"]=="medicion":
        result["estado"]=row.get("evaluation_status","historico_sin_estado")
        result["operacion"]=row.get("op")
        result["ensayo_fisico"]=bool(row.get("op") not in DERIVED_OPERATIONS)
    elif found["tipo"]=="accion":
        result["estado"]=row.get("evaluation_status", "sin_clasificacion")
    elif found["tipo"]=="prediccion":
        result["estado"]=row.get("status","sin_clasificacion")
    return result

def measured_records(person, ids, *, minimum=1, maximum=6,
                     allow_derived=False):
    """Obtiene ensayos por ID, mismo orden solicitado; ninguno se infiere del texto."""
    if (not isinstance(ids,list) or not minimum<=len(ids)<=maximum
            or any(not isinstance(rid,str) or not rid for rid in ids)
            or len(set(ids))!=len(ids)):
        return None
    indexed={r.get("id"):r for r in _records(person,"measurements")
             if isinstance(r,dict) and isinstance(r.get("id"),str)
             and r.get("id")}
    trials=[indexed.get(rid) for rid in ids]
    if any(row is None for row in trials):
        return None
    if not allow_derived and any(row.get("op") in DERIVED_OPERATIONS for row in trials):
        return None
    return trials

def projected_knowledge(person, *, limit=12):
    """Proyectar conocimiento registrado con una fuente exacta o marca legacy.

    Un texto igual no demuestra una ley universal: acredita a lo sumo el
    resultado de UNA acción. No se empareja por semejanza semántica.
    """
    stored=person.get("knowledge",{}) if isinstance(person,dict) else {}
    if not isinstance(stored,dict):
        return []
    actions=[row for row in _records(person,"action_outcomes")
             if isinstance(row,dict)]
    result=[]
    for key,statement in list(stored.items())[-max(0,int(limit)):]:
        text=str(statement).strip()
        if not text:continue
        source_op=("use" if str(key).startswith(("uso|","interaccion|","flotacion|","ensamblaje|"))
                   else "experiment" if "|" in str(key) else None)
        candidate=next((row for row in reversed(actions)
            if row.get("op")==source_op
            and text in [str(v).strip() for v in row.get("facts",[])
                         if isinstance(v,str)]),None) if source_op else None
        entry={"clave":str(key),"resultado":text[:240],
               "naturaleza":"resultado_registrado_no_ley_universal"}
        if candidate:
            action_id=candidate.get("id")
            if isinstance(action_id,str):
                entry["accion_id"]=action_id
            status=candidate.get("evaluation_status")
            entry["estado"]=("limite_sin_modelo" if status=="no_evaluable"
                else "ensayo_realizado" if candidate.get("success")
                else "fallo_observado")
            mid=(candidate.get("physical_result") or {}).get("measurement_id")
            if isinstance(mid,str):
                entry["fuente_medicion"]=reference(person,mid,expected="medicion")
            entry["trazabilidad"]="accion_registrada"
        else:
            entry["estado"]="sin_verificacion_por_id"
            entry["trazabilidad"]="conocimiento_historico_sin_id"
        result.append(entry)
    return result


def projected_conclusions(person, *, limit=15):
    """La etiqueta 'comprobada' histórica no oculta referencias ausentes."""
    result=[]
    for row in _records(person,"conclusions")[-max(0,int(limit)):]:
        if not isinstance(row,dict):continue
        item=deepcopy(row)
        evidence_ids=row.get("evidence_ids")
        refs=[reference(person,rid,expected="medicion") for rid in evidence_ids] if (
            isinstance(evidence_ids,list)) else []
        if not refs:
            trace="sin_ids_de_medicion"
        elif all(r["trazabilidad"]=="registro_disponible"
                 and r.get("ensayo_fisico") for r in refs):
            trace="ensayos_disponibles"
        elif any(r["trazabilidad"]=="tipo_incompatible" or
                 (r["trazabilidad"]=="registro_disponible"
                  and not r.get("ensayo_fisico")) for r in refs):
            trace="referencias_no_fisicas"
        else:
            trace="referencias_historicas_no_disponibles"
        item["naturaleza"]=CONCLUSION_TYPES.get(row.get("status"),
                                                "interpretacion_no_clasificada")
        item["trazabilidad"]=trace
        item["fuentes_de_evidencia"]=refs
        result.append(item)
    return result

def projected_research(person, *, limit=7):
    """Hipótesis y evidencias separadas: un texto de evidencia no prueba un efecto."""
    result=[]
    for row in _records(person,"research")[-max(0,int(limit)):]:
        if not isinstance(row,dict):continue
        item={k:deepcopy(v) for k,v in row.items()
              if k not in ("evidence",)}
        entries=row.get("evidence",[])
        if isinstance(entries,list):
            item["registros_narrativos"]=len(entries)
        refs=row.get("evidence_ids")
        if isinstance(refs,list):
            item["fuentes_de_evidencia"]=[
                reference(person,rid,expected="medicion") for rid in refs]
        item["naturaleza"]="hipotesis_en_investigacion"
        if row.get("state")=="concluida":
            sources=item.get("fuentes_de_evidencia") or []
            if not sources:
                item["naturaleza"]="investigacion_cerrada_sin_ids"
            elif all(r.get("trazabilidad")=="registro_disponible"
                     and r.get("ensayo_fisico") for r in sources):
                item["naturaleza"]="investigacion_cerrada_con_ensayos_disponibles"
            else:
                item["naturaleza"]="investigacion_cerrada_con_referencias_historicas"
        result.append(item)
    return result
