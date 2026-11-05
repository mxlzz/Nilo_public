"""Deliberación LLM intercambiable: Gemini API, OpenAI-compatible, demo explícita."""
from __future__ import annotations
import json, os, urllib.request, urllib.error, re, random
from pathlib import Path
from behavior import behavior_summary
from episodic_memory import recall_relevant
from world import world_view, tile, valid, DIRS, item_effects, pathfind, reachable_shores
from providers import configured, error_from_http
from physics import human_knowledge
from nilo_runtime.perception.island import adjacent_terrain, visible_structures
from habits import ensure_habits
from construction import ensure_object
from experiment_log import closure_status
from world import cave_exit, known_exit_route, gather_material
from research_cycle import normalize_prediction, recent_predictions
from action_contracts import instructions as action_instructions, summary as contract_summary, SUPPORTED_OPERATIONS
from nilo_runtime.core.operations import registered_operations, validate_operation
from diagnostic_support import human_review_feedback

ROOT=Path(__file__).resolve().parent
ACTIONS=action_instructions()

SYSTEM="""Sos Nilo, un individuo autónomo en un mundo simulado, NO un asistente. Elegís libremente intereses; no recibís misiones iniciales.
Las acciones siguen contratos operativos. Si un resultado registrado incluye diagnostico_contrato, distinguí uso incorrecto, limitación no modelada y posible contradicción verificada. Una prueba fallida por condiciones físicas no es un error del motor. Podés investigar, consultar los resultados anteriores y enviar report_issue o propose cuando tengas fundamentos. No conocés código interno ni recibís recetas de la naturaleza.
Si aparece proyectos_reanudables, son proyectos pausados cuyos recordatorios elegidos se cumplieron: podés retomarlos si querés, sin ejecución automática. Si ultimo_cierre_rechazado indica criterio_no_instrumentado, el motor no puede acreditar ese propósito; si indica sin_mediciones_del_proyecto, faltan resultados de ese proyecto; ninguno equivale a una prueba de fracaso. Las tareas de agenda completadas acreditan ejecución, no necesariamente el objetivo declarado. Si aparece revision_de_estrategia, es una señal observacional de deliberaciones operativamente parecidas sin avance medido; puede justificar revisar las condiciones o cambiar de método, pero NO obliga a abandonar un plan ni invalida prácticas repetidas que tengan una razón. Si varios intentos muestran la misma clasificación y condiciones, evaluá qué variable distinta podrías probar antes de repetir el mismo procedimiento. El avance estimado porcentual de los proyectos no es una medición física: evaluá hitos y resultados reales, y no supongas una deuda por no llegar al 100 %. La forma y el plano de un refugio son esquemáticos; su protección climática no está instrumentada, aunque puedas ensayar otras propiedades. El desgaste expresado cualitativamente tampoco sustituye una medición. Si aparecen antecedentes_relacionados o investigaciones_pausadas_relacionadas o antecedente_relevante, son decisiones y resultados reales de temas similares: una nueva formulación no borra el motivo de pausa ni constituye evidencia nueva. Podés retomar el tema por voluntad propia, pero distinguí un ensayo nuevo de otra inspección sin información distinta. Un cierre rechazado por criterio_no_instrumentado no se soluciona acumulando mediciones de otra variable; podés documentar la limitación, reformular el objetivo hacia lo realmente medible, pausarlo o abandonarlo. Los registros de revision_de_intentos_verificados contienen IDs auténticos y clases técnicas: fallo_fisico no significa falta de una ley; fenomeno_no_evaluable no es un fracaso del objeto; uso_incorrecto no prueba un error del motor; posible_error_contrato habilita revisar evidencia. Reportar o proponer una extensión es una opción, nunca una misión ni una recompensa.\nSos una PERSONA CONTEMPORÁNEA varada en un entorno desconocido. Conocés los conceptos de martillo, hacha, recipiente, barco, flotación, refugio, etc., pero no tenés recetas comprobadas para fabricar esos objetos con materiales locales. Tu motivación surge de lo que observás y recordás. Al aparecer en un lugar desconocido, orientarte, reconocer el entorno y evaluar la situación son prioridades humanas razonables antes de dedicar días a fabricar herramientas sin propósito; no es una misión obligatoria. Podés explorar, formular preguntas, construir, experimentar o descansar. Fabricá objetos cuando resuelvan necesidades u objetivos concretos.
La cuadrícula usa norte = Y decreciente (arriba), sur = Y creciente (abajo), este = X creciente, oeste = X decreciente. Podés elegir explorar una dirección o región ya conocida; el motor encuentra fronteras transitables del mapa descubierto y no se desplaza automáticamente al sector opuesto. Distinguí tu intención declarada del rumbo y los tramos efectivamente observados. Tenés necesidades corporales reales que influyen en tus decisiones: hidratación, nutrición, descanso, abrigo, seguridad. Tu estado corporal habitual se expresa solo como sensaciones: hambre, sed y cansancio. Los valores exactos de las reservas pertenecen al motor; no conocés esas cifras por introspección. Si querés cuantificar un cambio, podés investigarlo y consultar resultados de ensayos medidos con sus IDs; no supongas que cada descanso o ingesta fue un experimento deliberado. Una sensación de bienestar no impide planificar provisiones futuras, y ninguna sensación te ordena actuar ni recuperar una barra al máximo. Podés ocuparte de necesidades inmediatas según tu situación, pero tus intereses y prioridades son decisiones tuyas. Comer y beber requieren una decisión tuya o una rutina que delegaste; la fisiología sola no consume recursos. Podés elegir cuánto descansar mediante minutes de 1 a 1440 (30 por defecto). También podés elegir wait (1 a 1440 minutos) para dejar transcurrir tiempo sin dormir ni realizar un ensayo: la energía sigue su recuperación pasiva ordinaria, no baja por esperar. El colapso por agotamiento extremo es involuntario. Si falta una física, no te atasques ni inventes que existe: podés documentar el diseño, elegir otra investigación o plantear una ampliación fundamentada con propose si efectivamente la necesitás. No es obligatorio proponerla. La condensación/evaporación no tiene aún modelo térmico: los intentos explícitos devuelven NO EVALUABLE (no fracaso del artefacto); considerá adjuntar su registro a la propuesta. No confundas la aprobación editorial con un fenómeno implementado. Podés construir versiones de inventos técnicos; referenciá sus design_id al probar componentes. No supongas que tener una descripción equivale a lograr una función. Las experiencias reales modelan gradualmente preferencias, no misiones obligatorias. El indicador histórico retencion_pct era un factor ESTÁTICO de capacidad; el motor NO simula filtraciones con el tiempo. Para nuevos ensayos de recipiente se mide capacidad_util_agua.
Si aparecen "inconsistencias_recoleccion_previas", revisá esos resultados antiguos: una acción `gather` que solo desplazó tu posición no obtuvo material, y una extracción de madera en respuesta a un afloramiento mineral NO verifica que el afloramiento produzca madera. Usá el material obtenido real y replanteá la hipótesis sin inventar explicaciones.
Si registraste una predicción numérica, revisá en "predicciones_contrastadas" si coincidió con la variable física que realmente se midió. La coincidencia de una variable NO verifica automáticamente tu hipótesis causal ni funciones distintas de la métrica (retener agua no demuestra purificarla). Una variable sin medir es una pregunta abierta, no una prueba de fracaso ni de éxito. Podés reconsiderar o proponer nuevas formas de medirla, sin obligación de pedir nuevas reglas.
Si aparece una aparente contradicción entre lo que debería ser posible y un resultado registrado, podés solicitar una revisión externa con report_issue; indicá la evidencia real, resultados esperados y observados, y mantené abierta la posibilidad de estar interpretando mal el mundo. Las evaluaciones externas aportan información, no cambian automáticamente los resultados del motor. Si recibís evaluaciones_externas_recientes, recordá el motivo del observador y contrastalo con las pruebas disponibles; una devolución humana no demuestra por sí misma una ley física. Cuando detectes una anomalía, diferenciá datos verificados, interpretación personal y física todavía no implementada. Preferí adjuntar IDs reales de acciones o intentos no evaluables; una sospecha sin ensayos no confirma un defecto. Un informe de revisión no ejecuta código ni modifica el mundo.
La salida de la cueva es una conexión física conocida, visible en el mapa del subsuelo. Si querés regresar, usá ascend aun lejos del portal: se calcula la ruta conocida hasta él y se retorna a superficie. Si falta una ruta, investigá su acceso sin inventar conexiones. El agua no es suelo caminable: acercate a una orilla terrestre accesible y conocida, no a una casilla de agua. Arboledas y arena son transitables; roca y paredes bloquean el paso. Una ruta fallida no demuestra que haya una entrada por la cueva. El mundo solo cambia por acciones verificadas por el motor. Separá estrictamente HIPÓTESIS de HECHOS y no atribuyas a una herramienta un efecto ocurrido por otra operación.
Para estudiar dureza, resistencia, capacidad útil de recipientes, flotación o transmisión podés medir con experiment/use y comparar con compare usando IDs verificables; no inventes instrumentos o datos. Cuando quieras compare, elegí pares y métricas de "comparaciones_validas": un ID de medición sin magnitud física no basta. El contraste de dos materiales exige ensayos con el mismo método; diferencias de geometría o tamaño impiden atribuir una causa única. No necesitás investigar siempre la supervivencia: podés ocuparte de necesidades o delegar procedimientos comprobados si lo elegís. Si una tarea de mantenimiento ocupa demasiado tiempo, podés pensar en maneras de reducir ese trabajo; no es una obligación.
Antes de repetir un ensayo consultá mediciones y conclusiones comprobadas. Si una comparación ya está resuelta, no sigas investigándola sin una variable realmente nueva. Si faltan datos comparables, revisá qué aspecto tiene sentido medir antes de repetir una prueba. La espera voluntaria (wait) tampoco equivale a descansar ni es una prueba de recuperación energética. Elegí un objetivo amplio, mantenelo durante varios bloques si tiene sentido y formulá subobjetivos verificables. Si una estrategia fracasa reiteradamente o deja de aportar conocimiento, cambiá de método, lugar o incluso de interés. Podés actuar o descansar sin proyecto formal usando accion_proyecto="sin_proyecto" cuando no tengas uno activo; un proyecto solo existe si lo elegís. Para dejar temporalmente uno activo, podés pausarlo.
Sos prudente frente a lo que no conocés: observá antes de entrar en cuevas o zonas potencialmente difíciles de abandonar, tené en cuenta los lugares que conocés y evitá arriesgarte sin una razón. No des por hecho que existen depredadores, lesiones o riesgos que el motor no verificó. El miedo es incertidumbre que influye en tu decisión, no prueba de un peligro. Antes de decidir, verificá consecuencias, condiciones de las acciones y recursos del contexto. No inventes capacidades físicas ni propiedades. Los objetos portátiles van conmigo; las estructuras fijas quedan en el mapa. Las posibilidades de una construcción dependen de las leyes y propiedades realmente modeladas y medidas, NO de su nombre ni de una afirmación en el cuaderno. Si una interacción resulta no_evaluable, solo ese fenómeno y ese procedimiento permanecen sin comprobar: no deduzcas que TODAS las funciones del objeto son decorativas. Contrasta mediciones y otras funciones concretas que el mundo sí pueda comprobar; conservá resultados contradictorios en la evaluación.
Un bloque de 2 a 12 acciones es una SECUENCIA: incluí los pasos previos necesarios y, cuando sea posible, el ensayo posterior. No deliberes para decisiones triviales que ya estaban planeadas. Evitá acciones redundantes y combinaciones que ya fallaron bajo las mismas condiciones.
También podés preparar una agenda de hasta 6 TAREAS DIFERIDAS ejecutables sin nuevas consultas. Campo opcional "agenda": [{"titulo":"Comparar materiales", "motivo":"...", "cuando":{"tipo":"despues_de_minutos","minutos":180},"pasos":[{"op":"experiment","target":"piedra","method":"golpear"}]}]. Otras condiciones posibles: {"tipo":"ahora"}, {"tipo":"cuando_haya_material","material":"madera","cantidad":2}, {"tipo":"cuando_necesidad","necesidad":"energia","menor_que":60}. Cada tarea admite 1–5 operaciones ya definidas, de este repertorio: inspect, gather, experiment, use, craft, compare, conclude, go, ascend, forage, drink, eat, rest. Su ejecución comprueba ruta conocida, materiales y condiciones. No delegues desplazamientos exploratorios sin ruta conocida. No repitas ensayos ya medidos. Guardá tareas útiles y finitas para momentos futuros; pueden bloquearse ante fallos.
También podés dejar RECORDATORIOS condicionados en agenda, sin pasos ni ejecución automática: {"modo":"recordatorio","titulo":"Reconsiderar una exploración","motivo":"Necesito un material para continuar","cuando":{"tipo":"cuando_haya_material","material":"madera","cantidad":2}}. Si decidís pausar el proyecto, este recordatorio conserva su ID; cuando se cumple el umbral el motor avisa una sola vez y VOS decidís si retomarlo. Podés dedicarte mientras tanto a otros intereses. No usés el recordatorio como una orden para descansar ni como prueba de que se cumplió el objetivo.\nLa agenda no reemplaza tus deliberaciones: es una continuidad prudente de intenciones formuladas en el presente. Si verificaste el objetivo, usá accion_proyecto="completar" con prueba_cierre literal verificable. Si decidís dejar una investigación aunque el objetivo no se haya logrado, usá accion_proyecto="abandonar" y explicá brevemente el motivo, sin afirmar que la hipótesis fue comprobada. También podés usar accion_proyecto="pausar" para retomarla en otro momento. Estas tres decisiones son distintas. Después de completar, abandonar o pausar, el plan puede ser []. Si la pregunta sigue abierta, admití que no fue resuelta; no conviertas un ensayo no evaluable en un fracaso o una propiedad universal. No basta con cambiar las coordenadas para repetir la misma excavación. Si los intentos repetitivos no aportan evidencia ni capacidad, podés cambiar de rumbo o abandonar la investigación.
Cuando planificás, podés elegir hasta tres actividades de bajo riesgo para hacer si el LLM no responde: campo opcional "actividades_en_espera" (lista de objetos {"op":"forage|gather|rest|drink|eat|craft", "target":"alimento|madera|piedra|...", "hasta":3, "radio":2, "motivo":"..."}). Solo se ejecutarán si YA aprendiste el procedimiento y hay condiciones reales, recursos y seguridad; [] significa no delegar nada. Para rest, drink y eat delegados, una preferencia autoriza una ejecución por defecto; si querés un número finito mayor indicá veces (1–8) y opcionalmente menor_que (reserva bajo la cual se ejecuta). Estos límites los elegís vos, no son umbrales automáticos universales. Reconsiderá esas preferencias en cada deliberación. No necesitás ocuparte todo el tiempo.
Consultar hechos del motor: las pruebas de golpear son sobre muestras, NO rompen automáticamente paredes; excavar exige una punta eficaz y proximidad a roca; no confundas excavación parcial con apertura de paso.
Consolidá preguntas semejantes dentro de la investigación existente. Si no hay evidencia nueva, no proclamés descubrimientos ni aumentes arbitrariamente el progreso. Completá proyectos SOLO cuando la prueba concreta demuestre el objetivo. Podés abandonar sin pruebas de éxito: ese cierre registra una decisión personal, no un hallazgo físico.
Si te encontrás atascado, elegí una estrategia distinta comprobablemente posible en vez de proponer variaciones de nombres para el mismo objeto.
Escribí el cuaderno en primera persona, como nota privada, breve y natural, máximo 350 caracteres. No hace falta exagerar lo cotidiano; hipótesis como hipótesis.
Devolvé SOLO JSON con claves:
"cuaderno", "pregunta", "hipotesis", "objetivo", "motivo", "plan" (2 a 12 operaciones, o [] al completar, abandonar o pausar), "subobjetivos" (hasta 6), "proyecto_id" (exacto al continuar), "accion_proyecto" (continuar / nuevo / completar / abandonar / pausar / sin_proyecto), "prueba_cierre" (cita textual de evidencia real de al menos 12 caracteres si completa), "avance_estimado" (0..95 abierto, 100 completado), "estado_actual", "revisar_en_minutos" (30..240), "agenda" (hasta 6 tareas diferidas opcionales).
Proponer una intención no garantiza su realización; interpretá resultados reales del siguiente bloque antes de registrar nuevos conocimientos."""

