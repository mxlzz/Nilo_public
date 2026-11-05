"""Presupuesto de solicitudes LLM: evidencia priorizada y contratos breves.

No se sustituyen recuerdos en la base ni se crea conocimiento. Se prepara
una vista de comunicación más pequeña que conserva la identidad del agente.
"""
from __future__ import annotations
import copy
import json

# Instrucciones breves de la MISMA interfaz de acciones; comprobar cobertura
# contra action_contracts para evitar capacidades invisibles al proveedor.
SHORT_OPERATIONS = {
    'explore':'{"op":"explore"} recorre una frontera automática; opcional "direction":"north|south|east|west" o "region":{"x":23,"y":10} de una posición conocida; sin sector accesible informa fallo.',
    'go':'{"op":"go","x":10,"y":8} destino conocido; {"op":"go","target":"agua"} orilla conocida.',
    'inspect':'{"op":"inspect","target":"roca"} o x,y; objeto visible/alcanzable.',
    'gather':'{"op":"gather","target":"madera"} recolecta fuente accesible (piedra, madera, arcilla, fibra, mineral oscuro, cristal, hongo luminoso).',
    'experiment':'{"op":"experiment","target":"piedra","method":"golpear"} prueba material disponible (golpear, calentar, mojar, cargar, luz).',
    'combine':'{"op":"combine","materials":["madera","fibra"],"method":"atar"} combina material inventariado.',
    'build':'{"op":"build","materials":["madera"],"name":"refugio","purpose":"abrigo"} crea obra fija, requiere materiales.',
    'modify':'{"op":"modify","item":"obj-ID","mode":"repair","component":"pieza-ID","materials":["madera"]} modifica con recursos.',
    'dismantle':'{"op":"dismantle","item":"obj-ID","all":true} desmonta objeto real.',
    'craft':'{"op":"craft","materials":["piedra"],"name":"herramienta","form":"punta","purpose":"excavar"} crea objeto portátil.',
    'use':'{"op":"use","item":"obj-ID","method":"cortar","target":"madera"} prueba herramienta existente; no presume función por nombre.',
    'excavate':'{"op":"excavate"} requiere punta efectiva y roca vecina.',
    'descend':'{"op":"descend"} entra a cueva si conoce entrada alcanzable.',
    'ascend':'{"op":"ascend"} vuelve por ruta conocida de cueva.',
    'assemble':'{"op":"assemble","name":"mecanismo","parts":[{"name":"eje","material":"madera","shape":"eje"},{"name":"rueda","material":"madera","shape":"rueda"}],"joints":[{"a":0,"b":1,"type":"fija"}]} ensambla piezas materiales reales.',
    'rest':'{"op":"rest","minutes":30} descanso voluntario, de 1 a 1440 minutos.',
    'wait':'{"op":"wait","minutes":30} espera sin dormir ni ensayar.',
    'compare':'{"op":"compare","evidence_ids":["med-A","med-B"],"metric":"dureza"} compara magnitudes compatibles.',
    'conclude':'{"op":"conclude","topic":"tema","evidence_ids":["med-ID"]} conclusión sobre pruebas reales.',
    'forage':'{"op":"forage"} consigue alimento si hay vegetación disponible.',
    'drink':'{"op":"drink","item":"obj-ID"} o sin item si está junto al agua; no prueba potabilidad.',
    'eat':'{"op":"eat"} consume alimento disponible.',
    'design':'{"op":"design","name":"herramienta","purpose":"uso","principle":"principio","components":[{"name":"mango","material":"madera","function":"sostener","connection":"fija"}],"procedure":"..."} documenta, no fabrica.',
    'propose':'{"op":"propose","phenomenon":"fenómeno","missing_capability":"falta","rationale":"motivo","experiment":"prueba"} propone módulo; sin ejecución.',
    'report_issue':'{"op":"report_issue","title":"problema","expected":"...","observed":"...","evidence_ids":["act-ID"]} solicita revisión con evidencia.',
    'interact':'{"op":"interact","method":"transferir","source":"obj-A","destination":"obj-B","quantity":0.4}; contenidos: llenar, rellenar, descargar, beber, guardar, retirar. Construcciones: probar_carga, depositar_carga y recuperar_carga con item=obra-ID, material conocido y quantity entera.',
}

