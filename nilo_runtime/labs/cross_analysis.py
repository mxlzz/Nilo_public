"""Etapa 08: lectura transversal de turnos, evidencia y huellas operativas.

Una solicitud archivada = lo que estaba escrito en la petición. No inferimos
que el LLM haya leído, citado o aprovechado un dato. No inferimos resultados
de operaciones a partir de sus intenciones o de su proximidad temporal.

Solo consultas read-only sobre el mundo seleccionado por el servidor y su
sidecar exacta. No generar capturas retroactivas ni modificar el estado.
"""
from __future__ import annotations

from collections import Counter, OrderedDict
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from nilo_runtime.labs.literal_segments import index_request
from nilo_runtime.storage.llm_requests import RequestTraceStore

_CALL_ID = re.compile(r"^[a-f0-9]{32}$")
_DEFAULT_CALLS = 24
_MAX_CALLS = 48
_MAX_ATTEMPTS = 300
_MAX_BODY = 1024 * 1024
_MAX_HISTORY = 1600
_MAX_RESULTS = 45
_ID_KEYS = frozenset((
    "id", "experience_id", "experience_ids", "evidence_id", "evidence_ids",
    "source_id", "source_ids", "origin_id", "origin_ids", "related_ids",
    "measurement_id", "measurement_ids",
))
_MEMORY_FAMILIES = frozenset(("memoria", "evidencia"))


def _db(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri()+"?mode=ro",
                                 uri=True, timeout=1)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _has_table(db, name):
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)).fetchone() is not None


def _decode_record(text):
    try:
        value=json.loads(text)
        return value if isinstance(value,dict) else None
    except (TypeError,ValueError):
        return None


def _is_empty_json_literal(literal):
    try:
        data=json.loads("{"+literal+"}")
        if not isinstance(data,dict) or len(data)!=1:
            return None
        value=next(iter(data.values()))
        return value is None or value=="" or value==[] or value=={}
    except (TypeError,ValueError):
        return None


def _explicit_identifiers(value):
    """Solo igualdad de IDs en posiciones de referencia, nunca substring."""
    result=set()
    def visit(obj,depth=0):
        if depth>12:
            return
        if isinstance(obj,dict):
            for k,v in obj.items():
                if k in _ID_KEYS:
                    if isinstance(v,str) and v:
                        result.add(v)
                    elif isinstance(v,list):
                        result.update(x for x in v if isinstance(x,str) and x)
                visit(v,depth+1)
        elif isinstance(obj,list):
            for item in obj[:200]:
                visit(item,depth+1)
    visit(value)
    return result


def _attempt_rows(sidecar,limit):
    if not sidecar or not Path(sidecar).is_file():
        return [],False,0,["No hay solicitudes archivadas para la partida actual."]
    with closing(_db(sidecar)) as db:
        if not _has_table(db,"llm_requests"):
            return [],False,0,["La sidecar no tiene la tabla de solicitudes."]
        total=db.execute(
            "SELECT COUNT(DISTINCT call_id) FROM llm_requests "
            "WHERE purpose='deliberacion'").fetchone()[0]
        # La ventana se limita ANTES de indexar blobs; no cargar miles de
        # solicitudes en memoria ni confundir reintentos con turnos distintos.
        rows=db.execute(
            """SELECT rowid AS ordinal_key,attempt_id,call_id,attempt_ordinal,
                      provider,model,purpose,started_utc,simulated_at,status,
                      body,body_sha256,body_bytes
               FROM llm_requests WHERE purpose='deliberacion'
               ORDER BY rowid DESC LIMIT ?""",
            (_MAX_ATTEMPTS,)).fetchall()
    seen=OrderedDict()
    for row in rows:
        call=row["call_id"]
        if not isinstance(call,str) or not _CALL_ID.fullmatch(call):
            continue
        if call not in seen:
            seen[call]=[]
        seen[call].append(row)
        if len(seen)>limit+4:
            break
    chosen=[]
    for call,attempts in list(seen.items())[:limit]:
        # Seleccionar un intento por decisión: preferir el aceptado.
        # Un fallido se conserva como fallido, nunca se cuenta dos veces.
        match=next((r for r in attempts if r["status"]=="accepted"),attempts[0])
        chosen.append((match,len(attempts)))
    chosen.reverse()
    return chosen,total>len(chosen),total,[]


def _parse_attempt(row):
    raw=row["body"]
    if not isinstance(raw,bytes) or len(raw)>_MAX_BODY:
        raise ValueError("Cuerpo ilegible o superior a 1 MiB")
    if (len(raw)!=row["body_bytes"] or
            hashlib.sha256(raw).hexdigest()!=row["body_sha256"]):
        raise ValueError("La captura no supera su verificación SHA-256")
    return index_request(raw,provider=row["provider"],purpose=row["purpose"])


