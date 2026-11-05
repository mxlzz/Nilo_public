"""Pruebas genéricas de ensamblajes: uniones, carga, movimiento y energía térmica.

Unidades abstractas, deliberadamente no equivalentes a ingeniería real.
Cada resultado requiere componentes, recursos y condiciones concretas.
"""
from __future__ import annotations

from nilo_runtime.core.identity import new_uuid
from collections import Counter
from nilo_runtime.worlds.resources import ResourceBalanceError, check_materials, exchange_units
import uuid

from catalogo import JOINTS, SHAPES
from nilo_runtime.worlds.components import normalize_parts, normalize_joints, connected_parts


def create_assembly(person, step):
    """Inventaría un ensamblaje material real; verifica insumos y conexiones."""
    clean,error=normalize_parts(step.get('parts',[]),person.get('materials',{}))
    if error:return False,error
    required=Counter(p['material'] for p in clean)
    inv=person.get('inventory',{})
    if not check_materials(inv,dict(required)):
        return False,'No tengo suficientes materiales para ensamblar todas las piezas.'
    design_id=str(step.get('design_id') or '').strip()
    if design_id:
        from inventions import design_materials_error
        mismatch=design_materials_error(person,design_id,[piece['material'] for piece in clean])
        if mismatch:return False,mismatch
    connections,error=normalize_joints(step.get('joints',[]),len(clean))
    if error:return False,error
    if not connected_parts(len(clean),connections):
        return False,'El conjunto tiene piezas sin conectar.'
    # Consumo atómico: no modificar inventario antes de pasar validación completa.
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
    exchange_units(inv,dict(required))
    person.setdefault('items',[]).append(item)
    if design_id:step['_built_object_id']=item['id']
    return True,f"Construí '{item['name']}' con {len(clean)} piezas y {len(connections)} uniones; todavía debo probarlo."


def test_assembly(person,item,method,step):
    """Ensayo independiente del nombre del aparato. No crea trabajo mecánico gratuito."""
    if item.get('form')!='ensamblaje':return False,'No es un ensamblaje de piezas.'
    parts=item.get('parts',[]);joints=item.get('joints',[])
    if len(parts)<2 or not joints:return False,'El ensamblaje no tiene suficientes piezas conectadas para probar esa función.'
    # Las uniones se validan con el mismo grafo que la construcción.
    if not connected_parts(len(parts),joints):
        return False,'El ensamblaje contiene piezas desconectadas: necesito reparar sus uniones.'
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