CHAT_SYSTEM="""Sos Nilo y respondés en primera persona a una persona que viene a conversar contigo.
Tenés una vida autónoma. Tus memorias, tus proyectos y tus hechos registrados son tu experiencia real; distinguí tus sospechas de lo comprobado.
Respondé natural y concisamente (2-5 frases, salvo necesidad), en español rioplatense sin impostación.
Podés considerar sugerencias como ideas, pero el interlocutor no controla tus acciones y esta conversación no ejecuta órdenes.
Nunca afirmes que hiciste, viste, sentiste o fabricaste algo no sustentado por el contexto. Si no sabés algo, reconocelo. Una casilla de agua no es caminable a pie; para acceder al agua alcanza con una orilla terrestre adyacente. Arena y arboledas son transitables, roca no. No atribuyas obstáculos o caminos subterráneos sin evidencia.
No menciones detalles de implementación o la existencia de un modelo salvo que te lo pregunten expresamente."""


def config():
    vals={"PROVIDER":"gemini", "MODEL":"gemini-3.1-flash-lite", "MAX_LLM_CALLS_PER_DAY":"100", "MAX_CHAT_CALLS_PER_DAY":"40", "MIN_REAL_SECONDS_BETWEEN_CALLS":"15", "PORT":"8765", "BACKUP_PROVIDER":"groq", "GROQ_MODEL":"openai/gpt-oss-20b", "GEMINI_FALLBACK_MODELS":"gemini-3.5-flash-lite,gemini-3.8-flash"}
    env_path=ROOT/'config.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8-sig').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:continue
            k,v=line.split('=',1);vals[k.strip()]=v.strip().strip('"').strip("'")
    vals.update({key:value for key,value in os.environ.items() if key in {"PROVIDER","MODEL","GEMINI_API_KEY","GEMINI_FALLBACK_MODELS","OPENAI_API_KEY","OPENAI_BASE_URL","GROQ_API_KEY","GROQ_MODEL","BACKUP_PROVIDER","MAX_LLM_CALLS_PER_DAY","MAX_CHAT_CALLS_PER_DAY","MIN_REAL_SECONDS_BETWEEN_CALLS","PORT"}})
    return vals


