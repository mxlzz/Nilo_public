"""Agenda persistente: intenciones formuladas por LLM, ejecutadas sin nuevas consultas.

No crea conocimientos ni recursos; cada paso pasa por el mismo motor físico. Las
condiciones y rutas se vuelven a comprobar inmediatamente antes de ejecutar.
"""
from __future__ import annotations
import uuid
from world import tile_key, pathfind, known_exit_route, valid

# Tareas diferidas de bajo riesgo. Acciones creadoras de mundo requieren deliberación nueva.
ALLOWED={'inspect','gather','experiment','use','craft','compare','conclude',
         'go','ascend','forage','drink','eat','rest'}
NEEDS={'hidratacion','nutricion','energia'}
STATES={'pendiente','en_curso','completada','bloqueada','cancelada','pospuesta'}

def ensure_agenda(person):
    person.setdefault('agenda',[])
    person.setdefault('agenda_history',[])
    person.setdefault('strategy_attempts',[])
    return person

def normalize_task(raw, now, project_id=None):
    if not isinstance(raw,dict):return None
    title=str(raw.get('titulo') or raw.get('objetivo') or '').strip()[:140]
    if not title:return None
    steps=raw.get('pasos',[])
    mode=str(raw.get('modo') or 'tarea').lower()
    if mode not in ('tarea','recordatorio'):return None
    if mode=='recordatorio':
        if steps not in ([],None):return None
        steps=[]
    elif not isinstance(steps,list) or not 1<=len(steps)<=5:return None
    out=[]
    for s in steps:
        if not isinstance(s,dict) or str(s.get('op','')).lower() not in ALLOWED:return None
        s={k:v for k,v in s.items() if k in {'op','x','y','target','item','method','materials','name','form','purpose','geometry','evidence_ids','metric','topic','minutes'}}
        s['op']=s['op'].lower()
        if s['op']=='rest':
            from bodily_policy import rest_minutes
            duration=rest_minutes(s)
            if duration is None:return None
            s['minutes']=duration
        if s['op']=='go':
            if str(s.get('target','')).lower() in ('agua','orilla','costa','rio','río','lago'):
                # La búsqueda se resuelve físicamente por orillas conocidas.
                s={'op':'go','target':'agua'}
            else:
                try:s={'op':'go','x':int(s['x']),'y':int(s['y'])}
                except (ValueError,TypeError,KeyError):return None
        out.append(s)
    condition=raw.get('cuando',{})
    if not isinstance(condition,dict):condition={}
    kind=str(condition.get('tipo','ahora')).lower()
    if kind not in ('ahora','despues_de_minutos','cuando_haya_material','cuando_necesidad'):return None
    clean={'tipo':kind}
    if kind=='despues_de_minutos':
        try:minutes=float(condition.get('minutos',0))
        except (ValueError,TypeError):return None
        clean['minutos']=max(0,min(minutes,7*1440))
    elif kind=='cuando_haya_material':
        mat=str(condition.get('material','')).strip().lower()[:50]
        if not mat:return None
        try:qty=int(condition.get('cantidad',1))
        except (ValueError,TypeError):return None
        clean.update(material=mat,cantidad=max(1,min(30,qty)))
    elif kind=='cuando_necesidad':
        need=str(condition.get('necesidad',''))
        if need not in NEEDS:return None
        try:limit=float(condition.get('menor_que',50))
        except (ValueError,TypeError):return None
        clean.update(necesidad=need,menor_que=max(1,min(90,limit)))
    return {'id':'tar-'+uuid.uuid4().hex[:10], 'modo':mode, 'titulo':title,
            'motivo':str(raw.get('motivo','')).strip()[:200],
            'proyecto_id':project_id,'cuando':clean,'creada_minuto':float(now),
            'pasos':out,'indice':0,'estado':'pendiente','resultados':[],
            'ultimo_motivo':'Condición pendiente','intentos':0}

