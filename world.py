"""El mundo de Nilo: hechos comprobables, acciones primitivas y memoria espacial.

El LLM propone intenciones; este módulo define las consecuencias físicas.
Sin dependencias externas.
"""
from __future__ import annotations

from nilo_runtime.core.identity import physical_suffix
import math, random, collections, re
from physics import geometry_from_step, body_physics, evaluate_containment, evaluate_buoyancy, properties as material_physics
from mechanics import create_assembly, test_assembly
from construction import (initialize_object, ensure_object, apply_intervention)
from phenomena import missing_physics, record_unmodeled, no_model_message

from catalogo import (MATERIALS, TERRAINS, YIELDS, GATHER_SOURCES,
                     GATHER_ALIASES, INSPECT_ALIASES,
                     PORTABLE_WORDS, FORMS)
# Fachada estable del mundo: los niveles y el RNG de creación tienen dueño
# exclusivo en worlds/island, sin importar agente ni dispatcher de acciones.
from nilo_runtime.worlds.island import (
    W, H, PASSABLE, DIRS, tile_key, valid, tile, set_tile, new_world, reveal,
)
from nilo_runtime.worlds.navigation import (
    NavigationIndex, TRAVEL_MINUTES_PER_TILE,
    EXPLORATION_DIRECTIONS, EXPLORATION_LABELS,
    cave_exit, known_exit_route, passable, pathfind, reachable_shores,
    resolve_go, move, exploration_frontier, actual_travel_direction,
    advance_navigation, choose_frontier,
)


def gather_material(target):
    name=" ".join(str(target or "").casefold().split())
    return name if name in GATHER_SOURCES else GATHER_ALIASES.get(name)





# Objetos portátiles y estructuras ancladas tienen ciclos de vida diferentes.
# Las propiedades derivan de la forma y de los materiales existentes, no del relato del LLM.
def infer_form(name,form=''):
    form=str(form).lower().strip()
    if form in FORMS:return form
    name=str(name).lower()
    for kind,words in FORMS.items():
        if any(word in name for word in words):return kind
    return 'golpe' if 'herramienta' in name else 'simple'

def is_portable(name,form='',purpose=''):
    if str(form).lower().strip() in FORMS:return True
    name=str(name).lower()
    return any(word in name for word in PORTABLE_WORDS)

def item_effects(item):
    # Capacidades verificables limitadas por geometría y resistencia estructural.
    form=item.get('form','simple');q=float(item.get('resistance',0));hard=float(item.get('hardness',0))
    if form=='golpe':return {'golpear':round(min(10,(q+hard)/2),1)}
    if form=='punta':return {'excavar':round(min(10,hard*.7+q*.3),1),'golpear':round(hard*.4,1)}
    if form=='filo':return {'cortar':round(min(10,hard*.75+q*.25),1)}
    if form=='palanca':return {'mover':round(min(10,q*.8+hard*.2),1)}
    if form=='recipiente':return {'contener':round(min(10,q*.5),1)}
    return {}

def make_item(name,purpose,materials,props,clock,source=None,rng=None):
    form=infer_form(name,source or '')
    item={'id':'obj-'+str(physical_suffix(52,rng=rng)), 'name':name,'purpose':purpose,
          'form':form,'materials':list(materials),'resistance':round(props['resistencia'],1),
          'hardness':round(props['dureza'],1),'weight':round(props['peso'],1),
          'durability':100,'tests':[],'created_at_minutes':round(clock,1),'portable':True}
    item['possible_uses']=item_effects(item)
    return item

def migrate_portable_structures(w,p):
    p.setdefault('items',[]);p.setdefault('observations',[])
    kept=[];moved=[]
    for structure in w.get('structures',[]):
        name=structure.get('name','')
        if is_portable(name) and structure.get('created_by')=='nilo':
            mats=structure.get('materials',[])
            props={'resistencia':float(structure.get('resistance',3)),
                   'dureza':max([p.get('materials',{}).get(m,MATERIALS.get(m,{})).get('dureza',1) for m in mats] or [1]),
                   'peso':sum(p.get('materials',{}).get(m,MATERIALS.get(m,{})).get('peso',1) for m in mats)}
            item=make_item(name,structure.get('purpose',''),mats,props,structure.get('made_at_minutes',0))
            item['source_structure_id']=structure.get('id','')
            p['items'].append(item);moved.append(name)
        else:kept.append(structure)
    w['structures']=kept
    return moved

def record_experience(p,action,subject,success,result,reading=None):
    observations=p.setdefault('observations',[])
    entry={'op':action,'subject':subject,'success':bool(success),'result':str(result)[:250],
           'at':round(p.get('clock_minutes',0),2)}
    if reading is not None:entry['reading']=reading
    observations.append(entry)
    del observations[:-100]
    return entry

def classify_structure(name,purpose):
    """Clasificación solo visual: no atribuye funciones demostradas."""
    t=(name+' '+purpose).lower()
    if any(k in t for k in ('palanca','polea','contrapeso','mecanismo','rueda','engranaje','torno','herramienta','dispositivo')):return 'mecanismo'
    if any(k in t for k in ('refugio','habitación','habitáculo','casa','cabaña','taller','almacén','cobertizo')):return 'habitaculo'
    if any(k in t for k in ('soporte','puente','plataforma','escalera','muro','mesa','banco','andamio','estructura')):return 'estructura'
    return 'prototipo'


def structure_symbol(s):
    return {'mecanismo':'M','estructura':'E','habitaculo':'H','prototipo':'?'}.get(s.get('category','prototipo'),'?')


def enrich_structure(s):
    """Compatibilidad de construcciones previas: descripción basada en datos existentes."""
    s.setdefault('category',classify_structure(str(s.get('name','')),str(s.get('purpose',''))))
    s.setdefault('status','Prototipo sin funcionamiento verificado')
    mats=s.get('materials',[])
    strength=s.get('resistance',0)
    s.setdefault('description',f"{s.get('category','Prototipo').capitalize()} hecho con {', '.join(mats) if mats else 'materiales sin registrar'}. Resistencia estructural estimada: {strength}/10. La función que imaginé aún no está probada.")
    return s


# tile_key/valid/tile/set_tile/new_world/reveal se reexportan desde
# nilo_runtime.worlds.island. Reglas físicas y navegación siguen aquí
# hasta sus propias etapas (09–12); no existen generadores paralelos.