def _field_stats(indexed):
    found={}
    references=set()
    for message in indexed["messages"]:
        for block in message["blocks"]:
            if block["kind"] not in ("field","text"):
                continue
            pointer=block.get("json_pointer") if block["kind"]=="field" else None
            # Un campo sin ruta sigue siendo localizable mediante el rol y
            # la ruta del mensaje; no inventar una ruta JSON del contexto.
            name=(message["role"]+":"+
                  (pointer if pointer is not None else "@texto:"+message["path"]))
            item=found.setdefault(name,{
                "field":name,"title":block.get("title") or "Texto original",
                "family":block.get("display_group") or "otros",
                "role":message["role"],"message_path":message["path"],
                "part_hashes":[],"bytes":0,"empty_parts":[],"fragments":0
            })
            item["bytes"]+=len(block["literal"].encode("utf-8"))
            item["fragments"]+=1
            item["part_hashes"].append(block["literal_sha256"])
            if block["kind"]=="field":
                empty=_is_empty_json_literal(block["literal"])
                if empty is not None:
                    item["empty_parts"].append(empty)
                if block.get("display_group") in _MEMORY_FAMILIES:
                    parsed=_decode_record("{"+block["literal"]+"}")
                    if isinstance(parsed,dict):
                        references.update(_explicit_identifiers(parsed))
    for value in found.values():
        digest=":".join(value["part_hashes"])
        value["sha256"]=hashlib.sha256(digest.encode("ascii")).hexdigest()
        value["empty"]=(all(value["empty_parts"]) if value["empty_parts"]
                        and len(value["empty_parts"])==value["fragments"] else None)
        del value["empty_parts"]
        del value["part_hashes"]
    return found,references


def _matrix(chosen):
    turns=[]
    field_grid={}
    all_ids={}
    invalid=[]
    for row,retries in chosen:
        stamp=row["simulated_at"] or row["started_utc"]
        turn={"call_id":row["call_id"],"attempt_id":row["attempt_id"],
              "provider":row["provider"],"status":row["status"],
              "simulated_at":stamp,"retry_count":retries}
        try:
            index=_parse_attempt(row)
            fields,ids=_field_stats(index)
            turn["indexed"]=True
            turn["body_bytes"]=row["body_bytes"]
            turn["field_count"]=len(fields)
            all_ids[row["call_id"]]=ids
            for name,item in fields.items():
                field_grid.setdefault(name,[]).append((len(turns),item))
        except (ValueError,TypeError,UnicodeError,KeyError,RecursionError) as exc:
            turn["indexed"]=False
            turn["error"]="La captura no pudo verificarse o indexarse"
            invalid.append({"call_id":row["call_id"],
                            "attempt_id":row["attempt_id"],
                            "reason":str(exc)[:160]})
        turns.append(turn)
    matrix=[]
    for field,members in field_grid.items():
        cells=[None]*len(turns)
        for idx,item in members:
            cells[idx]={"bytes":item["bytes"],"sha256":item["sha256"],
                        "empty":item["empty"],"fragments":item["fragments"]}
        sizes=[c["bytes"] for c in cells if c is not None]
        hashes={c["sha256"] for c in cells if c is not None}
        first=members[0][1]
        matrix.append({
            "field":field,"title":first["title"],"family":first["family"],
            "role":first["role"],"occurrences":len(members),
            "total_bytes":sum(sizes),"min_bytes":min(sizes),"max_bytes":max(sizes),
            "identical_when_present":len(hashes)==1,
            "all_present":len(members)==len(turns),
            "empty_count":sum(c["empty"] is True for c in cells if c is not None),
            "cells":cells,
        })
    matrix.sort(key=lambda x:(-x["total_bytes"],x["field"]))
    return turns,matrix,all_ids,invalid


def _history_records(world):
    path=Path(world) if world else None
    if path is None or not path.is_file():
        return [],False,["No hay SQLite de mundo para leer relaciones de evidencia."]
    with closing(_db(path)) as db:
        if not _has_table(db,"history"):
            return [],False,["La partida es anterior al archivo de historial."]
        rows=db.execute(
            """SELECT seq,category,simulated_at,payload
               FROM history
               WHERE category IN ('experience','diagnostic','measurement')
               ORDER BY seq DESC LIMIT ?""",(_MAX_HISTORY+1,)).fetchall()
    truncated=len(rows)>_MAX_HISTORY
    return list(reversed(rows[:_MAX_HISTORY])),truncated,[]


def _signature(value):
    """La huella agrupa registros por lo que CADA registro declara."""
    op=value.get("op")
    if not isinstance(op,str) or not op:
        return None
    target=value.get("target")
    if not isinstance(target,(str,int,float)) or isinstance(target,bool):
        target=None
    flag=value.get("success")
    if type(flag) is bool:
        status="éxito" if flag else "fallo"
    else:
        status=value.get("evaluation_status") or value.get("status") or "sin clasificación"
        if not isinstance(status,str):
            status="sin clasificación"
    return op,str(target) if target is not None else None,status


