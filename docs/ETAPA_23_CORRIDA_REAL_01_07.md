# Nilo 0.7 — Etapa 23: primera partida con decisiones LLM reales

**Fecha:** 2026-11-05. **Estado:** diagnóstico preliminar; etapa 23 abierta.

## Procedencia y límites

Análisis local, solo lectura, de una base SQLite aportada por el usuario. **No se publicó ni incorporó la base, prompts, cuaderno, credenciales o configuraciones privadas.**

- Integridad SQLite: `quick_check = ok`.
- Sesión registrada: 10 min 56 s (21:59:01–22:09:57 UTC); 219,2 minutos simulados.
- `engine_version=0.6.4`, `code_commit=NULL`; por lo tanto, no es posible demostrar el commit exacto de `refactor/0.7` exclusivamente desde la partida. El nombre de la versión es heredado.
- Entorno `isla_v1`; semilla de mundo 7321; semilla del agente 9821; velocidad ×60. Inicio de mundo nuevo.
- LLM: 19 deliberaciones exitosas de Gemini: 18 con `gemini-3.1-flash-lite`, una con `gemini-3.5-flash-lite`. Hay errores HTTP 503 registrados en el estado de proveedores alternativos, pero **ninguna deliberación exitosa de Groq**.
- 238 filas de historial; 15 mediciones de acciones (14 éxitos, 1 fallo); 8 investigaciones al cierre, todas abiertas. Sesión no marcada como finalizada al momento del volcado (`ended_utc=NULL`).

## Secuencia física comprobada

1. Desde el inicio hasta el minuto 00:50: seis operaciones `explore`; 66 casillas nuevas observadas acumuladas según `behavior_metrics`. Descubrimiento de agua: medición `med-cb80ba9d0856`, historial seq 55–60.
2. Hasta 01:20: dos desplazamientos `go` y dos inspecciones `inspect`; llegó a la posición terrestre (22,19,0), adyacente al agua.
3. 02:21: `craft` positivo de un recipiente con piedra y madera, `med-75e78bcdbffd`.
4. 02:48: `use` con método `llenar` positivo, `med-c96bdfa4e55c`, capacidad estática estimada de 1,08 unidades de agua. **Esto no prueba potabilidad, impermeabilidad a largo plazo ni evaporación**.
5. Desde 02:49 hasta el final (03:38): ya no hay descubrimientos, movimientos ni nuevas pruebas físicas del recipiente. Hubo tres operaciones `conclude` (dos exitosas, una duplicada rechazada), sobre la evidencia previa.

## Anomalía reproducida en la partida: ciclo de cierre

- Proyecto original: «Localizar una orilla de agua transitable»; al final sigue **activo** con progreso estimado 95 %, 13 deliberaciones desde el último avance.
- Hay 14 rechazos de `accion_proyecto=completar`. El primero (00:50, antes de verificar acceso) puede ser razonable; **13 rechazos ocurren tras recolectar agua exitosamente**.
- El validador señala como evidencia pertinente de localización la medición `med-cb80ba9d0856` (exploración y observación de agua). El LLM insiste en usar `med-c96bdfa4e55c` (recolección real de agua), que sí existe y pertenece al mismo proyecto, pero no forma parte de los IDs aceptados para el objetivo.
- El LLM produjo repetidamente planes vacíos o nuevas conclusiones sobre el mismo hecho. Los registros muestran diez avisos de plan sin pasos verificables, ocho avisos de bloque repetido y 13 deliberaciones sin avance.
- En `nilo_runtime/autonomy/goal_evidence.py`, `check_goal` considera, para localizar agua, `explore` con primera observación, `inspect` apropiado, `go` con hechos explícitos, y `drink`, pero **no** `use/llenar`. Además, `select_closure_evidence` exige que la cita pertenezca al subconjunto que pasó `check_goal`. Esto explica la divergencia entre medición válida y evidencia admitida para el cierre.
- El rechazo y su ID pertinente estaban presentes en el contexto reducido (según tamaños de secciones); la instrucción de reconsiderar no logró impedir la reiteración. No se atribuye el problema únicamente al proveedor.

## Acciones técnicas recomendadas

1. **Revisar el criterio específico de “orilla de agua transitable”**: aceptar una prueba de recolección de agua con `use/llenar` físicamente verificada y acceso a la orilla, con predicados tipados; conservar los límites contra pruebas de potabilidad o propiedades no instrumentadas. No hacer cierre automático: debe seguir exigiéndose `accion_proyecto=completar` y cita de evidencia.
2. Agregar una regresión de `check_goal/select_closure_evidence` con la secuencia real reducida y casos negativos: un `craft` sin uso, agua meramente visible sin orilla alcanzada, ID de otro proyecto y afirmaciones sin medición.
3. Después de repetidos cierres rechazados por el mismo par proyecto/motivo sin nueva evidencia, interrumpir las reiteraciones idénticas y habilitar deliberación para continuar, pausar o cambiar de investigación, sin imponer un objetivo.
4. Incorporar procedencia reproducible de código al bundle usado fuera de Git: `code_commit` o identificador inmutable de compilación. La etiqueta `VERSION` heredada no identifica una revisión de 0.7.
5. Repetir una corrida nueva tras la corrección; mantener la matriz pendiente Gemini/Groq y dos semillas. **Esta única sesión no acredita mejora conductual general ni cierra etapa 23.**
