"""Revisión informativa de estrategias: evidencia de repetición, sin imponer objetivos.

Solo considera deliberaciones del mismo proyecto y resultados observables. No
interrumpe acciones por similitud, ni asume que repetir sea siempre un error.
"""
from __future__ import annotations
import json

_REST_WORDS=('descans','repos','recuper','energia','energía','dormir','sueño')


def _rest_research(person):
    project=person.get('project') or {}
    text=' '.join(str(x or '') for x in
                  (project.get('title'),project.get('reason'),person.get('active_research')))
    return any(term in text.casefold() for term in _REST_WORDS)


def semantic_signature(person, plan):
    """Identidad operativa conservadora, sin textos de cuaderno ni IDs efímeros.

    Solo se abstraen desplazamientos *cortos* en secuencias de investigación
    energética. Destinos lejanos, direcciones/regiones de exploración y métodos
    físicos distintos permanecen separados.
    """
    if not isinstance(plan,list):
        return ''
    physical=[s for s in plan if isinstance(s,dict) and s.get('op')!='write']
    if not physical:return ''
    ops=[str(s.get('op','')) for s in physical]
    rest_study=_rest_research(person) and 'rest' in ops
    pos=person.get('pos',[])
    sequence=[]
    for s in physical:
        op=str(s.get('op',''))
        if op=='go':
            x,y=s.get('x'),s.get('y')
            if (rest_study and isinstance(x,int) and not isinstance(x,bool)
                    and isinstance(y,int) and not isinstance(y,bool)
                    and len(pos)>=2 and isinstance(pos[0],int) and isinstance(pos[1],int)
                    and abs(x-pos[0])+abs(y-pos[1])<=3):
                sequence.append(['go','cercano'])
            else:
                sequence.append(['go',str(s.get('target') or ''),x,y])
        elif op=='rest':
            sequence.append(['rest','ensayo_energia'] if rest_study else
                            ['rest',s.get('minutes',30)])
        elif op=='explore':
            sequence.append(['explore',s.get('direction'),s.get('region'),
                             s.get('x'),s.get('y')])
        else:
            sequence.append([op,str(s.get('method') or ''),
                             str(s.get('item') or ''),str(s.get('target') or ''),
                             str(s.get('design_id') or ''),
                             tuple(str(m) for m in s.get('materials',[])
                                   if isinstance(m,str))
                             if isinstance(s.get('materials',[]),list) else ()])
    return json.dumps(sequence,ensure_ascii=False,sort_keys=True,default=str)


def evidence_snapshot(person,world):
    """Cambios verificables, no redacción ni porcentaje subjetivo de avance."""
    measured=sum(1 for m in person.get('measurements',[])
                 if isinstance(m,dict) and m.get('op')=='rest' and m.get('rest_comparable'))
    return [
        len(person.get('knowledge',{})),
        len(world.get('revealed',[])),
        sum(world.get('excavation',{}).values()),
        len(person.get('conclusions',[])),
        measured,
        len(person.get('items',[])),
        len(world.get('structures',[]))
    ]


def detect_repetition(history,signature,snapshot,project_id,*,rest_energy=None):
    """Señal tras 3 deliberaciones equivalentes sin cambio observable.

    Los registros históricos sin firma semántica no se reinterpretan.
    """
    if not signature or not project_id or not isinstance(history,list):
        return None
    matching=[]
    for row in reversed(history):
        if (not isinstance(row,dict) or row.get('semantic_signature')!=signature
                or row.get('project_id')!=project_id
                or row.get('evidence_snapshot')!=snapshot):
            break
        matching.append(row)
        if len(matching)>=2:break
    if len(matching)<2:return None
    message='Tres deliberaciones con secuencias operativas equivalentes, sin cambio en los indicadores registrados.'
    reasons=['misma secuencia operativa normalizada',
             'sin nuevos conocimientos, lugares, estructuras ni conclusiones comparables']
    if rest_energy is not None and rest_energy>60 and 'ensayo_energia' in signature:
        reasons.append('energía actual superior al máximo inicial de 60 para un ensayo comparable de descanso')
    return {'codigo':'repeticion_semantica_sin_evidencia_nueva',
            'coincidencias_consecutivas':len(matching)+1,
            'proyecto_id':project_id,'resumen':message,
            'fundamentos':reasons,
            'alcance':'Indicio para reconsiderar, no prueba de inutilidad ni orden para detenerse.',
            'plan_signature':signature[:280]}
