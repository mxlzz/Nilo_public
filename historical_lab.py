"""Estados históricos de deliberación/acción y reconstrucción local verificable.

Los checkpoints son observacionales y no forman parte de la memoria de Nilo.
No hay ejecución de código deserializado ni cambios en la partida de origen.
"""
from __future__ import annotations

from contextlib import contextmanager
from bisect import bisect_right
import copy
import hashlib
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import threading
import time
import zlib

from nilo_runtime.storage.timeline import (
    TimelineStore, FORMAT, MAX_DECOMPRESSED, _tuples, _json, _decompress,
)

REPLAY_LOCK = threading.RLock()


@contextmanager
def read_only_connection(filename):
    path = Path(filename).resolve()
    if not path.is_file() or path.suffix.lower() not in (".sqlite3", ".sqlite", ".db"):
        raise ValueError("Seleccioná una base SQLite de Nilo.")
    con = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
    con.execute("PRAGMA query_only=ON")
    try:
        yield con
    finally:
        con.close()


def _table_exists(conn, table):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone())


def catalog(filename, *, limit=12000):
    with read_only_connection(filename) as db:
        if not _table_exists(db, "history"):
            raise ValueError("El archivo no contiene el historial de Nilo.")
        has_cp = _table_exists(db, "timeline_checkpoints")
        cp_rows = (db.execute("""SELECT id,kind,clock_minutes,day_label,source,
                   operation,engine_version,history_seq,decision_json
                   FROM timeline_checkpoints ORDER BY id
                   LIMIT ?""", (limit,)).fetchall() if has_cp else [])
        first_seq = min((int(row[7]) for row in cp_rows), default=None)
        # Antes del primer checkpoint solo se dispone de hechos documentados:
        # no se presenta como si se pudiera reconstruir un estado histórico.
        sql = """SELECT seq,category,simulated_at,payload FROM history
                 WHERE category IN ('llm_decision','diagnostic','event')
                 AND (? IS NULL OR seq<=?)
                 ORDER BY seq LIMIT ?"""
        historic = db.execute(sql, (first_seq, first_seq, limit)).fetchall()
        entries = []
        for seq, category, stamp, payload in historic:
            try:
                d = json.loads(payload)
            except (ValueError, TypeError):
                d = {}
            if category == "event" and not any(
                w in str(d.get("text", "")).casefold()
                for w in ("empecé:", "terminé", "falló", "interrump", "proyecto", "decidí")
            ):
                continue
            action = d.get("decision") or d.get("action_result", {}) or d
            if not isinstance(action, dict):
                action = {}
            op = (action.get("op") or d.get("op") or
                  ("decisión" if category == "llm_decision" else category))
            entries.append({"id": "hist:" + str(seq), "kind": category,
                            "clock_minutes": d.get("clock_minutes"),
                            "label": stamp, "op": op,
                            "title": str(d.get("text") or d.get("title") or op)[:110],
                            "replayable": False,
                            "failed": bool(category=="diagnostic" and
                                           (d.get("success") is False or
                                            (d.get("action_result") or {}).get("success") is False)),
                            "reason": "Sin estado anterior preservado"})
        diagnostic_rows = db.execute(
            "SELECT seq,payload FROM history WHERE category='diagnostic' "
            "AND seq>? ORDER BY seq",
            (first_seq if first_seq is not None else 0,)
        ).fetchall() if cp_rows else []
        diagnostic_seqs = [int(row[0]) for row in diagnostic_rows]
        for idx,(ident, kind, minute, stamp, source, op, version, seq, raw_decision) in enumerate(cp_rows):
            try:
                doc = json.loads(raw_decision) if raw_decision else {}
            except ValueError:
                doc = {}
            title = (doc.get("objetivo") if kind == "decision" else
                     doc.get("name") or doc.get("target") or
                     (f"({doc.get('x')},{doc.get('y')})" if "x" in doc else "")) or ""
            recorded_failure = False
            if kind == "action":
                ceiling = cp_rows[idx+1][7] if idx+1 < len(cp_rows) else None
                cursor = bisect_right(diagnostic_seqs, seq)
                while cursor < len(diagnostic_rows):
                    dseq, raw_outcome = diagnostic_rows[cursor]
                    if ceiling is not None and dseq > ceiling:
                        break
                    try:
                        outcome = json.loads(raw_outcome)
                    except ValueError:
                        outcome = {}
                    if outcome.get("op") == op:
                        recorded_failure = (outcome.get("success") is False or
                            (outcome.get("action_result") or {}).get("success") is False)
                        break
                    cursor += 1
            entries.append({"id": "cp:" + str(ident), "kind": kind,
                            "clock_minutes": minute, "label": stamp,
                            "op": op or ("decisión" if kind == "decision" else "?"),
                            "title": str(title)[:110], "source": source,
                            "engine_version": version, "replayable": True,
                            "failed": bool(recorded_failure), "history_seq": seq})
        # Orden de aparición del archivo: los registros legados mantienen su
        # seq original; los checkpoints nuevos se ordenan por ID de captura.
        # No ordenar entradas legadas por minutos ausentes (las reordenaría).
        total = db.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        return {"entries": entries[-limit:], "history_rows": total,
                "checkpoint_count": len(cp_rows),
                "has_snapshots": has_cp,
                "limitations": ("Los momentos anteriores a la instrumentación se pueden leer "
                                "pero no reproducir exactamente desde un estado anterior."),
                "source": Path(filename).name}


