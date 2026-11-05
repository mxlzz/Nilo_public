"""Contratos operativos de Nilo: referencia única de interfaz y comprobaciones.

La descripción visible y los chequeos mecánicos parten de este módulo.
No es una acción del mundo. No proporciona propiedades ocultas ni recetas.
El verificador solo declara anomalías cuando puede contrastar un invariante
con hechos del estado: una prueba fallida nunca demuestra por sí sola un bug.
"""
from __future__ import annotations
import re

ACTION_GUIDE = {"explore":"{\"op\":\"explore\"} sin parámetros recorre frontera desconocida como antes; opcional {\"direction\":\"north|south|east|west\"} orienta hacia ese sector desde tu posición, o {\"region\":{\"x\":23,\"y\":10}} favorece fronteras alrededor de un punto YA CONOCIDO (mismo nivel); con ambos, direction es relativa al anclaje region. Norte reduce Y, sur aumenta Y, este aumenta X y oeste reduce X. El motor solo recorre casillas reveladas y accesibles, sin atravesar ni revelar suelo desconocido anticipadamente. Si no existe frontera en el sector, informa bloqueo y NO elige silenciosamente el opuesto.","go":"{\"op\":\"go\",\"x\":10,\"y\":8} se mueve a un destino conocido. Para buscar agua: {\"op\":\"go\",\"target\":\"agua\"}; el motor elige la orilla conocida más cercana que pueda alcanzar a pie. Si las coordenadas elegidas corresponden a agua conocida, el motor busca una orilla del mismo cuerpo de agua: NO intenta caminar dentro del agua. Un fracaso de acceso NO implica arboledas, arena ni pasajes subterráneos; consultá el diagnóstico real.","inspect":"{\"op\":\"inspect\",\"target\":\"ID o nombre de construcción/herramienta/terreno\"} o {\"op\":\"inspect\",\"x\":17,\"y\":19}. Herramientas llevadas siempre disponibles; construcciones y terreno hasta 4 casillas y mismo nivel; fuera de alcance no equivale a desaparecido.","gather":"{\"op\":\"gather\",\"target\":\"piedra\"} recoge una muestra localizada. Nombres permitidos: piedra (roca o ruinas), madera (arboleda), mineral oscuro (afloramiento mineral), arcilla (arenal), fibra (hierba), cristal y hongo luminoso. Se admiten los nombres del terreno entre paréntesis como alias EXACTOS. Si la fuente está lejos, caminar hacia ella no cuenta como haber recogido el material; la extracción debe aparecer como resultado e incremento real del inventario. Un nombre ambiguo no puede recolectar un recurso arbitrario.","experiment":"{\"op\":\"experiment\",\"target\":\"material disponible\",\"method\":\"mojar\"} prueba muestra en inventario. Métodos: golpear, calentar, mojar, cargar, luz. Si ya existe resultado, no repetirlo.","combine":"{\"op\":\"combine\",\"materials\":[\"material A\",\"material B\"],\"method\":\"unir\"} combina materiales disponibles (unir, atar, apilar, mezclar, compactar, trenzar).","build":"{\"op\":\"build\",\"materials\":[\"material A\"],\"name\":\"estructura\",\"purpose\":\"función hipotética\"} construcción FIJA en la posición actual; admite \"geometry\":{\"shape\":\"macizo|hueco|plataforma\",\"size\":2}, limitado por materiales utilizados; puede incluir \"layout\":{\"width_m\":3,\"length_m\":4,\"height_m\":2,\"entrance\":\"S\",\"zones\":[\"dormir\",\"guardar\"]}, acotado físicamente por recursos. El plano ASCII se genera del objeto materializado (las zonas son usos previstos, nunca paredes inventadas).","modify":"{\"op\":\"modify\",\"item\":\"ID de la obra o herramienta\",\"mode\":\"add|replace|remove|repair\",\"component\":\"ID real de pieza a reemplazar/reparar/quitar\",\"materials\":[\"madera\"],\"layout\":{\"zones\":[\"dormir\",\"guardar\"],\"entrance\":\"S\"}}. Modifica físicamente un objeto existente. add agrega material real; replace quita un componente y aporta otro; remove retira pieza; repair requiere pieza desgastada y recurso de reparación. No hay mejoras gratuitas y una modificación NO verifica por sí sola su función.","dismantle":"{\"op\":\"dismantle\",\"item\":\"ID de obra o herramienta\",\"all\":true}; para parcial usar {\"all\":false,\"component\":\"ID\"}. Recuperación parcial dependiente de material y estado. No desmontar si bastaría una reforma.","craft":"{\"op\":\"craft\",\"materials\":[\"material A\"],\"name\":\"objeto portátil\",\"form\":\"recipiente\",\"purpose\":\"función hipotética\"} fabrica un objeto transportable con geometría comprobable. Formas: golpe, punta, filo, palanca, recipiente, simple. Puede usar \"geometry\":{\"shape\":\"macizo|hueco|plataforma\",\"size\":2}; volumen limitado por número de componentes.","use":"{\"op\":\"use\",\"item\":\"ID o nombre que llevo\",\"method\":\"contener\",\"target\":\"material disponible\"} prueba funcionamiento físico. Formas admiten métodos: golpe→golpear muestras; punta→excavar roca adyacente; filo→cortar árboles; palanca→mover roca; recipiente→contener muestra. Métodos adicionales basados en propiedades generales: llenar agua (orilla adyacente), flotar (prueba sin pasajero), navegar (flotación con pasajero y geometría). Con navegar exitoso puede usar go/explore sobre agua. Puede llevar x,y si selecciona roca adyacente.","excavate":"{\"op\":\"excavate\"} excava roca adyacente USANDO una herramienta de punta que llevo; no excava por sí sola. x,y opcionales para elegir roca adyacente.","descend":"al descender reconocés el portal; ascend puede usarse desde CUALQUIER lugar de la cueva si existe una ruta conocida de regreso. El motor recorre ese camino y sale a superficie. No hace falta buscar una casilla especial a ojo.","ascend":"al descender reconocés el portal; ascend puede usarse desde CUALQUIER lugar de la cueva si existe una ruta conocida de regreso. El motor recorre ese camino y sale a superficie. No hace falta buscar una casilla especial a ojo.","assemble":"{\"op\":\"assemble\",\"name\":\"mecanismo\",\"purpose\":\"uso\",\"design_id\":\"inv-...\",\"parts\":[{\"name\":\"eje\",\"material\":\"madera\",\"shape\":\"eje\"},{\"name\":\"rueda\",\"material\":\"madera\",\"shape\":\"rueda\"}],\"joints\":[{\"a\":0,\"b\":1,\"type\":\"articulada\"}]} construye un ensamblaje material de 2-10 piezas. Uniones: fija, articulada, deslizante, flexible. Formas: macizo, hueco, plataforma, cilindro, rueda, eje, lámina. Todas las piezas consumen materiales. Probar con use (item=nombre, method=resistir_carga/load o transmitir_movimiento/input_energy). Solo acredita capacidades comprobadas.","rest":"{\"op\":\"rest\"} descanso voluntario: podés indicar minutes (1–1440 minutos simulados, por defecto 30). Registra la energía y el entorno sin imponer investigación; la inactividad no equivale a descanso.","compare":"{\"op\":\"compare\",\"evidence_ids\":[\"med-...\",\"med-...\"],\"metric\":\"capacidad_util_agua\"} compara 2–6 ensayos físicos REALES del mismo método y variable; exige materiales, objetos o versiones diferentes. Es una comparación descriptiva, no prueba causalidad. Consultá las mediciones disponibles.","conclude":"{\"op\":\"conclude\",\"topic\":\"tema medido\",\"evidence_ids\":[\"med-...\"]} sintetiza hechos de ensayos existentes; para el descanso el motor exige comparación válida. Los IDs deben provenir de mediciones_reales_recientes. Nunca declara una ley nueva por su cuenta.","forage":"{\"op\":\"forage\"} busca una porción de alimento vegetal en árboles/hierba cercanos, agotable por ubicación.","drink":"{\"op\":\"drink\"} bebe de agua adyacente, sin asegurar potabilidad. Con \"item\":\"ID de recipiente\" bebe voluntariamente 0,18 unidades de agua almacenada (+27 hidratación), sin consumo automático.","eat":"{\"op\":\"eat\"} consume una unidad real de alimento inventariado.","design":"{\"op\":\"design\",\"name\":\"dispositivo\",\"purpose\":\"qué necesito\",\"principle\":\"principio causal\",\"components\":[{\"name\":\"pieza\",\"material\":\"madera\",\"function\":\"sostener\",\"connection\":\"unión\"}],\"procedure\":\"cómo lo haría\",\"prediction\":\"cómo comprobarlo\",\"expected_test\":\"método físico exacto de prueba\",\"requirements\":\"requisitos\"} DOCUMENTA una ficha técnica; NO fabrica. Para nueva versión usar design_id de ficha anterior.","propose":"{\"op\":\"propose\",\"phenomenon\":\"fenómeno ausente\",\"missing_capability\":\"qué no representa el motor\",\"rationale\":\"justificación\",\"experiment\":\"prueba que lo demostraría\",\"context\":\"para qué me serviría\"} solicita revisión externa. NO altera la física, ni requiere respuesta inmediata.","report_issue":"{\"op\":\"report_issue\",\"title\":\"síntoma específico\",\"expected\":\"resultado esperado y motivo\",\"observed\":\"resultado observado\",\"rationale\":\"por qué merece una revisión\",\"related_action\":\"go\",\"evidence_ids\":[\"act-...\"]} presenta un POSIBLE error del motor. Úsalo solo cuando haya resultados incompatibles o una limitación que necesite aclaración, no por cada experimento fallido. Las referencias deben ser IDs presentes en \"resultados_de_acciones\"; NO inventes IDs. No afirmes conocer código interno ni declares un bug como hecho."}
COMMON_RULES = "Antes de construir una obra nueva, revisá construcciones existentes: si querés mejorar una, usá modify sobre su ID, no crees una duplicada. La cuadrícula del mapa solo ubica lugares: cada obra puede tener planta y piezas internas propias.\n- build/craft/use pueden incluir \"design_id\":\"inv-...\" para asociar sus resultados VERIFICADOS a la ficha técnica.\nCuando un paso pruebe una HIPÓTESIS importante, agregá al MISMO paso \"prediction\":{\"hypothesis\":\"qué creés que pasa\",\"expected_effect\":\"qué efecto observás si se cumple\",\"metric\":\"capacidad_util_agua\",\"operator\":\"gte\",\"threshold\":70}. Operadores: gte, gt, lte, lt, eq. El campo metric debe nombrar la variable que deseás verificar; si el motor no la mide (por ejemplo \"particulas_retenidas_pct\"), registrará variable_no_medida, NO confirmará el objetivo. Si no podés proponer umbral físico honesto, escribí hypothesis y expected_effect solamente: quedará cualitativa, sin verificación. Es optativo; usalo en ensayos que tengan una pregunta genuina y no en tareas triviales. Un resultado positivo de \"contener agua\" nunca demuestra filtración de partículas ni potabilidad.\nEspecificá materiales verdaderos del inventario. Si vinculás design_id en craft, build o assemble, la ficha vigente debe describir la misma cantidad de unidades de cada material que realmente vas a consumir. Si proyectaste un poste y construís cuatro, documentá la nueva versión con cuatro piezas o construí sin vincular. Coincidir en materiales NO demuestra geometría, uniones ni desempeño. Una herramienta tiene límites físicos: crearla no prueba que sea eficaz."
# IDs de respaldo son opcionales, pero las asociaciones que no se puedan
# acreditar con registros reales se distinguen de las referencias explícitas.
ACTION_GUIDE['propose'] += (' Si disponés de intentos no evaluables reales, añadí '
    '"evidence_ids":["no-modelo-..."]; no inventes IDs ni conviertas un '
    'fallo físico en un fenómeno sin modelo.')
