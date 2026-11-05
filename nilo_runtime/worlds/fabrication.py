"""Fabricación de compuestos, herramientas y estructuras para isla_v1.

Este módulo decide y aplica únicamente transformaciones materiales verificadas.
Recibe colaboradores desde el orquestador para que el dominio no importe
world.py, la aplicación ni el cuaderno, evitando ciclos de dependencias.
Las cantidades se validan antes de producir objetos o nuevos materiales.
"""
from __future__ import annotations

import collections
from statistics import mean

from catalogo import MATERIALS, FORMS
from nilo_runtime.core.identity import physical_suffix
from nilo_runtime.physics.materials import (
    geometry_from_step, body_physics, properties as material_physics,
)
from nilo_runtime.worlds.resources import (
    ResourceBalanceError, material_counts, check_materials, exchange_units,
)
from nilo_runtime.worlds.objects import (
    physical_item, item_effects, classify_structure, enrich_structure,
)


def combine_action(p,step,record_experience):
    """Convierte lotes físicos en un compuesto, sin acreditación parcial."""
    inv=p["inventory"]
    facts=[];notable=False
    method=str(step.get("method","")).strip().lower()[:40]
    requested=step.get('materials',[])
    if not isinstance(requested,list):requested=[]
    mats=[str(q).lower().strip() for q in requested[:6]]
    if len(mats)<2:
        mats=[m for m,q in inv.items() if q>0][:2]
    try:
        counts=material_counts(mats)
        enough=check_materials(inv,counts)
    except ResourceBalanceError:
        enough=False
    if len(mats)<2 or not enough:
        return 6,["No tengo suficientes componentes distintos o unidades para combinarlos."],False,False
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
    try:
        exchange_units(inv,counts,{key:1})
    except ResourceBalanceError:
        return 6,["La combinación no pudo conservar el balance material."],False,False
    p['materials'][key]=props
    facts.append(f"Combiné {', '.join(mats)} mediante '{method}'. Obtuve {key}, resistencia estimada {props['resistencia']}/10.")
    record_experience(p,'combine',key,True,facts[-1])
    notable=True;duration=35
    return duration,facts,True,notable


def fabricate_action(w,p,step,rng,record_experience,initialize_object,check_design):
    """Prepara una entidad real y debita unidades al publicarla en el mundo."""
    inv=p["inventory"]
    facts=[];notable=False
    op=str(step.get("op","")).lower().strip()
    requested=step.get('materials',[])
    if not isinstance(requested,list):requested=[]
    mats=[str(q).lower().strip() for q in requested[:6]]
    if not mats:mats=[m for m,n in inv.items() if n>0][:2]
    try:
        counts=material_counts(mats)
    except ResourceBalanceError:
        return 5,["La composición contiene materiales inválidos."],False,False
    name=str(step.get('name') or ('herramienta experimental' if op=='craft' else 'estructura experimental')).strip()[:75]
    purpose=str(step.get('purpose') or 'explorar una posibilidad física').strip()[:110]
    # El nombre o el propósito del artefacto no concede portabilidad:
    # craft produce un elemento transportable; build exige forma explícita.
    portable=op=='craft' or str(step.get('form','')).casefold().strip() in FORMS
    if not portable:
        category=classify_structure(name,purpose)
        same_site=next((s for s in w.get('structures',[]) if s.get('pos')==p['pos'] and s.get('category')==category and (category=='habitaculo' or s.get('name','').casefold()==name.casefold())),None)
        if same_site:
            return 5,[f"Ya existe '{same_site['name']}' ({same_site['id']}) en este lugar. Antes de construir otro habitáculo o estructura equivalente, puedo evaluar una reforma (modify), reparación o desmontaje."],False,False
    try:
        enough=check_materials(inv,counts)
    except ResourceBalanceError:
        enough=False
    if not mats or not enough:
        return 5,["No pude fabricar: me faltan componentes materiales."],False,False
    if step.get('design_id'):
        mismatch=check_design(p,step['design_id'],mats)
        if mismatch:return 5,[mismatch],False,False
    props_list=[p['materials'].get(m,MATERIALS.get(m,{})) for m in mats]
    score=round(sum(q.get('resistencia',0) for q in props_list)/len(props_list),1)
    # Fabricar una forma esquemática no prueba su eficacia estructural o funcional.
    # La resistencia se conserva como propiedad verificable en pruebas posteriores.
    # La creación física se prepara sin gastar lotes; el débito ocurre
    # una sola vez, inmediatamente antes de publicar la entidad.
    if portable:
        prop={'resistencia':score,'dureza':max(q.get('dureza',0) for q in props_list),
              'peso':sum(q.get('peso',0) for q in props_list)}
        item=physical_item(name,purpose,mats,prop,p.get('clock_minutes',0),step.get('form'),rng=rng)
        item['geometry']=geometry_from_step(step,mats,item['form'])
        item['possible_uses']=item_effects(item)
        item['physics']=body_physics(mats,item['geometry'],p.get('materials',{}))
        item['contents']={}
        initialize_object(item,structure=False)
        if any(d.get('id')==step.get('design_id') for d in p.get('designs',[])):
            item['design_id']=step['design_id']
            item['design_version']=next(d['versions'][-1]['version'] for d in p.get('designs',[]) if d['id']==step['design_id'])
            step['_built_object_id']=item['id']
        exchange_units(inv,counts)
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
        exchange_units(inv,counts)
        w['structures'].append(structure)
        facts.append(f"Construí '{name}' en {p['pos'][:]} con {', '.join(mats)}. Resistencia estructural {score}/10.")
        facts.append('La estructura queda en el lugar; su utilidad todavía no está demostrada.')
        record_experience(p,'build',name,True,facts[0])
    notable=True;duration=60
    return duration,facts,True,notable
