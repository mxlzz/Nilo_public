"""Laboratorio general. Extrae observables SOLO de ensayos ejecutados por el motor.

No revela propiedades internas antes de que Nilo las haya probado. Los resultados son
valores abstractos, no magnitudes de ingeniería real. Comparar no demuestra causalidad.
"""
from __future__ import annotations

from nilo_runtime.core.identity import new_uuid
import uuid
from physics import evaluate_containment, evaluate_buoyancy

METRIC_LABELS={
    'dureza':'Dureza estimada (0–10)',
    'resistencia':'Resistencia estimada (0–10)',
    'retencion_pct':'Factor aplicado a la capacidad de agua (%, histórico; no mide pérdidas)',
    'agua_retenida':'Capacidad útil de agua (unidades; nombre histórico)',
    'capacidad_util_agua':'Capacidad útil estimada de agua (unidades)',
    'empuje':'Empuje (unidades)',
    'carga':'Masa/carga (unidades)',
    'carga_aplicada':'Carga de prueba (unidades)',
    'limite_carga':'Límite estimado de carga (unidades)',
    'energia_aplicada':'Energía aplicada (unidades)',
    'energia_salida':'Energía transmitida (unidades)',
}

def _tool(person,step):
    requested=str(step.get('item') or step.get('target') or '').lower().strip()
    items=person.get('items',[])
    return next((it for it in items if it.get('id','').lower()==requested or it.get('name','').lower()==requested),
           next((it for it in items if requested and requested in it.get('name','').lower()),None))

def measured_physics(person,step,success,facts):
    """Los datos físicos se exponen después de una prueba verificable, incluso si falla.

    No se atribuye éxito a un prototipo creado, ni se ofrece su rendimiento por
    el mero hecho de que un LLM lo solicite.
    """
    op=step.get('op');method=str(step.get('method') or '').lower().strip()
    text=' '.join(map(str,facts)).lower()
    if op=='experiment':
        if 'ya había comprobado' in text:return None
        target=str(step.get('target') or '').lower()
        mat=next((m for m,n in person.get('inventory',{}).items() if n>0 and m in target and m in person.get('materials',{})),None)
        props=person.get('materials',{}).get(mat,{}) if mat else {}
        metric={'golpear':'dureza','cargar':'resistencia'}.get(method)
        if not (mat and metric and metric in props and success):return None
        return {'kind':'material','subject':mat,'method':method,'metrics':{metric:round(float(props[metric]),3)},
                'conditions':{'material':mat,'metodo':method},'precision':'escala estimada del motor, 0–10'}
    if op!='use':return None
    tool=_tool(person,step)
    if not tool:return None
    subject=tool.get('id','')
    geometry=tool.get('geometry') or {}
    conditions={'objeto':subject,'version':tool.get('revision',1),'materiales':list(tool.get('materials',[])),
                'forma':geometry.get('shape','desconocida'),'tamano':geometry.get('size')}
    if method in ('llenar','contener') and 'llené' in text and 'agua' in text and success:
        info=evaluate_containment(tool,'agua',person.get('materials',{}))
        return {'kind':'recipiente','subject':subject,'method':'llenar','metrics':{
            'capacidad_util_agua':info['quantity']},
            'conditions':conditions,'precision':'estimación estática de capacidad por geometría y permeabilidad; NO mide pérdidas con el tiempo; unidades abstractas'}
    if method in ('flotar','navegar') and (('flota' in text or 'se hunde' in text) and 'empuje' in text):
        info=evaluate_buoyancy(tool,passenger=(method=='navegar'),known=person.get('materials',{}))
        return {'kind':'flotacion','subject':subject,'method':method,'metrics':{
            'empuje':info['buoyant_capacity'],'carga':info['load']},
            'conditions':conditions,'precision':'modelo simplificado de flotación'}
    if tool.get('form')=='ensamblaje' and 'ensayo de carga' in text and method in ('carga','resistir_carga'):
        try:load=max(0.,min(100.,float(step.get('load',3))))
        except (ValueError,TypeError):load=3.
        return {'kind':'ensamblaje','subject':subject,'method':'carga','metrics':{
            'carga_aplicada':round(load,2),'limite_carga':round(float(tool.get('resistance',0))*1.5,2)},
            'conditions':conditions,'precision':'escala de carga abstracta del motor'}
    if tool.get('form')=='ensamblaje' and 'ensayo de transmisión' in text and method in ('transmision','transmitir_movimiento'):
        try:energy=max(0.,min(100.,float(step.get('input_energy',0))))
        except (ValueError,TypeError):energy=0.
        mobility=any(j.get('type') in ('articulada','deslizante') for j in tool.get('joints',[]))
        shape=any(x.get('shape') in ('rueda','eje','cilindro') for x in tool.get('parts',[]))
        result=round(min(float(tool.get('resistance',0))*1.5,energy*.65),2) if mobility and shape else 0.
        return {'kind':'ensamblaje','subject':subject,'method':'transmision','metrics':{
            'energia_aplicada':energy,'energia_salida':result},
            'conditions':conditions,'precision':'transmisión mecánica simplificada'}
    return None

