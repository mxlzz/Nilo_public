# Nilo 0.7.1 · Etapa 11 — protocolo A/B y paquete de evaluación

**Fecha:** 08/11/2026  
**Rama:** `work/0.7.1-lab-stage11-evaluation` (basada en la etapa 10, PR #94).  
**Estado al crear:** implementación y tests nuevos listos para CI; **validación humana de comportamiento pendiente**.

## Objetivo

El laboratorio debe poder demostrar, con evidencia reproducible, qué cambia al sustituir el contexto actual de Nilo por la variante modular de la etapa 10. No se presupone que una solicitud más breve produzca una decisión mejor. La métrica primaria de la fase offline es integridad y comparación del *cuerpo exacto de solicitud*, no una supuesta eficiencia cognitiva.

## 1. Auditoría del instrumental existente

El laboratorio ya contaba con:
- `context_pair`: dos payloads con misma referencia física, sin red.
- `physical_pair`: copias SQLite aisladas con guiones físicos elegidos por el observador, no resultados de una IA.
- `live_pair`: una deliberación real por rama (2 llamadas) o dos por rama con ejecución en mundos temporales (hasta 4 llamadas), siempre bajo consentimiento.
- Visor literal, registro HTTP, fichas de episodios, métricas de análisis transversal y evaluador histórico de autonomía `tools/evaluar_autonomia_23.py`.
- Variante modular en `gateway` y Ajustes, pero **Experimentos A/B no la transmitía a las solicitudes reales**. Sin corregir esto, la prueba conductual hubiera seguido comparando perfiles baseline, no baseline frente a contexto modular.

## 2. Cambios implementados

- `nilo_runtime/labs/ab_experiment.py`: el parámetro `context_mode` admite exactamente `baseline` o `modular`; la rama A usa siempre baseline, B usa la variante solicitada. Las percepciones parten del mismo estado congelado; cuando B solicita recuperación multifoco, esta se calcula **sobre su copia**, sin reescribir memoria ni alterar el mundo original. Se distinguen SHA de la percepción original, de la proyección alternativa y del cuerpo final transmitible.
- Las opciones `context`, `live` y `evolution` de `/experimentos` aceptan ese modo. `physical` sigue sin aceptar parámetros cognitivos: una prueba física guionada no demuestra una mejora de prompt.
- El selector de la interfaz indica explícitamente que **A es el contexto actual** y **B es el contexto modular opcional**. No modifica perfiles ni la partida.
- `nilo_runtime/labs/evaluation_11.py`: métricas de solicitud con cuerpo y roles verificados por SHA, bytes completos, campos presentes/ausentes, comprobación de reservas corporales internas y matriz de cambios. Para experimentos LLM, informa cantidades de decisiones válidas, operaciones propuestas, huellas de **planes completos** y tokens reportados, sin publicar textos ni inferir uso cognitivo de recuerdos.
- `tools/evaluar_laboratorio_11.py`: herramienta determinista, sin API, para evaluar **tres semillas × dos proveedores** y exportar JSON/Markdown **sin prompts, respuestas ni claves**.
- `.github/workflows/validacion.yml`: ejecuta la matriz sin red y adjunta JSON, Markdown y ZIP portátil de revisión a GitHub Actions como artefactos temporales. La instalación/migración/rollback Windows continúa en el job paralelo.
- `MANIFIESTO_SHA256.json`: incluye el módulo de evaluación para que el runtime del ZIP portátil pueda importarlo.

## 3. Protocolo de ensayos

### Fase T · Sin red (ejecutable automáticamente)

- Semillas 7321, 315 y 2026; proveedores Gemini y Groq; baseline vs modular.
- Para cada par: estado físico inicial común, modo registrado, modelo/configuración fija, roles literales, bytes UTF-8, hash de payload y campos omitidos/agregados.
- Comprobar preservación de `posición`, `necesidades`, `proyecto_actual` y `regla`; rechazar reservas numéricas internas si aparecen.
- Registrar la reducción/aumento de bytes por solicitud. **No estimar tokens ni creatividad a partir de esos bytes.**
- Repetir matriz en CI y retener el ZIP experimental y los informes como artefactos. El paquete contiene todas las etapas apiladas porque se construye directamente desde la rama 11, **sin fusionarlas en `main`**.

### Fase R1 · Respuesta LLM real (más adelante, con intervención del usuario)

- En **Experimentos A/B**, elegir B = modular, el mismo proveedor/modelo y una partida de referencia.
- Modalidad `live`: **2 llamadas reales**, una por rama, sin ejecutar decisiones. Observar original de solicitud, salida, normalización/errores, longitud y tipos de plan, coherencia contextual y consumos reales reportados por el proveedor.
- Exportar el JSON del experimento para la auditoría. **Puede contener prompts, cuadernos y salidas completas**; revisarlo antes de compartirlo.
- No inferir superioridad a partir de una sola respuesta no determinista.

### Fase R2 · Continuidad y evolución (más adelante, con intervención del usuario)

- Modalidad `evolution`: hasta **4 llamadas reales**, dos por rama y ejecución únicamente en mundos temporales. Repetir con varias semillas/estados para observar tendencias, errores, repetición e integridad física.
- Para continuidad de proyectos durante muchas deliberaciones se requieren **partidas longitudinales** controladas; cuatro llamadas son insuficientes para afirmar evolución de autonomía. El evaluador histórico de autonomía se reutilizará cuando esas partidas estén disponibles.
- Registrar fallos de conexión y decisiones inválidas como datos; no reintentar silenciosamente una llamada perdida.
- Antes de cambiar el modo activo, contrastar resultados de varias pruebas y revisar la UX del laboratorio con partida real y sidecar.

## 4. Limitaciones / criterios de aceptación

- La variante modular **no se aplica al Nilo activo**, y los filtros/checks del laboratorio no reescriben SQLite.
- Dos ramas estocásticas no prueban causalidad, aunque compartan semilla, snapshot y proveedor.
- Una memoria incluida en el HTTP no demuestra lectura/uso por el LLM; una acción declarada no acredita éxito físico.
- El JSON resumido excluye el texto literal; los originales siguen accesibles **solo** en los resultados completos del experimento cuando se exportan deliberadamente.
- Los tests usan respuestas sintéticas para verificar la lógica de comparación **sin hacer consultas API**.
- El ZIP preliminar puede seguir mostrando la **versión nominal 0.7.0** heredada del manifiesto de la rama. Se identifica externamente como **preview de laboratorio 0.7.1**; no publicarlo como release ni reemplazar versiones estables.

## 5. Cierre de etapa

La preparación técnica puede cerrarse tras aprobación de CI (suite general, matriz sin red, empaquetado e instalación Windows). **La evaluación conductual definitiva y la integración en main se mantienen abiertas** hasta las corridas reales y la revisión visual. La etapa 11 tiene por tanto un hito técnico y un hito de validación real; no declarar el segundo cumplido sin resultados de proveedores.

**Pendientes antes de recomendar un cambio de motor:** validar las rutas del laboratorio con una partida/sidecar real, comparar muestras de varias deliberaciones, documentar aceptación/rechazo de variantes y consolidar los PR #85–#95 tras esa prueba.
