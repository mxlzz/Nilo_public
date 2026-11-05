# Nilo 0.7 — Etapa 23 · Evaluación autónoma real

**Estado: en curso.** Se incorporaron instrumentos de ejecución y análisis en la rama de trabajo. **Todavía no se acreditan corridas reales de Gemini y Groq.** No cerrar la etapa por tests sintéticos o resultados del modo demo. La rama main y VERSION siguen en 0.6.4; PR #77 permanece como borrador.

[Plan general](PLAN_REESTRUCTURACION_NILO_07.md) · [Tablero](ESTADO_REESTRUCTURACION_07.md) · [Protocolo previo](PROTOCOLO_EVALUACION_0594.md).

## 1. Auditoría de datos existentes

La instrumentación registra engine_sessions, session_model_usage, history.llm_decision, history.diagnostic, history.measurement y acumuladores behavior_metrics. Los ocho días de la etapa 22 fueron **sin LLM** y no permiten concluir nada sobre la iniciativa.

Los límites reales de esta observación son:

- El uso declarado por el motor y las decisiones archivadas respaldan que se procesaron deliberaciones. No constituyen una prueba criptográfica del proveedor ni incluyen respuestas fallidas o coste monetario. Un proveedor simplemente configurado no cuenta como corrida.
- Los diagnósticos de acciones no contienen todas las tareas documentales (write, design, propose). Las estadísticas de comportamiento tampoco abarcan retroactivamente todo el historial.
- Una repetición de acciones o planes puede ser razonable si cambian las condiciones físicas; sus recuentos son señales para estudiar episodios por ID, no juicios automáticos sobre la inteligencia del agente.
- Una semilla común no fija las respuestas de un servicio LLM. Las comparaciones son descriptivas, nunca causalidad atribuida sin control adicional.
- El gateway usa temperatura 0,85 para deliberación Gemini y 0,8 para Groq. No se ajustan las leyes ni el prompt con fines de la evaluación.

## 2. Implementaciones de este paso

- **tools/ejecutar_autonomia_23.py:** corre una Simulation nueva con Gemini/Groq real, sin demo, fallback ni chat. Requiere una clave de entorno, semillas explícitas, límite de respuestas exitosas, intervalo mínimo de 15 s y límite temporal. Una carpeta de salida ya existente se rechaza; ninguna partida personal se modifica. Emite SQLite local y manifiesto sin secretos.
- **tools/evaluar_autonomia_23.py:** lectura SQLite mode=ro/query_only, mediciones, decisiones y modelos realmente registrados, procedencia de acciones, planes idénticos, fallos sucesivos, descubrimientos y proyectos. Los informes omiten cuaderno, conversación, motivos, planes completos, prompts y credenciales. El argumento --reports permite comparar JSON anonimizados sin circular bases personales.
- **tests/test_autonomia_23.py:** cobertura del reporte, neutralidad frente a texto narrativo, preflight con claves simuladas (sin llamadas reales), límites, repetición y no divulgación.
- **.github/workflows/validacion.yml:** pruebas offline normales y opción manual de corrida real al activar corrida_real=true en la rama refactor/0.7. Ningún push o pull request usa claves. Solo se suben tres reportes agregados como artifact; nunca la base SQLite.

## 3. Ejecución manual y controlada

En GitHub, abrir **Actions → Validación Nilo → Run workflow**, seleccionar refactor/0.7, marcar corrida_real y elegir proveedor, modelo y semillas. La clave debe estar configurada como secret GEMINI_API_KEY o GROQ_API_KEY en el repositorio. La opción manual ejecuta hasta **8 respuestas LLM exitosas** o **420 segundos reales**, con velocidad ×60. No es un ensayo prolongado y puede terminar incompleta por 429, fallos de red o presupuesto.

Como alternativa local, sobre una copia separada de la rama refactor/0.7, con la clave ya definida en el entorno:

    python tools/ejecutar_autonomia_23.py --provider gemini --model gemini-3.1-flash-lite --world-seed 7321 --rng-seed 1129 --max-calls 32 --max-seconds 1500 --speed 60 --output "C:\Nilo\eval-23-gemini-7321"

Para Groq se elige provider groq y model openai/gpt-oss-20b, con carpeta nueva. El script no pide la clave por línea de comandos y no la incluye en JSON. Para comparar dos informes previamente anonimizados:

    python tools/evaluar_autonomia_23.py --reports evaluacion_A.json evaluacion_B.json --json comparacion.json --markdown comparacion.md

O bien analizar dos SQLite locales, cerradas:

    python tools/evaluar_autonomia_23.py partida_A.sqlite3 partida_B.sqlite3 --markdown informe.md

## 4. Matriz de evaluación prospectiva

La tanda mínima prevista comprende **dos parejas de semillas** (mundo 7321/RNG 1129 y mundo 1129/RNG 7321) con **Gemini y Groq**, cuatro partidas totalmente nuevas. Para observar continuidad y reiteración hacen falta corridas más largas que el smoke manual: objetivo de al menos 32 deliberaciones reales por caso y evidencia sobre tiempo simulado. Mantener iguales las condiciones salvo el proveedor y anotar pausas, quotas, cambios humanos y respuestas incompletas. La comparación contra **0.6.4** requiere una matriz equivalente ejecutada en su motor, y no puede inferirse de la batería física de la etapa 22.

La revisión de cada caso debe estudiar: secuencia de planes y resultados físicos, descubrimientos reales y revisitaciones, investigaciones/proyectos con evidencia pertinente, consumos y esperas de proveedor, ensayos no evaluables por falta de física y condiciones corporales al cuidarse. El cuaderno puede explicar elecciones, pero no sustituye medidas. No imponer tareas externas ni alterar la física para obtener diversidad.

## 5. Puerta de salida

**Pendiente:** cuatro corridas reales documentadas, comparación reproducible, inspección de anomalías con IDs de acciones/mediciones y corrección exclusivamente de defectos atribuibles al motor si aparecen. La validación CI de instrumental no constituye cierre conductual. Hasta entonces, la etapa 24 y el release 0.7.0 permanecen bloqueados.
