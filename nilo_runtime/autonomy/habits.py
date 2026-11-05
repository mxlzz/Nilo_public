"""Actividades autónomas cuando no hay deliberación disponible.

No imagina habilidades: aprende de acciones físicas verificadas, recuerda lugares
comprobados y solo ejecuta actividades acotadas y de riesgo bajo. Las preferencias
las elige Nilo durante una deliberación; las necesidades acotan la ejecución.
"""
from __future__ import annotations

from world import DIRS, valid, tile, tile_key, nearest_known, pathfind, reachable_shores, MATERIALS, gather_material
from survival import ensure_needs

SUPPORTED = {'forage', 'gather', 'rest', 'drink', 'eat', 'craft'}
MATERIAL_CHARS = {'madera':'T', 'piedra':'^r', 'arcilla':'s', 'fibra':',',
                  'mineral oscuro':'o', 'cristal':'v', 'hongo luminoso':'v'}
DEFAULT_STOCK = {'alimento':3, 'madera':4, 'piedra':4, 'arcilla':2, 'fibra':3}


def ensure_habits(person):
    person.setdefault('skills', {})
    person.setdefault('waiting_preferences', [])
    person.setdefault('waiting_history', [])
    person.setdefault('waiting_last_minute', -10000.0)
    person.setdefault('waiting_last_failure', {})
    person.setdefault('waiting_state', {})
    return person


def bootstrap_skills(person, events):
    """Reconoce resultados positivos antiguos al migrar; nunca inventa lugares."""
    ensure_habits(person)
    if person.get('skills_bootstrapped_v051'):return
    for h in person.get('life_history',[]):
        if h.get('action')=='forage' and h.get('successful') and str(h.get('fact','')).lower().startswith('recolecté '):
            entry=person['skills'].setdefault('forage',{'op':'forage','target':'alimento','verified':True,'count':0})
            entry['count']+=1
            entry['last_fact']=str(h.get('fact',''))[:220]
            entry['last_success']=h.get('when','')
    for event in events[-500:]:
        line=str(event.get('text',''))
        if event.get('kind')!='resultado' or not line.lower().startswith('recogí '):continue
        m=_material_from_result([line])
        if m:
            entry=person['skills'].setdefault('gather:'+m,{'op':'gather','target':m,'verified':True,'count':0})
            entry['count']+=1
            entry['last_fact']=line[:220]
            entry['last_success']=event.get('when','')
    person['skills_bootstrapped_v051']=True


def _material_from_result(facts):
    text=' '.join(str(f) for f in facts).lower()
    if not text.startswith('recogí '):return None
    for material in MATERIALS:
        if f'unidades de {material}.' in text:return material
    return None


def record_skill(person, step, success, facts, stamp, old_inventory=None,
                 *, action_result=None, measurement=None):
    """Aprender del resultado estructurado; textos sólo en migraciones antiguas."""
    ensure_habits(person)
    if not success:return None
    op=step.get('op')
    if action_result is not None and (
            action_result.op != op or action_result.status != 'verified_success'
            or not action_result.success):
        return None
    if op=='forage' and person.get('inventory',{}).get('alimento',0)> (old_inventory or {}).get('alimento',0):
        key='forage';data={'op':'forage','target':'alimento'}
    elif op=='gather':
        # La habilidad procede de la operación exitosa y del inventario, no del
        # texto libre del resultado. El alias es el mismo que acepta el mundo.
        material=gather_material(step.get('target'))
        if (not material or not isinstance(old_inventory,dict)
                or person.get('inventory',{}).get(material,0)<=old_inventory.get(material,0)):
            return None
        key='gather:'+material;data={'op':'gather','target':material}
    elif op=='drink' and (action_result is not None or
                            any('bebí' in str(f).lower() for f in facts)):
        key='drink';data={'op':'drink','target':'agua'}
    elif op=='craft' and (
            (action_result is not None and isinstance(measurement,dict)
             and measurement.get('object_delta',0)>0)
            or (action_result is None and any('fabriqu' in str(f).lower() for f in facts))):
        # Fabricar algo demuestra el procedimiento constructivo, no su función.
        recipe={k:step[k] for k in ('materials','name','form','purpose','geometry') if k in step}
        if not recipe.get('materials') or not recipe.get('name'):return None
        key='craft:'+recipe['name'].casefold()[:65];data={'op':'craft','target':recipe['name'],'recipe':recipe}
    else:return None
    entry=person['skills'].setdefault(key,{'count':0,'verified':False})
    entry.update(data)
    entry['count']+=1
    entry['verified']=True
    entry['where']=list(person.get('pos',[]))
    entry['last_success']=stamp
    entry['last_fact']=str(facts[0] if facts else '')[:220]
    return entry