def compare(person,step,stamp):
    """Comparación controlada por IDs reales, sin extrapolar leyes físicas.

    Devuelve éxito, mensaje y conclusión. No permite fabricar medidas desde texto.
    """
    ids=step.get('evidence_ids',[])
    if not isinstance(ids,list) or not 2<=len(ids)<=6 or len(set(map(str,ids)))!=len(ids):
        return False,'Necesito entre 2 y 6 identificadores distintos de ensayos medidos.',None
    found={m['id']:m for m in person.get('measurements',[])}
    if any(not isinstance(x,str) or x not in found for x in ids):
        return False,'Hay identificadores de ensayos inexistentes o fuera de la memoria de trabajo.',None
    trials=[found[x] for x in ids]
    # Descansos ya medidos: la tasa de recuperación es una variable numérica
    # verificable y no está dentro del bloque `physical` de laboratorio.
    if all(t.get('op')=='rest' for t in trials):
        if not all(t.get('rest_comparable') and isinstance(t.get('energy_per_hour'),(int,float))
                   for t in trials):
            return False,'Los descansos no incluyen tasas energéticas comparables y no saturadas.',None
        if len({t.get('condition') for t in trials})<2:
            return False,'Comparar descansos requiere al menos refugio e intemperie.',None
        metric=str(step.get('metric') or 'energia_por_hora').strip()
        if metric not in ('energia_por_hora','energy_per_hour'):
            return False,'Para descansos la métrica disponible es energia_por_hora.',None
        if any(c.get('metric')=='energia_por_hora'
               and set(c.get('evidence_ids',[]))==set(ids)
               for c in person.get('conclusions',[])):
            return False,'Estos descansos ya fueron comparados.',None
        values=[t['energy_per_hour'] for t in trials]
        text='; '.join(f"{t['condition']} ({t['id']}): {t['energy_per_hour']:g} puntos/h"
                        for t in trials)
        observation=('Comparé descansos medidos: '+text+
                     '. Las diferencias describen esas condiciones y no prueban '
                     'por sí solas el funcionamiento de una construcción particular.')
        entry={'id':'con-'+new_uuid().hex[:12],'when':stamp,
               'topic':'comparacion:descanso:energia_por_hora',
               'status':'comparacion_medida','text':observation,
               'metric':'energia_por_hora','values':values,
               'evidence_ids':list(ids),
               'scope':'Comparación descriptiva sin atribución causal general.'}
        person.setdefault('conclusions',[]).append(entry)
        return True,observation,entry
    details=[t.get('physical') for t in trials]
    if any(not d or not d.get('metrics') for d in details):
        return False,'No todos los ensayos incluyen propiedades físicas cuantificadas por el motor.',None
    keys={(d['kind'],d['method']) for d in details}
    if len(keys)!=1:return False,'Las pruebas corresponden a tipos de fenómeno o métodos incompatibles.',None
    metric=str(step.get('metric') or '').strip()
    shared=set.intersection(*(set(d['metrics']) for d in details))
    if metric and metric not in shared:return False,'La variable solicitada no fue medida en todos los ensayos.',None
    if not metric:
        metric=sorted(shared)[0] if shared else ''
    if not metric:return False,'No existe una variable numérica común entre las pruebas.',None
    signatures=[(d.get('subject'),d['conditions'].get('version')) for d in details]
    if len(set(signatures))<2:
        return False,'Para comparar necesito objetos, materiales o versiones distintos; repetir el mismo caso no constituye contraste.',None
    values=[d['metrics'][metric] for d in details]
    if not all(isinstance(x,(int,float)) for x in values):
        return False,'El motor no registró valores numéricos comparables.',None
    line='; '.join(f"{d['subject']} ({t['id']}): {v:g}" for t,d,v in zip(trials,details,values))
    label=METRIC_LABELS.get(metric,metric)
    observation=f'Comparé {label} mediante pruebas {details[0]["method"]}: {line}. Diferencia entre máximo y mínimo: {max(values)-min(values):g}.'
    controls=[d.get('conditions',{}) for d in details]
    if len({str(sorted(c.items())) for c in controls})>1:
        observation+=' Las condiciones constructivas difieren; los resultados no demuestran por sí solos qué propiedad causó la diferencia.'
    if any(c.get('evidence_ids')==ids and c.get('metric')==metric for c in person.get('conclusions',[])):
        return False,'Esta comparación ya está registrada con esas mismas pruebas.',None
    entry={'id':'con-'+new_uuid().hex[:12],'when':stamp,
           'topic':'comparacion:'+details[0]['kind']+':'+metric,'status':'comparacion_medida',
           'text':observation,'metric':metric,'values':values,'evidence_ids':ids,
           'scope':'Medición descriptiva de condiciones concretas. No implica causalidad general.'}
    person.setdefault('conclusions',[]).append(entry)
    return True,observation,entry


