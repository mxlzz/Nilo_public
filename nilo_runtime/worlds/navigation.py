"""Rutas, accesibilidad, fronteras y movimiento en isla_v1.

Sin conocimiento privilegiado: known_only usa revealed, conservando orden DIRS,
orden de candidatos y consumo del RNG. No hay caché persistida de rutas.
"""
from __future__ import annotations

import collections
from catalogo import TERRAINS
from nilo_runtime.worlds.island import (
    W,H,PASSABLE,DIRS,tile_key,valid,tile,reveal,
)


def cave_exit(w):
    """Portal real y su posición en el subsuelo; los mapas heredados se migran."""
    site=w.get('sites',{}).get('cueva', {'x':23,'y':7})
    return int(site.get('x',23)),int(site.get('y',7))


def known_exit_route(w,person):
    """Desanda solo galerías descubiertas; nunca revela atravesando roca."""
    x,y,z=person['pos']
    if z!=-1:return None
    ex,ey=cave_exit(w)
    if tile_key(ex,ey,-1) not in set(w.get('revealed',[])):
        return None
    path=pathfind(w,(x,y,-1),(ex,ey,-1),known_only=True)
    return path if path or (x,y)==(ex,ey) else None


def passable(w,x,y,z): return tile(w,x,y,z) in PASSABLE


class NavigationIndex:
    """BFS determinista, con padres y distancias de una sola fuente.

    Índice local a una consulta: no muta estado ni queda desactualizado tras
    excavación, revelado o desplazamiento. None = inaccesible; [] = origen.
    """
    def __init__(self, world, origin, allow_water=False, known_only=False, target=None):
        self.origin=tuple(origin)
        self.level=origin[2]
        self.parents={}
        self.distances={}
        sx,sy,z=origin
        if not valid(sx,sy) or str(z) not in world.get('levels',{}):
            return
        known=set(world.get('revealed',())) if known_only else None
        self.parents[(sx,sy)]=None
        self.distances[(sx,sy)]=0
        pending=collections.deque([(sx,sy)])
        while pending:
            x,y=pending.popleft()
            if (x,y)==target:break
            for dx,dy in DIRS:
                nx,ny=x+dx,y+dy
                if (nx,ny) in self.parents or not valid(nx,ny):continue
                if known is not None and tile_key(nx,ny,z) not in known:continue
                ground=tile(world,nx,ny,z)
                if ground not in PASSABLE and not (allow_water and z==0 and ground=='~'):
                    continue
                self.parents[(nx,ny)]=(x,y)
                self.distances[(nx,ny)]=self.distances[(x,y)]+1
                pending.append((nx,ny))

    def distance(self,target):
        return self.distances.get(tuple(target))

    def path_to(self,target):
        current=tuple(target)
        if current not in self.parents:return None
        result=[]
        while self.parents[current] is not None:
            result.append(current)
            current=self.parents[current]
        result.reverse()
        return result


def pathfind(w,origin,target,allow_water=False,known_only=False):
    sx,sy,sz=origin;tx,ty,tz=target
    if (sz!=tz or not valid(tx,ty) or str(sz) not in w.get('levels',{}) or
        not (passable(w,tx,ty,tz) or
             (allow_water and tz==0 and tile(w,tx,ty,tz)=='~'))):
        return []
    if known_only and tile_key(tx,ty,tz) not in set(w.get('revealed',())):
        return []
    path=NavigationIndex(w,origin,allow_water=allow_water,
                         known_only=known_only,target=(tx,ty)).path_to((tx,ty))
    return path if path is not None else []


