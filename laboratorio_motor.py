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
    "resources.py:exchange_units": "Verifica el balance de lotes materiales",
    "tool_use.py:use_action": "Prueba acciones de herramientas con efectos reales",
    "fabrication.py:combine_action": "Combina materiales bajo transacción física",
    "fabrication.py:fabricate_action": "Fabrica artefactos bajo precondiciones",
    "intervention.py:execute_prepared": "Publica una reforma tras validarla completa",
    "intervention.py:_preflight": "Valida materiales, componentes y capacidades",
    "construction.py:_apply_intervention_mutating": "Interviene únicamente una copia del objeto",
    "objects.py:physical_item": "Crea una pieza transportable con forma física declarada",
    "objects.py:make_item": "Asigna identidad y propiedades a un objeto físico",
    "objects.py:item_effects": "Calcula capacidades desde forma y resistencia",
    "components.py:normalize_parts": "Valida materiales y formas de piezas",
    "components.py:normalize_joints": "Comprueba tipos y referencias de uniones",
    "components.py:connected_parts": "Verifica continuidad del ensamblaje",
    "construction.py:ensure_object": "Migra objeto legado sin consumir IDs innecesarios",
    "world.py:inspect_target": "Comprueba visibilidad y examina el objetivo",
    "tool_use.py:dig_with_tool": "Contrasta herramienta y resistencia de roca",
    "tool_use.py:adjacent_rock": "Selecciona roca físicamente adyacente",
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
    "materials.py:geometry_from_step": "Interpreta geometría declarada",
    "materials.py:body_physics": "Calcula atributos físicos de materiales",
    "materials.py:evaluate_containment": "Evalúa retención de contenido",
    "materials.py:evaluate_buoyancy": "Evalúa flotación",
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
    "survival.py:update_needs": "Conserva el contrato histórico de evolución corporal",
    "needs.py:update_needs": "Evolución física de energía, hambre y sed",
    "needs.py:perceived_needs": "Proyecta sensaciones sin barras numéricas",
    "policy.py:rest_minutes": "Valida descanso voluntario",
    "policy.py:wait_minutes": "Valida espera sin recuperación",
    "policy.py:should_collapse": "Decide pérdida de conciencia por energía",
    "policy.py:can_wake": "Decide recuperación de conciencia",
    "shelter.py:shelter_properties": "Evalúa resguardo físico sin interpretar nombres",
    "island_views.py:survival_conditions": "Consulta resguardo y fuentes de agua de la posición",
    "brain.py:context_for": "Prepara la percepción y memorias del contexto",
    "budget.py:compact_context": "Acota campos del contexto",
    "budget.py:bounded_context": "Ajusta contexto al presupuesto del modelo",
    "gateway.py:build_deliberation_request": "Arma el mensaje final sin enviarlo",
    "gateway.py:build_chat_request": "Prepara mensajes de chat sin llamar a la API",
    "cognitive_projection.py:project_context": "Filtra conocimiento no perceptible",
    "responses.py:normalize_decision": "Valida respuesta JSON y acciones planificadas",
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
                "fabrication.py": "nilo_runtime/worlds/fabrication.py",
                "intervention.py": "nilo_runtime/worlds/intervention.py",
                "tool_use.py": "nilo_runtime/worlds/tool_use.py",
                "objects.py": "nilo_runtime/worlds/objects.py",
                "components.py": "nilo_runtime/worlds/components.py",
                "materials.py": "nilo_runtime/physics/materials.py",
                "needs.py": "nilo_runtime/physiology/needs.py",
                "policy.py": "nilo_runtime/physiology/policy.py",
                "shelter.py": "nilo_runtime/worlds/shelter.py",
            }.get(row["file"], row["file"])
            row["url"] = ("https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/"
                          + source_path + "#L" + str(row["first"])
                          + "-L" + str(row["last"]))
            rows.append(row)
        return rows


from nilo_runtime.labs.sandbox import SimulationSandbox


class MotorLab(SimulationSandbox):
    """Fachada compatible del laboratorio, sin motor físico duplicado."""

    def __init__(self):
        super().__init__(trace_factory=ExecutionTrace)

    def reset(self,mode="nuevo",seed=7321,kit=False):
        # Mantener la ruta histórica parcheable por los tests existentes.
        return super().reset(mode,seed,kit,source=DB)


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