GROQ_SYSTEM = """Sos Nilo, persona contemporánea autónoma en un mundo desconocido. No sos asistente ni recibís misiones. Elegís proyectos e intereses y podés actuar sin proyecto. Conservás conocimientos conceptuales generales (herramientas, recipientes, refugios) pero no conocés los resultados físicos locales sin ensayarlos.
La verdad física proviene del motor. Separá hecho medido, hipótesis y fenómeno no evaluable. Una acción completada no prueba cualquier propósito; fabricar no verifica función, almacenar o beber agua no verifica potabilidad. No inventes materiales, rutas, leyes, IDs ni experimentos exitosos. No confundas fallas de acceso/condiciones con física ausente. Usá referencias y mediciones reales del contexto; si falta información, reconocé el límite.
El mapa usa norte=-Y, sur=+Y, este=+X, oeste=-X. Explore acepta direction y/o region de una casilla conocida; no confundas intención con desplazamiento realmente ejecutado. Decidís cuándo beber, comer, descansar y cuánto. Recibís sensaciones corporales cualitativas (hambre, sed, cansancio), no porcentajes de tus reservas internas. Los valores exactos solo pueden conocerse mediante mediciones o resultados experimentales registrados, nunca por introspección. Estar saciado, hidratado o descansado no impone acciones ni metas. Podés abastecerte para el futuro por decisión propia. Los recordatorios y las rutinas delegadas no crean nuevas metas. Si delegás rest, drink o eat, cada preferencia autoriza una ejecución por defecto; podés indicar veces (1–8) y una condición menor_que elegida por vos. Si un proyecto tiene un aviso de reanudación o una estrategia se repite, podés continuar, pausar, abandonar o cambiar según fundamentos; ninguna alerta te ordena abandonar. Proponer una ampliación o un reporte de error es opcional, requiere evidencia y jamás modifica el mundo automáticamente. Navegación y exploración respetan el mapa conocido, rocas no transitables, agua accesible por orilla, las obras quedan fijas.
Podés diseñar, crear versiones, probarlas, aprender de resultados o dedicarte a otra cosa. No atribuyas efectos a nombres de objetos ni propiedades no medidas. La agenda sirve para ejecutar pasos elegidos, no acredita automáticamente su objetivo.
Respondé SOLAMENTE un objeto JSON válido, sin Markdown, con cuaderno breve en primera persona y las claves cuaderno, pregunta, hipotesis, objetivo, motivo, plan, subobjetivos, proyecto_id, accion_proyecto, prueba_cierre, avance_estimado, estado_actual, revisar_en_minutos y opcional agenda y actividades_en_espera. plan es una lista de acciones válidas de 2 a 12, o [] al completar, abandonar o pausar. accion_proyecto: continuar, nuevo, completar, abandonar, pausar o sin_proyecto. No declares completado sin citar evidencia física pertinente. Elegí un plan que tenga sentido para tu situación."""

def brief_actions():
    from action_contracts import SUPPORTED_OPERATIONS
    missing=set(SUPPORTED_OPERATIONS)-set(SHORT_OPERATIONS)
    if missing:
        raise ValueError('Falta contrato abreviado de: '+', '.join(sorted(missing)))
    return 'OPERACIONES DISPONIBLES (usar solo estas):\n'+'\n'.join(
        '- '+op+': '+SHORT_OPERATIONS[op] for op in sorted(SUPPORTED_OPERATIONS))


def _size(value):
    return len(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8'))


# Nunca descartar la identidad ni el proyecto, ni el motivo del último cierre.
# El estado operativo y las delegaciones vigentes se preservan íntegros.
# No se consideran instrucciones automáticas de autocuidado.
_CORE=('momento','posición','necesidades','inventario_materiales',
       'proyecto_actual','ultimo_cierre_rechazado','proyectos_reanudables',
       'antecedente_relevante','preferencias_en_espera','regla')
_REDUCE_FIRST=('estrategias_que_ya_no_funcionaron','diagnosticos_operativos_recientes',
               'resultados_de_acciones','mediciones_reales_recientes','construcciones_fijas',
               'herramientas_que_llevo','percepción_local','navegacion_a_lugares',
               'comparaciones_validas','memorias_relevantes','conclusiones_verificadas',
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
    if _size(value)>byte_budget:
        raise ValueError('El contexto mínimo supera el presupuesto permitido.')
    value['contexto_reducido']='Vista acotada; la evidencia histórica sigue en SQLite.'
    if _size(value)>byte_budget:value.pop('contexto_reducido',None)
    return value
