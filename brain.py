"""Deliberación LLM intercambiable: Gemini API, OpenAI-compatible, demo explícita."""
from __future__ import annotations
import json, os, urllib.request, urllib.error, re, random
from pathlib import Path
from behavior import behavior_summary
from nilo_runtime.cognition.memory import recall_relevant
from nilo_runtime.cognition.evidence import projected_conclusions, projected_research, projected_knowledge
from world import world_view, tile, tile_key, valid, DIRS, item_effects, pathfind, reachable_shores
from providers import configured, error_from_http
from physics import human_knowledge
from nilo_runtime.perception.island import adjacent_terrain, visible_structures
from habits import ensure_habits
from construction import ensure_object
from experiment_log import closure_status
from world import cave_exit, known_exit_route, gather_material
from research_cycle import normalize_prediction, recent_predictions
from action_contracts import instructions as action_instructions, summary as contract_summary, SUPPORTED_OPERATIONS
from nilo_runtime.core.operations import registered_operations, validate_operation
from diagnostic_support import human_review_feedback

ROOT=Path(__file__).resolve().parent
ACTIONS=action_instructions()

from nilo_runtime.agent.prompts import SYSTEM, CHAT_SYSTEM
from nilo_runtime.agent.budget import compact_context, _cognitive_needs_context
from nilo_runtime.agent.responses import parse_json, normalize_decision
from nilo_runtime.agent.gateway import build_deliberation_request, request_llm, request_chat

def config():
    vals={"PROVIDER":"gemini", "MODEL":"gemini-3.1-flash-lite", "MAX_LLM_CALLS_PER_DAY":"100", "MAX_CHAT_CALLS_PER_DAY":"40", "MIN_REAL_SECONDS_BETWEEN_CALLS":"15", "PORT":"8765", "BACKUP_PROVIDER":"groq", "GROQ_MODEL":"openai/gpt-oss-20b", "GEMINI_FALLBACK_MODELS":"gemini-3.5-flash-lite,gemini-3.8-flash"}
    env_path=ROOT/'config.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8-sig').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:continue
            k,v=line.split('=',1);vals[k.strip()]=v.strip().strip('"').strip("'")
    from nilo_runtime.core.lab_settings import config_overlay
    vals.update(config_overlay(ROOT))
    vals.update({key:value for key,value in os.environ.items() if key in {"PROVIDER","MODEL","GEMINI_API_KEY","GEMINI_FALLBACK_MODELS","OPENAI_API_KEY","OPENAI_BASE_URL","GROQ_API_KEY","GROQ_MODEL","BACKUP_PROVIDER","MAX_LLM_CALLS_PER_DAY","MAX_CHAT_CALLS_PER_DAY","MIN_REAL_SECONDS_BETWEEN_CALLS","PORT"}})
    return vals


def available(cfg):
    return configured(cfg)


def known_site_routes(w, p):
    """Lugares ya observados y accesibilidad con el mapa revelado.

    Una ruta ausente significa que no hay conexión CONOCIDA, no que un
    obstáculo físico definitivo impida llegar. Nunca revela sitios ocultos.
    """
    position=p['pos']
    known=set(w.get('revealed',[]))
    results=[]
    for name, site in w.get('sites',{}).items():
        try:
            x,y,z=int(site['x']),int(site['y']),int(site['z'])
        except (TypeError,ValueError,KeyError):
            continue
        if f"{x},{y},{z}" not in known:
            continue
        if z!=position[2]:
            status="otro_nivel"
            distance=None
        elif (x,y)==tuple(position[:2]):
            status="en_destino"
            distance=0
        else:
            route=pathfind(w,tuple(position),(x,y,z),known_only=True)
            status="ruta_conocida" if route else "sin_ruta_conocida"
            distance=len(route) if route else None
        results.append({"nombre":name,"posicion":[x,y,z],
                        "acceso":status,"tramos_conocidos":distance})
    return results


