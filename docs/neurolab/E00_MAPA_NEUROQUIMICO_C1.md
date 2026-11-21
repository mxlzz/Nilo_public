# E00-H03 — conexiones genéticas entre cerebro y química de refuerzo

**21/11/2026.** Segunda inspección directa del `dad1.gen` extraído del CD por el usuario; no se ha ejecutado Creatures. Los genomas binarios no se publican en este repositorio. Comparación general en [E00_GENOMA_ORIGINAL_COMPARACION.md](E00_GENOMA_ORIGINAL_COMPARACION.md).

## 1. Qué se pudo verificar directamente

La secuencia de registros C1 aporta **43 genes de receptores** `type=1/subtype=0`, **27 de emisores** `1/1` y **58 de reacciones químicas** `1/2`. El receptor/emisor de C1 tiene un cuerpo de **8 bytes** y la reacción de **9 bytes**, después del marcador `gene` y de la cabecera de 6 bytes.

Al filtrar los genes que apuntan a `organ=0` (cerebro), el genoma aportado contiene **seis receptores** y **tres emisores**. Campos de los genes de receptor: `[organ, lobe, locus, chemical, threshold, nominal, gain, flags]`; para emisiones, `[organ, lobe, locus, chemical, threshold, sample_rate, gain, flags]` como lectura *estructural provisional* basada en C1. La importancia biológica de cada valor requiere contraste adicional.

### Receptores del cerebro

| Índice de gen (base 0) | Lóbulo | Locus | Químico observado (ID) | Umbral | Nominal | Ganancia | Flags |
|---:|---|---:|---:|---:|---:|---:|---:|
| 88 | Decision (6) | 13 | **49** | 0 | 0 | 255 | 0 |
| 89 | Decision (6) | 14 | **50** | 0 | 0 | 255 | 0 |
| 127 | Decision (6) | 15 | **53** | 0 | 16 | 255 | 1 |
| 128 | Decision (6) | 16 | **70** | 0 | 16 | 255 | 1 |
| 129 | Concept (8) | 13 | **51** | 0 | 0 | 255 | 0 |
| 126 | Concept (8) | 14 | **52** | 0 | 4 | 255 | 1 |

La documentación C1 de loci de cerebro identifica sucesivamente `Chemical n` para los índices que aquí aparecen 13–16; **la correspondencia propuesta de trabajo** es `locus 13=CHEM0`, `14=CHEM1`, `15=CHEM2`, `16=CHEM3`. Se debe verificar este offset exacto al implementar una interpretación del genoma en el motor, pero permite formular hipótesis explícitas.

**Consecuencia para Decision (ver E00-H02):**
- Clase 0 de dendritas se refuerza mediante `CHEM0` → asociado al químico numerado 49 por receptor.
- Clase 1 se refuerza mediante `CHEM1` → asociado al químico 50.
- La pérdida de fortaleza de clase 0 depende de `CHEM2` → receptor de químico 53.
- La pérdida de fortaleza de clase 1 depende de `CHEM3` → receptor de químico 70.
- El refuerzo es parte de una red biquímica concreta y **no equivale** a sumar ±16 a una sinapsis, como hace nuestro control E03.

**Consecuencia para Concept:**
- Clase 0 tiene SVRule de ganancia de fortaleza `OUTPUT TRUE CHEM0`; con la correspondencia propuesta, depende del químico 51.
- Pérdida de fortaleza `CHEM1`; depende del químico 52.
- A diferencia de Decision, sus SVRules de susceptibilidad y refuerzo de peso están vacías en la configuración genómica extraída; el papel de Concept es principalmente reconocer y reorganizar patrones.

### Emisores con origen en cerebro

| Índice de gen | Origen genético | Locus | Químico emitido (ID) | Umbral | Muestreo | Ganancia | Flags |
|---:|---|---:|---:|---:|---:|---:|---:|
| 123 | Concept (8) | 1 | **52** | 0 | 1 | 255 | 1 |
| 124 | Decision (6) | 1 | **53** | 0 | 1 | 255 | 1 |
| 125 | Decision (6) | 2 | **70** | 0 | 1 | 255 | 1 |