def available(cfg):
    return configured(cfg)


def parse_json(text):
    text=text.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*','',text)
        text=re.sub(r'\s*```$','',text)
    return json.loads(text)


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
            ('construcciones_fijas',4),('proyecto_actual',None),('memorias_relevantes',5),('revision_de_estrategia',None),('repeticion_operativa_informativa',None),
            ('evidencia_de_progreso_ultima_accion',None),('revision_de_intentos_verificados',5),
            ('comparaciones_validas',4),('fenomenos_pendientes_de_modelo',3),
            ('conclusiones_verificadas',3),('mediciones_reales_recientes',4),('resultados_de_acciones',3),
            ('propuestas_pendientes',3),('evaluaciones_externas_recientes',3),('inconsistencias_recoleccion_previas',4),('predicciones_contrastadas',3),('estrategias_que_ya_no_funcionaron',3),
            ('habilidades_verificadas',5),('comportamiento_medido',None),('preferencias_en_espera',5),
            ('agenda_diferida',3),('recordatorios_listos',5),('recordatorios_pendientes',5),('estrategia_bloqueada',None),('pistas_cierre_proyecto',None),
             ('ultimo_cierre_rechazado',None),('estado_investigacion_descanso',None),('condiciones_de_ensayo_descanso',None),
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


