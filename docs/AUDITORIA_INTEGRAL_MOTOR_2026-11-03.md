# Auditoría integral del motor · 3/11/2026

**Versión evaluada:** Nilo 0.6.1. **Estado:** diagnóstico verificable; no se implementaron correcciones.

## Alcance

- Orquestador real: Simulation.plan_ready → validación → tick → navegación → física → ActionResult → mediciones → archivo → persistencia SQLite, con decisiones de brain.demo_decision (NO LLM).
- Barrido manual de las 26 operaciones: 30 casos, sin excepciones. Algunos son rechazos físicos correctos; no equivalen a 26 rutas positivas completas.
- Casos positivos aislados: descender/ascender, fabricar/ensayar/reforzar/depositar/recuperar, recolección con desplazamiento, restauración desde SQLite.
- Análisis complementario de la partida real de 13 días simulados, 607 deliberaciones LLM y 856 acciones; esa corrida NO se reprodujo con Gemini/Groq en CI.
- 626 tests aprobados, uno omitido. Escenarios deterministas y replay entre procesos también aprobados.

## Resultados del simulador principal sin IA

| Semilla | Deliberaciones demo | Acciones físicas | Días simulados | Resultado |
| --- | ---: | ---: | ---: | --- |
| 7321 | 60 | 154 | 2,039 | Integridad y persistencia correctas |
| 2026 | 35 | 84 | 1,074 | Integridad y persistencia correctas |
| 7321 (prolongada) | 142 | 359 | 5,691 | Inconsciencia por agotamiento; controlador demo no practica autocuidado |

En la corrida prolongada: 141 exploraciones, 26 fallos y 34 sin nuevas casillas. El controlador es deliberadamente limitado; su comportamiento no representa autonomía LLM.

## Hallazgos verificables y propuestas

### 1. Contrato temporal inconsistente — prioridad alta

En la partida real, los campos action_result.duration_minutes y physical_result.duration_minutes difieren en más de 0,6 minutos en 369/369 exploraciones, 92/92 desplazamientos, 79/79 recolecciones, 77/77 descansos, 71/71 interacciones y 5/5 construcciones.

Ejemplos: ActionResult del viaje registra 0 minutos pese a 6–36 minutos medidos; build registra 60 frente a 90; rest registra 25 frente a 30. No se deduce que el reloj esté mal: deben distinguirse duración estimada, duración física aplicada y tiempo realmente transcurrido.

**Corregir:** crear una referencia temporal unificada por fase con duración planeada, transcurrida, de viaje, de trabajo e interrupciones. Las medidas y los diagnósticos deben usar el tiempo realmente simulado.

### 2. Recolección remota sin tiempo de extracción — prioridad alta

Caso aislado: reunir dos piedras desde tres tramos de distancia consume **9 minutos**. Reunirlas junto al recurso consume **22 minutos**. En la partida real también hay recolecciones exitosas de 3, 6 y 9 minutos. El motor consume tiempo del desplazamiento y ejecuta la extracción inmediatamente al llegar.

**Corregir:** separar viaje → trabajo/extracción → balance de recursos. Verificar interrupciones, consumo fisiológico y no acreditar materiales antes de completar la extracción.

### 3. Identificadores de construcciones no deterministas — prioridad alta

Mismo mapa, mismos materiales y misma semilla del RNG explícito producen obras llamadas obra-1-8805 y obra-1-51206 al variar solo el RNG global de Python. La generación actual utiliza random.getrandbits(16) en world.py.

**Corregir:** usar identificadores persistentes por mundo con secuencia determinista o fuente controlada. Preservar IDs antiguos, vínculos y migraciones. Revisar además continuidad del estado RNG tras reinicios: no se demostró todavía su efecto con una prueba de reanudación.

### 4. Exploración agotada y reiteración — prioridad alta, dimensión cognitiva

En la partida LLM hubo 369 exploraciones, 90 exitosas y 279 fallidas; desde el día 5 ninguna produjo éxito. El contador no_progress_steps no cuenta sistemáticamente explore fallido. La cueva conocida no fue descendida en el run real, pero la prueba física desde su entrada dio éxito al bajar y subir.