ACTION_GUIDE['report_issue'] += (' Referenciá resultados reales mediante '
    '"evidence_ids":["act-..."]. Una operación fallida semejante puede ser '
    'solo contexto: no prueba que haya un defecto.')

# Una capacidad nueva se expone con el mismo contrato genérico 'interact'.
# El método concreto se verifica contra el registro instalado al ejecutar.
ACTION_GUIDE['interact'] = (
    '{"op":"interact","method":"transferir","source":"ID A","destination":"ID B","quantity":0.4} '
    'transfiere contenido real entre recipientes cercanos. Métodos disponibles en capacidad contenidos v1: '
    'llenar/rellenar (destination o item, quantity opcional, requiere agua adyacente); '
    'transferir (source,destination,quantity); descargar (source,quantity; solo agua al entorno sin charco); '
    'beber (source,quantity opcional: 0,18 por defecto); '
    'guardar (destination,material,quantity entera; toma sólidos del inventario); '
    'retirar (source,quantity entera; devuelve sólidos al inventario). '
    'Nunca mezclar materiales diferentes, exceder capacidad ni inferir potabilidad. '
    'Los recipientes conservan geometría esquemática; consultar el resultado físico.'
)
ACTION_GUIDE['interact'] += (' Capacidad cargas_estructurales v1: ' 
    '{"op":"interact","method":"probar_carga","item":"obra-ID","material":"madera","quantity":2} ' 
    'ensaya temporalmente si una construcción soporta lotes reales de un material. ' 
    'depositar_carga y recuperar_carga trasladan lotes entre inventario y construcción ' 
    'sin crearlos; exigen obra fija cercana y cantidad entera. ' 
    'El límite estático depende de materiales, piezas, desgaste y geometría, NO del nombre; ' 
    'un ensayo informa el resultado, no acredita abrigo ni seguridad climática.')
