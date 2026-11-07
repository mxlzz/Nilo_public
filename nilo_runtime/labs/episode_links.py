"""Uniones verificables de episodios de deliberación para el laboratorio.

No reinterpreta el cuaderno ni deduce relaciones por reloj/hashes.
Lectura compatible con mundos nuevos y saves antiguos sin tablas o columnas
de procedencia; jamás escribe en SQLite.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3

_CALL_ID = re.compile(r"[0-9a-f]{32}")
_MAX_ACTIONS = 200


def _table(db, name):
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)).fetchone() is not None


def _columns(db, table):
    return {row[1] for row in db.execute("PRAGMA table_info(" + table + ")")}


_AUTOMATIC = frozenset(("agenda","espera","rutina","motor"))


def valid_planned_action_checkpoint(source, raw_command, journal_id):
    """Validar fuente Y paso archivado; una fila de enlace sola no alcanza.

    Los saves heredados y las bases manualmente modificadas pueden contener
    un enlace obsoleto. Nunca atribuir una acción automática a una decisión.
    """
    if source in _AUTOMATIC or not isinstance(journal_id,str) or not journal_id:
        return False
    try:
        action = json.loads(raw_command) if isinstance(raw_command,str) else raw_command
    except (ValueError,TypeError):
        return False
    return (isinstance(action,dict)
            and action.get("_origin") not in _AUTOMATIC
            and action.get("_journal_id")==journal_id)


def inspect_episode(world_path, call_id):
    """Exponer relaciones exactas por ID, o ausencias explícitas.

    archived_decision: historial con el mismo trace_call_id.
    decision_checkpoints: traza nueva con trace_call_id real.
    planned_actions: _journal_id del paso -> lab_journal_trace ->
        lab_action_links; no incluye por defecto hábitos o agenda.
    Ninguna cercanía temporal se promueve a relación causal.
    """
    if not isinstance(call_id, str) or not _CALL_ID.fullmatch(call_id):
        raise ValueError("Identificador de deliberación inválido")
    result = {
        "association": "only_exact_ids",
        "world_available": False,
        "archived_decisions": [],
        "decision_checkpoints": [],
        "planned_actions": [],
        "limitations": [],
    }
    world = Path(world_path).resolve() if world_path is not None else None
    if world is None or not world.is_file():
        result["limitations"].append("world_not_available")
        return result
    with closing(sqlite3.connect(
            world.as_uri()+"?mode=ro",uri=True,timeout=1)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        result["world_available"] = True

        if _table(db, "history"):
            rows = db.execute(
                """SELECT seq, simulated_at, payload FROM history
                   WHERE category='llm_decision' AND instr(payload,?)>0
                   ORDER BY seq DESC LIMIT 32""", (call_id,)).fetchall()
            for row in rows:
                try:
                    data = json.loads(row["payload"])
                except (ValueError, TypeError):
                    continue
                if isinstance(data,dict) and data.get("trace_call_id")==call_id:
                    result["archived_decisions"].append({
                        "seq":row["seq"],
                        "simulated_at":row["simulated_at"],
                        "record_id":data.get("id"),
                        "decision":data.get("decision"),
                        "matched_by":"trace_call_id",
                    })
        else:
            result["limitations"].append("history_not_available")

        if (_table(db,"timeline_checkpoints") and
                "trace_call_id" in _columns(db,"timeline_checkpoints")):
            rows = db.execute(
                """SELECT id,history_seq,day_label,engine_version,source
                   FROM timeline_checkpoints
                   WHERE kind='decision' AND trace_call_id=?
                   ORDER BY id DESC LIMIT 32""",(call_id,)).fetchall()
            result["decision_checkpoints"] = [{
                "id":r["id"],"history_seq":r["history_seq"],
                "label":r["day_label"],"engine_version":r["engine_version"],
                "source":r["source"],"matched_by":"trace_call_id",
            } for r in rows]
        else:
            result["limitations"].append("exact_decision_checkpoint_link_unavailable")

        if (_table(db,"lab_action_links") and
                _table(db,"timeline_checkpoints")):
            rows = db.execute(
                """SELECT l.action_checkpoint_id,l.journal_id,
                          t.operation,t.source,t.day_label,t.history_seq,
                          t.decision_json
                   FROM lab_action_links l
                   JOIN timeline_checkpoints t ON t.id=l.action_checkpoint_id
                   WHERE l.trace_call_id=? AND t.kind='action'
                   ORDER BY l.action_checkpoint_id LIMIT ?""",
                (call_id,_MAX_ACTIONS+1)).fetchall()
            if len(rows)>_MAX_ACTIONS:
                result["limitations"].append("planned_actions_limit_reached")
            # No creer una fila técnica si su checkpoint demuestra que la
            # acción vino de agenda/rutina, o si difiere el journal_id.
            result["planned_actions"] = [{
                "checkpoint_id":row["action_checkpoint_id"],
                "journal_id":row["journal_id"],
                "operation":row["operation"],
                "source":row["source"],
                "label":row["day_label"],
                "history_seq":row["history_seq"],
                "matched_by":"journal_id",
            } for row in rows[:_MAX_ACTIONS]
              if valid_planned_action_checkpoint(
                  row["source"],row["decision_json"],row["journal_id"])]
        else:
            result["limitations"].append("exact_planned_action_links_unavailable")

        # Las mediciones ya conservan journal_id; los diagnósticos tipados
        # conservan physical_result.measurement_id. Unir SOLO por esos IDs.
        # No unir por hora parecida, nombre de operación ni resultado textual.
        evidence={"journals":[],"measurements":[],"diagnostics":[],"experiences":[]}
        result["related_records"]=evidence
        if (_table(db,"lab_journal_trace") and _table(db,"history")):
            journals={row[0] for row in db.execute(
                "SELECT journal_id FROM lab_journal_trace WHERE trace_call_id=?",
                (call_id,))}
            measurement_ids=set()
            diagnostic_ids=set()
            max_rows=100
            def record(category,seq,value,by):
                dest=evidence[category]
                if len(dest)>=max_rows:
                    limit_name=category+"_limit_reached"
                    if limit_name not in result["limitations"]:
                        result["limitations"].append(limit_name)
                    return
                dest.append({"seq":seq,"matched_by":by,"record":value})
            if journals:
                rows=db.execute("""SELECT seq,category,payload FROM history
                    WHERE category IN ('journal','measurement') ORDER BY seq""")
                for seq,category,payload in rows:
                    try:
                        value=json.loads(payload)
                    except (ValueError,TypeError):
                        continue
                    if not isinstance(value,dict):
                        continue
                    if category=="journal" and value.get("id") in journals:
                        record("journals",seq,value,"journal_id")
                    elif category=="measurement" and value.get("journal_id") in journals:
                        record("measurements",seq,value,"journal_id")
                        if isinstance(value.get("id"),str):
                            measurement_ids.add(value["id"])
            if measurement_ids:
                rows=db.execute("""SELECT seq,payload FROM history
                    WHERE category='diagnostic' ORDER BY seq""")
                for seq,payload in rows:
                    try:
                        value=json.loads(payload)
                    except (ValueError,TypeError):
                        continue
                    if not isinstance(value,dict):
                        continue
                    physical=value.get("physical_result")
                    if (isinstance(physical,dict)
                            and physical.get("measurement_id") in measurement_ids):
                        record("diagnostics",seq,value,"measurement_id")
                        if isinstance(value.get("id"),str):
                            diagnostic_ids.add(value["id"])
            if measurement_ids or diagnostic_ids:
                rows=db.execute("""SELECT seq,payload FROM history
                    WHERE category='experience' ORDER BY seq""")
                for seq,payload in rows:
                    try:
                        value=json.loads(payload)
                    except (ValueError,TypeError):
                        continue
                    if not isinstance(value,dict):
                        continue
                    if value.get("measurement_id") in measurement_ids:
                        record("experiences",seq,value,"measurement_id")
                    elif value.get("action_id") in diagnostic_ids:
                        record("experiences",seq,value,"action_id")
        else:
            result["limitations"].append("exact_memory_evidence_links_unavailable")

        if not result["archived_decisions"]:
            result["limitations"].append("archived_decision_not_found")
    return result
