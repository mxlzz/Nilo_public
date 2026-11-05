"""Proyección de hechos del motor hacia percepción y conocimiento del personaje.

El estado interno y las mediciones persistentes NO se modifican aquí.
Esta capa se aplica al payload cognitivo de todos los proveedores y al chat.
No concede capacidades ni convierte el modelo esquemático en prueba física.
"""
from __future__ import annotations
from copy import deepcopy
from nilo_runtime.perception.objects import desgaste_observable as _desgaste

def _piezas(rows):
    result=[]
    for piece in rows if isinstance(rows,list) else []:
        if not isinstance(piece,dict):continue
        entry={k:piece[k] for k in ('id','material','name','function','connection') if k in piece}
        if 'estado' in piece:entry['desgaste_observable']=_desgaste(
            piece['estado']*100 if isinstance(piece['estado'],(int,float))
            and not isinstance(piece['estado'],bool)
            and 0<=piece['estado']<=1 else piece['estado'])
        result.append(entry)
    return result


def _proyecto(raw):
    if not isinstance(raw,dict):return raw
    # Progreso estimado en UI y guardado no es evidencia objetiva: excluirlo.
    keep=('id','title','reason','status','state','last_action','last_result',
          'reconsideration_required','antecedente_pausado')
    result={k:deepcopy(raw[k]) for k in keep if k in raw}
    milestones=raw.get('verified_milestones') or []
    if isinstance(milestones,list) and milestones:
        result['hitos_fisicos_registrados']=[
            {k:deepcopy(v) for k,v in entry.items()
             if k in ('when','op','fact','measurement_id')}
            for entry in milestones[-3:] if isinstance(entry,dict)]
    if 'verified_results' in raw and not result.get('hitos_fisicos_registrados'):
        verified=raw.get('verified_results') or []
        result['resultados_fisicos_registrados']=[
            {k:deepcopy(v) for k,v in entry.items()
             if k in ('when','action','result','measurement_id')}
            for entry in verified[-3:] if isinstance(entry,dict)]
    precedent=result.get('antecedente_pausado')
    if isinstance(precedent,dict):
        precedent.pop('acciones_sin_avance',None)
    return result


def _antecedente(context):
    """Un único antecedente pertinente con motivo registrado, no un objetivo impuesto."""
    project=context.get('proyecto_actual') or {}
    previous=project.get('antecedente_pausado') if isinstance(project,dict) else None
    if not isinstance(previous,dict):
        rows=context.get('antecedentes_relacionados') or []
        previous=rows[0] if isinstance(rows,list) and rows else None
    if not isinstance(previous,dict):return None
    result={'id':previous.get('id'),
            'titulo':previous.get('titulo') or previous.get('title'),
            'estado':previous.get('estado') or previous.get('status')}
    reason=previous.get('motivo') or previous.get('motivo_de_pausa_o_cierre') or previous.get('closure_reason')
    if reason:result['motivo_registrado']=reason
    if previous.get('ultimo_estado'):result['estado_que_quedo_pendiente']=previous['ultimo_estado']
    # Una referencia física o de investigación es trazable por ID; no inferir éxito.
    return {k:v for k,v in result.items() if v is not None}


def project_context(context):
    """Devuelve COPIA cognitiva: nunca contamina snapshots, UI ni SQLite."""
    from brain import _cognitive_needs_context
    view=deepcopy(_cognitive_needs_context(context))
    if not isinstance(view,dict):return view
    precedent=_antecedente(view)
    if precedent:view['antecedente_relevante']=precedent
    if 'proyecto_actual' in view:view['proyecto_actual']=_proyecto(view['proyecto_actual'])

    # Estos puntajes no son percepciones del personaje. La posición, las
    # cantidades del inventario y las mediciones físicas auténticas sí lo son.
    for key in ('predisposiciones','territorio_descubierto_pct',
                'acciones_sin_avance_reciente','siguiente_revision_objetivo_minuto',
                'comportamiento_medido'):
        view.pop(key,None)

    if 'antecedentes_relacionados' in view:
        view['antecedentes_relacionados']=[
            {k:deepcopy(v) for k,v in row.items() if k!='acciones_sin_avance'}
            for row in view['antecedentes_relacionados'] if isinstance(row,dict)]
    if 'investigaciones_pausadas_relacionadas' in view:
        view['investigaciones_pausadas_relacionadas']=[
            {k:deepcopy(v) for k,v in row.items()
             if k not in ('evidencias_registradas','reaperturas')}
            for row in view['investigaciones_pausadas_relacionadas'] if isinstance(row,dict)]

    if isinstance(view.get('herramientas_que_llevo'),list):
        tools=[]
        for tool in view['herramientas_que_llevo']:
            if not isinstance(tool,dict):continue
            t={k:deepcopy(v) for k,v in tool.items()
               if k not in ('durabilidad','usos_por_verificar','piezas')}
            if 'durabilidad' in tool:t['desgaste_observable']=_desgaste(tool['durabilidad'])
            if 'piezas' in tool:t['piezas_observables']=_piezas(tool['piezas'])
            uses=tool.get('usos_por_verificar')
            if isinstance(uses,dict) and uses:
                t['usos_propuestos_sin_ensayo']=[str(name) for name in uses]
            tools.append(t)
        view['herramientas_que_llevo']=tools
    # La potencia excavadora calculada no es una medición efectuada por Nilo.
    # Puede inferir hipótesis por forma y revisar pruebas, pero no recibe score.
    if 'herramientas_de_excavación' in view:
        view['herramientas_de_excavación']=[
            {k:deepcopy(v) for k,v in obj.items() if k in ('id','nombre')}
            for obj in view['herramientas_de_excavación'] if isinstance(obj,dict)]

    if isinstance(view.get('construcciones_fijas'),list):
        structures=[]
        for obj in view['construcciones_fijas']:
            if not isinstance(obj,dict):continue
            b={k:deepcopy(v) for k,v in obj.items()
               if k not in ('condicion_abrigo','piezas')}
            if 'piezas' in obj:b['piezas_observables']=_piezas(obj['piezas'])
            if obj.get('categoria')=='habitaculo':
                b['proteccion_climatica']='no evaluada por el motor'
                b['alcance_de_planta']='representación esquemática; no prueba cerramiento ni protección'
            structures.append(b)
        view['construcciones_fijas']=structures

    return view