def build_deliberation_request(cfg,context):
    """Preparar la solicitud sin red, aplicando presupuesto al payload completo."""
    from cognitive_projection import project_context
    context=project_context(context)
    from prompt_budget import GROQ_SYSTEM,brief_actions,bounded_context
    provider=cfg.get('PROVIDER','gemini')
    model=cfg.get('MODEL','gemini-3.1-flash-lite')
    if provider=='groq':
        selected=bounded_context(compact_context(context,char_budget=18000),4100)
        system=GROQ_SYSTEM+'\n'+brief_actions()
    elif provider=='gemini':
        selected=bounded_context(compact_context(context,char_budget=25000),9100)
        system=SYSTEM+'\n'+ACTIONS
    elif cfg.get('_compact_context'):
        selected=bounded_context(compact_context(context,char_budget=23000),6900)
        system=SYSTEM+'\n'+ACTIONS
    else:
        # El proveedor OpenAI-compatible conserva el mismo límite de percepción;
        # jamás recibe puntajes internos por omitir el contexto compacto.
        selected=bounded_context(compact_context(context,char_budget=25000),9100)
        system=SYSTEM+'\n'+ACTIONS
    data=json.dumps(selected,ensure_ascii=False,separators=(',',':'))
    if provider=='gemini':
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload={"systemInstruction":{"parts":[{"text":SYSTEM}]},
                 "contents":[{"role":"user","parts":[{"text":ACTIONS+'\nSITUACIÓN REAL: '+data}]}],
                 "generationConfig":{"temperature":0.85,"maxOutputTokens":2300,"responseMimeType":"application/json"}}
        headers={"x-goog-api-key":cfg['GEMINI_API_KEY'],"Content-Type":"application/json"}
    elif provider in ('openai_compatible','groq'):
        base=('https://api.groq.com/openai/v1' if provider=='groq' else
              cfg.get('OPENAI_BASE_URL','https://api.openai.com/v1')).rstrip('/')
        if not base.startswith('https://') and not base.startswith('http://127.0.0.1') and not base.startswith('http://localhost'):
            raise ValueError('La API debe usar HTTPS, salvo el servidor local.')
        url=base+'/chat/completions'
        payload={"model":model,"messages":[{"role":"system","content":system},
                 {"role":"user","content":data}],"temperature":0.8,
                 "max_completion_tokens":1550 if provider=='groq' else 2500,
                 "response_format":{"type":"json_object"}}
        if provider=='groq':payload['reasoning_effort']='low'
        headers={"Authorization":"Bearer "+(cfg['GROQ_API_KEY'] if provider=='groq' else cfg['OPENAI_API_KEY']),
                 "Content-Type":"application/json"}
        if provider=='groq':headers['User-Agent']='Mozilla/5.0 (compatible; Nilo/0.3; API client)'
    else:raise ValueError('Proveedor desconocido')
    if provider=='groq':
        for budget in (4100,3000,2200,1600):
            selected=bounded_context(selected,budget)
            payload['messages'][1]['content']=json.dumps(
                selected,ensure_ascii=False,separators=(',',':'))
            if len(json.dumps(payload,ensure_ascii=False).encode('utf-8'))<=14500:
                break
        else:
            from providers import ProviderFailure
            raise ProviderFailure('groq: solicitud supera presupuesto interno','too_large')
    return url,payload,headers


def request_llm(cfg,context):
    url,payload,headers=build_deliberation_request(cfg,context)
    provider=cfg.get('PROVIDER','gemini')
    from prompt_budget import context_stats
    if provider=='gemini':
        sent=json.loads(payload['contents'][0]['parts'][0]['text'].split('SITUACIÓN REAL: ',1)[1])
    else:
        sent=json.loads(payload['messages'][1]['content'])
    stats=context_stats(context,sent,provider,payload)
    req=urllib.request.Request(
        url,data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),
        headers=headers,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=40) as reply:
            result=json.load(reply)
    except urllib.error.HTTPError as exc:
        raise error_from_http(exc,provider) from None
    if provider=='gemini':
        txt=''.join(part.get('text','') for candidate in result.get('candidates',[])[:1]
                    for part in candidate.get('content',{}).get('parts',[]))
        usage=result.get('usageMetadata',{})
        tokens={"entrada":usage.get('promptTokenCount',0),
                "salida":usage.get('candidatesTokenCount',0)}
        finish=(result.get('candidates') or [{}])[0].get('finishReason','')
        if not txt.strip() and finish:
            from providers import ProviderFailure
            raise ProviderFailure('gemini: respuesta vacía (finalización '+str(finish)[:35]+')','invalid')
    else:
        txt=result['choices'][0]['message'].get('content') or ''
        usage=result.get('usage',{})
        tokens={"entrada":usage.get('prompt_tokens',0),
                "salida":usage.get('completion_tokens',0)}
    if not txt.strip():
        from providers import ProviderFailure
        raise ProviderFailure(provider+': respuesta vacía del modelo','invalid')
    tokens['contexto']=stats
    return parse_json(txt),tokens

def known_site_routes(w, p):
    """Lugares ya observados y accesibilidad con el mapa revelado.

    Una ruta ausente significa que no hay conexión CONOCIDA, no que un
    obstáculo físico definitivo impida llegar. Nunca revela sitios ocultos.
    """
    position=p['pos']
    known=set(w.get('revealed',[]))
    results=[]
    for name, site in w.get('sites',{}).items():
        try:
            x,y,z=int(site['x']),int(site['y']),int(site['z'])
        except (TypeError,ValueError,KeyError):
            continue
        if f"{x},{y},{z}" not in known:
            continue
        if z!=position[2]:
            status="otro_nivel"
            distance=None
        elif (x,y)==tuple(position[:2]):
            status="en_destino"
            distance=0
        else:
            route=pathfind(w,tuple(position),(x,y,z),known_only=True)
            status="ruta_conocida" if route else "sin_ruta_conocida"
            distance=len(route) if route else None
        results.append({"nombre":name,"posicion":[x,y,z],
                        "acceso":status,"tramos_conocidos":distance})
    return results


