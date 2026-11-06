"""Banco de escenarios del motor: ejecución íntegra de planes sin llamar a LLM.

Usa Simulation.plan_ready / Simulation.tick y SQLite temporal. Las condiciones
preparadas por cada caso se describen expresamente; no son éxitos simulados.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
import copy
import json
import linecache
from pathlib import Path
import sys
import tempfile

from action_contracts import ACTION_GUIDE
from brain import normalize_decision, build_deliberation_request
from nilo import Simulation
from world import tile, tile_key, set_tile, reveal, valid, MATERIALS, YIELDS

ROOT = Path(__file__).resolve().parent
WATCH = {
    "brain.py": {"context_for"},
    "nilo_runtime/agent/responses.py": {"normalize_decision", "parse_json"},
    "nilo_runtime/agent/gateway.py": {"build_deliberation_request", "request_llm", "build_chat_request", "request_chat"},
    "nilo_runtime/agent/budget.py": {"compact_context", "bounded_context"},
    # La traza sigue las funciones REALES después de extraer el motor a
    # casos de uso, no las confunde con la fachada nilo.py.
    "nilo_runtime/application/session.py": {"write"},
    "nilo_runtime/application/records.py": {"event"},
    "nilo_runtime/application/decisions.py": {"plan_ready", "validate_plan", "improve_plan", "followup_without_llm"},
    "nilo_runtime/application/clockwork.py": {"tick"},
    "island_planning.py": {"validate_plan", "improve_plan"},
    "environments.py": {"perform_result", "start_navigation", "move_navigation", "finish_navigation"},
    "world.py": {"resolve_go", "pathfind", "choose_frontier", "exploration_frontier", "prepare_navigation",
                 "advance_navigation", "navigation_result", "execute_action", "nearest_known",
                 "inspect_target", "dig_with_tool", "reveal"},
    "action_results.py": {"result_from_execution", "evidence_before"},
    "action_contracts.py": {"before", "classify"},
    "experiment_log.py": {"measure", "capture", "observational_conclusion"},
    "construction.py": {"initialize_object", "apply_intervention", "recompute"},
    "structural_loads.py": {"interact", "load_limit", "stored_load"},
    "vessels.py": {"interact", "capacity"},
    "capabilities.py": {"dispatch", "resolve"},
    "survival.py": {"update_needs"},
    "project_progress.py": {"advance_evidence", "discovered_during_action"},
    "inventions.py": {"register_design", "submit_proposal", "submit_debug_report", "record_action_outcome", "record_personal_experience"},
    "laboratory.py": {"compare"},
    "project_lifecycle.py": {"completion_evidence", "closure_diagnostic", "retire_project"},
    "goal_evidence.py": {"check_goal"},
    "timing.py": {"effective_speed"},
    "cognitive_projection.py": {"project_context"},
    # prompt_budget.py es fachada; los recortes reales viven en agent/budget.py.
    "agenda.py": {"set_agenda", "choose_agenda_step", "record_agenda_result"},
}
EXPLAIN = {
    "normalize_decision": "Normaliza la orden que habría generado el LLM",
    "plan_ready": "Aplica el cambio de proyecto y valida el plan",
    "validate_plan": "Descarta acciones incompatibles con condiciones físicas conocidas",
    "improve_plan": "Descarta pasos redundantes por conocimiento previo",
    "tick": "Avanza el reloj y procesa operaciones pendientes",
    "prepare_navigation": "Comprueba una ruta conocida y prepara el viaje",
    "advance_navigation": "Ejecuta tramos reales y revela el terreno",
    "navigation_result": "Resume el desplazamiento realizado",
    "resolve_go": "Resuelve el destino y sus restricciones",
    "exploration_frontier": "Busca una frontera alcanzable",
    "choose_frontier": "Selecciona candidatos de exploración",
    "pathfind": "Calcula una ruta conocida",
    "nearest_known": "Busca una fuente de recursos alcanzable",
    "execute_action": "Aplica las consecuencias físicas de la operación",
    "perform_result": "Envuelve las consecuencias en un resultado verificable",
    "result_from_execution": "Clasifica el resultado sin confiar en la narrativa",
    "measure": "Registra mediciones antes/después",
    "classify": "Contrasta las precondiciones y el resultado con el contrato",
    "update_needs": "Actualiza necesidades por el tiempo transcurrido",
    "record_action_outcome": "Registra los efectos de la operación en el archivo",
    "record_personal_experience": "Registra la experiencia personal del agente",
    "advance_evidence": "Determina si hubo avance material o conocimiento nuevo",
    "dispatch": "Dirige la interacción al módulo físico correspondiente",
    "interact": "Evalúa capacidad física del objeto y método elegido",
    "write": "Persiste una instantánea coherente en SQLite",
    "context_for": "Prepara percepción y recuerdos para deliberación",
    "register_design": "Documenta una ficha de diseño sin fabricar",
    "submit_proposal": "Registra propuesta sin instalar nueva física",
    "submit_debug_report": "Registra una anomalía hipotética con evidencias",
    "compare": "Contrasta mediciones documentadas",
    "completion_evidence": "Comprueba evidencias antes de cerrar un proyecto",
    "check_goal": "Verifica un criterio de cierre medible",
    "effective_speed": "Calcula el ritmo efectivo del reloj",
    "project_context": "Filtra datos internos que no debe conocer el agente",
    "bounded_context": "Recorta el contexto a un límite de presupuesto",
}
GROUPS = [
    ("01", "Acciones elementales"),
    ("02", "Navegación y exploración"),
    ("03", "Recolección y necesidades"),
    ("04", "Fabricación y física"),
    ("05", "Interacciones y construcciones"),
    ("06", "Investigación y registros"),
    ("07", "Planes y proyectos"),
    ("08", "Situaciones límite"),
]
CASES = []

def case(id, group, title, description, plan, *, fixture=(), mode="sin_proyecto", expected="accion",
         seed=7321, deliberations=None, note=""):
    CASES.append({"id": id, "group": group, "title": title, "description": description,
                  "plan": plan, "fixture": list(fixture), "mode": mode, "expected": expected,
                  "seed": seed, "deliberations": deliberations, "note": note})

# Cada variante representa una rama o clase de efecto, no una permutación de parámetros.
case("go-coord", "01", "Ir a una coordenada conocida",
     "Un trayecto válido hacia una casilla revelada.", [{"op":"go","x":16,"y":10}],
     fixture=("paso_libre",))
case("inspect-local", "01", "Inspeccionar una casilla visible",
     "Identificación de terreno, sin modificarlo.", [{"op":"inspect","x":15,"y":10}])
case("go-tree-name", "01", "go → árbol (capacidad pendiente)",
     "Comprueba que el comando por nombre NO está implementado; no simular éxito.",
     [{"op":"go","target":"arbol"}], expected="rechazo")
case("go-stone-name", "01", "go → piedra (capacidad pendiente)",
     "La petición por nombre aún no debe transformarse silenciosamente en coordenadas.",
     [{"op":"go","target":"piedra"}], expected="rechazo")
case("explore-auto", "01", "Explorar automáticamente",
     "Selecciona una frontera conocida y descubre casillas.", [{"op":"explore"}])
case("gather-stone", "01", "Recolectar piedra a mano",
     "Regla actual 0.6.1: sin herramienta y con rendimiento fijo; 33 % sigue pendiente.",
     [{"op":"gather","target":"piedra"}], fixture=("roca_cerca",))
case("eat", "01", "Comer un alimento existente",
     "Consume inventario y modifica necesidades.", [{"op":"eat"}], fixture=("equipo",))
case("rest", "01", "Descansar 60 minutos",
     "Duración solicitada, recuperación y mediciones.", [{"op":"rest","minutes":60}])
case("wait", "01", "Esperar sin descansar",
     "Distingue metabolismo pasivo y descanso voluntario.", [{"op":"wait","minutes":30}])
case("forage", "01", "Buscar alimento vegetal",
     "Recolección con depósito natural próximo.", [{"op":"forage"}], fixture=("arbol_cerca",))
case("drink", "01", "Beber de agua próxima",
     "No acredita potabilidad; necesita orilla físicamente accesible.",
     [{"op":"drink"}], fixture=("agua_cerca",))
case("inspect-invisible", "02", "Inspeccionar fuera del alcance",
     "Una negativa correcta distingue objeto lejano de objeto inexistente.",
     [{"op":"inspect","x":23,"y":7}], expected="fallo")
case("go-hidden", "02", "Destino no descubierto",
     "El validador no debe conceder una ruta a coordenadas ocultas.",
     [{"op":"go","x":35,"y":16}], expected="rechazo")
case("go-rock", "02", "Destino sobre roca sólida",
     "El validador distingue casilla conocida de casilla transitable.",
     [{"op":"go","x":16,"y":10}], fixture=("roca_cerca",), expected="rechazo")
case("go-water", "02", "Ir a una orilla conocida",
     "Una petición de agua debe resolverse en tierra firme.",
     [{"op":"go","target":"agua"}], fixture=("agua_cerca",))
case("go-unreachable-water", "02", "Ir al agua sin orilla descubierta",
     "No inventar una fuente alcanzable si todavía no la conoce.",
     [{"op":"go","target":"agua"}], expected="rechazo")
case("explore-north", "02", "Explorar sector norte",
     "La exploración dirigida no debe elegir silenciosamente el lado contrario.",
     [{"op":"explore","direction":"north"}])
case("explore-exhausted", "02", "Explorar sin fronteras conocidas",
     "Comprueba fallo físico y qué deja en el contador de estancamiento.",
     [{"op":"explore"}], fixture=("superficie_revelada",), expected="fallo")
case("descend-far", "02", "Descender lejos de la cueva",
     "La conexión entre niveles requiere proximidad real.",
     [{"op":"descend"}], expected="rechazo")
case("descend", "02", "Descender en la cueva",
     "Conexión correcta desde el portal.", [{"op":"descend"}], fixture=("entrada_cueva",))
case("ascend", "02", "Ascender desde la cueva",
     "Regreso desde la salida conocida.", [{"op":"ascend"}], fixture=("salida_cueva",))
case("gather-remote", "03", "Recolección con desplazamiento",
     "Reproduce el camino hacia el recurso y permite comparar tiempo de viaje/extracción.",
     [{"op":"gather","target":"piedra"}], fixture=("roca_lejana",))
case("gather-empty", "03", "Fuente de piedra agotada",
     "Nunca crear material si el depósito existe pero está vacío.",
     [{"op":"gather","target":"piedra"}], fixture=("piedra_agotada",), expected="fallo")
case("gather-invalid", "03", "Material desconocido",
     "El validador rechaza un nombre sin alias físico.",
     [{"op":"gather","target":"diamante interdimensional"}], expected="rechazo")
case("eat-empty", "03", "Comer sin alimentos",
     "La necesidad no produce comida.", [{"op":"eat"}], expected="fallo")
case("drink-far", "03", "Beber sin acceso al agua",
     "No inventa bebida por mera necesidad.", [{"op":"drink"}], expected="fallo")
case("energy-tension", "03", "Acción con cansancio elevado",
     "La fatiga modifica duración y, en extremos, puede interrumpir actividad.",
     [{"op":"rest","minutes":60}], fixture=("agotado",))
case("experiment", "04", "Experimentar dureza de piedra",
     "Necesita muestra real, registra conocimiento de material.",
     [{"op":"experiment","target":"piedra","method":"golpear"}], fixture=("equipo",))
case("experiment-no-sample", "04", "Ensayo sin muestra",
     "La física no debe inventar una muestra para poder medir.",
     [{"op":"experiment","target":"piedra","method":"golpear"}], fixture=("sin_equipo",), expected="rechazo")
case("combine", "04", "Combinar dos materiales",
     "Composición física con consumo de inventario.",
     [{"op":"combine","materials":["madera","fibra"],"method":"atar"}], fixture=("equipo",))
case("craft", "04", "Fabricar herramienta de punta",
     "La fabricación no demuestra automáticamente la utilidad de la herramienta.",
     [{"op":"craft","name":"punta de prueba","purpose":"excavar","materials":["madera","mineral oscuro"],"form":"punta"}],
     fixture=("equipo",))
case("craft-missing", "04", "Fabricar sin materiales",
     "El plan debe rechazar requisitos materiales ausentes.",
     [{"op":"craft","name":"punta de prueba","materials":["madera","mineral oscuro"],"form":"punta"}],
     fixture=("sin_equipo",), expected="rechazo")
case("excavate-no-tool", "04", "Excavar sin pico",
     "No concede excavación si Nilo carece de punta adecuada.",
     [{"op":"excavate"}], fixture=("roca_cerca",), expected="rechazo")
case("excavate-tool", "04", "Excavar con herramienta de punta",
     "Verifica resistencia, progreso y alteración del terreno.",
     [{"op":"excavate"}], fixture=("roca_cerca","pico",))
case("use-excavate", "04", "Usar punta para excavar",
     "Distingue uso físico de la herramienta de solo fabricar.",
     [{"op":"use","item":"$herramienta","method":"excavar","target":"roca"}],
     fixture=("roca_cerca","pico"))
case("build", "05", "Construir plataforma",
     "Construcción material y efectos sobre el inventario.",
     [{"op":"build","name":"plataforma laboratorio","purpose":"ensayar carga",
       "materials":["madera","madera"],"geometry":{"shape":"plataforma","size":2}}],
     fixture=("equipo",))
case("build-missing", "05", "Construir sin materiales",
     "No se permite generar una estructura de la nada.",
     [{"op":"build","name":"plataforma","materials":["madera","madera"]}],
     fixture=("sin_equipo",), expected="rechazo")
case("interact-vessel-fill", "05", "Llenar recipiente con agua",
     "Requiere recipiente hueco y agua adyacente; aumenta contenido físico real.",
     [{"op":"interact","method":"llenar","destination":"$vaso1","quantity":0.18}],
     fixture=("equipo","agua_cerca","recipiente"))
case("interact-vessel-store", "05", "Guardar sólido en recipiente",
     "El material pasa del inventario al recipiente sin duplicación.",
     [{"op":"interact","method":"guardar","destination":"$vaso1","material":"piedra","quantity":1}],
     fixture=("equipo","recipiente"))
case("interact-vessel-empty", "05", "Retirar de recipiente vacío",
     "Una operación imposible no crea sólidos.",
     [{"op":"interact","method":"retirar","source":"$vaso1","quantity":1}],
     fixture=("equipo","recipiente"),expected="fallo")
case("plan-vessel-transfer", "07", "Plan: llenar, transferir y beber",
     "Un ciclo de tres operaciones sobre dos recipientes materiales y una fuente ambiental.",
     [{"op":"interact","method":"llenar","destination":"$vaso1","quantity":0.18},
      {"op":"interact","method":"transferir","source":"$vaso1","destination":"$vaso2","quantity":0.18},
      {"op":"interact","method":"beber","source":"$vaso2","quantity":0.18}],
     fixture=("equipo","agua_cerca","dos_recipientes"))
case("interact-load", "05", "Ensayar carga estructural",
     "La prueba de resistencia no deposita material.",
     [{"op":"interact","method":"probar_carga","item":"$obra","material":"piedra","quantity":2}],
     fixture=("equipo","plataforma"))
case("interact-store", "05", "Depositar materiales en obra",
     "Transferencia persistente con conservación de masa.",
     [{"op":"interact","method":"depositar_carga","item":"$obra","material":"piedra","quantity":2}],
     fixture=("equipo","plataforma"))
case("interact-overload", "05", "Sobrecargar una obra",
     "Una carga superior a la capacidad debe fallar sin crear material.",
     [{"op":"interact","method":"depositar_carga","item":"$obra","material":"piedra","quantity":200}],
     fixture=("equipo","plataforma"), expected="fallo")
case("interact-unknown", "05", "Interacción inexistente",
     "Método fuera del registro físico; resultado no evaluable, sin éxito ficticio.",
     [{"op":"interact","method":"teletransportar","item":"$obra","quantity":2}],
     fixture=("equipo","plataforma"), expected="fallo")
case("modify", "05", "Reforzar construcción",
     "Aumenta revisión; consume piezas concretas.",
     [{"op":"modify","item":"$obra","mode":"add","materials":["madera"]}],
     fixture=("equipo","plataforma"))
case("dismantle", "05", "Desmontar construcción",
     "La obra se elimina con recuperación física, no gratuita.",
     [{"op":"dismantle","item":"$obra","all":True}],
     fixture=("equipo","plataforma"))
case("assemble", "05", "Ensamblar mecanismo",
     "Construye piezas y uniones, sin acreditar eficacia no ensayada.",
     [{"op":"assemble","name":"mecanismo laboratorio","purpose":"transmisión",
       "parts":[{"name":"eje","material":"madera","shape":"eje"},
                {"name":"rueda","material":"madera","shape":"rueda"}],
       "joints":[{"a":0,"b":1,"type":"articulada"}]}], fixture=("equipo",))
case("design", "06", "Documentar un diseño",
     "Crear una ficha no fabrica un prototipo.",
     [{"op":"design","name":"punta diseñada","purpose":"perforar roca","principle":"dureza",
       "requirements":"madera y mineral oscuro","procedure":"unir punta y mango",
       "prediction":"debería fracturar roca",
       "components":[{"name":"cabeza","material":"mineral oscuro","function":"perforar","connection":"fija"}]}])
case("propose", "06", "Proponer física adicional",
     "Registrar propuesta no habilita una capacidad del mundo.",
     [{"op":"propose","phenomenon":"viscosidad","missing_capability":"fluir",
       "rationale":"un ensayo no está modelado","experiment":"comparar flujos"}])
case("report-issue", "06", "Informar anomalía",
     "El informe no confirma que exista un error.",
     [{"op":"report_issue","title":"Resultado inesperado","expected":"se desplaza",
       "observed":"no llegó","rationale":"revisar evidencia"}])
case("compare-without-data", "06", "Comparar sin ensayos",
     "Rechaza conclusiones no respaldadas por IDs verificables.",
     [{"op":"compare","topic":"dureza","evidence_ids":[],"metric":"dureza"}], expected="fallo")
case("conclude-without-data", "06", "Concluir sin ensayos",
     "No inventa una ley por petición de Nilo.",
     [{"op":"conclude","topic":"dureza","evidence_ids":[]}], expected="fallo")
case("plan-gather-craft", "07", "Plan: recolectar y fabricar",
     "Valida recursos proyectados y verifica consumo real tras la recolección.",
     [{"op":"gather","target":"madera"},
      {"op":"craft","name":"martillo improvisado","purpose":"golpear",
       "form":"golpe","materials":["madera","madera"]}], fixture=("arbol_cerca",))
case("plan-craft-excavate", "07", "Plan: fabricar y excavar",
     "Una herramienta creada en el mismo plan puede habilitar la excavación posterior.",
     [{"op":"craft","name":"punta planificada","form":"punta",
       "purpose":"excavar","materials":["mineral oscuro","madera"]},
      {"op":"excavate"}], fixture=("equipo","roca_cerca"))
case("plan-build-use", "07", "Plan: construir y probar carga",
     "Expone una limitación: una obra recién creada puede requerir su ID en una deliberación posterior.",
     [{"op":"build","name":"soporte ciclo","purpose":"carga","materials":["madera","madera"],
       "geometry":{"shape":"plataforma","size":2}},
      {"op":"interact","method":"probar_carga","item":"soporte ciclo","material":"piedra","quantity":2}],
     fixture=("equipo",))
case("plan-rejected-step", "07", "Plan: paso imposible y paso válido",
     "El validador retira el paso inviable, pero conserva uno independiente.",
     [{"op":"go","x":35,"y":16},{"op":"inspect","x":15,"y":10}], expected="accion")
case("plan-with-project", "07", "Proyecto con pasos y verificación",
     "Comprueba apertura de proyecto, avance, registro y continuidad para deliberaciones siguientes.",
     [{"op":"experiment","target":"piedra","method":"golpear"},
      {"op":"build","name":"mesa experimental","purpose":"ensayo","materials":["madera","madera"]}],
     fixture=("equipo",), mode="nuevo")
case("plan-build-then-load", "07", "Dos decisiones: construir y después probar la obra por ID",
     "El segundo ciclo conoce el identificador generado en el primer ciclo.",
     [{"op":"build","name":"plataforma de dos etapas","purpose":"carga",
       "materials":["madera","madera"],"geometry":{"shape":"plataforma","size":2}}],
     fixture=("equipo",), deliberations=[
        {"plan":[{"op":"build","name":"plataforma de dos etapas","purpose":"carga",
                  "materials":["madera","madera"],"geometry":{"shape":"plataforma","size":2}}],
         "accion_proyecto":"sin_proyecto"},
        {"plan":[{"op":"interact","method":"probar_carga","item":"$obra",
                  "material":"piedra","quantity":2}],
         "accion_proyecto":"sin_proyecto"}])
case("plan-load-cycle", "07", "Plan de ensayo, depósito y recuperación",
     "Ensaya capacidad y verifica que recuperar restituye el inventario.",
     [{"op":"interact","method":"probar_carga","item":"$obra","material":"piedra","quantity":2},
      {"op":"interact","method":"depositar_carga","item":"$obra","material":"piedra","quantity":2},
      {"op":"interact","method":"recuperar_carga","item":"$obra","material":"piedra","quantity":2}],
     fixture=("equipo","plataforma"))
case("plan-compare-results", "07", "Dos decisiones: medir materiales y compararlos",
     "Primero se obtienen IDs de dos mediciones; después la segunda deliberación los consulta para comparar.",
     [{"op":"experiment","target":"piedra","method":"golpear"},
      {"op":"experiment","target":"madera","method":"golpear"}], fixture=("equipo",),
     deliberations=[
      {"plan":[{"op":"experiment","target":"piedra","method":"golpear"},
               {"op":"experiment","target":"madera","method":"golpear"}],
       "accion_proyecto":"sin_proyecto"},
      {"plan":[{"op":"compare","topic":"dureza comparada","metric":"dureza",
                "evidence_ids":["$med-2","$med-1"]}],
       "accion_proyecto":"sin_proyecto"}])
case("plan-go-then-inspect", "07", "Plan: ir a un lugar e inspeccionarlo",
     "Dos operaciones enlazadas: el segundo paso usa la nueva posición.",
     [{"op":"go","x":16,"y":10},{"op":"inspect","x":16,"y":10}],
     fixture=("paso_libre",))
case("plan-reconsider", "08", "Repetir una exploración agotada",
     "Muestra si el contador de no-progreso y el proyecto se actualizan tras fallos.",
     [{"op":"explore"}], fixture=("superficie_revelada",), mode="nuevo",
     expected="fallo",
     deliberations=[{"plan":[{"op":"explore"}],"accion_proyecto":"nuevo"},
                    {"plan":[{"op":"explore"}],"accion_proyecto":"continuar"},
                    {"plan":[{"op":"explore"}],"accion_proyecto":"continuar"},
                    {"plan":[{"op":"explore"}],"accion_proyecto":"continuar"}])
case("plan-no-project", "08", "Acciones sin proyecto artificial",
     "El personaje puede realizar actividades cotidianas sin registrar investigación.",
     [{"op":"eat"},{"op":"rest","minutes":30}], fixture=("equipo",))
case("plan-invalid-action", "08", "Operación desconocida en respuesta LLM",
     "La normalización debe rechazar un plan compuesto únicamente por órdenes inexistentes.",
     [{"op":"crear_oro"}], expected="rechazo")
case("plan-collapse", "08", "Colapso durante trabajo extenso",
     "El motor interrumpe una tarea prolongada por agotamiento extremo.",
     [{"op":"build","name":"gran mesa","materials":["madera","madera"]}],
     fixture=("equipo","energia_critica"), mode="nuevo", expected="interrupcion")
case("plan-paused", "08", "Pausar proyecto",
     "Dos deliberaciones: abrir proyecto y después pausarlo sin declararlo concluido.",
     [{"op":"inspect","x":15,"y":10}], mode="nuevo",
     deliberations=[{"plan":[{"op":"inspect","x":15,"y":10}],"accion_proyecto":"nuevo"},
                    {"plan":[],"accion_proyecto":"pausar"}])
case("plan-close-unproven", "08", "Cerrar proyecto sin pruebas",
     "El motor debe rechazar una conclusión física no demostrada.",
     [{"op":"inspect","x":15,"y":10}], mode="nuevo",
     deliberations=[{"plan":[{"op":"inspect","x":15,"y":10}],"accion_proyecto":"nuevo"},
                    {"plan":[],"accion_proyecto":"completar","prueba_cierre":"sin evidencia"}])

INDEX = {c["id"]: c for c in CASES}
if len(INDEX) != len(CASES):
    raise AssertionError("ID de escenario duplicado")
if not set(c["group"] for c in CASES).issubset(set(x for x,_ in GROUPS)):
    raise AssertionError("Grupo de escenario no definido")

def brief_state(s):
    p=s["person"];w=s["world"]
    return {
        "posicion": list(p["pos"]), "minuto": round(p["clock_minutes"],3),
        "inventario": copy.deepcopy(p["inventory"]),
        "necesidades": copy.deepcopy(p.get("needs",{})),
        "casillas_conocidas": len(w.get("revealed",[])),
        "construcciones": len(w.get("structures",[])),
        "herramientas": len(p.get("items",[])),
        "conocimientos": len(p.get("knowledge",{})),
        "mediciones": len(p.get("measurements",[])),
        "disenos": len(p.get("designs",[])),
        "propuestas": len(p.get("proposals",[])),
        "acciones_documentadas": len(p.get("action_outcomes",[])),
        "proyectos_historicos": len(p.get("projects",[])),
        "proyecto_actual": (p.get("project") or {}).get("title"),
        "contador_estancamiento": (p.get("project") or {}).get("no_progress_steps",0),
        "inconsciente": bool(p.get("unconscious")),
        "experiencias": len(p.get("experiences",[])),
        "revisar_estrategia": bool(p.get("strategy_review")),
        "resultados_estrategia": len(p.get("strategy_attempts",[])),
    }

def change(before,after):
    out={}
    for k in ("minuto","casillas_conocidas","construcciones","herramientas","conocimientos",
              "mediciones","proyectos_historicos","contador_estancamiento","experiencias","resultados_estrategia",
              "disenos","propuestas","acciones_documentadas"):
        a,b=before.get(k),after.get(k)
        if a!=b:out[k]={"antes":a,"despues":b,"delta":round(b-a,3)}
    for k in ("posicion","proyecto_actual","inconsciente"):
        if before.get(k)!=after.get(k):out[k]={"antes":before.get(k),"despues":after.get(k)}
    for domain in ("inventario","necesidades"):
        a=before.get(domain,{}) or {};b=after.get(domain,{}) or {}
        changed={}
        for key in sorted(set(a)|set(b)):
            if isinstance(a.get(key,0),(int,float)) and isinstance(b.get(key,0),(int,float)):
                d=round(b.get(key,0)-a.get(key,0),3)
                if d:changed[key]=d
        if changed:out[domain+"_delta"]=changed
    return out

class Trace:
    """Traza cronológica acotada; captura líneas realmente ejecutadas."""
    def __init__(self,max_calls=130):
        self.calls=[];self.max_calls=max_calls;self.previous=None;self.frames={}
    def hook(self,frame,event,arg):
        path=Path(frame.f_code.co_filename)
        name=frame.f_code.co_name
        try:
            relative=path.relative_to(ROOT).as_posix()
        except ValueError:
            return None
        if relative not in WATCH or name not in WATCH[relative]:
            return None
        if event=="call":
            if len(self.calls)>=self.max_calls:
                return None
            row={"archivo":relative,"funcion":name,
                 "explicacion":EXPLAIN.get(name,name.replace("_"," ")),
                 "inicio":frame.f_code.co_firstlineno+1,"fin":frame.f_code.co_firstlineno+1,
                 "lineas":set(),"repeticiones":1}
            self.calls.append(row)
            self.frames[id(frame)]=row
            return self.hook
        row=self.frames.get(id(frame))
        if row is not None and event=="line":
            row["lineas"].add(frame.f_lineno)
        elif row is not None and event in ("return","exception"):
            self.frames.pop(id(frame),None)
        return self.hook
    def __enter__(self):
        self.previous=sys.gettrace();sys.settrace(self.hook);return self
    def __exit__(self,*_):
        sys.settrace(self.previous)
    def serial(self):
        rows=[]
        for item in self.calls:
            loc=sorted(item["lineas"])
            if not loc:continue
            row={k:v for k,v in item.items() if k!="lineas"}
            row["inicio"],row["fin"]=loc[0],loc[-1]
            row["codigo"]=[{"linea":n,"texto":linecache.getline(str(ROOT/item["archivo"]),n).rstrip("\n")}
                           for n in loc[:14]]
            row["lineas_ejecutadas"]=len(loc)
            row["mas_lineas"]=len(loc)>14
            rows.append(row)
        # Consecutivas repetidas de la misma función: no ocultar el orden global.
        compact=[]
        for row in rows:
            if compact and (compact[-1]["archivo"],compact[-1]["funcion"]) == (row["archivo"],row["funcion"]):
                compact[-1]["repeticiones"]+=1
                compact[-1]["fin"]=max(compact[-1]["fin"],row["fin"])
            else:compact.append(row)
        return compact[:85]

def fixture(sim, tags):
    w=sim.s["world"];p=sim.s["person"]
    notes=[]
    if "equipo" in tags:
        for mat,count in (("madera",16),("piedra",16),("mineral oscuro",8),("fibra",8),
                          ("arcilla",8),("alimento",6)):
            p["inventory"][mat]=max(p["inventory"].get(mat,0),count)
        notes.append("Inventario de prueba aportado antes de empezar")
    if "sin_equipo" in tags:
        p["inventory"]={}
        notes.append("Inventario vacío como condición inicial")
    if "paso_libre" in tags:
        set_tile(w,16,10,0,"=");reveal(w,15,10,0,2)
        notes.append("Casilla vecina transitable y conocida")
    if "roca_cerca" in tags or "piedra_agotada" in tags:
        set_tile(w,16,10,0,"^");reveal(w,15,10,0,2)
        w["deposits"][tile_key(16,10,0)]=5
        notes.append("Roca visible a una casilla, con depósito de cinco unidades")
    if "arbol_cerca" in tags:
        set_tile(w,16,10,0,"T");w["deposits"][tile_key(16,10,0)]=5
        reveal(w,15,10,0,2)
        notes.append("Árbol próximo con recursos")
    if "agua_cerca" in tags:
        set_tile(w,16,10,0,"~");reveal(w,15,10,0,2)
        notes.append("Orilla visible a una casilla")
    if "roca_lejana" in tags:
        from world import PASSABLE
        for key in list(w.get("deposits",{})):
            x,y,z=map(int,key.split(","))
            if z==0 and tile(w,x,y,z) in "^or":w["deposits"][key]=0
        for x in (16,17,18,19):set_tile(w,x,10,0,"=")
        set_tile(w,20,10,0,"^");w["deposits"][tile_key(20,10,0)]=5
        for x in (16,17,18,19,20):reveal(w,x,10,0,1)
        notes.append("Corredor revelado hasta roca lejana; otras fuentes de piedra agotadas")
    if "piedra_agotada" in tags:
        for key in list(w.get("deposits",{})):
            x,y,z=map(int,key.split(","))
            if z==0 and tile(w,x,y,z) in "^or":w["deposits"][key]=0
        notes.append("Todas las fuentes de piedra conocidas marcadas agotadas")
    if "superficie_revelada" in tags:
        from world import W,H
        w["revealed"]=[tile_key(x,y,0) for y in range(H) for x in range(W)]
        notes.append("Toda la superficie marcada descubierta como condición de ensayo")
    if "entrada_cueva" in tags or "salida_cueva" in tags:
        p["pos"]=[23,7,-1 if "salida_cueva" in tags else 0]
        reveal(w,23,7,p["pos"][2],2)
        notes.append("Personaje ubicado en portal real entre niveles")
    if "agotado" in tags:
        p.setdefault("needs",{})["energia"]=19
        notes.append("Energía artificialmente baja para ensayar fatiga")
    if "energia_critica" in tags:
        p.setdefault("needs",{})["energia"]=5.2
        notes.append("Energía cercana al umbral de colapso")
    if "plataforma" in tags:
        from world import execute_action
        for mat,amount in (("madera",10),("piedra",10)):
            p["inventory"][mat]=max(p["inventory"].get(mat,0),amount)
        duration,facts,ok,_=execute_action(w,p,{"op":"build","name":"plataforma-fixture",
            "purpose":"ensayar", "materials":["madera","madera"],
            "geometry":{"shape":"plataforma","size":2}},sim.rng)
        if not ok:raise ValueError("No se pudo preparar plataforma con leyes reales: "+";".join(facts))
        notes.append("Plataforma construida con execute_action antes del caso")
    if "recipiente" in tags or "dos_recipientes" in tags:
        from world import execute_action
        for mat in ("piedra","madera"):
            p["inventory"][mat]=max(8,p["inventory"].get(mat,0))
        number=2 if "dos_recipientes" in tags else 1
        for i in range(number):
            _,facts,ok,_=execute_action(w,p,{
                "op":"craft","name":"vaso-fixture-"+str(i+1),
                "form":"recipiente","purpose":"contener agua y sólidos",
                "materials":["piedra","piedra"],
                "geometry":{"shape":"hueco","size":2}},sim.rng)
            if not ok:raise ValueError("Recipiente imposible: "+"; ".join(facts))
        notes.append(str(number)+" recipientes fabricados con física real antes del caso")
    if "pico" in tags:
        from world import execute_action
        p["inventory"]["madera"]=max(3,p["inventory"].get("madera",0))
        p["inventory"]["mineral oscuro"]=max(3,p["inventory"].get("mineral oscuro",0))
        _,facts,ok,_=execute_action(w,p,{"op":"craft","name":"punta-fixture",
            "form":"punta","purpose":"excavar",
            "materials":["madera","mineral oscuro"]},sim.rng)
        if not ok:raise ValueError("No se pudo fabricar punta de ensayo: "+";".join(facts))
        notes.append("Herramienta de punta fabricada con física real antes del caso")
    sim.write()
    return notes

def resolve(value, sim):
    if isinstance(value,str) and value in ("$med-1","$med-2"):
        items=sim.s["person"].get("measurements",[])
        idx=-1 if value=="$med-1" else -2
        if len(items)<abs(idx):raise ValueError("Faltan mediciones reales para "+value)
        return items[idx]["id"]
    if isinstance(value,str) and value in ("$vaso1","$vaso2"):
        tools=sim.s["person"].get("items",[])
        idx=(-2 if value=="$vaso1" and len(tools)>=2 else -1)
        if not tools:raise ValueError("No hay recipiente preparado")
        return tools[idx]["id"]
    if isinstance(value,str) and value=="$obra":
        objects=sim.s["world"].get("structures",[])
        if not objects:raise ValueError("Escenario no tiene obra preparada")
        return objects[-1]["id"]
    if isinstance(value,str) and value=="$herramienta":
        tools=sim.s["person"].get("items",[])
        if not tools:raise ValueError("Escenario no tiene herramienta preparada")
        return tools[-1]["id"]
    if isinstance(value,dict):return {k:resolve(v,sim) for k,v in value.items()}
    if isinstance(value,list):return [resolve(v,sim) for v in value]
    return value

def decision_for(spec, source):
    return {"cuaderno":"Ensayo técnico de escenario controlado; no es una decisión de un LLM.",
            "objetivo":spec["title"],"motivo":"Prueba reproducible", "plan":source["plan"],
            "accion_proyecto":source.get("accion_proyecto",spec["mode"]),
            "avance_estimado":0,"revisar_en_minutos":90,"estado_actual":"Evaluando condición física",
            "prueba_cierre":source.get("prueba_cierre","")}

def diagnostics_since(sim, seq):
    rows=sim.conn.execute(
        "SELECT seq,payload FROM history WHERE category='diagnostic' AND seq>? ORDER BY seq ASC",
        (seq,)).fetchall()
    return [{"seq":key,**json.loads(payload)} for key,payload in rows]

def last_seq(sim):
    row=sim.conn.execute("SELECT COALESCE(MAX(seq),0) FROM history").fetchone()
    return int(row[0])


def cognitive_preview(sim):
    from laboratorio_contexto import vista_de_contexto
    return vista_de_contexto(sim)


def run(spec_id, *, seed=None, custom_spec=None):
    spec=custom_spec if custom_spec is not None else INDEX.get(spec_id)
    if spec is None:raise ValueError("No existe el escenario "+str(spec_id))
    if seed is None:seed=spec["seed"]
    if type(seed) is not int or seed<0 or seed>1000000000:
        raise ValueError("Semilla fuera de rango")
    with tempfile.TemporaryDirectory(prefix="nilo-lab-") as dirname:
        sim=Simulation(db_path=Path(dirname)/"escenario.sqlite3",world_seed=seed,rng_seed=9821)
        sim.think=lambda: None  # No se llama a la API; el usuario sustituye la decisión.
        sim.s["speed"]=60
        sim.s["paused"]=False
        sim.s["mode"]="demo"
        stages=[]
        prepared=fixture(sim,spec["fixture"])
        initial=brief_state(sim.s)
        pre_context=cognitive_preview(sim)
        all_decisions=spec["deliberations"] or [{"plan":spec["plan"]}]
        for index,proto in enumerate(all_decisions):
            incoming=decision_for(spec,{**proto,"plan":resolve(proto["plan"],sim)})
            with Trace() as t:
                try:
                    normalized=normalize_decision(incoming)
                except Exception as exc:
                    stages.append({"tipo":"normalizacion","titulo":"Entrada del modelo rechazada",
                                   "descripcion":str(exc),"entrada":incoming,"codigo":t.serial(),
                                   "estado":"rechazado"})
                    break
            stages.append({"tipo":"normalizacion","titulo":"Normalizar decisión "+str(index+1),
                           "descripcion":"Operaciones reconocidas: "+str(len(normalized["plan"])),
                           "entrada":incoming,"salida":normalized,"codigo":t.serial(),"estado":"observado"})
            old=brief_state(sim.s)
            seq=last_seq(sim)
            with Trace() as t:
                # El contenido es sintético, pero recorre la misma rama fuente=="llm"
                # de preferencias, agenda, memoria y proyectos, sin consultar redes.
                sim.plan_ready(normalized,"llm",{})
            accepted=copy.deepcopy(sim.s["person"].get("plan",[]))
            stages.append({"tipo":"plan","titulo":"Validar y preparar plan",
                           "descripcion":str(len(accepted))+" de "+str(len(normalized["plan"]))+
                           " acciones permanecen en el plan",
                           "aceptadas":accepted,"rechazadas":len(normalized["plan"])-len(accepted),
                           "analitica":change(old,brief_state(sim.s)),
                           "codigo":t.serial(),"estado":"observado"})
            consumed=0
            while (sim.s["person"].get("pending") or sim.s["person"].get("plan")) and consumed<500:
                before=brief_state(sim.s)
                before_seq=last_seq(sim)
                pending_before=sim.s["person"].get("pending")
                selected=(pending_before or {}).get("step") or (
                    sim.s["person"].get("plan") or [{}])[0]
                previous_measures=len(sim.s["person"].get("measurements",[]))
                previous_events=len(sim.s.get("events",[]))
                # Avance por ticks reales. 3 s de reloj a ×60 = aprox. 3 min del mundo.
                with Trace(max_calls=120) as t:
                    for inner in range(120):
                        sim.tick(3.0)
                        consumed+=1
                        if len(sim.s["person"].get("measurements",[])) > previous_measures:
                            break
                        if not sim.s["person"].get("pending") and not sim.s["person"].get("plan"):
                            break
                        if consumed>=500:break
                diag=diagnostics_since(sim,before_seq)
                new_events=sim.s.get("events",[])[previous_events:]
                meas=sim.s["person"].get("measurements",[])
                stages.append({"tipo":"ejecucion","titulo":"Ejecutar "+str(selected.get("op","paso")),
                               "operacion":selected.get("op"),
                               "descripcion":str(len(diag))+" resultados tipados en "+str(inner+1)+" ticks",
                               "analitica":change(before,brief_state(sim.s)),
                               "diagnosticos":diag[-8:],
                               "hechos":[{"tipo":e.get("kind"),"texto":e.get("text")}
                                        for e in new_events[-12:]],
                               "ultima_medicion":meas[-1] if meas and len(meas)>previous_measures else None,
                               "codigo":t.serial(),
                               "estado":"observado" if diag else "en_progreso"})
                if sim.s["person"].get("unconscious"):
                    stages.append({"tipo":"interrupcion","titulo":"Interrupción fisiológica",
                                   "descripcion":"El motor suspendió la actividad por pérdida de conciencia",
                                   "analitica":change(before,brief_state(sim.s)),"estado":"observado"})
                    break
                # Ninguna deliberación adicional, pero tareas motoras autorizadas pueden
                # continuar. No inventar una decisión para completar el ciclo.
            if consumed>=500:
                stages.append({"tipo":"limite","titulo":"Límite de ejecución del ensayo",
                               "descripcion":"500 ticks consumidos; el escenario quedó incompleto",
                               "estado":"incompleto"})
                break
            if sim.s["person"].get("unconscious"):break
        sim.write()
        final=brief_state(sim.s)
        post_context=cognitive_preview(sim)
        diags=diagnostics_since(sim,0)
        statuses=Counter(d.get("evaluation_status") or d.get("action_result",{}).get("status") or
                         d.get("contract_status") for d in diags)
        accepted_actions=[d.get("action_result",{}) for d in diags if isinstance(d.get("action_result"),dict)]
        doc_change=final.get("disenos",0)>initial.get("disenos",0) or (
            final.get("propuestas",0)>initial.get("propuestas",0))
        has_success=any(x.get("success") is True for x in accepted_actions) or doc_change
        has_failure=any(x.get("success") is False for x in accepted_actions)
        was_rejected=any(x.get("estado")=="rechazado" or x.get("rechazadas",0)>0 for x in stages)
        was_interrupted=any(x.get("tipo")=="interrupcion" for x in stages)
        expected=spec["expected"]
        matched=(
            (expected=="accion" and has_success) or
            (expected=="rechazo" and was_rejected) or
            (expected=="fallo" and (has_failure or was_rejected)) or
            (expected=="interrupcion" and was_interrupted)
        )
        result={
            "version":(ROOT/"VERSION").read_text(encoding="utf-8").strip(),
            "id":spec["id"],"titulo":spec["title"],"grupo":spec["group"],
            "descripcion":spec["description"],"objetivo_esperado":spec["expected"],"cumple_expectativa":matched,
            "evaluacion":"confirmado" if matched else "revisar: resultado o fixture no cumple lo esperado",
            "preparacion":prepared,"semilla":seed,
            "inicio":initial,"final":final,"cambios":change(initial,final),
            "contexto_inicial":pre_context,"contexto_final":post_context,
            "pasos":stages,"diagnosticos_totales":len(diags),"estados":dict(statuses),
            "tiempo_simulado":round(final["minuto"]-initial["minuto"],3),
            "advertencia":"Decisiones prefijadas en el escenario, no respuestas de Gemini/Groq.",
            "reproduccion":"SQLite temporal, mundo independiente; planificación y ticks de Simulation reales.",
        }
        sim.conn.close()
        return result

def sandbox(steps, *, seed=7321, fixtures=(), mode='sin_proyecto'):
    from action_contracts import SUPPORTED_OPERATIONS
    if not isinstance(steps,list) or not 1<=len(steps)<=12:
        raise ValueError('El plan debe tener entre 1 y 12 acciones')
    if any(not isinstance(s,dict) or s.get('op') not in SUPPORTED_OPERATIONS for s in steps):
        raise ValueError('Operación desconocida en el sandbox')
    if not isinstance(fixtures,list) or len(fixtures)>8 or any(v not in (
        'equipo','sin_equipo','paso_libre','roca_cerca','arbol_cerca','agua_cerca',
        'roca_lejana','piedra_agotada','superficie_revelada','entrada_cueva',
        'salida_cueva','agotado','energia_critica','plataforma','pico',
        'recipiente','dos_recipientes') for v in fixtures):
        raise ValueError('Fixture de sandbox no permitido')
    if mode not in ('nuevo','sin_proyecto','continuar'):
        raise ValueError('Modo de proyecto no permitido')
    spec={'id':'sandbox','title':'Ensayo manual','group':'sandbox',
          'description':'Plan aportado por el observador a través de botones',
          'plan':steps,'fixture':fixtures,'seed':seed,'mode':mode,'expected':'accion',
          'deliberations':None}
    return run('sandbox',seed=seed,custom_spec=spec)

def catalog():
    ops=sorted(ACTION_GUIDE)
    covered=sorted({op for spec in CASES for d in (spec["deliberations"] or [{"plan":spec["plan"]}])
                    for st in d["plan"] for op in [st.get("op")] if op in ACTION_GUIDE})
    return {
        "grupos":[{"id":i,"nombre":title,"cantidad":sum(s["group"]==i for s in CASES)}
                  for i,title in GROUPS],
        "casos":copy.deepcopy(CASES),
        "operaciones":ops,"operaciones_con_escenario":covered,
        "sin_escenario":sorted(set(ops)-set(covered)),
        "total":len(CASES),
        "limite":"Se cubren ramas representativas, no todas las combinaciones infinitas de mundo y parámetros.",
    }

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--id",default="go-coord")
    parser.add_argument("--all",action="store_true")
    args=parser.parse_args()
    if args.all:
        report=[]
        for spec in CASES:
            try:
                x=run(spec["id"])
                report.append({"id":spec["id"],"etapas":len(x["pasos"]),
                               "diagnosticos":x["diagnosticos_totales"],"estados":x["estados"]})
            except Exception as exc:
                report.append({"id":spec["id"],"error":type(exc).__name__+":"+str(exc)})
        print(json.dumps(report,ensure_ascii=False,indent=2))
    else:print(json.dumps(run(args.id),ensure_ascii=False,indent=2))
