# NeuroLab E00-H02 — comparación de dad1.gen extraído del CD y genoma actualizado

**Fecha de inspección:** 2026-11-21. **Estado:** comparación binaria y decodificación de genes de lóbulos completadas; **NO** se ha ejecutado el juego ni se han verificado las reglas internas de su ejecutable. **Archivos binarios de terceros no incorporados al repositorio**.

## 1. Procedencia y huellas exactas

| Campo | Archivo aportado del CD | ZIP actualizado de Creatures Caves |
|---|---|---|
| Nombre interno | `dad1.gen` | `Updated C1 V2.zip/dad1.gen` |
| Procedencia | El usuario lo extrajo de la instalación contenida en su imagen de CD Creatures 1, carpeta `INSTALL/DATA.Z` | https://creaturescaves.com/downloads.php?section=Breeds&view=239 |
| Tamaño | **10.001 bytes** | **20.001 bytes** |
| SHA-256 | `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4` | `f32c0cac5985d9c71c9a6765b98cd321dd49574f315a1f2813cd4f0bb91babfe` |
| Marcadores `gene` | **320** | **320** |
| Genes de lóbulo `type=0/subtype=0` | **9** | **9** |
| Registros completos de los nueve lóbulos | **idénticos** | **idénticos** |

La procedencia «genoma original de fábrica» se basa en el archivo que el usuario extrajo de la imagen del CD; no se comparó con una huella oficial publicada por el fabricante. Este es el genoma C1 del CD aportado, no prueba independiente de la versión exacta del ejecutable.

**Comparación byte a byte:**
- Los archivos son exactamente iguales desde el byte 0 hasta el **7828 inclusive**.
- Las **15 posiciones** diferentes del tramo compartido de 10.001 bytes son: **7834, 7835, 7837, 7839–7850**, concentradas en el registro que comienza en el byte **7829**.
- Ambos archivos comparten 320 marcadores `gene` en las **mismas posiciones**. La última marca de gen está en **7829**.
- El `gend` principal aparece en **7848** en el archivo de CD y **7847** en el actualizado; la distinta longitud de ese registro desplaza el terminador. En la cola existen cadenas `gend` repetidas y bytes de relleno que no deben interpretarse como genes adicionales.
- El último byte no cero se encuentra en offset 7901 en ambas versiones. El tamaño extra de 10.000 bytes del archivo actualizado es relleno de ceros; **no son 10.000 bytes de genes nuevos**.
- El último registro cambia de categoría: cabecera de fábrica `type=1/subtype=2` (reacción química), cabecera actualizada `type=1/subtype=0` (receptor químico). También cambia su payload. Esto concuerda con la descripción del parche sobre antioxidantes/envejecimiento; **no se ha demostrado todavía a qué loci/químicos exactos se conecta el nuevo receptor**, por lo que no se atribuye un mecanismo metabólico más específico.

**Conclusión principal:** los **nueve genes de definición de lóbulos neuronales son idénticos** en el genoma de CD y el actualizado, y los primeros 319 marcadores de genes ocurren en posiciones idénticas con bytes anteriores al último registro idénticos. Puede usarse el espécimen recibido para documentar la estructura cerebral configurada genéticamente sin depender de la versión parcheada.

## 2. Formato comprobado en los genes de lóbulo C1

Cada uno de los nueve registros ocupa **122 bytes**:
- 4 bytes del marcador ASCII `gene`.
- 6 bytes de cabecera genética, los primeros dos son `type=0, subtype=0`.
- **112 bytes** de definición del lóbulo: posición y tamaño (4), flag perceptible (1), parámetros neuronales (umbral, tasa de decay, reposo, atenuación: 4), SVRule neuronal (8), flags neuronales (1), y dos clases de dendritas de **47 bytes cada una**.
- Las dos clases de dendritas codifican fuente, mínimo/máximo, distribución/fan, rangos iniciales de LTW y fortaleza, tipo de migración, tasas y cuatro SVRules de 8 bytes.

