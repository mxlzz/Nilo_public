"""Etapa 21: contratos de laboratorio, aislamiento y perfiles reversibles."""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from nilo_runtime.core.lab_settings import OPTIONAL_CONTEXT,LIMITS,baseline
from nilo_runtime.labs.profiles import ProfileStore


def check():
    problems=[]
    modules=[
        "nilo_runtime/core/lab_settings.py",
        "nilo_runtime/labs/profiles.py",
        "nilo_runtime/labs/sandbox.py",
        "nilo_runtime/labs/hub.py",
        "laboratorio_motor.py",
        "laboratorio_casos.py",
        "historical_lab.py",
        "nilo_runtime/agent/gateway.py",
    ]
    for rel in modules:
        path=ROOT/rel
        if not path.is_file():
            problems.append("Falta archivo "+rel)
            continue
        try:ast.parse(path.read_text("utf-8"),filename=rel)
        except SyntaxError as exc:problems.append("Sintaxis incorrecta "+str(exc))
    if problems:return problems
    motor=(ROOT/"laboratorio_motor.py").read_text("utf-8")
    sandbox=(ROOT/"nilo_runtime/labs/sandbox.py").read_text("utf-8")
    profiles=(ROOT/"nilo_runtime/labs/profiles.py").read_text("utf-8")
    hub=(ROOT/"nilo_runtime/labs/hub.py").read_text("utf-8")
    brain=(ROOT/"brain.py").read_text("utf-8")
    gateway=(ROOT/"nilo_runtime/agent/gateway.py").read_text("utf-8")
    for marker in ("class MotorLab(SimulationSandbox)","create_lab_server(",
                   "href="):
        if marker=="href=":continue
        if marker not in motor:problems.append("Fachada sin delegación: "+marker)
    if "def _execute(" in motor or "def _execute(" in sandbox:
        problems.append("Sobrevive un segundo motor físico del laboratorio")
    for marker in ("Simulation(","sim.plan_ready(","sim.tick(",
                   "self.sim.conn.close()","sqlite3.connect(",
                   "sim.think=lambda:None"):
        if marker not in sandbox:
            problems.append("Sandbox sin contrato del motor real: "+marker)
    for marker in ("ProfileStore","def apply(","def restore(",
                   "def _checkpoint(","os.replace(",
                   "checkpoint","_sha(_bytes("):
        if marker not in profiles:
            problems.append("Perfiles sin rollback/huella: "+marker)
    for forbidden in ("exec(","eval(","compile(","subprocess.","write_text(code",
                      "config.env"):
        if forbidden in profiles:
            problems.append("Almacenamiento de perfiles tiene operación insegura: "+forbidden)
    if "config_overlay(ROOT)" not in brain:
        problems.append("Nilo no recibe los límites del perfil aplicado")
    if "_LAB_OMIT_CONTEXT" not in gateway or "_LAB_PROMPT_NOTE" not in gateway:
        problems.append("El prompt real no usa las variantes validadas")
    if "nilo_runtime.labs" in gateway:
        problems.append("Dependencia agente -> laboratorio invertida")
    for marker in ("def preview(","def compare(","def backup_world(",
                   "def restore_world_copy(","build_deliberation_request(",
                   "restore_as_copy(","backup_file("):
        if marker not in hub:
            problems.append("Hub sin operación respaldada por código real: "+marker)
    for marker in ("/ajustes","/api/lab/profile/list",
                   "/api/lab/profile/load","/api/lab/profile/apply",
                   "/api/lab/profile/restore",
                   "/api/lab/profile/compare",
                   "/api/lab/profile/backup-world"):
        if marker not in motor:
            problems.append("Ruta de laboratorio ausente: "+marker)
    html=(ROOT/"laboratorio_ajustes.html")
    if not html.is_file():problems.append("No existe interfaz del centro de ajustes")
    else:
        source=html.read_text("utf-8")
        for marker in ("id=\"prompt-note\"","id=\"optional\"",
                       "id=\"world-backup\"","id=\"world-restore\"",
                       "/api/lab/profile/preview","/api/lab/profile/restore"):
            if marker not in source:
                problems.append("Interfaz sin control: "+marker)
    if not (ROOT/"tests/test_laboratorio_21.py").is_file():
        problems.append("Faltan pruebas específicas de etapa 21")
    if not OPTIONAL_CONTEXT or not LIMITS or baseline()["omit_context"]:
        problems.append("Esquema de perfil inconsistente")
    return problems


if __name__=="__main__":
    results=check()
    if results:raise SystemExit("\n".join(results))
    print("Etapa 21: sandbox unificado con Simulation y perfiles/backup verificados.")