def select_event(filename, event_id, *, full=False):
    if not isinstance(event_id, str) or len(event_id) > 48 or ":" not in event_id:
        raise ValueError("Evento histórico inválido.")
    kind, raw = event_id.split(":", 1)
    if not raw.isdecimal() or len(raw) > 14:
        raise ValueError("Identificador histórico inválido.")
    ident = int(raw)
    with read_only_connection(filename) as db:
        if kind == "hist":
            row = db.execute("""SELECT seq,category,simulated_at,payload
                                FROM history WHERE seq=?""", (ident,)).fetchone()
            if row is None:
                raise ValueError("No se encontró el evento.")
            return {"id":event_id,"kind":row[1],"label":row[2],
                    "replayable":False,"historical":json.loads(row[3]),
                    "reason":"No existe checkpoint anterior de este momento."}
        if kind != "cp" or not _table_exists(db,"timeline_checkpoints"):
            raise ValueError("No existe un checkpoint para ese evento.")
        row = db.execute("""SELECT kind,clock_minutes,day_label,source,operation,
               engine_version,history_seq,decision_json,blob,blob_sha256
               FROM timeline_checkpoints WHERE id=?""", (ident,)).fetchone()
        if row is None:
            raise ValueError("Checkpoint no encontrado.")
        cp_kind, minute, stamp, source, op, version, seq, command, blob, digest = row
        metadata = json.loads(command) if command else {}
        # Vincular diagnósticos solo hasta el checkpoint siguiente: si no hay
        # resultados en ese intervalo, NO asignar resultados de otra acción.
        boundary = db.execute(
            "SELECT history_seq FROM timeline_checkpoints WHERE id>? ORDER BY id LIMIT 1",
            (ident,)
        ).fetchone()
        maximum = int(boundary[0]) if boundary is not None else None
        recorded = db.execute("""SELECT category,payload FROM history
                                WHERE seq>? AND (? IS NULL OR seq<=?)
                                AND category='diagnostic'
                                ORDER BY seq LIMIT 12""",
                              (seq, maximum, maximum)).fetchall()
        related = []
        for category, item in recorded:
            decoded = json.loads(item)
            if cp_kind == "action" and decoded.get("op") != op:
                continue
            related.append({"category":category,"payload":decoded})
        result={"id":event_id,"kind":cp_kind,"clock_minutes":minute,
                "label":stamp,"source":source,"op":op,"engine_version":version,
                "command":metadata,"related":related,"replayable":True,
                "history_seq":seq}
        if full:
            if hashlib.sha256(blob).hexdigest() != digest:
                raise ValueError("El checkpoint presenta una discrepancia de integridad.")
            payload = _decompress(blob)
            if payload.get("format") != FORMAT:
                raise ValueError("Formato de checkpoint no compatible.")
            result["_restorable"] = payload
        return result


