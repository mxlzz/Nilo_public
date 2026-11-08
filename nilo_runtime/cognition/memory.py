"""Recuperación determinista de experiencias anteriores relevantes para la situación.

Lee registros reales del agente: no redacta hechos, no muta la memoria y no pide
consultas adicionales al LLM. Las rutinas repetidas se agrupan por contenido.
"""
from __future__ import annotations
from nilo_runtime.cognition.research import terms
from nilo_runtime.cognition.evidence import reference

_GENERIC = {'investigar', 'investigacion', 'explorar', 'exploracion', 'proyecto',
            'concluir', 'cerrar', 'completar', 'verificar', 'prueba', 'objetivo',
            'actual', 'entorno', 'resultado', 'resultados', 'progreso'}
_TRANSITIONS = {'descend', 'ascend'}
_MAX_FACT = 210


def recall_relevant(person, world, limit=6):
    """Devuelve experiencias con procedencia, vinculadas al objetivo o lugar.

    La cercanía a una entrada reconocida basta para recordar una transición ya
    realizada, incluso cuando el proyecto actual tenga otro título. No revela
    propiedades del terreno que Nilo no haya experimentado.
    """
    project = person.get('project') or {}
    # Focos simultáneos: proyecto, preguntas abiertas y acciones recientes.
    # Son temas documentados por Nilo, no sugerencias externas ni nuevas metas.
    query_parts = [
        project.get('title'), project.get('reason'), project.get('state'),
        project.get('last_action'), project.get('last_result'),
        person.get('active_research'),
    ]
    for row in (person.get('research') or [])[-5:]:
        if isinstance(row, dict) and row.get('state') == 'abierta':
            query_parts.extend((row.get('question'), row.get('hypothesis')))
    for row in (person.get('action_outcomes') or [])[-3:]:
        if isinstance(row, dict):
            query_parts.append(row.get('target'))
    query = ' '.join(str(value or '') for value in query_parts)
    keywords = terms(query) - _GENERIC
    project_id = project.get('id')
    # La referencia exacta a una entidad se prefiere a la coincidencia léxica.
    # Una mención textual solo ayuda a recuperar, nunca valida un objeto.
    focus_targets={str(r.get('target') or '').casefold()
                   for r in person.get('action_outcomes',[])[-4:]
                   if isinstance(r,dict) and str(r.get('target') or '').strip()}
    focus_targets.discard('')
    here = person.get('pos', [])
    nearby = set()
    revealed=set(world.get("revealed",[]))
    # Una exploración superficial estancada justifica recordar lugares con
    # resultados previos, aunque estén lejos y no coincidan con el título actual.
    recent=person.get('life_history',[])[-35:]
    failed_explores=sum(1 for e in recent if isinstance(e,dict)
                        and e.get('action')=='explore' and not e.get('successful'))
    stalled=(project.get('reconsideration_required') or project.get('no_progress_steps',0)>=3
             or failed_explores>=3)
    cave=(world.get('sites') or {}).get('cueva',{})
    known_cave=(isinstance(cave,dict) and all(isinstance(cave.get(k),int) for k in ('x','y'))
                and f"{cave.get('x')},{cave.get('y')},0" in revealed)
    # Una experiencia remota no debe imponerse por estancamiento si Nilo
    # está lejos y concentrado en otro lugar o material.
    interest_in_cave=bool('cueva' in keywords)
    near_known_cave=(len(here)>=3 and
        abs(cave['x']-here[0])+abs(cave['y']-here[1])<=12) if known_cave else False
    remembered_alternative=bool(stalled and known_cave and len(here)>=3
        and here[2]==0 and (near_known_cave or interest_in_cave))
    if isinstance(here, (list, tuple)) and len(here) >= 3:
        for name, point in (world.get('sites') or {}).items():
            if not isinstance(point, dict):
                continue
            if point.get('z', 0) != here[2]:
                continue
            if all(isinstance(point.get(k), int) and not isinstance(point.get(k),bool)
                   for k in ('x', 'y')):
                # Los sitios internos del generador no son memoria observable.
                # El mismo filtro de revelado se usa en navegación/percepción.
                if f"{point['x']},{point['y']},{point.get('z',0)}" not in revealed:
                    continue
                if abs(point['x'] - here[0]) + abs(point['y'] - here[1]) <= 3:
                    nearby.update(terms(str(name)))
    ranked, seen = [], set()
    for index, entry in enumerate(person.get('life_history', [])):
        if not isinstance(entry, dict):
            continue
        fact = str(entry.get('fact') or '').strip()
        op = str(entry.get('action') or '')
        if not fact:
            continue
        words = terms(fact) | terms(op)
        match = keywords & words
        local = nearby & words
        same_project=bool(project_id and entry.get('project_id')==project_id)
        target=str(entry.get('target') or '').casefold()
        obj=str(entry.get('object_id') or '').casefold()
        same_target=bool((target and target in focus_targets)
                         or (obj and obj in focus_targets))
        recorded_position=entry.get('position_at_end')
        near_recorded=(isinstance(here,(list,tuple)) and len(here)==3
                       and isinstance(recorded_position,list) and len(recorded_position)==3
                       and all(isinstance(v,int) and not isinstance(v,bool)
                               for v in recorded_position)
                       and recorded_position[2]==here[2]
                       and abs(recorded_position[0]-here[0])
                           +abs(recorded_position[1]-here[1])<=3)
        # Una entrada de cueva cercana se asocia a ascensos y descensos ya
        # realizados; no se convierte una transición fallida en paso conocido.
        transition = bool('cueva' in nearby and op in _TRANSITIONS)
        alternative=bool(remembered_alternative and op=='descend'
                         and entry.get('successful'))
        if not (match or local or transition or alternative or same_project or same_target):
            continue
        success = bool(entry.get('successful'))
        score = len(match) * 6 + len(local) * 12
        if same_project:score+=10
        if same_target:score+=18
        if near_recorded:score+=5
        if transition and success:
            score += 30
        elif transition:
            score += 4
        if success:
            score += 3
        if alternative:score += 36
        # No colapsar ensayos independientes que poseen IDs de acción
        # distintos. En registros legados sin IDs se mantiene deduplicación.
        action_id=entry.get("action_id")
        key = ("accion",action_id) if isinstance(action_id,str) and action_id else (
            op, success, fact.casefold())
        if key in seen:
            continue
        seen.add(key)
        memory={'id':entry.get('id'),
                'cuando':entry.get('when'),
                'accion':op,'exito':success,'hecho':fact[:_MAX_FACT]}
        for source,target_key in (('action_id','accion_id'),
                                  ('measurement_id','medicion_id'),
                                  ('object_id','objeto_id'),
                                  ('project_id','proyecto_id'),
                                  ('target','objetivo_registrado'),
                                  ('position_at_end','posicion_tras_accion')):
            if entry.get(source) is not None:memory[target_key]=entry[source]
        reasons=[]
        if match:reasons.append("terminos_del_interes")
        if local:reasons.append("lugar_descubierto_cercano")
        if same_project:reasons.append("mismo_proyecto")
        if same_target:reasons.append("mismo_objetivo_registrado")
        if near_recorded:reasons.append("posicion_del_recuerdo_cercana")
        if transition:reasons.append("transicion_cercana_registrada")
        if alternative:reasons.append("alternativa_previamente_recorrida")
        memory["criterios_recuperacion"]=reasons
        memory["naturaleza"]="recuerdo_de_accion"
        if entry.get("measurement_id"):
            memory["fuente_medicion"]=reference(
                person,entry["measurement_id"],expected="medicion")
        elif entry.get("action_id"):
            memory["fuente_accion"]=reference(
                person,entry["action_id"],expected="accion")
        else:
            memory["procedencia"]="registro_biografico_legacy"
        if alternative:
            memory['pista']='Transición previamente realizada; no garantiza un camino actual'
            memory['lugar_conocido']=[cave['x'],cave['y'],0]
        ranked.append((score,index,memory))
    ranked.sort(key=lambda item: (-item[0], -item[1]))
    return [row for _, _, row in ranked[:max(0, min(10, int(limit)))]]