def reachable_shores(w, person, target_water=None, max_results=8):
    """Orillas *conocidas*, alcanzables a pie desde la ubicación actual.

    Cada destino es suelo transitable junto a agua conocida. La búsqueda de
    caminos es la misma del resto del motor; el agua no se vuelve caminable.
    Si se especifica una casilla acuática conocida, se restringe a su cuerpo
    de agua conocido para evitar desviar a Nilo hacia otro sitio sin motivo.
    """
    x,y,z=person['pos']
    if z!=0:return []
    known=set(w.get('revealed',[]))
    if target_water is not None:
        tx,ty=target_water
        if not valid(tx,ty) or tile_key(tx,ty,z) not in known or tile(w,tx,ty,z)!='~':return []
        water={(tx,ty)};pending=collections.deque([(tx,ty)])
        while pending:
            wx,wy=pending.popleft()
            for dx,dy in DIRS:
                nx,ny=wx+dx,wy+dy
                if (nx,ny) not in water and valid(nx,ny) and tile_key(nx,ny,z) in known and tile(w,nx,ny,z)=='~':
                    water.add((nx,ny));pending.append((nx,ny))
    else:
        water={(int(parts[0]),int(parts[1])) for k in known
               for parts in [k.split(',')] if len(parts)==3 and parts[2]=='0'
               and tile(w,int(parts[0]),int(parts[1]),0)=='~'}
    routes=NavigationIndex(w,(x,y,z),known_only=True)
    candidates={}
    for wx,wy in water:
        for dx,dy in DIRS:
            sx,sy=wx+dx,wy+dy
            if not valid(sx,sy) or tile_key(sx,sy,z) not in known or not passable(w,sx,sy,z):continue
            route=routes.path_to((sx,sy))
            if route is None:continue
            score=len(route)
            if (sx,sy) not in candidates or score<candidates[(sx,sy)][0]:
                candidates[(sx,sy)]=(score,(wx,wy),route)
    return [{'shore':[sx,sy], 'water':list(item[1]),'steps':item[0], 'route':item[2]}
            for (sx,sy),item in sorted(candidates.items(),key=lambda v:(v[1][0], v[0][1],v[0][0]))[:max_results]]


def resolve_go(w,p,step):
    """Devuelve destino terrestre, agua objetivo opcional y diagnóstico verificable.

    Acepta go x/y a agua conocida, o go target=agua. No inventa playas
    accesibles ni presupone conexiones subterráneas. Con embarcación se conserva
    la navegación directa sobre agua.
    """
    x,y,z=p['pos']
    if str(step.get('target','')).strip().lower() in ('agua','orilla','costa','rio','río','lago'):
        shores=reachable_shores(w,p)
        if not shores:
            return None,None,('No tengo localizada una orilla de agua que pueda alcanzar caminando desde aquí. '
                              'Necesito explorar el terreno conocido o reconsiderar el recorrido.')
        best=shores[0]
        return tuple(best['shore']),tuple(best['water']),''
    try:tx,ty=int(step['x']),int(step['y'])
    except (ValueError,TypeError,KeyError):return None,None,'El destino no tiene coordenadas válidas.'
    if not valid(tx,ty):return None,None,'El destino está fuera de los límites del territorio representado.'
    known=tile_key(tx,ty,z) in set(w.get('revealed',[]))
    if not known:
        return None,None,('No conozco aún la casilla solicitada. Puedo explorar una frontera '
                          'visible, pero no deducir qué hay en un destino oculto.')
    terrain=tile(w,tx,ty,z)
    if z==0 and terrain=='~' and not p.get('vehicle_id') and known:
        shores=reachable_shores(w,p,(tx,ty))
        if shores:
            best=shores[0]
            return tuple(best['shore']),(tx,ty),''
        return None,(tx,ty),(f'El destino ({tx},{ty}) es agua: no puedo caminar dentro de ella. '
                             'Tampoco encuentro una orilla conocida y alcanzable a pie de ese cuerpo de agua.')
    if known and terrain not in PASSABLE and not (p.get('vehicle_id') and z==0 and terrain=='~'):
        return None,None,(f'La casilla ({tx},{ty}) es {TERRAINS.get(terrain,terrain)} y no es transitable '
                          'con mis capacidades actuales.')
    route=pathfind(w,(x,y,z),(tx,ty,z),allow_water=bool(p.get('vehicle_id')),known_only=True)
    if not route and (x,y)!=(tx,ty):
        return None,None,(f'No existe actualmente una ruta transitable hasta ({tx},{ty}) desde {tuple(p["pos"][:2])}. '
                          'No tengo evidencia para atribuirlo a un obstáculo concreto no observado.')
    return (tx,ty),None,''

