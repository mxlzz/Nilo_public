# E09.02i–I3c.5f — auditoría de estado basal C1 frente a la microred experimental

**21-11-2026 · auditoría documental y de bytes, SIN nueva hipótesis conductual ejecutada.** Depende de [I3c.5c](E09_02I_I3C5C_RESULTADO_DISPONIBILIDAD.md), [I3c.5d](E09_02I_I3C5D_RESULTADO_VENTANA_PRECOZ.md) e [I3c.5e](E09_02I_I3C5E_RESULTADO_PUERTA_SENAL.md).

## Fuentes comprobadas

- Se releyó directamente el **`dad1.gen` original** aportado en carpeta Drive `neurolab`, 10.001 bytes y SHA256 **e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4**. El parser existente [c1_genome_inspector.py](../../experiments/neurolab/c1_genome_inspector.py) ya define el formato de registros de lóbulo de122 bytes, clase dendrítica de47 y receptores de8; se hizo comprobación independiente mediante offsets de los 320 marcadores `gene`, sin ejecutar juego ni publicar GEN.
- [Especificación genética anterior](E00_GENOMA_ORIGINAL_COMPARACION.md); [migración x86](E09_02F_05A_MIGRACION_PRE_REGISTRO.md); [fuerza0 en EXE](E09_02I_I3C5B_H_RESULTADO_X86.md); [receptores originales verificados](resultados/e09h3_receptores_genoma_original.json). El ejecutable SHA256 **548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7** fue cotejado previamente para las rutas locales; no se ejecutó.

## 1. Lo que el GEN realmente inicializa

En el registro Decision original (offset **3417**, lóbulo6, 16 neuronas), clases excitatoria/inhibitoria:
- **128 dendritas por clase y neurona**, 16 neuronas → **4096 dendritas nominales de Decision**, frente a **8** en `C1ContextBrain` (2 neuronas, 2 fuentes×2 clases) o **4** en `DynamicContextBrain` (2 neuronas, 1 fuente×2 clases). Son reducciones deliberadas, no una reproducción de escala.
- **LTW inicial0..0** en ambas clases, **fortaleza inicial2..4**, migración Type1 y tasas genéticas `susceptibility_decay=48`, `STW_relax=80`, `LTW_rate=128`, ganancia de fortaleza cada3, pérdida cada5. En la ruta de nacimiento/migración reconstruida, **STW se inicializa igual a LTW**.
- El cerebro reducido inicia **todas** sus ocho dendritas con STW/LTW0 y strength **exactamente2**. Coincide con el borde inferior del genoma, pero suprime toda variabilidad de fortaleza y migración si se usa el baseline fijo.
- Lóbulo Concept original (offset **3661**, lóbulo8, 640 neuronas): clase principal con **1..3 entradas por neurona**, LTW inicial **128**, fuerza **1..10**, migración Type2. Los detectores one-hot del laboratorio usan STW128 y emiten126 en el estímulo máximo, una **convención de simplificación funcional**, no un Concept histórico completo. No atribuirle generalización/conceptualización automática.

## 2. Línea basal química que explica el agotamiento sin recompensa

Registros de receptor Decision leídos nuevamente sobre los bytes originales:
- Gen receptor **88** (lóbulo6, locus13→CHEM0, química49): **nominal0**.
- Gen **89** (lóbulo6, locus14→CHEM1, química50): **nominal0**.
- Gen **127** (lóbulo6, locus15→CHEM2, química53): **nominal16**, inhibición (`flags1`).
- Gen **128** (lóbulo6, locus16→CHEM3, química70): **nominal16**, inhibición (`flags1`).
- La carga nominal [initialize_brain_chem_loci](../../experiments/neurolab/e09_historical_locus.py) y el genoma avalan **Decision CHEM=(0,0,16,16)** sin variación externa. Las reglas de pérdida de fortaleza Decision leen CHEM2 para excitatoria y CHEM3 para inhibitoria; **nominal16>0 permite atrofia periódica aunque no exista recompensa ni química positiva de refuerzo**.
- Bajo `update_strength` sin incremento y con esos químicos positivos, una dendrita de fuerza inicial2 llega a0 en tick10, de fuerza3 en tick15 y de fuerza4 en tick20 (decrementos sólo en ticks5,10,15,20). Esta es una **consecuencia del modelo numérico y del calendario**, no una medición de todas las dendritas reales de un Norn. El modelo fijo con8/8 fuerza2 colapsa sincronizadamente en tick10, como observó I3c.5c.

## 3. Qué explica, qué no explica

**C1c.5f-BASAL (verificación de fuentes)**: no hay evidencia de bug aritmético por atrofia en ausencia de premio; el circuito fijo reducido fue construido deliberadamente sin variedad de fuerza ni renovación histórica. La magnitud de refuerzo de I3c.5d fue máxima1, frente al umbral mínimo STW5 (I3c.5e), y quedó eliminada por relax/strength. Así, **cambiar sólo strength2 por un valor del rango3/4 no salva un efecto unitario incapaz de atravesar la cuantización**. No justifica un ensayo nuevo de fuerza inicial por sí solo.

**El genoma original NO prueba que 4096 sinapsis o 16 neuronas sean necesarias para una mente mínima.** Tampoco prueba que el escalado `128→1` por clase funcione conservando la estadística de actividad y el crédito. El problema de NeuroLab es de **dinámica y dosificación química/eligibilidad más estructura**, no solo cantidad de neuronas. El C1 real incluye fuentes químicas, reacciones, actividad de cientos de Concept y migración; no se ha validado toda esa exposición/cronología en este laboratorio.

## 4. Decisión metodológica fundada y alternativas

- **No aumentar nodos/contactos ni dosis/gain por intuición.** Más contactos de STW0 o STW1 no generan señal por sí mismos porque la contribución `(source×STW)>>8` se trunca **por dendrita antes de sumar**; repetir un ensayo de un solo pulso sobre el mismo diseño carece de poder explicativo.
- **No reconstruir el Norn completo todavía.** Implicaría cuerpo, emisiones, PRNG y scheduler sin evidencia de que ese costo sea necesario para responder G05 (aprendizaje y crédito en una mente reducida).
- **Prioridad siguiente:** auditar cómo proporcionar a la microred una señal química **repetida y comparable** usando mecanismos originales de receptor/fortaleza, antes de proponer una intervención. Debe existir control neuronal con el feedback directo ya implementado, pero su ventaja histórica (E03/C) **no** se puede comparar causalmente con químico M mientras exposición/efecto difieran.
- Diseñar una **prueba de viabilidad multiepisodio** con calendario de estímulos/feedback congelado, control sin plasticidad, fuente causal y distractora, y reportes de fuerza+STW por tick. La comparación de **momento** y **amplitud** debe hacerse por factores separados, sin ajustar parámetros a la precisión final. Para la rama más fiel a C1, antes verificar los límites del metabolismo y el origen de químicos49/50/53/70; para la rama N, distinguir claramente cualquier transformación sintética del GEN histórico.

**Estado:** auditoría de bytes y referencias completada; **NO** nuevo experimento ni aprobación de arquitectura. G05/G09/G00-H continúan abiertas, PR #103 permanece draft, `main`/Nilo0.7 intactos.
