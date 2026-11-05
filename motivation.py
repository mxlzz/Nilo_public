"""Costo de oportunidad factual de tareas repetitivas.

No crea una barra artificial de aburrimiento ni impone objetivos: muestra al LLM
el trabajo de mantenimiento que Nilo realmente realizó para que él decida.
"""
from __future__ import annotations

DURATIONS={'drink':8, 'eat':12, 'forage':18, 'gather':22, 'rest':25}


def record_maintenance(person,kind,stamp,target=None,autonomous=False,minutes=None):
    if kind not in DURATIONS:return None
    minute=round(float(person.get('clock_minutes',0)),3)
    item={'when':stamp,'minute':minute,'kind':kind,'target':target or '',
          'autonomous':bool(autonomous),'duration_estimate_minutes':DURATIONS[kind] if minutes is None else float(minutes)}
    records=person.setdefault('maintenance_history',[])
    records.append(item)
    del records[:-400]
    return item


def maintenance_summary(person,window_minutes=4320):
    minute=float(person.get('clock_minutes',0))
    events=[e for e in person.get('maintenance_history',[])
            if isinstance(e,dict) and minute-float(e.get('minute',0))<=window_minutes]
    counts={}
    for event in events:counts[event['kind']]=counts.get(event['kind'],0)+1
    spent=round(sum(float(e.get('duration_estimate_minutes',0)) for e in events),1)
    repeated=any(k in counts and counts[k]>=4 for k in ('forage','gather','drink','eat'))
    return {'periodo_dias_simulados':round(window_minutes/1440,1),
            'actividades':counts,'minutos_de_mantenimiento_aprox':spent,
            'repeticion_detectada':repeated,
            'observacion':('Dedico tiempo a repetir tareas básicas; podría investigar alternativas si me interesa.'
                           if repeated else 'No hay evidencia de mantenimiento repetitivo importante.')}
