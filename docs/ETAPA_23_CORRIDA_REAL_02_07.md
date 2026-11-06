# Nilo 0.7 — Etapa 23: continuación prolongada de la primera partida real

**Fecha de lectura:** 2026-11-06. **Estado:** segunda observación de la **misma** sesión, no una corrida independiente. Etapa 23 abierta.

## Procedencia y límites

Se compararon localmente dos copias SQLite sucesivas provistas por el usuario; integridad `PRAGMA quick_check=ok` en ambas. **No se subieron las SQLite, cuadernos, prompts, secretos ni respuestas completas del agente.** Identificación de sesión inicial conservada (inicio UTC 2026-11-05 21:59:01); último registro UTC 2026-11-06 03:52:02. El archivo `engine_version=0.6.4` y `code_commit=NULL` persiste: la sesión no prueba por sí misma el commit ejecutado.

- Total real transcurrido desde inicio: **5 h 53 min** (aprox.). Tiempo simulado: **6391,24 minutos** (4 días y 10 h 31 min), a ×60 según snapshot final.
- Decisiones reales archivadas: **566** con Gemini (489 Flash-Lite 3.1, 76 Flash-Lite 3.5, 1 Flash 3.8); `session_model_usage` registra además **1 llamada de chat** con 3.5, que no es una deliberación. Sin decisiones exitosas de Groq.
- Historial: **6182** registros; mediciones físicas **350**; casillas conocidas **743** (706 incorporadas durante la corrida según métrica acumulada); casillas visitadas registradas: **330**. Cuatro objetos portátiles en inventario, cero estructuras fijas construidas; 50 conclusiones y 75 investigaciones (40 abiertas).
- Estos recuentos acreditan actividad, no la calidad semántica de cada conclusión ni un progreso constante.

## Secuencia del bucle y recuperación

1. **Día 1, 03:55:** Nilo **sí completó** por sí mismo el primer proyecto «Localizar una orilla de agua transitable», citando la medición de exploración pertinente `med-cb80ba9d0856`. No se modificó el motor entre el volcado anterior y esta continuación.
2. **Día 1, 03:57:** el agente intentó completar el objetivo recién cerrado sin proyecto activo y **abrió un segundo proyecto con el mismo título**, ID diferente. El validador pasó a exigir mediciones asociadas a ese nuevo proyecto y los ensayos originales dejaron de ser admisibles como evidencia del nuevo ID.
3. **Día 1, 10:36 y 19:23:** Nilo decidió abandonar su segundo proyecto, pero reanudó el mismo objetivo. Hubo períodos prolongados sin medidas pertinentes y con innumerables conclusiones duplicadas.
4. **Día 2, 10:26:** cerró satisfactoriamente el segundo proyecto gracias a la inspección verificada de agua, `med-93bfb70be587`; el cierre fue correcto conforme al criterio codificado.
5. **Día 2, 10:28:** volvió a **crear un tercer proyecto idéntico**, que finalmente **abandonó en el día 2, 10:42**, reconociendo la redundancia.
6. **Día 2, 10:44:** inició el proyecto diferente «Explorar el entorno inmediato para identificar y recolectar recursos básicos», asociado a desplazamientos, recolección y actividades físicas reales. Seguía activo a día 5, 10:11 (152 deliberaciones en ese proyecto). Esto es la **salida efectiva del bucle original**, pero ocurrió después de más de un día simulado de reiteraciones.

## Coste del estancamiento y cambio de conducta

| Día simulado | Decisiones LLM | Mediciones físicas | Rechazos de cierre | Deliberaciones con plan vacío |
|---|---:|---:|---:|---:|
| 1 | 332 | 95 | 324 | 256 |
| 2 | 104 | 101 | 77 | 47 |
| 3 | 67 | 56 | 44 | 38 |
| 4 | 46 | 74 | 0 | 0 |
| 5 (parcial) | 17 | 24 | 0 | 0 |
| **Total** | **566** | **350** | **445** | **341** |

El contador de **445 rechazos** proviene de eventos explícitos «No puedo declarar el objetivo cumplido», no de impresiones subjetivas. El agente pidió completar proyectos en 447 deliberaciones (incluye cierres exitosos). Los rechazos se distribuyen así:
- Día 1: mayormente evidencia inexistente para un proyecto recién duplicado.
- Día 2: sobre todo ausencia de observación/inspección/llegada que satisfaga el predicado de localización.
- Día 3: 44 rechazos con razón literal «Explorar no demuestra haber encontrado el objeto buscado», aun en una investigación que abarcaba exploración **y recolección** verificable. El criterio genérico no resuelve bien todos los objetivos compuestos.

El **día 4 es un cambio real**: 46 deliberaciones y 74 mediciones, sin rechazos de cierre; 55 exploraciones exitosas. Se fabricaron herramientas y se recolectaron materiales durante la fase nueva, pero no hubo construcciones fijas. No inferir que terminó el problema de autonomía: el proyecto de exploración seguía activo con 152 deliberaciones.

## Fricción posterior: exploración de fronteras

Durante los días 4 y 5 hubo **17** intentos de exploración fallidos por ausencia de una frontera alcanzable en la dirección solicitada (9 + 8); el historial también muestra exploraciones exitosas el día 5 (8), de modo que **no** se puede declarar agotado todo el mapa. El agente reaccionó a varios fallos cambiando de dirección y recorriendo rutas conocidas hacia las ruinas, pero luego volvió a pedir exploraciones sin frontera. En el volcado final ocupa `[12,7,0]` y tiene una exploración hacia el este recién comenzada, aún sin resultado.

## Conclusiones implementables

1. **Prioridad máxima: anti-recreación de proyectos completados.** Un proyecto marcado terminado conserva su identidad y sus evidencias; si una deliberación posterior solicita «completar» sin proyecto activo, **no crear otro con el mismo título**. Informar al agente del cierre registrado y ofrecerle libertad de abrir un objetivo genuinamente distinto. Incluir regresión de cierre → respuesta LLM repetida → no duplicado.
2. **Criterios de cierre semánticamente acotados y medibles.** Las metas de «explorar, identificar y recolectar» combinan múltiples tipos de pruebas. Una descripción general no debería dar cierre automático, pero la recolección física y la observación de recursos sí deberían poder usarse para demostrar sus cláusulas si el objetivo lo exige. Pruebas negativas contra evidencia no pertinente.
3. **Corte de propuestas de cierre idénticas sin prueba nueva**, manteniendo al LLM libre de continuar, pausar, abandonar o cambiar. En esta corrida los mensajes de advertencia coexistieron con hasta 445 rechazos: la prevención actual no basta.
4. **Revisar sugerencias de fronteras y contexto del mapa**, distinguiendo «no hay frontera en la dirección elegida» de «no queda nada accesible» y usando IDs de intentos previos para no reiterar órdenes infructuosas. No imponer exploración al motor.
5. **Procedencia del bundle ejecutado** (`code_commit` obligatorio para nuevas corridas evaluativas) y evaluación de costo/eficiencia por deliberación física, ya que 566 decisiones incluyen gran proporción sin plan realizable.
6. Hacer una corrida nueva tras correcciones y contrastar indicadores; completar también la matriz Gemini/Groq de dos semillas. **No cerrar etapa 23 aún.**

**Limitación:** esta segunda base representa la continuación de la primera, no una réplica independiente. No hubo control de proveedor ni temperatura. El conteo de una llamada de chat no demuestra si hubo intervención sobre decisiones; no suponerla.
