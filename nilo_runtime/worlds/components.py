"""Componentes y uniones: validación física pura sin mutar inventario/objeto.

Las etiquetas visibles de las piezas no alteran su geometría o las conexiones.
El catálogo determina formas y tipos de unión; el grafo debe ser conexo.
"""
from __future__ import annotations

from catalogo import JOINTS, SHAPES


def normalize_parts(raw, known_materials):
    """Piezas verificadas o mensaje histórico de precondición."""
    if not isinstance(raw,list) or not 2 <= len(raw) <= 10:
        return None,'Un mecanismo requiere entre dos y diez piezas concretas.'
    clean=[]
    for part in raw:
        if not isinstance(part,dict):
            return None,'Una pieza no tiene descripción válida.'
        name=str(part.get('name',''))[:70]
        material=str(part.get('material','')).lower().strip()
        shape=str(part.get('shape','macizo')).lower()
        if not name or material not in known_materials or shape not in SHAPES:
            return None,f'Pieza inválida o material no reconocido: {name}/{material}/{shape}.'
        clean.append({'name':name,'material':material,'shape':shape})
    return clean,None


def normalize_joints(raw, part_count):
    """Transcribe uniones declaradas, sin deducir conexiones por nombres."""
    if not isinstance(raw,list) or len(raw)>18 or not raw:
        return None,'No hay conexiones físicas entre las piezas.'
    joints=[]
    for edge in raw:
        try:
            if not isinstance(edge,dict):
                return None,'Conexión inválida.'
            if any(type(edge[k]) is bool for k in ('a','b')):
                return None,'Conexión inválida.'
            numeric=[edge['a'],edge['b']]
            for raw in numeric:
                if isinstance(raw,float) and not raw.is_integer():
                    return None,'Conexión inválida.'
                if isinstance(raw,str) and not raw.isdecimal():
                    return None,'Conexión inválida.'
            a,b=int(edge['a']),int(edge['b'])
            kind=str(edge['type']).lower()
        except (KeyError,TypeError,ValueError,OverflowError):
            return None,'Conexión inválida.'
        if kind not in JOINTS or not (0<=a<part_count and 0<=b<part_count) or a==b:
            return None,'Conexión fuera de las piezas o con unión inexistente.'
        joints.append({'a':a,'b':b,'type':kind})
    return joints,None


def connected_parts(part_count,joints):
    """Chequeo estructural puro; no acredita movimiento ni resistencia."""
    if type(part_count) is not int or part_count<1:
        return False
    seen={0}
    changed=True
    while changed:
        size=len(seen)
        for edge in joints:
            if not isinstance(edge,dict):
                return False
            a,b=edge.get('a'),edge.get('b')
            if (type(a) is not int or type(b) is not int or a==b
                    or not (0<=a<part_count and 0<=b<part_count)
                    or edge.get('type') not in JOINTS):
                return False
            if a in seen:seen.add(b)
            if b in seen:seen.add(a)
        changed=len(seen)!=size
    return len(seen)==part_count