def comparison_candidates(person,limit=5):
    """Pares de pruebas con variable común, IDs existentes y condiciones diferenciadas.

    Orientación para `compare`: no crea resultados ni garantiza inferencia causal.
    """
    samples=person.get('measurements',[])[-180:]
    available=[]
    rest={}
    for t in samples:
        if t.get('op')=='rest' and t.get('rest_comparable') and isinstance(t.get('energy_per_hour'),(int,float)):
            rest[t.get('condition')]=t
    if 'refugio' in rest and 'intemperie' in rest:
        available.append({'tipo':'descanso','metric':'energia_por_hora',
                          'evidence_ids':[rest[k]['id'] for k in ('refugio','intemperie')],
                          'condiciones':['refugio','intemperie']})
    groups={}
    for t in samples:
        physical=t.get('physical') or {}
        if not isinstance(physical,dict) or not isinstance(physical.get('metrics'),dict):
            continue
        subject=physical.get('subject')
        version=(physical.get('conditions') or {}).get('version')
        for metric,value in physical['metrics'].items():
            if not (isinstance(value,(int,float)) and not isinstance(value,bool)):
                continue
            key=(physical.get('kind'),physical.get('method'),metric)
            groups.setdefault(key,{})[(subject,version)]=t
    for (kind,method,metric),by_subject in groups.items():
        if len(by_subject)<2:continue
        pair=list(by_subject.values())[-2:]
        if any(c.get('metric')==metric and set(c.get('evidence_ids',[]))=={p['id'] for p in pair}
               for c in person.get('conclusions',[])):
            continue
        available.append({'tipo':kind,'metodo':method,'metric':metric,
                          'evidence_ids':[p['id'] for p in pair],
                          'condiciones':[str((p.get('physical') or {}).get('conditions') or {})[:120] for p in pair]})
    return available[-max(0,int(limit)):]
