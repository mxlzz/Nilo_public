"""Nilo: simulación autónoma local, deliberación externa, interfaz web.
Ejecutar: python nilo.py (Python 3.10+, solo biblioteca estándar).
"""
from __future__ import annotations
import json, sqlite3, threading, time, random, os, sys, webbrowser, traceback, difflib, uuid, collections, hashlib
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs
from datetime import datetime
from world import (new_world, world_view, execute_action, MATERIALS,
                   migrate_portable_structures, prepare_navigation, advance_navigation, navigation_result, TRAVEL_MINUTES_PER_TILE,
                   infer_form, is_portable, item_effects, tile, valid, DIRS, resolve_go)
from brain import config, available, context_for, normalize_decision, request_llm, demo_decision, request_chat
from providers import route, ProvidersUnavailable, public_info, routing_signature
from physics import geometry_from_step, human_knowledge
from cognition import consolidate_research, register_research
from survival import ensure_needs, update_needs, needs_summary, NEEDS_DEFAULT
from construction import ensure_object
from habits import (ensure_habits, bootstrap_skills, record_skill, set_wait_preferences,
                    choose_wait_action, record_wait_result, record_wait_selection)
from inventions import (ensure_records,register_design,record_design_test,
                        submit_proposal,review_proposal,record_personal_experience,
                        submit_debug_report,record_action_outcome)
from archive import History
from review_store import ReviewStore, TABS
from observer import pending_sources
from experiment_log import capture, measure, compare_rest, closure_status, topic as research_topic, link_conclusion, observational_conclusion
from physical_links import snapshot as physical_snapshot, entities_for_action
from phenomena import missing_physics
from laboratory import compare as compare_physical
from motivation import record_maintenance, maintenance_summary
from behavior import record_behavior, behavior_summary
from strategy_review import semantic_signature, evidence_snapshot, detect_repetition
from project_progress import discovered_during_action, advance_evidence, repeated_methods
from agenda import ensure_agenda, set_agenda, choose_agenda_step, record_agenda_result, awaken_reminders, acknowledge_reminders
from goals import verified_simple_goal
from timing import effective_speed, writing_tick, SUPPORTED_SPEEDS, deliberation_interval_seconds
from agent import initial_agent
from scenarios import get_scenario
from environments import get_environment
from action_results import ActionResult
from run_history import RunHistory
from diagnostics import inspect_invariants, record_invariant_issue, record_contract_issue, review_packet
from action_contracts import before as contract_before, classify as classify_contract
from research_cycle import begin_prediction, finish_prediction
from project_lifecycle import completion_evidence, project_needs_review, retire_project, closure_diagnostic
from bodily_policy import rest_minutes, fatigue_multiplier
from intervention import active_intervention
from interface_prefs import load as load_interface_prefs, save as save_interface_prefs

HERE=Path(__file__).resolve().parent
DB=HERE/'nilo_mundo.sqlite3'
ACTION_DURATIONS={'explore':22,'go':19,'inspect':9,'gather':20,'experiment':32,'combine':48,'build':90,'craft':60,'use':27,'excavate':50,'descend':16,'ascend':16,'rest':30,'wait':30,'forage':18,'drink':8,'eat':12,'design':26,'propose':28,'assemble':70,'modify':50,'dismantle':45,'report_issue':24,'conclude':12,'compare':15,'interact':18}

# Ritmo aproximado de una persona que escribe fluidamente en un teclado:
# unas 60-70 palabras por minuto, con pausas naturales tras puntuación.
# Compartir estas mismas constantes con interfaz.html para la animación local.
def typing_step(ch: str) -> float:
    return 0.11 if ch in ' \t' else 0.17


def typing_pause(ch: str) -> float:
    if ch in '.!?…': return 0.38
    if ch in ',;:': return 0.20
    if ch == '\n': return 0.42
    return 0.0


def typing_duration(text: str) -> float:
    total = 0.0
    for i, ch in enumerate(text):
        total += typing_step(ch)
        if i < len(text) - 1:
            total += typing_pause(ch)
    return round(max(1.0, total), 3)


def typing_visible_chars(text: str, elapsed_seconds: float) -> int:
    t = 0.0
    for i, ch in enumerate(text):
        t += typing_step(ch)
        if t > elapsed_seconds + 1e-6:
            return i
        if i < len(text) - 1:
            t += typing_pause(ch)
    return len(text)



def initial_state(world_seed=7321, scenario_id="territorio_desconocido"):
    """Partida nueva: el escenario elige agente y entorno, no la inteligencia."""
    scenario=get_scenario(scenario_id)
    environment=get_environment(scenario.environment_id)
    return {"version":5,
            "scenario_id":scenario.id,
            "world":environment.make_world(world_seed),
            "person":initial_agent(
                name=scenario.name,
                spawn=scenario.spawn,
                inventory=dict(scenario.starting_inventory),
                materials=environment.materials(),
                knowledge_profile=scenario.knowledge_profile,
                mood=scenario.mood),
            "events":[],"news":[],"read_marker":None,"journal":[],
            "speed":1.0,"paused":False,"real_saved":time.time(),"last_llm_real":0,
            "llm_daily":{},"llm_total":0,"last_tokens":{"entrada":0,"salida":0},
            "ai_error":"","planning":False,"last_reason":"","chat":[],
            "chatting":False,"chat_daily":{},"chat_error":"",
            "next_deliberation_real":0.0,"mode":"","updated":0,
            "provider_health":{},"last_provider":"","last_provider_model":""}


def highlight_key(text):
    q=str(text).strip().lower()
    if q.startswith(('observé por primera vez:', 'apareció en mi campo de visión:')):
        if 'agua' in q and not any(m in q for m in ('cueva','ruina','cristal','mineral oscuro')):
            return 'primer-contacto-agua'
        if 'cueva' in q:return 'primer-contacto-cueva'
    return None


def is_newsworthy(text, kind):
    """Hitos basados en hechos del motor, no en prosa espontánea del LLM.

    La lista de raíces filtra rutinarios; no pretende resumir narrativamente
    todos los eventos ni sustituye el cuaderno.
    """
    q=str(text).strip().lower()
    if kind=='decision':
        return any(v in q for v in ('finaliz', 'terminad', 'cerrad', 'nuevo proyecto', 'investigaci'))
    if kind in ('accion','resultado'):
        strong=('fabriqué ', 'construí ', 'abrí un ', 'abrí paso', 'excavé ',
                'utilicé ', 'descubrí:', 'descendí ', 'regresé ', 'llené ',
                'corté madera ', 'se hunde ', 'flota ', 'flotó ', 'navegar ',
                'probé ', 'completé ', 'intervine ', 'desmonté completamente ')
        if q.startswith(strong):return True
        if q.startswith(('observé por primera vez:', 'apareció en mi campo de visión:')):
            return any(word in q for word in ('cueva','ruina','mineral oscuro','cristal','agua'))
    return False


