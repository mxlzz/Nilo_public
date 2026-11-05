# Nilo 0.7 · Etapa 15 — Deliberación y proveedores LLM

Fecha: 5 de noviembre de 2026. Rama: refactor/0.7. 
Estado técnico: implementación integrada; cierre pendiente de confirmación del CI final.
Referencia: main / 0.6.4, save SQLite v5 y partidas personales sin modificaciones.

Referencias: [plan](PLAN_REESTRUCTURACION_NILO_07.md), [seguimiento](ESTADO_REESTRUCTURACION_07.md), [PR #77](https://github.com/mxlzz/Nilo_public/pull/77), [issue #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Reauditoría y hallazgos

Se examinaron brain.py, prompt_budget.py, providers.py, cognitive_projection.py, los casos de uso de deliberación y chat, el banco de escenarios, las previsualizaciones de contexto y las pruebas históricas de JSON, cuotas y fallback.

- La misma fuente brain.py contenía reglas narrativas, presupuesto, parseo, generación del cuerpo HTTP y acceso a red. Se repartió por propietario, manteniendo fachadas antiguas.
- SYSTEM y GROQ_SYSTEM estaban escritos y mantenidos independientemente; por lo tanto podían dar instrucciones distintas. Ahora se derivan de 24 reglas identificadas, con descripción extensa y su síntesis compacta.
- SHORT_OPERATIONS contenía ejemplos manuales duplicados del registro físico de operaciones. Se reemplazó por resúmenes derivados de OperationSpec, conservando el primer ejemplo JSON íntegro, sus llaves y su nombre de operación.
- El prompt extenso y el manual de wait aún lo describían como recuperador de energía pasiva. Se corrigió esa instrucción para respetar la distinción rest/wait implantada en etapa 13. No se alteró la fórmula física.
- El chat para proveedores compatibles colocaba los datos observados y posibles textos humanos dentro del mensaje de sistema. Se separaron las instrucciones de los datos: el estado se envía como contenido de usuario.
- La validación de URLs locales aceptaba por prefijo dominios HTTP que no eran realmente localhost. Ahora se comprueba el hostname y solo se permite HTTP para localhost y 127.0.0.1; los demás endpoints requieren HTTPS.
- Las trazas de los laboratorios apuntaban a funciones que habían sido trasladadas y dejaron de ejecutarse en las antiguas fachadas. Se reorientaron a sus rutas reales.
- La clave de salud de Groq se incrementó a compact-v2 para no heredar enfriamientos por errores 413 del presupuesto anterior. No se eliminan cuotas ni límites de los proveedores.

## 2. Responsabilidades y contratos nuevos

**nilo_runtime/agent/prompts.py:** una sola especificación de 24 reglas de identidad, evidencia, autonomía, necesidades, proyectos, agenda, límites de física y respuesta. Cada regla tiene ID, forma detallada para Gemini/compatibles y forma condensada para Groq. El chat tiene una instrucción propia que conserva la personalidad de Nilo y no ejecuta acciones.

**nilo_runtime/agent/budget.py:** selección de contexto por campos, priorización de hechos, preservación del núcleo y compresión íntegra de listas de evidencia. El presupuesto final de Groq considera los bytes de la solicitud real, incluidas instrucciones, operaciones y JSON. Las operaciones compactas se generan a partir del catálogo físico.

**nilo_runtime/agent/responses.py:** parseo de JSON y normalización de decisiones, usando la validación de operaciones del motor. Se rechaza explícitamente un plan que no sea una lista, así como decisiones sin cuaderno o acciones utilizables. Interpretar una propuesta de LLM no significa ejecutarla ni acreditar un resultado físico.

**nilo_runtime/agent/gateway.py:** construcción sin red de solicitudes de deliberación y chat, transporte único y decodificación de respuestas Gemini/OpenAI-compatible/Groq. El cuerpo de solicitud calculado es el mismo que usa el envío real; los encabezados con credenciales se mantienen fuera del payload. Los rechazos del modelo se expresan como errores controlables por el router.

**providers.py:** mantiene la única política de orden de proveedores, respaldo, enfriamiento, cuotas, reintentos y estado público, sin construir un segundo motor de decisiones. Los casos de uso del orquestador siguen llamando al mismo contrato externo.

**Fachadas:** brain.py conserva contexto cognitivo, configuración, modo demo y los nombres de importación históricos; prompt_budget.py solo reexporta funciones. cognitive_projection.py ya no depende de la función corporal privada ubicada dentro de brain.py.

**Laboratorio:** la auditoría de contexto y el laboratorio de motor usan el mismo constructor que la red y registran trazas ejecutadas de los nuevos propietarios, sin atribuir llamadas a la fachada.

## 3. Cambios deliberados y límites

La síntesis de Groq se reconstruye desde el contrato común, por lo que cambia el texto enviado respecto de versiones anteriores; comparte reglas y catálogo de operaciones con los demás proveedores, aunque contiene menos ejemplos y explicaciones. Se corrigió una información errónea sobre wait. El contexto del chat compatible pasa de rol de sistema a rol de usuario para no privilegiar su contenido.

Se conserva la identidad de persona contemporánea autónoma, la elección libre de proyectos, el trato de hipótesis frente a medición y la ausencia de autocuidado impuesto. No se añadieron conocimientos del mundo al LLM ni propiedades físicas por mera narrativa.

La equivalencia semántica y las pruebas de estructura no garantizan equivalencia conductual: solo partidas controladas con Gemini y Groq reales pueden evaluar iniciativa, repetición de procedimientos, continuidad de proyectos y costos de API. Eso corresponde a la etapa 23. Los experimentos de memoria y procedencia quedan para etapa 16.

## 4. Verificación

- Auditoría dedicada tools/auditar_deliberacion_15.py: verifica propietarios únicos, ausencia de duplicados, derivación de ambos prompts desde las mismas 24 reglas, catálogo de operaciones y trazas reales.
- Diez nuevos tests en tests/test_deliberacion_15.py: contrato compartido, ejemplos JSON, fachadas históricas, payload previsualizado frente al enviado, confidencialidad de headers, errores, fallback, URL local y chat.
- Se mantienen pruebas preexistentes del laboratorio, auditoría del contexto, proveedores y presupuestos. Las expectativas que asumían que el chat enviaba datos en rol de sistema se actualizaron; el límite del prompt compacto se mantiene, no se relajó.
- Los cambios del motor y de las partidas permanecen fuera de alcance; los checks integrales deben incluir replay, ZIP portable, escenarios, prueba de arranque y seis partidas históricas sintéticas.

## 5. Próximo alcance

Etapa 16: memoria, investigación y evidencias; procedencia de recuerdos y conclusiones verificadas. Permanecen previstas las revisiones de persistencia (18), laboratorio (21), QA (22) y evaluación autónoma con proveedores reales (23). No fusionar PR #77 ni publicar 0.7.0 antes de la etapa 24.
