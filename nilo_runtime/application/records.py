"""Nilo 0.7 / etapa 07: casos de uso RecordsUseCases; solo coordinación de Simulation.

No importa el servidor HTTP ni depende del frontend. Las funciones de legado
mantienen sus pasos, efectos y contratos originales.
"""
from __future__ import annotations
from .deps import *
from nilo_runtime.perception.island import visible_structures

class RecordsUseCases:
    @entropy_scoped
    def event(self, facts,kind='accion',notable=False,*,action_id=None,measurement_id=None):
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
                item={'id':'hit-'+str(new_uuid())[:12], 'when':self.stamp(), 'kind':kind,
                      'title':title, 'detail':' '.join(extras)[:700]}
                if action_id: item['action_id']=action_id
                if measurement_id: item['measurement_id']=measurement_id
                news=self.s.setdefault('news',[])
                # No crear clones contiguos del mismo resultado.
                key=highlight_key(signal)
                already=bool(key and any(highlight_key(n.get('title',''))==key for n in news))
                if not already and (not news or news[-1]['title']!=item['title']):
                    news.append(item)
                    self.archive.add('news',item)
                    del news[:-200]
        for fact in facts:
            entry={'id':str(new_uuid())[:15], 'when':self.stamp(),
                   'text':str(fact)[:350], 'kind':kind, 'notable':notable}
            if action_id: entry['action_id']=action_id
            if measurement_id: entry['measurement_id']=measurement_id
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


    @entropy_scoped
    def observer_summary(self,candidates,continuation=None):
        """Síntesis editorial de los pendientes; no afecta al agente ni borra omisiones.

        La primera página examina todos los registros sin leer. «Qué más» usa
        el mismo límite de secuencia y desciende en prioridad; solo acusa
        lectura de las fichas efectivamente expuestas en esta entrega.
        """
        cfg=self.services.config()
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
            if not self.services.available(cfg):
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
        (reply,tokens),provider,model=self.services.route(
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


    @entropy_scoped
    def journal(self,text, question='', hypothesis='',origin='llm',linked=None):
        text=text[:500]
        duration=typing_duration(text)
        entry={'id':str(new_uuid())[:10],'when':self.stamp(),'text':text,
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
            seen_structures=visible_structures(w)
            cfg=self.services.config();key_ok=self.services.available(cfg);pending=p.get('pending');routing=public_info(cfg,s)
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
            activity_timing=(phase_progress(pending)
                             if pending and pending.get('timing') else None)
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
              ('construction',seen_structures[-30:]+w.get('retired_structures',[])[-30:]),
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
                    'activity_timing':activity_timing,
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
                    'structures':seen_structures[-30:][::-1],
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