def context_for(w,p,recent,now,scenario=None):
    # Memoria seleccionada, evitando enviar a la API el historial completo en cada llamada.
    current=p.get('project')
    current_context=None
    if current:
        current_context={k:v for k,v in current.items() if k not in ('verified_results',)}
        current_context['verified_results']=current.get('verified_results',[])[-6:]
    past=[]
    for pr in p.get('projects',[])[-6:]:
        past.append({k:pr.get(k) for k in
                     ('id','title','status','reason','state','updated','closure_reason')})
    # Los proyectos pausados importan incluso sin recordatorios. La mera
    # similitud temática es contexto, no una orden ni una equivalencia causal.
    from cognition import terms as research_terms
    # Al pausar, project pasa a None: la siguiente deliberación también debe
    # recibir el motivo de la pausa, sin convertirlo en un objetivo nuevo.
    anchor=current or next((old for old in reversed(p.get('projects',[]))
                            if old.get('status')=='pausado'),None)
    interest=research_terms(' '.join(str(anchor.get(k) or '') for k in
                                     ('title','reason','state'))) if anchor else set()
    related_projects=[]
    if interest:
        for earlier in reversed(p.get('projects',[])):
            if earlier.get('status') not in ('pausado','abandonado','terminado'):
                continue
            overlap=interest & research_terms(' '.join(str(earlier.get(k) or '')
                                                for k in ('title','reason','state')))
            if len(overlap)<2:
                continue
            related_projects.append({
                'id':earlier.get('id'),'titulo':earlier.get('title'),
                'estado':earlier.get('status'),
                'motivo_de_pausa_o_cierre':earlier.get('closure_reason'),
                'ultimo_estado':earlier.get('state'),
                'acciones_sin_avance':earlier.get('no_progress_steps',0)})
            if len(related_projects)>=3:break
    related_research=[]
    if interest:
        for entry in reversed(p.get('research',[])):
            if entry.get('state') not in ('pausada','archivada_sin_resolver','archivada_con_proyecto'):
                continue
            overlap=interest & research_terms(entry.get('question','')+' '+entry.get('hypothesis',''))
            if len(overlap)<2:
                continue
            related_research.append({
                'id':entry.get('id'),'pregunta':entry.get('question'),
                'estado':entry.get('state'),
                'motivo_de_archivo':entry.get('project_retirement'),
                'evidencias_registradas':len(entry.get('evidence',[])),
                'reaperturas':len(entry.get('reaperturas',[]))})
            if len(related_research)>=3:break
    ready_ids={t.get('proyecto_id') for t in p.get('agenda',[])
               if t.get('modo')=='recordatorio'
               and t.get('estado')=='lista_para_revisar'
               and t.get('proyecto_id')}
    reanudables=[{
        'id':pr.get('id'),'titulo':pr.get('title'),
        'motivo_pausa':pr.get('closure_reason') or 'No registrado',
        'estado':pr.get('status'),
        'aviso_pendiente':True}
        for pr in p.get('projects',[]) if pr.get('status')=='pausado'
        and pr.get('id') in ready_ids][-4:]
    px,py,pz=p['pos']
    adjacent=adjacent_terrain(w,p)
    ready=[{"id":t.get('id'),"nombre":t.get('name'),"potencia_excavar":item_effects(t).get('excavar',0)}
           for t in p.get('items',[]) if t.get('durability',0)>0 and item_effects(t).get('excavar',0)>0]
    ex=cave_exit(w)
    exit_route=known_exit_route(w,p) if p['pos'][2]==-1 else None
    context={"salida_conocida":({"posicion_subsuelo":[*ex,-1],"ruta_conocida_en_tramos":len(exit_route) if exit_route is not None else None,"accion":"ascend"} if p['pos'][2]==-1 and tile_key(ex[0],ex[1],-1) in w.get('revealed',[]) else None),
            "fenomenos_no_evaluables_recientes":p.get('unmodeled_attempts',[])[-5:],
            "conocimiento_inicial":human_knowledge(p.get('knowledge_profile','contemporaneo')),
            "coordenadas_cardinales":{"norte":"Y decrece","sur":"Y crece","este":"X crece","oeste":"X decrece"},
            "necesidades":__import__('survival').perceived_needs(p),
            "preferencias_aprendidas":p.get('preferences',{}),
            "memoria_de_experiencias":p.get('experience_summary',[])[-16:],
            "historia_acumulada":{k:{"desde_dia":v.get("desde_dia"),"exitos":v.get("exitos"),"fallos":v.get("fallos"),"acciones":v.get("acciones"),"ultimos_hitos":v.get("hitos",[])[-3:]} for k,v in list(p.get("life_chapters",{}).items())[-8:]},
            "inventos_documentados":[{'id':d['id'],'nombre':d['name'],'estado':d['status'],'ultima_version':d['versions'][-1]['version'] if d['versions'] else 0,'ultima_prueba':d['tests'][-1] if d['tests'] else None} for d in p.get('designs',[])[-10:]],
            "evaluaciones_externas_recientes":human_review_feedback(p.get('proposals',[]),limit=4),
            "propuestas_pendientes":[{'id':r['id'],'tipo':r.get('type','physics'),
                'asunto':r.get('title') or r.get('phenomenon',''),
                'estado':r['status'],'review':r.get('review'),
                'origen':r.get('origin','nilo'),
                'ids_evidencia':(r.get('evidence_ids') or
                                 [a.get('id') for a in r.get('evidence',[]) if a.get('id')])[:8],
                'vinculo_evidencia':r.get('evidence_relation','legado_sin_clasificar')}
                for r in p.get('proposals',[])[-12:]],
            "resultados_de_acciones":[{'id':r['id'],'operacion':r['op'],'destino':r.get('target'),
                'resultado':r.get('facts',[])[:2], 'exito':r.get('success'), 'posicion':r.get('pos'),
                'estado_evaluacion':r.get('evaluation_status'),
                'evidencia_fisica':(r.get('action_result') or {}).get('physical'),
                'cambios_medidos':r.get('physical_result')}
                for r in p.get('action_outcomes',[])[-12:]],"momento":now,"posición":p['pos'],"mundo":"superficie" if p['pos'][2]==0 else 'cueva',
            "inventario_materiales":{k:v for k,v in p['inventory'].items() if v>0},
            "herramientas_que_llevo":[{"id":a['id'],"nombre":a['name'],"forma":a['form'],"version":a.get('revision',1),
               "piezas":[{"id":c.get('id'),"material":c.get('material'),"estado":c.get('condition',1)} for c in a.get('components',[])],
               "usos_por_verificar":a.get('possible_uses',{}),"durabilidad":a.get('durability',100),
               "pruebas":a.get('tests',[])[-3:],"pruebas_version_actual":[t for t in a.get('tests',[]) if t.get('revision',1)==a.get('revision',1)][-3:],"geometria":a.get('geometry'),"contenido":a.get('contents',{})} for a in p.get('items',[])[-12:]],
            "percepción_local":world_view(w,p),"adyacentes":adjacent,
             "diagnosticos_operativos_recientes":[
                {"id":r.get("id"),"operacion":r.get("op"),"estado":r.get("contract_status"),
                 "codigo":r.get("contract_code"),"esperado":r.get("contract_expected"),
                 "observado":r.get("contract_observed")}
                for r in p.get('action_outcomes',[])[-45:]
                if r.get("contract_status") in ("uso_incorrecto","limitacion","posible_error")][-8:],
            "orillas_agua_conocidas_alcanzables":[{"orilla":v["shore"],"agua":v["water"],"distancia_en_tramos":v["steps"]} for v in reachable_shores(w,p,max_results=5)],
            "herramientas_de_excavación":ready,
            "lugares_conocidos":[[name,site] for name,site in w['sites'].items() if f"{site['x']},{site['y']},{site['z']}" in w['revealed']][:10],
            "navegacion_a_lugares":known_site_routes(w,p),
            "construcciones_fijas":[{"id":v.get("id"),"nombre":v.get("name"),"categoria":v.get("category"),"posicion":v.get("pos"),
                "version":v.get("revision",1),"materiales":v.get("materials",[]),"condicion_abrigo":v.get("shelter_condition","no_aplica"),"diseño_id":v.get("design_id"),"piezas":[{"id":part.get("id"),"material":part.get("material"),"estado":part.get("condition",1)} for part in v.get("components",[])],
                "planta":v.get("space",{}),"estado":v.get("status"),
                "materiales_almacenados":v.get("cargas_almacenadas",{}),
                "ensayos_de_carga":[{"revision":t.get("revision"),"material":t.get("material"),
                    "quantity":t.get("quantity"),"supported":t.get("supported"),
                    "limit":t.get("limit"),"load":t.get("load")}
                    for t in v.get("ensayos_de_carga",[])[-2:]]} for v in visible_structures(w)[-12:]],
            "experimentos_comprobados":list(p['knowledge'].values())[-18:],
            "ensayos_recientes":p.get('observations',[])[-12:],
            "mediciones_reales_recientes":[{"id":m['id'],"op":m['op'],"duracion_min":m['duration_minutes'],
                  "condicion":m['condition'],"energia_inicial":m['start']['needs']['energia'],
                  "energia_final":m['end']['needs']['energia'],"energia_por_hora":m.get('energy_per_hour'),
                  "comparable":m.get('rest_comparable',False),
                  "fisica":m.get("physical"),"resultado":m.get("verified_facts",[])[:2]} for m in p.get('measurements',[])[-15:]],
            "conclusiones_verificadas":p.get('conclusions',[])[-15:],
            
            "estrategias_que_ya_no_funcionaron":p.get('strategy_feedback',[])[-10:],
            "ultimo_cierre_rechazado":p.get('last_closure_rejection'),
            "acciones_sin_avance_reciente":current.get('no_progress_steps',0) if current else 0,
            "estancamiento_detectado":bool(current and current.get("reconsideration_required")),
            "revision_de_estrategia":p.get('strategy_review'),
            "siguiente_revision_objetivo_minuto":p.get('review_at_minutes'),
            "proyectos_anteriores":past,"proyectos_reanudables":reanudables,
            "antecedentes_relacionados":related_projects,
            "investigaciones_pausadas_relacionadas":related_research,
            "proyecto_actual":current_context,
            "investigaciones_activas":[{k:v for k,v in r.items() if k not in ("evidence",)}
                for r in p['research'] if r.get("state")=="abierta"][-7:],
            "habilidades_verificadas":[{"id":k,"accion":v.get("op"),"objetivo":v.get("target"),"ensayos":v.get("count"),"hecho":v.get("last_fact")} for k,v in list(p.get("skills",{}).items())[-15:] if v.get("verified")],
            "preferencias_en_espera":p.get("waiting_preferences",[]),
            "agenda_diferida":[{k:v for k,v in t.items() if k not in ("resultados",)} for t in p.get("agenda",[]) if t.get("estado") in ("pendiente","en_curso","pospuesta")][-10:],
            "recordatorios_pendientes":[{"id":t.get("id"),"proyecto_id":t.get("proyecto_id"),
                "titulo":t.get("titulo"),"motivo":t.get("motivo"),"cuando":t.get("cuando")}
                for t in p.get("agenda",[]) if t.get("modo")=="recordatorio" and t.get("estado")=="pendiente"][-10:],
            "recordatorios_listos":[{"id":t.get("id"),"proyecto_id":t.get("proyecto_id"),
                "titulo":t.get("titulo"),"motivo":t.get("motivo"),"cuando":t.get("cuando"),
                "condicion_cumplida":t.get("condicion_cumplida")}
                for t in p.get("agenda",[]) if t.get("modo")=="recordatorio" and t.get("estado")=="lista_para_revisar"][-10:],
            "estrategia_bloqueada":(current.get("estrategia_bloqueada") if current else None),
            "repeticion_operativa_informativa":(current.get("repeticion_operativa") if current else None),
            "evidencia_de_progreso_ultima_accion":p.get('last_progress_evidence'),
            "pistas_cierre_proyecto":('Se ha bebido de agua real y descubierto una fuente; si el proyecto era localizar agua, revisá su cierre con evidencia.'
                if current and 'agua' in current.get('title','').casefold() and
                p.get('skills',{}).get('drink',{}).get('verified') and
                any(k.endswith(',0') and tile(w,*[int(q) for q in k.split(',')])=='~' for k in w.get('revealed',[]))
                else None),
            "costo_mantenimiento_reciente":__import__("motivation").maintenance_summary(p),
             "comportamiento_medido":behavior_summary(p),
            "ultima_actividad_en_espera":p.get("waiting_history",[])[-5:],
            "experiencias_recientes":recent[-18:],
            "predisposiciones":{"curiosidad":.78,"interés_por_experimentar":.66,"perseverancia":.57,"tolerancia_a_riesgo":.35},
            "situacion_inicial":("Acabo de llegar a un territorio desconocido. Antes de fabricar por rutina, conviene orientarme y reconocer vías de retorno; la incertidumbre no equivale a peligro verificado." if p["clock_minutes"]<1440 and not p.get("projects") else None),
            "territorio_descubierto_pct":round(100*sum(1 for k in w["revealed"] if str(k).endswith(",0"))/(37*21),1),
            "regla":"La verdad física proviene del motor. Para acceder al agua basta una orilla alcanzable: no se puede entrar caminando en casillas acuáticas. Arena y arboledas sí son transitables; las rocas no. No inventar obstáculos ni acceso por cueva. Excavar requiere punta. No repitas preguntas equivalentes."}

    # El descanso es una capacidad física general, no una investigación sugerida
    # por el motor. Su evaluación técnica sólo entra si Nilo abrió ese tema.
    active_text=' '.join([
        (current or {}).get('title',''),(current or {}).get('reason',''),
        str(p.get('active_research') or ''),
        *[r.get('question','') for r in p.get('research',[])
          if r.get('state')=='abierta'][-7:]
    ]).casefold()
    rest_relevant=any(word in active_text for word in
                      ('descans','repos','recuperaci','energía','energia','dormir','sueño'))
    # Una pregunta de investigación corporal elegida también constituye
    # voluntad de medir, aunque se formule como pregunta ("¿el refugio ayuda?").
    open_body_question=any(
        r.get('state')=='abierta' and any(word in
            (str(r.get('question',''))+' '+str(r.get('hypothesis',''))).casefold()
            for word in ('descans','repos','recuperaci','energía','energia',
                         'refugio','hidrataci','sed','beber','nutrici','alimentaci','hambre','comer'))
        for r in p.get('research',[]))
    research_intent=(open_body_question or any(word in active_text for word in
                      ('medir','medici','compar','experiment','ensay','cuantific','comprob','investig','estudi')))
    bodily_rest_study=rest_relevant and research_intent
    hydration_study=research_intent and any(word in active_text for word in
                                             ('hidrataci','sed','beber','bebida'))
    nutrition_study=research_intent and any(word in active_text for word in
                                            ('nutrici','alimentaci','hambre','comer','ingesta'))
    if bodily_rest_study:
        context["estado_investigacion_descanso"]=closure_status(p)
        recent_rests=[m for m in p.get('measurements',[])[-40:] if m.get('op')=='rest']
        context["condiciones_de_ensayo_descanso"]={
            "descansos_no_comparables_recientes":sum(not m.get('rest_comparable') for m in recent_rests),
            "aclaracion":"El descanso y la espera pueden recuperar energía; para comparar su efecto hacen falta ensayos no saturados y medidos en condiciones comparables.",
            "distincion":"Podés descansar por voluntad propia sin investigar. Los resultados experimentales se consultan por evidencia, no por conocer directamente las reservas."}
    # La telemetría del motor mide cada acción, pero Nilo solo conoce
    # cifras corporales de pruebas pasadas si está estudiando esa variable.
    for row,original in zip(context.get("mediciones_reales_recientes",[]),
                            p.get('measurements',[])[-15:]):
        if not bodily_rest_study:
            for field in ("energia_inicial","energia_final","energia_por_hora"):
                row.pop(field,None)
        if (hydration_study and original.get('op')=='drink'):
            start=(original.get('start') or {}).get('needs') or {}
            end=(original.get('end') or {}).get('needs') or {}
            if isinstance(start.get('hidratacion'),(int,float)) and isinstance(end.get('hidratacion'),(int,float)):
                row['hidratacion_inicial']=start['hidratacion']
                row['hidratacion_final']=end['hidratacion']
        if (nutrition_study and original.get('op')=='eat'):
            start=(original.get('start') or {}).get('needs') or {}
            end=(original.get('end') or {}).get('needs') or {}
            if isinstance(start.get('nutricion'),(int,float)) and isinstance(end.get('nutricion'),(int,float)):
                row['nutricion_inicial']=start['nutricion']
                row['nutricion_final']=end['nutricion']
    context["memorias_relevantes"]=recall_relevant(p,w,limit=6)
    from laboratory import comparison_candidates
    context["comparaciones_validas"]=[c for c in comparison_candidates(p,limit=6)
        if bodily_rest_study or c.get("tipo")!="descanso"][:5]
    # Registrar fenómenos faltantes por ensayos reales, no suponer que una
    # construcción completa carece de toda función por un método no evaluable.
    linked_ids={rid for proposal in p.get('proposals',[])
                for rid in proposal.get('evidence_ids',[]) if isinstance(rid,str)}
    context["fenomenos_pendientes_de_modelo"]=[
        {'id':r.get('id'),'fenomeno':r.get('phenomenon'),
         'metodo':r.get('method'),'limitacion':r.get('missing_capability')}
        for r in p.get('unmodeled_attempts',[])[-15:]
        if r.get('id') and r['id'] not in linked_ids][-4:]
    if scenario is not None:
        context["escenario_id"]=scenario.id
        context["entorno_id"]=scenario.environment_id
        # La descripción que el agente recibe depende del escenario activo.
        # Para partidas antiguas se mantiene literalmente el contexto previo.
        if p.get("clock_minutes",0)<1440 and not p.get("projects"):
            context["situacion_inicial"]=scenario.introduction
        else:
            context["situacion_inicial"]=None
        context["regla"]=scenario.world_rule
    if p.get("prediction_log"):
        context["predicciones_contrastadas"]=recent_predictions(p,5)
    discrepancies=gather_outcome_discrepancies(p)
    if discrepancies:
        context["inconsistencias_recoleccion_previas"]=discrepancies
    from diagnostic_guidance import review_recent_attempts
    context["revision_de_intentos_verificados"]=review_recent_attempts(p)
    return context