# Espera elegida por Nilo: transcurre tiempo, sin efecto de descanso/sueño.
ACTION_GUIDE['wait'] = ('{"op":"wait","minutes":30} espera voluntariamente entre 1 y 1440 '
    'minutos simulados (30 por defecto), sin acción física ni ensayo de descanso. '
    'Continúan el metabolismo y la recuperación pasiva normal de la inactividad; '
    'NO fuerza una disminución de energía, ni equivale a dormir. '
    'Las tareas diferidas pueden activarse por el tiempo transcurrido.')
SUPPORTED_OPERATIONS = frozenset(ACTION_GUIDE)

# A cada contrato comprobable se le asocian condiciones o efectos observables.
# Para el resto se conserva su documentación y el estado 'sin_verificar'
# hasta contar con evidencia suficiente para una validación más específica.
VERIFIABLE = {
    'inspect': {'pre':'Objeto identificado, dentro del alcance y visible',
                'post':'Inspección exitosa, sin fabricar ni borrar objetos'},
    'gather': {'pre':'Material solicitado y fuente alcanzable',
               'post':'Si informa extracción exitosa, crece la cantidad del material solicitado'},
    'use': {'pre':'Herramienta existente a disposición y método soportado',
            'post':'No informa éxito físico si el objeto no está disponible'},
    'experiment': {'pre':'Muestra disponible y procedimiento representado',
                   'post':'Un ensayo nuevo representado registra observación; no necesariamente una magnitud'},
    'build': {'pre':'Materiales disponibles y ubicación libre según reglas',
              'post':'Una construcción exitosa agrega una obra fija u objeto portátil real'},
    'modify': {'pre':'Objeto identificado, pieza y recursos apropiados',
               'post':'Una modificación exitosa cambia la revisión del objeto'},
    'interact': {'pre':'Método instalado y objeto físico accesible; cantidad/capacidad válidas',
                 'post':'Un intercambio exitoso aporta magnitudes y balances antes/después'},
}
def instructions():
    lines=['Operaciones disponibles (usar SOLO estas):']
    lines.extend(f'- {op}: {detail}' for op,detail in ACTION_GUIDE.items())
    from capabilities import manifest
    lines.append('Capacidades físicas instaladas en esta versión:')
    for cap in manifest():
        lines.append(f"- {cap['id']} v{cap['version']}: métodos {', '.join(cap['methods'])}.")
    return '\n'.join(lines)+'\n'+COMMON_RULES