def world_view(w, person):
    x,y,z=person['pos']; known=set(w['revealed']); near=[]
    for yy in range(max(0,y-4), min(H,y+5)):
        for xx in range(max(0,x-4), min(W,x+5)):
            k=tile_key(xx,yy,z)
            ch=tile(w,xx,yy,z)
            if k in known and ch in 'Tocersv^~':
                near.append({"pos":[xx,yy],"tipo":TERRAINS.get(ch,ch),"simbolo":ch,"distancia":abs(xx-x)+abs(yy-y)})
    near.sort(key=lambda v:v['distancia'])
    return near[:18]


def nearest_known(w,person,chars):
    """Localiza recursos accesibles incluso si el bloque de mineral es sólido.
    Devuelve lugar del recurso y posición de trabajo alcanzable.
    """
    x,y,z=person['pos']; opts=[]
    routes=NavigationIndex(w,(x,y,z),known_only=True)
    for k in w['revealed']:
        tx,ty,tz=map(int,k.split(','))
        if tz!=z or tile(w,tx,ty,z) not in chars:continue
        if w['deposits'].get(k,0)<=0:continue
        candidates=[(tx,ty)] if passable(w,tx,ty,z) else []
        candidates += [(tx+dx,ty+dy) for dx,dy in DIRS if passable(w,tx+dx,ty+dy,z)]
        for cx,cy in candidates:
            distance=routes.distance((cx,cy))
            if distance is not None:opts.append((distance,tx,ty,cx,cy))
    if not opts:return None
    _,tx,ty,cx,cy=min(opts)
    return tx,ty,cx,cy



def forage_source(w,person):
    """Fuente de forage en orden efectivo, leída sin alterar el mundo."""
    x,y,z=person['pos']
    spots=[(x+dx,y+dy) for dx,dy in [(0,0)]+DIRS if valid(x+dx,y+dy)
           and tile(w,x+dx,y+dy,z) in ('T',',')]
    growth=w.get('forage_growth',{})
    deposits=w.get('forage_deposits',{})
    clock=person.get('clock_minutes',0)
    for sx,sy in spots:
        key=tile_key(sx,sy,z)
        last=growth.get(key,clock)
        cycles=int(max(0,clock-last)//2880)
        amount=min(3,deposits.get(key,3)+cycles) if cycles else deposits.get(key,3)
        if amount>0:return sx,sy
    return None


def prepare_navigation(w,p,step,rng):
    """Prepara una ruta sin mover a Nilo ni revelar destino anticipadamente."""
    op=step.get('op');x,y,z=p['pos']
    destination=None;target_name=None;limit=12
    if op=='explore':
        destination,diagnostic=exploration_frontier(w,p,rng,step)
        if diagnostic:return None
        limit=9
    elif op=='ascend' and z==-1:
        route=known_exit_route(w,p)
        if route:
            destination=cave_exit(w);limit=W*H
        else:
            return None
    elif op=='go':
        destination,water_target,reason=resolve_go(w,p,step)
        if reason:return None
        limit=12
    elif op=='gather':
        requested=gather_material(step.get('target'))
        if requested is None:return None
        spot=nearest_known(w,p,GATHER_SOURCES[requested])
        if spot is None:return None
        tx,ty,wx,wy=spot
        if (x,y)==(wx,wy) or abs(tx-x)+abs(ty-y)<=1:return None
        destination=(wx,wy);target_name=(tx,ty);limit=10
    else:return None
    if destination is None:return None
    route=pathfind(w,(x,y,z),(*destination,z),allow_water=bool(p.get('vehicle_id')),
                   known_only=True)
    if not route:return None
    return {'kind':op,'route':[[rx,ry] for rx,ry in route[:limit]],
            'walked':0,'discovered':[], 'destination':list(destination),
            'resource_at':list(target_name) if target_name else None, 'level':z,
            'water_at':list(water_target) if op=='go' and water_target else None,
            **({'origin': [x,y], 'requested_direction': EXPLORATION_DIRECTIONS.get(
                str(step.get('direction')).casefold().strip()) if step.get('direction') is not None else None,
                'requested_region': step.get('region')}
               if op=='explore' and ('direction' in step or 'region' in step) else {})}


def navigation_result(nav,p):
    """Resultado verificable del recorrido, nunca inventado por el modelo."""
    n=nav['walked'];op=nav['kind'];z=nav['level'];position=p['pos'][:2]
    found=describe_findings(None, nav['discovered'])
    notable=bool(found)
    if op=='explore':
        facts=[f'Recorrí {n} tramos del nivel {z}, hasta {position}.']
        if 'origin' in nav:
            intended=nav.get('requested_direction')
            region=nav.get('requested_region')
            detail=('sector solicitado: '+EXPLORATION_LABELS[intended] if intended else 'región solicitada')
            if region:detail+='; anclaje conocido: '+str((region['x'],region['y']))
            detail+=('; frontera elegida: '+str(tuple(nav['destination']))+
                     '; dirección neta real: '+actual_travel_direction(nav['origin'],position)+
                     '; tramos realmente recorridos: '+str(n)+
                     '; casillas nuevas observadas: '+str(len(nav['discovered'])))
            facts.append('Exploración orientada · '+detail+'.')
        if found:facts.append('Observé por primera vez: '+', '.join(found)+'.')
    elif op=='ascend':
        facts=[f'Regresé por {n} tramos conocidos hasta la salida de la cueva en {position}.']
        if found:facts.append('En el regreso observé: '+', '.join(found)+'.')
    elif op=='go':
        if nav.get('water_at'):
            facts=[f'Avancé {n} tramos hasta la orilla {tuple(nav["destination"])}; el agua queda junto a {tuple(nav["water_at"])}.']
        else:
            facts=[f'Avancé {n} tramos hasta {position}; destino propuesto: {tuple(nav["destination"])}.']
        if found:facts.append('Apareció en mi campo de visión: '+', '.join(found)+'.')
    else:
        facts=[f'Me acerqué a una fuente de materiales en {tuple(nav["resource_at"] or nav["destination"])}, avanzando {n} tramos.']
        if found:facts.append('En el trayecto vi: '+', '.join(found)+'.')
    if nav.get('blocked'):
        facts.append(nav.get('blocked_reason') or 'El camino previsto quedó interrumpido; no tengo evidencia de la causa.')
    return facts,not nav.get('blocked',False),notable


def describe_findings(w,things):
    arr=[]
    for xx,yy,ch in things:
        if ch in 'oTcrve~^':
            d=TERRAINS.get(ch,ch)
            arr.append(f"{d} ({xx},{yy})")
    return list(dict.fromkeys(arr))[:5]


def adjacent_rock(w,position,step=None):
    """La elección de roca es física: adyacente y opcionalmente indicada por coordenadas."""
    x,y,z=position
    options=[(x+dx,y+dy) for dx,dy in DIRS
             if valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z) in '^#o']
    step=step or {}
    if 'x' in step or 'y' in step:
        try:
            choice=(int(step['x']),int(step['y']))
        except (TypeError,ValueError,KeyError):
            return None
        return choice if choice in options else None
    return options[0] if options else None


