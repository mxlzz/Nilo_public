"""Auditoría estructural de navegación 0.7/09, sin LLM ni UI."""
from __future__ import annotations
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OWNED={'cave_exit','known_exit_route','passable','pathfind','reachable_shores',
       'resolve_go','move','exploration_frontier','actual_travel_direction',
       'advance_navigation','choose_frontier'}
FORBIDDEN={'world','brain','island_planning','environments','nilo',
           'nilo_runtime.application','nilo_runtime.web','providers'}
def inspect():
    issues=[]
    path=ROOT/'nilo_runtime/worlds/navigation.py'
    if not path.exists():return ['Falta la única implementación de navegación']
    tree=ast.parse(path.read_text(encoding='utf-8'))
    defs={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    missing=OWNED-defs
    if missing:issues.append('Definiciones faltantes: '+str(sorted(missing)))
    if 'NavigationIndex' not in defs:issues.append('Falta NavigationIndex')
    for node in ast.walk(tree):
        names=([a.name for a in node.names] if isinstance(node,ast.Import)
               else [node.module or ''] if isinstance(node,ast.ImportFrom) else [])
        for name in names:
            if any(name==x or name.startswith(x+'.') for x in FORBIDDEN):
                issues.append('Import invertido: '+name)
    root=ast.parse((ROOT/'world.py').read_text(encoding='utf-8'))
    duplicated=OWNED & {n.name for n in root.body if isinstance(n,ast.FunctionDef)}
    if duplicated:issues.append('Funciones duplicadas: '+str(sorted(duplicated)))
    return issues
if __name__=='__main__':
    problems=inspect()
    if problems:raise SystemExit('\n'.join(problems))
    print('Etapa 09: rutas en worlds/navigation, sin duplicación/ciclos.')