def _state_summary(state):
    p = state["person"];w = state["world"]
    return {
        "pos": list(p.get("pos", [])),
        "minute": round(float(p.get("clock_minutes", 0)), 3),
        "inventory": dict(p.get("inventory", {})),
        "needs": dict(p.get("needs", {})),
        "known_tiles": len(w.get("revealed", [])),
        "structures": len(w.get("structures", [])),
        "tools": len(p.get("items", [])),
        "measurements": len(p.get("measurements", [])),
        "project": (p.get("project") or {}).get("title"),
        "plan": copy.deepcopy(p.get("plan", [])),
        "pending": copy.deepcopy(p.get("pending")),
    }


def _difference(a,b):
    result = {}
    for key in ("pos","minute","known_tiles","structures","tools","measurements","project"):
        if a.get(key) != b.get(key):
            result[key] = {"before":a.get(key),"after":b.get(key)}
    for key in ("inventory","needs"):
        diff = {}
        for material in sorted(set(a.get(key,{})) | set(b.get(key,{}))):
            x,y=a.get(key,{}).get(material,0),b.get(key,{}).get(material,0)
            if isinstance(x,(int,float)) and isinstance(y,(int,float)) and abs(x-y)>0.000001:
                diff[material]=round(y-x,3)
        if diff:result[key+"_delta"]=diff
    return result


