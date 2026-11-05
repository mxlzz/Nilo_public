"""Nilo 0.7 / etapa 07: casos de uso SessionLifecycle; solo coordinación de Simulation.

No importa el servidor HTTP ni depende del frontend. Las funciones de legado
mantienen sus pasos, efectos y contratos originales.
"""
from __future__ import annotations
from .deps import *

class SessionLifecycle:
    def __init__(self, db_path=None, world_seed=7321, rng_seed=None,
                 scenario_id="territorio_desconocido", *, services=None):
        # La aplicación sigue usando DB y las semillas anteriores. El modo de
        # prueba inyecta una base aislada y semillas explícitas.
        self.services=services if services is not None else RuntimeServices()
        self.lock=threading.RLock();self.conn=sqlite3.connect(db_path if db_path is not None else DB,check_same_thread=False,timeout=15)
        self.conn.execute('PRAGMA journal_mode=WAL')
        # Una migración inválida no deja tablas parcialmente confirmadas.
        # Abrir primero una unidad de trabajo, incluso para las DDL legadas.
        try:
            self.conn.execute('BEGIN IMMEDIATE')
            self._initialize_storage(world_seed,rng_seed,scenario_id)
        except BaseException:
            self.conn.rollback()
            self.conn.close()
            raise

    def _initialize_storage(self,world_seed,rng_seed,scenario_id):
        self.conn.execute('CREATE TABLE IF NOT EXISTS snapshot (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
        from nilo_runtime.storage.repository import SnapshotRepository
        self.repository=SnapshotRepository(self.conn)
        self.archive=History(self.conn)
        self.review=ReviewStore(self.conn)
        self.sessions=RunHistory(self.conn,HERE)
        from nilo_runtime.storage.timeline import TimelineStore
        self.timeline=TimelineStore(self.conn)
        self.timeline_capture_enabled=True
        self.timeline_version=(HERE / 'VERSION').read_text(encoding='utf-8').strip()
        payload=self.repository.current_payload()
        row=(payload,) if payload is not None else None
        if row:
            # Un save corrupto no es una partida nueva: reintentarlo como nuevo
            # destruiría el snapshot en la próxima escritura.
            try:
                loaded = json.loads(row[0])
            except (ValueError, TypeError) as exc:
                raise StateSchemaError(
                    "No se pudo leer el snapshot guardado. Conservá el archivo "
                    "SQLite y restaurá una copia válida; no se reinició el mundo."
                ) from exc
            # Rechazar un esquema futuro antes de que migrate() escriba versión 5.
            validate_loaded_envelope(loaded)
            self.s = loaded
            self.s['planning'] = False
        else:
            self.s = initial_state(world_seed, scenario_id)
            validate_loaded_envelope(self.s)
        # El RNG físico y los IDs se restauran desde una fila transaccional de
        # ESTA partida. Antes de 0.7 no existía esa fila: solo podemos aplicar
        # la semilla histórica, sin atribuirle continuidad anterior inexistente.
        initial_seed=(9821+int(self.s['person']['clock_minutes'])) if rng_seed is None else int(rng_seed)
        active_world_seed=self.s['world'].get('seed',world_seed)
        self.entropy,self.entropy_origin=load_entropy(
            self.conn,world_seed=int(active_world_seed),
            rng_seed=initial_seed,original_snapshot=bool(row),
            snapshot_payload=row[0] if row else None,
            allow_legacy_reimport=bool(row and (
                not self.s.get('archive_migrated_052')
                or not self.s.get('news_migrated_v4'))))
        self.rng=self.entropy.agent_rng
        self.rng_seed=self.entropy.rng_seed
        # La partida guardada manda: una opción nueva no reemplaza su escenario.
        self.scenario=get_scenario(self.s.get('scenario_id',"territorio_desconocido"))
        self.environment=get_environment(self.scenario.environment_id)
        # Volcar primero los registros legados, antes de migraciones que los pudieran acotar.
        with self.entropy.bind(): self.archive.sync(self.s)
        fresh_markers = not self.s.get('archive_migrated_052')
        self.migrate()
        validate_current_state(self.s)
        with self.entropy.bind(): self.archive.sync(self.s)
        if fresh_markers:
            legacy_id=self.s.get('read_marker')
            if legacy_id:
                legacy_seq=self.archive.seq_for('news', legacy_id)
                if legacy_seq:self.archive.mark_read('news',legacy_seq)
            # Antes de esta versión no existía 'cuaderno sin leer'.
            self.archive.mark_read('journal')
            self.s['archive_migrated_052']=True
        self.s['real_saved']=time.time()
        self.last_loop=time.monotonic();self.last_persist=0.0;self.stopped=False
        configured=self.services.config()
        signature=routing_signature(configured)
        # No cambiar partidas corrientes ni replays solo por iniciar Nilo:
        # la huella determinista del mundo debe seguir intacta.
        if (self.services.available(configured) and self.s.get('mode')=='espera'
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


    @entropy_scoped
    def migrate(self):
        """Compatibilidad con partidas del prototipo 01; nunca reinicia el mundo."""
        s=self.s; p=s['person']; s['version']=SAVE_SCHEMA_VERSION
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


    @entropy_scoped
    def write(self):
        """Snapshot, archivo, sesión y entropía comparten commit o rollback."""
        validate_current_state(self.s)
        current_seed=self.s['world'].get('seed',self.entropy.world_seed)
        if current_seed != self.entropy.world_seed:
            p=self.s['person']
            if (p.get('clock_minutes') or p.get('items') or p.get('measurements')
                    or p.get('research') or p.get('projects') or p.get('project')
                    or self.s['world'].get('structures') or self.s.get('events')):
                raise EntropyError(
                    "No se puede sustituir la semilla de un mundo con historia: "
                    "conservá la partida y creá un escenario nuevo."
                )
            self.entropy=EntropySession(int(current_seed),self.rng_seed)
            self.rng=self.entropy.agent_rng
            self.entropy_origin="empty_world_seed_replaced"
        self.repository.persist(
            self.s,entropy=self.entropy,rng=self.rng,
            archive=self.archive,sessions=self.sessions)
        self.last_persist=time.monotonic()


    def domain_snapshot(self):
        """Vista tipada, profunda e inmutable del estado; nunca comparte mutables."""
        with self.lock:
            return snapshot_state(self.s)


    def stamp(self):
        d=int(self.s['person']['clock_minutes']//1440)+1
        m=int(self.s['person']['clock_minutes']%1440)
        return f"Día {d} · {m//60:02d}:{m%60:02d}"
