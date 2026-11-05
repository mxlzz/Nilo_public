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
from nilo_runtime.worlds.resources import (
    ResourceBalanceError, StockTransfer, stock_units, transfer_units,
    gather_material, nearest_known, forage_source, forage_action,
    harvest_at, cut_wood, gather_action, consume_units,
)
from nilo_runtime.worlds.objects import (
    infer_form, is_portable, item_effects, make_item, physical_item,
    classify_structure, structure_symbol, enrich_structure,
)
from nilo_runtime.worlds.fabrication import combine_action, fabricate_action
from nilo_runtime.worlds.tool_use import adjacent_rock, dig_with_tool, use_action
from nilo_runtime.perception.island import world_view, visible_structures
from nilo_runtime.perception.objects import desgaste_observable


# Objetos portátiles y estructuras ancladas tienen ciclos de vida diferentes.
# Las propiedades derivan de la forma y de los materiales existentes, no del relato del LLM.
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

# tile_key/valid/tile/set_tile/new_world/reveal se reexportan desde
# nilo_runtime.worlds.island. Reglas físicas y navegación siguen aquí
# hasta sus propias etapas (09–12); no existen generadores paralelos.

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
    structures=visible_structures(w)
    if name:
        held=next((obj for obj in carried if name==str(obj.get('id','')).casefold()
            or name==str(obj.get('name','')).casefold()),None)
        if held:
            return True,[f"Inspeccioné la herramienta que llevo: {held.get('name')} (ID {held.get('id')}). "
                 f"Forma: {held.get('form','sin registrar')}. Materiales: {', '.join(held.get('materials',[]))}. "
                 f"Desgaste observable: {desgaste_observable(held.get('durability'))}. "
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
        return forage_action(w,p)
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
        try:
            consume_units(inv,'alimento',1)
        except ResourceBalanceError:
            return 5,['No tengo alimentos almacenados.'],False,False
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
        return gather_action(w,p,step,describe_findings)
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
        return combine_action(p,step,record_experience)
    elif op in ('build','craft'):
        from inventions import design_materials_error
        return fabricate_action(w,p,step,rng,record_experience,
                                initialize_object,design_materials_error)
    elif op in ('modify','dismantle'):
        return apply_intervention(w,p,step)
    elif op=='use':
        return use_action(w,p,step,record_experience,test_assembly)
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
