"""Objetos físicos modificables y planos técnicos 2.5D.

La cuadrícula territorial es un índice de ubicación, no la geometría de un
objeto. Las plantas usan coordenadas locales, dimensiones limitadas por
recursos, y un historial inmutable de versiones. No simula dinámica 3D.
"""
from __future__ import annotations

from nilo_runtime.core.identity import new_uuid
from collections import Counter
from copy import deepcopy
import math
import uuid
import hashlib

DIRECTIONS = {'N', 'S', 'E', 'O'}
from catalogo import RECOVERABILITY


def number(value, default, minimum, maximum):
    try:
        x = float(value)
        return round(max(minimum, min(maximum, x)), 2) if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def _materials(obj):
    return [str(m).strip().lower() for m in obj.get('materials', [])]


def dimensions(materials, raw=None):
    """Dimensiones abstractas en metros, acotadas por material consumido.

    No corresponde a certificación estructural. Cada unidad representa un lote
    de recurso, no una tabla con medidas conocidas.
    """
    raw = raw if isinstance(raw, dict) else {}
    units = max(1, len(materials))
    area_cap = max(1.5, units * 1.7)
    width = number(raw.get('width_m', raw.get('width')), min(3, math.sqrt(area_cap)), .7, min(8, area_cap/.7))
    length = number(raw.get('length_m', raw.get('length')), min(4, area_cap / width), .7, min(10, area_cap/.7))
    if width * length > area_cap:
        length = round(area_cap / width, 2)
    height_cap=min(3.4,1.0+units*.32)
    height = number(raw.get('height_m', raw.get('height')), min(2.1,height_cap), .45, height_cap)
    orientation = str(raw.get('orientation', 'N')).upper()
    if orientation not in DIRECTIONS:orientation = 'N'
    entrance = str(raw.get('entrance', 'S')).upper()
    if entrance not in DIRECTIONS:entrance = 'S'
    zones=[]
    for zone in raw.get('zones', [])[:3] if isinstance(raw.get('zones'), list) else []:
        if isinstance(zone, str): label=zone
        elif isinstance(zone, dict): label=zone.get('name', '')
        else:continue
        label=' '.join(str(label).split())[:18]
        if label and label not in zones:zones.append(label)
    return {'width_m':width,'length_m':length,'height_m':height,
            'orientation':orientation,'entrance':entrance,'zones':zones,
            'area_m2':round(width*length,2),'representation':'2.5d-schematic'}