def set_agenda(person, raw, now, project_id=None):
    ensure_agenda(person)
    if not isinstance(raw,list):return []
    current=person['agenda']
    added=[]
    for candidate in raw[:6]:
        task=normalize_task(candidate,now,project_id)
        if not task:continue
        if task['modo']=='recordatorio':
            signature=(task['titulo'].casefold(),str(task['cuando']),task.get('proyecto_id'))
            duplicate=any(
                t.get('modo')=='recordatorio'
                and (t.get('titulo','').casefold(),str(t.get('cuando')),t.get('proyecto_id'))==signature
                and t.get('estado') in ('pendiente','lista_para_revisar','pospuesta')
                for t in current)
        else:
            # Preservar la deduplicacion anterior para las tareas ya existentes.
            signature=(task['titulo'].casefold(),str(task['pasos']))
            duplicate=any(
                t.get('modo','tarea')!='recordatorio'
                and (t.get('titulo','').casefold(),str(t.get('pasos')))==signature
                and t.get('estado') in ('pendiente','en_curso','pospuesta')
                for t in current)
        if duplicate:continue
        if sum(x.get('estado') in ('pendiente','en_curso','pospuesta') for x in current)>=35:break
        current.append(task);added.append(task)
    # Conserva los últimos registros, sin eliminar pendientes para hacer lugar.
    completed=[t for t in current if t['estado'] in ('completada','cancelada','bloqueada')]
    if len(completed)>70:
        drop=set(t['id'] for t in completed[:-70])
        person['agenda']=[t for t in current if t['id'] not in drop]
    return added

def condition_met(task,person):
    c=task.get('cuando',{});kind=c.get('tipo','ahora')
    if kind=='despues_de_minutos':
        return person.get('clock_minutes',0)>=task.get('creada_minuto',0)+c.get('minutos',0)
    if kind=='cuando_haya_material':
        return person.get('inventory',{}).get(c.get('material'),0)>=c.get('cantidad',1)
    if kind=='cuando_necesidad':
        return person.get('needs',{}).get(c.get('necesidad'),100)<c.get('menor_que',50)
    return True

def safe_step(world, person, step):
    """Decidir si se puede ejecutar sin deliberar. No revelar casillas nuevas."""
    op=step['op'];x,y,z=person['pos'];known=world.get('revealed',set())
    if op=='go':
        if step.get('target')=='agua':
            from world import reachable_shores
            shores=reachable_shores(world,person,max_results=10)
            return any((q['shore']==(x,y) or bool(pathfind(world,(x,y,z),(*q['shore'],z),known_only=True))) for q in shores)
        tx,ty=step['x'],step['y']
        return valid(tx,ty) and tile_key(tx,ty,z) in known and ((tx,ty)==(x,y) or bool(pathfind(world,(x,y,z),(tx,ty,z),known_only=True)))
    if op=='ascend':return z==-1 and known_exit_route(world,person) is not None
    if op=='gather':
        from habits import _gather_access
        return _gather_access(world,person,str(step.get('target','')).lower(),5)
    if op=='forage':
        from habits import _forage_access
        return _forage_access(world,person,1)
    if op=='drink':
        if step.get('item') or step.get('source'):
            from vessels import _accessible, _contents
            obj=_accessible(world,person,step.get('item') or step.get('source'))
            if obj is None:return False
            medium,q=_contents(obj)
            return medium=='agua' and q>=.18
        from habits import _near_water
        return _near_water(world,person)
    if op=='interact':
        from capabilities import resolve
        return resolve(str(step.get('method') or '').lower().strip()) is not None
    if op=='eat':return person.get('inventory',{}).get('alimento',0)>0
    if op=='craft':
        mats=step.get('materials',[])
        return bool(mats and step.get('name') and all(person.get('inventory',{}).get(m,0)>=mats.count(m) for m in set(mats)))
    if op=='experiment':return any(n in str(step.get('target','')).lower() and qty>0 for n,qty in person.get('inventory',{}).items())
    if op=='use':return any(step.get('item') in (a.get('name'),a.get('id')) for a in person.get('items',[]))
    if op=='inspect':
        from world import world_view
        wanted=str(step.get('target','')).lower().strip()
        return not wanted or any(wanted in ob.get('tipo','').lower() for ob in world_view(world,person))
    if op=='rest':return True
    if op in ('compare','conclude'):
        ids=step.get('evidence_ids',[])
        actual={m.get('id') for m in person.get('measurements',[])}
        return bool(ids and all(mid in actual for mid in ids))
    return True

