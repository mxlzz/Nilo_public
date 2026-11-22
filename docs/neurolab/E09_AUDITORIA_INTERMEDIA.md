# E09 — auditoría intermedia de mecanismos y decisión sobre integración

> **Archivo histórico de 20/11, no estado vigente (nota 22/11):** aquí se indica que todavía faltaban `dad1.gen` y `Creatures.exe`, pero ambos fueron aportados e inspeccionados después; tampoco equivale la integración parcial E09 cerebro-química a una integración de todas las capacidades. Ver [GEN original](E00_GENOMA_ORIGINAL_COMPARACION.md), [EXE auditado](E09_02F_INFORME_EJECUTABLE.md), [auditoría actual](E09_01_AUDITORIA_CAPACIDADES_20261122.md) y [errata](E09_00R_RECONCILIACION_GATES_20261122.md). Conservar las observaciones y su fecha, sin aprobar G09 por ellas.

**Fecha:** 2026-11-20. **Carácter:** auditoría de lo realmente ejecutado en E00–E08; **NO cierre de G09**. No se creó todavía un cerebro que combine todas las capacidades; no presentar módulos independientes como un agente funcional.

## 1. Evidencia reproducible

| Mecanismo | Versión | Resultado respaldado | Límite |
|---|---|---|---|
| E00, arqueología de Norn C1 | [Informe histórico](E00_INFORME_HISTORICO_01.md) | Fuentes primarias/guías comparadas, 952 posiciones nominales, 9 lóbulos, reglas conceptuales | **G00-H abierta**: sin genoma/binario original, contradicción sobre umbral |
| E01, cómputo neuronal | [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44850766887) | 19 tests de transición numérica y checkpoint pasan | Ecuaciones de NeuroLab, no réplica byte a byte C1 |
| E02, decisiones | [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44850881701) | Circuito seis unidades y WTA, ocho tests específicos | Sin aprendizaje en E02 aislada |
| E03, plasticidad simple | [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44851094727) | 20 semillas, aprendizaje y reversión vs pesos fijos; umbrales preregistrados alcanzados | Asociación con refuerzo inmediato y episodios cortos reiniciados |
| E04, dos escalas de peso | [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44851265622) | STW/LTW propios, shock y relajación, checkpoints | Solo sinapsis aislada, **no** combinada aún con selector E03 |
| E05, elegibilidad | [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44851485383) | Refuerzo diferido local funciona; prueba de distractor correlacionado muestra atribución indebida | **G05 NO superada** para crédito causal; 10 tests verifican la matemática, no causalidad correcta |
| E06, conceptos de pares | [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44851722169) | Conjunciones fijas transferidas al contexto inédito, 20 semillas y controles | Los detectores NO se forman por aprendizaje; XOR esencial sí estaba en train |
| E07, recableado | [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44852027094) | Con dos slots se aprenden patrones nuevos por reconexión, comparado con slots fijos y LRU | Reglas de atrofia propias, no genoma; puede ser solo gestión de caché |
| E08, recurrentes | [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44852126108) | Oscilación de dos neuronas, amortiguación sin entradas y perturbación, 20 semillas | Ciclo prefijado por topología, **no** pensamiento autónomo |

**Advertencia de revisión:** que cada módulo tenga tests verdes NO demuestra que los módulos mantengan estas propiedades cuando se combinan. Los informes de los runners, con resultados por semilla y parámetros, se generan reproduciblemente en código; esta auditoría no inventa porcentajes que no se hayan extraído de las salidas JSON.

## 2. Deficiencias que impiden G09

1. **Fidelidad histórica:** no se inspeccionó `dad1.gen` auténtico ni un ejecutable original. Umbral, orden exacto de ticks y parámetros sinápticos difieren o siguen inciertos.
2. **Integración real:** E03, E04, E05, E06 y E07 usan modelos específicos separados. No existe todavía una red única con aprendizaje continuo, atención, conceptos adquiridos y consolidación compartida.
3. **Crédito causal:** E05 refuerza más al distractor B que a A cuando A era la causa y B estaba más reciente. No hay inferencia causal confiable.
4. **Representación:** E06 muestra invariancia contextual, no creación de nuevos conceptos. E07 recablea slots según reglas externas, no demuestra descubrimiento autónomo de nuevas categorías.
5. **Recompensa:** todo refuerzo lo aporta un evaluador sin cuerpo. No sabemos cómo el sistema asignaría prioridades o generaría motivaciones sin esa evaluación externa.
6. **Comparación simple:** además de controles por etapa, falta ablación integrada con memoria tabular, tamaño mínimo y relación entre capacidad y coste.
7. **Trazabilidad numérica:** las ejecuciones CI están enlazadas y ejecutan scripts; faltan artefactos consolidados y comparables de métricas y pesos para evaluación global externa.

## 3. Etapas pendientes para declarar un «cerebro mínimo»

- **E09.01:** congelar SHA y exportar resultados agregados y por semilla en artefactos versionados/no modificables; antes de nueva ejecución registrar versión de análisis.
- **E09.02:** definir una interfaz común de estado y tick, con neurofisiología y sinapsis no inconsistentes; integrar E01–E04 y E06 en una variante sin E05 y otra con E05 rotulada de atribución limitada.
- **E09.03:** comparar ablaciones (sin STW/LTW, conceptos simples, sin recableado, sin recurrencia) sobre las **mismas** tareas y presupuestos.
- **E09.04:** barrido sistemático de número de neuronas y sinapsis; las capacidades no se comparan si las reglas de entrenamiento y evaluador difieren.
- **E09.05:** incluir baseline tabular/caché equivalente, no únicamente controles seleccionados para favorecer una red.
- **E09.06:** definir retención y continuidad de comportamiento en sesiones sin reiniciar estado cada tres ticks; checkpoint completo.
- **E09.07:** realizar evaluación con semillas nuevas y errores/limitaciones publicados, incluyendo problemas de atribución temporal.
- **E09.08:** concluir solo la capacidad realmente demostrada. Si no supera baseline simple, mantener solución simple.

## 4. Revisión de arquitectura vs meta original

La hipótesis del usuario es estudiar **cómo funcionaba la mente de Norns** para hallar una unidad mínima útil y ampliarla. Hasta aquí existe un buen banco de mecanismos y resultados, pero todavía **no una réplica fiel ni una mente unificada**.

**Próxima dependencia histórica:** contar con un genoma C1 original de procedencia legítima (por ejemplo `dad1.gen` extraído de una instalación del juego), o aceptar explícitamente que la investigación seguirá solo con documentación secundaria y modelos derivados. [Gene Loom](https://lisdude.com/Creatures/Community/GeneLoom/) permite abrir genomas de Creatures 1 sin desarrollar un editor.

**La integración no debe adelantarse fingiendo reglas históricas inexistentes.** Cuando se decida continuar con el modelo propio, no hace falta un ejecutable original para evaluar nuestras ecuaciones, pero jamás se debe etiquetar ese resultado como reproducción de C1.

**G09: ABIERTA.** Informe preliminar únicamente; autoriza mejor diseño, no declaración de éxito del objetivo final.