def _plan(obj):
    """Planta ASCII desde dimensiones internas, sin inventar tabiques.

    Perímetro dibujado solo para habitáculos con suficientes componentes;
    otras estructuras muestran el contorno de su huella, no paredes reales.
    Zonas son usos previstos, no divisiones verificadas.
    """
    d=obj['space'];width= max(12, min(26,round(d['width_m']*4)))
    height=max(5, min(11,round(d['length_m']*2)))
    kind=obj.get('category')
    enclosed=kind=='habitaculo' and len(obj.get('components',[]))>=4
    rows=[list(' '*(width+2)) for _ in range(height+2)]
    for i in range(1,width+1):rows[0][i]=rows[-1][i]='-' if enclosed else '.'
    for j in range(1,height+1):rows[j][0]=rows[j][-1]='|' if enclosed else ':'
    for xx,yy in ((0,0),(0,height+1),(width+1,0),(width+1,height+1)):
        rows[yy][xx]='+' if enclosed else '.'
    if enclosed:
        e=d.get('entrance','S')
        if e=='S':
            for xx in (width//2,width//2+1):rows[-1][xx]=' '
        elif e=='N':
            for xx in (width//2,width//2+1):rows[0][xx]=' '
        elif e=='E':rows[height//2][-1]=rows[height//2+1][-1]=' '
        elif e=='O':rows[height//2][0]=rows[height//2+1][0]=' '
    labels=d.get('zones') or []
    if not labels: labels=['ESPACIO INTERIOR' if enclosed else 'HUELLA']
    positions=[round((height)*(i+1)/(len(labels)+1)) for i in range(len(labels))]
    for label,y in zip(labels,positions):
        label=label.upper()[:max(4,width-2)]
        start=max(1, (width+2-len(label))//2)
        for idx,ch in enumerate(label):rows[y][start+idx]=ch
    legend=('Perimetro aproximado; entrada '+d.get('entrance','S') if enclosed
            else 'Contorno de ocupacion, sin cerramiento verificado')
    return 'N ^  PLANTA / '+d.get('orientation','N')+'\n'+('\n'.join(''.join(row) for row in rows))+(
        f"\n{d['width_m']:.2f} x {d['length_m']:.2f} m; h {d['height_m']:.2f} m"
        f'\n{legend}'
        + ('\nZonas: usos propuestos, no tabiques comprobados.' if d.get('zones') else '')
        + '\nEsquema, no plano ejecutivo.' )


def _tool_scheme(obj):
    pieces=obj.get('components',[])
    return ('ESQUEMA DE PIEZAS (sin escala)\n'
            + '\n'.join(f"[{n:02}] {p['material']} / {p['id']}" for n,p in enumerate(pieces,1))
            + '\nUniones y forma detallada: no modeladas.' )


def _components(materials):
    return [{'id':'cmp-'+new_uuid().hex[:9],'material':m,'condition':1.0}
            for m in materials]


def ensure_object(obj, *, structure=False):
    """Migra obras/herramientas anteriores sin fingir detalles desconocidos."""
    obj.setdefault('components',_components(_materials(obj)))
    if not isinstance(obj.get('space'),dict):
        obj['space']=dimensions(_materials(obj),obj.get('layout'))
    if structure:
        obj.setdefault('category','prototipo')
        obj.setdefault('revision',1)
        obj.setdefault('revisions',[])
        if obj.get('category')=='habitaculo':
            obj.setdefault('shelter_condition', 'cubierto_parcialmente' if len(obj.get('components',[]))>=4 and float(obj.get('resistance',0))>=3 else 'insuficiente')
        if not obj['revisions']:
            obj['revisions'].append(_version(obj, 'Inventario inicial', 'Registro de geometría aproximada; no se observaron subdivisiones internas.'))
    else:
        obj.setdefault('revision',1)
        obj.setdefault('revisions',[])
        if not obj['revisions']:
            obj['revisions'].append(_version(obj, 'Inventario inicial', 'Registro de componentes originales; forma detallada desconocida.'))
    return obj


def _version(obj,operation,observation):
    return {'revision':obj.get('revision',1),'operation':operation,'at_minute':obj.get('made_at_minutes',obj.get('created_at_minutes',0)),
            'materials':list(_materials(obj)),'components':deepcopy(obj.get('components',[])),
            'space':deepcopy(obj['space']),
            'schematic':_plan(obj) if 'category' in obj else _tool_scheme(obj),
            'observation':observation}


def initialize_object(obj, *, structure=False, layout=None):
    obj['components']=_components(_materials(obj))
    obj['space']=dimensions(_materials(obj),layout)
    obj['revision']=1
    if structure and obj.get('category')=='habitaculo':
        obj['shelter_condition']='cubierto_parcialmente' if len(obj['components'])>=4 and float(obj.get('resistance',0))>=3 else 'insuficiente'
    obj['revisions']=[_version(obj,'Construcción inicial','Geometría estimada a partir de recursos reales.')]
    return obj


def find_object(world,person,identifier):
    identifier=str(identifier or '').strip().casefold()
    if not identifier:return None,None
    buildings=world.get('structures',[])
    tools=person.get('items',[])
    for objs,kind in ((buildings,'structure'),(tools,'tool')):
        match=next((obj for obj in objs if str(obj.get('id','')).casefold()==identifier),None)
        if match:return kind,match
    matches=[(kind,obj) for objs,kind in ((buildings,'structure'),(tools,'tool')) for obj in objs
             if str(obj.get('name','')).casefold()==identifier]
    if len(matches)==1:return matches[0]
    return None,None


def _score(person,mat):
    data=person.get('materials',{}).get(mat, {})
    return float(data.get('resistencia', 3))


def recompute(obj,person):
    mats=[c['material'] for c in obj['components']]
    obj['materials']=mats
    strength=sum(_score(person,m)*c.get('condition',1.0) for m,c in zip(mats,obj['components']))/max(1,len(mats))
    obj['resistance']=round(strength,2)
    if obj.get('portable'):
        obj['hardness']=max((float(person.get('materials',{}).get(m,{}).get('dureza',2)) for m in mats),default=0.0)
        obj['weight']=round(sum(float(person.get('materials',{}).get(m,{}).get('peso',2)) for m in mats),2)
    obj['space']=dimensions(mats,obj.get('space'))
    if obj.get('category') == 'habitaculo':
        obj['shelter_condition']='cubierto_parcialmente' if len(mats)>=4 and strength>=3 else 'insuficiente'
    if obj.get('portable'):
        from physics import body_physics
        from world import item_effects
        obj['durability']=max(0,min(100,round(100*sum(c['condition'] for c in obj['components'])/max(1,len(mats)))))
        obj['physics']=body_physics(mats,obj.get('geometry',{}),person.get('materials',{}))
        obj['possible_uses']=item_effects(obj)
    else:
        from physics import body_physics
        obj['physics']=body_physics(mats,obj.get('geometry',{}),person.get('materials',{}))


def salvage(components,person,*, complete=False):
    """Recuperación entera por lote; sin recursos fraccionarios creados.

    Para una única pieza desmontada, el resultado es probabilístico pero
    determinista por condición y material (sin aleatoriedad gratuita).
    """
    counts=Counter()
    # Acumular fracciones por tipo para lograr recuperación parcial de lotes.
    scores={}
    for c in components:
        m=c['material'];ratio=RECOVERABILITY.get(m,.5)*number(c.get('condition',1),1,0,1)
        scores[m]=scores.get(m,0)+ratio
    for m,score in scores.items():
        recovered=int(score+1e-9)
        remaining=score-recovered
        # Un lote aislado también puede recuperarse; decisión estable según ID.
        if remaining>0:
            identities=','.join(c['id'] for c in components if c['material']==m)
            roll=int.from_bytes(hashlib.sha256((m+identities).encode()).digest()[:8],'big') / 2**64
            if roll<remaining:recovered+=1
        if recovered>0:
            counts[m]=recovered
            person['inventory'][m]=person['inventory'].get(m,0)+recovered
    return dict(counts)


def apply_intervention(world,person,step):
    """Modificar/reparar/desarmar objetos identificables y accesibles.

    No modifica el mundo si falla la validación. Ejecuta la operación sobre
    componentes reales: retirar, sustituir, agregar, reparar o desmontar.
    """
    op=str(step.get('op','')).lower()
    kind,obj=find_object(world,person,step.get('item') or step.get('target') or step.get('object'))
    if not obj:return 5,['No identifico un objeto existente; necesito su ID o nombre exacto.'],False,False
    if kind=='structure':
        pos=obj.get('pos',[]);me=person['pos']
        if len(pos)!=3 or pos[2]!=me[2] or abs(pos[0]-me[0])+abs(pos[1]-me[1])>1:
            return 5,['Para modificar esa obra primero debo acercarme a ella.'],False,False
    ensure_object(obj,structure=kind=='structure')
    if op=='modify':
        mode=str(step.get('mode','add')).lower()
        if mode not in ('add','replace','remove','repair'):
            return 5,['Modificación inválida: usar add, replace, remove o repair.'],False,False
    elif op=='dismantle':mode='all' if step.get('all',True) else 'remove'
    else:return 5,['Operación de intervención no reconocida.'],False,False
    requested=step.get('materials',[])
    requested=requested if isinstance(requested,list) else []
    mats=[str(m).strip().lower() for m in requested[:8]]
    inv=person['inventory'];cost=Counter(mats)
    existing=obj['components']
    cid=str(step.get('component','')).strip().casefold()
    chosen=next((c for c in existing if c['id'].casefold()==cid),None) if cid else None
    if chosen is None and cid:
        matches=[c for c in existing if c['material'].casefold()==cid]
        if len(matches)==1:chosen=matches[0]
    if mode in ('replace','remove','repair') and chosen is None and not (mode=='remove' and op=='dismantle'):
        return 5,['Debo indicar el ID de un componente existente para intervenirlo.'],False,False
    if mode=='remove' and chosen is None:
        return 5,['Para desmontar parcialmente necesito indicar una pieza concreta.'],False,False
    if mode in ('add','replace','repair') and not mats:
        return 5,['Para esa intervención necesito indicar materiales nuevos que voy a consumir.'],False,False
    if mode in ('add','replace','repair') and any(m not in person.get('materials',{}) for m in cost):
        return 5,['Uno de los materiales propuestos no existe como material constructivo conocido.'],False,False
    if mode in ('add','replace','repair') and any(inv.get(m,0)<n for m,n in cost.items()):
        return 5,['No tengo suficientes materiales para intervenir el objeto.'],False,False
    from vessels import preflight_intervention
    content_problem=preflight_intervention(person,obj,mode,chosen,mats)
    if content_problem:
        return 5,[content_problem],False,False
    if kind=="structure":
        from structural_loads import preflight_intervention as preflight_loads
        load_problem=preflight_loads(person,obj,mode,chosen,mats)
        if load_problem:
            return 5,[load_problem],False,False
    if mode=='add' and len(existing)+len(mats)>40:
        return 5,['La ampliación supera el máximo de componentes que puedo representar.'],False,False
    if mode=='all':
        recovered=salvage(existing,person,complete=True)
        if kind=='structure':
            world['structures'].remove(obj)
            archived=world.setdefault('retired_structures',[])
            obj['status']='Desmontada';obj['revision']+=1
            obj['made_at_minutes']=round(person.get('clock_minutes',0),1)
            obj['revisions'].append(_version(obj,'Desmontaje total','Se retiraron los componentes existentes.'))
            archived.append(obj)
        else:
            person['items'].remove(obj)
            person.setdefault('retired_items',[]).append(obj)
        return 32,[f"Desmonté completamente '{obj['name']}'. Recuperé {recovered or 'ningún lote completo'}; los demás materiales se perdieron o quedaron inutilizables."],True,True
    former_components=deepcopy(existing)
    removed=[]
    if mode in ('remove','replace'):
        existing.remove(chosen)
        removed=[chosen]
    elif mode=='repair':
        if chosen.get('condition',1)>=.95:
            return 5,['Esa pieza no presenta desgaste que justifique repararla.'],False,False
    for m,n in cost.items():inv[m]-=n
    recovered=salvage(removed,person) if removed else {}
    if mode in ('add','replace'):existing.extend(_components(mats))
    if mode=='repair':chosen['condition']=min(1., chosen['condition']+.25*len(mats))
    if not existing:
        if kind=='structure':
            world['structures'].remove(obj);world.setdefault('retired_structures',[]).append(obj)
        else:
            person['items'].remove(obj);person.setdefault('retired_items',[]).append(obj)
        obj['status']='Desmontada'
    if obj.get('form')=='ensamblaje':
        # El ensamblaje mantiene sólo uniones entre piezas que siguen existiendo.
        original_parts=obj.get('parts',[])
        by_id={c['id']:original_parts[i] for i,c in enumerate(former_components) if i<len(original_parts)}
        old_index={c['id']:i for i,c in enumerate(former_components)}
        current_index={c['id']:i for i,c in enumerate(obj['components'])}
        remapped=[]
        for edge in obj.get('joints',[]):
            a,b=edge.get('a'),edge.get('b')
            if isinstance(a,int) and isinstance(b,int) and 0<=a<len(former_components) and 0<=b<len(former_components):
                ca,cb=former_components[a]['id'],former_components[b]['id']
                if ca in current_index and cb in current_index:
                    remapped.append({'a':current_index[ca],'b':current_index[cb],'type':edge.get('type','fija')})
        if mode=='replace' and removed and mats:
            # Una sustitución conserva la interfaz original de la pieza reemplazada.
            old_id=removed[0]['id'];old_idx=old_index[old_id]
            new_id=obj['components'][-len(mats)]['id']
            for edge in obj.get('joints',[]):
                a,b=edge.get('a'),edge.get('b')
                if a==old_idx or b==old_idx:
                    other=b if a==old_idx else a
                    if isinstance(other,int) and 0<=other<len(former_components):
                        old_other=former_components[other]['id']
                        if old_other in current_index:
                            remapped.append({'a':current_index[new_id] if a==old_idx else current_index[old_other],
                                             'b':current_index[old_other] if a==old_idx else current_index[new_id],
                                             'type':edge.get('type','fija')})
            original=by_id.get(old_id,{})
            by_id[new_id]={'name':original.get('name','pieza sustituida'),'shape':original.get('shape','macizo')}
        obj['parts']=[{'name':by_id.get(c['id'],{}).get('name','pieza añadida'),
                       'material':c['material'],
                       'shape':by_id.get(c['id'],{}).get('shape','macizo')}
                      for c in obj['components']]
        obj['joints']=remapped
    recompute(obj,person)
    obj['revision']+=1
    obj['made_at_minutes']=round(person.get('clock_minutes',0),1)
    obj['status']='Modificada, función pendiente de comprobar' if existing else 'Desmontada'
    # Las pruebas permanecen para consulta histórica; una versión nueva no
    # hereda la certificación funcional de la versión anterior.
    previous_rev=obj['revision']-1
    if obj.get('rest_evidence_ids') or obj.get('function_tests'):
        obj.setdefault('past_function_evidence',[]).append({
            'revision':previous_rev,'rest_evidence_ids':obj.pop('rest_evidence_ids',[]),
            'function_tests':obj.pop('function_tests',[])})
    obj['verified_revision']=None
    obj['verified_function_current']=False
    # Toda modificación invalida pruebas del estado anterior; se preserva historia.
    obj['last_intervention']={'operation':mode,'used':mats,'recovered':recovered}
    obj.setdefault('revisions',[]).append(_version(obj,mode,'Sin nueva prueba funcional; cambios materiales realizados.'))
    if 'layout' in step and existing:
        # No conceder dimensiones sin recursos: sólo orientación/usos previstos.
        update=step['layout'] if isinstance(step['layout'],dict) else {}
        if update:
            normalized=dimensions(obj['materials'],{**obj['space'],**update})
            obj['space']=normalized
            obj['revisions'][-1]=_version(obj,mode,'Reorganización propuesta; espacios no evaluados funcionalmente.')
    return 30,[f"Intervine '{obj['name']}' (v{obj['revision']}, {mode}). Materiales empleados: {mats or 'ninguno'}; recuperados: {recovered or 'ningún lote completo'}. Conservé su historial y esquema."],True,True
