"""Laboratorio de operaciones de Nilo: motor real, estado aislado y traza verificable.

No llama a Gemini/Groq, no modifica el SQLite original, no ejecuta el
planificador temporal completo. Cada accion prueba una operacion fisica real.
"""
from __future__ import annotations

import copy
from dataclasses import replace
import json
import os
import random
import sqlite3
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from action_contracts import ACTION_GUIDE, SUPPORTED_OPERATIONS, before as contract_before, classify
from action_results import ActionResult
from brain import build_deliberation_request, context_for
from environments import get_environment
from experiment_log import capture, measure, observational_conclusion
from inventions import register_design, record_action_outcome, submit_debug_report, submit_proposal
from laboratory import compare as compare_physical
from nilo import DB, HERE, initial_state
from survival import update_needs
from bodily_policy import rest_minutes
from world import TRAVEL_MINUTES_PER_TILE, tile, valid

HTML_FILE = HERE / "laboratorio_motor.html"
SCENARIO_HTML_FILE = HERE / "laboratorio_escenarios.html"
HISTORY_HTML_FILE = HERE / "laboratorio_historico.html"
TRACE_TEXT = {
    "navigation.py:resolve_go": "Comprueba destino y accesibilidad conocida",
    "navigation.py:reachable_shores": "Busca orillas alcanzables",
    "navigation.py:pathfind": "Calcula ruta entre casillas conocidas",
    "navigation.py:choose_frontier": "Selecciona una frontera explorable",
    "navigation.py:exploration_frontier": "Filtra fronteras y sectores posibles",
    "world.py:prepare_navigation": "Prepara el recorrido sin mover",
    "navigation.py:advance_navigation": "Avanza por casillas y revela terreno",
    "island.py:reveal": "Incorpora casillas observadas",
    "world.py:navigation_result": "Resume desplazamiento y hallazgos",
    "world.py:execute_action": "Aplica las reglas físicas de la acción",
    "resources.py:nearest_known": "Localiza una fuente conocida y alcanzable",
    "resources.py:harvest_at": "Verifica depósito, distancia, balance y extracción",
    "resources.py:transfer_units": "Transfiere unidades sin saldos negativos",
    "resources.py:forage_action": "Gestiona reservas vegetales y recolección",
    "world.py:inspect_target": "Comprueba visibilidad y examina el objetivo",
    "world.py:dig_with_tool": "Contrasta herramienta y resistencia de roca",
    "world.py:adjacent_rock": "Selecciona roca físicamente adyacente",
    "environments.py:perform_result": "Solicita un resultado físico tipado",
    "environments.py:perform": "Invoca el motor del entorno",
    "environments.py:start_navigation": "Solicita preparación de ruta",
    "environments.py:move_navigation": "Ejecuta tramo de navegación",
    "environments.py:finish_navigation": "Cierra el resultado de navegación",
    "action_results.py:evidence_before": "Captura evidencias previas",
    "action_results.py:result_from_execution": "Clasifica el resultado y sus evidencias",
    "action_contracts.py:before": "Captura condiciones previas del contrato",
    "action_contracts.py:classify": "Diagnostica el contrato operativo",
    "capabilities.py:dispatch": "Deriva el método al módulo físico instalado",
    "capabilities.py:resolve": "Encuentra el método de interacción",
    "structural_loads.py:interact": "Ensaya o transfiere cargas estructurales",
    "structural_loads.py:load_limit": "Calcula capacidad por piezas y geometría",
    "structural_loads.py:stored_load": "Calcula la carga almacenada",
    "vessels.py:interact": "Comprueba y transfiere contenidos de recipientes",
    "vessels.py:capacity": "Evalúa capacidad del recipiente",
    "construction.py:apply_intervention": "Modifica piezas y revisiones del objeto",
    "construction.py:initialize_object": "Registra piezas de la construcción",
    "construction.py:recompute": "Recalcula atributos tras la modificación",
    "physics.py:geometry_from_step": "Interpreta geometría declarada",
    "physics.py:body_physics": "Calcula atributos físicos de materiales",
    "physics.py:evaluate_containment": "Evalúa retención de contenido",
    "physics.py:evaluate_buoyancy": "Evalúa flotación",
    "mechanics.py:create_assembly": "Ensambla piezas y uniones reales",
    "mechanics.py:test_assembly": "Contrasta comportamiento del mecanismo",
    "experiment_log.py:capture": "Fotografía el estado medible",
    "experiment_log.py:measure": "Registra variaciones comprobables",
    "experiment_log.py:observational_conclusion": "Verifica evidencia de la conclusión",
    "inventions.py:register_design": "Registra una ficha de diseño",
    "inventions.py:submit_proposal": "Registra una propuesta sin instalar física",
    "inventions.py:submit_debug_report": "Registra una posible anomalía",
    "inventions.py:record_action_outcome": "Documenta la acción y sus resultados",
    "laboratory.py:compare": "Compara mediciones registradas",
    "survival.py:update_needs": "Actualiza necesidades durante el tiempo simulado",
    "brain.py:context_for": "Prepara la percepción y memorias del contexto",
    "brain.py:compact_context": "Acota campos del contexto",
    "brain.py:build_deliberation_request": "Arma el mensaje final sin enviarlo",
    "cognitive_projection.py:project_context": "Filtra conocimiento no perceptible",
    "prompt_budget.py:bounded_context": "Ajusta contexto al presupuesto del modelo",
}