La estructura coincide con [Home Sweet Albia, Lobe Gene Structure](https://zenzoa.com/creatures/c1-brains.html) y [Creatures Developer Resource](https://double.nz/creatures/brainlobes/intro.htm). Las etiquetas de opcode que siguen usan el mapeo documentado en la guía, no una interpretación improvisada.

## 3. Lóbulos del dad1.gen aportado (datos reales)

| ID* | Lóbulo | X,Y | Ancho×alto | Células | Umbral | Decay | Reposo | Atenuación | Flag perceptible | Flag WTA | SVRule neuronal |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | Percepción | 4,13 | 7×16 | 112 | 10 | 0 | 0 | 255 | 0 | 0 | sin opcodes |
| 1 | Drive | 34,30 | 8×2 | 16 | 24 | 0 | 0 | 255 | 2 | 0 | sin opcodes |
| 2 | Source | 15,24 | 8×5 | 40 | 0 | 16 | 0 | 255 | 0 | 1 | sin opcodes |
| 3 | Verb | 37,24 | 8×2 | 16 | 0 | 32 | 0 | 255 | 2 | 1 | sin opcodes |
| 4 | Noun | 21,3 | 20×2 | 40 | 0 | 32 | 0 | 255 | 0 | 1 | sin opcodes |
| 5 | General Sense | 32,34 | 8×4 | 32 | 0 | 24 | 0 | 255 | 1 | 0 | sin opcodes |
| 6 | Decision | 53,15 | 1×16 | 16 | 0 | 24 | 80 | 128 | 0 | 1 | `STATE PLUS TYPE0 MINUS TYPE1` |
| 7 | Attention | 44,30 | 5×8 | 40 | 0 | 48 | 0 | 255 | 1 | 1 | `STATE PLUS TYPE0 PLUS TYPE1` |
| 8 | Concept | 12,6 | 40×16 | 640 | 0 | 8 | 0 | 255 | 0 | 0 | `ANDTYPE0` |
| | **Suma** | | | **952** | | | | | | | |

*Los IDs 0–8 se asignan por orden de las nueve definiciones de lóbulos, según la correspondencia C1 documentada; sus números de secuencia de gen no equivalen a su ID funcional. Los flags se transcriben como enteros del archivo: `1` de WTA es consistente con la documentación, y `2` perceptible incluye exclusividad. Un gen con SVRule neuronal vacía puede seguir siendo funcional porque algunos lóbulos son especiales y operan mediante el ejecutable.*

## 4. Conectividad y plasticidad realmente codificadas

**Decision, 16 neuronas, WTA:**
- SVRule: `STATE + TYPE0 - TYPE1`, valores crudos `09 17 0C 18 0D 00 00 00`.
- Clase 0: fuente Concept (lóbulo 8), **128 conexiones por neurona**, tipo de migración `1`, LTW inicial `0..0`, fortaleza inicial `2..4`.
- Clase 1: misma fuente, **128 conexiones por neurona**, migración `1`, LTW inicial `0..0`, fortaleza inicial `2..4`.
- Potencial de conexiones tipo 0+1: `16×(128+128)=4096` dendritas, sujeto a comportamiento del motor. No son 4096 neuronas.
- SVRule susceptibilidad ambas: `OUTPUT TRUE INPUT`. Reinforce clase 0: `CHEM0`; clase 1: `CHEM1`. Gain strength clase 0: `SUSCEPT TRUE CHEM0 TRUE STW`; clase 1: `SUSCEPT TRUE CHEM1 TRUE STW`. Lose strength clase 0: `CHEM2`; clase 1: `CHEM3`. Significado y cronología de los químicos: dependen de receptores y motor.

**Attention, 40 neuronas, WTA:**
- SVRule: `STATE + TYPE0 + TYPE1`, bytes `09 17 0C 17 0D 00 00 00`.
- Una dendrita de clase 0 por neurona desde Source (lóbulo 2); una clase 1 desde Noun (lóbulo 4), ambas con LTW y fortaleza inicial 255, migración 0.
- Total nominal: **80 dendritas de atención**, con esta configuración.

**Concept, 640 neuronas:**
- SVRule: `ANDTYPE0` (byte `0E` seguido de ceros).
- Dendritas de clase 0 desde Perception (lóbulo 0); **mínimo 1, máximo 3** por neurona; migración `2` (Concept-style). LTW inicial `128..128`, fortaleza `1..10`.
- Clase 1 no conecta (mínimo/máximo 0).
- Rango nominal de dendritas en concepto: **640–1920**, según asignación en nacimiento, no conteo de sinapsis observadas en una criatura real.
- La interpretación tradicional «una neurona de concepto puede tener hasta cuatro entradas» no aplica a esta configuración particular: **la cabecera genética fija aquí máximo tres**.

**Suma potencial del conjunto con conectividad significativa:** `4096 + 80 + 640..1920 = 4816..6096`, compatible con la descripción histórica «aproximadamente 5000 sinapsis». La cantidad exacta y distribución se fijan durante nacimiento/actividad y no puede leerse como un recuento instantáneo solo del genoma.

## 5. Correcciones a nuestras hipótesis anteriores

| Supuesto anterior | Evidencia de dad1.gen y literatura | Corrección |
|---|---|---|
| Norn = 952 neuronas en cualquier caso | Este genoma codifica 952 posiciones; el motor podría ajustar tamaños | **952 para este espécimen**, no cifra universal |
| Concept = 1 a 4 entradas | Clase 0 desde Perception tiene mínimo 1, máximo 3 | **1–3 para este genoma** |
| Todas las neuronas usan la misma regla genérica | Seis genes de entrada tienen SVRule vacía y partes son hardcoded | Se requiere comportamiento especial de lóbulos C1 |
| E02 circuito de 6 neuronas se parece directamente a subred C1 | E02 usa conectividad fija E→C→D y pesos propios; C1 tiene 128 dendritas de dos clases para decisiones y migración | E02 es un control de aprendizaje elemental, **no emulación C1** |
| E03 regla ±16 imita sinapsis original | El genoma usa químicos `CHEM0/1/2/3`, STW/LTW, susceptibilidad y fortaleza | E03 es propia; se debe estudiar traductor bioquímico/genético antes de integración histórica |
| Atenuación/relajación exacta inferible de un valor | El valor genético no revela necesariamente cómo lo ejecuta el motor | Mantener distinción genoma vs ejecutable |

## 6. Qué falta para una reconstrucción histórica fiel

- Contrastar comportamiento efectivo de `output=state` (paper) vs `output=state-threshold` (guías técnicas): el genoma permite leer umbrales, pero no resuelve por sí solo el código ejecutable.
- Verificar orden exacto de evaluación, condiciones WTA y actualización de dendritas/relajación, ya que hay operaciones hardcoded.
- Mapear receptores/emisores y químicos de refuerzo reales de C1 conectados a Decision y Concept para entender el aprendizaje, en vez de usar recompensas externas arbitrarias.
- Diferenciar SVRules realmente ejecutadas del juego frente a interpretación de guías.
- Para reproducir el nacimiento de una criatura y conectividad inicial, recrear el algoritmo de asignación de dendritas y RNG histórico o contrastarlo experimentalmente con el juego.

## 7. Continuidad

**E00.02 — genes de lóbulos: desbloqueada con fuente del CD del usuario y comparación byte a byte.** La huella permite comprobar que futuras versiones usan el mismo archivo. La evidencia de origen original es la procedencia aportada, no una certificación externa del fabricante. **G00-H sigue abierta en ejecución exacta del motor C1.**

**Siguiente trabajo documentado:** (a) catalogar receptores y químicos `CHEM0..3` de las dendritas de Decision/Concept; (b) reconstruir una especificación C1 basada en reglas verificadas con tests independientes; (c) decidir si E09.02 debe integrar la mente experimental propia o una variante fiel histórica, sin combinarlas en un solo modelo ambiguo.

Fuentes: [Grand, Cliff y Malhotra (1996–1997)](https://eem.foo/ccarchive/Sites/fp.cyberlifersrch.plus.com/articles/agents_%2797_paper.htm), [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html), [Brain Lobes de CDR](https://double.nz/creatures/brainlobes/intro.htm), [SVRules de CDR](https://double.nz/creatures/genetics/svrules.htm).