def replay(filename, event_id, *, override=None, max_ticks=400):
    """Reproduce un checkpoint en Simulation real, en SQLite temporal independiente.

    Exactitud de efectos físicos comparables, no identidad bit a bit:
    UUID, reloj real, ruta de proveedores y eventos externos pueden divergir.
    """
    if type(max_ticks) is not int or not 1 <= max_ticks <= 800:
        raise ValueError("Límite de ticks inválido.")
    event = select_event(filename, event_id, full=True)
    if not event.get("replayable") or "_restorable" not in event:
        raise ValueError("Este evento sólo tiene registro histórico; falta el estado anterior.")
    payload = event.pop("_restorable")
    if override is not None:
        if not isinstance(override, dict) or len(_json(override)) > 12000:
            raise ValueError("Orden experimental inválida.")
    state = payload["state"]
    before = _state_summary(state)
    version = event["engine_version"]
    with REPLAY_LOCK:
        old_global_state = random.getstate()
        try:
            random.setstate(_tuples(payload["global_rng_state"]))
            from nilo import Simulation
            from laboratorio_casos import Trace
            with tempfile.TemporaryDirectory(prefix="nilo-historico-") as td:
                sim = Simulation(db_path=Path(td)/"replay.sqlite3",
                                 world_seed=state["world"].get("seed",7321),rng_seed=9821,
                                 scenario_id=state.get("scenario_id","territorio_desconocido"))
                sim.timeline_capture_enabled = False
                sim.think = lambda: None
                sim.s = copy.deepcopy(state)
                random.setstate(_tuples(payload["global_rng_state"]))
                sim.s["planning"] = False
                sim.s["paused"] = False
                sim.s["auto_wait_frozen"] = False
                if "entropy_state" in payload:
                    from nilo_runtime.core.identity import EntropySession
                    sim.entropy = EntropySession.from_record(
                        payload["entropy_state"],
                        world_seed=int(state["world"].get("seed",7321)),
                    )
                    sim.rng = sim.entropy.agent_rng
                    sim.rng_seed = sim.entropy.rng_seed
                else:
                    # Los checkpoints 0.6.x sólo conservaban RNG físico y
                    # global; sus UUID de os.urandom no se pueden reconstruir.
                    sim.legacy_identity_mode = True
                    sim.rng_seed = -1
                sim.rng.setstate(_tuples(payload["rng_state"]))
                stages = []
                if event["kind"] == "decision":
                    decision = copy.deepcopy(override if override is not None else event["command"])
                    from brain import normalize_decision
                    decision = normalize_decision(decision)
                    with Trace(max_calls=220) as trace:
                        sim.plan_ready(decision, event["source"] or "llm", {})
                    stages.append({"name":"Validación y planificación",
                                   "trace": trace.serial(),
                                   "plan":copy.deepcopy(sim.s["person"].get("plan", [])),
                                   "after":_state_summary(sim.s)})
                    target_actions = max(1,len(sim.s["person"].get("plan",[])))
                else:
                    if override is not None:
                        from action_contracts import SUPPORTED_OPERATIONS
                        if override.get("op") not in SUPPORTED_OPERATIONS:
                            raise ValueError("La acción experimental no existe.")
                        plan = sim.s["person"].setdefault("plan",[])
                        if plan:plan[0] = copy.deepcopy(override)
                        else:plan.insert(0,copy.deepcopy(override))
                    target_actions = 1
                completed = 0
                was_pending = bool(sim.s["person"].get("pending"))
                measured_at = len(sim.s["person"].get("measurements",[]))
                for _ in range(max_ticks):
                    with Trace(max_calls=250) as trace:
                        sim.tick(3.0)
                    p=sim.s["person"]
                    current_measures=len(p.get("measurements",[]))
                    pending=bool(p.get("pending"))
                    if current_measures>measured_at or (was_pending and not pending):
                        completed += 1
                        stages.append({"name":"Acción completada",
                                       "trace":trace.serial(),
                                       "after":_state_summary(sim.s)})
                        measured_at=current_measures
                    elif len(stages)<8 and trace.calls and not stages:
                        stages.append({"name":"Inicio de ejecución",
                                       "trace":trace.serial()})
                    was_pending=pending
                    if p.get("unconscious") or (not pending and not p.get("plan")):
                        break
                    if completed >= target_actions and not pending:
                        break
                after=_state_summary(sim.s)
                observed = sim.conn.execute(
                    "SELECT payload FROM history WHERE category='diagnostic' "
                    "ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                simulated = json.loads(observed[0]) if observed else None
                archived = next((e["payload"] for e in event.get("related",[])
                                 if e.get("category")=="diagnostic"), None)
                metric_keys = ("op","success","evaluation_status")
                comparison = {}
                for key in metric_keys:
                    original = archived.get(key) if archived else None
                    experimental = simulated.get(key) if simulated else None
                    comparison[key] = {"original":original,"experimental":experimental,
                                       "same":original==experimental if archived and simulated else None}
                for key in ("duration_minutes","inventory_delta","needs_delta",
                            "position_start","position_end"):
                    original = (archived.get("physical_result") or {}).get(key) if archived else None
                    experimental = (simulated.get("physical_result") or {}).get(key) if simulated else None
                    comparison[key] = {"original":original,"experimental":experimental,
                                       "same":original==experimental if archived and simulated else None}
                end = {"before":before,"after":after,"changes":_difference(before,after),
                       "stages":stages,"completed_actions":completed,
                       "unfinished":bool(sim.s["person"].get("plan") or sim.s["person"].get("pending")),
                       "historical":event,"outcome_comparison":comparison,
                       "recorded_outcome":archived,"simulated_outcome":simulated,
                       "model":"Re-ejecución del código actual con estado anterior documentado.",
                       "limits":("No se reproduce la generación LLM ni se garantizan UUID o "
                                 "eventos de reloj real idénticos; no se altera la partida original."),
                       "version_recorded":version}
                sim.conn.close()
                return end
        finally:
            random.setstate(old_global_state)
