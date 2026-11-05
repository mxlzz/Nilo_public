"""Proyección visual efímera de la casilla físicamente intervenida.

No forma parte de la memoria del agente ni modifica el mundo. Nunca se
interpreta una ruta, el lugar del agente o una herramienta portátil como
el sitio de intervención de otra entidad.
"""
import re

from world import (
    DIRS, H, W, GATHER_SOURCES, INSPECT_ALIASES, TERRAINS,
    adjacent_rock, forage_source, gather_material, item_effects,
    nearest_known, tile, tile_key, valid, world_view,
)
from construction import find_object
from world import is_portable


def _visible(w, point):
    if point is None:
        return None
    x,y,z=point
    if not valid(x,y) or str(z) not in w.get('levels',{}):
        return None
    if tile_key(x,y,z) not in w.get('revealed',[]):
        return None
    return {'x':x,'y':y,'z':z}


def _inspection_site(w,p,step):
    """Replica las mismas prioridades de inspección: inventario, obra, terreno."""
    x,y,z=p['pos']
    name=str(step.get('target') or step.get('item') or '').strip().casefold()
    coords=None
    if 'x' in step or 'y' in step:
        try:
            coords=(int(step['x']),int(step['y']))
        except (KeyError,TypeError,ValueError,OverflowError):
            return None
    if coords is None:
        normalized=name.replace('[','(').replace(']',')')
        match=re.search(r'[(]([0-9]{1,2})[ ]*[,;][ ]*([0-9]{1,2})[)]',normalized)
        if not match:
            match=re.fullmatch(r'[ ]*([0-9]{1,2})[ ]*[,;][ ]*([0-9]{1,2})[ ]*',normalized)
        if match:
            coords=int(match.group(1)),int(match.group(2))
    if name and any(name==str(obj.get('id','')).casefold()
                    or name==str(obj.get('name','')).casefold()
                    for obj in p.get('items',[])):
        return None  # Objeto portátil: no señalar la casilla del portador.
    structures=w.get('structures',[])
    named=([obj for obj in structures
            if name==str(obj.get('id','')).casefold()
            or name==str(obj.get('name','')).casefold()
            or (len(name)>=4 and name in str(obj.get('name','')).casefold())]
           if name else [])
    by_coordinate=[obj for obj in structures if coords is not None
                   and tuple(obj.get('pos',[])[:2])==coords
                   and len(obj.get('pos',[]))==3 and obj['pos'][2]==z]
    candidates=by_coordinate or named
    if not candidates and coords is None and name:
        candidates=[obj for obj in structures
                    if str(obj.get('name','')).casefold() in name
                    and len(str(obj.get('name','')))>3]
    if candidates:
        obj=min(candidates,key=lambda ob:(ob.get('pos',[x,y,z])[2]!=z,
            abs(ob.get('pos',[x,y,z])[0]-x)+abs(ob.get('pos',[x,y,z])[1]-y)))
        ox,oy,oz=obj.get('pos',[x,y,z])
        if oz!=z or max(abs(ox-x),abs(oy-y))>4:
            return None
        return _visible(w,(ox,oy,oz)) if (ox,oy)==(x,y) or tile_key(ox,oy,oz) in w.get('revealed',[]) else None
    if coords is not None:
        tx,ty=coords
        if max(abs(tx-x),abs(ty-y))<=4:
            return _visible(w,(tx,ty,z))
        return None
    observed=INSPECT_ALIASES.get(name,name)
    if observed:
        candidates=[]
        for ty in range(max(0,y-4),min(H,y+5)):
            for tx in range(max(0,x-4),min(W,x+5)):
                if tile_key(tx,ty,z) not in w.get('revealed',[]):continue
                label=TERRAINS.get(tile(w,tx,ty,z),tile(w,tx,ty,z))
                if observed in label.casefold():
                    candidates.append((abs(tx-x)+abs(ty-y),tx,ty))
        if candidates:
            _,tx,ty=min(candidates,key=lambda v:v[0])
            return _visible(w,(tx,ty,z))
    elif not name:
        visible=world_view(w,p)
        if visible:
            tx,ty=visible[0]['pos']
            return _visible(w,(tx,ty,z))
    return None


def active_intervention(w,p,pending):
    """Ubicación real verificable durante una operación todavía pendiente."""
    if not isinstance(pending,dict) or p.get('unconscious'):
        return None
    step=pending.get('step')
    if not isinstance(step,dict):
        return None
    # Mientras se camina, el destino de la ruta no es un trabajo sobre él.
    if pending.get('navigation'):
        return None
    op=str(step.get('op','')).lower()
    x,y,z=p['pos']
    point=None
    if op=='inspect':
        point=_inspection_site(w,p,step)
    elif op=='gather':
        requested=gather_material(step.get('target'))
        if requested:
            spot=nearest_known(w,p,GATHER_SOURCES[requested])
            if spot:
                tx,ty,wx,wy=spot
                if (x,y)==(wx,wy) or abs(tx-x)+abs(ty-y)<=1:
                    point=_visible(w,(tx,ty,z))
    elif op=='forage':
        if p.get('inventory',{}).get('alimento',0)<12:
            source=forage_source(w,p)
            if source:
                point=_visible(w,(*source,z))
    elif op in ('excavate','use') and (op=='excavate'
            or str(step.get('method') or step.get('action') or '').lower().strip()=='excavar'):
        if op=='use':
            name=str(step.get('item') or step.get('target') or '').strip().lower()
            held=p.get('items',[])
            tool=next((obj for obj in held if obj.get('name','').lower()==name or obj.get('id')==name),None)
            if not tool:
                tool=next((obj for obj in held if name and name in obj.get('name','').lower()),None)
            if not tool or tool.get('durability',0)<=0 or item_effects(tool).get('excavar',0)<=0:
                return None
        else:
            if not any(obj.get('durability',0)>0 and item_effects(obj).get('excavar',0)>0
                       for obj in p.get('items',[])):
                return None
        spot=adjacent_rock(w,p['pos'],step)
        if spot is not None:
            point=_visible(w,(*spot,z))
    elif op in ('modify','dismantle'):
        kind,obj=find_object(w,p,step.get('item') or step.get('target') or step.get('object'))
        if kind=='structure' and obj:
            pos=obj.get('pos',[])
            if len(pos)==3 and pos[2]==z and abs(pos[0]-x)+abs(pos[1]-y)<=1:
                point=_visible(w,tuple(pos))
    elif op=='build':
        name=str(step.get('name') or 'estructura experimental').strip()[:75]
        purpose=str(step.get('purpose') or 'explorar una posibilidad física').strip()[:110]
        if not is_portable(name,step.get('form',''),purpose):
            point=_visible(w,(x,y,z))
    if point is None:
        return None
    return {**point,'op':op}
