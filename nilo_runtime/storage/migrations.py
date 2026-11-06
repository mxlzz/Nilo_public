"""Migración de snapshots históricos al esquema físico v5, sin publicar v6.

Esta rutina se ejecuta dentro de la transacción iniciada por SessionLifecycle,
antes de escribir snapshot + entropía. Los marcadores legados mantienen las
migraciones idempotentes; no se reescriben archivos fuente de importación.
"""
from __future__ import annotations

import random
import time

from nilo_runtime.core.state import (
    SAVE_SCHEMA_VERSION, validate_loaded_envelope, validate_current_state,
)
from nilo_runtime.core.identity import new_uuid
from survival import ensure_needs, NEEDS_DEFAULT
from inventions import ensure_records
from habits import ensure_habits, bootstrap_skills
from agenda import ensure_agenda
from world import migrate_portable_structures, TRAVEL_MINUTES_PER_TILE
from cognition import consolidate_research
from goals import verified_simple_goal
from construction import ensure_object


def migration_path(raw):
    """Describe la transición SIN tocar el save ni su historial de IDs."""
    validate_loaded_envelope(raw)
    old=raw.get("version",0)
    return {"origen":old, "destino":SAVE_SCHEMA_VERSION,
            "reescritura_de_esquema":old!=SAVE_SCHEMA_VERSION,
            "compatibilidad_marcadores":"verificar_y_completar_si_faltan"}


