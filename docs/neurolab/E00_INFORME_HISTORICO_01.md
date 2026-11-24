# E00 — Arqueología técnica: ejecución documental 01

**Fecha de trabajo:** 2026-11-20 · **Evidencia:** lectura directa de páginas identificadas abajo · **Código/experimentos:** ninguno durante E00. · **Estado:** E00.01 verificada; E00.02–E00.10 analizadas con lagunas declaradas; G00-H (réplica histórica) **abierta**; G00-N (prototipo mínimo propio) puede habilitarse con decisiones explícitas.

## 1. Inventario verificable de fuentes — E00.01

| ID | Tipo | Fuente y alcance real | Resultado |
|---|---|---|---|
| SRC-01 | P1: texto técnico de autores | [Grand, Cliff y Malhotra, *Creatures: Artificial Life Autonomous Software Agents for Home Entertainment*](https://eem.foo/ccarchive/Sites/fp.cyberlifersrch.plus.com/articles/agents_%2797_paper.htm); publicado/presentado 1996–1997; arquitectura C1, Tables 1–3, aprendizaje, decisión | **Accesible y leído**. Contiene arquitectura y ecuaciones esquemáticas, no todos los parámetros de genoma original. |
| SRC-02 | S1: guía especializada posterior | [Home Sweet Albia, *Creatures 1 Brains*](https://zenzoa.com/creatures/c1-brains.html), 30/07/2022; secuencia de ticks, SVRules, migración, decays | **Accesible y leído**. Guía inversa; no equivale a código fuente original. |
| SRC-03 | S1: experimentación C1 histórica | [Creatures Developer Resource, *Brain Lobes*](https://double.nz/creatures/brainlobes/intro.htm), nota de 08/10/1999; editor genético y experimentación | **Accesible y leído**. Autor declara parámetros sin resolver. |
| SRC-04 | S1: análisis moderno | [Alan Zucconi, *The AI of Creatures*](https://www.alanzucconi.com/2020/07/27/the-ai-of-creatures/), 27/07/2020 | **Accesible, revisada**; revisión pedagógica, no origen de cifras verificadas si hay primaria. |
| SRC-05 | S2: implementación abierta incompleta | [openc2e README](https://github.com/openc2e/openc2e) | **Accesible y verificado**; README declara que Norns C1/C2 no funcionan aún, por tanto no se usa como oráculo. |
| SRC-06 | P1: notas de diseño originales del creador | [Steve Grand, *I Am Ron's Brain*](https://web.archive.org/web/20071208173623/fp.cyberlifersrch.plus.com/creaturesarchive/braindesc.htm), última revisión declarada 08/05/1995 | **Accesible y leído**. DESARROLLO PREVIO al lanzamiento, no representa necesariamente arquitectura final. |
| SRC-07 | S1: experimentación con genoma original | [CDR, *Tutorial One*](https://double.nz/creatures/tutorial1/tutorial1ss.htm); usa `dad1.gen`, presenta posiciones, dimensiones y lista de lóbulos estándar | **Accesible y leído**; justifica tabla de 952 posiciones, pero el archivo binario no fue adquirido/hasheado. |
| SRC-08 | S1: vocabulario histórico | [CDR, *State Variable Rules*](https://double.nz/creatures/genetics/svrules.htm); separa comandos C1 y C2 | **Accesible y leído**; reconoce incertidumbres en algunos opcodes. |

**Alcance de validación:** se verificaron existencia, autoría/fecha declarada, contenido y compatibilidad con C1 en páginas publicadas. No se descargaron ni ejecutaron binarios, no se inspeccionó el ejecutable C1 y no se realizaron pruebas en un Norn vivo. Una fuente primaria puede describir el modelo sin certificar cada detalle del binario final.

## 2. Edición y topología — E00.02 / E00.03

**Referencia elegida provisional:** *Creatures 1* original (1996), genoma `dad1.gen` descrito por SRC-07. No hay hash de archivo, SKU/build exacto ni instalación propia verificada. Por tanto **E00.02 parcialmente resuelta**, no afirma genotipo bit a bit.

| Índice C1 | Lóbulo | Posición (x,y) | Ancho×alto | Neuronas | Papel |
|---:|---|---|---|---:|---|
| 0 | Perception | (4,13) | 7×16 | 112 | Agregación de estímulos |
| 1 | Drive | (34,30) | 8×2 | 16 | Necesidades |
| 2 | Source | (15,24) | 8×5 | 40 | Categorías de objetos |
| 3 | Verb | (37,24) | 8×2 | 16 | Verbos |
| 4 | Noun | (21,3) | 20×2 | 40 | Sustantivos |
| 5 | General Sense | (32,34) | 8×4 | 32 | Otras percepciones |
| 6 | Decision | (53,15) | 1×16 | 16 | Acciones posibles |
| 7 | Attention | (44,30) | 5×8 | 40 | Elección de foco |
| 8 | Concept | (12,6) | 40×16 | 640 | Detectores de patrones |
| | **Total** | | | **952** | |

**Evidencia:** SRC-07, tabla “Overview”. El artículo de los autores (SRC-01) utiliza «aproximadamente 1.000 neuronas, nueve lóbulos y unas 5.000 sinapsis». 952 es **suma de posiciones nominales de los 9 lóbulos de un genoma descrito**, no garantía de que estén todas activas ni conteo de cualquier Norn mutado. SRC-03 documenta que algunos lóbulos especiales se implementan en el ejecutable.

## 3. Neurona — E00.04

### Elementos con apoyo histórico

- `state`: estado de activación; `threshold`: umbral; `output`: salida; `rest state`: punto de retorno; `relaxation rate`: velocidad de retorno; `input gain/attenuation`; `SVRule`: pequeña expresión codificada por genoma. SRC-01 Tabla 1 y SRC-03.
- SRC-03 y SRC-02 trabajan con valores tipo byte en `[0,255]`, no floats sin límites.
- Las entradas en dendritas llegan a neuronas *destino* desde clases 0/1 de un lóbulo *origen*; pueden afectar excitación/inhibición.
- En general `state` se computa con SVRule sobre estado/inputs; luego se calcula la salida y se relaja estado hacia reposo. Fuente primaria SRC-01.

### Contradicción NO RESUELTA: salida sobre umbral

- **P1 (SRC-01 Tabla 1):** `output = state if state > threshold else 0`.
- **S1 (SRC-02, Updating Input/Output Lobes; SRC-03, Cell Body):** `output = state - threshold if state > threshold else 0`.

No es aceptable declarar equivalentes ambas ecuaciones. Para `state=160, threshold=40`, la primera da **160**, la segunda **120**. Puede tratarse de un error del paper, una diferencia entre prototipo y ejecutable, o interpretación errónea de guías; **no se verificó cuál ejecuta C1**. NeuroLab puede probar ambas como modos explícitos, sin declararlos fieles históricamente.

### SVRule — esquema documentado

Según SRC-02 y SRC-08, C1 emplea opcodes `0..27` para: BLANK, constantes 0/1/64/255, cuatro CHEM, STATE, OUTPUT, THRESHOLD, TYPE0/TYPE1, ANDTYPE0/ANDTYPE1, INPUT, CONDUCT, SUSCEPTIBILITY, STW, LTW, STRENGTH, TRUE, PLUS, MINUS, TIMES (/256), INCR y DECR.

**No mezclar con C2:** `CONST32`, `CONST128`, `FALSE`, `random`, `move twrds`, `leak in/out` documentados como C2; no usarlos para implementar C1.

Ejemplos de SRC-01: `STATE PLUS TYPE0`; `STATE PLUS TYPE0 MINUS TYPE1`; `ANDTYPE0`; `STATE PLUS TYPE0 TIMES CHEM2`. **Ambigüedad:** la precedencia exacta, saturación intermedia, codificación de operandos y manejo de opcodes inválidos no están suficientemente verificados desde fuente primaria.

## 4. Sinapsis — E00.05

Fuente P1 SRC-01 Tabla 3 y SRC-06:

- `STW` controla intensidad efectiva de propagación; `LTW` es reposo a largo plazo de STW.
- Susceptibilidad al refuerzo: aumenta cuando participa en decisión y decae después, permitiendo un refuerzo retrasado, con atribución imperfecta.
- Fuerza/fortaleza estructural determina si la dendrita se desconecta y migra a otra fuente.
- Reglas SVRule pueden modular susceptibilidad, refuerzo, ganancia y pérdida de fortaleza.
- Cálculo esquemático de señal `source_output * STW / 255` respaldado como aproximación por SRC-03; la guía SRC-02 da rutina discreta de actualización de susceptibilidad y pesos, pero **no hay trazabilidad al código binario original**.
- `STW` se relaja hacia `LTW`; `LTW` cambia más lentamente hacia `STW`. No hay coeficientes universales: los parámetros están genéticamente controlados.
- SRC-01 afirma que un mecanismo adicional competitivo de migración por “fittest” se implementó pero quedó desconectado. **No implementarlo como C1 activo** sin confirmación.

**Cuidado temporal:** SRC-06 (1995) plantea reciclaje al extinguir fortaleza y peso. SRC-02 (2022) describe migraciones C1 más detalladas. No afirmar que ambas descripciones documentan exactamente el mismo criterio/fase.

## 5. Reloj y decisión — E00.06

**Secuencia derivada de SRC-02 (secundaria, todavía no contrastada en ejecutable):**
1. Actualizar entradas Drive/Source/Verb/Noun/General Sense (excepto Perception).
2. Copiar señales marcadas perceptibles hacia Perception según reglas especiales.
3. Actualizar Perception.
4. Actualizar lóbulos de salida: Decision, Attention y Concept, con aplicación de SVRule, umbral, relajación, refuerzo y migración según su clase.
5. En lóbulos marcados `winner-takes-all`, conservar únicamente el máximo; desempate exacto no establecido.

**Evidencia P1 SRC-01:** Concept detecta conjuntos de señales, Decision (16 células) integra excitación e inhibición; cuando cambia el ganador se invoca un script de acción. Atención selecciona un objeto; el modelo considera un foco cada vez.

**Pendiente:** orden exacto de actualización entre Concept, Decision y Attention para evitar introducir una dependencia incorrecta de valores nuevos/anteriores; el guía enumera una agrupación y no basta para certificar las reglas de snapshots. Tampoco hay frecuencia exacta del tick históricamente validada; no inferirla a partir del «about 4?» del tutorial de terceros.

## 6. Refuerzo, instintos y límites — E00.07

SRC-01 afirma que los cambios en necesidades (drives) generan químicos de recompensa o castigo: subir drive puede penalizar y reducirlo premiar, con efectos dependientes del estado fisiológico. SRC-06 explica el compromiso de crédito: la susceptibilidad decae y puede reforzar acciones equivocadas cuando la recompensa llega muy tarde. El aprendizaje fue pensado para control de conducta, no planificación causal general.

**Excluido en NeuroLab inicial:** bioquímica, cuerpo, drive, placer/dolor. El laboratorio administra una señal abstracta y fija de refuerzo que no debe confundirse con la química de los Norns.

**Distinción de épocas muy importante:** SRC-06 (1995) describe un diseño inicial de representación jerárquica binaria (unidades no asignadas de dos dendritas); SRC-01 (1996–97) describe Concept como detectores de hasta cuatro entradas y sinapsis migratorias. **No unir estos dos estados históricos en un mismo algoritmo sin evidencia**.

## 7. Matriz de certeza — E00.08

| Claim | Fuente | Estado para C1 | Qué falta |
|---|---|---|---|
| CL-001: Norn estándar, 9 lóbulos, 952 posiciones | SRC-07 y SRC-01 (≈1000) | Alta para descripción de genoma de tutorial | `dad1.gen` y hash |
| CL-002: neuronal state/threshold/rest/SVRule | SRC-01 Tabla 1 | Alta conceptual | Escalas/cálculo exacto |
| CL-003: bytes 0–255 | SRC-03, SRC-02 | Moderada; experimental histórico | inspección binario/datos C1 |
| CL-004: dos clases de dendritas | SRC-01 Tabla 1, SRC-02 | Alta | topología original genoma |
| CL-005: threshold output `state` o `state-threshold` | SRC-01 vs SRC-02/03 | **Contradicción abierta** | ejecución C1 o ingeniería inversa confiable |
| CL-006: STW/LTW/susceptibilidad/fuerza | SRC-01 Tabla 3 | Alta conceptual | coeficientes iniciales/precisión |
| CL-007: Concept 1–4 inputs, detección conjunta | SRC-01 sección Brain Model | Alta para modelo expuesto en 1996–97 | distribución C1 real |
| CL-008: Decision 16 con WTA | SRC-01 y SRC-07 | Alta para modelo | desempates/frecuencia exacta |
| CL-009: reward vía modificaciones de drives | SRC-01, SRC-06 | Alta conceptual | genoma de reacciones |
| CL-010: migración especial competitiva desactivada | SRC-01 sección Migration | Alta en modelo descrito | versión binario posterior |
| CL-011: algoritmo byte exacto de decay de guía | SRC-02 appendix | Moderada | contraste primario/ejecutable |
| CL-012: orden del tick de guía | SRC-02 Brain in Action | Moderada | contraste primario/ejecutable |
| CL-013: genoma `dad1.gen` disponible para análisis | SRC-07 lo menciona | Nombre identificado, archivo **no inspeccionado** | hash/edición/licencia |
| CL-014: diseño binario jerárquico 1995 = final de C1 | SRC-06 vs SRC-01 | **No comprobado; probablemente cambia** | cronología genoma |

## 8. Especificación N mínima (propuesta experimental explícita) — E00.09

Para desbloquear una prueba neuronal, **no se exige fingir que la ecuación exacta de C1 está resuelta**. En la línea N se proponen parámetros propios:

- Dominio neuronal: números enteros de 0–255, saturados; ticks discretos.
- `output_mode` configurable: `state` (según paper) o `above_threshold` (según guías). Por defecto experimental `above_threshold`; no se afirma fidelidad.
- `state_pre = clamp(state_old + type0_signal - type1_signal, 0, 255)` para una SVRule **seleccionada**, no interpreter universal.
- `output = state_pre - threshold` si `state_pre>threshold`, de otro modo 0 (modo `above_threshold`).
- `state_next = rest + floor((state_pre - rest) * (256 - relax_coeff) / 256)` para `state_pre>=rest`; para el otro sentido usar forma simétrica bien especificada. Esta es **ecuación de NeuroLab**, no recreación histórica del decay.
- `type0_signal = sum(floor(source_output * weight / 255))`, analogía del peso de SRC-03, con saturación posterior.
- Entradas externas directas a neuronas del tipo `input`; las neuronas de cómputo toman señales de sinapsis. Salida y nuevo estado se calculan desde una copia del estado anterior dentro de un tick, para evitar dependencias accidentales del orden de iteración. **Decisión de diseño propia**, no copia de un tick C1.
- Hasta E03, sin refuerzo ni STW/LTW: peso sináptico fijo (0..255), sin migración ni aleatoriedad. Separación explícita en el código.
- Si se usa una red con 6 unidades: dos entradas, dos conceptos, dos decisiones; no se declara réplica exacta de ninguna subred del Norn.

**Oráculos manuales preliminares (modo `above_threshold`, descanso inmediato `relax_coeff=0` = sin cambio):**
1. `state_old=30`, `threshold=40`, `type0=20`, `type1=0` ⇒ `pre=50`, `output=10`, `next=50`.
2. `state_old=120`, `threshold=20`, `type0=0`, `type1=50` ⇒ `pre=70`, `output=50`, `next=70`.
3. `state_old=150`, `threshold=40`, `type0=0`, `type1=0`, `rest=0`, `relax_coeff=128` ⇒ `pre=150`, `output=110`, `next=75`.
4. `state_old=160`, `threshold=40`, modo paper `state` ⇒ `output=160`; modo secundario `above_threshold` ⇒ `output=120`.

Una implementación necesita tests independientes para demostrar estos resultados.

## 9. Revisión crítica — E00.10

- No introducir operadores C2/C3 ni asumir que todos los lóbulos se comportan como neuronas genéricas: algunos son especiales.
- No considerar autobiografía de diseño de 1995 una medición del ejecutable de 1996.
- No usar `openc2e` como referencia de comportamiento C1 verificado, dado que su soporte de Norns originales es incompleto.
- No presentar 952 como cardinal universal de genomas variables.
- No equiparar aprendizaje por refuerzo con inteligencia general o comprensión.
- El modelo histórico tiene sesgo conductista y crédito diferido imperfecto, reconocido expresamente por Grand.

## 10. Veredicto honesto y siguiente paso

| Subtarea | Resultado documental |
|---|---|
| E00.01 | **VALIDADA**: ocho fuentes accesibles e identificadas; cinco previstas más tres relevantes adicionales |
| E00.02 | **PARCIAL**: `dad1.gen` elegido como referencia, sin archivo/hash/edición |
| E00.03 | **VALIDADA para descripción documental** de 952 posiciones; pendiente cotejo con binario |
| E00.04 | **PARCIAL**: variables y ejemplos establecidos; ecuación de umbral contradicha |
| E00.05 | **PARCIAL**: variables y dirección del aprendizaje establecidas; parámetros exactos no |
| E00.06 | **PARCIAL**: secuencia de guía, falta orden verificado del ejecutable |
| E00.07 | **VALIDADA conceptual**: refuerzo a través de drives documentado, se excluye en N |
| E00.08 | **VALIDADA como inventario de certeza**, no resolución de dudas |
| E00.09 | **VALIDADA para la línea experimental N solamente**, fórmula propuesta no original |
| E00.10 | **VALIDADA como auditoría documental**, no auditoría del ejecutable |

**Puerta G00-H:** ABIERTA. Faltan genoma/verificación del algoritmo byte a byte. Puede continuarse la arqueología en paralelo.

**Puerta G00-N:** habilita **solamente** E01 como unidad neuronal de NeuroLab, bajo reglas explícitamente experimentales y comprobables, conservando las incertidumbres históricas. No habilita afirmar una réplica histórica.

**Siguiente acción técnica propuesta:** E01.01 → E01.09 en `experiments/neurolab/`, con tests manuales, determinismo y checkpoint. Si una prueba falla, no avanzar a E02.