**Corregir:** representar el agotamiento territorial como hecho condicional al mapa realmente conocido y a capacidades observadas; revisar el contador y el registro de intentos por sector/resultado. Evitar avisos espontáneos de «se actualizó el mundo» o recomendaciones obligatorias de explorar cueva; respetar las decisiones de diseño sobre autonomía y memoria (#2, #4, #20, #63).

### 5. Precondiciones difíciles de interpretar en interact — prioridad media-alta

33 de 71 interacciones reales terminaron en precondition_failed. En barrido, métodos de carga fallaron correctamente por distancia; al colocar a Nilo junto a la obra, probar, depositar y recuperar fueron exitosos.

**Corregir:** exponer IDs únicos, alcance, método instalado, precondiciones observables y alternativas de localización sin eliminar validación física. Relación con go por nombres (#64) y catálogo operativo (#66).

### 6. Cobertura desigual de diagnósticos — prioridad media

642 de 856 diagnósticos del run real tienen código sin_regla_especifica (aprox. 75 %), principalmente en operaciones generales. No son 642 errores, pero limitan la auditabilidad de invariantes temporales, trayectos y evidencias.

**Corregir:** completar contratos genéricos verificables sin inventar fenómenos físicos.

### 7. Proyectos y cierres sin continuidad — prioridad media-alta

La partida real tiene 35 proyectos pausados, 7 abandonados y 3 terminados. Hay rechazos criterio_no_instrumentado cuando un objetivo descriptivo pretende cerrarse como hipótesis física. El demo crea nuevos proyectos por diseño: sus 55 proyectos pausados no prueban una falla equivalente del motor.

**Corregir:** distinguir actividad realizada de hipótesis demostrada, conservar evidencias y motivos por ID, recuperar solo por reconocimiento, continuidad o consulta voluntaria; evitar inyección de intereses.

## Capacidades físicas verificadas

- Cueva: descenso en (23,7,0) a (23,7,-1) y ascenso inverso; ambos verified_success.
- Cargas: prueba de dos piedras no las consume; depósito 16→14 piedras; reforzar aumenta revisión 1→2; recuperar deja 16. Ciclo completo successful.
- Persistencia: hora, posición y casillas reveladas conservadas tras cerrar y reabrir SQLite.
- Integridad: sin inventarios negativos en los escenarios probados ni excepciones durante el barrido de 30 casos.

## Límites

Sin credenciales de Gemini/Groq no hay una nueva corrida real autónoma con LLM. La demo no decide metas creativas ni autocuidado y no permite inferir evolución psicológica. No se ejercitaron rutas exitosas de todas las operaciones: algunas pruebas negativas se mantuvieron como verificaciones de precondición.

El laboratorio 0.6.1 ejecuta acciones sueltas pero no muestra todavía el flujo integral de normalize_decision → IslandPlanner → plan_ready → tick → evidencia → memoria. Para auditar como si el usuario fuera el LLM, convendría añadir un modo de plan completo y ejecución paso a paso sin duplicar el motor.

## Orden de trabajo sugerido

1. Unificar tiempos y corregir extracción remota.
2. Corregir IDs deterministas y probar persistencia del RNG.
3. Corregir estancamiento de exploración y cierres de proyectos; evaluación con LLM real antes de atribuir mejora cognitiva.
4. Ampliar diagnósticos, percepción contextual y affordancias por objeto; el diseño sobre memoria y navegación por nombres sigue abierto.
5. Ampliar el laboratorio con el ciclo completo de deliberación y planificación.

## Reproducibilidad

Ejecutar en el repositorio: python -m unittest tests.test_auditoria_integral_motor -v.

La suite usa mundos nuevos y SQLite temporal, no modifica la partida real del observador. Los resultados aparecen en el log de CI bajo el prefijo AUDITORIA_. Este informe no modifica las leyes del motor ni compromete una nueva versión.