def migrate_state(state, *, environment, highlight_key, is_newsworthy,
                  typing_duration):
    """Normalizar un save de 0.5/0.6 respetando su mundo y extensiones.

    La validación se repite al finalizar antes de cualquier commit.
    """
    migration_path(state)
    s=state; p=s['person']; s['version']=SAVE_SCHEMA_VERSION
    s.setdefault('scenario_id',"territorio_desconocido")
    ensure_needs(p);ensure_records(p);ensure_habits(p);ensure_agenda(p)
    # Migrar velocidades antiguas sin modificar tiempos simulados ya transcurridos.
    if s.get('speed') in (300,600):s['speed']=80
    s.setdefault("auto_pause_on_wait",True)
    s.setdefault("auto_wait_frozen",False)
    if not p.get('passive_needs_migrated_v0561'):
        # Las versiones anteriores reducían estas barras por el mero paso del
        # tiempo aunque no existieran frío, clima ni amenazas simuladas.
        # Se corrige exclusivamente el cero heredado, con registro auditable.
        fixed={}
        for key in ('abrigo','seguridad'):
            try:previous=float(p['needs'].get(key,NEEDS_DEFAULT[key]))
            except (TypeError,ValueError):previous=NEEDS_DEFAULT[key]
            if previous<=0:
                p['needs'][key]=NEEDS_DEFAULT[key]
                fixed[key]={'anterior':previous,'nuevo':NEEDS_DEFAULT[key]}
        if fixed:
            p.setdefault('migration_fixes',[]).append({'version':'0.5.6.1','reason':'Barras antiguas agotadas sin amenazas físicas modeladas', 'values':fixed})
        p['passive_needs_migrated_v0561']=True
    p.setdefault('measurements',[]);p.setdefault('conclusions',[]);p.setdefault('maintenance_history',[])
    p.setdefault('autonomy_stats',{'routine_actions':0,'deliberated_actions':0})
    p.setdefault('routine_since_llm',0)
    bootstrap_skills(p,s.get("events",[]))
    s['world'].setdefault('forage_deposits',{})
    p.setdefault('knowledge_profile','contemporaneo')
    p.setdefault('vehicle_id',None)
    s.setdefault('news',[])
    s.setdefault('read_marker',None)
    if not s.get('news_migrated_v4'):
        historical_keys={highlight_key(h.get('title','')) for h in s['news']}
        for e in s.get('events',[]):
            if e.get('notable') and is_newsworthy(e.get('text',''),e.get('kind','')):
                key=highlight_key(e.get('text',''))
                if key and key in historical_keys:continue
                s['news'].append({'id':'leg-'+str(new_uuid())[:10], 'when':e.get('when','—'),
                    'kind':e.get('kind','accion'), 'title':str(e.get('text',''))[:130],
                    'detail':str(e.get('text',''))[:350]})
                if key:historical_keys.add(key)
        s['news']=s['news'][-160:]
        s['news_migrated_v4']=True
    for k,default in [('chat',[]),('chat_daily',{}),('chat_error',''),('chatting',False),('llm_daily',{}),('llm_total',0),('provider_health',{}),('last_provider',''),('last_provider_model','')]:
        s.setdefault(k,default)
    s.setdefault('world', {})
    s['world'].setdefault('trail', [])
    # Actualización no destructiva de mundos existentes: la salida había sido
    # dibujada como suelo ':' indistinguible de las demás galerías.
    from world import cave_exit, tile, set_tile, reveal, tile_key
    ex,ey=cave_exit(s['world'])
    if tile(s['world'],ex,ey,-1)==':':
        set_tile(s['world'],ex,ey,-1,'e')
    # Solo es conocimiento si Nilo ya descendió o vio la conexión.
    if p.get('pos',[0,0,0])[2]==-1 or s['world'].get('visited',{}).get(tile_key(ex,ey,-1),0):
        if tile_key(ex,ey,-1) not in s['world'].get('revealed',[]):
            reveal(s['world'],ex,ey,-1,0)
    p.setdefault('unmodeled_attempts',[])
    if not s['world'].get('portable_migrated_v3'):
        migrated=migrate_portable_structures(s['world'],p)
        s['world']['portable_migrated_v3']=True
        if migrated:s.setdefault('events',[]).append({'when':'Migración v3','text':f"Guardé como herramientas portátiles {len(migrated)} objeto(s) anteriores: {', '.join(migrated[:5])}.",'kind':'sistema','notable':True})
    # Convertimos viajes pendientes de versiones anteriores sin ejecutar un salto.
    old_pending=p.get('pending')
    if old_pending and 'navigation' not in old_pending and old_pending.get('step',{}).get('op') in ('go','explore','gather'):
        nav=environment.start_navigation(s['world'],p,old_pending['step'],random.Random(9821+int(p.get('clock_minutes',0))))
        if nav:
            old_pending['navigation']=nav
            old_pending['total']=len(nav['route'])*TRAVEL_MINUTES_PER_TILE
            old_pending['remaining']=old_pending['total']
    s['chatting']=False;s['planning']=False
    p.setdefault('projects',[]);p.setdefault('project',None);p.setdefault('research',[]);p.setdefault('plan',[])
    # Las consultas al antiguo manual no eran acciones físicas: descartarlas al migrar.
    p['plan']=[step for step in p['plan'] if step.get('op')!='manual']
    if isinstance(p.get('pending'),dict) and p['pending'].get('step',{}).get('op')=='manual':
        p['pending']=None
    p.setdefault('strategy_feedback',[]);p.setdefault('review_at_minutes',0.0);p.setdefault('local_followups',0)
    if not p.get('research_consolidated_v032'):
        consolidate_research(p)
    if not p.get('research_consolidated_v0563'):
        consolidate_research(p)
        p['research_consolidated_v0563']=True
    p.setdefault('decision_history',[])

    for project in p['projects']+([p['project']] if p.get('project') else []):
        if not isinstance(project,dict):continue
        if not project.get('id'):project['id']=str(new_uuid())[:8]
        project.setdefault('status','activo' if project is p.get('project') else 'histórico (v1)')
        project.setdefault('progress',0);project.setdefault('steps_done',0);project.setdefault('state','Investigar posibilidades')
        project.setdefault('verified_results',[]);project.setdefault('subgoals',[]);project.setdefault('failed_actions',0)
        project.setdefault('no_progress_steps',0);project.setdefault('reconsideration_required',False)
        project.setdefault('verified_milestones',[])
    # Si el objetivo concreto de reconocimiento + agua se cumplió y existe
    # prueba real de haber bebido, ya no conservarlo artificialmente al 95%.
    closure=verified_simple_goal(s['world'],p,f"Día {int(p.get('clock_minutes',0)//1440)+1}")
    if closure:
        s['events'].append({'id':str(new_uuid()),'when':'Migración 0.5.6.3',
            'text':'Cerré un proyecto por hechos registrados: fuente de agua observada, bebida comprobada y entorno recorrido.',
            'kind':'evaluación','notable':True})
    for b in s['world'].get('structures',[]):
        from world import enrich_structure
        enrich_structure(b)
        ensure_object(b,structure=True)
    for b in s['world'].get('retired_structures',[]):ensure_object(b,structure=True)
    for item in p.get('items',[]):ensure_object(item,structure=False)
    for note in s.get('journal',[]):
        if not note.get('id'):note['id']=str(new_uuid())[:10]
        note.setdefault('duration_seconds',0)
        note.setdefault('started_at',0);note.setdefault('origin','llm')
    # Si estaba escribiendo al cerrar, solo esa anotación puede terminar según reloj real.
    pending=p.get('pending')
    if pending and pending.get('step',{}).get('op')=='write':
        # Una entrada empezada en la versión anterior adopta la velocidad
        # nueva y continúa desde el progreso que le corresponda.
        if pending.get('timing_version') != 2:
            old_entry=next((note for note in s.get('journal',[])
                            if note.get('id')==pending.get('journal_id')),None)
            if old_entry:
                duration=typing_duration(old_entry['text'])
                old_entry['duration_seconds']=duration
                pending['total_real']=duration
                pending['total']=duration/60
            pending['timing_version']=2
        # El progreso ya queda guardado en el snapshot. No deducirlo
        # nuevamente desde hora real: al cerrar el programa Nilo no escribe
        # y a ×2 los segundos reales tampoco equivalen a avance escrito.
        if 'remaining_real' not in pending:
            pending['remaining_real']=max(0,float(pending.get('total_real',40))-
                max(0,time.time()-float(pending.get('started_at',time.time()))))
        pending['remaining_real']=min(float(pending.get('total_real',40)),
                                       max(0.0,float(pending['remaining_real'])))
        pending['remaining']=pending['remaining_real']/60

    validate_current_state(state)
    return state