def _safe_preference(raw):
    if not isinstance(raw,dict):return None
    op=str(raw.get('op','')).lower().strip()
    target=str(raw.get('target','')).lower().strip()
    if op not in SUPPORTED:return None
    if op=='gather' and target not in MATERIAL_CHARS:return None
    if op=='craft' and not target:return None
    try:qty=int(raw.get('hasta',DEFAULT_STOCK.get(target,3)))
    except (ValueError,TypeError):qty=3
    try:radius=int(raw.get('radio',4))
    except (ValueError,TypeError):radius=4
    choice={'op':op,'target':target,'hasta':max(1,min(8,qty)),
            'radio':max(0,min(5,radius)), 'motivo':str(raw.get('motivo',''))[:160]}
    if op=='rest':
        from bodily_policy import rest_minutes
        minutes=rest_minutes(raw)
        if minutes is None:return None
        choice['minutes']=minutes
    if op in ('rest','drink','eat'):
        # Las delegaciones corporales son finitas; solo Nilo puede pedir
        # explícitamente varias ejecuciones, con un máximo verificable.
        try:times=int(raw.get('veces',1))
        except (TypeError,ValueError):times=1
        choice['veces']=max(1,min(8,times))
        if raw.get('menor_que') is not None:
            try:threshold=float(raw['menor_que'])
            except (TypeError,ValueError):threshold=None
            if threshold is not None and 0 < threshold <= 100:
                choice['menor_que']=threshold
    return choice


def set_wait_preferences(person, raw, stamp):
    """Solo deliberaciones LLM válidas pueden modificar las preferencias."""
    ensure_habits(person)
    if raw is None:return False
    if not isinstance(raw,list):return False
    choices=[]
    for item in raw[:5]:
        p=_safe_preference(item)
        if p and p not in choices:choices.append(p)
    person['waiting_preferences']=choices
    person['waiting_preferences_updated']=stamp
    # Solo una deliberación válida reautoriza el plan delegado. Replays
    # históricos usan una ruta distinta; partidas existentes empiezan en 0.
    person['waiting_preference_usage']={}
    return True


def _reachable(w,p,source,max_steps,*,known_only=False):
    x,y,z=p['pos'];tx,ty=source
    if abs(tx-x)+abs(ty-y)>max_steps:return False
    if (tx,ty)==(x,y):return True
    route=pathfind(w,(x,y,z),(tx,ty,z),known_only=known_only)
    return bool(route) and len(route)<=max_steps


def _forage_access(w,p,radius,*,known_only=False):
    x,y,z=p['pos']
    if z!=0:return False
    available=w.get('forage_deposits',{})
    for dx,dy in [(0,0)]+DIRS:
        xx,yy=x+dx,y+dy
        if (valid(xx,yy) and
                (not known_only or tile_key(xx,yy,z) in w.get('revealed',[]))
                and tile(w,xx,yy,z) in ('T',',')
                and available.get(tile_key(xx,yy,z),3)>0):
            return True
    return False


def _gather_access(w,p,target,radius,*,known_only=False):
    if target not in MATERIAL_CHARS:return False
    found=nearest_known(w,p,MATERIAL_CHARS[target])
    if not found:return False
    tx,ty,wx,wy=found
    if abs(wx-p['pos'][0])+abs(wy-p['pos'][1])>radius:return False
    if not _reachable(w,p,(wx,wy),radius,known_only=known_only):return False
    # No acercarse para recolección si no existe reserva tangible disponible.
    return w.get('deposits',{}).get(tile_key(tx,ty,p['pos'][2]),0)>0


