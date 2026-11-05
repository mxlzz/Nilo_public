"""Reproducción sin servidor ni API de decisiones registradas o guionadas.

No recrea el razonamiento del modelo: ejecuta los JSON ya elegidos usando el
mismo plan_ready/tick de Nilo. Requiere una partida inicial controlada por semilla.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import tempfile
import time
import types
import uuid
from pathlib import Path
from unittest.mock import patch

import nilo
from brain import normalize_decision
from scenarios import get_scenario

FORMAT = "nilo-replay-v1"


class ReplayError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False, default=str)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class VirtualClock:
    def __init__(self, start):
        self.wall = float(start)

    def time(self):
        return self.wall

    def monotonic(self):
        return self.wall

    def advance(self, seconds):
        self.wall += float(seconds)


def check_spec(spec):
    if not isinstance(spec, dict) or spec.get("format") != FORMAT:
        raise ReplayError("Formato inválido: se requiere nilo-replay-v1.")
    get_scenario(spec.get("scenario_id", "territorio_desconocido"))
    if not isinstance(spec.get("decisions"), list) or not spec["decisions"]:
        raise ReplayError("Se requiere al menos una respuesta registrada del LLM.")
    if len(spec["decisions"]) > 100:
        raise ReplayError("Máximo 100 deliberaciones por prueba.")
    for raw in spec["decisions"]:
        normalize_decision(raw)  # Igual que la respuesta real del proveedor.
    speed = spec.get("speed", 60)
    if speed not in (1, 10, 60, 300, 600):
        raise ReplayError("Velocidad permitida: 1, 10, 60, 300 o 600.")
    step = spec.get("seconds_per_tick", 10)
    if isinstance(step, bool) or not isinstance(step, (int, float)) or not 0 < step <= 20:
        raise ReplayError("seconds_per_tick debe estar entre 0 y 20.")
    maximum = spec.get("max_ticks", 1000)
    if isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 20000:
        raise ReplayError("max_ticks debe estar entre 1 y 20000.")
    for key in ("world_seed", "rng_seed", "uuid_seed"):
        value = spec.get(key, 7321)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ReplayError(key + " debe ser un entero.")
    start = spec.get("wall_start", 1700000000)
    if isinstance(start, bool) or not isinstance(start, (int, float)) or not 1 <= start <= 4102444800:
        raise ReplayError("wall_start debe ser una marca de tiempo Unix válida.")
    return spec


def archive_state(sim):
    history = sim.conn.execute(
        "SELECT seq,category,item_id,simulated_at,real_at,payload FROM history ORDER BY seq"
    ).fetchall()
    revisions = sim.conn.execute(
        "SELECT revision,category,item_id,captured_at,digest,payload "
        "FROM history_revisions ORDER BY revision"
    ).fetchall()
    return {"history": history, "revisions": revisions}


def run_replay(spec, diagnostics=False):
    """Devuelve resumen, hashes del estado completo y la traza de deliberaciones.

    Cada ejecución usa su propio SQLite temporal. Ni siquiera lee DB por defecto.
    La semilla controla mapa, RNG del agente, RNG global y UUID.
    """
    check_spec(spec)
    clock = VirtualClock(spec.get("wall_start", 1700000000))
    uuid_rng = random.Random(spec.get("uuid_seed", 7321))
    seeds = (spec.get("world_seed", 7321), spec.get("rng_seed", 7321))
    decisions = copy.deepcopy(spec["decisions"])
    issued = []
    old_random = random.getstate()
    fake_uuid = lambda: uuid.UUID(int=uuid_rng.getrandbits(128))
    no_provider = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("Replay no permite conexión con proveedores LLM.")
    )
    with tempfile.TemporaryDirectory(prefix="nilo-replay-") as directory:
        try:
            random.seed(spec.get("rng_seed", 7321))
            with (patch.object(time, "time", clock.time),
                  patch.object(time, "monotonic", clock.monotonic),
                  patch.object(uuid, "uuid4", fake_uuid),
                  patch.object(nilo, "config", lambda: {"PROVIDER": "gemini"}),
                  patch.object(nilo, "available", lambda cfg: False),
                  patch.object(nilo, "request_llm", no_provider),
                  patch.object(nilo, "request_chat", no_provider),
                  patch.object(nilo, "route", no_provider)):
                sim = nilo.Simulation(
                    db_path=Path(directory) / "replay.sqlite3",
                    world_seed=seeds[0], rng_seed=seeds[1],
                    scenario_id=spec.get("scenario_id","territorio_desconocido"))
                # Un guion previo conserva la física y huella originales.
                # Los nuevos escenarios pueden optar por reglas 0.5.9.3.20.
                sim.legacy_replay_rules=(spec.get("ruleset") not in ("0.5.9.3.20","0.5.9.3.22"))
                sim.legacy_autocare_rules=(spec.get("ruleset")=="0.5.9.3.20")
                # Congelar huellas de TODOS los rulesets ya publicados; no
                # inyectar instrumentación .32 en una reproducción histórica.
                sim.historical_replay=True
                sim.s["speed"] = spec.get("speed", 60)
                sim.s["auto_pause_on_wait"] = False

                def scripted_think(self):
                    if self.s["person"].get("pending") or self.s["person"]["plan"]:
                        return
                    if len(issued) >= len(decisions):
                        return
                    raw = decisions[len(issued)]
                    decision = normalize_decision(raw,legacy_rest=(spec.get('ruleset')!='0.5.9.3.22'))
                    # Traza de la entrada y del estado real inmediatamente anterior.
                    issued.append({
                        "index": len(issued),
                        "minute": round(self.s["person"]["clock_minutes"], 6),
                        "state_before": fingerprint(self.s),
                        "raw_sha256": fingerprint(raw)
                    })
                    self.s["mode"] = "llm_replay"
                    self.s["llm_total"] += 1
                    self.plan_ready(decision, "llm")

                sim.think = types.MethodType(scripted_think, sim)
                ticks = 0
                try:
                    sim.think()
                    for ticks in range(1, spec.get("max_ticks", 1000) + 1):
                        clock.advance(spec.get("seconds_per_tick", 10))
                        sim.tick(spec.get("seconds_per_tick", 10))
                        p = sim.s["person"]
                        if len(issued) == len(decisions) and not p.get("pending") and not p["plan"]:
                            break
                    else:
                        raise ReplayError(
                            "Se agotaron max_ticks antes de terminar todas las acciones."
                        )
                    sim.write()
                    state = copy.deepcopy(sim.s)
                    archived = archive_state(sim)
                finally:
                    sim.conn.close()
        finally:
            random.setstate(old_random)

    full = {"state": state, "archive": archived}
    result = {
        "format": FORMAT,
        "scenario_id": spec.get("scenario_id","territorio_desconocido"),
        "world_seed": seeds[0], "rng_seed": seeds[1],
        "uuid_seed": spec.get("uuid_seed", 7321),
        "seconds_per_tick": spec.get("seconds_per_tick", 10),
        "ticks": ticks,
        "decisions_consumed": len(issued),
        "actions_completed": state["person"].get("autonomy_stats", {}),
        "time_minutes": round(state["person"]["clock_minutes"], 6),
        "state_sha256": fingerprint(state),
        "archive_sha256": fingerprint(archived),
        "fingerprint": fingerprint(full),
        "trace": issued
    }
    if diagnostics:
        result["diagnostics"] = {
            "state_fields": {k:fingerprint(v) for k,v in state.items()},
            "person_fields": {k:fingerprint(v) for k,v in state["person"].items()},
            "world_fields": {k:fingerprint(v) for k,v in state["world"].items()},
            "archive_history_categories": {
                category:fingerprint([row for row in archived["history"] if row[1] == category])
                for category in sorted(set(row[1] for row in archived["history"]))
            },
        }
    expected = spec.get("expected_fingerprint")
    if expected is not None and expected != result["fingerprint"]:
        raise ReplayError(
            "Divergencia: esperado " + str(expected) + ", obtenido " + result["fingerprint"]
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="JSON con semillas, reloj y decisiones")
    parser.add_argument("--output", type=Path, help="Archivo JSON de resultados (opcional)")
    parser.add_argument("--diagnostics", action="store_true", help="Huellas por campo para investigar divergencias")
    args = parser.parse_args()
    try:
        spec = json.loads(args.case.read_text(encoding="utf-8"))
        report = run_replay(spec, diagnostics=args.diagnostics)
        body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(body, encoding="utf-8")
        print(body, end="")
    except (ReplayError, ValueError, KeyError) as exc:
        parser.exit(1, "Error de reproducción: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
