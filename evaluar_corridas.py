"""Observatorio offline de partidas SQLite de Nilo 0.5.9.4.

Solo lectura, sin migraciones ni llamadas a proveedores. Las métricas proceden de
registros físicos y de decisiones archivadas: no interpretan intenciones del diario.
Uso:
    python evaluar_corridas.py partida_A.sqlite3 partida_B.sqlite3 --json informe.json --markdown informe.md
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.parse import quote

FORMAT = "nilo-evaluacion-v1"
NEEDS = ("hidratacion", "nutricion", "energia")
MAINTENANCE = ("drink", "eat", "rest")
EXPLORE = ("explore", "go", "inspect", "descend", "ascend")
EXPERIMENT = ("experiment", "use", "compare", "conclude")
CREATIVE = ("combine", "build", "craft", "assemble", "modify", "dismantle", "design")
PROVIDERS = ("deliberacion", "chat")


class EvaluationError(ValueError):
    pass


def _connect(path):
    file = Path(path).resolve()
    if not file.is_file():
        raise EvaluationError(f"No existe el SQLite: {file}")
    # URI ro: jamás crear o modificar una partida. El archivo puede tener WAL.
    db = sqlite3.connect("file:" + quote(str(file), safe="/") + "?mode=ro", uri=True)
    db.execute("PRAGMA query_only=ON")
    return db


def _tables(db):
    return {row[0] for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def _load_json(raw, origin):
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise EvaluationError(f"JSON inválido en {origin}") from exc
    if not isinstance(data, dict):
        raise EvaluationError(f"Registro no estructurado en {origin}")
    return data


def _history(db, tables):
    if "history" not in tables:
        return {}, "ausente"
    groups = {}
    for category, item_id, payload in db.execute(
            "SELECT category,item_id,payload FROM history ORDER BY seq"):
        record = _load_json(payload, "history:" + str(item_id))
        groups.setdefault(category, []).append(record)
    return groups, "completo_desde_inicio_de_archivo"


def _sessions(db, tables):
    if "engine_sessions" not in tables:
        return [], []
    columns={row[1] for row in db.execute("PRAGMA table_info(engine_sessions)")}
    optional=("start_state_sha256","rng_seed","world_seed")
    extras=[col if col in columns else "NULL" for col in optional]
    rows = db.execute("""SELECT id,engine_version,scenario_id,environment_id,
        simulated_start_min,simulated_end_min,configured_provider,configured_model,
        code_commit,manifest_sha256,""" + ",".join(extras) +
        " FROM engine_sessions ORDER BY id").fetchall()
    keys = ("id", "version", "scenario", "environment", "start", "end",
            "configured_provider", "configured_model", "commit", "manifest_sha256",
            "start_state_sha256","rng_seed","world_seed")
    sessions = [dict(zip(keys, r)) for r in rows]
    usages = []
    if "session_model_usage" in tables:
        for sid, provider, model, purpose, calls in db.execute(
                "SELECT session_id,provider,model,purpose,calls FROM session_model_usage"):
            usages.append({"session_id":sid, "provider":provider,
                           "model":model, "purpose":purpose, "calls":calls})
    return sessions, usages


def _version_set(sessions):
    return sorted({s["version"] for s in sessions if s["version"]})


def _number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool)


def _ratio(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else None


def _counter(rows, field):
    return dict(sorted(Counter(str(r.get(field) or "no_registrado") for r in rows).items()))


def analyze(path):
    """Resumen factual de partida, no atribución causal por versión."""
    with closing(_connect(path)) as db:
        tables = _tables(db)
        if "snapshot" not in tables:
            raise EvaluationError("No existe la tabla snapshot.")
        row = db.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()
        if not row:
            raise EvaluationError("La partida no contiene snapshot id=1.")
        state = _load_json(row[0], "snapshot")
        person = state.get("person")
        world = state.get("world")
        if not isinstance(person, dict) or not isinstance(world, dict):
            raise EvaluationError("Snapshot sin person/world.")
        groups, archive_status = _history(db, tables)
        sessions, usage = _sessions(db, tables)

    seed = world.get("seed")
    scenario = state.get("scenario_id")
    # La primera sesión no equivale al comienzo real de una partida importada.
    first_minute = min((s["start"] for s in sessions), default=None)
    current_minute = person.get("clock_minutes")
    duration = (round(float(current_minute) / 1440, 5)
                if _number(current_minute) and current_minute >= 0 else None)
    observed_span = (round((float(current_minute)-first_minute)/1440, 5)
                     if duration is not None and first_minute is not None and first_minute <= current_minute
                     else None)

    measurements = groups.get("measurement", [])
    outcomes = groups.get("diagnostic", [])
    decisions = groups.get("llm_decision", [])
    projects = groups.get("project", [])
    investigations = groups.get("research", [])
    behavior = person.get("behavior_metrics") or {}
    by_op = _counter(outcomes, "op")
    by_origin = _counter([r for r in outcomes if r.get("origin")], "origin")
    missing_origin = sum(not r.get("origin") for r in outcomes)
    by_eval = _counter(outcomes, "evaluation_status")
    by_contract = _counter(outcomes, "contract_status")
    early_high = Counter()
    high_by_origin = Counter()
    trace_by_measurement={}
    for row in outcomes:
        mid=(row.get("physical_result") or {}).get("measurement_id")
        if mid:
            trace_by_measurement[mid]=row
    directed=[r for r in outcomes
              if r.get("op")=="explore" and isinstance(r.get("exploration_trace"),dict)]
    noncomparable_rest = 0
    comparable_rest = 0
    for row in measurements:
        op = row.get("op")
        if op in MAINTENANCE:
            start = (row.get("start") or {}).get("needs") or {}
            metric = {"drink":"hidratacion","eat":"nutricion","rest":"energia"}[op]
            value = start.get(metric)
            if _number(value) and value >= 90:
                early_high[op] += 1
                origin=trace_by_measurement.get(row.get("id"),{}).get("origin")
                high_by_origin[(op,str(origin or "desconocido"))] += 1
        if op == "rest":
            if row.get("rest_comparable"):
                comparable_rest += 1
            else:
                noncomparable_rest += 1

    outcome_ids = {x.get("id") for x in outcomes}
    measurement_ids = {x.get("id") for x in measurements}
    trace = {"actions_with_origin":sum(by_origin.values()),
             "actions_without_origin":missing_origin,
             "measurements_with_id":len(measurement_ids - {None}),
             "outcomes_with_id":len(outcome_ids - {None}),
             "actions_linked_to_measurement":sum(
                 (r.get("physical_result") or {}).get("measurement_id") in measurement_ids
                 for r in outcomes),
             "llm_decisions_with_context_hash":sum(bool(r.get("context_sha256")) for r in decisions)}

    version_names = _version_set(sessions)
    actual_usage = {}
    for u in usage:
        key = (u["provider"], u["model"], u["purpose"])
        actual_usage[key] = actual_usage.get(key, 0) + u["calls"]
    known_models = [{"provider":p,"model":m,"purpose":purpose,"calls":calls}
                    for (p,m,purpose),calls in sorted(actual_usage.items())]
    claimed_total = sum(r["calls"] for r in known_models if r["purpose"]=="deliberacion")

    warnings = []
    if archive_status == "ausente":
        warnings.append("Sin history: los indicadores de acciones archivadas son incompletos.")
    if not sessions:
        warnings.append("Sin engine_sessions: no se conoce la procedencia de las versiones.")
    elif len(version_names) > 1:
        warnings.append("Partida multiversión: no atribuir estadísticas globales a una versión individual.")
    if first_minute is not None and first_minute > 0:
        warnings.append("Primera sesión instrumentada después del inicio: falta historia completa de versiones.")
    if missing_origin:
        warnings.append("Existen acciones anteriores al registro de origen: no asignarles procedencia.")
    if not sessions or not sessions[0].get("start_state_sha256"):
        warnings.append("No hay huella del estado inicial de la primera sesión; no acreditar equivalencia de copias.")
    if groups.get("measurement") and len(groups["measurement"])>len(person.get("measurements",[])):
        warnings.append("La memoria activa de mediciones está truncada; los conteos usan el archivo completo.")
    if measurements and not outcomes:
        warnings.append("No hay diagnósticos archivados: cobertura de acciones incompleta.")
    if not decisions:
        warnings.append("No hay decisiones LLM archivadas: no reconstruir sus motivaciones.")
    if not behavior:
        warnings.append("Los contadores behavior_metrics no cubren toda la partida; no inferir progreso ausente.")
    if not sessions or len(sessions)>1:
        warnings.append("Los indicadores históricos agregados no permiten aislar estadísticamente una sola sesión.")
    if claimed_total != len(decisions) and sessions and decisions:
        warnings.append("Cantidad de deliberaciones archivadas y uso de sesiones no coincide; comprobar migraciones o cobertura.")

    # No conservar nombres de proyectos, cuaderno, prompts, claves ni posiciones.
    return {
        "format": FORMAT,
        "source": {"file":Path(path).name, "data":"snapshot + history SQLite en solo lectura",
                   "coverage":"partida_acumulada; NO métricas por versión si hay sesiones mixtas"},
        "identity": {"scenario":scenario, "world_seed":seed,
                     "versions":version_names,
                     "environments":sorted({s["environment"] for s in sessions}),
                     "initial_instrumented_minute":first_minute,
                     "simulated_minutes":current_minute, "days_total":duration,
                     "days_in_instrumented_span":observed_span,
                     "actual_models_used":known_models,
                     "configured_models_not_proof_of_use":sorted({
                         (s["configured_provider"],s["configured_model"])
                         for s in sessions if s["configured_provider"] and s["configured_model"]}),
                     "first_session_state_sha256":sessions[0]["start_state_sha256"] if sessions else None,
                     "first_session_rng_seed":sessions[0]["rng_seed"] if sessions else None,
                     "first_session_world_seed":sessions[0]["world_seed"] if sessions else None},
        "actions": {"total_archived":len(outcomes), "by_op":by_op,
                    "by_origin_verified":by_origin, "unknown_origin":missing_origin,
                    "evaluation_status":by_eval, "contract_status":by_contract,
                    "unsuccessful":sum(r.get("success") is False for r in outcomes),
                    "operations_exploration":sum(by_op.get(k,0) for k in EXPLORE),
                    "operations_experiment":sum(by_op.get(k,0) for k in EXPERIMENT),
                    "operations_creative":sum(by_op.get(k,0) for k in CREATIVE),
                    "operations_maintenance":sum(by_op.get(k,0) for k in MAINTENANCE),
                    "directed_exploration_with_trace":len(directed),
                    "directed_exploration_with_discoveries":sum(
                        (r["exploration_trace"].get("discovered_tiles") or 0)>0 for r in directed),
                    "directed_exploration_traveled_tiles":sum(
                        r["exploration_trace"].get("traveled_tiles") or 0 for r in directed),
                    "per_simulated_day":_ratio(len(outcomes),duration)},
        "needs": {"maintenance_with_initial_reserve_at_least_90":dict(early_high),
                  "high_reserve_actions_by_origin":{f"{k}:{origin}":n
                       for (k,origin),n in sorted(high_by_origin.items())},
                  "rest_measured_comparable":comparable_rest,
                  "rest_measured_not_comparable":noncomparable_rest,
                  "interpretation":"No equivale a ingesta injustificada; una reserva alta no prohíbe decisiones voluntarias."},
        "autonomy": {"observed_behavior_summary":_behavior_snapshot(behavior),
                     "llm_decisions_archived":len(decisions),
                     "llm_calls_recorded_in_sessions":claimed_total,
                     "projects_archived":len(projects),
                     "investigations_archived":len(investigations)},
        "evidence": {"measurements_archived":len(measurements),
                     "measurements_active":len(person.get("measurements",[])),
                     "archived_not_active":len(measurement_ids -
                         {m.get("id") for m in person.get("measurements",[])}),
                     "typed_physical_measurements":sum(bool(m.get("physical")) for m in measurements),
                     "trace":trace},
        "warnings":warnings,
    }


def _behavior_snapshot(behavior):
    fields = ("since_minute","actions","by_group","by_origin",
              "progress_actions","novelty_actions","new_tiles","new_knowledge",
              "revisited_destinations","project_switches")
    return {k:behavior[k] for k in fields if k in behavior}


def compare(reports):
    """Comparaciones descriptivas: un emparejamiento no prueba causalidad."""
    if not 2 <= len(reports) <= 8:
        raise EvaluationError("Comparar requiere entre dos y ocho partidas distintas.")
    if len({r["source"]["file"] for r in reports}) != len(reports):
        raise EvaluationError("Usá nombres de archivo distintos para identificar cada partida.")
    identities = [r["identity"] for r in reports]
    same_seed = len({str(v["world_seed"]) for v in identities}) == 1
    same_scenario = len({v["scenario"] for v in identities}) == 1
    same_environment = len({tuple(v["environments"]) for v in identities}) == 1
    initial_hashes=[v["first_session_state_sha256"] for v in identities]
    rng_seeds=[v["first_session_rng_seed"] for v in identities]
    matching_initial_state=(all(initial_hashes) and len(set(initial_hashes))==1)
    matching_rng=(all(x is not None for x in rng_seeds) and len(set(rng_seeds))==1)
    same_horizon = len({v["simulated_minutes"] for v in identities}) == 1
    from_start = all(v["initial_instrumented_minute"] == 0 for v in identities)
    single_version = all(len(v["versions"]) == 1 for v in identities)
    # Se exige comprobar realmente estado inicial y semilla RNG separadamente;
    # esos datos no están en los metadatos antiguos de engine_sessions.
    conditions = {
        "same_world_seed":same_seed,
        "same_scenario":same_scenario,
        "same_environment":same_environment,
        "same_simulated_horizon":same_horizon,
        "sessions_start_at_zero":from_start,
        "each_run_has_single_version":single_version,
        "same_initial_snapshot_sha256":matching_initial_state,
        "same_rng_seed_documented":matching_rng,
        "same_external_llm_response_sequence":False,
    }
    differences = {}
    for label,path in (("acciones_archivadas",("actions","total_archived")),
                       ("acciones_fallidas",("actions","unsuccessful")),
                       ("exploracion",("actions","operations_exploration")),
                       ("experimentos",("actions","operations_experiment")),
                       ("mantenimiento",("actions","operations_maintenance")),
                       ("novedad_instrumentada",("autonomy","observed_behavior_summary","novelty_actions")),
                       ("mediciones",("evidence","measurements_archived")),
                       ("decisiones_llm",("autonomy","llm_decisions_archived"))):
        differences[label] = {r["source"]["file"]:_get(r,path) for r in reports}
    return {
        "format": FORMAT,
        "comparison_kind":"descriptiva_sin_atribucion_causal",
        "conditions":conditions,
        "can_claim_controlled_comparison":False,
        "explanation":("La semilla del mundo y el horizonte no acreditan el mismo snapshot "
                       "inicial, semilla RNG ni respuestas del LLM. Para un contraste "
                       "causal hace falta protocolo prospectivo y condiciones registradas."),
        "metrics_by_run":differences,
    }


def _get(obj,keys):
    for key in keys:
        if not isinstance(obj,dict):return None
        obj=obj.get(key)
    return obj


def format_markdown(results):
    reports=results["runs"]
    out=["# Nilo · evaluación descriptiva de corridas","",
         "Las métricas provienen de SQLite sin abrir la simulación. No equivalen a mejoras causales.","",
         "| Partida | Versiones de sesiones | Días simulados | Acciones archivadas | Decisiones LLM | Novedades instrumentadas |",
         "| --- | --- | ---: | ---: | ---: | ---: |"]
    for r in reports:
        i=r["identity"];a=r["actions"];u=r["autonomy"]
        out.append(f"| {r['source']['file']} | {', '.join(i['versions']) or 'sin datos'} | "
                   f"{i['days_total']} | {a['total_archived']} | "
                   f"{u['llm_decisions_archived']} | "
                   f"{u['observed_behavior_summary'].get('novelty_actions','sin datos')} |")
    out.append("")
    for r in reports:
        out.extend(["## "+r["source"]["file"],"",
                    "Versiones registradas: "+(", ".join(r["identity"]["versions"]) or "desconocidas")+".",
                    "Acciones por operación: "+json.dumps(r["actions"]["by_op"],ensure_ascii=False,sort_keys=True)+".",
                    "Procedencia conocida: "+json.dumps(r["actions"]["by_origin_verified"],ensure_ascii=False,sort_keys=True)+
                    f"; sin origen: {r['actions']['unknown_origin']}.",
                    "Reservas iniciales ≥90: "+json.dumps(r["needs"]["maintenance_with_initial_reserve_at_least_90"],ensure_ascii=False,sort_keys=True)+".",
                    "Mediciones archivadas: "+str(r["evidence"]["measurements_archived"])+
                    "; inaccesibles desde la lista activa: "+str(r["evidence"]["archived_not_active"])+"."])
        if r["warnings"]:
            out.extend(["Advertencias: "+"; ".join(r["warnings"])+"."])
        out.append("")
    if results.get("comparison"):
        c=results["comparison"]
        out.extend(["## Comparabilidad","",
                    "Criterios observados: "+json.dumps(c["conditions"],ensure_ascii=False,sort_keys=True)+".",
                    "**No se declara causalidad:** "+c["explanation"],""])
    return "\n".join(out)+"\n"


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite", nargs="+", type=Path, help="Una a ocho copias SQLite cerradas o accesibles en modo lectura")
    parser.add_argument("--json", type=Path, dest="json_output")
    parser.add_argument("--markdown", type=Path, dest="markdown_output")
    args=parser.parse_args(argv)
    try:
        if len(args.sqlite)>8:
            raise EvaluationError("Máximo ocho partidas por comparación.")
        reports=[analyze(p) for p in args.sqlite]
        result={"format":FORMAT,"runs":reports}
        if len(reports)>1:
            result["comparison"]=compare(reports)
        body=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
        if args.json_output:args.json_output.write_text(body,encoding="utf-8")
        if args.markdown_output:args.markdown_output.write_text(format_markdown(result),encoding="utf-8")
        print(body,end="")
        return 0
    except (EvaluationError,sqlite3.Error,OSError) as exc:
        parser.exit(1,"Error de evaluación: "+str(exc)+"\n")


if __name__=="__main__":
    main()