def summary():
    from capabilities import manifest
    return {'operaciones':list(ACTION_GUIDE),'capacidades_disponibles':manifest(),
            'regla':'Las condiciones y las consecuencias de cada operación se verifican contra hechos del motor. '
                    'Los rechazos normales no prueban errores; un fenómeno sin modelo permite proponer una ampliación.'}

def spec_for(op):
    return {'operacion':op,'descripcion':ACTION_GUIDE.get(op),
            'contrato':VERIFIABLE.get(op),
            'resultado':'conforme / uso_incorrecto / limitacion / posible_error / no_verificado'}

def _object(world,person,requested):
    target=str(requested or '').strip().casefold()
    if not target:return None
    for item in person.get('items',[])+world.get('structures',[]):
        if str(item.get('id','')).casefold()==target or str(item.get('name','')).casefold()==target:
            return item
    return None

def before(world,person,step):
    """Fotografía mínima antes de ejecutar; jamás incluye claves ni secretos."""
    op=step.get('op','')
    target=(step.get('item') or step.get('object') or step.get('target')) if op in ('use','modify') else (step.get('target') or step.get('item') or step.get('object'))
    item=_object(world,person,target)
    own=(item in person.get('items',[])) if item else False
    pos=list(person.get('pos',[0,0,0]))
    visible=False
    if item and own:visible=True
    elif item and len(item.get('pos',[]))==3:
        ox,oy,oz=item['pos']
        visible=(oz==pos[2] and max(abs(ox-pos[0]),abs(oy-pos[1]))<=4
            and (f'{ox},{oy},{oz}' in world.get('revealed',[]) or
                 (ox,oy)==tuple(pos[:2])))
    requested=str(target or '').strip().casefold()
    # Solo es una expectativa fuerte cuando el objetivo identifica inequívocamente
    # una ficha existente. Los terrenos se resuelven por sus propias reglas.
    expected_inspect=(op=='inspect' and visible)
    if op=='inspect' and not expected_inspect:
        try:
            if 'x' in step and 'y' in step:
                tx,ty=int(step['x']),int(step['y'])
            else:
                match=re.search(r'[(\\[]\\s*(\\d{1,2})\\s*[,;]\\s*(\\d{1,2})\\s*[)\\]]',requested)
                tx,ty=(int(match.group(1)),int(match.group(2))) if match else (None,None)
            if tx is not None and 0<=tx<37 and 0<=ty<21 and max(abs(tx-pos[0]),abs(ty-pos[1]))<=4:
                known=f'{tx},{ty},{pos[2]}' in world.get('revealed',[])
                building=any(tuple(obj.get('pos',[]))==(tx,ty,pos[2]) for obj in world.get('structures',[]))
                expected_inspect=bool(known or building)
        except (TypeError,ValueError,KeyError):
            pass
    inventory=dict(person.get('inventory',{}))
    object_revisions={str(i.get('id')):i.get('revision',1)
                      for i in world.get('structures',[])+person.get('items',[])}
    return {'op':op,'target':requested,'expected_inspect':expected_inspect,
            'inventory':inventory,'structures':len(world.get('structures',[])),
            'items':len(person.get('items',[])),'revisions':object_revisions,
            'knowledge':list(person.get('knowledge',{}).keys()),
            'object_id':item.get('id') if item else None,
            'object_available':bool(item and (own or visible)),
            'position':pos}

