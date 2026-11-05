"""Preparar una síntesis factual de registros pendientes para un narrador externo.

Las referencias proceden del motor y del archivo, no de texto proporcionado
por el navegador. Nunca se considera la fecha del resumen como checkpoint.
"""
from __future__ import annotations
from record_links import record_title
from review_store import TABS,KINDS

CATEGORIES={
 'event':'event','research':'research','prediction':'prediction',
 'measurement':'measurement','conclusion':'conclusion','finding':'conclusion',
 'design':'design','proposal':'proposal','project':'project',
 'experience':'experience','habit':'habit','plan':'construction',
}
def record_for(kind,item_id,state,archive):
    category=CATEGORIES.get(kind)
    if category:
        found=archive.latest_record(category,item_id)
        if kind=='plan' and found is None:found=archive.latest_record('tool',item_id)
        if found:return found
    p=state['person'];w=state['world']
    arrays={
      'research':p.get('research',[]),'prediction':p.get('prediction_log',[]),
      'measurement':p.get('measurements',[]),'conclusion':p.get('conclusions',[]),
      'finding':p.get('conclusions',[]),'design':p.get('designs',[]),
      'proposal':p.get('proposals',[]),'project':p.get('projects',[])+([p['project']] if p.get('project') else []),
      'agenda':p.get('agenda',[]),'experience':p.get('experience_summary',[]),
      'habit':p.get('waiting_history',[]),'event':state.get('events',[]),
      'plan':w.get('structures',[])+w.get('retired_structures',[])+p.get('items',[]),
    }
    if kind=='knowledge':
        value=dict(p.get('knowledge',{})).get(item_id)
        return {'id':item_id,'text':str(value)} if value is not None else None
    if kind=='skill':
        value=p.get('skills',{}).get(item_id)
        return {'id':item_id,**value} if isinstance(value,dict) else None
    for item in arrays.get(kind,[]):
        if not isinstance(item,dict):continue
        if str(item.get('id',''))==item_id:return item
        if kind=='plan' and item.get('name')==item_id:return item
    return None

def describe_record(kind,record):
    if kind=='knowledge':return record.get('text','')
    if kind=='skill':return 'Habilidad '+str(record.get('op',''))+'; '+str(record.get('last_fact',''))
    fields={
      'event':('text',),'research':('question','hypothesis','conclusion','state'),
      'prediction':('hypothesis','expected_effect','status'),
      'measurement':('op','target','verified_facts','evaluation_status'),
      'finding':('text','scope','status'),'conclusion':('text','scope','status'),
      'design':('name','status'),'plan':('name','purpose','status'),
      'proposal':('title','phenomenon','rationale','status'),
      'project':('title','reason','state','status'),
      'agenda':('titulo','motivo','estado'),
      'experience':('fact',),'habit':('fact','reason','action'),
    }.get(kind,('text',))
    parts=[]
    for k in fields:
        value=record.get(k)
        if isinstance(value,str) and value.strip():parts.append(value.strip())
        elif isinstance(value,list):parts.extend(str(v) for v in value[:3])
    return ' · '.join(parts)[:330]

# Prioridad editorial para el observador. No es una recompensa, experiencia ni
# señal enviada al agente: clasifica registros documentados, no intenciones.
# El orden secundario por secuencia evita decisiones aleatorias entre empates.
MIN_IMPORTANCE = 56
SUMMARY_PAGE_SIZE = 7

_BASE_IMPORTANCE={
    'proposal':105, 'project':100, 'conclusion':99, 'finding':99,
    'design':91, 'plan':88, 'research':83, 'prediction':77,
    'measurement':61, 'knowledge':62, 'journal':57,
    'news':50, 'event':49, 'agenda':49,
    'experience':45, 'skill':37, 'habit':18
}
_IMPORTANT_TERMS=(
    ('completad',12),('terminad',10),('conclu',12),('descubr',14),
    ('verificad',13),('evidencia',11),('comprob',11),('constru',10),
    ('fabric',8),('propuest',13),('proyecto',12),('investig',9),('hipótes',10),('encontr',9),('conseguí',10),('logré',10),('limitaci',14),('contradicci',14),
    ('incompatib',14),('error del motor',12),('abandon',9),
    ('cambio de estrategia',12),('nuevo proyecto',10),('no evaluable',7),
)
_ROUTINE_TERMS=(
    'descansé','comí','bebí','rutina','me acerqué','avancé','recogí',
    'no obtendría información nueva','recuperé energía','sin novedades',
    'repetirlo no aportaría','sin cambios','esperando'
)

def importance(record):
    """Puntaje explicable de relevancia; no lee secretos ni inventa conclusiones."""
    kind=record.get('kind','')
    text=str(record.get('text','')).casefold()
    score=_BASE_IMPORTANCE.get(kind,45)
    score+=min(25,sum(weight for term,weight in _IMPORTANT_TERMS if term in text))
    if any(term in text for term in _ROUTINE_TERMS):
        score-=27 if kind in ('journal','news','event','measurement') else 8
    if kind=='prediction':
        if any(term in text for term in ('descartad','contradich','refutad','confirmad')):score+=14
    if kind=='measurement' and any(term in text for term in ('variable_no_medida','no evaluable')):
        score+=12
    return max(0,min(140,score))

