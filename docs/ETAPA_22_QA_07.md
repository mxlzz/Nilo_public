# Nilo 0.7 — Etapa 22: QA transversal, cobertura y rendimiento

**Fecha:** 5 de noviembre de 2026 · **Rama:** \`refactor/0.7\` · **Base estable:** \`main\` / \`VERSION 0.6.4\`.

[Plan de etapas](PLAN_REESTRUCTURACION_NILO_07.md) · [Seguimiento](ESTADO_REESTRUCTURACION_07.md) · [PR #77](https://github.com/mxlzz/Nilo_public/pull/77) · [Issue #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Reauditoría de los huecos de pruebas

Se revisaron el árbol de suites y auditores de las etapas 00–21, el replay con baseline, el reloj y la fisiología, los contratos físicos de navegación/materiales, las operaciones de SQLite v5, la API local, la interfaz en assets y los tres laboratorios sobre el motor unificado.

La suite anterior contaba con 991 tests ejecutados. La nueva suite añade 17 pruebas transversales. El inventario estático de funciones \`test_*\` es un indicador de mantenimiento, **no** una medición de cobertura ni un conteo de pruebas exitosas. Se distingue de los casos realmente ejecutados por unittest.

**Hallazgos corregidos:**

- La operación física \`resolve_go\` convertía x/y con \`int\` pero no interceptaba \`OverflowError\` de infinito; un booleano podía pasar por el entero 0/1. Ahora devuelve un rechazo diagnóstico sin mutar terreno ni posición. No se alteraron las rutas válidas.
- \`update_needs\` aceptaba valores de duración como \`"12"\` al convertirlos silenciosamente con \`float\`. Se alineó su frontera con el contrato temporal numérico de \`core.clock\`: solo int/float finitos, sin booleanos ni cadenas. No cambiaron tasas ni límites corporales.
- La primera prueba de aislamiento del RNG global cambiaba el seed de Python durante la suite sin restaurarlo. Se ajustó con \`try/finally\` para mantener los tests independientes y evitar fallos por orden de ejecución.
- El subconjunto inicial instrumentado para cobertura dejaba casi sin ejecutar rutas de agenda, recursos y reloj, pese a existir sus suites. Se amplió la instrumentación a tests de estado, operaciones, tiempo, mundo, navegación, recursos, objetos, interacciones, fisiología, observación, deliberación, memoria, autonomía, persistencia, HTTP y laboratorio. El nuevo reporte presenta el universo de líneas **seleccionado** sin fingir cobertura total de Nilo.

## 2. Pruebas transversales nuevas

\`tests/test_qa_22.py\` introduce 17 pruebas y casos parametrizados, sin llamadas a LLM ni partidas de usuarios:

- **Topología:** 32 semillas de isla reproducibles y validación de la estructura; generación sin alterar el RNG global; 16 semillas con rutas comparadas contra un BFS de referencia independiente.
- **Conocimiento espacial:** alterar casillas ocultas no cambia rutas ni selección de frontera conocida, ni el consumo de entropía del agente.
- **Entradas adversas:** coordenadas no finitas, booleanas, cadenas fuera de rango y objetos no numéricos se rechazan antes de consultar rutas.
- **Conservación:** 100 transferencias aleatorias con cantidades y existencias conocidas conservan la suma origen+destino.
- **Necesidades:** 25 series de 40 cambios de tiempo, energía/hidratación/nutrición siempre acotadas; sin consumo de comida o bebida por el motor si Nilo no ha delegado tal decisión.
- **Temporalidad:** los mismos diez segundos reales ejecutados en un único tick o particionados en dos producen el mismo resultado físico en ocho semillas; pausa congela reloj y RNG.
- **Memoria y observatorio:** leer vistas, registros y snapshots repetidamente no escribe mundo, RNG o SQLite.
- **Historial:** 400 entradas grabadas en lote o en diez escrituras producen idéntico orden e IDs; fallo inyectado después de escribir en el archivo revierte DB y cachés y permite un reintento sin duplicación.
- **Continuidad:** ejecución prolongada sobre Simulation, guardado y reapertura con tiempo, inventario y posición preservados; backup con investigaciones/proyectos/IDs y RNG exacto; dos mundos independientes no comparten memoria.

Las suites focalizadas 07–21 siguen ejecutándose separadamente en CI, además de la regresión total. La reproducción \`reproducir.py\` exige el fingerprint \`expected_fingerprint\` guardado en \`tests/fixtures/replay_basico.json\`, y se contrasta también entre procesos con distintos \`PYTHONHASHSEED\`.

## 3. Cargas técnicas reproducibles

\`tools/benchmark_qa_22.py\` mide, en Linux GitHub Actions y sin proveedor LLM:

| Fixture | Construcción y búsqueda de mundos | Historial | Tiempo simulado | HTTP local |
| --- | --- | --- | --- | --- |
| QA transversal | 24 semillas / hasta 10 rutas por mundo | 3.000 registros + 100 añadidos | 100 ticks x20 minutos = 2.000 min | 36 GET |
| QA prolongada | 48 semillas / hasta 10 rutas por mundo | 8.000 registros + 100 añadidos | 576 ticks x20 minutos = 11.520 min = 8 días | 90 GET |

Para ambos fixtures se compara el orden e identidad de filas SQLite, se prueba lectura \`public_state\` sin escrituras, se realiza backup consistente con WAL, se abre la copia con RNG exacto y se mide latencia p50/p95, tiempos de escritura y memoria máxima trazada con \`tracemalloc\`. No se establecen umbrales arbitrarios en milisegundos: el rendimiento puede variar según la máquina y los datos.

**Importante:** ocho días de tiempo simulado con \`think\` sustituido por una función local constituyen una carga técnica. No equivalen a ocho días de decisiones autónomas del LLM: eso se estudiará en etapa 23.

## 4. Cobertura por líneas y trazabilidad

Se añadió \`tools/cobertura_qa_22.py\`, que usa únicamente \`sys.settrace\` y \`dis.findlinestarts\` de Python estándar. Mide líneas realmente ejecutadas en 16 módulos seleccionados de world, clock, physiology, autonomy, cognition, agent, storage, API, security y laboratorio.

La medición se obtiene ejecutando suites declaradas contra el motor real. El reporte adjunta por módulo: líneas ejecutables, alcanzadas y porcentaje. **No es cobertura de ramas ni de todo el repositorio**; las acciones en subprocess Node o Python no quedan instrumentadas por este proceso. Los porcentajes no deben compararse con otra cobertura de universo diferente.

\`tools/auditar_qa_22.py\` conserva un inventario reproducible de cantidad de archivos, funciones \`test_*\`, dominios y checks CI; informa explícitamente que el conteo de definiciones AST no reemplaza los resultados de ejecución.

Los reportes se generan en cada CI como archivos:
\`qa_22_inventory.json\`, \`qa_22_benchmark.json\`, \`qa_22_stress.json\`, \`qa_22_coverage.json\`. Se publican en el artifact **nilo-qa-22** de GitHub Actions, sin guardar fixtures personales ni artefactos temporales en el repo.

## 5. Matriz de cambios intencionales frente a 0.6.4

| Subsistema | Regla baseline que se conserva | Cambio deliberado 0.7 | Control de QA |
| --- | --- | --- | --- |
| Isla y física | Generación determinista; mismas leyes de terreno | Módulos y contratos separados, sin nuevo entorno físico | Topología multi-semilla, BFS independiente, reproducción con huella fija |
| Navegación | Mismo recorrido y fronteras sobre terreno conocido | Rechazo seguro de entradas no finitas/booleanas | Metamorfismo de casillas ocultas y casos adversos |
| Recursos | No se crea material; transferencias contabilizadas | Inventario/registros con validación explícita | 100 transferencias y regresión 10–12 |
| Necesidades | Mismas tasas fisiológicas | Mensajes cualitativos, acciones voluntarias y tipo estricto de duración | 25 secuencias, reserva acotada, regresión 13 |
| Ciclo de vida | Objetivos no se comprueban por narrativa | Cierre por evidencia, agenda/hábitos y reconsideración separadas | Regresión 16–17, rollback y no duplicación |
| Memoria/LLM | Sus objetivos siguen perteneciendo a Nilo | Contexto con procedencia y puerta LLM centralizada | Regresión 14–16, sin APIs reales en QA |
| SQLite v5 | Schema y IDs de mundos históricos | Escrituras atómicas, backup WAL, archivo incremental | Reapertura, inyección de fallo, copia verificada e histórico de seis saves |
| API y observatorio | Lecturas no ejecutan acciones físicas | API v1, barrera local de seguridad y vista sin identificadores sensibles | Regresión 19, lecturas repetidas sin mutar SQLite/RNG |
| Interfaz | Aspecto y renderizadores de la vista original | CSS y JS desacoplados con paridad byte a byte | Regresión 20, ZIP y comprobación HTML/DOM |
| Laboratorio | Mismas leyes de ejecución | Sandbox sobre Simulation, perfiles reversibles, copias seguras | Regresión 21, estados y recursos aislados |

Esta matriz separa **paridad deliberada** de **diferencias funcionales intencionales**. El replay de decisiones fijadas es una puerta de continuidad, no certificación de eficacia autónoma.

## 6. Puerta de salida y reservas

La validación definitiva requiere: CI total verde, fixture de 8 días concluido, artifact con inventario/benchmark/cobertura, reproducción determinista y ZIP portátil, más compatibilidad histórica sobre seis SQLite sintéticos. Los resultados cuantitativos, SHA de CI y estado final se registran después de verificar estas condiciones.

Limitaciones que siguen abiertas: no hay pruebas de navegación visual manual en todos los dispositivos, ni long-run con Gemini/Groq reales, ni un porcentaje global de líneas/ramas del sistema. Corresponden respectivamente a verificación final de interfaz, evaluación autónoma de etapa 23 y eventual ampliación continua de QA. No se editaron partidas personales ni se fusionó \`main\` durante esta etapa.