class ExecutionTrace:
    """Registra funciones y lineas realmente recorridas, no una traza inventada."""

    def __init__(self):
        self.entries = {}
        self.previous = None

    def _trace(self, frame, event, _arg):
        name = Path(frame.f_code.co_filename).name + ":" + frame.f_code.co_name
        if event == "call":
            if name not in TRACE_TEXT:
                return None
            entry = self.entries.get(name)
            if entry is None:
                entry = {"file": name.split(":")[0], "function": frame.f_code.co_name,
                         "text": TRACE_TEXT[name], "count": 0, "lines": set()}
                self.entries[name] = entry
            entry["count"] += 1
            return self._trace
        if event == "line" and name in self.entries:
            self.entries[name]["lines"].add(frame.f_lineno)
        return self._trace

    def __enter__(self):
        self.previous = sys.gettrace()
        sys.settrace(self._trace)
        return self

    def __exit__(self, *_):
        sys.settrace(self.previous)

    def records(self):
        rows = []
        for entry in self.entries.values():
            lines = sorted(entry["lines"])
            if not lines:
                continue
            row = {key: value for key, value in entry.items() if key != "lines"}
            row["first"] = lines[0]
            row["last"] = lines[-1]
            row["line_count"] = len(lines)
            # Las trazas corresponden al código realmente ejecutado de 0.7.
            source_path = {
                "navigation.py": "nilo_runtime/worlds/navigation.py",
                "island.py": "nilo_runtime/worlds/island.py",
                "resources.py": "nilo_runtime/worlds/resources.py",
            }.get(row["file"], row["file"])
            row["url"] = ("https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/"
                          + source_path + "#L" + str(row["first"])
                          + "-L" + str(row["last"]))
            rows.append(row)
        return rows