def context_for(w,p,recent,now,scenario=None):
    # Memoria seleccionada, evitando enviar a la API el historial completo en cada llamada.
    current=p.get('project')
    current_context=None
    if current:
        current_context={k:v for k,v in current.items() if k not in ('verified_results',)}
        current_context['verified_results']=current.get('verified_results',[])[-6:]
    past=[]
    for pr in p.get('projects',[])[-6:]:
        past.append({k:pr.get(k) for k in
                     ('id','title','status','reason','state','updated','closure_reason')})
    # Los proyectos pausados importan incluso sin recordatorios. La mera
    # similitud temática es contexto, no una orden ni una equivalencia causal.
    from cognition import terms as research_terms
    # Al pausar, project pasa a None: la siguiente deliberación también debe
    # recibir el motivo de la pausa, sin convertirlo en un objetivo nuevo.
    anchor=current or next((old for old in reversed(p.get('projects',[]))
                            if old.get('status')=='pausado'),None)
    interest=research_terms(' '.join(str(anchor.get(k) or '') for k in
                                     ('title','reason','state'))) if anchor else set()
    related_projects=[]
    if interest:
        for earlier in reversed(p.get('projects',[])):
            if earlier.get('status') not in ('pausado','abandonado','terminado'):
                continue
            overlap=interest & research_terms(' '.join(str(earlier.get(k) or '')
                                                for k in ('title','reason','state')))
            if len(overlap)<2:
                continue
            related_projects.append({
                'id':earlier.get('id'),'titulo':earlier.get('title'),
                'estado':earlier.get('status'),
                'motivo_de_pausa_o_cierre':earlier.get('closure_reason'),
                'ultimo_estado':earlier.get('state'),
                'acciones_sin_avance':earlier.get('no_progress_steps',0)})
            if len(related_projects)>=3:break
    related_research=[]
    if interest:
        for entry in reversed(p.get('research',[])):
            if entry.get('state') not in ('pausada','archivada_sin_resolver','archivada_con_proyecto'):
                continue
            overlap=interest & research_terms(entry.get('question','')+' '+entry.get('hypothesis',''))
            if len(overlap)<2:
                continue
            related_research.append({
                'id':entry.get('id'),'pregunta':entry.get('question'),
                'estado':entry.get('state'),
                'motivo_de_archivo':entry.get('project_retirement'),
                'evidencias_registradas':len(entry.get('evidence',[])),
                'reaperturas':len(entry.get('reaperturas',[]))})
            if len(related_research)>=3:break
    ready_ids={t.get('proyecto_id') for t in p.get('agenda',[])
               if t.get('modo')=='recordatorio'
               and t.get('estado')=='lista_para_revisar'
               and t.get('proyecto_id')}
    reanudables=[{
        'id':pr.get('id'),'titulo':pr.get('title'),
        'motivo_pausa':pr.get('closure_reason') or 'No registrado',
        'estado':pr.get('status'),
        'aviso_pendiente':True}
        for pr in p.get('projects',[]) if pr.get('status')=='pausado'
        and pr.get('id') in ready_ids][-4:]
    px,py,pz=p['pos']
    adjacent=adjacent_terrain(w,p)
    ready=[{"id":t.get('id'),"nombre":t.get('name'),"potencia_excavar":item_effects(t).get('excavar',0)}
           for t in p.get('items',[]) if t.get('durability',0)>0 and item_effects(t).get('excavar',0)>0]
    ex=cave_exit(w)
    exit_route=known_exit_route(w,p) if p['pos'][2]==-1 else None
    context={"salida_conocida":({"posicion_subsuelo":[*ex,-1],"ruta_conocida_en_tramos":len(exit_route) if exit_route is not None else None,"accion":"ascend"} if p['pos'][2]==-1 and tile_key(ex[0],ex[1],-1) in w.get('revealed',[]) else None),
            "fenomenos_no_evaluables_recientes":p.get('unmodeled_attempts',[])[-5:],
            "conocimiento_inicial":human_knowledge(p.get('knowledge_profile','contemporaneo')),
            "coordenadas_cardinales":{"norte":"Y decrece","sur":"Y crece","este":"X crece","oeste":"X decrece"},
            "necesidades":__import__('survival').perceived_needs(p),
            "preferencias_aprendidas":p.get('preferences',{}),
            "memoria_de_experiencias":p.get('experience_summary',[])[-16:],
            "historia_acumulada":{k:{"desde_dia":v.get("desde_dia"),"exitos":v.get("exitos"),"fallos":v.get("fallos"),"acciones":v.get("acciones"),"ultimos_hitos":v.get("hitos",[])[-3:]} for k,v in list(p.get("life_chapters",{}).items())[-8:]},
            "inventos_documentados":[{'id':d['id'],'nombre':d['name'],'estado':d['status'],'ultima_version':d['versions'][-1]['version'] if d['versions'] else 0,'ultima_prueba':d['tests'][-1] if d['tests'] else None} for d in p.get('designs',[])[-10:]],
            "evaluaciones_externas_recientes":human_review_feedback(p.get('proposals',[]),limit=4),
            "propuestas_pendientes":[{'id':r['id'],'tipo':r.get('type','physics'),
                'asunto':r.get('title') or r.get('phenomenon',''),
                'estado':r['status'],'review':r.get('review'),
                'origen':r.get('origin','nilo'),
                'ids_evidencia':(r.get('evidence_ids') or
                                 [a.get('id') for a in r.get('evidence',[]) if a.get('id')])[:8],
                'vinculo_evidencia':r.get('evidence_relation','legado_sin_clasificar')}
                for r in p.get('proposals',[])[-12:]],
            "resultados_de_acciones":[{'id':r['id'],'operacion':r['op'],'destino':r.get('target'),
                'resultado':r.get('facts',[])[:2], 'exito':r.get('success'), 'posicion':r.get('pos'),
                'estado_evaluacion':r.get('evaluation_status'),
                'evidencia_fisica':(r.get('action_result') or {}).get('physical'),
                'cambios_medidos':r.get('physical_result')}
                for r in p.get('action_outcomes',[])[-12:]],"momento":now,"posición":p['pos'],"mundo":"superficie" if p['pos'][2]==0 else 'cueva',
            "inventario_materiales":{k:v for k,v in p['inventory'].items() if v>0},
            "herramientas_que_llevo":[{"id":a['id'],"nombre":a['name'],"forma":a['form'],"version":a.get('revision',1),
               "piezas":[{"id":c.get('id'),"material":c.get('material'),"estado":c.get('condition',1)} for c in a.get('components',[])],
               "usos_por_verificar":a.get('possible_uses',{}),"durabilidad":a.get('durability',100),
               "pruebas":a.get('tests',[])[-3:],"pruebas_version_actual":[t for t in a.get('tests',[]) if t.get('revision',1)==a.get('revision',1)][-3:],"geometria":a.get('geometry'),"contenido":a.get('contents',{})} for a in p.get('items',[])[-12:]],
            "percepción_local":world_view(w,p),"adyacentes":adjacent,
             "diagnosticos_operativos_recientes":[
                {"id":r.get("id"),"operacion":r.get("op"),"estado":r.get("contract_status"),
                 "codigo":r.get("contract_code"),"esperado":r.get("contract_expected"),
                 "observado":r.get("contract_observed")}
                for r in p.get('action_outcomes',[])[-45:]
                if r.get("contract_status") in ("uso_incorrecto","limitacion","posible_error")][-8:],
            "orillas_agua_conocidas_alcanzables":[{"orilla":v["shore"],"agua":v["water"],"distancia_en_tramos":v["steps"]} for v in reachable_shores(w,p,max_results=5)],
            "herramientas_de_excavación":ready,
            "lugares_conocidos":[[name,site] for name,site in w['sites'].items() if f"{site['x']},{site['y']},{site['z']}" in w['revealed']][:10],
            "navegacion_a_lugares":known_site_routes(w,p),
            "construcciones_fijas":[{"id":v.get("id"),"nombre":v.get("name"),"categoria":v.get("category"),"posicion":v.get("pos"),
                "version":v.get("revision",1),"materiales":v.get("materials",[]),"condicion_abrigo":v.get("shelter_condition","no_aplica"),"diseño_id":v.get("design_id"),"piezas":[{"id":part.get("id"),"material":part.get("material"),"estado":part.get("condition",1)} for part in v.get("components",[])],
                "planta":v.get("space",{}),"estado":v.get("status"),
                "materiales_almacenados":v.get("cargas_almacenadas",{}),
                "ensayos_de_carga":[{"revision":t.get("revision"),"material":t.get("material"),
                    "quantity":t.get("quantity"),"supported":t.get("supported"),
                    "limit":t.get("limit"),"load":t.get("load")}
                    for t in v.get("ensayos_de_carga",[])[-2:]]} for v in visible_structures(w)[-12:]],
            # Lectura histórica: las entradas knowledge también pueden documentar
            # fallos; su procedencia se expone por separado sin acreditarlas.
            "experimentos_comprobados":list(p['knowledge'].values())[-18:],
            "conocimiento_con_procedencia":projected_knowledge(p,limit=12),
            "ensayos_recientes":p.get('observations',[])[-12:],
            "mediciones_reales_recientes":[{"id":m['id'],"op":m['op'],"duracion_min":m['duration_minutes'],
                  "condicion":m['condition'],"energia_inicial":m['start']['needs']['energia'],
                  "energia_final":m['end']['needs']['energia'],"energia_por_hora":m.get('energy_per_hour'),
                  "comparable":m.get('rest_comparable',False),
                  "fisica":m.get("physical"),"resultado":m.get("verified_facts",[])[:2]} for m in p.get('measurements',[])[-15:]],
            "conclusiones_verificadas":projected_conclusions(p,limit=15),
            
            "estrategias_que_ya_no_funcionaron":p.get('strategy_feedback',[])[-10:],
            "ultimo_cierre_rechazado":p.get('last_closure_rejection'),
            "acciones_sin_avance_reciente":current.get('no_progress_steps',0) if current else 0,
            "estancamiento_detectado":bool(current and current.get("reconsideration_required")),
            "revision_de_estrategia":p.get('strategy_review'),
            "siguiente_revision_objetivo_minuto":p.get('review_at_minutes'),
            "proyectos_anteriores":past,"proyectos_reanudables":reanudables,
            "antecedentes_relacionados":related_projects,
            "investigaciones_pausadas_relacionadas":related_research,
            "proyecto_actual":current_context,
            "investigaciones_activas":[r for r in projected_research(p,limit=25)
                if r.get("state")=="abierta"][-7:],
            "habilidades_verificadas":[{"id":k,"accion":v.get("op"),"objetivo":v.get("target"),"ensayos":v.get("count"),"hecho":v.get("last_fact")} for k,v in list(p.get("skills",{}).items())[-15:] if v.get("verified")],
            "preferencias_en_espera":p.get("waiting_preferences",[]),
            "agenda_diferida":[{k:v for k,v in t.items() if k not in ("resultados",)} for t in p.get("agenda",[]) if t.get("estado") in ("pendiente","en_curso","pospuesta")][-10:],
            "recordatorios_pendientes":[{"id":t.get("id"),"proyecto_id":t.get("proyecto_id"),
                "titulo":t.get("titulo"),"motivo":t.get("motivo"),"cuando":t.get("cuando")}
                for t in p.get("agenda",[]) if t.get("modo")=="recordatorio" and t.get("estado")=="pendiente"][-10:],
            "recordatorios_listos":[{"id":t.get("id"),"proyecto_id":t.get("proyecto_id"),
                "titulo":t.get("titulo"),"motivo":t.get("motivo"),"cuando":t.get("cuando"),
                "condicion_cumplida":t.get("condicion_cumplida")}
                for t in p.get("agenda",[]) if t.get("modo")=="recordatorio" and t.get("estado")=="lista_para_revisar"][-10:],
            "estrategia_bloqueada":(current.get("estrategia_bloqueada") if current else None),
            "repeticion_operativa_informativa":(current.get("repeticion_operativa") if current else None),
            "evidencia_de_progreso_ultima_accion":p.get('last_progress_evidence'),
            "pistas_cierre_proyecto":('Se ha bebido de agua real y descubierto una fuente; si el proyecto era localizar agua, revisá su cierre con evidencia.'
                if current and 'agua' in current.get('title','').casefold() and
                p.get('skills',{}).get('drink',{}).get('verified') and
                any(k.endswith(',0') and tile(w,*[int(q) for q in k.split(',')])=='~' for k in w.get('revealed',[]))
                else None),
            "costo_mantenimiento_reciente":__import__("motivation").maintenance_summary(p),
             "comportamiento_medido":behavior_summary(p),
            "ultima_actividad_en_espera":p.get("waiting_history",[])[-5:],
            "experiencias_recientes":recent[-18:],
            "predisposiciones":{"curiosidad":.78,"interés_por_experimentar":.66,"perseverancia":.57,"tolerancia_a_riesgo":.35},
            "situacion_inicial":("Acabo de llegar a un territorio desconocido. Antes de fabricar por rutina, conviene orientarme y reconocer vías de retorno; la incertidumbre no equivale a peligro verificado." if p["clock_minutes"]<1440 and not p.get("projects") else None),
            "territorio_descubierto_pct":round(100*sum(1 for k in w["revealed"] if str(k).endswith(",0"))/(37*21),1),
            "regla":"La verdad física proviene del motor. Para acceder al agua basta una orilla alcanzable: no se puede entrar caminando en casillas acuáticas. Arena y arboledas sí son transitables; las rocas no. No inventar obstáculos ni acceso por cueva. Excavar requiere punta. No repitas preguntas equivalentes."}

    # El descanso es una capacidad física general, no una investigación sugerida
    # por el motor. Su evaluación técnica sólo entra si Nilo abrió ese tema.
    active_text=' '.join([
        (current or {}).get('title',''),(current or {}).get('reason',''),
        str(p.get('active_research') or ''),
        *[r.get('question','') for r in p.get('research',[])
          if r.get('state')=='abierta'][-7:]
    ]).casefold()
    rest_relevant=any(word in active_text for word in
                      ('descans','repos','recuperaci','energía','energia','dormir','sueño'))
    # Una pregunta de investigación corporal elegida también constituye
    # voluntad de medir, aunque se formule como pregunta ("¿el refugio ayuda?").
    open_body_question=any(
        r.get('state')=='abierta' and any(word in
            (str(r.get('question',''))+' '+str(r.get('hypothesis',''))).casefold()
            for word in ('descans','repos','recuperaci','energía','energia',
                         'refugio','hidrataci','sed','beber','nutrici','alimentaci','hambre','comer'))
        for r in p.get('research',[]))
    research_intent=(open_body_question or any(word in active_text for word in
                      ('medir','medici','compar','experiment','ensay','cuantific','comprob','investig','estudi')))
    bodily_rest_study=rest_relevant and research_intent
    hydration_study=research_intent and any(word in active_text for word in
                                             ('hidrataci','sed','beber','bebida'))
    nutrition_study=research_intent and any(word in active_text for word in
                                            ('nutrici','alimentaci','hambre','comer','ingesta'))
    if bodily_rest_study:
        context["estado_investigacion_descanso"]=closure_status(p)
        recent_rests=[m for m in p.get('measurements',[])[-40:] if m.get('op')=='rest']
        context["condiciones_de_ensayo_descanso"]={
            "descansos_no_comparables_recientes":sum(not m.get('rest_comparable') for m in recent_rests),
            "aclaracion":"Solo el descanso voluntario recupera energía por descanso; wait deja pasar tiempo con metabolismo, sin recuperación de sueño. Para comparar descansos hacen falta ensayos no saturados en condiciones comparables.",
            "distincion":"Podés descansar por voluntad propia sin investigar. Los resultados experimentales se consultan por evidencia, no por conocer directamente las reservas."}
    # La telemetría del motor mide cada acción, pero Nilo solo conoce
    # cifras corporales de pruebas pasadas si está estudiando esa variable.
    for row,original in zip(context.get("mediciones_reales_recientes",[]),
                            p.get('measurements',[])[-15:]):
        if not bodily_rest_study:
            for field in ("energia_inicial","energia_final","energia_por_hora"):
                row.pop(field,None)
        if (hydration_study and original.get('op')=='drink'):
            start=(original.get('start') or {}).get('needs') or {}
            end=(original.get('end') or {}).get('needs') or {}
            if isinstance(start.get('hidratacion'),(int,float)) and isinstance(end.get('hidratacion'),(int,float)):
                row['hidratacion_inicial']=start['hidratacion']
                row['hidratacion_final']=end['hidratacion']
        if (nutrition_study and original.get('op')=='eat'):
            start=(original.get('start') or {}).get('needs') or {}
            end=(original.get('end') or {}).get('needs') or {}
            if isinstance(start.get('nutricion'),(int,float)) and isinstance(end.get('nutricion'),(int,float)):
                row['nutricion_inicial']=start['nutricion']
                row['nutricion_final']=end['nutricion']
    context["memorias_relevantes"]=recall_relevant(p,w,limit=6)
    from laboratory import comparison_candidates
    context["comparaciones_validas"]=[c for c in comparison_candidates(p,limit=6)
        if bodily_rest_study or c.get("tipo")!="descanso"][:5]
    # Registrar fenómenos faltantes por ensayos reales, no suponer que una
    # construcción completa carece de toda función por un método no evaluable.
    linked_ids={rid for proposal in p.get('proposals',[])
                for rid in proposal.get('evidence_ids',[]) if isinstance(rid,str)}
    context["fenomenos_pendientes_de_modelo"]=[
        {'id':r.get('id'),'fenomeno':r.get('phenomenon'),
         'metodo':r.get('method'),'limitacion':r.get('missing_capability')}
        for r in p.get('unmodeled_attempts',[])[-15:]
        if r.get('id') and r['id'] not in linked_ids][-4:]
    if scenario is not None:
        context["escenario_id"]=scenario.id
        context["entorno_id"]=scenario.environment_id
        # La descripción que el agente recibe depende del escenario activo.
        # Para partidas antiguas se mantiene literalmente el contexto previo.
        if p.get("clock_minutes",0)<1440 and not p.get("projects"):
            context["situacion_inicial"]=scenario.introduction
        else:
            context["situacion_inicial"]=None
        context["regla"]=scenario.world_rule
    if p.get("prediction_log"):
        context["predicciones_contrastadas"]=recent_predictions(p,5)
    discrepancies=gather_outcome_discrepancies(p)
    if discrepancies:
        context["inconsistencias_recoleccion_previas"]=discrepancies
    from diagnostic_guidance import review_recent_attempts
    context["revision_de_intentos_verificados"]=review_recent_attempts(p)
    return context