def move(w,p,target,steps=9):
    x,y,z=p['pos']; tx,ty=target
    # La ruta ejecutada nunca atraviesa casillas ocultas para ahorrar distancia.
    route=pathfind(w,(x,y,z),(tx,ty,z),allow_water=bool(p.get('vehicle_id')),
                   known_only=True)
    if not route and (x,y)!=(tx,ty):return 0,[]
    travel=route[:steps]
    if travel:
        p['pos']=[*travel[-1],z]
        trail=w.setdefault('trail',[])
        for sx,sy in travel:
            trail.append(tile_key(sx,sy,z))
        if len(trail)>80:
            del trail[:-80]
    px,py,pz=p['pos']; new=reveal(w,px,py,pz,2)
    key=tile_key(px,py,pz);w['visited'][key]=w['visited'].get(key,0)+1
    trail=w.setdefault('trail',[])
    if not trail or trail[-1]!=key:
        trail.append(key)
        if len(trail)>80:
            del trail[:-80]
    return len(travel),new


# Desplazamientos progresivos. La ruta es parte del estado persistente de la tarea.
# Un paso lleva tres minutos del mundo; a velocidad ×60 equivale a tres segundos reales.
TRAVEL_MINUTES_PER_TILE = 3.0


# Direcciones físicas: norte = -Y, sur = +Y, este = +X, oeste = -X.
# Solo se utilizan casillas reveladas: el anclaje NO predice lo que hay detrás.
EXPLORATION_DIRECTIONS = {
    'north':'north', 'norte':'north', 'n':'north',
    'south':'south', 'sur':'south', 's':'south',
    'east':'east', 'este':'east', 'e':'east',
    'west':'west', 'oeste':'west', 'o':'west', 'w':'west'
}
EXPLORATION_LABELS={'north':'norte','south':'sur','east':'este','west':'oeste'}


def exploration_frontier(w,p,rng,step):
    """Selecciona una frontera conocida alcanzable, sin consultar territorio oculto.

    'explore' sin opciones conserva EXACTAMENTE el algoritmo anterior, incluido RNG.
    Si hay region, direction se interpreta respecto del anclaje; si no, respecto
    de la posición actual del agente. Los sectores se respetan estrictamente.
    """
    if 'direction' not in step and 'region' not in step:
        return choose_frontier(w,p,rng),''
    x,y,z=p['pos']
    direction=step.get('direction')
    if direction is not None:
        direction=EXPLORATION_DIRECTIONS.get(str(direction).casefold().strip())
        if direction is None:
            return None,'La dirección de exploración no es válida: usá north, south, east o west.'
    origin=(x,y)
    if 'region' in step:
        region=step['region']
        if not isinstance(region,dict) or 'x' not in region or 'y' not in region:
            return None,'La región de exploración requiere coordenadas conocidas x e y.'
        try:
            rx,ry=int(region['x']),int(region['y'])
        except (TypeError,ValueError,OverflowError):
            return None,'La región de exploración tiene coordenadas inválidas.'
        if not valid(rx,ry) or tile_key(rx,ry,z) not in set(w.get('revealed',[])):
            return None,'No conozco la región indicada en este nivel: explorar no revela destinos ocultos por anticipado.'
        origin=(rx,ry)
    known=set(w.get('revealed',[]))
    routes=NavigationIndex(w,(x,y,z),allow_water=bool(p.get('vehicle_id')),
                           known_only=True)
    ox,oy=origin
    candidates=[]
    # La secuencia de revelación es estable entre procesos y replays.
    # Iterar un set introduciría un consumo RNG dependiente del hash de Python.
    for k in w['revealed']:
        tx,ty,tz=map(int,k.split(','))
        if tz!=z or not (passable(w,tx,ty,z) or
                        (p.get('vehicle_id') and z==0 and tile(w,tx,ty,z)=='~')):
            continue
        if not any(valid(tx+dx,ty+dy) and tile_key(tx+dx,ty+dy,z) not in known
                   for dx,dy in DIRS):continue
        if direction=='north' and ty>=oy:continue
        if direction=='south' and ty<=oy:continue
        if direction=='east' and tx<=ox:continue
        if direction=='west' and tx>=ox:continue
        distance=routes.distance((tx,ty))
        if distance is None:continue
        # El anclaje dirige por proximidad, sin elegir un destino oculto.
        proximity=abs(tx-ox)+abs(ty-oy)
        score=(distance*0.75+proximity*0.7+
               w.get('visited',{}).get(k,0)*2+rng.random()*0.3)
        candidates.append((score,ty,tx))
    if not candidates:
        qualifier=(' hacia el '+EXPLORATION_LABELS[direction]) if direction else ''
        qualifier+=(' desde la región conocida '+str(origin)) if 'region' in step else ''
        return None,('No encuentro una frontera desconocida, transitable y alcanzable'+qualifier+
                     '. No voy a cambiar silenciosamente al sector opuesto.')
    _,ty,tx=min(candidates)
    return (tx,ty),''