class Simulation:
    def __init__(self, db_path=None, world_seed=7321, rng_seed=None,
                 scenario_id="territorio_desconocido"):
        # La aplicación sigue usando DB y las semillas anteriores. El modo de
        # prueba inyecta una base aislada y semillas explícitas.
        self.lock=threading.RLock();self.conn=sqlite3.connect(db_path if db_path is not None else DB,check_same_thread=False,timeout=15)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('CREATE TABLE IF NOT EXISTS snapshot (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
        self.archive=History(self.conn)
        self.review=ReviewStore(self.conn)
        self.sessions=RunHistory(self.conn,HERE)
        from historical_lab import TimelineStore
        self.timeline=TimelineStore(self.conn)
        self.timeline_capture_enabled=True
        self.timeline_version=(HERE / 'VERSION').read_text(encoding='utf-8').strip()
        row=self.conn.execute('SELECT payload FROM snapshot WHERE id=1').fetchone()
        if row:
            try:self.s=json.loads(row[0]);self.s['planning']=False
            except (ValueError,KeyError):self.s=initial_state(world_seed,scenario_id)
        else:self.s=initial_state(world_seed,scenario_id)
        # La partida guardada manda: una opción nueva no reemplaza su escenario.
        self.scenario=get_scenario(self.s.get('scenario_id',"territorio_desconocido"))
        self.environment=get_environment(self.scenario.environment_id)
        # Volcar primero los registros legados, antes de migraciones que los pudieran acotar.
        self.archive.sync(self.s)
        fresh_markers = not self.s.get('archive_migrated_052')
        self.migrate()
        self.archive.sync(self.s)
        if fresh_markers:
            legacy_id=self.s.get('read_marker')
            if legacy_id:
                legacy_seq=self.archive.seq_for('news', legacy_id)
                if legacy_seq:self.archive.mark_read('news',legacy_seq)
            # Antes de esta versión no existía 'cuaderno sin leer'.
            self.archive.mark_read('journal')
            self.s['archive_migrated_052']=True
        self.s['real_saved']=time.time()
        self.rng_seed=(9821+int(self.s['person']['clock_minutes'])) if rng_seed is None else int(rng_seed)
        self.rng=random.Random(self.rng_seed)
        self.last_loop=time.monotonic();self.last_persist=0.0;self.stopped=False
        configured=config()
        signature=routing_signature(configured)
        # No cambiar partidas corrientes ni replays solo por iniciar Nilo:
        # la huella determinista del mundo debe seguir intacta.
        if (available(configured) and self.s.get('mode')=='espera'
                and self.s.get('routing_signature')!=signature):
            # Había una espera calculada con modelos/clave anteriores.
            self.s['routing_signature']=signature
            self.s['next_deliberation_real']=0
            self.s['auto_wait_frozen']=False
        self.sessions.start(self.s,self.scenario.id,self.scenario.environment_id,
                            configured_provider=configured.get("PROVIDER"),
                            configured_model=configured.get("MODEL"),
                            rng_seed=self.rng_seed)
        self.write()

    def migrate(self):
        """Compatibilidad con partidas del prototipo 01; nunca reinicia el mundo."""
        s=self.s; p=s['person']; s['version']=5
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
                    s['news'].append({'id':'leg-'+str(uuid.uuid4())[:10], 'when':e.get('when','—'),
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
            nav=self.environment.start_navigation(s['world'],p,old_pending['step'],random.Random(9821+int(p.get('clock_minutes',0))))
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
            project.setdefault('id',str(uuid.uuid4())[:8]);project.setdefault('status','activo' if project is p.get('project') else 'histórico (v1)')
            project.setdefault('progress',0);project.setdefault('steps_done',0);project.setdefault('state','Investigar posibilidades')
            project.setdefault('verified_results',[]);project.setdefault('subgoals',[]);project.setdefault('failed_actions',0)
            project.setdefault('no_progress_steps',0);project.setdefault('reconsideration_required',False)
            project.setdefault('verified_milestones',[])
        # Si el objetivo concreto de reconocimiento + agua se cumplió y existe
        # prueba real de haber bebido, ya no conservarlo artificialmente al 95%.
        closure=verified_simple_goal(s['world'],p,f"Día {int(p.get('clock_minutes',0)//1440)+1}")
        if closure:
            s['events'].append({'id':str(uuid.uuid4()),'when':'Migración 0.5.6.3',
                'text':'Cerré un proyecto por hechos registrados: fuente de agua observada, bebida comprobada y entorno recorrido.',
                'kind':'evaluación','notable':True})
        for b in s['world'].get('structures',[]):
            from world import enrich_structure
            enrich_structure(b)
            ensure_object(b,structure=True)
        for b in s['world'].get('retired_structures',[]):ensure_object(b,structure=True)
        for item in p.get('items',[]):ensure_object(item,structure=False)
        for note in s.get('journal',[]):
            note.setdefault('id',str(uuid.uuid4())[:10]);note.setdefault('duration_seconds',0)
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

    def write(self):
        # Estado coherente en una transacción SQLite. La clave API nunca se persiste.
        self.s['updated']=time.time()
        self.sessions.touch(self.s['person']['clock_minutes'])
        self.archive.sync(self.s)
        self.conn.execute('INSERT INTO snapshot (id,payload) VALUES (1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(json.dumps(self.s,ensure_ascii=False),))
        self.conn.commit();self.last_persist=time.monotonic()

    def stamp(self):
        d=int(self.s['person']['clock_minutes']//1440)+1
        m=int(self.s['person']['clock_minutes']%1440)
        return f"Día {d} · {m//60:02d}:{m%60:02d}"

    def event(self, facts,kind='accion',notable=False):
        if notable and facts:
            signal=next((str(f) for f in facts if is_newsworthy(f,kind)),None)
            if signal:
                # Título = hecho principal. Detalle = SOLO información adicional;
                # no repetir la misma frase al expandir la novedad.
                title=signal.strip()
                overflow=''
                if len(title)>130:
                    cut=title.rfind(' ',0,129)
                    cut=cut if cut>=60 else 130
                    overflow=title[cut:].strip()
                    title=title[:cut].rstrip()+'…'
                extras=[overflow] if overflow else []
                extras.extend(str(f).strip()[:350] for f in facts[:3] if str(f).strip()!=signal.strip())
                item={'id':'hit-'+str(uuid.uuid4())[:12], 'when':self.stamp(), 'kind':kind,
                      'title':title, 'detail':' '.join(extras)[:700]}
                news=self.s.setdefault('news',[])
                # No crear clones contiguos del mismo resultado.
                key=highlight_key(signal)
                already=bool(key and any(highlight_key(n.get('title',''))==key for n in news))
                if not already and (not news or news[-1]['title']!=item['title']):
                    news.append(item)
                    self.archive.add('news',item)
                    del news[:-200]
        for fact in facts:
            entry={'id':str(uuid.uuid4())[:15], 'when':self.stamp(),
                   'text':str(fact)[:350], 'kind':kind, 'notable':notable}
            self.archive.add('event',entry)
            self.s['events'].append(entry)
        self.s['events']=self.s['events'][-250:]

    def review_rule(self, proposal_id, decision, reason):
        with self.lock:
            result=review_proposal(self.s['person'],proposal_id,decision,reason,self.stamp())
            # Una aprobación NO modifica el código ni habilita una física inventada.
            subject=result.get('title') or result.get('phenomenon','propuesta')
            self.event([f"Evaluación externa de '{subject}': {result['status']}. "
                        f"Fundamento: {result['review']['reason']}"], 'evaluación', True)
            self.write()
            return {'ok':True,'status':result['status'],'engine_enabled':False}

    def diagnostic_package(self, proposal_id):
        """Consulta de revisión local, sin ejecutar código ni modificar el estado."""
        with self.lock:
            return review_packet(self.s['person'], proposal_id,
                                 scenario_id=self.scenario.id,
                                 environment_id=self.scenario.environment_id,
                                 version=(HERE/'VERSION').read_text(encoding='utf-8').strip())

    def measurement_record(self, item_id):
        """Consulta de un ensayo archivado para enlaces entre fichas."""
        if not isinstance(item_id, str) or not item_id.startswith('med-') or len(item_id)>60:
            raise ValueError('Identificador de medición inválido')
        with self.lock:
            record=self.archive.get('measurement', item_id)
            if record is None:
                record=next((m for m in self.s['person'].get('measurements',[])
                             if m.get('id')==item_id),None)
            if record is None:
                raise ValueError('La medición no está disponible en el archivo')
            return record

    def mark_read(self, category, item_id=None, all_items=False):
        """La marca de lectura avanza sin borrar datos históricos."""
        with self.lock:
            if category not in ('journal','news'):raise ValueError('Categoría inválida')
            if not all_items:
                seq=self.archive.seq_for(category,item_id)
                if not seq:raise ValueError('No existe la entrada indicada')
            else:seq=None
            self.archive.mark_read(category,seq)
            if category=='news':
                items=self.archive.recent('news',1) if all_items else [dict(id=item_id)]
                self.s['read_marker']=items[0]['id'] if items else None
            self.write()
            return {'ok':True,'category':category,'unread':self.archive.count_unread(category)}

    def mark_one_read(self, category, item_id):
        """Abrir una entrada solo marca ESA entrada, sin dar otras por leídas."""
        with self.lock:
            if category not in ('journal','news'):raise ValueError('Categoría inválida')
            seq=self.archive.seq_for(category,item_id)
            if not seq:raise ValueError('No existe la entrada indicada')
            unread=self.archive.mark_one_read(category,seq)
            self.write()
            return {'ok':True,'category':category,'unread':unread}

    def mark_all_read(self, categories):
        with self.lock:
            for category in categories:
                if category not in ('journal','news'):raise ValueError('Categoría inválida')
            for category in categories:self.archive.mark_read(category)
            if 'news' in categories:
                items=self.archive.recent('news',1)
                self.s['read_marker']=items[0]['id'] if items else None
            self.write()
            return {'ok':True,'unread':{c:self.archive.count_unread(c) for c in ('journal','news')}}

    def mark_summarized_read(self):
        """Solo mensajes incluidos en un resumen del chat ya respondido."""
        with self.lock:
            positions=self.s.get('last_catchup_covered',{})
            if not positions:raise ValueError('Todavía no hay un resumen completado para marcar.')
            for category,seq in positions.items():
                self.archive.mark_read(category,seq)
            items=self.archive.recent('news',1)
            if items and 'news' in positions:
                seen=self.archive.db.execute('SELECT item_id FROM history WHERE category=? AND seq=?',
                    ('news',self.archive.position('news'))).fetchone()
                if seen:self.s['read_marker']=seen[0]
            self.s['last_catchup_covered']={}
            self.s['catchup_offset']=0
            self.write()
            return {'ok':True,'unread':{cat:self.archive.count_unread(cat) for cat in ('journal','news')}}

    def catchup(self, offset=0, limit=80):
        """Entradas todavía no leídas, ordenadas por su secuencia de hechos.
        No confundir el resumen con un nuevo descubrimiento de Nilo.
        """
        with self.lock:
            total,selected=self.archive.pending_page(offset,limit)
            out=[]
            for entry in selected:
                if entry.get('text') is not None and entry.get('origin'):
                    kind='Cuaderno';detail=str(entry.get('text',''))[:460]
                else:
                    kind='Novedad';detail=str(entry.get('detail',entry.get('title','')))[:460]
                out.append({'seq':entry['seq'],'tipo':kind,'fecha':entry.get('when',''),
                            'texto':detail,'id':entry['id']})
            return {'total':total,'desde':offset,'mostradas':len(out),'entradas':out,
                    'restantes':max(0,total-offset-len(out)),
                    'marcadores':{c:self.archive.position(c) for c in ('journal','news')}}


    def bootstrap_reviews(self,seen):
        with self.lock:
            self.review.bootstrap(seen)
            self.conn.commit()
            return {'ok':True,'review_seen':self.review.seen()}

    def mark_tab_reviewed(self,tab,keys):
        if tab not in TABS or not isinstance(keys,list) or len(keys)>1500:
            raise ValueError('Lectura de solapa inválida')
        with self.lock:
            self.review.mark([(tab,key) for key in keys])
            self.conn.commit()
            return {'ok':True}

    def observer_summary(self,candidates,continuation=None):
        """Síntesis editorial de los pendientes; no afecta al agente ni borra omisiones.

        La primera página examina todos los registros sin leer. «Qué más» usa
        el mismo límite de secuencia y desciende en prioridad; solo acusa
        lectura de las fichas efectivamente expuestas en esta entrega.
        """
        cfg=config()
        if continuation is not None:
            if (not isinstance(continuation,dict)
                or type(continuation.get('snapshot_seq')) is not int
                or type(continuation.get('max_score')) is not int
                or not 0<=continuation['snapshot_seq']<=2**63-1
                or not 0<=continuation['max_score']<=140):
                raise ValueError('Continuación de resumen inválida')
        with self.lock:
            if not self.review.initialized():
                raise ValueError('Inicializá primero los indicadores de lectura.')
            current_max=int(self.conn.execute(
                'SELECT COALESCE(MAX(seq),0) FROM history').fetchone()[0])
            snapshot_seq=min(current_max,continuation['snapshot_seq']) if continuation else current_max
            # El cliente confirma cada entrega antes de ofrecer «¿Qué más?».
            # Buscar nuevamente los pendientes del mismo snapshot: el viejo
            # techo de puntuación ocultaba proyectos no mostrados cuando una
            # página diversa incluía registros de prioridad menor.
            records,refs,remaining,omitted=pending_sources(
                self.s,self.archive,self.review,candidates,
                limit=12,max_seq=snapshot_seq,score_ceiling=None,
                include_omitted=True)
            if not records:
                text=('No quedan otras novedades destacadas en esta síntesis.' if continuation
                     else 'No hay acontecimientos destacados pendientes.')
                if omitted:
                    # Nada se marca al generarlo: la interfaz debe confirmar
                    # después de recibir esta respuesta.
                    sid=self.review.new_summary(text,omitted,'motor/sin-llm')
                    self.write()
                    return {'empty':True,'id':sid,'remaining':0,'text':text,
                            'reviewed':len(omitted),'omitted':len(omitted),
                            'count':0,'continuation':None,'links':[]}
                return {'empty':True,'remaining':0,'text':text}
            if not available(cfg):
                raise ValueError('Para generar una síntesis narrativa hace falta una API de LLM configurada.')
            day=datetime.now().strftime('%Y-%m-%d')
            if self.s['chat_daily'].get(day,0)>=int(cfg.get('MAX_CHAT_CALLS_PER_DAY','40')):
                raise ValueError('Se alcanzó el límite diario de consultas de chat y resúmenes.')
        observations=[{'id':str(i+1),'tipo':r['kind'],'fecha':r['when'],
                       'hecho':r['text']} for i,r in enumerate(records)]
        context={'hechos_documentados_seleccionados':observations,
                 'registros_rutinarios_evaluados_y_omitidos':len(omitted),
                 'instruccion_de_resumen':'Informar novedades relevantes; agrupar proyectos, '
                 'construcciones y ensayos repetidos. No atribuir hechos no presentes.',
                 'regla':'Resumen para observador externo. Nilo conserva autonomía.'}
        system=("Sos un observador externo de una simulación autónoma. Respondé en español "
                "argentino con encabezados breves por acontecimiento o tema "
                "(por ejemplo Exploración, Construcciones, Proyecto), no con una crónica "
                "de introducción, desarrollo y cierre. La extensión depende de los hechos: "
                "una sola novedad admite una oración; varias relevantes pueden necesitar "
                "más apartados. Agrupá lo repetitivo y evitá enumerar objetos equivalentes. "
                "Si aparece un descubrimiento, una decisión o un experimento excepcional, "
                "podés narrarlo en un párrafo más desarrollado, solo con evidencia registrada. "
                "Explicá qué hizo Nilo, qué cambió y qué quedó pendiente. Distinguir intención, "
                "resultado físico verificable e hipótesis. No inventes causalidad ni éxitos. "
                "Un proyecto marcado como terminado no prueba por sí solo su hipótesis: "
                "distinguí el estado administrativo de las mediciones pertinentes. "
                "Una retención parcial no es estanqueidad, y contener agua no demuestra "
                "contención de sólidos. No atribuyas mediciones ausentes. "
                "No agregues advertencias de rutina ni comentarios sobre el formato. "
                "No es una lista de tareas para Nilo ni una evaluación psicológica.")
        (reply,tokens),provider,model=route(
            cfg,self.s,self.lock,
            lambda pcfg:request_chat(pcfg,context,[{'role':'user','text':
                '¿Qué me perdí? Resumí lo principal de estos hechos seleccionados.'}],
                system_instruction=system),'chat')
        if not isinstance(reply,str) or not reply.strip():
            raise ValueError('El modelo no devolvió una síntesis válida; no se marcó nada como leído.')
        with self.lock:
            self.s['chat_daily'][day]=self.s['chat_daily'].get(day,0)+1
            self.sessions.note_llm(provider,model,"chat")
            summary_id=self.review.new_summary(reply,refs+omitted,provider+'/'+model)
            self.write()
            # El cursor fija el snapshot. Lo ya leído desaparece por la
            # confirmación, no por un techo de puntaje que pierda categorías.
            cursor={'snapshot_seq':snapshot_seq,'max_score':records[-1]['priority']}
            contextual_links=[]
            seen_context=set()
            for ref in refs:
                key=(ref.get('category'),ref.get('id'))
                if ref.get('related_context') and key not in seen_context:
                    seen_context.add(key)
                    contextual_links.append({
                        'category':ref['category'],'id':ref['id'],
                        'title':ref.get('title','Registro vinculado')[:90]})
            return {'id':summary_id,'text':reply,'count':len(records),
                    'related_links':contextual_links,
                    'reviewed':len(refs)+len(omitted),'omitted':len(omitted),
                    'remaining':remaining,'continuation':cursor if remaining else None,
                    'links':[{'category':r['category'],'id':r['id'],'kind':r['kind'],
                              'title':r['text'][:90]} for r in records]}

    def acknowledge_observer_summary(self,summary_id):
        with self.lock:
            result=self.review.acknowledge(summary_id,self.archive)
            self.write()
            return {'ok':True,'id':summary_id,'acknowledged':result['acknowledged']}

    def observer_summary_history(self):
        with self.lock:return self.review.recent_summaries()

    def journal(self,text, question='', hypothesis='',origin='llm',linked=None):
        text=text[:500]
        duration=typing_duration(text)
        entry={'id':str(uuid.uuid4())[:10],'when':self.stamp(),'text':text,
               'question':question,'hypothesis':hypothesis,'origin':origin,
               'started_at':time.time(),'duration_seconds':duration}
        if isinstance(linked,dict):
            for name in ('project_id','research_id'):
                if isinstance(linked.get(name),str) and linked[name]:entry[name]=linked[name]
        self.archive.add('journal',entry)
        self.s['journal'].append(entry)
        self.s['journal']=self.s['journal'][-160:]
        # Duración base de escritura, expresada en segundos simulados.
        # La política temporal ajusta la tasa al avanzar, no este valor.
        self.s['person']['pending']={'step':{'op':'write'},'start':self.stamp(),
                'started_at':entry['started_at'],'total_real':duration,'remaining_real':float(duration),
                'journal_id':entry['id'],'timing_version':2,'total':duration/60,'remaining':duration/60}
        return entry

    def remember_strategy(self, message):
        p=self.s['person'];feedback=p.setdefault('strategy_feedback',[])
        if not feedback or feedback[-1]!=message:
            feedback.append(str(message)[:220]);del feedback[:-18]

    def validate_plan(self,steps):
        """Conservar API interna; delegar reglas de plan al entorno actual."""
        return self.environment.validate_plan(
            self.s['world'], self.s['person'], steps,
            self.remember_strategy, self.event)

    def improve_plan(self,steps):
        """Filtrar acciones redundantes según las capacidades del entorno."""
        return self.environment.improve_plan(
            self.s['world'], self.s['person'], steps,
            self.remember_strategy, self.event)

    def followup_without_llm(self):
        """Completa una prueba de herramienta pendiente sin consumir otra deliberación.

        Solo para operaciones verificables, dos continuaciones como máximo por bloque.
        """
        p=self.s['person'];w=self.s['world']
        if not p.get('project') or p.get('project',{}).get('reconsideration_required') or p.get('local_followups',0)>=2:
            return None
        if p.get('clock_minutes',0)>=p.get('review_at_minutes',0):
            return None
        x,y,z=p['pos'];inv=p['inventory']
        for obj in reversed(p.get('items',[])):
            if any(t.get('revision',1)==obj.get('revision',1) for t in obj.get('tests',[])) or obj.get('durability',0)<=0:
                continue
            form=obj.get('form');uses=item_effects(obj)
            if form=='golpe' and uses.get('golpear'):
                sample=next((m for m,n in inv.items() if n>0 and m in p['materials']),None)
                if sample:return {'op':'use','item':obj['id'],'method':'golpear','target':sample}
            if form=='punta' and uses.get('excavar'):
                if any(valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z) in '^#o' for dx,dy in DIRS):
                    return {'op':'use','item':obj['id'],'method':'excavar','target':'roca'}
            if form=='filo' and uses.get('cortar'):
                if any(valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z)=='T' for dx,dy in DIRS):
                    return {'op':'use','item':obj['id'],'method':'cortar','target':'árbol'}
            if form=='palanca' and uses.get('mover'):
                if any(valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z)=='^' for dx,dy in DIRS):
                    return {'op':'use','item':obj['id'],'method':'mover','target':'roca'}
            if form=='recipiente' and uses.get('contener'):
                if z==0 and any(valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z)=='~' for dx,dy in DIRS):
                    return {'op':'use','item':obj['id'],'method':'llenar','target':'agua'}
                sample=next((m for m,n in inv.items() if n>0 and m in p['materials']),None)
                if sample:return {'op':'use','item':obj['id'],'method':'contener','target':sample}
        return None

    def plan_ready(self,decision,source,tokens=None):
        p=self.s['person'];p['routine_since_llm']=0
        if p.get('unconscious'):return  # Ignorar una deliberación tardía mientras está inconsciente.
        # Registrar el estado inmediatamente ANTERIOR a procesar la decisión.
        # El checkpoint es técnico: nunca se inyecta en la memoria del LLM.
        if getattr(self, 'timeline_capture_enabled', True):
            try:
                self.timeline.record('decision',self.s,self.rng,source=source,
                                     decision=decision,engine_version=self.timeline_version)
            except (ValueError,TypeError,OverflowError,sqlite3.Error):
                pass  # Registrar historial no puede detener al personaje.
        current=p.get('project');saved=p.setdefault('projects',[])
        objective=decision['objetivo'] or 'Investigar el entorno'
        selected_id=decision.get('proyecto_id') or ''
        project_action=decision.get('accion_proyecto','nuevo')
        if project_action=='sin_proyecto':
            # Vivir, observar o descansar no crea un proyecto ficticio.
            # Un proyecto existente se conserva intacto; esta deliberación
            # no le atribuye avances que corresponden a otra actividad.
            p['plan']=self.validate_plan(self.improve_plan(decision['plan']))
            p['review_at_minutes']=p.get('clock_minutes',0)+decision.get('revisar_en_minutos',90)
            p['local_followups']=0
            self.s['last_reason']=decision.get('motivo','')
            if source=='llm':
                set_wait_preferences(p,decision.get('actividades_en_espera'),self.stamp())
                set_agenda(p,decision.get('agenda',[]),p['clock_minutes'],None)
            research_entry=None
            if decision.get('pregunta'):
                research_entry,_=register_research(
                    p,decision['pregunta'],decision.get('hipotesis',''),
                    self.stamp(),str(uuid.uuid4())[:8])
                p['research']=p['research'][-75:]
            note=self.journal(decision['cuaderno'],decision.get('pregunta',''),
                              decision.get('hipotesis',''),source,
                              linked={'research_id':research_entry.get('id') if research_entry else None})
            for action in p['plan']:
                if action.get('_origin') not in ('agenda','espera','rutina','motor'):
                    action['_journal_id']=note['id']
            if tokens:self.s['last_tokens']=tokens
            self.write()
            return
        if project_action=='nuevo':selected_id=''  # Un proyecto nuevo jamás reutiliza un ID anterior.
        chosen=None
        if selected_id and current and selected_id==current.get('id'):chosen=current
        if selected_id and not chosen:
            found=next((r for r in saved if r.get('id')==selected_id and r.get('status')!='terminado'),None)
            if found:
                saved.remove(found);chosen=found
        if not chosen and current and (project_action=='continuar' or (project_action!='nuevo' and difflib.SequenceMatcher(None,current.get('title','').lower(),objective.lower()).ratio()>.82)):
            chosen=current
        proof=decision.get('prueba_cierre','').strip()
        closure=completion_evidence(chosen or current,proof,p)
        proof_ok=bool(closure)
        # Terminar, abandonar y pausar son decisiones diferentes; no crear un
        # proyecto idéntico después de cerrar uno durante la misma deliberación.
        if project_action in ('completar','abandonar','pausar'):
            target=chosen or current
            if project_action=='completar' and not proof_ok:
                from goal_evidence import check_goal
                valid_goal,goal_ids,reason=check_goal(target,p,proof) if target else (False,[],'No hay proyecto activo.')
                if valid_goal:
                    reason=('El objetivo tiene mediciones pertinentes, pero la prueba de cierre '
                            'no cita una de ellas. ID verificable: '+', '.join(goal_ids[:5])+'.')
                closure_fields={}
                if not getattr(self,'historical_replay',False):
                    diagnosis=closure_diagnostic(target,p,proof)
                    closure_fields={'estado_verificacion':diagnosis['estado'],
                                    'ids_evidencia_pertinente':diagnosis['ids_evidencia'][:6],
                                    'limitacion_fisica':(diagnosis['motivo']
                                        if diagnosis['estado']=='criterio_no_instrumentado' else None)}
                p['last_closure_rejection']={
                    **closure_fields,
                    'project_id':(target or {}).get('id'),
                    'objective':(target or {}).get('title'),
                    'reason':reason,'when':self.stamp(),
                    'not_a_completed_goal':True,
                    'next_options':(['reformular el objetivo hacia una propiedad medible',
                                      'pausar','abandonar']
                                     if closure_fields.get('estado_verificacion')=='criterio_no_instrumentado'
                                     else ['continuar con una evidencia pertinente','pausar','abandonar'])}
                self.event(['No puedo declarar el objetivo cumplido: '+reason+
                            ' Puedo continuar, pausarlo o abandonarlo sin simular un éxito.'],
                           'evaluación')
                if current:chosen=current
            elif target is not None:
                status={'completar':'terminado','abandonar':'abandonado',
                        'pausar':'pausado'}[project_action]
                if status=='pausado' and source=='llm':
                    # Los recordatorios pueden mantenerse activos al suspender
                    # una investigacion. No ejecutan tareas sin consentimiento.
                    reminders=[a for a in decision.get('agenda',[])
                               if isinstance(a,dict) and a.get('modo')=='recordatorio']
                    registered=set_agenda(p,reminders,p['clock_minutes'],target.get('id'))
                    if registered:self.event([f'Deje {len(registered)} recordatorio(s) para reconsiderar este proyecto al cumplirse sus condiciones.'],'agenda')
                retire_project(p,target,status,self.stamp(),
                               reason=decision.get('estado_actual') or decision.get('motivo'),
                               evidence=closure if status=='terminado' else None)
                p['plan']=[]
                p['review_at_minutes']=p.get('clock_minutes',0)
                p['local_followups']=0
                p['active_research']=None
                if source=='llm':
                    set_wait_preferences(p,[],self.stamp())
                message=(
                    'Di por terminado el proyecto con la evidencia registrada: '
                    if status=='terminado' else
                    'Decidí abandonar esta investigación sin declarar el objetivo cumplido: '
                    if status=='abandonado' else
                    'Decidí pausar la investigación y conservar sus resultados: '
                )+target.get('title','Proyecto')
                self.event([message],'decision',True)
                self.write()
                return
            else:
                self.event(['No hay un proyecto identificado para cerrar o pausar.'],
                           'evaluación')
                p['plan']=[]
                self.write()
                return
        if chosen is None:
            # Al abrir un proyecto similar a otro pausado, conservar el motivo
            # anterior. No bloquear la decisión de retomarlo ni inventar un éxito.
            from cognition import same_research
            precedent=next((old for old in reversed(saved)
                if old.get('status') in ('pausado','abandonado')
                and same_research(old.get('title',''),objective)),None)
            if current and current.get('status')!='terminado':
                current['status']='pausado';current['state']=current.get('state') or 'Pendiente de retomar'
                if current not in saved:saved.append(current)
            chosen={'id':str(uuid.uuid4())[:8],'title':objective,'reason':decision['motivo'],
                    'started':self.stamp(),'source':source,'status':'activo','progress':0,
                    'steps_done':0,'failed_actions':0,'no_progress_steps':0,'verified_results':[],'subgoals':[],
                    'deliberations':0,'deliberations_since_progress':0,
                    'state':decision.get('estado_actual') or 'Definiendo los siguientes pasos'}
            if precedent:
                chosen['antecedente_pausado']={
                    'id':precedent.get('id'),'titulo':precedent.get('title'),
                    'estado':precedent.get('status'),
                    'motivo':precedent.get('closure_reason'),
                    'acciones_sin_avance':precedent.get('no_progress_steps',0)}
                self.remember_strategy(
                    'Este tema se parece a una investigación antes suspendida: '
                    +str(precedent.get('title',''))[:95]+'. Revisar sus evidencias '
                    'y motivo antes de considerar nueva una prueba repetida.')
            self.event([f"Me propuse: {chosen['title']}"],'decision',True)
        else:
            if chosen.get('status')=='pausado':
                for task in p.get('agenda',[]):
                    if (task.get('proyecto_id')==chosen.get('id')
                            and task.get('ultimo_motivo')=='Proyecto pausado'
                            and task.get('estado')=='pospuesta'):
                        task['reanudar_minuto']=p.get('clock_minutes',0)
                        task['ultimo_motivo']='Proyecto retomado'
            acknowledge_reminders(p,chosen.get('id'),self.stamp())
            chosen['status']='activo';chosen['reason']=decision['motivo'] or chosen.get('reason','')
            chosen['state']=decision.get('estado_actual') or chosen.get('state','Continuando la investigación')
            self.event([f"Retomé el proyecto: {chosen['title']}"],'decision')
        # El porcentaje lo estima el personaje; se presenta como estimación, nunca verificación automática.
        chosen['progress']=min(95,max(0,int(decision.get('avance_estimado',0))))
        chosen['deliberations']=chosen.get('deliberations',0)+1
        chosen['deliberations_since_progress']=chosen.get('deliberations_since_progress',0)+1
        if project_needs_review(chosen):
            chosen['reconsideration_required']=True
            chosen['state']='Objetivo prolongado sin nuevos resultados: revisar si conviene continuar, pausar o cambiar de proyecto.'
            self.remember_strategy('Este proyecto lleva varias deliberaciones sin avances materiales. Elegí explícitamente continuar, iniciar otro o completar SOLO con evidencias.')
        if decision.get('subobjetivos'):
            chosen['subgoals']=decision['subobjetivos'][:6]
        chosen['updated']=self.stamp()
        chosen['reconsideration_required']=bool(chosen.get('reconsideration_required') and project_needs_review(chosen))
        p['project']=chosen;p['plan']=self.validate_plan(self.improve_plan(decision['plan']))
        if not p['plan']:
            self.event(['El plan del modelo quedó sin pasos verificables; necesito reconsiderar.'], 'evaluación')
        # Guardar intenciones para la próxima espera. Solo el LLM modifica preferencias.
        if source=="llm":
            set_wait_preferences(p,decision.get("actividades_en_espera"),self.stamp())
            added=set_agenda(p,decision.get('agenda',[]),p['clock_minutes'],chosen.get('id'))
            if added:self.event([f'Preparé {len(added)} tarea(s) para ejecutar más adelante, si se cumplen las condiciones.'],'decisión')
        # Si ya se comprobó el estancamiento de un método, no aceptar una nueva
        # variante de la misma operación sin cambio de estrategia real.
        blocked=chosen.get('estrategia_bloqueada')
        # Los bloqueos por nombre de operación eran demasiado generales:
        # 'explore' puede probar fronteras distintas y 'use' objetos distintos.
        # Se conservan solo durante replays históricos. En reglas vigentes
        # Nilo recibe evidencia de repetición pero conserva sus decisiones.
        legacy_replay=getattr(self,'legacy_replay_rules',False)
        historical_replay=getattr(self,'historical_replay',False)
        if not legacy_replay and not historical_replay and blocked:
            chosen.pop('estrategia_bloqueada',None)
        if (legacy_replay or historical_replay) and blocked and p['plan']:
            physical=[s for s in p['plan'] if s.get('op') not in ('write','rest','eat','drink')]
            same=physical and all(s.get('op') in blocked.get('operations',[]) for s in physical)
            if same:
                chosen['reconsideration_required']=True
                self.event(['La propuesta insiste en el método agotado sin ofrecer una alternativa. Reconsideraré la investigación.'],'evaluación')
                p['plan']=[]
                if p['pos'][2]==-1 and p['needs']['hidratacion']<60:
                    from world import known_exit_route
                    if known_exit_route(self.s['world'],p) is not None:
                        p['plan']=[{'op':'ascend'}]
                if not p['plan']:
                    self.s['next_deliberation_real']=time.time()+120
        # Dos planes idénticos sin cambio de conocimiento ni terreno son una señal
        # objetiva de bucle, aunque el LLM cambie la redacción del cuaderno.
        sig=json.dumps(p['plan'],sort_keys=True,ensure_ascii=False)
        outcome=(len(p['knowledge']),len(self.s['world']['revealed']),
                 sum(self.s['world'].get('excavation',{}).values()))
        history=p.setdefault('decision_history',[])
        # Los replays antiguos mantienen su huella histórica exacta.
        legacy_replay=getattr(self,'legacy_replay_rules',False)
        semantic=''
        evidence=None
        if not legacy_replay:
            # Una señal sobre deliberaciones equivalentes, sin veto de acciones.
            semantic=semantic_signature(p,p['plan'])
            evidence=evidence_snapshot(p,self.s['world'])
            energy=p.get('needs',{}).get('energia')
            signal=detect_repetition(
                history,semantic,evidence,chosen.get('id'),
                rest_energy=energy if isinstance(energy,(int,float)) else None)
            previous=p.get('strategy_review')
            if signal:
                p['strategy_review']=signal
                if not previous or previous.get('plan_signature')!=signal['plan_signature']:
                    self.event(['Observé una reiteración de estrategia sin evidencia nueva: '
                                +signal['resumen']+
                                ' Puedo mantenerla si tengo fundamentos o reconsiderarla.'],
                               'evaluación')
            else:
                p.pop('strategy_review',None)
        duplicate=bool(history and history[-1].get('signature')==sig and
                       tuple(history[-1].get('outcome',[]))==outcome)
        if duplicate and p['plan']!=[{'op':'explore'}] and (legacy_replay or historical_replay):
            self.remember_strategy('El bloque nuevo repetía exactamente otro plan sin cambios comprobables; necesito investigar otra posibilidad.')
            # Repetir exploración genérica no constituye una estrategia diferente.
            p['plan']=[]
            chosen['reconsideration_required']=True
            self.s['next_deliberation_real']=time.time()+120
            self.event(['Descarté un plan idéntico al anterior sin avances y voy a explorar otra posibilidad.'],'evaluación')
        entry={'signature':sig,'outcome':list(outcome)}
        if not legacy_replay:
            entry.update({'semantic_signature':semantic,'evidence_snapshot':evidence,
                          'project_id':chosen.get('id')})
        history.append(entry)
        del history[:-12]
        if duplicate and not legacy_replay and not historical_replay and p['plan']!=[{'op':'explore'}]:
            chosen['reconsideration_required']=True
            self.remember_strategy(
                'El plan repite el bloque anterior sin evidencia nueva; revisá si cambiaron las condiciones antes de insistir.')
            self.event(['El bloque propuesto coincide con el anterior sin nuevos resultados comprobados. Puedo reconsiderarlo o mantenerlo si hay razones.'],'evaluación')
        p['review_at_minutes']=p['clock_minutes']+decision.get('revisar_en_minutos',90)
        p['local_followups']=0
        self.s['last_reason']=decision['motivo']
        research_entry=None
        if decision.get('pregunta'):
            subject=research_topic(' '.join((decision['pregunta'],decision.get('hipotesis',''),objective)))
            resolved=next((c for c in p.get('conclusions',[]) if c.get('topic')==subject and c.get('status')=='comprobada'),None) if subject else None
            if resolved:
                self.remember_strategy('Investigación resuelta por mediciones: '+resolved['text']+' No repetirla salvo nuevo material, método o condición.')
                chosen['reconsideration_required']=True
                chosen['state']='Investigación ya comprobada: '+resolved['text']
            else:
                research_entry,_=register_research(p,decision['pregunta'],decision['hipotesis'],self.stamp(),str(uuid.uuid4())[:8])
                p['research']=p['research'][-75:]
        note=self.journal(decision['cuaderno'],decision['pregunta'],decision['hipotesis'],source,
            linked={'project_id':chosen.get('id'),
                    'research_id':research_entry.get('id') if research_entry else None})
        # Solo el plan de esta deliberación procede de esta entrada. La agenda,
        # los hábitos y las acciones automáticas NO se atribuyen al cuaderno.
        for action in p['plan']:
            if action.get('_origin') not in ('agenda','espera','rutina','motor'):
                action['_journal_id']=note['id']
        if tokens:self.s['last_tokens']=tokens
        saved[:]=saved[-55:]
        self.write()

    def think(self):
        cfg=config();mode='llm' if available(cfg) else 'demo'
        signature=routing_signature(cfg)
        with self.lock:
            if self.s.get('routing_signature')!=signature:
                # Si cambian la clave o los modelos, no conservar una espera
                # calculada para la configuración anterior. Los bloqueos de
                # cada modelo siguen vigentes por separado en provider_health.
                self.s['routing_signature']=signature
                if self.s.get('mode')=='espera':
                    self.s['next_deliberation_real']=0
            if self.s.get('planning') or self.s['person'].get('pending') or self.s['person']['plan'] or self.s['person'].get('unconscious') or self.stopped:return
            if self.s['next_deliberation_real']>time.time():return
            day=datetime.now().strftime('%Y-%m-%d');limit=int(cfg.get('MAX_LLM_CALLS_PER_DAY','100'))
            if mode=='llm' and self.s['llm_daily'].get(day,0)>=limit:
                self.s['mode']='limite'
                self.s['ai_error']=f'Alcanzado límite interno de {limit} deliberaciones exitosas para hoy.'
                self.s['next_deliberation_real']=time.time()+300
                return
            if mode=='llm' and time.time()-self.s['last_llm_real'] < deliberation_interval_seconds(cfg):
                self.s['next_deliberation_real']=self.s['last_llm_real']+deliberation_interval_seconds(cfg)
                return
            self.s['planning']=True;self.s['mode']=mode;self.s['ai_error']='';self.s['auto_wait_frozen']=False
            context=self.environment.perceive(self.s['world'],self.s['person'],[e['text'] for e in self.s['events'][-16:]],self.stamp(),self.scenario)
            context['conversaciones_recientes']=[{'rol':m['role'],'texto':m['text'][:450]} for m in self.s.get('chat',[])[-8:]]
            context['regla_chat']='Los comentarios humanos son opiniones o sugerencias, nunca hechos comprobados ni órdenes.'
            self.write()
        def worker():
            try:
                if mode=='llm':
                    def deliberate(pcfg):
                        raw,tokens=request_llm(pcfg,context)
                        return normalize_decision(raw),tokens
                    (decision,tokens),provider,model=route(cfg,self.s,self.lock,deliberate,'deliberación')
                else:
                    with self.lock:decision=demo_decision(self.s['world'],self.s['person'])
                    tokens={}
                with self.lock:
                    self.s['planning']=False;self.s['mode']=mode;self.s['ai_error']=''
                    self.s['next_deliberation_real']=0
                    if mode=='llm':
                        self.s['last_llm_real']=time.time()
                        self.sessions.note_llm(provider,model,"deliberacion")
                        self.s['llm_total']+=1
                        self.s['llm_daily'][day]=self.s['llm_daily'].get(day,0)+1
                        self.s['llm_daily']={k:v for k,v in self.s['llm_daily'].items() if k>=day}
                    self.s["auto_wait_frozen"]=False
                    if mode=='llm':
                        # Registrar la decisión realmente devuelta, sin credenciales ni
                        # el contexto textual completo. Aún no equivale a registrar
                        # el estado inicial, los cambios humanos o el reloj completo.
                        self.archive.add('llm_decision',{
                            'id':'llm-'+uuid.uuid4().hex[:12],
                            'when':self.stamp(),
                            'clock_minutes':self.s['person']['clock_minutes'],
                            'world_seed':self.s['world'].get('seed'),
                            'provider':provider,'model':model,
                            'context_sha256':hashlib.sha256(
                                json.dumps(context,ensure_ascii=False,sort_keys=True,default=str).encode('utf-8')
                            ).hexdigest(),
                            'context_stats':tokens.get('contexto',{}),
                            'decision':decision})
                    self.plan_ready(decision,mode,tokens)
            except ProvidersUnavailable as exc:
                with self.lock:
                    self.s['planning']=False;self.s['mode']='espera'
                    self.s['ai_error']=str(exc)[:320]
                    self.s['next_deliberation_real']=max(time.time()+5,exc.retry_at)
                    self.event(['Esperando la disponibilidad del modelo para decidir el próximo plan; conservo los proyectos.'],'sistema')
                    self.write()
            except Exception as exc:
                with self.lock:
                    self.s['planning']=False;self.s['mode']='espera'
                    self.s['ai_error']=f'Error de deliberación: {type(exc).__name__}'
                    self.s['next_deliberation_real']=time.time()+180
                    self.event(['Error inesperado al deliberar. Próximo intento dentro de 3 minutos.'],'sistema')
                    self.write()
        threading.Thread(target=worker,name='NiloDeliberation',daemon=True).start()

    def retry_llm(self):
        """Solicitud manual prudente: nunca evade límites 429, cuota ni temporizador real."""
        cfg=config();now=time.time()
        with self.lock:
            if self.s.get('planning') or self.s['person'].get('pending') or self.s['person'].get('unconscious'):
                return {'ok':False,'reason':'Hay una acción, una consulta o un estado inconsciente en curso.'}
            day=datetime.now().strftime('%Y-%m-%d')
            if self.s['llm_daily'].get(day,0)>=int(cfg.get('MAX_LLM_CALLS_PER_DAY','100')):
                return {'ok':False,'reason':'Límite interno diario alcanzado.'}
            minimum=deliberation_interval_seconds(cfg)
            if now-self.s.get('last_llm_real',0)<minimum:
                return {'ok':False,'reason':'Intervalo mínimo entre deliberaciones aún vigente.'}
            routing=public_info(cfg,self.s)
            valid=[]
            for provider in routing.get('providers',[]):
                name=provider['name'];health_key=provider.get('health_key',name)
                h=self.s.get('provider_health',{}).get(health_key,{})
                if h.get('last_status') in (401,403,413,429) and h.get('cooldown_until',0)>now:
                    continue
                if h.get('cooldown_until',0)>now and h.get('last_status') in (500,502,503,504,0):
                    h['cooldown_until']=0
                if h.get('cooldown_until',0)<=now:valid.append(name)
            if not valid:
                return {'ok':False,'reason':'Los proveedores todavía están bloqueados por cuota o autorización.'}
            self.s['next_deliberation_real']=0
            self.s['auto_wait_frozen']=False
            self.write()
        self.think()
        return {'ok':True,'reason':'Se solicitó una nueva deliberación a un proveedor disponible.'}

    def tick(self,real_elapsed):
        """Subpasos acotados: evitar saltar acciones al acelerar ×300/×600.

        Cada subpaso transcurre como máximo un minuto de reloj simulado y se
        interrumpe exactamente cuando termina una acción en curso.
        """
        remaining=max(0.0,min(float(real_elapsed),20.0))
        if remaining<=0:
            self._tick_slice(0.0)
            return
        for _ in range(1000):
            if remaining<=1e-9:
                break
            with self.lock:
                if self.stopped or self.s.get('paused') or self.s.get('auto_wait_frozen'):
                    chunk=0.0
                else:
                    pending=self.s['person'].get('pending')
                    rate=effective_speed(self.s['speed'],pending,
                                         planning=bool(self.s.get('planning')))
                    chunk=min(remaining,60.0/max(1.0,rate))
                    if pending and pending.get('step',{}).get('op')=='write':
                        left=float(pending.get('remaining_real',0))
                        if left>1e-8:
                            chunk=min(chunk,left/max(1.0,rate))
                    elif pending:
                        left=float(pending.get('remaining',0))
                        if left>1e-8:
                            chunk=min(chunk,left*60.0/max(1.0,rate))
            if chunk<=1e-9:
                self._tick_slice(0.0)
                break
            self._tick_slice(chunk)
            remaining-=chunk
        else:
            raise RuntimeError('Límite de subpasos temporales excedido')

    def _tick_slice(self,real_elapsed):
        if self.s.get('auto_wait_frozen'):
            # Congelar solo el tiempo simulado; reintentar LLM según hora real.
            if self.s.get('next_deliberation_real',0)<=time.time():
                self.think()
            return
        with self.lock:
            if self.stopped or self.s['paused']:return
            p=self.s['person'];elapsed=max(0,min(real_elapsed,20))
            pending=p.get('pending')
            writing=pending and pending.get('step',{}).get('op')=='write'
            if writing:
                simulated_seconds, writing_remaining=writing_tick(
                    elapsed,pending.get('remaining_real',0),self.s['speed'])
                delta=simulated_seconds/60
            else:
                delta=elapsed*effective_speed(self.s['speed'],pending,
                                              planning=bool(self.s.get('planning')))/60
            p['clock_minutes']+=delta
            # La topología y los criterios de refugio pertenecen al entorno.
            shelter,near_water=self.environment.surroundings(self.s['world'],p)
            for routine in update_needs(p,self.s['world'],delta,shelter,near_water,active=bool(pending and pending.get('step',{}).get('op') not in ('rest','wait')),
                                        resting=bool((pending and pending.get('step',{}).get('op')=='rest') or p.get('unconscious')),
                                        legacy_energy_cap=getattr(self,'legacy_replay_rules',False),
                                        legacy_autocare=(getattr(self,'legacy_replay_rules',False) or getattr(self,'legacy_autocare_rules',False))):
                self.event([routine],'autocuidado',False)
            # El colapso es fisiológico. No se interpreta como una decisión de descansar.
            if not (getattr(self,'legacy_replay_rules',False) or getattr(self,'legacy_autocare_rules',False)):
                energy=ensure_needs(p)['energia']
                if not p.get('unconscious') and energy<=5:
                    interrupted=p.get('pending')
                    p['unconscious']=True
                    p['collapsed_at']=self.stamp()
                    p['interrupted_by_collapse']=({
                        'op':interrupted['step']['op'],
                        'elapsed_minutes':round(
                            interrupted.get('total',0)-interrupted.get('remaining',0),3),
                        'when':self.stamp(),
                        'origin':interrupted['step'].get('_origin','llm')}
                        if interrupted else None)
                    if interrupted and interrupted['step'].get('_agenda_id'):
                        for task in p.get('agenda',[]):
                            if task.get('id')==interrupted['step']['_agenda_id']:
                                task['estado']='pospuesta'
                                task['ultimo_motivo']='Acción interrumpida por pérdida de conciencia'
                    p['pending']=None
                    p['plan']=[]
                    self.s['auto_wait_frozen']=False
                    self.event(['Perdí el conocimiento por agotamiento extremo; la actividad quedó interrumpida.'],'estado',True)
                elif p.get('unconscious') and energy>=40:
                    p['unconscious']=False
                    p['recovered_at']=self.stamp()
                    self.event(['Recuperé el conocimiento y puedo decidir nuevamente.'],'estado',True)
                if p.get('unconscious'):
                    if time.monotonic()-self.last_persist>=5:self.write()
                    return
            pending=p.get('pending')
            for reminder in awaken_reminders(p,self.stamp()):
                self.event(['Se cumplio mi condicion para reconsiderar: '+reminder['titulo']
                            +'. Puedo retomar el proyecto cuando lo decida.'],'agenda',True)

            if pending:
                if writing:
                    pending['remaining_real']=writing_remaining
                    pending['remaining']=writing_remaining/60
                    if pending['remaining_real']<=0:
                        p['pending']=None
                        self.event(['Terminé de escribir una entrada en mi cuaderno.'],'cuaderno')
                else:
                    pending['remaining']=max(0,pending['remaining']-delta)
                    nav=pending.get('navigation')
                    if nav:
                        elapsed_world=pending['total']-pending['remaining']
                        due=int((elapsed_world+1e-7)/pending.get('travel_minutes_per_tile',TRAVEL_MINUTES_PER_TILE))
                        self.environment.move_navigation(self.s['world'],p,nav,due)
                    if pending['remaining']<=0 or (nav and nav.get('blocked')):
                        step=pending['step'];p['pending']=None
                        w=self.s['world']
                        before=(len(p.get('items',[])),len(w['structures']),len(p['knowledge']),len(w['revealed']),
                                sum(w.get('excavation',{}).values()), tuple(p['pos']),
                                tuple(sorted(p['inventory'].items())))
                        old_inventory=dict(p["inventory"])
                        contract_prior=contract_before(w,p,step)
                        action_result=None
                        if nav:
                            facts,success,notable=self.environment.finish_navigation(nav,p)
                            if success and nav.get('kind')=='ascend':
                                ascent_result=self.environment.perform_result(w,p,step,self.rng)
                                _,ascent_facts,ascent_ok,ascent_notable=ascent_result.as_legacy()
                                facts.extend(ascent_facts);success=ascent_ok;notable=notable or ascent_notable
                            elif nav.get('kind')=='gather':
                                # La navegación solo acredita un desplazamiento.
                                # La operación gather se considera exitosa únicamente
                                # si efectivamente extrae el material solicitado.
                                arrived=(success and
                                         tuple(p['pos'][:2])==tuple(nav['destination']))
                                if arrived:
                                    harvested=self.environment.perform_result(w,p,step,self.rng)
                                    _,harvest_facts,success,harvest_notable=harvested.as_legacy()
                                    facts.extend(harvest_facts)
                                    notable=notable or harvest_notable
                                    action_result=ActionResult.from_legacy(
                                        step,facts,success,notable,
                                        physical=harvested.physical)
                                else:
                                    success=False
                                    facts.append('No completé la extracción: '
                                                 'el inventario no ganó el material solicitado.')
                        elif step.get('op')=='design':
                            success,message=register_design(p,step,self.stamp())
                            facts=[message];notable=success
                        elif step.get('op')=='propose':
                            success,message=submit_proposal(p,step,self.stamp(),
                                ('flotacion','contencion','excavacion','impacto'))
                            facts=[message];notable=success
                        elif step.get('op')=='report_issue':
                            success,message=submit_debug_report(p,step,self.stamp())
                            facts=[message];notable=success
                        elif step.get('op')=='compare':
                            success,description,entry=compare_physical(p,step,self.stamp())
                            facts=[description];notable=bool(success)
                            if entry:
                                subject=str(step.get('topic') or '').strip()[:150]
                                if subject:
                                    entry['label']=subject
                                    from cognition import same_research
                                    for investigation in p.get('research',[]):
                                        if investigation.get('state')=='abierta' and same_research(investigation.get('question',''),subject):
                                            investigation['state']='documentada'
                                            investigation['conclusion']=entry['text']
                                            investigation['evidence_ids']=entry['evidence_ids']
                                            investigation['closed']=entry['when']
                                            if p.get('active_research')==investigation.get('question'):
                                                p['active_research']=None
                                self.archive.add('conclusion',entry)
                                self.event(['Comparación de ensayos medidos: '+description],'evaluación',True)
                        elif step.get('op')=='conclude':
                            # Se admite una conclusión de hechos medidos, nunca una verdad
                            # causal nueva que el LLM inventa: resolver se basa en datos.
                            label=str(step.get('topic') or step.get('target') or '')
                            success,description,entry=observational_conclusion(p,step,self.stamp())
                            facts=[description];notable=False
                            if entry:
                                self.archive.add('conclusion',entry)
                                # Documentar no equivale a demostrar la hipótesis general.
                                from cognition import same_research
                                for r in p.get('research',[]):
                                    if r.get('state')=='abierta' and same_research(r.get('question',''),entry['label']):
                                        r['state']='documentada';r['conclusion']=entry['text'];r['evidence_ids']=entry['evidence_ids'];r['closed']=entry['when']
                                        if p.get('active_research')==r.get('question'):p['active_research']=None
                        else:
                            action_result=self.environment.perform_result(w,p,step,self.rng)
                            duration,facts,success,notable=action_result.as_legacy()
                        if action_result is None:
                            # Navegación, diseño y tareas documentales todavía usan
                            # sus motores específicos, pero comparten el contrato.
                            action_result=ActionResult.from_legacy(step,facts,success,notable)
                        start=pending.get('measurement_start')
                        measurement=measure(p,step,start,capture(w,p),facts,success,self.stamp(),
                                            action_result=action_result)
                        if measurement:
                            if not getattr(self,'legacy_replay_rules',False):
                                measurement['entity_links']=entities_for_action(
                                    pending.get('physical_entities_start'),w,p,step,measurement)
                            if isinstance(step.get('_journal_id'),str):
                                measurement['journal_id']=step['_journal_id']
                                project_id=(p.get('project') or {}).get('id')
                                if project_id:measurement['project_id']=project_id
                            self.archive.add('measurement',measurement)
                            if step.get('op')=='rest':
                                if measurement.get('rest_comparable'):
                                    facts.append('Medí energía: %.2f → %.2f en %.1f minutos (%+.2f puntos/hora), %s.' % (
                                        start['needs']['energia'],measurement['end']['needs']['energia'],
                                        measurement['duration_minutes'],measurement['energy_per_hour'],measurement['condition']))
                                else:
                                    facts.append(
                                        'Descanso registrado sin comparación válida (energía cercana al límite de recuperación o condiciones no controladas).'
                                        if getattr(self,'legacy_replay_rules',False)
                                        else 'Descanso registrado: variación de energía documentada, sin comparación experimental.'
                                    )
                                # El refugio sólo adquiere un estado funcional después
                                # de una medición, no al fabricarse ni por el nombre.
                                if (getattr(self,'legacy_replay_rules',False) and
                                        measurement.get('rest_comparable') and measurement['condition']=='refugio'):
                                    for home in w.get('structures',[]):
                                        if tuple(home.get('pos',[]))==tuple(measurement['start']['position']) and home.get('category')=='habitaculo':
                                            tests=home.setdefault('function_tests',[])
                                            if measurement['id'] not in tests:tests.append(measurement['id'])
                                            home['status']='Descanso observado; comparación pendiente'
                                # La comparación automática pertenece sólo al modelo histórico.
                                # Los nuevos mundos registran datos; Nilo debe decidir compararlos.
                                conclusion=(compare_rest(p,self.stamp())
                                    if getattr(self,'legacy_replay_rules',False) else None)
                                if conclusion:
                                    if conclusion['rates']['refugio']>conclusion['rates']['intemperie']:
                                        ref=next((m for m in p.get('measurements',[]) if m['id']==conclusion['evidence_ids'][0]),None)
                                        if ref:
                                            for home in w.get('structures',[]):
                                                if tuple(home.get('pos',[]))==tuple(ref['start']['position']) and home.get('category')=='habitaculo':
                                                    home['status']='Mejora de descanso comprobada (otras funciones pendientes)'
                                                    home['rest_evidence_ids']=conclusion['evidence_ids']
                                    self.archive.add('conclusion',conclusion)
                                    link_conclusion(p,conclusion)
                                    facts.append('Conclusión medida: '+conclusion['text'])
                                    self.event(['Finalicé la comparación de descanso con datos verificables: '+conclusion['text']],'decision',True)
                                    self.remember_strategy('No repetir comparación de descanso ya comprobada: '+conclusion['text'])
                        if step.get('op') in ('craft','build','use','excavate','assemble','modify','dismantle','rest'):
                            record_design_test(p,step,success,facts,self.stamp(),
                                measurement_id=measurement.get('id') if measurement else None,
                                measurement=measurement,world=w,notable=action_result.notable)
                        unmodeled=action_result.status=='no_evaluable'
                        if step.get('op') not in ('propose','report_issue','design'):
                            outcome=record_action_outcome(p,step,success,facts,self.stamp(),p['pos'])
                            if not (getattr(self,'historical_replay',False)
                                    or getattr(self,'legacy_replay_rules',False)):
                                # Metadatos observacionales, nunca órdenes a Nilo.
                                # No atribuir origen retroactivo a replays históricos.
                                outcome['origin']=step.get('_origin') or (
                                    'demo' if self.s.get('mode')=='demo' else 'llm')
                                outcome['project_id']=(p.get('project') or {}).get('id')
                                if nav and nav.get('kind')=='explore':
                                    outcome['exploration_trace']={
                                        'requested_direction':nav.get('requested_direction'),
                                        'requested_region':nav.get('requested_region'),
                                        'chosen_frontier':nav.get('destination'),
                                        'traveled_tiles':nav.get('walked',0),
                                        'discovered_tiles':len(nav.get('discovered',[])),
                                        'blocked':bool(nav.get('blocked')),
                                        'end_position':list(p['pos'])}
                            # Contrato numérico, independiente de la redacción de los mensajes.
                            if measurement:
                                outcome['physical_result']={
                                    'duration_minutes':measurement.get('duration_minutes'),
                                    'needs_delta':measurement.get('needs_delta',{}),
                                    'inventory_delta':measurement.get('inventory_delta',{}),
                                    'object_delta':measurement.get('object_delta',0),
                                    'structure_delta':measurement.get('structure_delta',0),
                                    'position_start':measurement.get('start',{}).get('position'),
                                    'position_end':measurement.get('end',{}).get('position'),
                                    'measurement_id':measurement.get('id')}
                            outcome['evaluation_status']=action_result.status
                            outcome['action_result']=action_result.to_record()
                            if unmodeled:
                                outcome['unmodeled_attempt_id']=p.get('unmodeled_attempts',[{}])[-1].get('id')
                            prediction_id=pending.get('prediction_id')
                            if prediction_id:
                                prediction=finish_prediction(
                                    p,prediction_id,action_result,self.stamp(),
                                    measurement_id=measurement.get('id') if measurement else None,
                                    action_id=outcome['id'],measurement=measurement)
                                if prediction:
                                    outcome['prediction_id']=prediction_id
                                    self.archive.add('prediction',prediction)
                            contract=classify_contract(w,p,step,contract_prior,action_result)
                            outcome.update({'contract_status':contract['status'],
                                'contract_code':contract['code'],
                                'contract_expected':contract['expected'],
                                'contract_observed':contract['observed']})
                            self.archive.add('diagnostic',outcome)
                            if contract['status']=='posible_error':
                                proposal=record_contract_issue(p,contract,outcome,self.stamp(),
                                    self.scenario.environment_id)
                                if proposal:
                                    self.archive.add('proposal',proposal)
                                    self.event(['El verificador encontró una posible contradicción operativa: '
                                        +proposal['title']+'. Queda pendiente de revisión.'],
                                        'evaluación',True)
                            integrity=inspect_invariants(w,p,action_result,p['pos'],
                                                         self.scenario.environment_id)
                            for issue in integrity:
                                proposal=record_invariant_issue(
                                    p,issue,outcome,self.stamp(),self.scenario.environment_id)
                                if proposal:
                                    self.archive.add('proposal',proposal)
                                    self.event([
                                        'El monitor detectó una posible anomalía del estado físico: '
                                        +proposal['title']+'. Solicitud '+proposal['id']
                                        +' pendiente de revisión.'
                                    ],'evaluación',True)
                        record_personal_experience(
                            p,step,success,notable,facts,self.stamp(),
                            position=p.get('pos'),
                            measurement_id=measurement.get('id') if measurement else None,
                            action_id=(outcome.get('id') if step.get('op') not in
                                       ('propose','report_issue','design') else None),
                            legacy=(getattr(self,'legacy_replay_rules',False)
                                    or getattr(self,'historical_replay',False)))
                        autonomous=step.get('_origin') in ('espera','rutina','agenda','motor')
                        key='routine_actions' if autonomous else 'deliberated_actions'
                        p.setdefault('autonomy_stats',{'routine_actions':0,'deliberated_actions':0})[key]+=1
                        if success and step.get('op') in ('forage','gather','drink','eat','rest'):
                            record_maintenance(p,step.get('op'),self.stamp(),step.get('target'),autonomous)
                        if step.get('_origin')=='agenda':
                            task=record_agenda_result(p,step,success,facts,self.stamp(),
                                legacy=(getattr(self,'legacy_replay_rules',False)
                                    or getattr(self,'historical_replay',False)))
                            self.event([('Terminé' if success else 'Suspendí')+' paso de mi agenda: '+task.get('titulo','')], 'agenda')
                            if success:record_skill(p,step,success,facts,self.stamp(),old_inventory)
                            if not success:p['plan']=[s for s in p['plan'] if s.get('_agenda_id')!=step.get('_agenda_id')]
                        elif autonomous:
                            record_wait_result(p,step,success,facts,self.stamp())
                        else:
                            record_skill(p,step,success,facts,self.stamp(),old_inventory)

                        after=(len(p.get('items',[])),len(w['structures']),len(p['knowledge']),len(w['revealed']),
                               sum(w.get('excavation',{}).values()), tuple(p['pos']),
                               tuple(sorted(p['inventory'].items())))
                        # El movimiento simple, la compra de materiales o el nombre de otra
                        # herramienta NO constituyen por sí solos conocimiento nuevo.
                        new_knowledge=after[2]>before[2]
                        tiles_new=discovered_during_action(
                            w,pending,before[3],
                            legacy=(getattr(self,'legacy_replay_rules',False)
                                    or getattr(self,'historical_replay',False)))
                        new_discovery=tiles_new>0
                        terrain_change=after[4]>before[4]
                        new_structure=after[1]>before[1]
                        new_material=any(v>0 and before_mat==0 for m,v in p['inventory'].items()
                            for before_mat in [dict(before[6]).get(m,0)])
                        new_tool=after[0]>before[0]
                        tool_novel=new_tool and any(
                            (it.get('form'),tuple(sorted(it.get('materials',[])))) not in
                            {(old.get('form'),tuple(sorted(old.get('materials',[])))) for old in p['items'][:-1]}
                            for it in p.get('items',[])[-1:])
                        observed=advance_evidence(
                            new_knowledge=new_knowledge, new_tiles=tiles_new,
                            terrain_change=terrain_change,new_structure=new_structure,
                            new_material=new_material,novel_tool=tool_novel,
                            useful_revision=(success and step.get('op') in ('modify','dismantle')))
                        progress=observed['progress']
                        if not getattr(self,'legacy_replay_rules',False) and not getattr(self,'historical_replay',False):
                            p['last_progress_evidence']={'when':self.stamp(),
                                'op':step.get('op'),'motivos':observed['reasons'],
                                'nuevas_casillas':tiles_new,
                                'proyecto_id':(p.get('project') or {}).get('id'),
                                'progreso':progress}
                        # Métricas observables, sin reconstrucción retroactiva de los históricos.
                        record_behavior(
                            p, op=step.get('op'), origin=step.get('_origin','llm'),
                            duration_minutes=measurement.get('duration_minutes') if measurement else None,
                            position_before=(start or {}).get('position',before[5]), position_after=after[5],
                            project_id=(p.get('project') or {}).get('id'),
                            new_tiles=len(w['revealed'])-pending.get('behavior_revealed_at_start',before[3]),
                            new_knowledge=after[2]-before[2],
                            new_materials=[name for name,qty in p['inventory'].items()
                                           if qty>0 and dict(before[6]).get(name,0)==0],
                            progress=progress)
                        self.event(facts,'resultado',notable)
                        project=p.get('project')
                        if project and step.get('_origin') not in ('espera','rutina'):
                            project['steps_done']=project.get('steps_done',0)+1
                            project['last_action']=self.describe_action(step)
                            project['last_result']='; '.join(facts)[:260]
                            project['updated']=self.stamp()
                            project.setdefault('verified_results',[])
                            if success and step.get('op') not in ('design','propose','report_issue','conclude','compare','manual','write'):
                                project['verified_results'].append({'when':self.stamp(),'action':step.get('op'),'result':facts[0][:230],
                                    'measurement_id':measurement.get('id') if measurement else None})
                                project['verified_results']=project['verified_results'][-30:]
                            elif not unmodeled:
                                project['failed_actions']=project.get('failed_actions',0)+1
                            if progress:
                                project['deliberations_since_progress']=0
                                project['no_progress_steps']=0
                                project['reconsideration_required']=False
                                project['estrategia_bloqueada']=None
                                if not getattr(self,'legacy_replay_rules',False) and not getattr(self,'historical_replay',False):
                                    project.pop('repeticion_operativa',None)
                                project.setdefault('verified_milestones',[]).append({
                                    'when':self.stamp(),'op':step.get('op'),'fact':facts[0][:230],
                                    'measurement_id':measurement.get('id') if measurement else None})
                                project['verified_milestones']=project['verified_milestones'][-50:]
                            elif (step.get('op')=='rest' and measurement and
                                  not measurement.get('rest_comparable') and
                                  any(t in (project.get('title','')+' '+str(p.get('active_research') or '')).casefold()
                                      for t in ('descans','repos','recuper','energía','energia'))):
                                # Una medición saturada de descanso no aporta evidencia
                                # al ensayo; esto NO veta descansos voluntarios.
                                project['no_progress_steps']=project.get('no_progress_steps',0)+1
                            elif step.get('op') in ('experiment','use','craft','build','combine','inspect','excavate'):
                                project['no_progress_steps']=project.get('no_progress_steps',0)+1
                            # La alerta no es sólo narrativa: lleva memoria de método,
                            # no se borra porque el LLM cambie la redacción.
                            if project['no_progress_steps']>=7:
                                attempts=p.setdefault('strategy_attempts',[])[-12:]
                                repetitive=repeated_methods(attempts,project.get('id'))
                                if repetitive:
                                    project['reconsideration_required']=True
                                    if getattr(self,'legacy_replay_rules',False) or getattr(self,'historical_replay',False):
                                        if not project.get('estrategia_bloqueada'):
                                            project['estrategia_bloqueada']={'operations':repetitive,'when':self.stamp(),
                                                'reason':'Insistencia sin avances comprobables en las últimas acciones'}
                                            p['plan']=[a for a in p['plan'] if a.get('op') not in repetitive]
                                            self.event(['Interrumpí una estrategia repetitiva sin resultados; debo reconsiderar un método o un objetivo diferente.'],'evaluación',True)
                                    else:
                                        previous=project.get('repeticion_operativa') or {}
                                        project['repeticion_operativa']={
                                            'operations':repetitive,'when':self.stamp(),
                                            'reason':'Operaciones repetidas sin progreso medido; no impide ensayar otra condición',
                                            'not_a_block':True}
                                        if previous.get('operations')!=repetitive:
                                            self.event(['Detecté operaciones reiteradas sin evidencia nueva. El aviso no cancela el plan; puedo decidir cambiar de método.'],'evaluación',True)
                            if project['no_progress_steps']>=4 and not project.get('reconsideration_required'):
                                project['reconsideration_required']=True
                                self.remember_strategy('Estancamiento comprobado: cuatro intentos sin conocimiento, terreno o capacidad nuevos. Considerar otro problema, contexto o método.')
                                self.event(['Mis ensayos no están generando resultados nuevos. Necesito reconsiderar la hipótesis o el objetivo.'],'evaluación',True)
                                # No descartar el resto del bloque: puede contener la prueba
                                # pertinente. El LLM recibe el diagnóstico al concluir.
                        p.setdefault('strategy_attempts',[]).append({'project_id':project.get('id') if project else None,
                            'op':step.get('op'),'progress':progress,'pos':list(p['pos']),
                            'at_minute':p['clock_minutes']})
                        p['strategy_attempts']=p['strategy_attempts'][-80:]
                        if p.get('active_research') and (notable or step.get('op') in ('experiment','build','craft','use','excavate','combine')):
                            line=next((r for r in reversed(p['research']) if r['question']==p['active_research']),None)
                            if line is not None:
                                line.setdefault('evidence',[]).append({'when':self.stamp(),'facts':facts[:3]})
                                line['evidence']=line['evidence'][-20:]
                        if not success or notable:self.s['last_reason']='; '.join(facts)[:150]
                        if not success:
                            self.remember_strategy((f"No evaluable por física ausente: {facts[0][:155]}" if unmodeled else f"Falló {self.describe_action(step)}: {facts[0][:155]}"))
                            # Solo se interrumpen los pasos dependientes del fallo. Un resultado
                            # inesperado no invalida los experimentos o exploraciones independientes.
                            if nav and nav.get('blocked'):
                                p['plan']=[]
                            elif step['op'] in ('craft','build'):
                                name=str(step.get('name','')).lower()
                                p['plan']=[a for a in p['plan'] if not (a.get('op')=='use' and name
                                      and name in str(a.get('item','')).lower())]
                            elif step['op']=='gather':
                                missing=str(step.get('target','')).lower()
                                p['plan']=[a for a in p['plan'] if not
                                    (a.get('op') in ('craft','build','combine') and missing in
                                     [str(v).lower() for v in a.get('materials',[])])]
                            elif step['op']=='use':
                                p['plan']=[a for a in p['plan'] if a != step]
                        # Los hallazgos se guardan y enriquecen la memoria; ya no destruyen
                        # un bloque coherente después de fabricar una herramienta.
            elif p['plan']:
                # Antes de consumir el paso, retener un estado restaurable.
                # Se guarda la acción AÚN en la cola para que el replay reproduzca
                # su ejecución por el mismo Simulation.tick.
                if getattr(self,'timeline_capture_enabled',True):
                    try:
                        self.timeline.record('action',self.s,self.rng,
                            source=p['plan'][0].get('_origin') or self.s.get('mode',''),
                            action=p['plan'][0],engine_version=self.timeline_version)
                    except (ValueError,TypeError,OverflowError,sqlite3.Error):
                        pass
                step=p['plan'].pop(0)
                op=step['op'];minutes=ACTION_DURATIONS[op]
                if op in ('rest','wait'):
                    if op=='rest' and getattr(self,'legacy_replay_rules',False) or getattr(self,'legacy_autocare_rules',False):
                        minutes=20
                    else:
                        # Los planes modernos se validan al recibirlos; no confiar
                        # en que una partida importada contenga solo pasos nuevos.
                        minutes=rest_minutes(step) or 30
                # Mismo factor de fatiga para esfuerzo estacionario y por tramo.
                n=ensure_needs(p)
                physical=op in ('go','explore','gather','forage','build','craft','assemble','excavate','modify','dismantle','interact')
                factor=fatigue_multiplier(n) if physical else 1.0
                minutes*=factor
                nav=self.environment.start_navigation(self.s['world'],p,step,self.rng)
                travel_tile=TRAVEL_MINUTES_PER_TILE*(1.0 if getattr(self,'legacy_replay_rules',False) else factor)
                if nav:
                    minutes=len(nav['route'])*travel_tile
                p['pending']={'step':step,'start':self.stamp(),'remaining':minutes,'total':minutes,
                              **({} if getattr(self,'legacy_replay_rules',False) else {'travel_minutes_per_tile':travel_tile}),
                              'measurement_start':capture(self.s['world'],p),
                              **({} if getattr(self,'legacy_replay_rules',False) else {'physical_entities_start':physical_snapshot(self.s['world'],p)}),
                              'behavior_revealed_at_start':len(self.s['world']['revealed'])}
                if nav:p['pending']['navigation']=nav
                prediction=begin_prediction(p,step,self.stamp())
                if prediction:
                    p['pending']['prediction_id']=prediction['id']
                    self.archive.add('prediction',prediction)
                self.event([f"Empecé: {self.describe_action(step)}"],'accion')
            # Ejecutar una tarea formulada previamente por Nilo, un paso cada vez.
            if not p['pending'] and not p['plan'] and not self.s.get('planning'):
                queued=choose_agenda_step(self.s['world'],p)
                if queued:
                    taskstep,task=queued
                    p['plan'].append(taskstep)
                    self.s['auto_wait_frozen']=False
                    self.event([f'Retomé una tarea diferida: {task["titulo"]}. Motivo: {taskstep.get("_reason","")}'],'agenda')
            if not p['pending'] and not p['plan'] and not self.s.get('planning'):
                followup=self.followup_without_llm()
                if followup:
                    p['plan'].append(dict(followup,_origin='motor',_reason='Verificación local de herramienta sin nuevo LLM'))
                    p['local_followups']=p.get('local_followups',0)+1
                    self.event(['El motor inició una verificación pendiente previamente permitida; no fue una nueva decisión del LLM.'],'sistema')
            # En las reglas actuales no hay acciones de espera sin delegación.
            if (not getattr(self,'legacy_replay_rules',False)
                    and not p['pending'] and not p['plan'] and not self.s.get('planning')
                    and p.get('waiting_preferences') and p.get('routine_since_llm',0)<2
                    and p['clock_minutes']-p.get('routine_last_minute',-1e6)>=18):
                selected=choose_wait_action(self.s['world'],p)
                if selected:
                    step,reason=selected
                    step=dict(step)
                    record_wait_selection(p,step)
                    p['plan'].append(dict(step,_origin='rutina',_reason=reason))
                    p['routine_since_llm']+=1
                    p['routine_last_minute']=p['clock_minutes']
                    self.event(['Ejecuté un procedimiento delegado: '+reason],'hábito')
            # Política previa, exclusivamente en reproducción histórica.
            if (getattr(self,'legacy_replay_rules',False)
                    and not p['pending'] and not p['plan'] and not self.s.get('planning')
                    and p.get('routine_since_llm',0)<2
                    and p['clock_minutes']-p.get('routine_last_minute',-1e6)>=18
                    and (p.get('pos',[0,0,0])[2]==-1 and p.get('needs',{}).get('hidratacion',100)<40 or
                         p.get('needs',{}).get('energia',100)<30 or
                         p.get('needs',{}).get('hidratacion',100)<30 or
                         (p.get('needs',{}).get('nutricion',100)<55 and p['inventory'].get('alimento',0)<1))):
                selected=choose_wait_action(self.s['world'],p,legacy_wait_policy=True)
                if selected and selected[0].get('op') in ('rest','forage','drink','go','ascend'):
                    step,reason=selected
                    p['plan'].append(dict(step,_origin='rutina',_reason=reason))
                    p['routine_since_llm']+=1
                    p['routine_last_minute']=p['clock_minutes']
                    self.event(['Apliqué un hábito aprendido: '+reason],'hábito')
            # Si la deliberación no está disponible, realizar tareas que Nilo ya
            # aprendió y ha elegido, sin explorar terreno desconocido ni inventar resultados.
            unavailable=available(config()) and (
                self.s.get('mode') in ('espera','limite')
                or self.s.get('next_deliberation_real',0)>time.time()+1)
            if (unavailable and not p['pending'] and not p['plan'] and not self.s.get('planning')
                    and p['clock_minutes']-p.get('waiting_last_minute',-10000)>=18):
                selected=choose_wait_action(self.s['world'],p,legacy_wait_policy=getattr(self,'legacy_replay_rules',False))
                if selected:
                    step,reason=selected
                    last_failed=p.get('waiting_last_failure',{}).get(step['op']+':'+str(step.get('target','')),-1e8)
                    if p['clock_minutes']-last_failed>=360:
                        step=dict(step,_origin='espera',_reason=reason)
                        if not getattr(self,'legacy_replay_rules',False):
                            record_wait_selection(p,step)
                        p['plan'].append(step)
                        p['waiting_last_minute']=p['clock_minutes']
                        p['waiting_state']={'kind':'ocupado','reason':reason,'when':self.stamp(), 'action':step['op']}
                        self.event([f'Mientras espero una nueva deliberación, decidí {self.describe_action(step).lower()}. Motivo: {reason}'], 'hábito')
                else:
                    status=p.get('waiting_state',{})
                    if status.get('kind')!='inactivo':
                        p['waiting_state']={'kind':'inactivo','when':self.stamp(),
                            'reason':'No tengo una actividad comprobada, útil y segura pendiente.'}
                        self.event(['Quedé sin actividades disponibles mientras espero otra deliberación.'],'hábito')
                    # Una tarea que debe activarse al transcurrir tiempo simulado
                    # cuenta como trabajo pendiente: no congelar su propio reloj.
                    future_clock=any(t.get('estado') in ('pendiente','pospuesta')
                        and t.get('cuando',{}).get('tipo')=='despues_de_minutos'
                        and p['clock_minutes']<t.get('creada_minuto',0)+t['cuando'].get('minutos',0)
                        for t in p.get('agenda',[]))
                    if (self.s.get('auto_pause_on_wait',True) and unavailable
                            and not p.get('pending') and not p.get('plan') and not future_clock):
                        self.s['auto_wait_frozen']=True
            elif not unavailable and p.get('waiting_state',{}).get('kind') in ('inactivo','ocupado'):
                p['waiting_state']={'kind':'normal','when':self.stamp()}
            if time.monotonic()-self.last_persist>=5:self.write()
            should_think=(not p['pending'] and not p['plan'] and not p.get('unconscious') and not self.s.get('planning'))
        if should_think:self.think()

    def describe_action(self,step):
        op=step['op']
        words={'write':'Escribir en el cuaderno','explore':'Explorar una zona desconocida','go':'Desplazarme','inspect':'Examinar','gather':'Recolectar','experiment':'Experimentar con','combine':'Combinar','build':'Construir','craft':'Fabricar herramienta','use':'Probar herramienta','excavate':'Excavar','descend':'Descender a la cueva','ascend':'Volver a la superficie','rest':'Descansar','wait':'Esperar sin descansar','forage':'Buscar alimentos','drink':'Beber agua','eat':'Comer','design':'Documentar invento','propose':'Solicitar ampliación física','assemble':'Armar mecanismo','modify':'Modificar objeto existente','dismantle':'Desmontar objeto','report_issue':'Presentar posible error','compare':'Comparar ensayos medidos'}
        suffix=step.get('target') or step.get('name') or ''
        if op=='explore' and ('direction' in step or 'region' in step):
            from world import EXPLORATION_DIRECTIONS,EXPLORATION_LABELS
            direction=EXPLORATION_DIRECTIONS.get(str(step.get('direction')).casefold().strip())
            suffix=('hacia el '+EXPLORATION_LABELS[direction]) if direction else ''
            if isinstance(step.get('region'),dict):
                reg=step['region'];suffix+=f" cerca de ({reg.get('x','?')}, {reg.get('y','?')})"
        if op=='go':suffix=('hacia el agua' if str(step.get('target','')).lower() in ('agua','orilla','costa','rio','río','lago')
                             else f"({step.get('x','?')}, {step.get('y','?')})")
        if op in ('combine','build','craft'):suffix=step.get('name') or ', '.join(map(str,step.get('materials',[])))
        if op=='wait':suffix=str(step.get('minutes',30))+' min'
        if op=='use':
            ref=step.get('item') or step.get('target') or ''
            # Las referencias siguen siendo IDs en el plan y en la física.
            # Solo la descripción destinada al observador usa el nombre.
            tool=next((obj for obj in self.s['person'].get('items',[])
                       if obj.get('id')==ref),None)
            display=(tool.get('name') if tool else None) or ref
            method=step.get('method') or ''
            suffix=str(display)+(' · '+str(method) if method else '')
        description=f"{words.get(op,op)} {suffix}".strip()
        label={'agenda':'[Agenda] ','espera':'[Hábito] ','rutina':'[Hábito] '}.get(step.get('_origin'),'')
        return label+description

    def start_chat(self,message):
        message=str(message).strip()
        if not message or len(message)>1000:raise ValueError('El mensaje debe tener entre 1 y 1000 caracteres.')
        cfg=config()
        if not available(cfg):raise ValueError('Configurá una API antes de conversar con Nilo.')
        with self.lock:
            if self.s.get('chatting'):raise ValueError('Nilo todavía está escribiendo su respuesta.')
            day=datetime.now().strftime('%Y-%m-%d')
            quota=max(0,int(cfg.get('MAX_CHAT_CALLS_PER_DAY','40')))
            if self.s['chat_daily'].get(day,0)>=quota:raise ValueError('Se alcanzó el límite de respuestas exitosas del chat para hoy.')
            self.s['chatting']=True;self.s['chat_error']=''
            self.s['chat'].append({'id':str(uuid.uuid4())[:8],'role':'user','text':message,'at':time.time()})
            self.archive.add('chat',self.s['chat'][-1])
            self.s['chat']=self.s['chat'][-80:]
            import copy
            context=self.environment.perceive(self.s['world'],self.s['person'],[e['text'] for e in self.s['events'][-30:]],self.stamp(),self.scenario)
            context['cuaderno']=self.s['journal'][-8:]
            context['mediciones_recientes']=[{'id':m['id'],'accion':m['op'],
                'duracion':m['duration_minutes'],'condicion':m['condition'],
                'cambios':m['needs_delta'],'comparacion_valida':m.get('rest_comparable',False)}
                for m in self.s['person'].get('measurements',[])[-12:]]
            context['conclusiones_comprobadas']=self.s['person'].get('conclusions',[])[-12:]
            if any(word in message.casefold() for word in ('descans','repos','refugio','energia','energía','sueño','dormir')):
                context['evaluacion_del_descanso']=closure_status(self.s['person'])
            context['evaluaciones_recientes']=[{'asunto':r.get('title') or r.get('phenomenon'),
                'tipo':r.get('type','physics'),'estado':r.get('status'),'decision':r.get('review')}
                for r in self.s['person'].get('proposals',[])[-12:] if r.get('review')]
            context['actividad_actual']=self.describe_action(self.s['person']['pending']['step']) if self.s['person'].get('pending') else 'Reflexionando'
            import re
            ask_catchup=bool(re.search(r'(qu[eé] me perd[ií]|qu[eé] pas[oó]|poneme al d[ií]a|resum[ií].*pendiente|qu[eé] hiciste desde|m[aá]s importante que te pas[oó])',message,re.I))
            continue_catchup=bool(self.s.get('catchup_offset',0) and re.search(r'^(segu[ií]|contin[uú]a|qu[eé] m[aá]s|el resto|seguimos)',message,re.I))
            catchup_offset=self.s.get('catchup_offset',0) if continue_catchup else 0
            page=None
            if ask_catchup or continue_catchup:
                page=self.catchup(offset=catchup_offset,limit=10)
                context['resumen_de_lo_no_leido']=page
                # Evitar mezclar anotaciones ya leídas con el período solicitado.
                context['cuaderno']=[]
                context['experiencias_recientes']=[]
                context['memoria_de_experiencias']=[]
                context['instruccion_de_resumen']='Respondé solamente sobre las entradas pendientes incluidas en resumen_de_lo_no_leido. Distinguí hechos demostrados de hipótesis. Si restantes > 0, aclaralo expresamente y no afirmes haber revisado todo el período; ofrecé consultar las entradas restantes. No marques nada como leído.'
            history=copy.deepcopy(self.s['chat'][-12:]);self.write()
        def worker():
            try:
                (reply,tokens),provider,model=route(cfg,self.s,self.lock,lambda pcfg:request_chat(pcfg,context,history),'chat')
                with self.lock:
                    self.s['chat_daily'][day]=self.s['chat_daily'].get(day,0)+1
                    self.sessions.note_llm(provider,model,"chat")
                    self.s['chat'].append({'id':str(uuid.uuid4())[:8],'role':'assistant','text':reply,'at':time.time(),
                                           'provider':provider})
                    self.archive.add('chat',self.s['chat'][-1])
                    if page is not None:
                        self.s['catchup_offset']=page['desde']+page['mostradas'] if page['restantes'] else 0
                        positions=dict(self.s.get('last_catchup_covered',{})) if page['desde'] else {}
                        for entry in page['entradas']:
                            cat='journal' if entry['tipo']=='Cuaderno' else 'news'
                            positions[cat]=max(positions.get(cat,0),entry['seq'])
                        self.s['last_catchup_covered']=positions
                    self.s['chatting']=False;self.s['chat_error']='';self.write()
            except ProvidersUnavailable as exc:
                with self.lock:
                    remaining=max(0,round(exc.retry_at-time.time()))
                    self.s['chatting']=False
                    self.s['chat_error']=f'No se pudo consultar a los modelos. {exc} Próximo intento posible en aprox. {remaining} s.'[:350]
                    self.write()
            except Exception:
                with self.lock:
                    self.s['chatting']=False;self.s['chat_error']='Error inesperado del chat; se conserva la conversación.'
                    self.write()
        threading.Thread(target=worker,daemon=True,name='NiloChat').start()
        return True

    def linked_record(self,category,item_id):
        """Consulta histórica de solo lectura, acotada a categorías de interfaz."""
        allowed={'news','journal','research','project','prediction','measurement','conclusion',
                 'proposal','design','construction','tool','diagnostic','event'}
        if category not in allowed or not isinstance(item_id,str) or not (0<len(item_id)<=100):
            raise ValueError('Registro o categoría inválida')
        with self.lock:
            record=self.archive.latest_record(category,item_id)
            if record is None:raise ValueError('No se encontró el registro solicitado')
            return {'category':category,'record':record,
                    'relations':self.archive.relations_for(category,item_id)}

    def public_state(self):
        with self.lock:
            s=self.s;p=s['person'];w=s['world']
            world_projection=self.environment.render_map(w,p)
            cfg=config();key_ok=available(cfg);pending=p.get('pending');routing=public_info(cfg,s)
            remaining_world=None;remaining_real=None;remaining_write_base=None
            if pending:
                if pending['step']['op']=='write':
                    remaining_real=round(max(0,pending.get('remaining_real',0))/
                                         effective_speed(s['speed'],pending),2)
                    remaining_world=round(max(0,pending.get('remaining_real',0))/60,2)
                    remaining_write_base=max(0,pending.get('remaining_real',0))
                    progress=round(100*(1-pending['remaining_real']/pending['total_real'])) if pending['total_real'] else 100
                else:
                    remaining_world=round(max(0,pending['remaining']),2)
                    remaining_real=round(max(0,pending['remaining'])*60/max(1,s['speed']))
                    progress=round(100*(1-pending['remaining']/pending['total'])) if pending['total'] else 100
            else:progress=None
            archive_meta,read_items=self.archive.recent_meta()
            journal=[]
            for note in s['journal'][-50:][::-1]:
                item=dict(note)
                if pending and pending.get('journal_id')==note.get('id') and pending.get('step',{}).get('op')=='write':
                    total=pending.get('total_real',40)
                    elapsed=max(0,total-pending.get('remaining_real',0))
                    item['visible_text']=(note['text'] if s['speed']>=300 else
                                         note['text'][:typing_visible_chars(note['text'],elapsed)])
                    item['writing']=True
                else:item['visible_text']=note['text'];item['writing']=False
                item['seq']=archive_meta.get('journal',{}).get(note['id'],0)
                item['read']=(item['seq'] > 0 and
                              (item['seq'] <= self.archive.position('journal') or
                              ('journal',item['seq']) in read_items))
                journal.append(item)
            # El grafo visible se resuelve desde SQLite, sin reconstruir relaciones
            # por proximidad de horas o por parecido entre textos.
            visible_keys=[]
            projections=(
              ('journal',s['journal'][-50:]),
              ('research',p.get('research',[])[-30:]),
              ('project',p.get('projects',[])[-50:]+([p['project']] if p.get('project') else [])),
              ('prediction',p.get('prediction_log',[])[-80:]),
              ('measurement',p.get('measurements',[])[-65:]),
              ('conclusion',p.get('conclusions',[])[-40:]),
              ('proposal',p.get('proposals',[])[-100:]),
              ('design',p.get('designs',[])[-100:]),
              ('construction',w.get('structures',[])[-30:]+w.get('retired_structures',[])[-30:]),
              ('tool',p.get('items',[])[-30:]),
              ('event',s.get('events',[])[-90:])
            )
            for category,records in projections:
                visible_keys.extend((category,r['id']) for r in records
                                    if isinstance(r,dict) and r.get('id'))
            record_relations=self.archive.relations_batch(visible_keys)
            return {'name':p.get('name','Nilo'),'version':5,'scenario_id':self.scenario.id,'environment_id':self.scenario.environment_id,'time':self.stamp(),'time_minutes':round(p['clock_minutes'],2),'position':p['pos'],
                    **world_projection,
                    'active_intervention':active_intervention(w,p,pending),
                    'unconscious':bool(p.get('unconscious')),
                    'installed_capabilities':w.get('capability_versions',{}),
                    'activity':(self.describe_action(pending['step'])+
                        (' · escritura rápida' if pending.get('step',{}).get('op')=='write' and s['speed']>=300 else
                         ' · ×2 temporal' if pending.get('step',{}).get('op')=='write' and s['speed']>1 else '')) if pending else ('Inconsciente · recuperación involuntaria' if p.get('unconscious') else 'Deliberando' if s['planning'] else ('En espera de deliberación · tiempo detenido' if s.get('auto_wait_frozen') else ('En espera de deliberación' if s.get('mode') in ('espera','limite') else 'Pensando qué hacer'))),
                    'progress':progress,'remaining_world_minutes':remaining_world,'remaining_real_seconds':remaining_real,
                    'remaining_write_base_seconds':remaining_write_base,
                    'effective_speed':effective_speed(s['speed'],pending,
                        planning=bool(s.get('planning')),frozen=bool(s.get('auto_wait_frozen')),
                        paused=bool(s.get('paused'))),
                    'project':p['project'],'plan':p['plan'][:8],'inventory':{k:v for k,v in p['inventory'].items() if v>0},
                    'items':p.get('items',[])[-30:],'observations':p.get('observations',[])[-25:][::-1],
                    'research':p['research'][::-1], 'journal':journal,
                    'events':s['events'][-90:][::-1],
                    'measurements':p.get('measurements',[])[-65:][::-1],
                    'conclusions':p.get('conclusions',[])[-40:][::-1],
                    'experiment_status':closure_status(p),
                    'maintenance':maintenance_summary(p),
                    'needs':needs_summary(p),'preferences':p.get('preferences',{}),
                     'skills':[{ 'key':k, **v} for k,v in list(p.get('skills',{}).items())[-35:]],
                     'waiting_preferences':p.get('waiting_preferences',[]),
                     'waiting_history':p.get('waiting_history',[])[-50:][::-1],
                     'waiting_state':p.get('waiting_state',{}),
                     'agenda':p.get('agenda',[])[-75:][::-1],
                     'agenda_history':p.get('agenda_history',[])[-75:][::-1],
                     'auto_wait_frozen':s.get('auto_wait_frozen',False),
                     'auto_pause_on_wait':s.get('auto_pause_on_wait',True),
                     'autonomy_stats':p.get('autonomy_stats',{}),
                     'behavior':behavior_summary(p),
                    'experience_summary':p.get('experience_summary',[])[-70:][::-1],
                    'life_chapters':p.get('life_chapters',{}),
                    'designs':p.get('designs',[])[-100:][::-1],
                    'proposals':p.get('proposals',[])[-100:][::-1],
                    'prediction_log':p.get('prediction_log',[])[-80:][::-1],
                    'engine_sessions':self.sessions.recent(),
                    'engine_identity':self.sessions.identity,
                    'news':[{**v,'seq':archive_meta.get('news',{}).get(v['id'],0),
                             'read':(archive_meta.get('news',{}).get(v['id'],0)<=self.archive.position('news')
                                     or ('news',archive_meta.get('news',{}).get(v['id'],0)) in read_items)}
                            for v in s.get('news',[])[-100:][::-1]],
                    'read_marker':s.get('read_marker'),
                    'unread':{c:self.archive.count_unread(c) for c in ('journal','news')},
                    'read_positions':{c:self.archive.position(c) for c in ('journal','news')},
                    'archive_counts':self.archive.counts(),'record_relations':record_relations,
                     'review_initialized':self.review.initialized(),
                     'review_seen':self.review.seen(),
                     'knowledge':list(p['knowledge'].items())[-20:][::-1],
                    'structures':w['structures'][-30:][::-1],
                    'retired_structures':w.get('retired_structures',[])[-30:][::-1],'projects':p['projects'][-50:][::-1],
                    'chat':s['chat'][-50:],'chatting':s['chatting'],'chat_error':s['chat_error'],
                    'summary_markable':bool(s.get('last_catchup_covered')), 
                    'speed':s['speed'],'paused':s['paused'],'planning':s['planning'],
                    'ai':{'provider':cfg.get('PROVIDER'),'model':cfg.get('MODEL'),'configured':key_ok,'mode':s['mode'] if key_ok else 'demo',
                          'error':s['ai_error'],'daily_calls':s['llm_daily'].get(datetime.now().strftime('%Y-%m-%d'),0),
                          'daily_limit':cfg.get('MAX_LLM_CALLS_PER_DAY','100'),'chat_calls':s['chat_daily'].get(datetime.now().strftime('%Y-%m-%d'),0),
                          'chat_limit':cfg.get('MAX_CHAT_CALLS_PER_DAY','40'),'tokens':s['last_tokens'],
                          'min_interval_seconds':deliberation_interval_seconds(cfg),
                          'routing':routing,'next_try_seconds':max(0,round(s.get('next_deliberation_real',0)-time.time()))}}

    def change_speed(self,speed=None,paused=None,auto_pause_on_wait=None):
        with self.lock:
            if speed is not None and type(speed) is int and speed in SUPPORTED_SPEEDS:self.s['speed']=speed
            if paused is not None and isinstance(paused,bool):self.s['paused']=paused
            if isinstance(auto_pause_on_wait,bool):
                self.s['auto_pause_on_wait']=auto_pause_on_wait
                if not auto_pause_on_wait:self.s['auto_wait_frozen']=False
            self.write()

    def run(self):
        while not self.stopped:
            now=time.monotonic();elapsed=now-self.last_loop;self.last_loop=now
            try:self.tick(elapsed)
            except Exception as exc:
                traceback.print_exc()
                with self.lock:self.s['ai_error']=f"Error de simulación: {exc}"
            time.sleep(1)


HTML_FILE=HERE/'interfaz.html'

class Handler(BaseHTTPRequestHandler):
    sim=None
    def log_message(self,*args):pass
    def send_json(self,obj,code=200):
        body=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path in ('/','/index.html'):
            body=HTML_FILE.read_bytes();self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        elif path=='/api/state':self.send_json(self.sim.public_state())
        elif path=='/api/summary-history':
            self.send_json({'summaries':self.sim.observer_summary_history()})
        elif path=='/api/unread':
            qs=parse_qs(urlsplit(self.path).query)
            category=(qs.get('category') or [''])[0]
            if category not in ('journal','news'):
                self.send_json({'error':'Categoría de archivo inválida'},400)
            else:
                with self.sim.lock:
                    self.send_json({'category':category,
                        'total':self.sim.archive.count_unread(category),
                        'entries':self.sim.archive.unread(category,limit=80)})
        elif path=='/api/record':
            qs=parse_qs(urlsplit(self.path).query)
            category=(qs.get('category') or [''])[0][:40]
            rid=(qs.get('id') or [''])[0][:101]
            try:self.send_json(self.sim.linked_record(category,rid))
            except ValueError as exc:self.send_json({'error':str(exc)},404)
        elif path=='/api/measurement':
            qs=parse_qs(urlsplit(self.path).query)
            mid=(qs.get('id') or [''])[0][:80]
            try:self.send_json(self.sim.measurement_record(mid))
            except ValueError as exc:self.send_json({'error':str(exc)},404)
        elif path=='/api/ui-preferences':
            with self.sim.lock:
                self.send_json(load_interface_prefs(HERE))
        elif path=='/api/diagnostic':
            qs=parse_qs(urlsplit(self.path).query)
            rid=(qs.get('id') or [''])[0][:80]
            try:self.send_json(self.sim.diagnostic_package(rid))
            except ValueError as exc:self.send_json({'error':str(exc)},404)
        else:self.send_json({'error':'No encontrado'},404)
    def do_POST(self):
        path=urlsplit(self.path).path
        if path not in ('/api/settings','/api/chat','/api/read-news','/api/read','/api/read-all','/api/read-summary','/api/review-rule','/api/retry-llm','/api/ui-preferences','/api/review-bootstrap','/api/review-mark','/api/summary-generate','/api/summary-ack'):return self.send_json({'error':'No encontrado'},404)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>(65000 if path in ('/api/review-bootstrap','/api/review-mark','/api/summary-generate') else 3000):return self.send_json({'error':'Solicitud demasiado grande o vacía'},413)
            data=json.loads(self.rfile.read(size))
            if path=='/api/review-bootstrap':
                return self.send_json(self.sim.bootstrap_reviews(data.get('seen',{})))
            if path=='/api/review-mark':
                return self.send_json(self.sim.mark_tab_reviewed(data.get('tab'),data.get('keys',[])))
            if path=='/api/summary-generate':
                try:return self.send_json(self.sim.observer_summary(data.get('candidates',[]),data.get('continuation')))
                except (ProvidersUnavailable,RuntimeError) as exc:
                    return self.send_json({'error':str(exc)[:450]},503)
            if path=='/api/summary-ack':
                return self.send_json(self.sim.acknowledge_observer_summary(str(data.get('id',''))[:80]))
            if path=='/api/ui-preferences':
                with self.sim.lock:
                    return self.send_json(save_interface_prefs(HERE,data))
            if path=='/api/retry-llm':
                result=self.sim.retry_llm()
                return self.send_json(result,200 if result['ok'] else 409)
            if path=='/api/review-rule':
                return self.send_json(self.sim.review_rule(str(data.get('id',''))[:80],
                    str(data.get('decision',''))[:15],str(data.get('reason',''))[:700]))
            if path in ('/api/read-news','/api/read'):
                category='news' if path=='/api/read-news' else str(data.get('category',''))
                if data.get('single') is True:
                    return self.send_json(self.sim.mark_one_read(category,str(data.get('id',''))[:60]))
                return self.send_json(self.sim.mark_read(category, str(data.get('id',''))[:60]))
            if path=='/api/read-all':
                categories=data.get('categories',['journal','news'])
                if not isinstance(categories,list) or len(categories)>2:raise ValueError('Categorías inválidas')
                return self.send_json(self.sim.mark_all_read(categories))
            if path=='/api/read-summary':return self.send_json(self.sim.mark_summarized_read())
            if path=='/api/chat':
                self.sim.start_chat(data.get('message',''))
                return self.send_json({'ok':True},202)
            speed=data.get('speed')
            if speed is not None and (type(speed) is not int or speed not in SUPPORTED_SPEEDS):raise ValueError('Velocidad inválida')
            paused=data.get('paused')
            if paused is not None and not isinstance(paused,bool):raise ValueError('Pausa inválida')
            auto_pause=data.get('auto_pause_on_wait')
            if auto_pause is not None and not isinstance(auto_pause,bool):raise ValueError('Ajuste de pausa inválido')
            self.sim.change_speed(speed,paused,auto_pause)
            self.send_json({'ok':True})
        except (ValueError,TypeError,KeyError) as exc:self.send_json({'error':str(exc)},400)



def main():
    sim=Simulation();Handler.sim=sim
    cfg=config();port=int(cfg.get('PORT','8765'))
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=sim.run,daemon=True,name='NiloClock').start()
    print(f"\nNILO · {sim.sessions.identity['engine_version']}\nAbri en el navegador: http://127.0.0.1:{port}\n")
    print('LLM configurado: '+('SÍ ('+cfg.get('MODEL','')+')' if available(cfg) else 'NO; modo demostración claramente indicado'))
    print('Para detener la simulación: Ctrl+C o cerrar esta ventana.\n')
    threading.Timer(1.5,lambda:webbrowser.open(f'http://127.0.0.1:{port}')).start()
    try:server.serve_forever(poll_interval=.5)
    except KeyboardInterrupt:pass
    finally:
        sim.stopped=True
        with sim.lock:
            sim.write()
            sim.sessions.finish(sim.s['person']['clock_minutes'])
        server.server_close();sim.conn.close()

if __name__=='__main__':main()