def _near_water(w,p,*,known_only=False):
    x,y,z=p['pos']
    return z==0 and any(
        valid(x+dx,y+dy)
        and (not known_only or tile_key(x+dx,y+dy,z) in w.get('revealed',[]))
        and tile(w,x+dx,y+dy,z)=='~' for dx,dy in DIRS)


def _legacy_choose_wait_action(w,p):
    """Devuelve (paso, motivo) o None. Nunca explora casillas desconocidas.

    Por defecto abastece solamente necesidades materiales moderadas y comprobadas.
    Una preferencia del LLM puede subir el stock sin poder eludir límites físicos.
    """
    ensure_habits(p);needs=ensure_needs(p);inv=p.get('inventory',{})
    # Priorizar agua ANTES de volver a descansar; ninguna rutina puede generar agua.
    # En una cueva sin agua, primero regresar por el camino descubierto hacia superficie.
    if p['pos'][2]==-1 and needs['hidratacion'] < 40 and needs['energia']>=12:
        from world import known_exit_route
        if known_exit_route(w,p) is not None:
            return {'op':'ascend'},'La hidratación disminuye; regresaré a la superficie por la salida conocida.'
    # El motor selecciona únicamente una orilla conocida y alcanzable por tierra.
    if needs['hidratacion'] < 30:
        if _near_water(w,p):
            return {'op':'drink'},'Necesito hidratarme y tengo acceso inmediato al agua.'
        if needs['energia'] >= 12:
            x,y,z=p['pos']
            shores=reachable_shores(w,p,max_results=75)
            candidates=[]
            for shore in shores:
                sx,sy=shore['shore']
                safe=pathfind(w,(x,y,z),(sx,sy,z),known_only=True)
                if safe and len(safe)<=24:candidates.append((len(safe),sx,sy))
            if candidates:
                _,sx,sy=min(candidates)
                return {'op':'go','x':sx,'y':sy},'Necesito llegar a una orilla conocida por un camino ya explorado para beber.'
    if needs['energia'] < 38:
        return {'op':'rest'},'Necesito recuperar fuerzas antes de emprender otra actividad.'
    # Primero las preferencias explícitas, luego provisiones básicas demostradas.
    chosen=list(p['waiting_preferences'])
    chosen += [{'op':'forage','target':'alimento','hasta':2,'radio':2,'motivo':'Reserva de comida reducida'},
               {'op':'gather','target':'madera','hasta':3,'radio':2,'motivo':'Reserva de madera reducida'},
               {'op':'gather','target':'piedra','hasta':3,'radio':2,'motivo':'Reserva de piedra reducida'}]
    for req in chosen:
        op=req['op'];target=req.get('target','')
        max_stock=req.get('hasta',2)
        radius=req.get('radio',2)
        if op=='rest':
            if needs['energia']<70 and needs['hidratacion']>=20:return {'op':'rest'},req.get('motivo') or 'Descanso previsto.'
        elif op=='drink':
            if needs['hidratacion']<45 and _near_water(w,p):
                return {'op':'drink'},req.get('motivo') or 'Agua comprobada.'
        elif op=='forage' and inv.get('alimento',0)<max_stock and p['skills'].get('forage',{}).get('verified'):
            if needs['energia']>=48 and needs['hidratacion']>=32 and _forage_access(w,p,radius):
                return {'op':'forage'},req.get('motivo') or 'Reponer alimentos cercanos.'
        elif op=='gather' and inv.get(target,0)<max_stock and p['skills'].get('gather:'+target,{}).get('verified'):
            if needs['energia']>=56 and needs['hidratacion']>=42 and _gather_access(w,p,target,radius):
                return {'op':'gather','target':target},req.get('motivo') or f'Reponer {target} conocida.'
        elif op=='craft':
            s=p['skills'].get('craft:'+target.casefold()[:65])
            if not s or not s.get('verified') or inv.get('alimento',0)<1 or needs['energia']<64:continue
            recipe=s.get('recipe',{});mats=recipe.get('materials',[])
            if not mats or any(inv.get(mat,0)<mats.count(mat) for mat in set(mats)):continue
            if sum(1 for x in p.get('items',[]) if x.get('name','').casefold()==target.casefold() and x.get('durability',0)>0)>=max_stock:continue
            # No clonar herramientas por rutina a menos que el LLM lo autorizara expresamente.
            if req not in p['waiting_preferences']:continue
            return {'op':'craft',**recipe},req.get('motivo') or 'Reproducir un procedimiento comprobado.'
    return None