def dig_with_tool(w,p,tool,power,step=None):
    """Única regla para abrir roca, utilizada por 'use/excavar' y 'excavate'."""
    spot=adjacent_rock(w,p['pos'],step)
    if spot is None:return False,'No hay roca excavable adyacente en el destino indicado.',False
    tx,ty=spot;z=p['pos'][2];k=tile_key(tx,ty,z)
    kind=tile(w,tx,ty,z)
    minimum={'^':4.0,'#':5.5,'o':6.0}.get(kind,4.0)
    if power < minimum:
        return False,(f"La herramienta '{tool['name']}' tiene capacidad {power}/10: "
                      f"no supera la resistencia de {TERRAINS.get(kind,kind)} en ({tx},{ty}) "
                      f"(umbral {minimum}/10)."),False
    gain=2 if power>=minimum+2.0 else 1
    w['excavation'][k]=w['excavation'].get(k,0)+gain
    progress=w['excavation'][k]
    if progress>=3:
        set_tile(w,tx,ty,z,':' if z==-1 else '.')
        p['inventory']['piedra']=p['inventory'].get('piedra',0)+2
        # El cambio físico comprobado es que la casilla dejó de ser sólida.
        # No atribuir apertura de conexión o atajo sin comprobar rutas.
        return True,(f"Con '{tool['name']}' despejé la casilla ({tx},{ty}) "
                     f"al excavar {TERRAINS.get(kind,kind)}; ahora es transitable "
                     f"y recuperé dos piedras. No comprobé que esto abra "
                     f"una ruta nueva."),True
    return True,(f"Con '{tool['name']}' avancé {gain} unidades de excavación "
                 f"en ({tx},{ty}); acumulado {progress}/3."),False


def inspect_target(w,p,step):
    """Inspección inequívoca de objetos existentes, inventario y terreno visible.

    Un resultado negativo distingue existencia, alcance, terreno no observado
    y nombre desconocido; jamás se interpreta un objeto fijo como desaparecido.
    """
    name=str(step.get('target') or step.get('item') or '').strip().casefold()
    x,y,z=p['pos']
    coords=None
    if 'x' in step or 'y' in step:
        try:coords=(int(step['x']),int(step['y']))
        except (KeyError,ValueError,TypeError):
            return False,['Inspección inválida: especificá ambas coordenadas x e y como números enteros.']
    if coords is None:
        normalized=name.replace('[','(').replace(']',')')
        match=re.search(r'[(]([0-9]{1,2})[ ]*[,;][ ]*([0-9]{1,2})[)]',normalized)
        if not match:match=re.fullmatch(r'[ ]*([0-9]{1,2})[ ]*[,;][ ]*([0-9]{1,2})[ ]*',normalized)
        if match:coords=(int(match.group(1)),int(match.group(2)))
    carried=p.get('items',[])
    structures=w.get('structures',[])
    if name:
        held=next((obj for obj in carried if name==str(obj.get('id','')).casefold()
            or name==str(obj.get('name','')).casefold()),None)
        if held:
            return True,[f"Inspeccioné la herramienta que llevo: {held.get('name')} (ID {held.get('id')}). "
                 f"Forma: {held.get('form','sin registrar')}. Materiales: {', '.join(held.get('materials',[]))}. "
                 f"Durabilidad: {held.get('durability','desconocida')}%. "
                 f"Pruebas registradas: {len(held.get('tests',[]))}. Su función depende de las pruebas, no del nombre."]
        named=[obj for obj in structures if (name==str(obj.get('id','')).casefold()
            or name==str(obj.get('name','')).casefold()
            or (len(name)>=4 and name in str(obj.get('name','')).casefold()))]
    else:named=[]
    by_coordinate=[obj for obj in structures if coords is not None
                   and tuple(obj.get('pos',[])[:2])==coords and
                   len(obj.get('pos',[]))==3 and obj['pos'][2]==z]
    candidates=by_coordinate or named
    if not candidates and not coords and name:
        # Permitir nombres descriptivos de obras sin exigir saber primero su ID.
        candidates=[obj for obj in structures if str(obj.get('name','')).casefold() in name
                    and len(str(obj.get('name','')))>3]
    if candidates:
        candidates.sort(key=lambda obj:(obj.get('pos',[x,y,z])[2]!=z,
            abs(obj.get('pos',[x,y,z])[0]-x)+abs(obj.get('pos',[x,y,z])[1]-y)))
        obj=candidates[0];ox,oy,oz=obj.get('pos',[x,y,z])
        if oz!=z or max(abs(ox-x),abs(oy-y))>4:
            return False,[f"La construcción {obj.get('name')} (ID {obj.get('id')}) consta en mi registro en "
                          f"({ox},{oy},{oz}), pero está fuera de alcance de inspección desde ({x},{y},{z})."]
        if f'{ox},{oy},{oz}' not in w.get('revealed',[]) and (ox,oy)!=(x,y):
            return False,['La construcción está en un sector todavía no observado desde aquí.']
        return True,[f"Inspeccioné mi construcción {obj.get('name')} (ID {obj.get('id')}) en ({ox},{oy},{oz}). "
            f"Materiales: {', '.join(obj.get('materials',[]))}. "
            f"Estado: {obj.get('status','prototipo no evaluado')}. "
            f"Pruebas físicas: {len(obj.get('function_tests',[]))}. "
            "Su presencia es verificable; sus funciones requieren ensayos."]
    if coords is not None:
        tx,ty=coords
        if not valid(tx,ty):return False,[f"Las coordenadas ({tx},{ty}) están fuera del mapa."]
        if max(abs(tx-x),abs(ty-y))>4:
            return False,[f"La casilla ({tx},{ty}) queda fuera del alcance actual (máximo 4 casillas)."]
        if f'{tx},{ty},{z}' not in w.get('revealed',[]):
            return False,[f"El terreno ({tx},{ty},{z}) todavía no fue observado; necesito explorarlo."]
        kind=tile(w,tx,ty,z)
        return True,[f"Inspeccioné el terreno en ({tx},{ty},{z}): {TERRAINS.get(kind,kind)}."]
    observed_target=INSPECT_ALIASES.get(name,name)
    visible=world_view(w,p)
    # world_view se limita a 18 hitos para la interfaz del LLM, pero inspeccionar
    # por nombre no debe perder un objetivo visible por ese truncamiento.
    terrain=None
    if observed_target:
        candidates=[]
        revealed=set(w.get('revealed',[]))
        for ty in range(max(0,y-4),min(H,y+5)):
            for tx in range(max(0,x-4),min(W,x+5)):
                if f'{tx},{ty},{z}' not in revealed:continue
                ch=tile(w,tx,ty,z)
                label=TERRAINS.get(ch,ch)
                if observed_target in label.casefold():
                    candidates.append({'pos':[tx,ty],'tipo':label,'simbolo':ch,
                                      'distancia':abs(tx-x)+abs(ty-y)})
        if candidates:terrain=min(candidates,key=lambda obj:obj['distancia'])
    if not name and visible:terrain=visible[0]
    if terrain:
        facts=[f"Examiné {terrain['tipo']} en {terrain['pos']} (distancia {terrain['distancia']})."]
        if terrain['simbolo']=='v':facts.append('Noté una corriente de aire templado y cristales incrustados.')
        if terrain['simbolo']=='o':facts.append('El afloramiento tiene vetas de dureza irregular.')
        return True,facts
    if name:
        return False,[f"No identifico '{name}' entre las construcciones, herramientas y terrenos "
                      "observables desde aquí. El resultado no demuestra que un objeto lejano haya desaparecido; "
                      'revisá el identificador, las coordenadas y el alcance documentado de inspect.']
    return True,['Observé el suelo y la vegetación sin identificar elementos especiales.']


