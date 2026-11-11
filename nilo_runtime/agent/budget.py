"""Selección y presupuestos de contexto para todos los proveedores LLM.

Un único registro físico define las acciones; las variantes compactas se
producen con las descripciones existentes, nunca con recetas paralelas.
Las entradas preservan JSON completo por campo y no escriben memoria.
"""
from __future__ import annotations
import copy
import json
from types import MappingProxyType

from nilo_runtime.agent.prompts import GROQ_SYSTEM
from nilo_runtime.core.operations import registered_operations

def _short_description(spec):
    """Primera cláusula del contrato oficial, sin inventar una operación."""
    description = spec.description.strip()
    # Extraer el PRIMER ejemplo JSON sin recortar sus llaves o comillas.
    # La nota abreviada sale del mismo texto de OperationSpec, no de otro
    # diccionario de operaciones editado a mano.
    try:
        example, end = json.JSONDecoder().raw_decode(description)
        if not isinstance(example,dict) or example.get("op") != spec.name:
            raise ValueError("Ejemplo ajeno a la operación")
        sample = json.dumps(example,ensure_ascii=False,separators=(",",":"))
        note = description[end:].strip()
    except (ValueError,TypeError):
        sample = json.dumps({"op":spec.name},separators=(",",":"))
        note = description
    if len(note)>94:
        note=note[:89].rsplit(" ",1)[0].rstrip(" ,;:") + "…"
    return sample + ((" "+note) if note else "") + " [síntesis]"

SHORT_OPERATIONS = MappingProxyType({
    op: _short_description(spec) for op, spec in registered_operations().items()
})

def brief_actions():
    from action_contracts import SUPPORTED_OPERATIONS
    if set(SUPPORTED_OPERATIONS) != set(SHORT_OPERATIONS):
        raise RuntimeError("Las operaciones abreviadas difieren del registro físico")
    return ("OPERACIONES DISPONIBLES (usar solo estas):\n" +
            "\n".join("- "+op+": "+SHORT_OPERATIONS[op]
                      for op in sorted(SUPPORTED_OPERATIONS)))

def compact_context(context, char_budget=6800):
    """Reduce contexto por CAMPOS, nunca trunca JSON crudo ni crea hechos.

    Se prefiere el estado actual y la evidencia al historial literario.
    """
    limits=(('momento',None),('posición',None),('necesidades',None),
            ('inventario_materiales',None),('salida_conocida',None),('proyectos_reanudables',4),
            ('antecedentes_relacionados',3),('investigaciones_pausadas_relacionadas',3),
            ('antecedente_relevante',None),
            ('navegacion_a_lugares',6),('diagnosticos_operativos_recientes',5),
            ('fenomenos_no_evaluables_recientes',3),('orillas_agua_conocidas_alcanzables',3),
            ('percepción_local',6),('herramientas_que_llevo',4),
            ('construcciones_fijas',4),('proyecto_actual',None),('investigaciones_activas',3),('memorias_relevantes',5),('revision_de_estrategia',None),('repeticion_operativa_informativa',None),
            ('evidencia_de_progreso_ultima_accion',None),('revision_de_intentos_verificados',5),
            ('comparaciones_validas',4),('fenomenos_pendientes_de_modelo',3),
            ('conclusiones_verificadas',3),('conocimiento_con_procedencia',6),('mediciones_reales_recientes',4),('resultados_de_acciones',3),
            ('propuestas_pendientes',3),('evaluaciones_externas_recientes',3),('inconsistencias_recoleccion_previas',4),('predicciones_contrastadas',3),('estrategias_que_ya_no_funcionaron',3),
            ('habilidades_verificadas',5),('comportamiento_medido',None),('preferencias_en_espera',5),
            ('agenda_diferida',3),('recordatorios_listos',5),('recordatorios_pendientes',5),('estrategia_bloqueada',None),('pistas_cierre_proyecto',None),
             ('ultimo_cierre_rechazado',None),('ultima_referencia_de_proyecto_rechazada',None),('estado_investigacion_descanso',None),('condiciones_de_ensayo_descanso',None),
            ('regla',None))
    selected={}
    for key,count in limits:
        if key in context:
            value=context[key]
            if key=='orillas_agua_conocidas_alcanzables' and isinstance(value,list):
                # Aun sin sed se puede planificar agua; evitar que la lista
                # completa domine deliberaciones sin interés por ella.
                project=context.get('proyecto_actual') or {}
                title=' '.join(str(project.get(k) or '') for k in ('title','reason','state')).casefold()
                water_interest=any(k in title for k in ('agua','hidrata','beb','orilla','costa'))
                sed=(context.get('necesidades') or {}).get('hidratacion')
                if not water_interest and sed in ('bien hidratado','sin sed'):
                    value=value[:1]
            if isinstance(value,list) and count is not None:
                # Memorias: ranking descendente; demás registros: cronología.
                value=value[:count] if key=='memorias_relevantes' else value[-count:]
            if key=='investigaciones_activas' and isinstance(value,list):
                # Conservar la pregunta, la hipótesis y la procedencia; acotar
                # solo el historial *en el payload*, no en la partida.
                value=[{k:(v[k][-3:] if k=='hypothesis_history'
                             and isinstance(v[k],list) else v[k])
                        for k in ('id','question','hypothesis','state',
                                  'naturaleza','hypothesis_history',
                                  'evidence_ids','fuentes_de_evidencia')
                        if k in v} for v in value if isinstance(v,dict)]
            if key=='proyecto_actual' and isinstance(value,dict):
                value={k:value[k] for k in ('id','title','reason','state','status','last_action','last_result','reconsideration_required','antecedente_pausado','hitos_fisicos_registrados','resultados_fisicos_registrados') if k in value}
            selected[key]=value
    selected['contexto_reducido']='Historial resumido por límite del proveedor. Consultar diario para detalles.'
    def length():return len(json.dumps(selected,ensure_ascii=False,separators=(',',':')))
    for key in ('mediciones_reales_recientes','herramientas_que_llevo','construcciones_fijas','percepción_local','habilidades_verificadas','estrategias_que_ya_no_funcionaron'):
        while length()>char_budget and isinstance(selected.get(key),list) and selected[key]:
            selected[key]=selected[key][1:]
    # La identidad del proyecto y las conclusiones deben sobrevivir a la compresión.
    # El presupuesto es orientativo: nunca se omiten estos hechos para simular que Nilo los olvidó.
    if length()>char_budget:
        for key in ('comportamiento_medido','propuestas_pendientes','predicciones_contrastadas','fenomenos_no_evaluables_recientes','preferencias_en_espera','agenda_diferida'):
            if length()<=char_budget:break
            selected.pop(key,None)
    return selected