def choose_agenda_step(world, person):
    ensure_agenda(person)
    # Se evalúan las precondiciones físicas de cada paso, no umbrales generales.
    for task in person['agenda']:
        if task.get('modo','tarea')=='recordatorio':continue
        if task.get('estado') not in ('pendiente','en_curso','pospuesta'):continue
        if task['estado']=='pospuesta' and person.get('clock_minutes',0)<task.get('reanudar_minuto',0):continue
        if not condition_met(task,person):continue
        index=task.get('indice',0)
        if index>=len(task.get('pasos',[])):
            task['estado']='completada';continue
        step=task['pasos'][index]
        if not safe_step(world,person,step):
            task['estado']='pospuesta'
            task['reanudar_minuto']=person.get('clock_minutes',0)+120
            task['intentos']=task.get('intentos',0)+1
            task['ultimo_motivo']='Condiciones físicas o ruta conocida no disponibles'
            if task['intentos']>=3:task['estado']='bloqueada'
            continue
        task['estado']='en_curso';task['ultimo_motivo']='Procedimiento delegado disponible'
        return dict(step,_origin='agenda',_agenda_id=task['id'],_reason=task['motivo'] or task['titulo']),task
    return None

def awaken_reminders(person,stamp):
    """Advertir una sola vez al cumplirse una condicion elegida por Nilo."""
    ensure_agenda(person)
    ready=[]
    for task in person['agenda']:
        if task.get('modo')!='recordatorio' or task.get('estado')!='pendiente':
            continue
        if condition_met(task,person):
            task['estado']='lista_para_revisar'
            task['ultimo_motivo']='Condicion cumplida: reconsiderar cuando se desee'
            task['condicion_cumplida']=stamp
            ready.append(task)
    return ready


def acknowledge_reminders(person,project_id,stamp):
    """El proyecto retomado deja de mostrar el mismo aviso pendiente."""
    if not project_id:return
    for task in person.get('agenda',[]):
        if task.get('modo')=='recordatorio' and task.get('proyecto_id')==project_id and task.get('estado')=='lista_para_revisar':
            task['estado']='completada'
            task['resuelto']=stamp
            task['ultimo_motivo']='El proyecto fue retomado'


def record_agenda_result(person,step,success,facts,stamp,*,legacy=False):
    ensure_agenda(person)
    task=next((t for t in person['agenda'] if t['id']==step.get('_agenda_id')),None)
    if not task:return None
    entry={'when':stamp,'paso':task.get('indice',0)+1,'op':step.get('op'),'exito':bool(success),
           'hecho':str(facts[0] if facts else '')[:220]}
    task['resultados'].append(entry)
    person['agenda_history'].append({'id':task['id'],'titulo':task['titulo'],**entry})
    if success:
        task['indice']+=1
        task['estado']='completada' if task['indice']>=len(task['pasos']) else 'pendiente'
        task['ultimo_motivo']='Secuencia terminada' if task['estado']=='completada' else 'Paso verificado; siguiente pendiente'
        if task['estado']=='completada' and not legacy:
            # Completar los pasos no verifica el objetivo escrito en la tarea.
            # El motor no adjudica conclusiones por el título o el porcentaje.
            task['cumplimiento_objetivo']={
                'estado':'no_verificado_por_ejecucion',
                'nota':'Secuencia ejecutada; el propósito requiere evidencia independiente.'}
    else:
        task['estado']='bloqueada'
        task['ultimo_motivo']='La acción falló; no ejecutar pasos dependientes'
    return task