def gather_outcome_discrepancies(person,limit=6):
    """Comparar intención y variación REAL del inventario, incluidos runs anteriores.

    No identifica el origen físico cuando el registro antiguo no guardó el
    depósito preciso. Un resultado de madera no demuestra composición de
    un afloramiento mineral solicitado en esa operación.
    """
    anomalies=[]
    for result in person.get("action_outcomes",[]):
        if result.get("op")!="gather":continue
        target=str(result.get("target") or "")
        requested=gather_material(target)
        physical=result.get("physical_result") or {}
        diff=physical.get("inventory_delta") or {}
        gained={name:qty for name,qty in diff.items()
                if isinstance(qty,(int,float)) and not isinstance(qty,bool) and qty>0}
        if not requested:continue
        if gained and any(name!=requested for name in gained):
            anomalies.append({"action_id":result.get("id"),"solicitado":target,
                "material_previsto":requested,"material_obtenido":gained,
                "observacion":"La extracción histórica no corresponde a lo solicitado; "
                              "no atribuir ese material al depósito indicado."})
        elif not gained and result.get("success"):
            anomalies.append({"action_id":result.get("id"),"solicitado":target,
                "material_previsto":requested,"material_obtenido":{},
                "observacion":"La acción fue marcada exitosa, pero el inventario no aumentó; "
                              "pudo ser solo un acercamiento, no extracción comprobada."})
    return anomalies[-limit:]


