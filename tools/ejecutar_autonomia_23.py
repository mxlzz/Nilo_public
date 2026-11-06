"""Corrida REAL y acotada de Nilo con Gemini o Groq (etapa 23).

NO tiene modo demo, no emula respuestas y no se ejecuta en CI automático.
Requiere la clave del proveedor en variable de entorno. Crea una partida nueva
y registra un manifiesto SIN claves ni textos privados. No sobrescribe saves.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def preflight(provider, model, max_calls, duration, world_seed, rng_seed, environ=None):
    env = os.environ if environ is None else environ
    if provider not in ("gemini", "groq"):
        raise ValueError("Solo Gemini y Groq reales; demo no es válido.")
    if not isinstance(model, str) or not re.fullmatch(r"[a-zA-Z0-9_.\-/]{3,100}", model):
        raise ValueError("Nombre de modelo inválido.")
    if not (1 <= max_calls <= 100):
        raise ValueError("El presupuesto debe ser de 1 a 100 deliberaciones.")
    if not (30 <= duration <= 3600):
        raise ValueError("Horizonte real permitido: 30 a 3600 segundos.")
    if not all(type(seed) is int and 0 <= seed < 2**31
               for seed in (world_seed, rng_seed)):
        raise ValueError("Las semillas deben ser enteros no negativos menores a 2^31.")
    key_name = "GEMINI_API_KEY" if provider == "gemini" else "GROQ_API_KEY"
    if not env.get(key_name, "").strip():
        raise ValueError("Falta " + key_name + " en el entorno. No se usará el modo demo.")
    return key_name


def _commit():
    try:
        run = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, timeout=3, check=False)
        if run.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", run.stdout.strip()):
            return run.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def execute(args):
    preflight(args.provider, args.model, args.max_calls, args.max_seconds,
              args.world_seed, args.rng_seed)
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        raise ValueError("La carpeta de salida ya existe: se prohíbe sobrescribir partidas.")
    # Preparar una partida aislada antes de importar el motor (lee config.env).
    os.environ.update({
        "PROVIDER": args.provider, "MODEL": args.model,
        "GROQ_MODEL": args.model if args.provider == "groq" else os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
        "GEMINI_FALLBACK_MODELS": "", "BACKUP_PROVIDER": "",
        "MAX_LLM_CALLS_PER_DAY": str(args.max_calls),
        "MAX_CHAT_CALLS_PER_DAY": "0",
        "MIN_REAL_SECONDS_BETWEEN_CALLS": "15",
    })
    from brain import config, available
    from providers import candidate_configs
    cfg = config()
    candidates = candidate_configs(cfg)
    if not available(cfg) or len(candidates) != 1:
        raise ValueError("La selección no produce exactamente un proveedor real; se cancela.")
    chosen_provider, chosen_cfg = candidates[0]
    chosen_model = chosen_cfg.get("MODEL")
    if chosen_provider != args.provider or chosen_model != args.model:
        raise ValueError("El proveedor/modelo efectivo difiere del solicitado.")
    from nilo import Simulation
    from tools.evaluar_autonomia_23 import analyze_autonomy, report_text

    output.mkdir(parents=True)
    db = output / "world.sqlite3"
    started_utc = _now()
    start = time.monotonic()
    engine = None
    stopped_reason = "max_real_seconds"
    finishing_error = None
    planning_at_end = False
    try:
        engine = Simulation(db_path=db, world_seed=args.world_seed,
                            rng_seed=args.rng_seed,
                            scenario_id="territorio_desconocido")
        engine.change_speed(args.speed, paused=False, auto_pause_on_wait=False)
        last = time.monotonic()
        while time.monotonic() - start < args.max_seconds:
            now = time.monotonic()
            engine.tick(min(now - last, 1.0))
            last = now
            with engine.lock:
                count = int(engine.s.get("llm_total", 0))
                err = str(engine.s.get("mode", ""))
                planning = bool(engine.s.get("planning"))
            if count >= args.max_calls:
                stopped_reason = "call_budget_reached"
                break
            if err == "limite":
                stopped_reason = "internal_daily_limit"
                break
            time.sleep(0.25)
    finally:
        if engine is not None:
            with engine.lock:
                engine.stopped = True
            # La solicitud HTTP iniciada puede terminar tras el último tick.
            # No cerrar la conexión mientras esa deliberación siga viva.
            grace = time.monotonic() + 75
            while time.monotonic() < grace:
                with engine.lock:
                    planning_at_end = bool(engine.s.get("planning"))
                if not planning_at_end:
                    break
                time.sleep(0.2)
            try:
                if not planning_at_end:
                    with engine.lock:
                        engine.s["paused"] = True
                        engine.sessions.finish(engine.s["person"]["clock_minutes"],
                                               reason="etapa_23_" + stopped_reason)
                        engine.write()
            except Exception as exc:
                finishing_error = type(exc).__name__
            finally:
                # Si aún hay worker LLM, el proceso lo termina (daemon), sin
                # cerrar la conexión debajo de una transacción en curso.
                if not planning_at_end:
                    engine.conn.close()

    from tools.evaluar_autonomia_23 import analyze_autonomy, report_text
    report = analyze_autonomy(db)
    metadata = {
        "format": "nilo-corrida-real-23-v1",
        "source": "nilo_runtime/application/engine.py, sin interfaz",
        "commit": _commit(),
        "started_utc": started_utc, "finished_utc": _now(),
        "provider_requested": args.provider, "model_requested": args.model,
        "world_seed": args.world_seed, "rng_seed": args.rng_seed,
        "speed": args.speed, "real_seconds": round(time.monotonic() - start, 2),
        "max_real_seconds": args.max_seconds,
        "max_successful_llm_calls": args.max_calls,
        "minimum_real_seconds_between_calls": 15,
        "scenario_id": "territorio_desconocido",
        "fallback_enabled": False, "human_interventions": 0,
        "stopped_reason": stopped_reason,
        "worker_still_planning": planning_at_end,
        "finalization_error_type": finishing_error,
        "real_llm_evidence": report["verified_real_llm"],
        "observed_models": report["providers_observed"],
        "llm_calls_counted": report["llm"]["successful_deliberations_counted"],
        "llm_decisions_archived": report["llm"]["decisions_archived"],
        "has_full_budget": report["llm"]["decisions_archived"] >= args.max_calls,
        "notes": "Se mide una partida nueva; las decisiones pueden depender de servicio, hora y respuestas externas.",
    }
    (output / "manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
    (output / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    (output / "evaluation.md").write_text(report_text([report]) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output), "stop": stopped_reason,
        "real_llm": report["verified_real_llm"],
        "decisions": report["llm"]["decisions_archived"],
        "full_budget": metadata["has_full_budget"],
        "worker_still_planning": planning_at_end,
    }, ensure_ascii=False))
    return 0 if report["verified_real_llm"] and not planning_at_end and not finishing_error else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("gemini", "groq"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--world-seed", type=int, default=7321)
    parser.add_argument("--rng-seed", type=int, default=1129)
    parser.add_argument("--max-calls", type=int, default=8)
    parser.add_argument("--max-seconds", type=int, default=420)
    parser.add_argument("--speed", type=int, choices=(1, 10, 60, 80), default=60)
    args = parser.parse_args(argv)
    try:
        return execute(args)
    except (ValueError, OSError) as exc:
        parser.exit(2, "No se inició la corrida: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
