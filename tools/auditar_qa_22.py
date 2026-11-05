"""Etapa 22: inventario auditable de tests y puertas transversales.

No confundir inventario de pruebas con cobertura de líneas. El reporte cuenta
test_* definidos en los archivos, no los da por ejecutados. La suite CI
es la fuente de verdad para ejecución, skips y éxito.
"""
from __future__ import annotations

import ast
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

STAGES={
    "esquema_estado": ("tests/test_estado_07.py","tests/test_identidad_07.py"),
    "tiempo_y_operaciones": ("tests/test_tiempo_07.py","tests/test_operaciones_07.py"),
    "mundo_y_navegacion": ("tests/test_mundo_08.py","tests/test_navegacion_09.py"),
    "recursos_y_objetos": ("tests/test_recursos_10.py","tests/test_objetos_11.py"),
    "interacciones_fisicas": ("tests/test_interacciones_12.py","tests/test_fisiologia_13.py"),
    "observacion_y_cognicion": ("tests/test_observacion_14.py","tests/test_memoria_16.py"),
    "deliberacion_y_autonomia": ("tests/test_deliberacion_15.py","tests/test_autonomia_17.py"),
    "persistencia_y_migracion": ("tests/test_persistencia_18.py",),
    "api_y_interfaz": ("tests/test_api_19.py","tests/test_interfaz_20.py"),
    "laboratorio": ("tests/test_laboratorio_21.py",),
    "integracion_y_metamorfismos": ("tests/test_auditoria_integral_motor.py",
                                   "tests/test_qa_22.py"),
}
GATES=(
    "tools/auditar_arquitectura.py",
    "tools/auditar_identidad_07.py",
    "tools/auditar_operaciones_07.py",
    "tools/auditar_persistencia_18.py",
    "tools/auditar_api_19.py",
    "tools/auditar_interfaz_20.py",
    "tools/auditar_laboratorio_21.py",
    "tools/benchmark_navegacion_09.py",
    "tools/benchmark_persistencia_18.py",
    "tools/benchmark_qa_22.py",
    "tools/cobertura_qa_22.py",
    "tests/fixtures/baseline_historico_07.zip",
    "tests/fixtures/replay_basico.json",
    "tools/verificar_paquete_07.py",
)

def defined_tests(path):
    code=ast.parse(path.read_text("utf-8"),filename=str(path))
    names=set()
    for node in ast.walk(code):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                names.add((node.lineno,node.name))
    return len(names)


def inventory():
    errors=[]
    files=sorted((ROOT/"tests").glob("test_*.py"))
    if len(files)<65:
        errors.append("El inventario de pruebas perdió módulos de regresión")
    for p in GATES:
        if not (ROOT/p).is_file():errors.append("Puerta requerida ausente: "+p)
    summary={p.relative_to(ROOT).as_posix():defined_tests(p) for p in files}
    focus={}
    for group,paths in STAGES.items():
        missing=[p for p in paths if p not in summary]
        if missing:
            errors.append("Dominio sin suite: "+group+": "+", ".join(missing))
            continue
        total=sum(summary[p] for p in paths)
        if total<4:
            errors.append("Dominio con menos de cuatro pruebas declaradas: "+group)
        focus[group]={"files":len(paths),"tests_defined":total}
    qa=summary.get("tests/test_qa_22.py",0)
    if qa<15:errors.append("Faltan tests metamórficos de QA 22")
    workflow=(ROOT/".github/workflows/validacion.yml").read_text("utf-8")
    for required in (
        "python -m unittest discover -s tests -v",
        "python validar_escenarios.py --seed 7321",
        "python tools/verificar_paquete_07.py",
        "python tools/benchmark_qa_22.py",
        "python tools/cobertura_qa_22.py",
        "python tools/auditar_qa_22.py",
        "test_qa_22.py",
        "Comparar huellas entre procesos independientes",
    ):
        if required not in workflow:errors.append("CI no aplica puerta: "+required)
    # El código del motor se mantiene separado de HTTP e incluso del
    # laboratorio; no se aceptan dos implementaciones del intérprete de acciones.
    engine=(ROOT/"nilo_runtime/application/engine.py").read_text("utf-8")
    sandbox=(ROOT/"nilo_runtime/labs/sandbox.py").read_text("utf-8")
    if "class Simulation(" not in engine or "sim.plan_ready(" not in sandbox:
        errors.append("El sandbox no utiliza el motor real")
    navigation=(ROOT/"nilo_runtime/worlds/navigation.py").read_text("utf-8")
    if "except (ValueError,TypeError,KeyError,OverflowError)" not in navigation:
        errors.append("La navegación no contiene el rechazo seguro de infinitos")
    packages=(ROOT/"MANIFIESTO_SHA256.json").read_text("utf-8")
    manifest=json.loads(packages).get("files",{})
    for item in ("tests/test_qa_22.py","tools/benchmark_qa_22.py",
                 "tools/auditar_qa_22.py","tools/cobertura_qa_22.py"):
        if item not in manifest:errors.append("Falta en manifiesto: "+item)
    return {
        "schema":"nilo_qa_inventory_v1",
        "test_files":len(files),
        "tests_defined_static_count":sum(summary.values()),
        "legacy_modules":sum(p.name.startswith("test_v0") for p in files),
        "qa22_tests_defined":qa,
        "domains":focus,
        "gates_required":len(GATES),
        "errors":errors,
        "disclaimer":"AST/inventario, no cobertura de líneas; la ejecución se verifica en GitHub Actions."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=inventory()
    text=json.dumps(result,indent=2,ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text+"\n",encoding="utf-8")
    print(text)
    if result["errors"]:raise SystemExit(1)


if __name__=="__main__":
    main()