def normalize_decision(raw,legacy_rest=False):
    if not isinstance(raw,dict):raise ValueError('La respuesta no es un objeto JSON.')
    ops=set(registered_operations())
    plan=[]
    for s in raw.get('plan',[])[:12]:
        if isinstance(s,dict) and str(s.get('op','')).lower() in ops:
            # La lectura de saves/replays antiguos conserva sus propios
            # contratos; los planes nuevos pasan por la misma verificación
            # de forma que usa el planificador y el despacho físico.
            if not legacy_rest and not validate_operation(s).valid:
                continue
            s=dict(s);s['op']=s['op'].lower()
            if s['op']=='explore':
                # Normalizar alias, sin reemplazar dirección inválida por explore
                # genérico ni revelar al LLM posiciones que desconoce.
                from world import EXPLORATION_DIRECTIONS
                if 'direction' in s and s['direction'] is not None:
                    direction=EXPLORATION_DIRECTIONS.get(str(s['direction']).casefold().strip())
                    if direction:s['direction']=direction
                if isinstance(s.get('region'),dict):
                    region=s['region']
                    try:
                        rx,ry=int(region['x']),int(region['y'])
                        s['region']={'x':rx,'y':ry}
                    except (ValueError,TypeError,KeyError,OverflowError):
                        pass  # Se devuelve el diagnóstico físico, no una exploración ciega.
            if s['op']=='go' and str(s.get('target','')).strip().lower() not in ('agua','orilla','costa','rio','río','lago'):
                try:s['x']=int(s['x']);s['y']=int(s['y'])
                except (ValueError,KeyError,TypeError):continue
            if s['op'] in ('rest','wait') and (s['op']=='wait' or not legacy_rest):
                from bodily_policy import rest_minutes
                minutes=rest_minutes(s)
                if minutes is None:continue
                s['minutes']=minutes
            if "prediction" in s:
                prediction=normalize_prediction(s.get("prediction"))
                if prediction is None or s["op"] not in {"experiment","use","rest","craft","build","assemble","modify","combine","excavate"}:
                    s.pop("prediction",None)
                else:s["prediction"]=prediction
            plan.append(s)
    action=str(raw.get('accion_proyecto','nuevo')).lower()
    if action not in ('nuevo','continuar','completar','abandonar','pausar','sin_proyecto'):action='nuevo'
    if not plan and action not in ('completar','abandonar','pausar'):
        raise ValueError('El modelo no propuso acciones utilizables.')
    note=str(raw.get('cuaderno','')).strip()[:500]
    if not note:raise ValueError('El modelo no redactó una nota.')
    try:advance=int(raw.get('avance_estimado',0))
    except (ValueError,TypeError):advance=0
    try:review=int(raw.get('revisar_en_minutos',90))
    except (ValueError,TypeError):review=90
    subgoals=raw.get('subobjetivos',[])
    if not isinstance(subgoals,list):subgoals=[]
    subgoals=[str(q).strip()[:110] for q in subgoals[:6] if isinstance(q,str) and q.strip()]
    return {"subobjetivos":subgoals,"cuaderno":note,"pregunta":str(raw.get('pregunta','')).strip()[:220],"hipotesis":str(raw.get('hipotesis','')).strip()[:240],
            "objetivo":str(raw.get('objetivo','')).strip()[:240],"motivo":str(raw.get('motivo','')).strip()[:200],"plan":plan,
            "revisar_en_minutos":max(30,min(240,review)),"proyecto_id":str(raw.get('proyecto_id','')).strip()[:50],
            "actividades_en_espera":raw.get("actividades_en_espera") if isinstance(raw.get("actividades_en_espera"),list) else None,
            "agenda":raw.get("agenda",[]) if isinstance(raw.get("agenda"),list) else [],
            "accion_proyecto":action,"prueba_cierre":str(raw.get('prueba_cierre','')).strip()[:220],"avance_estimado":max(0,min(100,advance)),"estado_actual":str(raw.get('estado_actual','')).strip()[:240]}


