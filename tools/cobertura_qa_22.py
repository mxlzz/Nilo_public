"""Cobertura por líneas EJECUTADAS de un conjunto acotado de módulos Nilo 0.7.

Solo biblioteca estándar: sys.settrace + dis.findlinestarts. No modifica
módulos de producción ni incluye red. NO es cobertura de ramas ni de toda
la aplicación: los tests invocados son un subconjunto explícito de suites.
"""
from __future__ import annotations

import argparse
import dis
import json
from pathlib import Path
import sys
import threading
from types import CodeType
import unittest

ROOT=Path(__file__).resolve().parents[1]
TESTS=ROOT/"tests"
for p in (ROOT,TESTS):
    if str(p) not in sys.path:sys.path.insert(0,str(p))

MODULES=(
    "nilo_runtime/core/state.py",
    "nilo_runtime/core/clock.py",
    "nilo_runtime/worlds/island.py",
    "nilo_runtime/worlds/navigation.py",
    "nilo_runtime/worlds/resources.py",
    "nilo_runtime/physiology/needs.py",
    "nilo_runtime/autonomy/agenda.py",
    "nilo_runtime/autonomy/projects.py",
    "nilo_runtime/cognition/memory.py",
    "nilo_runtime/agent/gateway.py",
    "nilo_runtime/storage/repository.py",
    "nilo_runtime/storage/backups.py",
    "nilo_runtime/web/api.py",
    "nilo_runtime/web/security.py",
    "nilo_runtime/web/http.py",
    "nilo_runtime/labs/sandbox.py",
)
SUITES=(
    "test_qa_22.py",
    "test_api_19.py",
    "test_persistencia_18.py",
    "test_navegacion_09.py",
    "test_fisiologia_13.py",
    "test_memoria_16.py",
    "test_laboratorio_21.py",
)
PATHS={str(ROOT/p):p for p in MODULES}
EXECUTED={name:set() for name in MODULES}


def code_lines(co):
    """Líneas ejecutables según los offsets de bytecode Python 3.12."""
    result={lineno for _,lineno in dis.findlinestarts(co)
            if isinstance(lineno,int) and lineno>0}
    for obj in co.co_consts:
        if isinstance(obj,CodeType):
            result.update(code_lines(obj))
    return result


def line_trace(frame,event,arg):
    if event=="line":
        path=PATHS.get(frame.f_code.co_filename)
        if path is not None:
            EXECUTED[path].add(frame.f_lineno)
    return line_trace


def call_trace(frame,event,arg):
    if event=="call" and frame.f_code.co_filename in PATHS:
        return line_trace
    return None


def run():
    suite=unittest.TestSuite()
    loader=unittest.TestLoader()
    for filename in SUITES:
        suite.addTests(loader.discover(
            str(TESTS),pattern=filename,top_level_dir=str(TESTS)))
    baseline=threading.gettrace()
    prior=sys.gettrace()
    sys.settrace(call_trace)
    threading.settrace(call_trace)
    try:
        result=unittest.TextTestRunner(verbosity=1,stream=sys.stderr).run(suite)
    finally:
        sys.settrace(prior)
        threading.settrace(baseline)
    rows=[]
    for path in MODULES:
        absolute=ROOT/path
        lines=code_lines(compile(absolute.read_text("utf-8"),str(absolute),"exec"))
        hit=len(lines&EXECUTED[path])
        rows.append({
            "module":path,
            "executable_lines":len(lines),
            "executed_lines":hit,
            "lines_pct":round(100*hit/max(1,len(lines)),2),
        })
    total=sum(x["executable_lines"] for x in rows)
    executed=sum(x["executed_lines"] for x in rows)
    return {
        "schema":"nilo_selected_line_coverage_v1",
        "method":"sys.settrace (líneas ejecutadas) / dis.findlinestarts",
        "python_runtime":sys.version.split()[0],
        "suites":list(SUITES),
        "tests_run":result.testsRun,
        "failures":len(result.failures),
        "errors":len(result.errors),
        "skipped":len(result.skipped),
        "selected_lines_total":total,
        "selected_lines_hit":executed,
        "selected_line_coverage_pct":round(100*executed/max(1,total),2),
        "modules":rows,
        "limits":"Subconjunto y líneas, no cobertura global ni de ramas. "
                 "Subprocesos externos pueden no estar instrumentados.",
        "success":result.wasSuccessful(),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=run()
    data=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(data+"\n",encoding="utf-8")
    print(data)
    if not result["success"]:
        raise SystemExit(1)


if __name__=="__main__":
    main()