def _cognitive_needs_context(context):
    """Última barrera: no exponer reservas a un modelo por usar un contexto legado.

    El observador y los replays continúan usando el JSON físico original.
    """
    needs=context.get('necesidades')
    if not isinstance(needs,dict):return context
    if isinstance(needs.get('valores'),dict):
        values=needs['valores']
    elif any(isinstance(needs.get(k),(int,float)) and not isinstance(needs.get(k),bool)
             for k in ('hidratacion','nutricion','energia')):
        values={k:needs[k] for k in ('hidratacion','nutricion','energia') if k in needs}
    else:return context
    from survival import perceived_needs
    sanitized=dict(context)
    sanitized['necesidades']=perceived_needs({
        'needs':dict(values),
        'strain':bool(needs.get('tension_corporal',False)),
        'unconscious':bool(needs.get('unconscious',False))
    })
    return sanitized


def _size(value):
    return len(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8'))


# Nunca descartar la identidad ni el proyecto, ni el motivo del último cierre.
# El estado operativo y las delegaciones vigentes se preservan íntegros.
# No se consideran instrucciones automáticas de autocuidado.
_CORE=('momento','posición','necesidades','inventario_materiales',
       'proyecto_actual','investigaciones_activas','ultimo_cierre_rechazado',
       'ultima_referencia_de_proyecto_rechazada','proyectos_reanudables',
       'antecedente_relevante','preferencias_en_espera','regla')
_REDUCE_FIRST=('estrategias_que_ya_no_funcionaron','diagnosticos_operativos_recientes',
               'resultados_de_acciones','mediciones_reales_recientes','construcciones_fijas',
               'herramientas_que_llevo','percepción_local','navegacion_a_lugares',
               'comparaciones_validas','memorias_relevantes','conclusiones_verificadas',
               'conocimiento_con_procedencia',
               'propuestas_pendientes','recordatorios_pendientes','recordatorios_listos')
_REMOVE_FIRST=('comportamiento_medido','agenda_diferida',
               'fenomenos_pendientes_de_modelo','revision_de_intentos_verificados',
               'predicciones_contrastadas','inconsistencias_recoleccion_previas',
               'estado_investigacion_descanso','condiciones_de_ensayo_descanso',
               'habilidades_verificadas','pistas_cierre_proyecto',
               'revision_de_estrategia','repeticion_operativa_informativa',
               'evidencia_de_progreso_ultima_accion')

def context_focus(context):
    """Relevancia operativa aproximada; no impone proyectos ni objetivos."""
    project=context.get('proyecto_actual') or {}
    message=' '.join(str(project.get(k) or '') for k in
                     ('title','reason','state','last_action','last_result')).casefold()
    if any(s in message for s in ('explor','ruta','territor','cueva','camino','orilla','recorr')):
        return 'navegacion'
    if any(s in message for s in ('fabric','diseñ','herramient','constru','modific','ensambl','recipiente','mecanism')):
        return 'fabricacion'
    if any(s in message for s in ('experiment','ensay','medic','compar','verific','hipotes','hipótes','resisten','dureza')):
        return 'experimentacion'
    return 'general'


def context_stats(original, selected, provider, payload):
    """Telemetría segura de bytes y secciones; no guarda el contenido del prompt."""
    def nbytes(obj):
        return len(json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
    if provider=='gemini':
        system=payload['systemInstruction']['parts'][0]['text']
    else:
        system=payload['messages'][0]['content']
    return {
        'foco':context_focus(original),
        'contexto_original_bytes':nbytes(original),
        'contexto_enviado_bytes':nbytes(selected),
        'instrucciones_bytes':len(system.encode('utf-8')),
        'solicitud_bytes':len(json.dumps(payload,ensure_ascii=False).encode('utf-8')),
        'secciones_incluidas':sorted(selected),
        'bytes_por_seccion':{k:nbytes(v) for k,v in selected.items()},
        'secciones_omitidas':sorted(set(original)-set(selected)),
        'recuerdos_incluidos':[v.get('id') for v in selected.get('memorias_relevantes',[]) if isinstance(v,dict)],
    }


def bounded_context(context,byte_budget=4600):
    """Selecciona evidencia íntegra, atendiendo al proyecto sin borrar memoria.

    Memorias_relevantes llegan ordenadas de mayor a menor pertinencia.
    La siguiente etapa puede recuperar más evidencia; no se altera SQLite.
    """
    value=copy.deepcopy(context)
    if _size(value)<=byte_budget:
        return value
    # La API histórica de bounded_context recibe también contextos CRUDOS,
    # no solo la versión precompactada. Esos historiales de 100 preguntas
    # no deben bloquear el presupuesto ni eliminar toda investigación viva.
    active=value.get('investigaciones_activas')
    if isinstance(active,list) and len(active)>2:
        value['investigaciones_activas']=[
            {k:row[k] for k in ('id','question','hypothesis','state',
                                'naturaleza','evidence_ids','fuentes_de_evidencia')
             if k in row}
            for row in active[-2:] if isinstance(row,dict)]
    focus=context_focus(context)
    protects={
        'navegacion':('navegacion_a_lugares','percepción_local'),
        'fabricacion':('herramientas_que_llevo','construcciones_fijas'),
        'experimentacion':('comparaciones_validas','mediciones_reales_recientes'),
        'general':()
    }[focus]
    for key in _REMOVE_FIRST:
        if _size(value)<=byte_budget:break
        value.pop(key,None)
    # Eliminar primero datos ajenos a la actividad; no perder el recuerdo más
    # relevante mientras sea posible evitarlo mediante otro campo.
    order=[k for k in _REDUCE_FIRST if k not in protects and k!='memorias_relevantes']
    order+=['memorias_relevantes',*protects]
    while _size(value)>byte_budget:
        changed=False
        for key in order:
            rows=value.get(key)
            if not isinstance(rows,list) or not rows:continue
            # Último recurso: preservar un registro relevante si cabe.
            if key in protects or key=='memorias_relevantes':
                if len(rows)<=1:continue
            if key=='memorias_relevantes':
                rows.pop()  # peor clasificado primero
            else:
                rows.pop(0) # más antiguo primero
            changed=True
            if _size(value)<=byte_budget:break
        if not changed:break
    for key in list(value):
        if _size(value)<=byte_budget:break
        if key not in _CORE and key not in protects and key!='memorias_relevantes':
            del value[key]
    if _size(value)>byte_budget:
        # Quitar registros completos solo como último recurso, nunca crear
        # una versión recortada o falsa de una medición o una conclusión.
        for key in (*protects,'memorias_relevantes'):
            if _size(value)<=byte_budget:break
            if key in value:del value[key]
    if _size(value)>byte_budget and isinstance(value.get('investigaciones_activas'),list):
        # Conservar el último interrogante completo; nunca cortar un ID,
        # hipótesis o cita a mitad de un JSON.
        while len(value['investigaciones_activas'])>1 and _size(value)>byte_budget:
            value['investigaciones_activas'].pop(0)
    if _size(value)>byte_budget:
        raise ValueError('El contexto mínimo supera el presupuesto permitido.')
    value['contexto_reducido']='Vista acotada; la evidencia histórica sigue en SQLite.'
    if _size(value)>byte_budget:value.pop('contexto_reducido',None)
    return value