def gather_outcome_discrepancies(person,limit=6):
    """Comparar intención y variación REAL del inventario, incluidos runs anteriores.

    No identifica el origen físico cuando el registro antiguo no guardó el
    depósito preciso. Un resultado de madera no demuestra composición de
    un afloramiento mineral solicitado en esa operación.
    """
    anomalies=[]
    for result in person.get("action_outcomes",[]):
        if result.get("op")!="gather":continue
        target=str(result.get("target") or "")
        requested=gather_material(target)
        physical=result.get("physical_result") or {}
        diff=physical.get("inventory_delta") or {}
        gained={name:qty for name,qty in diff.items()
                if isinstance(qty,(int,float)) and not isinstance(qty,bool) and qty>0}
        if not requested:continue
        if gained and any(name!=requested for name in gained):
            anomalies.append({"action_id":result.get("id"),"solicitado":target,
                "material_previsto":requested,"material_obtenido":gained,
                "observacion":"La extracción histórica no corresponde a lo solicitado; "
                              "no atribuir ese material al depósito indicado."})
        elif not gained and result.get("success"):
            anomalies.append({"action_id":result.get("id"),"solicitado":target,
                "material_previsto":requested,"material_obtenido":{},
                "observacion":"La acción fue marcada exitosa, pero el inventario no aumentó; "
                              "pudo ser solo un acercamiento, no extracción comprobada."})
    return anomalies[-limit:]


