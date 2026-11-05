# Roadmap técnico histórico · Nilo

> **Este documento conserva la evolución técnica desde 0.5.7 y las propuestas de entonces.** No se debe leer una mención histórica de «siguiente versión» como compromiso vigente.
>
> **Plan de desarrollo actual (2/11/2026): [FUTUROS_CAMINOS.md](FUTUROS_CAMINOS.md).** Motor publicado: `0.5.9.3.34.1`. Próximo incremento propuesto: `0.5.9.3.35` (exploración dirigida y cardinales, #106/#55). `0.5.9.4` es el hito ya previsto de corridas comparables (#15). Las propuestas `0.5.9.3.36` y `.37` **no están confirmadas** como requisitos para avanzar a `0.6`; no hay hito `0.5.9.3.40` establecido. **0.6** conserva la física composicional y modularidad como próximo gran salto funcional propuesto.
>
> **Criterio de cambio:** verificar dependencias reales, evidencia de runs, riesgos y coste de oportunidad antes de añadir parches; el orden y alcance son revisables por decisión del observador. Actualizar primero el plan vivo, después los issues. Este registro anterior no se reescribe retroactivamente.

---

## Estado actual al 3/11/2026 — auditoría 0.6.3

La planificación vigente está en [FUTUROS_CAMINOS.md](FUTUROS_CAMINOS.md); este documento conserva cronología técnica. Ya están publicados el primer corte físico 0.6.0 y los instrumentos de prueba **0.6.1–0.6.3**: 68 escenarios con el orquestador real, traza de código y slider histórico con checkpoints para runs nuevos. La [CI de release 0.6.3](https://github.com/mxlzz/Nilo/actions/runs/41663032997) registró **634 tests (1 omitido)** y verificó escenarios/replay entre procesos; no es prueba de conducta LLM. La [auditoría integral](AUDITORIA_INTEGRAL_MOTOR_2026-11-03.md) se incorporó con [PR #138](https://github.com/mxlzz/Nilo/pull/138).

**C.1 — avance parcial:** ahora hay capturas restaurables de decisión/acción nuevas, pero siguen sin cubrirse UUID y reloj real externos, versiones antiguas sin estado previo, evidencia archivada fuera del snapshot y costo de historial a largo plazo ([#65](https://github.com/mxlzz/Nilo/issues/65)). **C.2 — avance parcial:** resultados físicos tipados persisten, pero las duraciones reportadas no tienen aún contrato uniforme ([#141](https://github.com/mxlzz/Nilo/issues/141), [#142](https://github.com/mxlzz/Nilo/issues/142)). Identificadores no deterministas en construcción ([#143](https://github.com/mxlzz/Nilo/issues/143)). Los reintentos sin progreso de `explore` siguen bajo [#14](https://github.com/mxlzz/Nilo/issues/14). No marcar como completados por disponer de un laboratorio.

## Contenido histórico desde 0.5.7.1

# Estado de consolidación después de Nilo 0.5.7.1

> **Registro vivo de futuros caminos y decisiones pendientes:** [FUTUROS_CAMINOS.md](FUTUROS_CAMINOS.md). Este archivo mantiene historia técnica y contiene hitos que ya fueron implementados; el índice distingue explícitamente lo completado, lo planificado y lo exploratorio.


## Versiones y ramas

- `archive/0.5.7-alpha.1`: primer intento preliminar (commit `b4d7a699`). Histórico; no es la base del desarrollo.
- `release/0.5.7`: segunda implementación (commit `ab1ce158`), base de la serie 0.5.7.x.
- `main`: versión de desarrollo establecida desde esa segunda implementación.

## Auditoría 0.5.6.3: estado de los cambios

| Propuesta | Estado en 0.5.7.1 | Pendiente real |
| --- | --- | --- |
| C.1 Arnés reproducible | Escenarios físicos y reproducción offline validada entre procesos con reloj/semillas controlados en 0.5.7.2 | Capturar snapshot inicial, decisiones del observador y secuencia temporal real para reproducción histórica exacta |
| C.2 Resultados estructurados | Diagnósticos tipados y deltas en las acciones | Sustituir consumo de cadenas y duplicación de acciones en todos los módulos |
| C.8 Estadísticas factuales | Métricas desde 0.5.7.1, visibles e incorporadas a contexto | Corridas comparables con semillas y agentes de referencia |
| Corrección fuga de navegación | Implementada en 0.5.7 | Regresión y pruebas largas |
| Procedencia de acciones | Continuaciones automáticas identificadas como `motor` | Revisar sistemáticamente las restantes rutinas |
| Interfaz multicapa | Introducida en 0.5.7 | Enlaces internos de mediciones, diseños, obras y conclusiones |

## Orden de trabajo después de 0.5.7.1

1. Completar C.1 para partidas reales: exportar snapshot inicial y una traza ordenada de llamadas, decisiones humanas y tiempo; el replay guionado con comparación SHA256 ya está implementado en 0.5.7.2.
2. Completar C.2: contrato único de `ActionResult`, desde `execute_action` hasta laboratorio, hábitos, novedades y proyectos. Prohibir deducciones desde cadenas de narrativa.
3. Establecer métricas de referencia y ejecutar comparaciones multisemilla antes de modificar las leyes físicas.
4. En 0.6: sustrato de propiedades físicas y variación entre muestras; conocimiento estructurado y procedimientos reutilizables.
5. En 0.7: termodinámica, luego clima y ciclos ambientales. En 0.8: políticas condicionales offline.

No mezclar cambios de leyes físicas con cambios de prompt; preservar el principio «el motor verifica, el LLM propone». Los cambios de documentación o versión no son pruebas de ejecución.

## Arquitectura introducida en 0.5.8

- **Agente**: `agent.initial_agent` genera el estado inicial; `person` contiene memoria, decisiones, proyectos y experiencia.
- **Escenario**: `scenarios.Scenario` define las condiciones iniciales, perfil de conocimientos y encuadre perceptivo, sin adjudicar efectos físicos.
- **Entorno**: `environments.Environment` / `IslandEnvironment` constituyen la frontera inicial de percepción y acciones verificables. Las reglas de `world.py` siguen invariantes.
- **Siguiente desacoplamiento**: quitar referencias a topología y agua de `nilo.py`, trasladar supervivencia a capacidades opcionales del entorno, separar visualizador del mapa y formalizar `ActionResult` tipado sin consumir narrativa.
- **Prueba de transferencia futura**: conservar una partida y memoria del agente al cambiar a un entorno pequeño de segunda implementación con efectos verificados, y comparar mediante replay. No asumir que un prompt por sí solo constituye un mundo nuevo.

## Separación complementaria en 0.5.8.1

- El cálculo de refugio/orilla y el mapa JSON dejan de estar en `Simulation` y quedan detrás de `Environment.surroundings` y `Environment.render_map`, implementados por `island_views.py` para isla_v1.
- Continuar con validación de acciones y rutas fuera del coordinador, sin modificar física hasta que las pruebas de regresión y replay garanticen equivalencia.
- Documento técnico actualizado: `docs/ARQUITECTURA_0581.md`.

## Hitos realizados en 0.5.8.2

- Se delegan en el adaptador del entorno la validación previa de pasos y la detección de acciones repetidas, sin cambiar la lógica original.
- Se recupera la jerarquía visual de materiales en el mapa; temas Bosque, Grafito y Terracota son exclusivamente visuales y persistidos localmente.
- Pendientes: resultados tipados de las acciones (C.2), navegación de procedimientos y reglas de supervivencia desacopladas, y prueba de transferencia a un segundo entorno simple.

## C.2 — avance 0.5.8.3

- Se introduce `ActionResult` y el recorrido estructurado entorno → mediciones → histórico → contexto del LLM, con evidencia numérica de ensayos efectivos.
- Sigue pendiente sustituir los retornos legados de `world.execute_action`, los eventos de navegación, la comparación/investigación y las rutinas que interpretan texto. No dar C.2 por cerrado.
- Se preservan pruebas y línea base de replay tras verificar el cambio intencional en el JSON persistido. Véase `docs/ARQUITECTURA_0583.md`.

## Autodiagnóstico 0.5.9.0 (primera etapa)

- Instrumentada la detección automática de cuatro invariantes inequívocos. Los reportes `bug-...` se abren como **solicitudes**, no como correcciones automáticas. Un fracaso físico ordinario no es un fallo del software.
- Paquete JSON de revisión exportable desde la UI con evidencia acreditada, propuesta, traza de acciones disponible y SHA256 del contenido.
- **Pendientes técnicos:** reproducción exacta por acción con snapshots de mundo/estado/RNG/reloj; experimentos adicionales que Nilo pueda realizar para contrastar sus sospechas; informes de evidencia comprensibles para el observador; casos de regresión cuando el observador decida implementar una corrección.
- **Gobernanza permanente:** Nilo observa, investiga y propone. El observador lee cada solicitud, la discute con ChatGPT y toma la decisión. Solo entonces, con autorización explícita, se diseña y modifica el código; las pruebas y la publicación son parte de esa implementación supervisada. Una aprobación conceptual en la interfaz no altera el motor ni autoriza una modificación automática.
- **Fuera de alcance:** agente desarrollador o revisor autónomo, aprobación de cambios sin el observador, generación e instalación automática de parches. Véase `docs/PROTOCOLO_REVISION_HUMANA.md`.

## Registro de sesiones — 0.5.9.1 implementado

- Cada ejecución crea una fila `engine_sessions` en su propio archivo SQLite con versión exacta, inicio/último guardado/cierre UTC, minutos del mundo, escenario, hash de manifiesto y commit Git si existe.
- Conteo real de proveedores/modelos por deliberación y conversación, sin imputar resultados a una configuración de respaldo que nunca respondió.
- **Sin reconstrucción ficticia:** sesiones previas a 0.5.9.1 quedan desconocidas; una interrupción conserva `ended_utc` nulo.
- Pestaña **Versiones** en el Diario. Tablas de metadatos fuera de la memoria del agente.
- **0.5.9.2 (siguiente):** hipótesis, predicción explícita, contraste con efecto físico medido y propiedades aún no demostradas.
- **0.5.9.3:** reconsideración estratégica justificada ante estancamiento/contradicción/ausencia de física, sin forzar intereses.
- **0.5.9.4:** comparación de corridas con mismo mundo/modelo, métricas observables y control de semillas/contexto.
- Cada hito es independiente y debe conservar control exclusivo del observador sobre nuevas leyes/cambios en código.

## Etapa cognitiva 0.5.9.2 implementada

- El LLM puede formular una hipótesis, efecto esperado y, cuando conozca una variable numérica, un valor observable con comparador.
- El motor escribe la predicción antes de ejecutar y la contrasta después con una métrica efectivamente emitida; **éxito de la acción no equivale a corroborar el objetivo**.
- Ejemplo de límite: contención de agua no proporciona información sobre pureza o filtración. Una variable ausente queda explícitamente sin medir, y Nilo recibe esa discrepancia para revisar sus planes.
- Predicciones previas y contrastes persisten con versiones en el archivo; no se inventa evidencia histórica. No se obliga a formular predicción para toda actividad.
- **0.5.9.3:** revisión estratégica ante contradicciones, estancamientos o hipótesis sin criterio verificable; conservar autonomía de elección.
- **0.5.9.4:** comparación de partidas/runs de referencia con semillas/modelos/contextos controlados, seguimiento de hipótesis y calidad de solicitudes de física.

## Interfaz 0.5.9.2.1

- Implementados puntos de notificación en solapas madre e hijas. Cuaderno, Novedades y Propuestas reflejan sus estados existentes; las demás categorías incorporan marcadores locales de revisión explícita.
- Mapa plegable con referencias; inventario y obras siguen visibles. Ajustes de modelo y consultas dentro de Configuración, junto con Avisos. Solapas conservan los colores previos.
- Diseño de escritorio adapta los paneles a la pantalla y deja scroll interno para historiales extensos; en móvil conserva scroll habitual.
- Siguiente hito **0.5.9.3**, revisión estratégica cognitiva, sin mezclarla con los cambios visuales de 0.5.9.2.1.

## Reparación de recolección 0.5.9.2.2

- Se elimina la ambigüedad entre acercamiento y extracción y la búsqueda genérica ante recursos desconocidos, identificadas en un run real de la 0.5.9.2.
- Alias inequívocos de terreno/material e inspección coherente (piedra/roca, mineral oscuro/afloramiento mineral).
- Diagnóstico verificable de acciones antiguas sin inventario añadido o con material incompatible; la hipótesis del agente permanece revisable por él.
- Regresiones del mismo seed 7321, CI y replay. Mantener **0.5.9.3** para revisión estratégica más general, no mezclar este arreglo con cambios de leyes.

## Recuperación de la hoja de ruta original 0.6–0.9 (registro histórico)

En conversaciones previas se propuso **0.6 física composicional y variación de materiales; 0.7 termodinámica seguida de entorno dinámico; 0.8 autonomía y procedimientos reutilizables; 0.9 transferencia de memoria/competencias de Nilo A a otro mundo; 1.0 experimentos de larga duración**. La secuencia era una **hipótesis de desarrollo**, no una promesa de versiones. El roadmap parcial previo no había conservado explícitamente **0.9** ni el horizonte **1.0**.

- [0.6, Issue #21](https://github.com/mxlzz/Nilo/issues/21): materiales, forma, composición y mecanismos verificables; las etapas de percepción y conocimiento ([#16](https://github.com/mxlzz/Nilo/issues/16), [#17](https://github.com/mxlzz/Nilo/issues/17)) pueden preceder a la física avanzada. Variación extraordinaria aplazada ([#18](https://github.com/mxlzz/Nilo/issues/18)).
- [0.7, Issue #22](https://github.com/mxlzz/Nilo/issues/22): primero pruebas térmicas aisladas; luego clima/ciclos. No mezclar leyes simultáneas o cambios de prompt sin controles.
- [0.8, Issue #23](https://github.com/mxlzz/Nilo/issues/23): evaluar qué capacidades de autonomía todavía faltan frente a agendas, hábitos y revisión ya desarrollados en 0.5.x.
- [0.9, Issue #24](https://github.com/mxlzz/Nilo/issues/24): transferir un mismo agente con memoria a **un segundo entorno realmente distinto**, medir transferencia y necesidad de nuevos ensayos. No es lo mismo que Nilo B.
- **1.0:** estabilidad de runs prolongados y análisis empírico, sin definir por adelantado un criterio fijo de publicación.

Documento de seguimiento y revisión a medida que avanza el experimento: [FUTUROS_CAMINOS.md](FUTUROS_CAMINOS.md). Antes de cada versión, revisar prioridades, dependencias y si la propuesta sigue siendo válida; registrar modificaciones o descartes con el motivo.