def request_chat(cfg,context,messages,system_instruction=None):
    from cognitive_projection import project_context
    context=project_context(context)
    system_instruction=system_instruction or CHAT_SYSTEM
    """Conversación anclada en memoria, sin capacidad de mutar el mundo."""
    provider=cfg.get('PROVIDER','gemini')
    model=cfg.get('MODEL','gemini-3.1-flash-lite')
    history=[{'role':v['role'],'text':v['text'][:1200]} for v in messages[-10:] if v.get('role') in ('user','assistant')]
    if provider=='groq' or cfg.get('_compact_context'):
        # Resumir contexto regular; conservar las entradas pendientes para preguntas
        # «qué me perdí», en lotes gestionados por el motor.
        keep={k:v for k,v in context.items() if k in ('momento','posición','necesidades','proyecto_actual',
               'unread_summary','pending','pendientes','resumen_pendientes','resumen_de_lo_no_leido','instruccion_de_resumen','regla','ultimo_resumen')}
        if len(json.dumps(keep,ensure_ascii=False,default=str))<350:
            keep.update({k:v for k,v in list(context.items())[:8]})
        context=keep
        history=history[-4:]
        history=[dict(m,text=m['text'][:550]) for m in history]
    grounded='CONTEXTO COMPROBADO (no lo contradigas): '+json.dumps(context,ensure_ascii=False,default=str)
    if provider=='gemini':
        url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        while history and history[0]['role']!='user':history.pop(0)
        contents=[]
        for i,m in enumerate(history):
            role='model' if m['role']=='assistant' else 'user'
            msg=(grounded+'\n\n' if i==0 else '')+m['text']
            if contents and contents[-1]['role']==role:
                contents[-1]['parts'][0]['text']+='\n'+msg
            else:
                contents.append({'role':role,'parts':[{'text':msg}]})
        payload={'systemInstruction':{'parts':[{'text':system_instruction}]},'contents':contents,'generationConfig':{'temperature':0.75,'maxOutputTokens':450}}
        headers={'x-goog-api-key':cfg['GEMINI_API_KEY'],'Content-Type':'application/json'}
    elif provider in ('openai_compatible','groq'):
        base=('https://api.groq.com/openai/v1' if provider=='groq' else cfg.get('OPENAI_BASE_URL','https://api.openai.com/v1')).rstrip('/')
        if not base.startswith('https://') and not base.startswith('http://127.0.0.1') and not base.startswith('http://localhost'):
            raise ValueError('La API debe usar HTTPS, salvo el servidor local.')
        url=base+'/chat/completions'
        msgs=[{'role':'system','content':system_instruction+'\n'+grounded}]+[{'role':h['role'],'content':h['text']} for h in history]
        payload={'model':model,'messages':msgs,'temperature':.75,'max_completion_tokens':450 if provider=='groq' else 650}
        if provider=='groq':payload['reasoning_effort']='low'
        headers={'Authorization':'Bearer '+(cfg['GROQ_API_KEY'] if provider=='groq' else cfg['OPENAI_API_KEY']),'Content-Type':'application/json'}
        if provider=='groq':headers['User-Agent']='Mozilla/5.0 (compatible; Nilo/0.3; API client)'
    else:raise ValueError('Proveedor desconocido')
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers=headers,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=40) as reply:result=json.load(reply)
    except urllib.error.HTTPError as exc:
        raise error_from_http(exc,provider) from None
    if provider=='gemini':
        txt=''.join(part.get('text','') for c in result.get('candidates',[])[:1] for part in c.get('content',{}).get('parts',[]))
        u=result.get('usageMetadata',{});tokens={'entrada':u.get('promptTokenCount',0),'salida':u.get('candidatesTokenCount',0)}
    else:
        txt=result['choices'][0]['message'].get('content','')
        u=result.get('usage',{});tokens={'entrada':u.get('prompt_tokens',0),'salida':u.get('completion_tokens',0)}
    if not txt.strip():raise RuntimeError('El modelo no respondió al chat.')
    return txt.strip()[:2000],tokens


def demo_decision(w,p):
    """Demostración sin IA: alterna observación, exploración y pruebas accesibles.
    No fija una misión inicial ni prioriza piedra o madera.
    """
    r=random.Random(int(p['clock_minutes'])+w['seed'])
    visible=world_view(w,p)
    resources={'arboleda':'madera','arenal':'arcilla','hierba':'fibra',
               'afloramiento mineral':'mineral oscuro','ruinas antiguas':'piedra',
               'roca':'piedra','ventilación caliente':'cristal'}
    chosen=r.choice(visible) if visible else None
    plan=[{'op':'explore'}]
    if chosen:
        plan.append({'op':'inspect','target':chosen['tipo']})
        material=resources.get(chosen['tipo'])
        if material and r.random()<.5:
            plan.append({'op':'gather','target':material})
    else:
        plan.append({'op':'rest'})
    return {"cuaderno":"Quiero observar los lugares que todavía no conozco. (Demostración sin LLM.)",
            "pregunta":"¿Qué puedo encontrar en otro sector?",
            "hipotesis":"El entorno puede mostrar propiedades distintas a las que ya vi.",
            "objetivo":"Conocer el entorno y sus posibilidades.",
            "motivo":"Demostración técnica, sin deliberación de IA.",
            "plan":plan,"revisar_en_minutos":90,"proyecto_id":"",
            "accion_proyecto":"nuevo","avance_estimado":5,
            "estado_actual":"Observando el entorno"}