def demo_decision(w,p):
    """Demostración sin IA: alterna observación, exploración y pruebas accesibles.
    No fija una misión inicial ni prioriza piedra o madera.
    """
    r=random.Random(int(p['clock_minutes'])+w['seed'])
    visible=world_view(w,p)
    resources={'arboleda':'madera','arenal':'arcilla','hierba':'fibra',
               'afloramiento mineral':'mineral oscuro','ruinas antiguas':'piedra',
               'roca':'piedra','ventilación caliente':'cristal'}
    chosen=r.choice(visible) if visible else None
    plan=[{'op':'explore'}]
    if chosen:
        plan.append({'op':'inspect','target':chosen['tipo']})
        material=resources.get(chosen['tipo'])
        if material and r.random()<.5:
            plan.append({'op':'gather','target':material})
    else:
        plan.append({'op':'rest'})
    return {"cuaderno":"Quiero observar los lugares que todavía no conozco. (Demostración sin LLM.)",
            "pregunta":"¿Qué puedo encontrar en otro sector?",
            "hipotesis":"El entorno puede mostrar propiedades distintas a las que ya vi.",
            "objetivo":"Conocer el entorno y sus posibilidades.",
            "motivo":"Demostración técnica, sin deliberación de IA.",
            "plan":plan,"revisar_en_minutos":90,"proyecto_id":"",
            "accion_proyecto":"nuevo","avance_estimado":5,
            "estado_actual":"Observando el entorno"}
