# Nilo 0.7.1 · Visor LLM — Etapa 04: procedencia y transformaciones

**Fecha:** 2026-11-06. **Rama:** `work/0.7.1-visor-contexto-llm`. **Estado:** implementación pendiente de CI. **Versión estable:** `v0.7.0`.

## Objetivo y límite de precisión

Para cada campo JSON del mensaje que Nilo recibe, necesitamos poder explicar de qué archivo/función se calcula y qué transformaciones ocurrieron antes de enviarlo, sin deducir información inexistente ni modificar la solicitud.

**Dos tipos de evidencia, obligatoriamente separados:**

1. **Transición observada en tiempo de ejecución:** presencia y cambios efectivos de campos y subcampos JSON entre etapas del constructor real. Un campo puede permanecer, aparecer, cambiar de valor o desaparecer. Esto es una observación efectiva.
2. **Referencia verificable en el código:** archivo, función, línea, extracto de expresión y SHA256 del código fuente local del lugar donde se declara/asigna el campo. Se extrae mediante AST del código; **no prueba por sí sola cuál rama condicional se ejecutó ni atribuye un único origen si hay varios candidatos**.

Los subcampos (por ejemplo `/proyecto_actual/status`) heredan el origen del campo padre, con precisión explícita `heredada_del_campo_raiz_no_exacta`. No se presenta esa referencia como una asignación granular que no esté realmente instrumentada. Las claves sin referencias verificadas se etiquetan como `origen_no_instrumentado`.

## Componentes implementados

- `nilo_runtime/agent/provenance.py`: inventario AST de las expresiones de `brain.context_for`, los contextos agregados en `DecisionUseCases.think` y `start_chat`, asignaciones de `cognitive_projection.project_context` y campos añadidos por `compact_context` / `bounded_context`. Devuelve referencias a código y digest del archivo. **No aplica reglas físicas ni recorre código fuente de forma ejecutable.**
- `nilo_runtime/agent/trace_context.py`: `observe_context(stage,context)` copia temporalmente los objetos en la memoria del worker, solo cuando hay un `capture_call` real. Al elegir un nuevo proveedor en fallback, borra las instantáneas anteriores. La ejecución del LLM no depende de la telemetría.
- `nilo_runtime/agent/gateway.py`: puntos de observación **después** de cada transformación vigente, reutilizando las funciones del motor, sin implementar un segundo constructor ni alterar sus parámetros/resultado: `percepcion` → `proyeccion` → `perfil` → `compactacion` → `presupuesto` → (Groq: `limite_proveedor`) → `solicitud_preparada`. En chat: `percepcion` → `proyeccion` → `filtro_chat` → `solicitud_preparada`.
- `nilo_runtime/storage/llm_requests.py`: tabla SQLite **aditiva** `llm_request_provenance`, vinculada por `attempt_id` a `llm_requests` de etapa 02; los metadatos se guardan en la misma transacción que los bytes exactos. El borrado FIFO de intentos purga también la procedencia; bases anteriores sin tabla siguen siendo legibles.

## Datos guardados (y datos que deliberadamente NO se guardan)

Se persisten: lista y orden de etapas, rutas JSON Pointer, operaciones entre etapas (`added`, `removed`, `modified`), presencia al final, tipos JSON, referencias de origen, digest de archivos, fuentes de los roles (`SYSTEM`, `GROQ_SYSTEM`, `CHAT_SYSTEM`, contratos y chat) y verificación de coincidencia con el cuerpo HTTP.

**No se persisten los valores de las etapas intermedias, reservas fisiológicas ocultas, textos originales de campos omitidos, hashes reversibles de esos valores ni contextos reconstruidos**. El texto que efectivamente se preparó para el LLM sigue almacenado únicamente en el BLOB original de etapa 02, sin cambios.

El motor puede manejar listas que se reordenan/truncan. La comparación usa **rutas posicionales**, no identidad de entidades: un cambio de `/memorias_relevantes/0` significa que cambió el valor en ese índice, no demuestra qué objeto fue eliminado o reemplazado. Las operaciones de un campo padre pueden reflejar cambios de sus hijos.

No se registra una “causa” más precisa que el **módulo responsable y el límite de etapa observado**, salvo cuando existe una referencia de código específica comprobable. Un `removed` durante `compactacion` no prueba por sí solo qué heurística interna lo eliminó. Para ese diagnóstico se consulta la implementación, evitando inventar razonamientos del LLM.

## Comprobación de exposición al modelo

Antes de registrar que un campo está en el payload, `build_metadata` extrae el JSON de contexto del **mismo BLOB HTTP de etapa 02** y lo compara con `solicitud_preparada`. Distinguimos:

- `verificado_con_payload_http`: los valores concuerdan con el contexto que el gateway preparó, para ese intento concreto. Esto **no implica que la API lo haya recibido o respondido**, que corresponde al estado de transporte.
- `no_verificado_con_el_payload`: si no coincide, los campos guardan `in_http_payload=null`. No declarar algo enviado a partir de un snapshot divergente.

La procedencia tiene un **límite de 400 kB por intento**. Si se excede, se almacena explícitamente `trace_status=excede_limite` y la captura del cuerpo HTTP continúa completa; no se expone una traza parcial como si fuera exhaustiva.

Las instantáneas efímeras se descartan al salir de `capture_call`, y los fallos del observador son de mejor esfuerzo, sin interrumpir a Nilo. La captura solo se activa en solicitudes reales, no en vistas previas.

## Verificaciones y compatibilidad

`tests/test_visor_llm_04.py` cubre (con red simulada, sin APIs reales ni datos privados):

- Dato corporal legado numérico que se transforma antes de llegar al LLM: se registra el cambio de rutas, **no su valor original**.
- Omisión por perfil y por compactación en etapas distintas, comparando el BLOB HTTP final.
- Orígenes por AST de `necesidades`, `proyecto_actual`, `conversaciones_recientes`, `antecedente_relevante` y `contexto_reducido` con SHA256 comprobable.
- Presupuesto final Groq y fallback Gemini→Groq con trazas separadas, sin contaminar candidatos.
- Chat con filtro/roles y mensaje humano correlacionado.
- Migración aditiva de sidecars existentes, retención FIFO sin metadatos huérfanos e integridad en lectura.
- Rechazo de atribución al payload si el snapshot no coincide, y distinción posicional en arrays.

**No hay API pública ni interfaz nueva.** La etapa 05 expondrá lectura local de registros y procedencia, uniendo estos datos con `literal_segments.index_saved_attempt`. La etapa 06 presentará la misma información en vista simple y profesional, con subtítulos no enviados al LLM.

**Límite histórico:** la procedencia no puede reconstruirse para intentos anteriores a esta etapa si la sidecar solo tiene cuerpo HTTP; puede segmentarse el contenido literal, pero no afirmar qué etapas se ejecutaron.
