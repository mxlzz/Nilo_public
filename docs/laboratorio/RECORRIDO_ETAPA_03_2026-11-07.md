# Nilo 0.7.1 — Laboratorio, etapa 03: Recorrido y ficha de episodio

**Fecha:** 2026-11-07 · **PR:** [#87 (borrador)](https://github.com/mxlzz/Nilo_public/pull/87), apilado sobre #86 y #85.  
**Estado:** implementado en rama; pruebas de GitHub Actions según estado del PR. No integrado en `main`.

## Qué se muestra

El historial tiene ahora dos modos que comparten **la misma partida seleccionada**:

- **Recorrido** (nuevo): una línea por deliberación conservada, acción independiente o consulta que no produjo decisión archivada. Seleccionar abre **ficha de episodio**.
- **Reproducción** (existente): checkpoints, datos originales y reejecución aislada del motor instalado. Permanece accesible desde su propio modo y desde la ficha para los momentos restaurables.

La **ficha** organiza el material en cuatro bloques legibles, siempre expandibles:

1. **Recibió:** intentos HTTP archivados, proveedor, estado y tamaño; enlace a la solicitud literal cuando la partida es exactamente la del visor LLM. No se reconstruye el prompt desde el estado actual.
2. **Decidió:** texto original de salida del LLM, si fue capturado desde etapa 02, y decisión normalizada por separado. El Cuaderno de Nilo se presenta como relato del personaje, no prueba causal de su deliberación.
3. **Ejecutó:** las acciones que **efectivamente llegaron a tener checkpoint** y que poseen vínculo exacto con el cuaderno del plan (o acción independiente sin atribución). No confundir intención con comienzo de ejecución.
4. **Quedó registrado:** notas, mediciones, diagnósticos y experiencias asociadas por IDs exactos. **Registrado no significa que el siguiente prompt haya incluido ese dato**.

La ficha informa explícitamente las ausencias: sin cuerpo HTTP, sin respuesta original, sin checkpoint o sin vínculo exacto. El texto se muestra literalmente y escapado para prevenir la ejecución de HTML incluido en una memoria o salida de modelo. Las relaciones temporales no verificadas se rotulan como tales.

## Qué no hace esta etapa

- No analiza ni modifica reglas físicas (eso corresponde al inspector contextual, etapa 04).
- No añade checks de exclusión, anotaciones humanas ni exportación de auditoría (etapa 06).
- No cambia selección de recuerdos, presupuesto, prompts, proveedores, planes ni autonomía.
- No reinterpreta un replay del motor como idéntico a una deliberación real.
- No recupera datos que nunca se registraron en una partida antigua.

## Fuentes y restricciones

**Código nuevo:** `nilo_runtime/labs/episode_view.py` construye catálogo y ficha en lectura local. `laboratorio_motor.py` sirve `/api/history/episodes` y `/api/history/episode?id=cp:…|hist:…|call:…`, con IDs estrictos; ninguna ruta desde el cliente. Para una partida subida mediante el selector local solo se consulta su copia aislada; no se toma información de la partida activa.

**Dependencias reutilizadas:** `historical_lab.catalog` y `select_event`, `nilo_runtime/labs/episode_links.inspect_episode`, `RequestTraceStore.response_for`, visor LLM literal.

**Vínculos explícitos**: `trace_call_id` → decisión/checkpoint → `_journal_id` → acción → `journal_id` en medición → `measurement_id` en diagnóstico/experiencia. Una acción que carece de esas pruebas sigue como actividad independiente y no se atribuye a la decisión más próxima.

La vista incorpora consultas HTTP no archivadas en el historial de decisiones como episodios separados. **Su posición cronológica en el reloj de la simulación puede no estar verificada**, y por eso se presentan aparte sin inventar una secuencia causal.

## Comprobaciones para aceptar la etapa

1. Decisión con HTTP válido, salida original, plan, acción y evidencia archivada: todos los enlaces por identificador exacto.
2. Consulta con error y reintento aceptado, pero sin decisión: visible como episodio incompleto.
3. Acción de agenda no atribuida al último LLM; decisión generada por simulación manual etiquetada separadamente.
4. Partida anterior o importada sin sidecar: no enlazar al visor de la partida activa, ni reconstruir HTTP.
5. Cuerpo/tamaño SHA falsificado: lectura de intento rechazada.
6. Navegación, filtros y reproducción histórica anterior siguen operativos; JS compila y entradas textuales no ejecutan HTML.
7. APIs solo en servidor del laboratorio, sin filtros de rutas arbitrarias; partida original consultada sin mutaciones.
8. Windows portátil contiene el nuevo módulo; CI verde.

**Siguiente etapa:** 04 — inspector de reglas físicas y condiciones **realmente evaluadas**, sin equiparar referencias estáticas del código a trazas de ejecución.
