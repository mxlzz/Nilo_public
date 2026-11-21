# NeuroLab — fuentes y reconstrucción histórica de Creatures 1 (C1)

**Objetivo:** obtener una especificación *implementable y comprobable* de los mecanismos relevantes de la mente de los Norns originales, distinguiendo evidencia documental de hipótesis y adaptaciones propias.

## 1. Jerarquía de evidencia

- **P1 — Primaria técnica:** publicaciones originales, documentación de desarrolladores, manuales/genoma/herramientas originales fechados y verificables.
- **P2 — Código o datos de época:** archivos de la instalación original y genomas con procedencia demostrable, herramientas oficiales, registros reproducibles de ejecución. Interpretar en el contexto de la versión.
- **S1 — Secundaria técnica:** guías de terceros que citan fuentes y muestran reglas, ejemplos y límites.
- **S2 — Comunidad / reproducción:** wikis, proyectos emuladores, análisis posteriores. No tratar una reproducción incompleta como la verdad del C1.
- **H — Hipótesis propia:** extrapolación necesaria para un diseño mínimo, siempre rotulada y contrastable.

**Registro por afirmación:** `claim_id`, afirmación exacta, elemento (lóbulo/neurona/sinapsis/genoma/sueño), fuente, localizador interno (página/sección/cita breve), edición/versión, evidencia `P1/P2/S1/S2/H`, nivel de confianza argumentado, evidencias que la contradicen, consecuencias de implementación, estado `confirmado/provisional/abierto`.

No usar “952”, “nueve lóbulos”, “STW/LTW”, “SVRule” o una ecuación concreta como comprobación de fidelidad histórica por sí mismos. Toda cifra de arquitectura se verifica frente al genoma de referencia y se delimita a ese genoma.

## 2. Fuentes iniciales — no representan verificación de todos sus detalles

| ID | Referencia | Estudio esperado | Advertencia |
|---|---|---|---|
| SRC-01 | [Grand, Cliff y Malhotra — paper de Creatures / Agents '97](https://eem.foo/ccarchive/Sites/fp.cyberlifersrch.plus.com/articles/agents_%2797_paper.htm) | Arquitectura, modelos de plasticidad, fisiología y conducta | Distinguir mecanismos propuestos de los ejecutados en C1 |
| SRC-02 | [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html) | Detalles de SVRules, neuronas, dendritas y fases del tick | Guía secundaria; confrontar con fuente primaria |
| SRC-03 | [Brain Lobes — recursos históricos](https://double.nz/creatures/brainlobes/intro.htm) | Lóbulos y editor genético | Confirmar versión C1, no confundir con C2/C3 |
| SRC-04 | [Alan Zucconi: The AI of Creatures](https://www.alanzucconi.com/2020/07/27/the-ai-of-creatures/) | Reconstrucción pedagógica moderna | Es interpretación secundaria |
| SRC-05 | [openc2e](https://github.com/openc2e/openc2e) | Contraste de organización e implementación | README declara soporte incompleto para criaturas C1/C2; **no** fuente normativa de activación C1 |

Fuentes adicionales se agregan **solo cuando resuelvan una laguna concreta**, guardando URL estable y evidencia.

## 3. Inventario de lo que se debe reconstruir, sin presuponer resolución

### H-01: Genoma y topología
- Identificar archivo/genoma estándar de referencia, su versión, hash y origen lícito.
- Tabla de lóbulos: ID histórico, tamaño, tipo, entradas, salidas, conexiones y función documentada.
- Determinar si `952` describe neuronas disponibles, activas, máximos o unidades nominales.
- Diferenciar estructura codificada genéticamente de conectividad construida o modificada durante la vida.
- Identificar tamaño real de repertorio de acciones del C1, propiedades de atención e influencia de entradas lingüísticas.

### H-02: Neurona elemental
Para cada clase de neurona, determinar si existen:
- `state` / estado interno; `output`; estado de reposo; umbrales; tasa/función de relajación; indicadores químicos; marcas temporales.
- Dominio y representación numérica: bytes, enteros, flotantes, rango, saturación, redondeo y overflow.
- Regla exacta `SVRule`: operadores, orden de precedencia, entradas accesibles, secuenciación.
- Orden de lectura/escritura: sincrónico por copia de estado anterior vs secuencial *in place*; dependencia del orden de lóbulos/neurona.
- Comportamiento ante entradas ausentes, inactivas, señal simultánea y valores fuera de rango.

### H-03: Sinapsis y propagación
- Variables `STW`, `LTW`, `susceptibility`, `strength` (o nomenclatura realmente usada por C1); valores iniciales y límites.
- Signo excitador/inhibidor y forma de acumulación de entradas.
- Reglas exactas para atrofia, reforzamiento, decrecimiento, estabilización y migración.
- Cronología de crédito diferido: cuándo se marca elegibilidad y cuándo se consume refuerzo.
- Restricciones de número/destino de dendritas, competencia y reconexión.
- Condiciones de sueño e instintos **solo si** se verifica su influencia en la dinámica original.

### H-04: Reloj cerebral y selección de decisión
- Qué constituye un tick cerebral, frecuencia y desacoplamiento del reloj del juego.
- Etapas de procesamiento, propagación, aprendizaje y elección.
- `winner-takes-all`: empates, falta de salida, oscilaciones, inhibición, persistencia de decisión.
- Demarcar la acción seleccionada y la intervención de scripts de objetos; el cerebro no era un motor físico genérico.

### H-05: Entradas y refuerzo
- Categorías y escalas de estímulos perceptivos/verbales/drives.
- Cómo se calculaba el refuerzo químico a partir de diferencias en drives.
- Diferenciar refuerzo genético (instintos), refuerzo químico y recompensa del laboratorio diseñado por nosotros.
- Cómo se desambiguaba crédito cuando una consecuencia seguía a varias acciones.

## 4. Plantilla obligatoria de una regla a implementar

| Campo | Descripción |
|---|---|
| `rule_id` | Identificador versionado |
| `source_claim_ids` | Afirmaciones que la respaldan |
| `status` | histórica confirmada / reconstruida / propia / desconocida |
| `state_before` | Variables de entrada y dominio |
| `transition` | Pseudocódigo o fórmula inequívoca |
| `state_after` | Variables que se actualizan |
| `order` | Orden dentro de un tick |
| `edge_cases` | Cero, signo, saturación, empates, entradas ausentes |
| `example_manual` | Estado inicial y resultado calculado a mano |
| `test_oracle` | Fuente del resultado esperado, no derivada del mismo código |

**Prohibición metodológica:** implementar una fórmula “parecida” y etiquetarla de histórica por producir una curva plausible. Si el registro original no permite establecerla, llevarla a la línea experimental N como decisión explícita.

## 5. Preguntas abiertas iniciales (E00)

- [ ] ¿Cuál es la edición exacta de C1 que se tomará como referencia?
- [ ] ¿Cómo se accede legalmente a un genoma C1 y a herramientas necesarias para contrastarlo?
- [ ] ¿Qué operaciones exactas admiten SVRules en C1?
- [ ] ¿Qué fases del tick leen el estado anterior y cuáles leen el actualizado?
- [ ] ¿Cómo se codificaban STW/LTW y sus escalas?
- [ ] ¿Qué reglas de migración estaban efectivamente habilitadas?
- [ ] ¿Qué refuerzos ocurrían durante el sueño y cuáles durante la vigilia?
- [ ] ¿Qué variables no son identificables sin ejecutar el programa o leer datos originales?

Al cerrar E00, cada duda debe quedar **resuelta con fuente o declarada limitación**; no inventar lo que falta.
