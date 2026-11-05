"""Interacciones físicas de herramientas del entorno isla_v1.

Formas, recursos, resistencia y topología verificable gobiernan las acciones.
El cuaderno se pasa por callback; el dominio no depende del dispatcher ni LLM.
"""
from __future__ import annotations

import math

from catalogo import MATERIALS, TERRAINS
from nilo_runtime.worlds.island import DIRS, valid, tile, tile_key, set_tile
from nilo_runtime.worlds.objects import item_effects
from nilo_runtime.worlds.resources import cut_wood, exchange_units, ResourceBalanceError
from nilo_runtime.physics.materials import evaluate_containment, evaluate_buoyancy


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
    progress=w['excavation'].get(k,0)+gain
    if progress>=3:
        try:
            exchange_units(p['inventory'],credits={'piedra':2})
        except ResourceBalanceError:
            return False,'No pude registrar la piedra sin un balance válido.',False
        w['excavation'][k]=progress
        set_tile(w,tx,ty,z,':' if z==-1 else '.')
        # El cambio físico comprobado es que la casilla dejó de ser sólida.
        # No atribuir apertura de conexión o atajo sin comprobar rutas.
        return True,(f"Con '{tool['name']}' despejé la casilla ({tx},{ty}) "
                     f"al excavar {TERRAINS.get(kind,kind)}; ahora es transitable "
                     f"y recuperé dos piedras. No comprobé que esto abra "
                     f"una ruta nueva."),True
    w['excavation'][k]=progress
    return True,(f"Con '{tool['name']}' avancé {gain} unidades de excavación "
                 f"en ({tx},{ty}); acumulado {progress}/3."),False



def use_action(w,p,step,record_experience,test_assembly):
    """Prueba una capacidad en circunstancias físicas observables."""
    target=str(step.get('target','')).strip().lower()[:70]
    inv=p['inventory']
    x,y,z=p['pos']
    facts=[];notable=False;success=True;duration=8
    held=p.get('items',[])
    item_name=str(step.get('item') or step.get('target') or '').strip().lower()
    tool=next((t for t in held if item_name and t.get('id')==item_name),None)
    if tool is None and item_name:
        exact=[t for t in held if str(t.get('name','')).lower()==item_name]
        choices=exact or [t for t in held if item_name in str(t.get('name','')).lower()]
        if len(choices)>1:
            return 5,["Varias herramientas coinciden; necesito el ID único."],False,False
        tool=choices[0] if choices else None
    if not tool:return 5,[f"No llevo conmigo la herramienta '{item_name}'."],False,False
    desired=str(step.get('method') or step.get('action') or '').lower().strip()
    if tool.get('durability',100)<=0:
        return 5,[f"'{tool['name']}' está inutilizable por desgaste."],False,False
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
        contents=tool.get('contents') or {}
        if not isinstance(contents,dict):
            return 5,["El contenido registrado del objeto es inválido; no lo sobrescribí."],False,False
        try:
            held_amount=float(contents.get('quantity',0))
        except (TypeError,ValueError,OverflowError):
            return 5,["El contenido registrado no es medible; no lo sobrescribí."],False,False
        if not math.isfinite(held_amount) or held_amount<0:
            return 5,["La reserva del recipiente tiene un saldo inválido."],False,False
        if held_amount>0:
            if contents.get('material')=='agua':
                return 3,[f"'{tool['name']}' ya contiene agua; llenarlo otra vez no aporta información nueva."],True,False
            return 5,["El recipiente contiene otro material; debo retirarlo antes de llenarlo con agua."],False,False
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
            tx,ty=spots[0];amount=1 if cut_wood(w,p,tx,ty,z) else 0
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
            tx,ty=spots[0]
            try:
                exchange_units(inv,credits={'piedra':1})
            except ResourceBalanceError:
                return 5,["No puedo acreditar piedra con el inventario actual."],False,False
            set_tile(w,tx,ty,z,'.')
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
    return duration,facts,success,notable