def _footprints(records):
    rows=[]
    for item in records:
        if item["category"]!="diagnostic":
            continue
        data=_decode_record(item["payload"])
        if data is None:
            continue
        key=_signature(data)
        if key is not None:
            rows.append((int(item["seq"]),key,data))
    groups={}
    for seq,key,data in rows:
        group=groups.setdefault(key,{"op":key[0],"target":key[1],
                                     "result":key[2],"count":0,
                                     "first_seq":seq,"last_seq":seq,
                                     "sample_seq":[],"max_adjacent":0})
        group["count"]+=1
        group["last_seq"]=seq
        if len(group["sample_seq"])<12:
            group["sample_seq"].append(seq)
    # "Adyacente" refiere exclusivamente a diagnósticos consecutivos en
    # el listado de *diagnósticos*, NO a pasos consecutivos de Nilo.
    last=None;streak=0
    for seq,key,_ in rows:
        streak=streak+1 if key==last else 1
        last=key
        groups[key]["max_adjacent"]=max(groups[key]["max_adjacent"],streak)
    return sorted(groups.values(),key=lambda x:(-x["count"],-x["max_adjacent"]))[:_MAX_RESULTS],len(rows)


def _memory_traces(records,turns,ids_by_call):
    # Solo registrar igualdad de IDs en campos JSON del contexto; nunca
    # contar coincidencias textuales (falso positivo por substring).
    experiences=[]
    by_id={}
    for item in records:
        if item["category"]!="experience":
            continue
        value=_decode_record(item["payload"])
        if not value or not isinstance(value.get("id"),str):
            continue
        ident=value["id"]
        record={"id":ident,"history_seq":int(item["seq"]),
                "simulated_at":item["simulated_at"],
                "measurement_id":value.get("measurement_id"),
                "action_id":value.get("action_id"),
                "in_requests":[],"relation":"explicit_id_present_in_prompt_only"}
        experiences.append(record)
        by_id.setdefault(ident,[]).append(record)
    for index,turn in enumerate(turns):
        for ident in ids_by_call.get(turn["call_id"],()):
            for source in by_id.get(ident,()):
                source["in_requests"].append({
                    "call_id":turn["call_id"],"attempt_id":turn["attempt_id"],
                    "turn_index":index,
                    "relation":"equal_id_in_archived_context_not_proof_of_use"})
    return {
        "experiences":[x for x in experiences if x["in_requests"]][:100],
        "experience_count_in_window":len(experiences),
        "with_explicit_request_id":sum(bool(x["in_requests"]) for x in experiences),
        "limitations":[
            "La existencia de una experiencia en la partida no demuestra que se haya seleccionado para el prompt.",
            "Una coincidencia exacta de ID dentro de un campo de memoria/evidencia demuestra inclusión textual; no demuestra lectura, uso ni causa de la decisión.",
            "Los registros sin ID explícito en el contexto no pueden rastrearse mediante este método.",
            "La ventana de solicitudes y la de historial pueden tener retenciones distintas; la cronología cruzada no está garantizada.",
        ],
    }


def analyze(world, *, limit=_DEFAULT_CALLS):
    """Vista agregada, fuente exclusivamente local, lectura sin efectos."""
    if type(limit) is not int or not 1<=limit<=_MAX_CALLS:
        raise ValueError("Límite de turnos inválido")
    origin=Path(world).resolve() if world is not None else None
    sidecar=RequestTraceStore.for_world(origin).path if origin is not None else None
    selected,shortened,total,notices=_attempt_rows(sidecar,limit)
    turns,matrix,ids,invalid=_matrix(selected)
    records,history_shortened,history_notes=_history_records(origin)
    footprints,diagnostics=_footprints(records)
    memories=_memory_traces(records,turns,ids)
    limitations=notices+history_notes+[
        "Una columna representa una deliberación archivada (se elige el intento aceptado si existe); los reintentos no se cuentan como nuevos turnos.",
        "Bytes de campo son UTF-8 de los fragmentos; NO son tokens de proveedor.",
        "La igualdad de huellas SHA-256 prueba texto idéntico dentro de la ventana, no relevancia ni utilidad.",
        "Las agrupaciones operativas describen registros diagnósticos, no intenciones, causas ni decisiones completas.",
    ]
    if shortened:
        limitations.append("La matriz cubre una ventana acotada; hay turnos anteriores que no se muestran.")
    if history_shortened:
        limitations.append("El historial de evidencia se ha acotado a 1600 registros; no representa toda la partida.")
    if invalid:
        limitations.append("Hay capturas incompletas/corruptas; no se infieren campos de las solicitudes fallidas.")
    return {
        "schema":"nilo.lab.cross_analysis.v1",
        "source":"local_world_and_matching_sidecar_readonly",
        "window":{"requested_calls":limit,"visible_calls":len(turns),
                  "total_archived_calls":total,"more_calls_exist":shortened,
                  "history_rows_in_window":len(records),
                  "history_truncated":history_shortened},
        "turns":turns,"matrix":matrix,
        "operations":{"diagnostics_with_fingerprint":diagnostics,
                      "patterns":footprints,
                      "scope":"only_diagnostic_records_with_explicit_operation",
                      "adjacent_scope":"consecutive_diagnostic_records_not_all_actions"},
        "memory":memories,"invalid_attempts":invalid,
        "limitations":limitations,
        "no_world_writes":True,"no_llm_calls":True,
    }
