"""Registro contractual único de operaciones v0.7 (sin dependencias del mundo).

Este es el único origen del nombre de una acción, descripción comunicada al LLM,
duración estimada, esquema mínimo y ruta hacia su ejecutor. Las condiciones
materiales siguen siendo responsabilidad del entorno/handler: no inferir efectos
de la intención ni de este documento.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any

# Descripciones, reglas y contratos EXACTOS del baseline para no alterar prompts.
ACTION_GUIDE = {"explore":"{\"op\":\"explore\"} sin parámetros recorre frontera desconocida como antes; opcional {\"direction\":\"north|south|east|west\"} orienta hacia ese sector desde tu posición, o {\"region\":{\"x\":23,\"y\":10}} favorece fronteras alrededor de un punto YA CONOCIDO (mismo nivel); con ambos, direction es relativa al anclaje region. Norte reduce Y, sur aumenta Y, este aumenta X y oeste reduce X. El motor solo recorre casillas reveladas y accesibles, sin atravesar ni revelar suelo desconocido anticipadamente. Si no existe frontera en el sector, informa bloqueo y NO elige silenciosamente el opuesto.","go":"{\"op\":\"go\",\"x\":10,\"y\":8} se mueve a un destino conocido. Para buscar agua: {\"op\":\"go\",\"target\":\"agua\"}; el motor elige la orilla conocida más cercana que pueda alcanzar a pie. Si las coordenadas elegidas corresponden a agua conocida, el motor busca una orilla del mismo cuerpo de agua: NO intenta caminar dentro del agua. Un fracaso de acceso NO implica arboledas, arena ni pasajes subterráneos; consultá el diagnóstico real.","inspect":"{\"op\":\"inspect\",\"target\":\"ID o nombre de construcción/herramienta/terreno\"} o {\"op\":\"inspect\",\"x\":17,\"y\":19}. Herramientas llevadas siempre disponibles; construcciones y terreno hasta 4 casillas y mismo nivel; fuera de alcance no equivale a desaparecido.","gather":"{\"op\":\"gather\",\"target\":\"piedra\"} recoge una muestra localizada. Nombres permitidos: piedra (roca o ruinas), madera (arboleda), mineral oscuro (afloramiento mineral), arcilla (arenal), fibra (hierba), cristal y hongo luminoso. Se admiten los nombres del terreno entre paréntesis como alias EXACTOS. Si la fuente está lejos, caminar hacia ella no cuenta como haber recogido el material; la extracción debe aparecer como resultado e incremento real del inventario. Un nombre ambiguo no puede recolectar un recurso arbitrario.","experiment":"{\"op\":\"experiment\",\"target\":\"material disponible\",\"method\":\"mojar\"} prueba muestra en inventario. Métodos: golpear, calentar, mojar, cargar, luz. Si ya existe resultado, no repetirlo.","combine":"{\"op\":\"combine\",\"materials\":[\"material A\",\"material B\"],\"method\":\"unir\"} combina materiales disponibles (unir, atar, apilar, mezclar, compactar, trenzar).","build":"{\"op\":\"build\",\"materials\":[\"material A\"],\"name\":\"estructura\",\"purpose\":\"función hipotética\"} construcción FIJA en la posición actual; admite \"geometry\":{\"shape\":\"macizo|hueco|plataforma\",\"size\":2}, limitado por materiales utilizados; puede incluir \"layout\":{\"width_m\":3,\"length_m\":4,\"height_m\":2,\"entrance\":\"S\",\"zones\":[\"dormir\",\"guardar\"]}, acotado físicamente por recursos. El plano ASCII se genera del objeto materializado (las zonas son usos previstos, nunca paredes inventadas).","modify":"{\"op\":\"modify\",\"item\":\"ID de la obra o herramienta\",\"mode\":\"add|replace|remove|repair\",\"component\":\"ID real de pieza a reemplazar/reparar/quitar\",\"materials\":[\"madera\"],\"layout\":{\"zones\":[\"dormir\",\"guardar\"],\"entrance\":\"S\"}}. Modifica físicamente un objeto existente. add agrega material real; replace quita un componente y aporta otro; remove retira pieza; repair requiere pieza desgastada y recurso de reparación. No hay mejoras gratuitas y una modificación NO verifica por sí sola su función.","dismantle":"{\"op\":\"dismantle\",\"item\":\"ID de obra o herramienta\",\"all\":true}; para parcial usar {\"all\":false,\"component\":\"ID\"}. Recuperación parcial dependiente de material y estado. No desmontar si bastaría una reforma.","craft":"{\"op\":\"craft\",\"materials\":[\"material A\"],\"name\":\"objeto portátil\",\"form\":\"recipiente\",\"purpose\":\"función hipotética\"} fabrica un objeto transportable con geometría comprobable. Formas: golpe, punta, filo, palanca, recipiente, simple. Puede usar \"geometry\":{\"shape\":\"macizo|hueco|plataforma\",\"size\":2}; volumen limitado por número de componentes.","use":"{\"op\":\"use\",\"item\":\"ID o nombre que llevo\",\"method\":\"contener\",\"target\":\"material disponible\"} prueba funcionamiento físico. Formas admiten métodos: golpe→golpear muestras; punta→excavar roca adyacente; filo→cortar árboles; palanca→mover roca; recipiente→contener muestra. Métodos adicionales basados en propiedades generales: llenar agua (orilla adyacente), flotar (prueba sin pasajero), navegar (flotación con pasajero y geometría). Con navegar exitoso puede usar go/explore sobre agua. Puede llevar x,y si selecciona roca adyacente.","excavate":"{\"op\":\"excavate\"} excava roca adyacente USANDO una herramienta de punta que llevo; no excava por sí sola. x,y opcionales para elegir roca adyacente.","descend":"{\"op\":\"descend\"} desciende desde la superficie solo si la entrada conocida de la cueva está accesible (a distancia de una casilla). No crea conexiones ni permite entrar desde lejos: antes debo llegar a la entrada. Si no estoy junto a ella, el motor informa que no hay conexión accesible.","ascend":"al descender reconocés el portal; ascend puede usarse desde CUALQUIER lugar de la cueva si existe una ruta conocida de regreso. El motor recorre ese camino y sale a superficie. No hace falta buscar una casilla especial a ojo.","assemble":"{\"op\":\"assemble\",\"name\":\"mecanismo\",\"purpose\":\"uso\",\"design_id\":\"inv-...\",\"parts\":[{\"name\":\"eje\",\"material\":\"madera\",\"shape\":\"eje\"},{\"name\":\"rueda\",\"material\":\"madera\",\"shape\":\"rueda\"}],\"joints\":[{\"a\":0,\"b\":1,\"type\":\"articulada\"}]} construye un ensamblaje material de 2-10 piezas. Uniones: fija, articulada, deslizante, flexible. Formas: macizo, hueco, plataforma, cilindro, rueda, eje, lámina. Todas las piezas consumen materiales. Probar con use (item=nombre, method=resistir_carga/load o transmitir_movimiento/input_energy). Solo acredita capacidades comprobadas.","rest":"{\"op\":\"rest\"} descanso voluntario: podés indicar minutes (1–1440 minutos simulados, por defecto 30). Registra la energía y el entorno sin imponer investigación; la inactividad no equivale a descanso.","compare":"{\"op\":\"compare\",\"evidence_ids\":[\"med-...\",\"med-...\"],\"metric\":\"capacidad_util_agua\"} compara 2–6 ensayos físicos REALES del mismo método y variable; exige materiales, objetos o versiones diferentes. Es una comparación descriptiva, no prueba causalidad. Consultá las mediciones disponibles.","conclude":"{\"op\":\"conclude\",\"topic\":\"tema medido\",\"evidence_ids\":[\"med-...\"]} sintetiza hechos de ensayos existentes; para el descanso el motor exige comparación válida. Los IDs deben provenir de mediciones_reales_recientes. Nunca declara una ley nueva por su cuenta.","forage":"{\"op\":\"forage\"} busca una porción de alimento vegetal en árboles/hierba cercanos, agotable por ubicación.","drink":"{\"op\":\"drink\"} bebe de agua adyacente, sin asegurar potabilidad. Con \"item\":\"ID de recipiente\" bebe voluntariamente 0,18 unidades de agua almacenada; la recuperación corporal se expresa mediante sensaciones, sin consumo automático.","eat":"{\"op\":\"eat\"} consume una unidad real de alimento inventariado.","design":"{\"op\":\"design\",\"name\":\"dispositivo\",\"purpose\":\"qué necesito\",\"principle\":\"principio causal\",\"components\":[{\"name\":\"pieza\",\"material\":\"madera\",\"function\":\"sostener\",\"connection\":\"unión\"}],\"procedure\":\"cómo lo haría\",\"prediction\":\"cómo comprobarlo\",\"expected_test\":\"método físico exacto de prueba\",\"requirements\":\"requisitos\"} DOCUMENTA una ficha técnica; NO fabrica. Para nueva versión usar design_id de ficha anterior.","propose":"{\"op\":\"propose\",\"phenomenon\":\"fenómeno ausente\",\"missing_capability\":\"qué no representa el motor\",\"rationale\":\"justificación\",\"experiment\":\"prueba que lo demostraría\",\"context\":\"para qué me serviría\"} solicita revisión externa. NO altera la física, ni requiere respuesta inmediata.","report_issue":"{\"op\":\"report_issue\",\"title\":\"síntoma específico\",\"expected\":\"resultado esperado y motivo\",\"observed\":\"resultado observado\",\"rationale\":\"por qué merece una revisión\",\"related_action\":\"go\",\"evidence_ids\":[\"act-...\"]} presenta un POSIBLE error del motor. Úsalo solo cuando haya resultados incompatibles o una limitación que necesite aclaración, no por cada experimento fallido. Las referencias deben ser IDs presentes en \"resultados_de_acciones\"; NO inventes IDs. No afirmes conocer código interno ni declares un bug como hecho."}
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
    'Continúa el metabolismo, pero wait no recupera energía como descanso; '
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

# Tabla de duraciones estimadas, antes duplicada en nilo.py.
ACTION_DURATIONS={'explore':22,'go':19,'inspect':9,'gather':20,'experiment':32,'combine':48,'build':90,'craft':60,'use':27,'excavate':50,'descend':16,'ascend':16,'rest':30,'wait':30,'forage':18,'drink':8,'eat':12,'design':26,'propose':28,'assemble':70,'modify':50,'dismantle':45,'report_issue':24,'conclude':12,'compare':15,'interact':18}

# Los ejecutores documentales son los únicos que no delegan al entorno físico.
DOCUMENT_EXECUTORS = {
    "design": "design",
    "propose": "propose",
    "report_issue": "report_issue",
    "compare": "compare",
    "conclude": "conclude",
}
NAVIGATION_OPERATIONS = frozenset(("go", "explore", "gather", "ascend"))
# Campos imprescindibles para que el motor pueda interpretar la intención.
# No constituyen prueba de disponibilidad física. Los errores por material,
# alcance, geometría, etc. continúan perteneciendo al entorno.
REQUIRED_FIELDS = {
    "gather": ("target",),
    "interact": ("method",),
    "use": ("item",),
    "compare": ("evidence_ids",),
}
# Los formatos permitidos no impiden que el handler rechace una operación.
FIELD_TYPES = {
    "materials": (list,),
    "parts": (list,),
    "joints": (list,),
    "components": (list,),
    "evidence_ids": (list,),
    "prediction": (dict,),
    "geometry": (dict,),
    "layout": (dict,),
    "region": (dict,),
    "x": (int,),
    "y": (int,),
}


@dataclass(frozen=True)
class OperationSpec:
    name: str
    description: str
    planned_minutes: int
    executor: str
    navigable: bool
    required_fields: tuple[str, ...]
    verified_preconditions: str | None
    verified_postconditions: str | None

    def to_record(self) -> dict[str, Any]:
        return {
            "op": self.name,
            "description": self.description,
            "planned_minutes": self.planned_minutes,
            "executor": self.executor,
            "navigable": self.navigable,
            "required_fields": list(self.required_fields),
            "verified_preconditions": self.verified_preconditions,
            "verified_postconditions": self.verified_postconditions,
        }


if set(ACTION_GUIDE) != set(ACTION_DURATIONS):
    raise RuntimeError(
        "Catálogo incoherente: manual y duración deben definir las mismas acciones "
        f"(solo guía: {sorted(set(ACTION_GUIDE)-set(ACTION_DURATIONS))}; "
        f"solo duraciones: {sorted(set(ACTION_DURATIONS)-set(ACTION_GUIDE))})"
    )
if not set(VERIFIABLE).issubset(ACTION_GUIDE):
    raise RuntimeError("Un contrato verifica una operación que no existe")
if not set(DOCUMENT_EXECUTORS).issubset(ACTION_GUIDE):
    raise RuntimeError("Ejecutor documental sin operación registrada")

_REGISTRY = MappingProxyType({
    op: OperationSpec(
        name=op,
        description=description,
        planned_minutes=ACTION_DURATIONS[op],
        executor=DOCUMENT_EXECUTORS.get(op, "physical"),
        navigable=op in NAVIGATION_OPERATIONS,
        required_fields=REQUIRED_FIELDS.get(op, ()),
        verified_preconditions=VERIFIABLE.get(op, {}).get("pre"),
        verified_postconditions=VERIFIABLE.get(op, {}).get("post"),
    )
    for op, description in ACTION_GUIDE.items()
})


def registered_operations() -> Mapping[str, OperationSpec]:
    """Registro inmutable de las operaciones conocidas."""
    return _REGISTRY


def get_spec(op: str) -> OperationSpec:
    if not isinstance(op, str) or op.lower() not in _REGISTRY:
        raise ValueError(f"Operación desconocida: {op!r}")
    return _REGISTRY[op.lower()]


@dataclass(frozen=True)
class OperationValidation:
    valid: bool
    code: str
    reason: str
    operation: str | None


def validate_operation(step: Any, *, check_required: bool = False) -> OperationValidation:
    """Precondiciones de forma únicamente, sin consultar materiales ni mundo.

    La compatibilidad con partidas viejas permite omitir campos esenciales;
    `check_required=True` se usa al diseñar acciones nuevas, no para
    reescribir resultados físicos ni planes anteriores.
    """
    if not isinstance(step, dict):
        return OperationValidation(False, "invalid_type",
                                   "Una acción debe ser un objeto JSON.", None)
    raw=step.get("op")
    if not isinstance(raw, str):
        return OperationValidation(False, "missing_operation",
                                   "Falta el nombre de la operación.", None)
    op=raw.lower()
    if op not in _REGISTRY:
        return OperationValidation(False, "unknown_operation",
                                   "La operación no pertenece al catálogo instalado.", op)
    for key, types in FIELD_TYPES.items():
        if key not in step:
            continue
        value=step[key]
        # design.documentación usa "prediction" textual: el mismo campo
        # describe una hipótesis narrativa, no una predicción medible.
        if key == "prediction" and op == "design" and isinstance(value, str):
            continue
        if key in ("x","y"):
            # Alias numéricos de las decisiones LLM se normalizan en brain.
            # Aquí rechazamos booleanos, que son int en Python.
            if type(value) in (int, str) and str(value).lstrip("-").isdigit():
                continue
            return OperationValidation(False, "invalid_field_type",
                                       f"{key} debe ser una coordenada entera.", op)
        if not isinstance(value, types):
            return OperationValidation(False, "invalid_field_type",
                                       f"{key} debe ser de tipo {types[0].__name__}.", op)
    if check_required:
        for key in _REGISTRY[op].required_fields:
            if not step.get(key):
                return OperationValidation(False, "missing_parameter",
                                           f"Falta {key} para {op}.", op)
    return OperationValidation(True, "valid", "", op)


def manual_lines() -> list[str]:
    """La documentación LLM usa el MISMO orden y texto del registro tipado."""
    return [f"- {spec.name}: {spec.description}"
            for spec in _REGISTRY.values()]
