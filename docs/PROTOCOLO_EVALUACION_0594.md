# Protocolo de evaluación de corridas — Nilo 0.5.9.4

Este hito añade **instrumentación y análisis observacional**, no nuevos objetivos para Nilo. La herramienta `evaluar_corridas.py` lee bases SQLite **sin editarlas** y produce un informe JSON o Markdown. Un informe **no** es, por sí mismo, una demostración de mejora de autonomía.

## Fuentes verificables y cobertura

- **`engine_sessions`**: versión real, commit/manifiesto cuando existen, escenario, intervalos simulados, proveedor configurado. Desde **0.5.9.4** guarda además `world_seed`, **semilla RNG efectiva** y **SHA256 del estado inicial** (`world`, `person`, escenario y entorno). Las sesiones antiguas conservan **NULL**: no se rellenan retrospectivamente.
- **`session_model_usage` y `llm_decision`**: respuestas exitosas por proveedor/modelo, número de decisiones y huellas de contexto cuando están documentadas. No registramos credenciales ni pretendemos reproducir el pensamiento del LLM.
- **`history.measurement` y `history.diagnostic`**: operaciones, resultados verificables, medidas, éxitos/fallos, posible agotamiento de investigación, información de exploración. Desde .4 los resultados nuevos añaden `origin`, `project_id` y traza de exploración, cuando existen. Las acciones anteriores sin origen mantienen **desconocido**, nunca se etiquetan como LLM por defecto.
- **`behavior_metrics`**: acumuladores reales desde la instrumentación anterior. Pueden comenzar después del día 1: documentar cobertura. El archivo `history` sirve para contar acciones y mediciones conservadas más allá de las últimas ventanas activas.
- **Alcance actual**: la cuenta de acciones archivadas usa `diagnostic`, que no contiene todas las acciones documentales (`write`, `design`, `propose`): **no equivale a absolutamente todas las operaciones**. `behavior_metrics.actions` tiene cobertura distinta. La comparación es acumulada por partida, **no una tasa separada por versión** cuando hay sesiones mixtas.

## Uso básico

Con Nilo cerrado o con una copia respaldada de la base:

```bat
python evaluar_corridas.py "nilo_mundo_A.sqlite3" --json "evaluacion_A.json" --markdown "evaluacion_A.md"
python evaluar_corridas.py "nilo_mundo_A.sqlite3" "nilo_mundo_B.sqlite3" --json "comparacion.json" --markdown "comparacion.md"
```

Los informes se escriben a las rutas solicitadas; las bases solo se abren con SQLite **`mode=ro`** y `query_only`. Si la partida está abierta con WAL, usar un respaldo consistente de SQLite, no copiar solo el archivo principal mientras hay escrituras. No compartir datos de partidas privadas sin revisar el contenido exportado; el informe omite diarios, prompts, nombres de proyectos, textos de chat y contraseñas.

## Protocolo prospectivo para comparar cambios cognitivos

1. Conservar una **copia única de partida de origen** y **dos copias de trabajo distintas**, intactas hasta empezar. Registrar SHA256 del archivo de origen y estado inicial, escenario, posición, tiempo simulado, reservas y condiciones de suministro para el observador, pero **no pasarlas como objetivos al personaje**.
2. Fijar y documentar **versión del motor, commit/manifest**, proveedor/modelo real, configuración de temperatura y respuestas si el servicio las expone, semilla de mundo, **semilla RNG**, velocidad, horizonte simulado, límite de consultas y si hubo mensajes/intervenciones. Al comparar versiones, aislar **una diferencia técnica** por vez (p. ej., representación numérica frente a cualitativa), sin cambiar física y prompts simultáneamente. Las versiones históricas mixtas no son equivalentes a un A/B controlado.
3. Ejecutar sin misiones ni restricciones ficticias. Repetir por varias semillas/partidas con una ventana de tiempo comparable. Si hay una interrupción, importación, cambio de versión, desvío del proveedor o cambio humano, **registrar el tramo**, no ocultarlo bajo un promedio.
4. Analizar las bases con el comando anterior. Comparar **origen** de ingestas `drink/eat` o `rest` con reserva ≥90, **sin concluir que esos actos fueron errores**. Revisar deliberaciones elegidas, acciones rutinarias delegadas, descansos voluntarios, exploraciones orientadas (rumbo, distancia, descubrimientos, bloqueos), repetición de intentos y resultados de experimentos. Los contadores son descriptivos, no una puntuación de personalidad.
5. Revisar al menos casos concretos con IDs de `diagnostic`/`measurement`, y consultar los cuadernos como **explicación narrativa secundaria**, no como evidencia física. La presencia de `no_evaluable` no equivale a un fracaso de Nilo: puede ser una capacidad todavía no instalada.
6. No atribuir causalidad si cambian estado inicial, versiones intermedias, proveedor, respuestas, duración o intervenciones. Una misma semilla no garantiza deliberaciones idénticas con un LLM externo.

### Dos tipos de validación diferentes

- **Regresión determinista**, sin API: `python -m unittest discover -s tests -v`, `python validar_escenarios.py --seed 7321` y `python reproducir.py tests/fixtures/replay_basico.json`. Verifican reglas/huellas de una secuencia **ya decidida**; no miden autonomía espontánea.
- **Evaluación conductual real con LLM**: requiere corridas posteriores a .35 con condiciones y resultados documentados. `evaluar_corridas.py` entrega métricas, procedencia e indicadores de comparabilidad. **No hace llamadas a la API ni simula pensamiento.** La publicación .4 confirma la infraestructura, **no afirma aún que la percepción cualitativa o la navegación dirigida hayan mejorado la conducta**.

## Criterios de aceptación del hito de infraestructura

- Analiza un SQLite antiguo sin migraciones ni escritura y reconoce información ausente.
- Registra nueva semilla RNG + hash de estado inicial por sesión para evitar comparar partidas incompatibles.
- Separa origen `llm`, `rutina`, `agenda`, `espera` o `motor` si **efectivamente se registró**, y `desconocido` si no; mantiene reglas de replays antiguos.
- Mide necesidades físicas con datos del motor; explica reservas altas sin prescribir comportamiento.
- Diferencia actividades, pruebas comparables, huellas de decisiones, casos sin modelar, novedades y trazas dirigidas, sin forzar diversidad ni proyectos.
- Una comparación emite **condiciones individuales de correspondencia** y declara explícitamente que no hay prueba causal automática.
- Los runs antiguos, incluso si atraviesan versiones, no reciben etiquetas retrospectivas ni estadísticas fraudulentas por sesión.

**Próxima etapa:** recopilar y contrastar corridas reales con Nilo 0.5.9.4 y, con esa referencia, empezar 0.6 por capacidades físicas modulares e identificación progresiva. Relacionado con [#15](https://github.com/mxlzz/Nilo/issues/15), [#14](https://github.com/mxlzz/Nilo/issues/14), [#94](https://github.com/mxlzz/Nilo/issues/94).