Estos emisores y receptores muestran circuitos de retroalimentación **plausibles** entre actividad cerebral y sustancias químicas, pero la cronología/semántica efectiva de `locus 1` y `locus 2` no se deduce de los números solamente. Antes de llamar a un químico «reward» o «punishment» por su función o nombre, hay que verificar la tabla C1 de sustancias y el comportamiento del ejecutable.

## 2. Qué NO demuestra esta lectura

- No demuestra que químico49=«recompensa» y 50=«castigo» con certeza si no se valida su nombre en tabla C1 o su generación metabólica.
- No demuestra fórmulas exactas de susceptibilidad, refuerzo o reducción de fuerza; los genes contienen SVRules y parámetros, mientras el ejecutable regula cómo se aplican.
- No muestra valores *en ejecución* de químicos o estado sináptico; son instrucciones genéticas.
- No confirma si una configuración de atención influye en una decisión en el mismo tick o en uno posterior.

## 3. Prioridad siguiente

El paso que más conocimiento aporta antes de integrar una mente nueva no es añadir neuronas: es **reconstruir un ciclo neuronal/sináptico fiel a las reglas conocidas y contrastar la química que alimenta `CHEM0..3`**.

Mantener explícitamente separadas:
1. una **línea H** con especificación genética C1 y partes hardcoded todavía inciertas;
2. una **línea N** de NeuroLab con aprendizajes simplificados demostrados E01–E08.

**No sustituir** en línea H una regla de refuerzo química de C1 por el `reward=±1` del banco de pruebas sin clasificarlo como aproximación experimental.

### Fuentes de lectura estructural

- [CDR: Chemical Receptor](https://double.nz/creatures/genetics/receptor.htm).
- [CDR: Chemical Emitter](https://double.nz/creatures/genetics/emitter.htm).
- [CDR: Brain Lobes](https://double.nz/creatures/brainlobes/intro.htm).
- [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html).


## 4. Actualización de nomenclatura histórica — 21/11/2026

Una fuente independiente de los bytes del genoma permite ahora identificar los **nombres oficiales usados en C1**: [C1 Chemical List (transcripción atribuida al Genetics Preview Kit)](https://creatures.fandom.com/wiki/C1_Chemical_List). Es una lista histórica reproducida por la comunidad, no el ejecutable original. La descripción del **paper Grand/Cliff/Malhotra** respalda Reward/Punishment/Reinforcement y su participación en aprendizaje.

| ID de genoma C1 | Nombre documentado | Uso bioquímico descrito |
|---:|---|---|
| **49** | Reward | Señal de refuerzo positivo hacia conexiones excitatorias de Decision |
| **50** | Punishment | Señal de refuerzo negativo hacia conexiones inhibitorias de Decision |
| **51** | Reinforcement | Producto químico breve derivado tanto de Reward como Punishment; actúa sobre fortaleza de Concept independientemente del signo del refuerzo |
| **52** | ConASH | *Concept Atrophy Suppressing Hormone*: control de la pérdida/migración de dendritas en Concept |
| **53** | DecASH1 | *Decision Atrophy Suppressing Hormone* clase 0, conexiones excitatorias |
| **70** | DecASH2 | *Decision Atrophy Suppressing Hormone* clase 1, conexiones inhibitorias |

**Nota sobre registros previos:** La sección 2 declaró que no se había verificado el nombre/función de los químicos 49/50/51/52/53/70. Ese límite estaba vigente durante la inspección binaria, pero esta tabla lo **resuelve parcialmente con una fuente independiente**. No transforma en dato verificado el orden de ejecución ni las funciones exactas que usa el motor para convertir concentraciones químicas a STW/LTW, susceptibilidad y fortaleza.

### Implicación mecánica para la investigación

El circuito del genoma separa **(i) aprendizaje de qué decisiones resultan útiles bajo una situación** (CHEM0/1 en lóbulo Decision), **(ii) mantenimiento/atenuación de dendritas de esas decisiones** (CHEM2/3, DecASH1/2) y **(iii) mantenimiento de detectores conjuntivos de conceptos** (Reinforcement/ConASH). Por eso el actual ajuste experimental de un peso +16 o -16 en cinco neuronas no es una reproducción de estas capas.

**Próximo trabajo histórico prioritario:** usar [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html) para reconstruir cada fase de actualización de sinapsis con niveles de evidencia y valores de genoma, elaborando tests de oráculo manual antes de incorporar la química al microcircuito; distinguir de una eventual corrección por exploración.