def _delegation_available(person, req, index):
    """Una delegación no es una rutina perpetua ni una regla universal."""
    op=req.get('op')
    if op not in ('rest','drink','eat'):return True
    used=person.get('waiting_preference_usage',{}).get(str(index),0)
    try:allowed=max(1,min(8,int(req.get('veces',1))))
    except (TypeError,ValueError):allowed=1
    if used >= allowed:return False
    if req.get('menor_que') is not None:
        name={'rest':'energia','drink':'hidratacion','eat':'nutricion'}[op]
        try:
            if ensure_needs(person)[name] >= float(req['menor_que']):
                return False
        except (TypeError,ValueError,KeyError):return False
    return True


def record_wait_selection(person, step):
    """Descontar al agendar, sin alterar el contrato público de las acciones."""
    ensure_habits(person)
    for index,req in enumerate(person.get('waiting_preferences',[])):
        if step.get('op')!=req.get('op') or req.get('op') not in ('rest','drink','eat'):
            continue
        if not _delegation_available(person,req,index):continue
        if req['op']=='rest' and float(step.get('minutes',30))!=float(req.get('minutes',30)):
            continue
        counts=person.setdefault('waiting_preference_usage',{})
        counts[str(index)]=int(counts.get(str(index),0))+1
        return


def choose_wait_action(w, p, legacy_wait_policy=False):
    """Ejecuta procedimientos elegidos, sin repetir autocuidado sin límite."""
    if legacy_wait_policy:
        return _legacy_choose_wait_action(w,p)
    ensure_habits(p)
    inv=p.get('inventory',{})
    for index,req in enumerate(p.get('waiting_preferences',[])):
        op=req.get('op')
        target=req.get('target','')
        maximum=req.get('hasta',2)
        radius=req.get('radio',2)
        if not _delegation_available(p,req,index):continue
        if op=='rest':
            from bodily_policy import rest_minutes
            minutes=rest_minutes(req)
            if minutes is not None:
                return {'op':'rest','minutes':minutes},req.get('motivo') or 'Descanso delegado.'
        elif op=='drink' and _near_water(w,p,known_only=True):
            return {'op':'drink'},req.get('motivo') or 'Bebida delegada.'
        elif op=='eat' and inv.get('alimento',0)>0:
            return {'op':'eat'},req.get('motivo') or 'Comida delegada.'
        elif op=='forage' and inv.get('alimento',0)<maximum and p['skills'].get('forage',{}).get('verified') and _forage_access(w,p,radius,known_only=True):
            return {'op':'forage'},req.get('motivo') or 'Búsqueda delegada.'
        elif op=='gather' and inv.get(target,0)<maximum and p['skills'].get('gather:'+target,{}).get('verified') and _gather_access(w,p,target,radius,known_only=True):
            return {'op':'gather','target':target},req.get('motivo') or 'Recolección delegada.'
        elif op=='craft':
            skill=p['skills'].get('craft:'+target.casefold()[:65])
            if not skill or not skill.get('verified'):continue
            recipe=skill.get('recipe',{})
            mats=recipe.get('materials',[])
            if not mats or any(inv.get(m,0)<mats.count(m) for m in set(mats)):continue
            if sum(1 for obj in p.get('items',[]) if obj.get('name','').casefold()==target.casefold() and obj.get('durability',0)>0)>=maximum:continue
            return {'op':'craft',**recipe},req.get('motivo') or 'Fabricación delegada.'
    return None

def record_wait_result(person, step, success, facts, stamp):
    ensure_habits(person)
    entry={'when':stamp,'origin':step.get('_origin','espera'),'op':step.get('op'),'target':step.get('target'),
           'success':bool(success),'reason':step.get('_reason',''),
           'fact':str(facts[0] if facts else '')[:240]}
    person['waiting_history'].append(entry)
    # El historial íntegro no se trunca; la interfaz y el LLM reciben ventanas.
    person['waiting_state']={'kind':'resultado','last':entry}
    if not success:
        person['waiting_last_failure'][step.get('op','')+':'+str(step.get('target',''))]=person.get('clock_minutes',0)
    return entry
