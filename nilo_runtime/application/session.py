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
        self.conn_db_path=db_path if db_path is not None else DB
        self.lock=threading.RLock();self.conn=sqlite3.connect(self.conn_db_path,check_same_thread=False,timeout=15)
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
        from nilo_runtime.storage.llm_requests import RequestTraceStore
        self.llm_request_store=RequestTraceStore.for_world(
            self.conn_db_path)
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
        """Adaptador histórico; migraciones v0–v5 son propietarias de storage."""
        from nilo_runtime.storage.migrations import migrate_state
        return migrate_state(
            self.s, environment=self.environment,
            highlight_key=highlight_key, is_newsworthy=is_newsworthy,
            typing_duration=typing_duration)


    @entropy_scoped
    def write(self):
        """Snapshot, archivo, sesión y entropía comparten commit o rollback."""
        validate_current_state(self.s)
        old_entropy,old_rng,old_origin=self.entropy,self.rng,self.entropy_origin
        try:
            return self._write_atomic(old_entropy,old_rng,old_origin)
        except BaseException:
            # Si se cambió la semilla de un mundo todavía vacío y luego
            # falló el commit, restaurar también el generador en memoria.
            self.entropy,self.rng,self.entropy_origin=old_entropy,old_rng,old_origin
            raise

    def _write_atomic(self,old_entropy,old_rng,old_origin):
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
