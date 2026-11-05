"""Nilo 0.7 etapa 17: propietarios únicos, contratos de proyectos y delegaciones."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

MODULES={
    "projects":("project_lifecycle.py",{
        "retire_project","completion_evidence","closure_diagnostic","project_needs_review"}),
    "goal_evidence":("goal_evidence.py",{
        "check_goal","select_closure_evidence","_cites_record"}),
    "agenda":("agenda.py",{
        "choose_agenda_step","normalize_task","safe_step","record_agenda_result"}),
    "habits":("habits.py",{
        "choose_wait_action","set_wait_preferences","record_wait_selection"}),
    "strategy":("strategy_review.py",{
        "semantic_signature","detect_repetition","repeated_strategies"}),
    "progress":("project_progress.py",{
        "advance_evidence","repeated_methods"}),
}

def defs(filename):
    tree=ast.parse((ROOT/filename).read_text("utf-8"),filename=filename)
    return {node.name for node in tree.body if isinstance(node,ast.FunctionDef)}

def inspect():
    errors=[]
    for name,(facade,required) in MODULES.items():
        owner=f"nilo_runtime/autonomy/{name}.py"
        missing=required-defs(owner)
        if missing:errors.append(owner+": faltan "+repr(sorted(missing)))
        if defs(facade):
            errors.append("Fachada con implementación paralela: "+facade)
    from agenda import choose_agenda_step
    from project_lifecycle import retire_project
    from habits import choose_wait_action
    from strategy_review import repeated_strategies
    from goal_evidence import select_closure_evidence
    from nilo_runtime.autonomy import agenda,projects,habits,strategy,goal_evidence
    if choose_agenda_step is not agenda.choose_agenda_step:
        errors.append("Agenda con duplicación de ejecutores")
    if retire_project is not projects.retire_project:
        errors.append("Proyecto con duplicación de ejecutores")
    if choose_wait_action is not habits.choose_wait_action:
        errors.append("Hábito con duplicación de ejecutores")
    if repeated_strategies is not strategy.repeated_strategies:
        errors.append("Estrategia con duplicación de ejecutores")
    if select_closure_evidence is not goal_evidence.select_closure_evidence:
        errors.append("Cierre con dos validadores")
    selection=(ROOT/"nilo_runtime/autonomy/habits.py").read_text("utf-8")
    if "known_only=True" not in selection:
        errors.append("Hábitos actuales pueden leer rutas ocultas")
    delegated=(ROOT/"nilo_runtime/autonomy/agenda.py").read_text("utf-8")
    if "Proyecto no activo" not in delegated or "measured_records(" not in delegated:
        errors.append("Agenda sin guardas de ciclo de vida o pruebas por ID")
    closing=(ROOT/"nilo_runtime/autonomy/projects.py").read_text("utf-8")
    if closing.index("if status=='terminado' and not evidence")>closing.index("project['status']=status"):
        errors.append("El rechazo de cierre muta el proyecto antes de fallar")
    use_cases=(ROOT/"nilo_runtime/application/clockwork.py").read_text("utf-8")
    if "followup=(self.followup_without_llm()" not in use_cases or "else None)" not in use_cases:
        errors.append("El motor sigue inventando pruebas de herramientas sin deliberación")
    if "repeated_strategies(" not in use_cases:
        errors.append("Los bucles siguen agrupados solo por nombre de operación")
    decisions=(ROOT/"nilo_runtime/application/decisions.py").read_text("utf-8")
    if "or getattr(self,'historical_replay',False))" not in decisions:
        errors.append("No se preserva investigación externa a un proyecto al retirarlo")
    if not (ROOT/"tests/test_autonomia_17.py").exists():
        errors.append("Faltan pruebas específicas de la etapa")
    return errors

if __name__=="__main__":
    found=inspect()
    if found:raise SystemExit("\n".join(found))
    print("Etapa 17: proyectos, agenda, habilidades y estrategias con dueño único.")