class MotorLab:
    """Mundo independiente en RAM; nunca guarda modificaciones en la partida."""

    def __init__(self):
        self.lock = threading.RLock()
        self.reset("nuevo", 7321, True)

    def reset(self, mode="nuevo", seed=7321, kit=False):
        with self.lock:
            if mode not in ("nuevo", "partida"):
                raise ValueError("Origen de mundo no reconocido.")
            if mode == "partida":
                if not DB.is_file():
                    raise ValueError("No existe una partida guardada en esta carpeta.")
                uri = "file:" + DB.as_posix() + "?mode=ro"
                conn = sqlite3.connect(uri, uri=True, timeout=4)
                try:
                    row = conn.execute("SELECT payload FROM snapshot WHERE id=1").fetchone()
                finally:
                    conn.close()
                if not row:
                    raise ValueError("La base no contiene una partida para copiar.")
                state = json.loads(row[0])
                if not isinstance(state.get("world"), dict) or not isinstance(state.get("person"), dict):
                    raise ValueError("Snapshot sin mundo o personaje válidos.")
                self.origin = "Copia en memoria del último estado guardado"
            else:
                if type(seed) is not int or not 0 <= seed <= 1000000000:
                    raise ValueError("La semilla debe estar entre 0 y 1.000.000.000.")
                state = initial_state(seed)
                self.origin = "Mundo nuevo, semilla " + str(seed)
            self.world = copy.deepcopy(state["world"])
            self.person = copy.deepcopy(state["person"])
            self.person["pending"] = None
            self.person["plan"] = []
            if kit:
                for material, qty in (("madera", 16), ("piedra", 16),
                                      ("arcilla", 10), ("fibra", 10),
                                      ("mineral oscuro", 8), ("alimento", 6)):
                    self.person["inventory"][material] = max(
                        qty, self.person["inventory"].get(material, 0))
                self.origin += " · materiales de prueba añadidos"
            self.environment = get_environment("isla_v1")
            self.rng = random.Random(9821 + int(self.person.get("clock_minutes", 0)))
            self.history = []
            self.last = None
            return self.state()

    def state(self):
        with self.lock:
            w, p = self.world, self.person
            x, y, z = p["pos"]
            known = set(w.get("revealed", []))
            cells = []
            for yy in range(y - 7, y + 8):
                row = []
                for xx in range(x - 7, x + 8):
                    inside = valid(xx, yy)
                    discovered = inside and f"{xx},{yy},{z}" in known
                    ch = tile(w, xx, yy, z) if discovered else "?"
                    if (xx, yy) == (x, y):
                        ch = "@"
                    row.append({"x": xx, "y": yy, "ch": ch, "known": bool(discovered),
                                "selectable": bool(inside and discovered)})
                cells.append(row)
            structures = [{"id": o.get("id"), "name": o.get("name"),
                           "pos": o.get("pos"), "version": o.get("revision", 1)}
                          for o in w.get("structures", [])]
            items = [{"id": o.get("id"), "name": o.get("name"),
                      "form": o.get("form"), "revision": o.get("revision", 1)}
                     for o in p.get("items", [])]
            sites = [{"name": name, "pos": [q["x"], q["y"], q.get("z", 0)]}
                     for name, q in w.get("sites", {}).items()
                     if f"{q['x']},{q['y']},{q.get('z',0)}" in known]
            return {"origin": self.origin, "position": list(p["pos"]),
                    "minute": round(p.get("clock_minutes", 0), 2),
                    "inventory": {k: v for k, v in p["inventory"].items() if v},
                    "needs": dict(p.get("needs", {})),
                    "map": cells, "known": len(known),
                    "structures": structures, "items": items, "sites": sites,
                    "history": self.history[-15:][::-1], "last": self.last,
                    "actions": [{"name": k, "description": v} for k, v in ACTION_GUIDE.items()]}

    def _execute(self, step):
        w, p, env = self.world, self.person, self.environment
        op = step["op"]
        if op in ("go", "explore", "gather", "ascend"):
            nav = env.start_navigation(w, p, step, self.rng)
            if nav is not None:
                env.move_navigation(w, p, nav, len(nav["route"]))
                facts, success, notable = env.finish_navigation(nav, p)
                duration = len(nav["route"]) * TRAVEL_MINUTES_PER_TILE
                if nav.get("kind") == "ascend" and success:
                    res = env.perform_result(w, p, step, self.rng)
                    facts += list(res.facts)
                    success, notable = res.success, notable or res.notable
                elif nav.get("kind") == "gather":
                    arrived = success and tuple(p["pos"][:2]) == tuple(nav["destination"])
                    if arrived:
                        res = env.perform_result(w, p, step, self.rng)
                        facts += list(res.facts)
                        success, notable = res.success, notable or res.notable
                    else:
                        success = False
                        facts.append("Solo avancé hacia la fuente; todavía no extraje material.")
                return ActionResult.from_legacy(step, facts, success, notable,
                                                duration_minutes=duration)
        stamp = "Laboratorio · minuto " + str(round(p.get("clock_minutes", 0), 2))
        if op == "design":
            success, message = register_design(p, step, stamp)
            return ActionResult.from_legacy(step, [message], success, success, 26)
        if op == "propose":
            success, message = submit_proposal(p, step, stamp,
                                               ("flotacion", "contencion", "excavacion", "impacto"))
            return ActionResult.from_legacy(step, [message], success, success, 28)
        if op == "report_issue":
            success, message = submit_debug_report(p, step, stamp)
            return ActionResult.from_legacy(step, [message], success, success, 24)
        if op == "compare":
            success, message, _entry = compare_physical(p, step, stamp)
            return ActionResult.from_legacy(step, [message], success, success, 15)
        if op == "conclude":
            success, message, _entry = observational_conclusion(p, step, stamp)
            return ActionResult.from_legacy(step, [message], success, success, 12)
        return env.perform_result(w, p, step, self.rng)

    def act(self, step):
        if not isinstance(step, dict) or not isinstance(step.get("op"), str):
            raise ValueError("La acción debe ser un objeto con operación válida.")
        if step["op"] not in SUPPORTED_OPERATIONS:
            raise ValueError("Operación no disponible en esta versión del motor.")
        if len(json.dumps(step, ensure_ascii=False)) > 4000:
            raise ValueError("Acción demasiado extensa.")
        with self.lock:
            saved_world = copy.deepcopy(self.world)
            saved_person = copy.deepcopy(self.person)
            saved_rng = self.rng.getstate()
            start = capture(self.world, self.person)
            prior = contract_before(self.world, self.person, step)
            try:
                with ExecutionTrace() as trace:
                    result = self._execute(step)
                    if step['op'] in ('rest', 'wait'):
                        result = replace(result, duration_minutes=rest_minutes(step) or 30)
                    duration = max(0.0, min(float(result.duration_minutes), 1440))
                    self.person["clock_minutes"] = self.person.get("clock_minutes", 0) + duration
                    shelter, water = self.environment.surroundings(self.world, self.person)
                    update_needs(self.person, self.world, duration, shelter, water,
                                 active=step["op"] not in ("rest", "wait"),
                                 resting=step["op"] == "rest")
                    stamp = "Laboratorio · minuto " + str(round(self.person["clock_minutes"], 2))
                    measured = measure(self.person, step, start,
                                       capture(self.world, self.person),
                                       list(result.facts), result.success, stamp,
                                       action_result=result)
                    diagnostic = classify(self.world, self.person, step, prior, result)
                    record_action_outcome(self.person, step, result.success,
                                          list(result.facts), stamp, self.person["pos"])
                lines = trace.records()
            except Exception:
                # Operación de prueba atómica aunque el código lance una excepción.
                self.world = saved_world
                self.person = saved_person
                self.rng.setstate(saved_rng)
                raise
            report = {"step": step, "result": result.to_record(),
                      "diagnostic": diagnostic,
                      "measurement": {"id": measured["id"],
                                      "inventory_delta": measured["inventory_delta"],
                                      "needs_delta": measured["needs_delta"]}
                      if measured else None,
                      "trace": lines}
            self.last = report
            self.history.append({"op": step["op"], "success": result.success,
                                 "status": result.status,
                                 "facts": list(result.facts)[:2]})
            return self.state()

    def payload(self, provider="gemini"):
        if provider not in ("gemini", "groq"):
            raise ValueError("Proveedor de previsualización no soportado.")
        with self.lock:
            with ExecutionTrace() as trace:
                context = context_for(self.world, self.person, [],
                                      "Laboratorio · minuto " + str(round(self.person["clock_minutes"], 2)))
                cfg = {"PROVIDER": provider,
                       "MODEL": "gemini-3.1-flash-lite" if provider == "gemini" else "openai/gpt-oss-20b",
                       "GEMINI_API_KEY": "simulacion-sin-red", "GROQ_API_KEY": "simulacion-sin-red"}
                _, payload, _ = build_deliberation_request(cfg, context)
            if provider == "gemini":
                sent = json.loads(payload["contents"][0]["parts"][0]["text"].split("SITUACIÓN REAL: ", 1)[1])
            else:
                sent = json.loads(payload["messages"][1]["content"])
            return {"provider": provider, "context": sent,
                    "sections_omitted": sorted(set(context) - set(sent)),
                    "trace": trace.records(),
                    "note": "Vista real del constructor de payload; no se envió ninguna consulta LLM."}

