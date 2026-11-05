"""Pruebas genéricas de ensamblajes: uniones, carga, movimiento y energía térmica.

Unidades abstractas, deliberadamente no equivalentes a ingeniería real.
Cada resultado requiere componentes, recursos y condiciones concretas.
"""
from __future__ import annotations

from nilo_runtime.core.identity import new_uuid
from collections import Counter
import uuid

from catalogo import JOINTS, SHAPES


def create_assembly(person, step):
    """Inventaría un ensamblaje material real; verifica insumos y conexiones."""
    parts=step.get('parts',[])
    if not isinstance(parts,list) or not 2<=len(parts)<=10:
        return False,'Un mecanismo requiere entre dos y diez piezas concretas.'
    clean=[]
    for p in parts:
        if not isinstance(p,dict):return False,'Una pieza no tiene descripción válida.'
        name=str(p.get('name',''))[:70];mat=str(p.get('material','')).lower().strip()
        shape=str(p.get('shape','macizo')).lower()
        if not name or mat not in person.get('materials',{}) or shape not in SHAPES:
            return False,f'Pieza inválida o material no reconocido: {name}/{mat}/{shape}.'
        clean.append({'name':name,'material':mat,'shape':shape})
    required=Counter(p['material'] for p in clean)
    inv=person.get('inventory',{})
    if any(inv.get(m,0)<n for m,n in required.items()):
        return False,'No tengo suficientes materiales para ensamblar todas las piezas.'
    design_id=str(step.get('design_id') or '').strip()
    if design_id:
        from inventions import design_materials_error
        mismatch=design_materials_error(person,design_id,[piece['material'] for piece in clean])
        if mismatch:return False,mismatch
    edges=step.get('joints',[])
    if not isinstance(edges,list) or len(edges)>18 or not edges:
        return False,'No hay conexiones físicas entre las piezas.'
    connections=[]
    for e in edges:
        try:
            a,b=int(e['a']),int(e['b']);kind=str(e['type']).lower()
        except (KeyError,TypeError,ValueError):return False,'Conexión inválida.'
        if kind not in JOINTS or not (0<=a<len(clean) and 0<=b<len(clean)) or a==b:
            return False,'Conexión fuera de las piezas o con unión inexistente.'
        connections.append({'a':a,'b':b,'type':kind})
    found={0};changed=True
    while changed:
        before=len(found)
        for e in connections:
            if e['a'] in found:found.add(e['b'])
            if e['b'] in found:found.add(e['a'])
        changed=len(found)!=before
    if len(found)!=len(clean):return False,'El conjunto tiene piezas sin conectar.'
    # Consumo atómico: no modificar inventario antes de pasar validación completa.
    for m,n in required.items():inv[m]-=n
    materials=[p['material'] for p in clean]
    properties=[person['materials'][m] for m in materials]
    resistance=min(float(q.get('resistencia',3)) for q in properties)
    item={'id':'mec-'+new_uuid().hex[:10], 'name':str(step.get('name','Ensamblaje'))[:85],
          'form':'ensamblaje','purpose':str(step.get('purpose',''))[:220],
          'materials':materials,'parts':clean,'joints':connections,
          'resistance':resistance,'hardness':max(float(q.get('dureza',2)) for q in properties),
          'weight':sum(float(q.get('peso',3)) for q in properties),
          'durability':100,'tests':[],'portable':True,'contents':{},'geometry':{'shape':'macizo','size':len(clean)},
          'possible_uses':{'carga':True,'transmision':True}}
    if design_id:
        design=next(d for d in person['designs'] if d['id']==design_id)
        item['design_id']=design_id
        item['design_version']=design['versions'][-1]['version']
    from construction import initialize_object
    initialize_object(item,structure=False)
    person.setdefault('items',[]).append(item)
    if design_id:step['_built_object_id']=item['id']
    return True,f"Construí '{item['name']}' con {len(clean)} piezas y {len(connections)} uniones; todavía debo probarlo."


def test_assembly(person,item,method,step):
    """Ensayo independiente del nombre del aparato. No crea trabajo mecánico gratuito."""
    if item.get('form')!='ensamblaje':return False,'No es un ensamblaje de piezas.'
    parts=item.get('parts',[]);joints=item.get('joints',[])
    if len(parts)<2 or not joints:return False,'El ensamblaje no tiene suficientes piezas conectadas para probar esa función.'
    connected={0};changed=True
    while changed:
        previous=len(connected)
        for edge in joints:
            a,b=edge.get('a'),edge.get('b')
            if not (isinstance(a,int) and isinstance(b,int) and 0<=a<len(parts) and 0<=b<len(parts)):
                return False,'Hay una unión inválida tras la reforma.'
            if a in connected:connected.add(b)
            if b in connected:connected.add(a)
        changed=len(connected)!=previous
    if len(connected)!=len(parts):return False,'El ensamblaje contiene piezas desconectadas: necesito reparar sus uniones.'
    try:load=max(0.,min(100.,float(step.get('load',3))))
    except (ValueError,TypeError):load=3
    limits=max(0.,float(item.get('resistance',0)))*1.5
    if method in ('carga','resistir_carga'):
        ok=load<=limits
        return ok,f"Ensayo de carga {load:.1f} unidades frente a resistencia {limits:.1f}: {'soporta' if ok else 'cede'}."
    if method in ('transmision','transmitir_movimiento'):
        mobility=any(j['type'] in ('articulada','deslizante') for j in joints)
        has_mobile_shape=any(p['shape'] in ('rueda','eje','cilindro') for p in parts)
        input_energy=max(0.,min(100.,float(step.get('input_energy',0))))
        result=round(min(limits,input_energy*.65),2) if mobility and has_mobile_shape else 0.
        ok=result>0
        return ok,f"Ensayo de transmisión: energía aplicada {input_energy}, salida {result} (hay movimiento: {ok})."
    return False,f"El motor no simula '{method}' en ensamblajes. Podría solicitar que se incorpore como fenómeno general."