def classify(world,person,step,prior,result):
    """Resultado estructurado de la ejecución, derivado de hechos, no de prosa."""
    op=step.get('op','')
    status=getattr(result,'status',None)
    success=bool(getattr(result,'success',False))
    data={'operation':op,'status':'no_verificado','code':'sin_regla_especifica',
          'expected':None,'observed':None,'evidence_kind':'contract_v1'}
    def mark(kind,code,expected,observed):
        data.update(status=kind,code=code,expected=expected,observed=observed)
        return data
    if status=='precondition_failed':
        return mark('uso_incorrecto','precondicion_no_satisfecha',
                    'Objetos, materiales, cantidad, proximidad y capacidad físicamente disponibles',
                    'El método no se ejecutó por una condición inválida. No demuestra fallo físico del recipiente.')
    if status=='no_evaluable':
        record=person.get('unmodeled_attempts',[])
        latest=record[-1] if record else {}
        data.update({'scope':latest.get('scope'),
                     'requested_method':latest.get('requested_method'),
                     'missing_effect_or_metric':latest.get('missing_effect_or_metric'),
                     'known_available_measures':latest.get('known_available_measures',[]),
                     'evidence_id':latest.get('id'),
                     'interpretation_limits':latest.get('interpretation_limits')})
        return mark('limitacion','fisica_no_implementada',
                    'La operación solo evalúa fenómenos físicos representados',
                    'El motor ha señalado que la física de este fenómeno no está implementada.')
    if op not in VERIFIABLE:return data
    if op=='interact':
        if not success:
            return mark('no_verificado','interaccion_no_completada',
                        'Solo se ejecutan operaciones físicas viables',
                        'No hubo intercambio de materiales.')
        physical=getattr(result,'physical',None) or {}
        proof=physical.get('conditions') or {}
        amount=proof.get('quantity')
        if physical.get('kind')!='capability' or not isinstance(amount,(int,float)) or amount<=0:
            return mark('posible_error','intercambio_sin_evidencia',
                        'Toda transferencia exitosa requiere cantidad real registrada',
                        {'evidencia':physical})
        if proof.get('method')=='transferir':
            old=proof.get('before') or {}
            new=proof.get('after') or {}
            if (not all(k in old and k in new for k in ('source','destination')) or
                abs((old.get('source',0)+old.get('destination',0))-
                    (new.get('source',0)+new.get('destination',0)))>0.001):
                return mark('posible_error','transferencia_no_conservativa',
                            'Los balances del origen y destino deben conservar la suma',
                            {'antes':old,'despues':new})
        if proof.get('method')=='probar_carga':
            return mark('conforme','carga_estatica_ensayada',
                        'El ensayo informa si los materiales reales fueron soportados',
                        {'cantidad':amount,'soportado':proof.get('supported'),
                         'limite_medido':proof.get('limit'),'revision':proof.get('revision')})
        return mark('conforme','intercambio_verificado',
                    'La capacidad aporta un efecto físico medido',
                    {'cantidad':amount,'capacidad':proof.get('capability'),'version':proof.get('version')})
    if op=='inspect':
        if prior.get('expected_inspect'):
            return mark('conforme' if success else 'posible_error',
                'objeto_disponible' if success else 'inspeccion_contradictoria',
                'Un objeto registrado, visible y al alcance puede inspeccionarse',
                'Inspección exitosa' if success else 'El motor rechazó una inspección que cumple esas condiciones.')
        if not success:return mark('uso_incorrecto','objetivo_no_observable',
                'Un ID existente y visible, o un terreno observado dentro del alcance',
                'No se encontró el objetivo en las condiciones indicadas; no significa que haya desaparecido.')
    elif op=='gather':
        from world import gather_material
        requested=gather_material(step.get('target'))
        if requested is None:return mark('uso_incorrecto','material_desconocido',
            'Usar un material o un depósito admitido para gather','El objetivo no corresponde a un recurso admitido.')
        diff=person.get('inventory',{}).get(requested,0)-prior.get('inventory',{}).get(requested,0)
        unexpected={k:person.get('inventory',{}).get(k,0)-prior['inventory'].get(k,0)
                    for k in person.get('inventory',{}) if k!=requested
                    and person.get('inventory',{}).get(k,0)>prior['inventory'].get(k,0)}
        if success and (diff<=0 or unexpected):return mark('posible_error','recoleccion_inconsistente',
            f'Si gather informa extracción de {requested}, aumenta solo ese recurso',
            {'incremento_solicitado':diff,'otros_incrementos':unexpected})
        if success:return mark('conforme','extraccion_verificada',f'Incrementar {requested}',{'incremento':diff})
        return mark('uso_incorrecto','extraccion_no_completada',
            'Fuente alcanzable con recursos y extracción completada','La extracción no se completó.')
    elif op=='build':
        if success:
            changes=(len(world.get('structures',[]))-prior['structures'],
                     len(person.get('items',[]))-prior['items'])
            if max(changes)<=0:return mark('posible_error','construccion_sin_objeto',
                'Una fabricación exitosa incorpora un objeto material al mundo o inventario',
                {'obras_nuevas':changes[0],'objetos_nuevos':changes[1]})
            return mark('conforme','construccion_materializada','Crear una obra u objeto nuevo',changes)
        return mark('uso_incorrecto','construccion_rechazada',
            'Recursos y espacio físicamente disponibles','La construcción no cumplió alguna condición de ejecución.')
    elif op=='modify':
        if success:
            rid=prior.get('object_id')
            obj=_object(world,person,rid)
            old_rev=prior.get('revisions',{}).get(str(rid),1)
            if obj is not None and obj.get('revision',1)<=old_rev:
                return mark('posible_error','modificacion_sin_revision',
                    'Una modificación exitosa incrementa la revisión del objeto',
                    {'id':rid,'revision_anterior':old_rev,'revision_actual':obj.get('revision',1)})
            return mark('conforme','modificacion_registrada',
                'Una modificación material debe actualizar la versión del objeto',
                {'id':rid,'revision_actual':obj.get('revision') if obj else None})
        return mark('uso_incorrecto','modificacion_rechazada',
            'Objeto, componentes, proximidad y materiales adecuados',
            'La intervención no cumple las condiciones de modificación.')
    elif op=='use':
        if success and not prior.get('object_available'):
            return mark('posible_error','uso_sin_herramienta',
                'Una prueba real requiere una herramienta disponible','La operación informó éxito sin objeto accesible.')
        if not success and not prior.get('object_available'):
            return mark('uso_incorrecto','herramienta_no_disponible',
                'Herramienta identificable y al alcance','No hay objeto utilizable identificado.')
        return mark('conforme' if success else 'no_verificado',
                    'prueba_registrada' if success else 'resultado_fisico_negativo',
                    'El éxito depende de materiales, forma y condiciones',
                    'El resultado físico de esta prueba no demuestra por sí solo una anomalía.')
    elif op=='experiment':
        target=str(step.get('target','')).casefold()
        has_sample=any(q>0 and m in target for m,q in prior.get('inventory',{}).items())
        method=str(step.get('method') or 'golpear').casefold()
        represented=method in ('golpear','calentar','mojar','cargar','luz')
        if not has_sample:return mark('uso_incorrecto','muestra_ausente',
            'Disponer del material a ensayar','No había muestra en inventario.')
        if not represented:return mark('limitacion','metodo_sin_modelo',
            'Solo los métodos documentados tienen interpretación física',
            f'El método {method} no está representado.')
        return mark('conforme' if success else 'no_verificado',
                    'ensayo_registrado' if success else 'ensayo_sin_resultado',
                    'Registrar una observación del ensayo','La operación no fue necesariamente una comprobación numérica.')
    return data