def actual_travel_direction(origin,position):
    """Dirección comprobada por desplazamiento neto; cero no es cardinal."""
    dx=position[0]-origin[0];dy=position[1]-origin[1]
    parts=[]
    if dy:parts.append('norte' if dy<0 else 'sur')
    if dx:parts.append('este' if dx>0 else 'oeste')
    return '-'.join(parts) if parts else 'sin desplazamiento'


def advance_navigation(w,p,nav,steps_due):
    """Ejecuta cada casilla vencida: posición, descubrimientos y rastro real."""
    route=nav['route'];steps_due=min(len(route),max(0,int(steps_due)))
    while nav['walked']<steps_due:
        nx,ny=route[nav['walked']];px,py,pz=p['pos']
        if pz!=nav['level'] or abs(nx-px)+abs(ny-py)!=1 or not (passable(w,nx,ny,pz) or (pz==0 and p.get('vehicle_id') and tile(w,nx,ny,pz)=='~')):
            nav['blocked']=True
            ch=tile(w,nx,ny,pz)
            if pz==0 and ch=='~' and not p.get('vehicle_id'):
                nav['blocked_reason']=f'La siguiente casilla ({nx},{ny}) contiene agua; no puedo entrar caminando.'
            elif ch not in PASSABLE:
                nav['blocked_reason']=f'La siguiente casilla ({nx},{ny}) es {TERRAINS.get(ch,ch)} y bloquea el paso.'
            else:
                nav['blocked_reason']='El camino previsto ya no es válido con la posición y el nivel actuales.'
            return
        p['pos']=[nx,ny,pz]
        # Se desembarca automáticamente al alcanzar tierra firme.
        if p.get('vehicle_id') and tile(w,nx,ny,pz)!='~':p['vehicle_id']=None
        nav['walked']+=1
        new=reveal(w,nx,ny,pz,2)
        nav['discovered'].extend([[xx,yy,ch] for xx,yy,ch in new])
        key=tile_key(nx,ny,pz)
        w['visited'][key]=w['visited'].get(key,0)+1
        trail=w.setdefault('trail',[])
        trail.append(key)
        if len(trail)>80:del trail[:-80]


def choose_frontier(w,p,rng):
    x,y,z=p['pos'];known=set(w['revealed']);opts=[]
    routes=NavigationIndex(w,(x,y,z),allow_water=bool(p.get('vehicle_id')),
                           known_only=True)
    for k in w['revealed']:
        tx,ty,tz=map(int,k.split(','))
        if tz!=z or not (passable(w,tx,ty,z) or (p.get('vehicle_id') and z==0 and tile(w,tx,ty,z)=='~')):continue
        if not any(tile_key(tx+dx,ty+dy,z) not in known and valid(tx+dx,ty+dy) for dx,dy in DIRS):continue
        distance=routes.distance((tx,ty))
        if distance is None:continue
        opts.append((distance+rng.random()*3+w['visited'].get(k,0)*2, (tx,ty)))
    if not opts:return None
    opts.sort(key=lambda n:n[0]);return rng.choice(opts[:min(6,len(opts))])[1]


