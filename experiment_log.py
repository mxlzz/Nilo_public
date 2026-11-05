"""Mediciones verificables y conclusiones condicionales.

El modelo puede escoger ensayos; sólo el motor mide los resultados. No se extrapola
un resultado de una condición a otras ni se confunden tareas rutinarias con ensayos.
"""
from __future__ import annotations
import uuid, unicodedata, re
from survival import ensure_needs
from laboratory import measured_physics


def canonical(text):
    s = ''.join(c for c in unicodedata.normalize('NFKD', str(text).lower()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', s))


def topic(text):
    s=canonical(text)
    # No confundir refugio como construcción con un estudio de recuperación.
    if any(k in s for k in ('descans', 'recuper', 'repos', 'dorm', 'energia', 'fatiga')) and any(
        k in s for k in ('refugio', 'intemperie', 'aire libre', 'arboleda', 'arenal', 'entorno', 'sue')
    ):
        return 'recuperacion_energia'
    return ''


def sheltered(world,person):
    x,y,z=person['pos']
    if str(z) not in world.get('levels',{}):return False
    if world['levels'][str(z)][y][x]=='h':return True
    return any(tuple(b.get('pos',[]))==(x,y,z) and b.get('category')=='habitaculo'
               and b.get('shelter_condition')!='insuficiente' for b in world.get('structures',[]))


def capture(world,person):
    return {'minute':round(person.get('clock_minutes',0),4),
            'position':list(person['pos']), 'sheltered':sheltered(world,person),
            'terrain':world['levels'][str(person['pos'][2])][person['pos'][1]][person['pos'][0]],
            'needs':dict(ensure_needs(person)),
            'inventory':{k:v for k,v in person.get('inventory',{}).items() if v},
            'objects':len(person.get('items',[])), 'structures':len(world.get('structures',[]))}


def measure(person,step,start,end,facts,success,stamp,action_result=None):
    """Registro general: variaciones observadas, no interpretación narrativa."""
    if not start:return None
    duration=max(0,round(end['minute']-start['minute'],3))
    if duration <= 0:return None
    keys=sorted(set(start['needs'])|set(end['needs']))
    changes={k:round(end['needs'].get(k,0)-start['needs'].get(k,0),3) for k in keys}
    items=sorted(set(start['inventory'])|set(end['inventory']))
    inv_change={k:end['inventory'].get(k,0)-start['inventory'].get(k,0) for k in items
                if end['inventory'].get(k,0)!=start['inventory'].get(k,0)}
    op=step.get('op','')
    condition=('refugio' if start['sheltered'] else 'intemperie')
    good_rest=(op=='rest' and success and duration>=15
               and start['position']==end['position'] and start['sheltered']==end['sheltered']
               and start['needs']['energia']<=60 and end['needs']['energia']<74.9)
    sample={'id':'med-'+uuid.uuid4().hex[:12],'when':stamp,'op':op,
            'target':str(step.get('target') or step.get('item') or '')[:80],
            'method':str(step.get('method',''))[:60], 'duration_minutes':duration,
            'start':start,'end':end,'needs_delta':changes,'inventory_delta':inv_change,
            'object_delta':end['objects']-start['objects'],
            'structure_delta':end['structures']-start['structures'],
            'success':bool(success),
            'evaluation_status':(action_result.status if action_result is not None else
                ('no_evaluable' if facts and str(facts[0]).startswith('FÍSICA NO IMPLEMENTADA:') else ('comprobado' if success else 'fallido'))),
            'verified_facts':[str(v)[:220] for v in facts[:4]],
            'condition':condition,'rest_comparable':good_rest}
    if good_rest:sample['energy_per_hour']=round(changes['energia']*60/duration,3)
    # La simulación utiliza evidencia tipada; mantener antigua interfaz únicamente
    # para consumidores legados que todavía llamen measure sin ActionResult.
    physical=(action_result.physical if action_result is not None else
              measured_physics(person,step,success,facts))
    if physical:sample['physical']=physical
    person.setdefault('measurements',[]).append(sample)
    person['measurements']=person['measurements'][-180:]
    return sample


def compare_rest(person,stamp):
    """Comparación descriptiva, no causalidad general: misma métrica, ventana comparable.

    Requiere en ambas condiciones medidas no saturadas y duración >= 15 min.
    Una sola muestra por condición acredita la diferencia observada pero no
    variabilidad/clima/seguridad a lo largo de muchos días.
    """
    if any(v.get('topic')=='recuperacion_energia' and v.get('status')=='comprobada'
           for v in person.get('conclusions',[])):
        return None
    samples=[s for s in person.get('measurements',[]) if s['op']=='rest' and s.get('rest_comparable')]
    indoor=[s for s in samples if s['condition']=='refugio']
    outdoor=[s for s in samples if s['condition']=='intemperie']
    if not indoor or not outdoor:return None
    # Sólo últimos ensayos válidos de cada condición; se documentan sus IDs.
    a,b=indoor[-1],outdoor[-1]
    diff=round(a['energy_per_hour']-b['energy_per_hour'],2)
    if abs(diff)<0.1:
        conclusion='En las condiciones medidas, la recuperación energética por hora fue equivalente dentro y fuera del refugio.'
    elif diff>0:
        conclusion=f'En los descansos medidos, recuperé {diff:.2f} puntos de energía por hora más dentro del refugio que a la intemperie.'
    else:
        conclusion=f'En los descansos medidos, recuperé {abs(diff):.2f} puntos de energía por hora más a la intemperie que en el refugio.'
    entry={'id':'con-'+uuid.uuid4().hex[:12], 'when':stamp,'topic':'recuperacion_energia',
           'status':'comprobada','text':conclusion,
           'evidence_ids':[a['id'],b['id']],
           'rates':{'refugio':a['energy_per_hour'],'intemperie':b['energy_per_hour']},
           'scope':'Comparación de dos descansos, sin inferir efectos independientes de tipos de terreno.'}
    person.setdefault('conclusions',[]).append(entry)
    return entry


def closure_status(person):
    """Ante muestras repetidas sin contraste, indica qué cambia el valor informativo."""
    records=person.get('measurements',[])
    rest=[v for v in records if v.get('op')=='rest']
    by={'refugio':[v for v in rest if v.get('rest_comparable') and v['condition']=='refugio'],
        'intemperie':[v for v in rest if v.get('rest_comparable') and v['condition']=='intemperie']}
    resolved=next((v for v in reversed(person.get('conclusions',[])) if v.get('topic')=='recuperacion_energia'
                   and v.get('status')=='comprobada'),None)
    if resolved:return {'status':'comprobada','topic':'recuperacion_energia','conclusion':resolved['text'],
                        'evidence_ids':resolved['evidence_ids']}
    if len(rest)<2:return {'status':'sin_comparacion','topic':'recuperacion_energia',
                            'message':'Faltan al menos dos descansos medidos en condiciones diferentes.'}
    missing=[condition for condition,values in by.items() if not values]
    if missing:
        warnings=[]
        if len(rest)>=3:warnings.append('Los descansos repetidos sin un contraste válido no permiten resolver la hipótesis; cambiar una condición o el método.')
        return {'status':'incompleta','topic':'recuperacion_energia',
                'valid_counts':{k:len(v) for k,v in by.items()},
                'missing_conditions':missing,'message':'Faltan mediciones no saturadas en: '+', '.join(missing)+'. '+ ' '.join(warnings)}
    return {'status':'lista','topic':'recuperacion_energia'}


def link_conclusion(person,conclusion):
    """Cerrar una investigación equivalente, sin cerrar proyectos no relacionados."""
    for research in person.get('research',[]):
        if research.get('state')!='abierta':continue
        candidate=' '.join((research.get('question',''),research.get('hypothesis','')))
        if topic(candidate)!='recuperacion_energia':continue
        research['state']='concluida';research['conclusion']=conclusion['text']
        research['evidence_ids']=conclusion['evidence_ids'];research['closed']=conclusion['when']
        if person.get('active_research')==research.get('question'):
            person['active_research']=None
    project=person.get('project')
    if project and topic(' '.join((project.get('title',''),project.get('reason',''))))=='recuperacion_energia':
        project['reconsideration_required']=True
        project['state']='Ensayo resuelto: '+conclusion['text']


def observational_conclusion(person,step,stamp):
    """Conclusión reproducible de uno o más ensayos concretos, sin validar prosa del LLM.

    Un resultado fallido también es evidencia. El texto es redactado por el motor
    usando solamente hechos capturados, identificadores y estados verificados.
    """
    label=str(step.get('topic') or step.get('target') or '').strip()[:100]
    evidence_ids=step.get('evidence_ids',[])
    if not label or not isinstance(evidence_ids,list) or not 1 <= len(evidence_ids) <= 6:
        return False,'Indicar un tema y entre uno y seis identificadores de ensayos comprobados.',None
    if topic(label)=='recuperacion_energia':
        return False,'La comparación del descanso necesita muestras válidas en ambas condiciones y una conclusión del motor.',None
    found={e['id']:e for e in person.get('measurements',[])}
    if len(set(evidence_ids))!=len(evidence_ids) or any(ref not in found for ref in evidence_ids):
        return False,'Los IDs proporcionados no corresponden a mediciones disponibles. No atribuyo pruebas inexistentes.',None
    samples=[found[ref] for ref in evidence_ids]
    # Las mediciones de síntesis administrativas registran tiempo transcurrido,
    # pero no constituyen nuevas observaciones físicas.
    derived={'conclude','compare','manual','write','design','propose','report_issue'}
    if any(m.get('op') in derived for m in samples):
        return False,'No puedo usar conclusiones ni registros derivados como si fueran ensayos físicos independientes.',None
    parts=[]
    for m in samples:
        recorded='; '.join(m['verified_facts'][:2]).strip()
        if not recorded:return False,'Algún ensayo no posee un resultado verificable.',None
        parts.append(f"{m['op']} ({m['id']}; {'éxito' if m['success'] else 'fallo'}): {recorded}")
    content='En los ensayos registrados observé: '+' / '.join(parts)
    key='observacion:'+canonical(label)[:90]
    if any(c.get('topic')==key and set(c.get('evidence_ids',[]))==set(evidence_ids) for c in person.get('conclusions',[])):
        return False,'Ya registré esa misma observación con las mismas evidencias.',None
    entry={'id':'con-'+uuid.uuid4().hex[:12],'when':stamp,'topic':key,'status':'observacion_comprobada',
           'text':content[:1100], 'label':label,'evidence_ids':list(evidence_ids),
           'scope':'Resultados observados en esas acciones; no demuestra una regla física universal.'}
    person.setdefault('conclusions',[]).append(entry)
    return True,'Registré una conclusión descriptiva apoyada en pruebas reales: '+content[:420],entry