def execute_action(w,p,step,rng):
    """Ejecuta una única operación verificada; jamás concede efectos por narración del LLM.
    Return duration_minutes, event facts, outcomes, success, notable.
    """
    op=str(step.get('op','')).lower().strip()
    # Despacho físico único para nuevas capacidades: compatible con acciones históricas.
    if op=='interact':
        from capabilities import dispatch
        return dispatch(w,p,step,rng)
    target=str(step.get('target','')).strip().lower()[:70]
    method=str(step.get('method','')).strip().lower()[:40]
    x,y,z=p['pos']; inv=p['inventory']; facts=[]; notable=False; success=True
    duration=8

    missing=missing_physics(step)
    if missing and op=='experiment':
        # Antes de señalar física ausente, verificar que haya muestra real.
        sample=str(step.get('target') or '').casefold()
        if not any(n>0 and mat in sample for mat,n in p.get('inventory',{}).items()):
            p["_last_capability_diagnostic"]={"status":"precondition_failed",
                 "scope":"experiment","reason":"muestra_ausente"}
            return 5,['No tengo una muestra real del material solicitado para ese ensayo.'],False,False
    if missing:
        # Para usar un artefacto tiene que existir físicamente; el vacío del motor
        # no transforma un objeto imaginado en objeto disponible.
        if op=='use':
            item_name=str(step.get('item') or '').strip().casefold()
            held=any(item_name and (i.get('id','').casefold()==item_name or i.get('name','').casefold()==item_name)
                     for i in p.get('items',[]))
            # Un experimento con una base fija es válido si Nilo está junto a ella.
            nearby=any(item_name and (obj.get('id','').casefold()==item_name or obj.get('name','').casefold()==item_name)
                       and len(obj.get('pos',[]))==3 and obj['pos'][2]==z
                       and abs(obj['pos'][0]-x)+abs(obj['pos'][1]-y)<=1
                       for obj in w.get('structures',[]))
            if not (held or nearby):
                return 5,['No tengo el dispositivo indicado a mi alcance para intentar la prueba.'],False,False
        entry=record_unmodeled(p,step,missing,f"Día {int(p.get('clock_minutes',0)//1440)+1}")
        return 6,[no_model_message(entry)],False,False

    if op=='assemble':
        success,result=create_assembly(p,step)
        return 70,[result],success,True
    if op=='forage':
        if inv.get('alimento',0)>=12:
            return 3,[f"Tengo {inv['alimento']} porciones guardadas; no necesito recolectar más ahora. "
                      "Puedo consumir reservas o dedicarme a otra actividad."],False,False
        # Recolección limitada por depósitos del mapa; no aparece comida por narración.
        spots=[(x+dx,y+dy) for dx,dy in [(0,0)]+DIRS if valid(x+dx,y+dy)
               and tile(w,x+dx,y+dy,z) in ('T',',')]
        # Rebrote natural lento: una porción cada 48 h simuladas, máximo tres.
        growth=w.setdefault('forage_growth',{})
        deposits=w.setdefault('forage_deposits',{})
        for sx,sy in spots:
            key=tile_key(sx,sy,z)
            last=growth.get(key,p.get('clock_minutes',0))
            cycles=int(max(0,p.get('clock_minutes',0)-last)//2880)
            if cycles:
                deposits[key]=min(3,deposits.get(key,3)+cycles)
                growth[key]=last+cycles*2880
        source=forage_source(w,p)
        if source is None:
            return 8,['No encontré frutos o vegetación comestible disponible en las casillas cercanas.'],False,False
        sx,sy=source;key=tile_key(sx,sy,z)
        w['forage_deposits'][key]=w['forage_deposits'].get(key,3)-1
        w.setdefault('forage_growth',{}).setdefault(key,p.get('clock_minutes',0))
        inv['alimento']=inv.get('alimento',0)+1
        return 18,[f'Recolecté una porción experimental de alimento vegetal en ({sx},{sy}); tengo {inv["alimento"]}.'],True,True
    if op=='drink':
        if step.get('item') or step.get('source'):
            from capabilities import dispatch
            return dispatch(w,p,{'op':'interact','method':'beber',
                     'source':step.get('item') or step.get('source'),
                     **({'quantity':step['quantity']} if 'quantity' in step else {})},rng)
        from survival import ensure_needs
        needs=ensure_needs(p)
        nearby_water=z==0 and any(valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z)=='~' for dx,dy in DIRS)
        if not nearby_water:return 5,['No tengo agua accesible a mi lado.'],False,False
        needs['hidratacion']=min(100,needs['hidratacion']+25)
        return 8,['Bebí de una fuente de agua cercana. Su potabilidad todavía no está comprobada.'],True,True
    if op=='eat':
        from survival import ensure_needs
        if inv.get('alimento',0)<1:return 5,['No tengo alimentos almacenados.'],False,False
        inv['alimento']-=1
        needs=ensure_needs(p);needs['nutricion']=min(100,needs['nutricion']+35)
        return 12,['Comí una porción de alimento vegetal previamente recolectado.'],True,False
    if op=='explore':
        goal,diagnostic=exploration_frontier(w,p,rng,step)
        if goal is None:
            return 8,[diagnostic or "No encuentro un sector accesible y desconocido desde aquí."],False,False
        starting_position=(x,y)
        travelled,found=move(w,p,goal,9)
        if not travelled and not found:
            return 6,['La frontera elegida no produjo desplazamiento ni nuevas observaciones. Debo reconsiderar la exploración.'],False,False
        duration=max(6,travelled*3)
        facts.append(f"Recorrí {travelled} tramos del nivel {z}, hasta {p['pos'][:2]}.")
        if 'direction' in step or 'region' in step:
            selected=EXPLORATION_DIRECTIONS.get(str(step.get('direction')).casefold().strip())
            requested=('sector solicitado: '+EXPLORATION_LABELS[selected] if selected else 'región solicitada')
            if 'region' in step:
                region=step['region']
                requested+='; anclaje conocido: '+str((int(region['x']),int(region['y'])))
            facts.append('Exploración orientada · '+requested+
                         '; frontera elegida: '+str(goal)+
                         '; dirección neta real: '+actual_travel_direction(starting_position,p['pos'][:2])+
                         '; tramos realmente recorridos: '+str(travelled)+
                         '; casillas nuevas observadas: '+str(len(found))+'.')
        if found:
            interesting=describe_findings(w,found)
            if interesting:
                facts.append("Observé por primera vez: "+', '.join(interesting)+'.');notable=True
    elif op=='go':
        destination,water_target,reason=resolve_go(w,p,step)
        if reason:return 4,[reason],False,False
        tx,ty=destination
        travelled,found=move(w,p,(tx,ty),12)
        if travelled==0 and (x,y)!=(tx,ty):return 4,[f"No encontré ruta transitable hacia ({tx},{ty}) con mis capacidades actuales."],False,False
        duration=max(3,travelled*3)
        if water_target:
            if travelled:
                facts.append(f"Avancé hasta la orilla {p['pos'][:2]}; agua identificada junto a {water_target}.")
            else:
                facts.append(f"Ya estoy en la orilla {p['pos'][:2]}; hay agua adyacente en {water_target}.")
        else:
            facts.append(f"Avancé hasta {p['pos'][:2]}; destino propuesto: ({tx},{ty}).")
        interesting=describe_findings(w,found)
        if interesting:facts.append("Apareció en mi campo de visión: "+', '.join(interesting)+'.');notable=True
    elif op=='inspect':
        success,facts=inspect_target(w,p,step)
        notable=False;duration=6
    elif op=='gather':
        requested=gather_material(target)
        if requested is None:
            return 5,[f"No reconozco '{target}' como material o fuente de recolección. "
                      "Puedo solicitar piedra (roca), madera (arboleda), mineral oscuro "
                      "(afloramiento mineral), arcilla, fibra, cristal u hongo luminoso."],False,False
        nearest=nearest_known(w,p,GATHER_SOURCES[requested])
        if nearest is None:
            return 5,[f"No tengo localizada una fuente accesible y con recursos de {requested}."],False,False
        tx,ty,wx,wy=nearest
        travel=0
        if (x,y)!=(wx,wy) and abs(tx-x)+abs(ty-y)>1:
            travel,discovered=move(w,p,(wx,wy),10)
            facts.append(f"Me acerqué {travel} tramos a la fuente de {requested} en ({tx},{ty}).")
            other=describe_findings(w,discovered)
            if other:facts.append('En el trayecto vi: '+', '.join(other)+'.');notable=True
            # Viajar no equivale a extraer. Si la distancia excede el recorrido
            # máximo, esta acción sigue inconclusa y debe plantearse otra.
            if tuple(p['pos'][:2])!=(wx,wy):
                facts.append(f"Todavía no llegué al depósito de {requested} y no recogí material.")
                return max(5,travel*3),facts,False,notable
        kind=tile(w,tx,ty,z)
        mat=YIELDS[kind][0]
        if requested=='hongo luminoso' and kind=='v':mat='hongo luminoso'
        if mat!=requested:
            return 5,[f"El depósito indicado no produce {requested}; no extraje nada."],False,False
        key=tile_key(tx,ty,z)
        amount=w['deposits'].get(key,0)
        if amount<=0:
            return 8,[f"La fuente de {requested} en ({tx},{ty}) está agotada."],False,False
        qty=min(2,amount)
        inv[mat]=inv.get(mat,0)+qty;w['deposits'][key]=amount-qty
        facts.append(f"Recogí {qty} {'unidad' if qty==1 else 'unidades'} de {mat} del "
                     f"{TERRAINS[kind]} en ({tx},{ty}). Ahora tengo {inv[mat]}.")
        if amount-qty==0:
            facts.append('Agoté el recurso de este lugar.');notable=True
        duration=max(0,travel*3)+12+qty*5
    elif op=='experiment':
        mat=next((m for m in inv if inv.get(m,0)>0 and m in target),None)
        if not mat:return 4,[f"No tengo una muestra de {target or 'ese material'} para experimentar."],False,False
        props=p['materials'].get(mat,MATERIALS.get(mat,{})); method=method or 'golpear'
        observations={"golpear": f"Al golpear {mat}, su dureza estimada es {props.get('dureza',2)}/10.",
                      "calentar": f"Al calentar {mat}, {'se quema con facilidad' if props.get('combustible',0)>=6 else 'no se consume fácilmente'}.",
                      "mojar": f"Tras mojar {mat}, {'se deforma' if props.get('dureza',0)<3 else 'mantiene bastante bien su forma'}.",
                      "cargar": f"Al someter {mat} a una carga, su resistencia estimada es {props.get('resistencia',2)}/10.",
                      "luz": f"Al oscurecer el entorno, {mat} {'emite un brillo propio' if props.get('brillo',0)>5 else 'no produce una iluminación apreciable'}."}
        key=f"{mat}|{method}"
        if key in p['knowledge']:
            return 3,[f"Ya había comprobado cómo responde {mat} al procedimiento '{method}': {p['knowledge'][key]} No obtendría información nueva repitiéndolo sin cambiar las condiciones."],True,False
        text=observations.get(method,f"Probé '{method}' sobre {mat}; no tengo un procedimiento físico específico para medir ese efecto.")
        facts.append(text)
        record_experience(p,'experiment',f'{mat}|{method}',method in observations,text)
        if method in observations and key not in p['knowledge']:
            p['knowledge'][key]=text; facts.append('Es un resultado que no había registrado antes.');notable=True
        duration=18
    elif op=='combine':
        requested=step.get('materials',[])
        if not isinstance(requested,list):requested=[]
        mats=[str(q).lower().strip() for q in requested[:6]]
        if len(mats)<2:
            mats=[m for m,q in inv.items() if q>0][:2]
        counts=collections.Counter(mats)
        if len(mats)<2 or any(inv.get(m,0)<count for m,count in counts.items()):
            return 6,["No tengo suficientes componentes distintos o unidades para combinarlos."],False,False
        for m,count in counts.items():inv[m]-=count
        known=[p['materials'].get(m,MATERIALS.get(m,{})) for m in mats]
        method=method or 'unir'
        avg=lambda key:round(sum(d.get(key,0) for d in known)/len(known),1)
        # La combinación solo cambia propiedades con reglas generales verificables.
        modifier={"atar": 1.15, "apilar": .85,"unir":1.1,"mezclar":.65,"compactar":1.2,"trenzar":1.25}.get(method, .8)
        props={"dureza":avg('dureza'),"resistencia":min(10,round(avg('resistencia')*modifier,1)),"peso":round(sum(d.get('peso',0) for d in known),1),"combustible":avg('combustible'),"brillo":max(d.get('brillo',0) for d in known)}
        key='compuesto '+method+' ('+' + '.join(sorted(mats))+')'
        from statistics import mean
        physical=[material_physics(m,p.get('materials',{})) for m in mats]
        props['density']=round(sum(q['density'] for q in physical)/len(physical),4)
        # Mezclar no vuelve milagrosamente impermeables los componentes.
        props['permeability']=round(max(0.0,min(1.0,mean(q['permeability'] for q in physical))),4)
        p['materials'][key]=props;inv[key]=inv.get(key,0)+1
        facts.append(f"Combiné {', '.join(mats)} mediante '{method}'. Obtuve {key}, resistencia estimada {props['resistencia']}/10.")
        record_experience(p,'combine',key,True,facts[-1])
        notable=True;duration=35
    elif op in ('build','craft'):
        requested=step.get('materials',[])
        if not isinstance(requested,list):requested=[]
        mats=[str(q).lower().strip() for q in requested[:6]]
        if not mats:mats=[m for m,n in inv.items() if n>0][:2]
        counts=collections.Counter(mats)
        name=str(step.get('name') or ('herramienta experimental' if op=='craft' else 'estructura experimental')).strip()[:75]
        purpose=str(step.get('purpose') or 'explorar una posibilidad física').strip()[:110]
        portable=op=='craft' or is_portable(name,step.get('form',''),purpose)
        if not portable:
            category=classify_structure(name,purpose)
            same_site=next((s for s in w.get('structures',[]) if s.get('pos')==p['pos'] and s.get('category')==category and (category=='habitaculo' or s.get('name','').casefold()==name.casefold())),None)
            if same_site:
                return 5,[f"Ya existe '{same_site['name']}' ({same_site['id']}) en este lugar. Antes de construir otro habitáculo o estructura equivalente, puedo evaluar una reforma (modify), reparación o desmontaje."],False,False
        if not mats or any(inv.get(m,0)<n for m,n in counts.items()):
            return 5,["No pude fabricar: me faltan componentes materiales."],False,False
        if step.get('design_id'):
            from inventions import design_materials_error
            mismatch=design_materials_error(p,step['design_id'],mats)
            if mismatch:return 5,[mismatch],False,False
        props_list=[p['materials'].get(m,MATERIALS.get(m,{})) for m in mats]
        score=round(sum(q.get('resistencia',0) for q in props_list)/len(props_list),1)
        # Fabricar una forma esquemática no prueba su eficacia estructural o funcional.
        # La resistencia se conserva como propiedad verificable en pruebas posteriores.
        for m,n in counts.items():inv[m]-=n
        if portable:
            prop={'resistencia':score,'dureza':max(q.get('dureza',0) for q in props_list),
                  'peso':sum(q.get('peso',0) for q in props_list)}
            item=make_item(name,purpose,mats,prop,p.get('clock_minutes',0),step.get('form'),rng=rng)
            item['geometry']=geometry_from_step(step,mats,item['form'])
            item['physics']=body_physics(mats,item['geometry'],p.get('materials',{}))
            item['contents']={}
            initialize_object(item,structure=False)
            if any(d.get('id')==step.get('design_id') for d in p.get('designs',[])):
                item['design_id']=step['design_id']
                item['design_version']=next(d['versions'][-1]['version'] for d in p.get('designs',[]) if d['id']==step['design_id'])
                step['_built_object_id']=item['id']
            p.setdefault('items',[]).append(item)
            facts.append(f"Fabriqué '{name}' y lo guardé conmigo. Forma: {item['form']}. Componentes: {', '.join(mats)}.")
            facts.append('Todavía tengo que comprobar sus posibles usos en una prueba real.')
            equivalent_count=sum(1 for existing in p.get('items',[])[:-1]
                if existing.get('form')==item['form']
                and collections.Counter(existing.get('materials',[]))==counts
                and existing.get('geometry')==item['geometry'])
            if equivalent_count:
                facts.append(f"Es el ejemplar adicional n.º {equivalent_count+1} de esta forma y composición; mantiene ID, revisión y desgaste independientes.")
            record_experience(p,'craft',name,True,facts[0])
        else:
            structure={'id':f"obra-{len(w['structures'])+1}-{physical_suffix(16,rng=rng)}",'name':name,'purpose':purpose,'materials':mats,
                       'resistance':score,'pos':p['pos'][:],'created_by':'nilo',
                       'category':classify_structure(name,purpose),'status':'Prototipo sin funcionamiento verificado',
                       'made_at_minutes':round(p.get('clock_minutes',0),1)}
            structure['geometry']=geometry_from_step(step,mats,'simple')
            structure['physics']=body_physics(mats,structure['geometry'],p.get('materials',{}))
            enrich_structure(structure)
            initialize_object(structure,structure=True,layout=step.get('layout'))
            if any(d.get('id')==step.get('design_id') for d in p.get('designs',[])):
                structure['design_id']=step['design_id']
                structure['design_version']=next(d['versions'][-1]['version'] for d in p.get('designs',[]) if d['id']==step['design_id'])
                step['_built_object_id']=structure['id']
            w['structures'].append(structure)
            facts.append(f"Construí '{name}' en {p['pos'][:]} con {', '.join(mats)}. Resistencia estructural {score}/10.")
            facts.append('La estructura queda en el lugar; su utilidad todavía no está demostrada.')
            record_experience(p,'build',name,True,facts[0])
        notable=True;duration=60
    elif op in ('modify','dismantle'):
        return apply_intervention(w,p,step)
    elif op=='use':
        held=p.setdefault('items',[])
        item_name=str(step.get('item') or step.get('target') or '').strip().lower()
        tool=next((t for t in held if t['name'].lower()==item_name or t['id']==item_name),None)
        if not tool:
            tool=next((t for t in held if item_name and item_name in t['name'].lower()),None)
        if not tool:return 5,[f"No llevo conmigo la herramienta '{item_name}'."],False,False
        desired=str(step.get('method') or step.get('action') or '').lower().strip()
        if tool.get('form')=='ensamblaje':
            ok,msg=test_assembly(p,tool,desired,step)
            tool.setdefault('tests',[]).append({'method':desired,'target':'mecanismo',
                 'result':msg,'success':ok,'pos':list(p['pos']),'revision':tool.get('revision',1)})
            if ok:
                tool['verified_revision']=tool.get('revision',1)
                tool['verified_function_current']=True
            record_experience(p,'use',tool['name'],ok,msg)
            p.setdefault('knowledge',{})[f'ensamblaje|{tool["id"]}|{desired}']=msg
            return 18,[msg],ok,True
        expected=item_effects(tool)
        power=expected.get(desired,0)
        if tool.get('durability',0)<=0:
            return 5,[f"'{tool['name']}' está inutilizable por desgaste."],False,False
        # Fenómenos físicos generales: propiedades y geometría, no nombres o recetas.
        # El líquido existe en el terreno y no tiene que estar en el inventario.
        nearby_water = z==0 and any(valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z)=='~' for dx,dy in DIRS)
        if desired in ('contener','llenar') and ('agua' in target or desired=='llenar'):
            if not nearby_water:
                return 5,['No tengo agua accesible en una casilla adyacente.'],False,False
            result=evaluate_containment(tool,'agua',p.get('materials',{}))
            if not result['possible']:
                msg=f"La geometría de '{tool['name']}' no permite retener agua."
                record_experience(p,'use',tool['name'],False,msg)
                return 10,[msg],False,True
            if tool.get('contents',{}).get('material')=='agua' and tool['contents'].get('quantity',0)>0:
                return 3,[f"'{tool['name']}' ya contiene agua; llenarlo otra vez no aporta información nueva."],True,False
            tool['contents']={'material':'agua','quantity':result['quantity']}
            msg=(f"Llené '{tool['name']}' con {result['quantity']} unidades de agua. "
                 f"Capacidad útil estimada: {result['quantity']} unidades. "
                 "Es un límite inicial calculado por forma y permeabilidad; no mide filtraciones ni pérdida con el tiempo.")
            tool.setdefault('tests',[]).append({'method':'llenar','target':'agua','success':True,'result':msg,'pos':list(p['pos']),'revision':tool.get('revision',1)})
            tool['verified_revision']=tool.get('revision',1)
            tool['verified_function_current']=True
            record_experience(p,'use',tool['name'],True,msg,result)
            p.setdefault('knowledge',{})[f"interaccion|{tool['id']}|agua"]=msg
            return 16,[msg],True,True
        if desired in ('flotar','navegar'):
            if not nearby_water:
                return 5,['Necesito una orilla con agua accesible para probar flotación.'],False,False
            result=evaluate_buoyancy(tool, passenger=desired=='navegar',known=p.get('materials',{}))
            ok=result['floats']
            if desired=='navegar' and result['shape'] not in ('hueco','plataforma'):
                ok=False
            msg=(f"'{tool['name']}': {'flota' if ok else 'se hunde o no soporta la carga'} "
                 f"(empuje {result['buoyant_capacity']}, masa {result['load']}; geometría {result['shape']}).")
            if ok and desired=='navegar':
                p['vehicle_id']=tool['id'];msg+=' Puedo desplazarme por casillas de agua conectadas a la orilla.'
            tool.setdefault('tests',[]).append({'method':desired,'target':'agua','success':ok,'result':msg,'pos':list(p['pos']),'revision':tool.get('revision',1)})
            if ok:
                tool['verified_revision']=tool.get('revision',1)
                tool['verified_function_current']=True
            record_experience(p,'use',tool['name'],ok,msg,result)
            p.setdefault('knowledge',{})[f"flotacion|{tool['id']}|{desired}"]=msg
            return 20,[msg],ok,True
        if power<=0:
            result=f"La forma de '{tool['name']}' no permite ejecutar '{desired}'."
            record_experience(p,'use',tool['name'],False,result)
            return 6,[result],False,False
        target_mat=next((m for m,q in inv.items() if q>0 and m in target),None)
        context_target=target_mat or 'entorno'
        target_spot=adjacent_rock(w,p['pos'],step) if desired=='excavar' else None
        repeated=next((trial for trial in reversed(tool.get('tests',[]))
            if not trial.get('success') and trial.get('method')==desired
            and trial.get('target')==context_target
            and trial.get('revision',1)==tool.get('revision',1)
            and (desired=='golpear' or
                 (desired=='excavar' and target_spot is not None and trial.get('target_pos')==list(target_spot)) or
                 (desired not in ('golpear','excavar') and trial.get('pos')==p['pos']))),None)
        if repeated:
            return 3,[f"Ya comprobé que '{tool['name']}' no funciona así con {context_target}. Sin cambios en la herramienta o las condiciones, repetirlo no aportaría nada."],True,False
        if desired=='golpear':
            if not target_mat:return 5,['No tengo una muestra en el inventario para golpear.'],False,False
            hardness=p['materials'].get(target_mat,MATERIALS.get(target_mat,{})).get('dureza',5)
            success=power>=hardness*.75
            result=f"Probé '{tool['name']}' golpeando {target_mat}: {'dejó una marca' if success else 'no consiguió deformarlo'} (capacidad {power}/10, dureza {hardness}/10)."
        elif desired=='cortar':
            spots=[(x+dx,y+dy) for dx,dy in DIRS if valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z)=='T']
            if not spots:return 5,['No hay vegetación leñosa adyacente que pueda cortar.'],False,False
            success=power>=3.5
            if success:
                tx,ty=spots[0];k=tile_key(tx,ty,z);amount=w['deposits'].get(k,0)
                if amount:
                    w['deposits'][k]-=1;inv['madera']=inv.get('madera',0)+1
            result=(f"Corté madera con '{tool['name']}' y recuperé una unidad." if success and amount else
                    f"Probé el filo de '{tool['name']}' contra un tronco, pero no conseguí extraer madera.")
            success=bool(success and amount)
        elif desired=='excavar':
            success,result,_opened=dig_with_tool(w,p,tool,power,step)
        elif desired=='mover':
            # Solo permite desplazar un obstáculo físico conocido, no inventar objetos.
            spots=[(x+dx,y+dy) for dx,dy in DIRS if valid(x+dx,y+dy) and tile(w,x+dx,y+dy,z)=='^']
            if not spots:return 5,['No hay rocas sueltas adyacentes que desplazar.'],False,False
            success=power>=5
            if success:
                tx,ty=spots[0];set_tile(w,tx,ty,z,'.')
                inv['piedra']=inv.get('piedra',0)+1
                result=f"Utilicé '{tool['name']}' para apartar una roca en ({tx},{ty}) y despejé la casilla."
            else:result=f"'{tool['name']}' se flexionó sin conseguir mover la roca (capacidad {power}/10)."
        elif desired=='contener':
            if not target_mat:return 5,['No tengo un material para probar el recipiente.'],False,False
            success=power>=2.5
            result=(f"El recipiente '{tool['name']}' sostuvo una muestra de {target_mat}." if success else
                    f"El recipiente '{tool['name']}' no sostuvo la muestra de {target_mat}.")
        else:return 5,[f"No existe una prueba física para '{desired}'."],False,False
        tool['durability']=max(0,tool.get('durability',100)- (5 if success else 8))
        # El desgaste debe afectar las piezas reales y hacer posible repararlas.
        if tool.get('components'):
            condition=tool['durability']/100
            for component in tool['components']:
                component['condition']=min(component.get('condition',1.0),condition)
        trial={'method':desired,'target':target_mat or 'entorno','result':result,'success':bool(success),
               'pos':list(p['pos']),'target_pos':list(target_spot) if target_spot else None,
               'at':round(p.get('clock_minutes',0),1),'revision':tool.get('revision',1)}
        tool.setdefault('tests',[]).append(trial)
        tool['tests']=tool['tests'][-15:]
        if success:
            tool['verified_revision']=tool.get('revision',1)
            tool['verified_function_current']=True
        key=f"uso|{tool['id']}|{desired}|{target_mat or 'entorno'}"
        p['knowledge'][key]=result
        record_experience(p,'use',tool['name'],success,result,power)
        facts.append(result)
        if not success:facts.append('Tendré que revisar la forma, los materiales o la estrategia.')
        duration=22;notable=True
    elif op=='excavate':
        # Excavar no es una capacidad mágica: se necesitan forma y potencia adecuadas.
        tools=[(item_effects(t).get('excavar',0),t) for t in p.get('items',[])
               if t.get('durability',0)>0]
        tools.sort(key=lambda v:v[0],reverse=True)
        if not tools or tools[0][0]<=0:
            msg='Para excavar roca necesito una herramienta de punta; no llevo ninguna capaz de hacerlo.'
            record_experience(p,'excavate','sin herramienta',False,msg)
            return 6,[msg],False,False
        power,tool=tools[0]
        step['_used_tool_id']=tool['id']
        # Mismo mecanismo físico y mismas comprobaciones que use/excavar.
        return execute_action(w,p,{'op':'use','item':tool['id'],'method':'excavar',
                 'target':'roca',**{k:step[k] for k in ('x','y') if k in step}},rng)
    elif op in ('descend','ascend'):
        target_level=-1 if op=='descend' else 0
        ex,ey=cave_exit(w)
        is_entrance = (abs(x-ex)+abs(y-ey)<=1)
        if not is_entrance or z==target_level:
            detail=(f"La salida a superficie está en ({ex},{ey},-1); todavía debo regresar por galerías conocidas."
                    if op=='ascend' else 'No hay una conexión entre niveles accesible desde mi posición.')
            return 5,[detail],False,False
        p['pos']=[ex,ey,target_level];new=reveal(w,ex,ey,target_level,3)
        facts.append('Descendí a la cueva; identifiqué la salida hacia superficie.' if op=='descend' else 'Regresé a la superficie siguiendo la salida conocida.')
        interesting=describe_findings(w,new)
        if interesting:facts.append('Descubrí: '+', '.join(interesting)+'.')
        notable=True;duration=14
    elif op=='rest':
        facts.append('Me detuve a descansar y observar el entorno.')
        duration=25
    elif op=='wait':
        facts.append('Dejé transcurrir el tiempo sin realizar una actividad ni descansar. '
                     'Las necesidades evolucionaron con la inactividad habitual.')
        duration=1
    else:
        return 5,[f"No conozco la operación física '{op}'."],False,False
    return duration,facts,success,notable