def pending_sources(state,archive,review,candidates,limit=SUMMARY_PAGE_SIZE,
                    max_seq=None,score_ceiling=None,include_omitted=False):
    """Seleccionar lo importante entre TODOS los pendientes, no los 100 más viejos.

    Devolver solo referencias de fichas incluidas en esta página. La lectura se
    confirma más tarde y nunca afecta fichas omitidas. Una continuación usa el
    tope de puntuación anterior y la secuencia inicial de archivo para que
    nuevas publicaciones no se interpongan en el orden editorial.
    """
    result=[]
    for category in ('journal','news'):
        for item in archive.unread(category):
            if max_seq is not None and item.get('seq',0)>max_seq:continue
            if category=='journal' and state['person'].get('pending',{}):
                pending=state['person']['pending']
                if pending and pending.get('journal_id')==item.get('id'):continue
            result.append({'category':category,'id':item['id'],
                'kind':category,'tab':'notes' if category=='journal' else 'activity',
                'when':item.get('when',''),'text':str(item.get('text') if category=='journal'
                        else (item.get('title','')+' · '+item.get('detail','')))[:330],
                'seq':item.get('seq',0)})
    if not isinstance(candidates,list):raise ValueError('Selección de registros inválida')
    if len(candidates)>1500:raise ValueError('Demasiados registros pendientes')
    for item in candidates:
        if not isinstance(item,dict):continue
        tab,key,kind,rid=(item.get(k) for k in ('tab','key','kind','id'))
        if (tab not in TABS or kind not in KINDS or not isinstance(key,str) or
            not (0<len(key)<=300) or not isinstance(rid,str) or not (0<len(rid)<=120)):
            continue
        if review.is_seen(tab,key):continue
        source=record_for(kind,rid,state,archive)
        if not source:continue
        category=CATEGORIES.get(kind,kind)
        if kind=='plan' and archive.get('construction',rid) is None and archive.get('tool',rid):category='tool'
        seq=archive.seq_for(category,rid) or 0
        if max_seq is not None and seq>max_seq:continue
        result.append({'category':category,'tab':tab,'key':key,'kind':kind,'id':rid,
          'when':str(source.get('when',source.get('started','')))[:60],
          'text':describe_record(kind,source),'seq':seq})
    # Un mismo hallazgo visible en dos solapas se resume y acusa una única vez,
    # pero conserva las marcas por solapa. Lo mismo para otros IDs repetidos.
    unique={}
    for r in result:
        kind='conclusion' if r['kind']=='finding' else 'plan' if r['kind']=='plan' else r['kind']
        identity=(kind,r['id'])
        if identity in unique:
            unique[identity]['aliases'].append({k:r[k] for k in ('tab','key','category','id') if k in r})
            continue
        unique[identity]=dict(r,aliases=[])
    for r in unique.values():r['priority']=importance(r)
    eligible=[r for r in unique.values() if r['priority']>=MIN_IMPORTANCE
        and (score_ceiling is None or r['priority']<=score_ceiling)]
    eligible.sort(key=lambda r:(-r['priority'],-r['seq'],r['id']))
    # Un lote editorial debe representar acontecimientos de distintos tipos,
    # sin dejar que una sucesión administrativa de proyectos desplace ensayos,
    # investigaciones o descubrimientos relevantes. Si solo hay una categoría,
    # se conserva la paginación habitual.
    page_size=max(1,min(20,int(limit)))
    kinds={r['kind'] for r in eligible}
    selected=[]
    if len(kinds)>1:
        first_limit=max(2,(page_size+2)//3)
        by_kind={}
        for r in eligible:
            if len(selected)>=page_size:break
            if by_kind.get(r['kind'],0)>=first_limit:continue
            selected.append(r)
            by_kind[r['kind']]=by_kind.get(r['kind'],0)+1
    picked={(r['category'],r['id']) for r in selected}
    for r in eligible:
        if len(selected)>=page_size:break
        if (r['category'],r['id']) not in picked:
            selected.append(r)
            picked.add((r['category'],r['id']))
    # Ordenar lo elegido de modo reproducible y legible, sin interpolar
    # causas o agrupar entidades sin un vínculo registrado.
    selected.sort(key=lambda r:(-r['priority'],-r['seq'],r['id']))
    # Una ficha destacada puede tener vínculos explícitos a otra ficha con
    # aviso pendiente. Si la mostramos como contexto revisado, confirmamos
    # también sus marcadores en todas las solapas. Nunca inferir parentesco
    # a partir de cercanía temporal o coincidencia de palabras.
    pending_by_identity={(r['category'],r['id']):r for r in eligible}
    selected_ids={(r['category'],r['id']) for r in selected}
    contextual=[]
    contextual_ids=set()
    if include_omitted:
        for source in selected:
            for link in archive.relations_for(source['category'],source['id'],limit=40):
                identity=(link['category'],link['id'])
                target=pending_by_identity.get(identity)
                if (not target or identity in selected_ids or
                        identity in contextual_ids or
                        target['priority']<MIN_IMPORTANCE):
                    continue
                contextual.append(target)
                contextual_ids.add(identity)
                if len(contextual)>=12:
                    break
            if len(contextual)>=12:
                break
    references=[]
    for r in selected+contextual:
        refs=[{k:r[k] for k in ('tab','key','category','id') if k in r}]+r['aliases']
        for ref in refs:
            ref['kind']=r['kind']
            ref['title']=r['text'][:95]
            if (r['category'],r['id']) in contextual_ids:
                ref['related_context']=True
        references.extend(refs)
    remaining=max(0,len(eligible)-len(selected)-len(contextual))
    if not include_omitted:
        return selected,references,remaining
    # Solo se descartan registros evaluados dentro del snapshot inicial.
    # Los pendientes con prioridad suficiente que no entraron en esta página
    # siguen sin leer y se ofrecen en «¿Qué más?».
    omitted=[]
    for r in unique.values():
        if r['priority']>=MIN_IMPORTANCE:continue
        refs=[{k:r[k] for k in ('tab','key','category','id') if k in r}, *r['aliases']]
        for ref in refs:
            ref['kind']=r['kind']
            ref['title']=r['text'][:95]
        omitted.extend(refs)
    return selected,references,remaining,omitted