class HistorySource:
    """Sólo administra un archivo de consulta. Nunca modifica la partida original."""
    def __init__(self):
        import tempfile
        self.lock = threading.RLock()
        self.path = DB if DB.is_file() else None
        self.temp_directory = tempfile.TemporaryDirectory(prefix="nilo-historial-cargado-")

    def load_bytes(self, data):
        if not data.startswith(b"SQLite format 3\x00"):
            raise ValueError("El archivo seleccionado no es una base SQLite válida.")
        file = Path(self.temp_directory.name) / "partida_cargada.sqlite3"
        with self.lock:
            file.write_bytes(data)
            from historical_lab import catalog
            try:
                checked = catalog(file)
            except Exception:
                file.unlink(missing_ok=True)
                raise
            self.path = file
            return checked

    def use_default(self):
        with self.lock:
            if not DB.is_file():
                raise ValueError("No existe una partida en esta carpeta.")
            self.path = DB
            from historical_lab import catalog
            return catalog(self.path)

    def require(self):
        with self.lock:
            if self.path is None or not self.path.is_file():
                raise ValueError("No hay partida cargada. Elegí un archivo .sqlite3.")
            return self.path



class Handler(BaseHTTPRequestHandler):
    lab = None

    def log_message(self, *_):
        pass

    def json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", "/index.html","/sandbox","/historico"):
            source = (HTML_FILE if path=="/sandbox" else
                      HISTORY_HTML_FILE if path=="/historico" else SCENARIO_HTML_FILE)
            contents = source.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
            self.send_header("Content-Length", str(len(contents)))
            self.end_headers()
            self.wfile.write(contents)
        elif path == "/api/catalog":
            from laboratorio_casos import catalog
            self.json(catalog())
        elif path.startswith("/api/scenario/"):
            from laboratorio_casos import run
            try:
                scenario_id=path.rsplit("/",1)[-1]
                if len(scenario_id)>90:
                    raise ValueError("Identificador de escenario demasiado largo")
                raw=(parse_qs(urlsplit(self.path).query).get("seed") or [None])[0]
                seed=int(raw) if raw is not None else None
                self.json(run(scenario_id, seed=seed))
            except (ValueError, KeyError, TypeError) as exc:
                self.json({"error":str(exc)},400)
        elif path in ("/api/history/catalog", "/api/history/event", "/api/history/default"):
            try:
                from historical_lab import catalog, select_event
                source = self.history.require()
                if path.endswith("default"):
                    result = self.history.use_default()
                elif path.endswith("catalog"):
                    result = catalog(source)
                else:
                    ids = parse_qs(urlsplit(self.path).query).get("id") or [""]
                    result = select_event(source, ids[0])
                self.json(result)
            except (ValueError, sqlite3.Error, OSError) as exc:
                self.json({"error": str(exc)}, 400)
        elif path == "/api/state":
            self.json(self.lab.state())
        elif path == "/api/payload":
            try:
                provider = (parse_qs(urlsplit(self.path).query).get("provider") or ["gemini"])[0]
                self.json(self.lab.payload(provider))
            except (ValueError, KeyError) as exc:
                self.json({"error": str(exc)}, 400)
        else:
            self.json({"error": "No encontrado"}, 404)

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/api/history/upload":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 16 <= size <= 200 * 1024 * 1024:
                    raise ValueError("La partida debe ocupar entre 16 bytes y 200 MB.")
                data = self.rfile.read(size)
                if len(data) != size:
                    raise ValueError("Carga incompleta.")
                return self.json(self.history.load_bytes(data))
            except (ValueError, OSError, sqlite3.Error) as exc:
                return self.json({"error": str(exc)}, 400)
        if path not in ("/api/reset", "/api/act", "/api/manual", "/api/history/replay"):
            return self.json({"error": "No encontrado"}, 404)
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.json({"error": "Se requiere JSON"}, 415)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 16000:
                return self.json({"error": "Solicitud fuera de límite"}, 413)
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Se esperaba un objeto JSON.")
            if path == "/api/history/replay":
                from historical_lab import replay
                result = replay(self.history.require(), body.get("id",""),
                                override=body.get("override"),
                                max_ticks=body.get("max_ticks",400))
            elif path == "/api/manual":
                from laboratorio_casos import sandbox
                result=sandbox(body.get("steps"),seed=body.get("seed",7321),
                               fixtures=body.get("fixtures",[]),mode=body.get("mode","sin_proyecto"))
            elif path == "/api/reset":
                result = self.lab.reset(body.get("mode", "nuevo"), body.get("seed", 7321),
                                        body.get("kit", False) is True)
            else:
                result = self.lab.act(body.get("step"))
            self.json(result)
        except (ValueError, TypeError, KeyError, sqlite3.Error) as exc:
            self.json({"error": str(exc)}, 400)
        except Exception as exc:
            self.json({"error": "Error del motor: " + type(exc).__name__}, 500)


def main():
    port = int(os.environ.get("NILO_LAB_PORT", "8766"))
    Handler.lab = MotorLab()
    Handler.history = HistorySource()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    address = "http://127.0.0.1:" + str(port)
    print("\nLABORATORIO DEL MOTOR · Nilo\n" + address)
    print("Estado aislado en RAM. Sin llamadas LLM ni cambios en la partida original.")
    threading.Timer(1.2, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever(poll_interval=.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
