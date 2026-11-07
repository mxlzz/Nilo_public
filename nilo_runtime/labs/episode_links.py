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
                          t.operation,t.source,t.day_label,t.history_seq
                   FROM lab_action_links l
                   JOIN timeline_checkpoints t ON t.id=l.action_checkpoint_id
                   WHERE l.trace_call_id=? AND t.kind='action'
                   ORDER BY l.action_checkpoint_id LIMIT ?""",
                (call_id,_MAX_ACTIONS+1)).fetchall()
            if len(rows)>_MAX_ACTIONS:
                result["limitations"].append("planned_actions_limit_reached")
            result["planned_actions"] = [{
                "checkpoint_id":r["action_checkpoint_id"],
                "journal_id":r["journal_id"],
                "operation":r["operation"],
                "source":r["source"],
                "label":r["day_label"],
                "history_seq":r["history_seq"],
                "matched_by":"journal_id",
            } for r in rows[:_MAX_ACTIONS]]
        else:
            result["limitations"].append("exact_planned_action_links_unavailable")

        if not result["archived_decisions"]:
            result["limitations"].append("archived_decision_not_found")
    return result
