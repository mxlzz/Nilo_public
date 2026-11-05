"""Nilo 0.7 / etapa 07: casos de uso ClockUseCases; solo coordinación de Simulation.

No importa el servidor HTTP ni depende del frontend. Las funciones de legado
mantienen sus pasos, efectos y contratos originales.
"""
from __future__ import annotations
from .deps import *

class ClockUseCases:
    @entropy_scoped
    def tick(self,real_elapsed):
        """Subpasos acotados: evitar saltar acciones al acelerar ×300/×600.

        Cada subpaso transcurre como máximo un minuto de reloj simulado y se
        interrumpe exactamente cuando termina una acción en curso.
        """
        # Los replays ya publicados conservan su método de recorte original.
        remaining=(max(0.0,min(float(real_elapsed),20.0))
                   if getattr(self,'historical_replay',False)
                   else clamp_real_elapsed(real_elapsed))
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
                    if interrupted and interrupted.get('timing') and not getattr(self,'historical_replay',False):
                        # El reloj ya avanzó en este slice, pero el handler no se
                        # ejecutó. Registrar fase parcial SIN acreditar materiales.
                        interrupted['remaining']=max(0.0,interrupted['remaining']-delta)
                        interrupted['timing']['phase']=phase_progress(interrupted)['phase']
                        interrupted_timing=completion_contract(
                            interrupted,measured_minutes=max(
                                0.0,p['clock_minutes']-
                                interrupted.get('measurement_start',{}).get(
                                    'minute',p['clock_minutes'])),
                            declared_handler_minutes=0.0,interrupted=True)
                    else:
                        interrupted_timing=None
                    p['interrupted_by_collapse']=({
                        'op':interrupted['step']['op'],
                        'elapsed_minutes':round(
                            interrupted.get('total',0)-interrupted.get('remaining',0),3),
                        'when':self.stamp(),
                        'origin':interrupted['step'].get('_origin','llm'),
                        **({'time_contract':interrupted_timing}
                           if interrupted_timing is not None else {})}
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
                    progress=phase_progress(pending) if pending.get('timing') else None
                    if progress:
                        pending['timing']['phase']=progress['phase']
                    if nav:
                        elapsed_world=(progress['elapsed_travel_minutes'] if progress
                                       else pending['total']-pending['remaining'])
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
                        action_handler=get_spec(step['op']).executor
                        if nav:
                            facts,success,notable=self.environment.finish_navigation(nav,p)
                            if success and nav.get('kind')=='ascend':
                                ascent_result=self.environment.perform_result(w,p,step,self.rng)
                                facts.extend(ascent_result.facts)
                                success=ascent_result.success
                                notable=notable or ascent_result.notable
                                action_result=ActionResult.from_legacy(
                                    step,facts,success,notable,
                                    duration_minutes=(0 if getattr(self,'historical_replay',False)
                                                      else ascent_result.duration_minutes),
                                    physical=ascent_result.physical,
                                    status_override=ascent_result.status)
                            elif nav.get('kind')=='gather':
                                # La navegación solo acredita un desplazamiento.
                                # La operación gather se considera exitosa únicamente
                                # si efectivamente extrae el material solicitado.
                                arrived=(success and
                                         tuple(p['pos'][:2])==tuple(nav['destination']))
                                if arrived:
                                    # La fuente elegida al iniciar el trayecto se conserva
                                    # tras navegar. No cambiar silenciosamente de depósito
                                    # después de completar la fase de trabajo.
                                    extraction_step=step
                                    if (not getattr(self,'historical_replay',False)
                                            and not getattr(self,'legacy_replay_rules',False)
                                            and nav.get('resource_at') is not None):
                                        extraction_step=dict(step,_resource_at=[
                                            *nav['resource_at'],nav['level']])
                                    harvested=self.environment.perform_result(
                                        w,p,extraction_step,self.rng)
                                    facts.extend(harvested.facts)
                                    success=harvested.success
                                    notable=notable or harvested.notable
                                    action_result=ActionResult.from_legacy(
                                        step,facts,success,notable,
                                        duration_minutes=(0 if getattr(self,'historical_replay',False)
                                                          else harvested.duration_minutes),
                                        physical=harvested.physical,
                                        status_override=harvested.status)
                                else:
                                    success=False
                                    facts.append('No completé la extracción: '
                                                 'el inventario no ganó el material solicitado.')
                        elif action_handler!='physical':
                            # El registro tipado elige un único adaptador documental.
                            # Ninguna ficha o propuesta modifica la física del mundo.
                            facts,success,notable=execute_document(self,p,step)
                        else:
                            action_result=self.environment.perform_result(w,p,step,self.rng)
                            facts=list(action_result.facts)
                            success=action_result.success
                            notable=action_result.notable
                        if action_result is None:
                            # Navegación, diseño y tareas documentales todavía usan
                            # sus motores específicos, pero comparten el contrato.
                            action_result=ActionResult.from_legacy(step,facts,success,notable)
                        start=pending.get('measurement_start')
                        measurement=measure(p,step,start,capture(w,p),facts,success,self.stamp(),
                                            action_result=action_result)
                        time_contract=(completion_contract(
                            pending,
                            measured_minutes=(measurement.get('duration_minutes')
                                              if measurement else None),
                            declared_handler_minutes=action_result.duration_minutes,
                            blocked=bool(nav and nav.get('blocked')))
                            if pending.get('timing') and
                               not getattr(self,'historical_replay',False)
                            else None)
                        if measurement:
                            if time_contract:
                                measurement['time_contract']=time_contract
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
                            if time_contract:
                                outcome['time_contract']=time_contract
                            if unmodeled:
                                outcome['unmodeled_attempt_id']=p.get('unmodeled_attempts',[{}])[-1].get('id')
                            if not (getattr(self,'historical_replay',False)
                                    or getattr(self,'legacy_replay_rules',False)):
                                # Evidencia física sólo de la medición de esta acción.
                                # El ID de la acción identifica el mismo evento.
                                outcome['causal_event']=causal_event_from_measurement(
                                    outcome['id'],action_result,measurement,
                                    unmodeled_attempt_id=outcome.get('unmodeled_attempt_id'),
                                ).to_record()
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
                        # En partidas nuevas el aprendizaje se fundamenta en
                        # resultado tipado y medición. El replay legado conserva
                        # sus registros históricos sin interpretar retroactivamente.
                        skill_result=(None if (getattr(self,'historical_replay',False)
                              or getattr(self,'legacy_replay_rules',False))
                              else action_result)
                        if step.get('_origin')=='agenda':
                            task=record_agenda_result(p,step,success,facts,self.stamp(),
                                legacy=(getattr(self,'legacy_replay_rules',False)
                                    or getattr(self,'historical_replay',False)))
                            self.event([('Terminé' if success else 'Suspendí')+' paso de mi agenda: '+task.get('titulo','')], 'agenda')
                            if success:record_skill(p,step,success,facts,self.stamp(),old_inventory,
                                action_result=skill_result,measurement=measurement)
                            if not success:p['plan']=[s for s in p['plan'] if s.get('_agenda_id')!=step.get('_agenda_id')]
                        elif autonomous:
                            record_wait_result(p,step,success,facts,self.stamp())
                        else:
                            record_skill(p,step,success,facts,self.stamp(),old_inventory,
                                action_result=skill_result,measurement=measurement)

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
                        causal_action=(outcome.get('id')
                            if step.get('op') not in ('propose','report_issue','design')
                            and not (getattr(self,'historical_replay',False)
                                     or getattr(self,'legacy_replay_rules',False))
                            else None)
                        self.event(facts,'resultado',notable,
                            action_id=causal_action,
                            measurement_id=(measurement.get('id') if causal_action
                                            and measurement else None))
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
                            action=p['plan'][0],engine_version=self.timeline_version,
                            entropy=(None if getattr(self,'historical_replay',False)
                                     or getattr(self,'legacy_replay_rules',False)
                                     else self.entropy))
                    except (ValueError,TypeError,OverflowError,sqlite3.Error):
                        pass
                step=p['plan'].pop(0)
                op=step['op'];minutes=get_spec(op).planned_minutes
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
                    travel_minutes=len(nav['route'])*travel_tile
                    # #142: gather remoto necesita trabajo de extracción una
                    # vez completado el viaje. El handler se ejecuta recién
                    # después de ambas fases (no acredita material al llegar).
                    if op=='gather' and not (getattr(self,'historical_replay',False)
                                             or getattr(self,'legacy_replay_rules',False)):
                        planned=plan_time(op,minutes,travel_minutes)
                        minutes=planned.planned_total_minutes
                    else:
                        minutes=travel_minutes
                if not (getattr(self,'historical_replay',False)
                        or getattr(self,'legacy_replay_rules',False)):
                    planned=plan_time(
                        op,minutes if not nav else
                        (get_spec(op).planned_minutes*factor if op=='gather' else 0.0),
                        0.0 if not nav else len(nav['route'])*travel_tile,
                        travel_is_only_phase=bool(nav and op!='gather'))
                    minutes=planned.planned_total_minutes
                p['pending']={'step':step,'start':self.stamp(),'remaining':minutes,'total':minutes,
                              **({} if getattr(self,'historical_replay',False)
                                  or getattr(self,'legacy_replay_rules',False)
                                  else {'timing':planned.to_pending()}),
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
            unavailable=self.services.available(self.services.config()) and (
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
