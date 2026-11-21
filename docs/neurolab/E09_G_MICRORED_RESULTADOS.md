# NeuroLab E09g — primer resultado de microred mínima sin mundo

**Corte verificado:** 2026-11-21. Fuente primaria: `dad1.gen` del CD (SHA `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`) y `Creatures.exe` (SHA `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`). Ningún binario del juego se subió al repositorio ni se ejecutó.

## 1. Arquitectura estudiada

**Cinco unidades:** P0,P1→C→D0,D1, 4 sinapsis plásticas de Decision (dos por neurona), 2 entradas fijas de Concept. **Es una reducción experimental radical** frente al genoma C1 (16 decisiones con 128 dendritas excitatorias +128 inhibitorias por decisión, Concept 640 neuronas). Sin cuerpo, mundo ni LLM.

- Regla Concept: `ANDTYPE0`; Decision: `STATE PLUS TYPE0 MINUS TYPE1`.
- Cómputo exacto de operandos y atenuación en aritmética de byte x86, tablas reales de decay/relax, plasticidad por susceptibilidad y concentraciones químicas, STW/LTW con tasas de **Decision del dad1.gen** (48/80/128), ganancia de fortaleza cada3 ticks y pérdida cada5.
- Químicos Reward49/CHEM0 y Punishment50/CHEM1, producidos **por un evaluador externo de laboratorio** tras la acción elegida. No hay metabolismo interno ni cinética real de reacciones.
- La entrada P0=P1=255 activa siempre **el mismo Concept C=253**. No hay todavía adquisición de conceptos ni varias situaciones distintas.

## 2. Diferencia temporal demostrada por el código máquina

- En `0x403C92–0x403CBB`, el ejecutable procesa lóbulos de salida 6,7,8 en ese orden, por lo que Decision lee el Concept del tick anterior.
- En `0x403ED1–0x403EF0`, el ejecutable copia a SVTable **OUTPUT y STATE de la neurona anteriores al cálculo**. Esto permite que la susceptibilidad responda a la salida que sobrevivió WTA el tick previo, no indiscriminadamente al puntaje actual.
- En `0x4048CC–0x404911`, WTA conserva el primer máximo y pone a cero las demás salidas.
- En `0x404114–0x404162`, los estados internos se relajan usando el genoma: Decision rest80/decay24.
- La creación real de refuerzo tiene cinética bioquímica adicional no simulada.
- **Aleatoriedad:** tabla IAT `0x441088` importa `rand` y `0x4410A8` importa `srand` de CRT Microsoft; en `0x42354A–0x42355C` el ejecutable llama a `time(NULL)` (IAT0x44103C) y pasa su retorno a `srand`. Esto define su semilla inicial en un arranque corriente, pero no revela el número de llamadas a rand() acumuladas en cada instante ni el seed de una partida guardada.

## 3. Resultados E09g.2 — sensibilidad al WTA en mismo ensayo

**Evidencia:** [CI #44933734902](https://github.com/mxlzz/Nilo_public/actions/runs/44933734902), 20 semillas por condición; [JSON completo por semilla](resultados/run-44933734902/e09g2.json).

| Gating de output para susceptibilidad | Desempate | Aprendizaje D0 | Reversión D1 | Control congelado D0 | Preregistro |
|---|---|---:|---:|---:|---|
| Solo ganador del ensayo | random_tie | **1.0000** | **1.0000** | 0.4925 | **Sí** (20/20 semillas en ambas) |
| Solo ganador | first_index | 1.0000 | 1.0000 | **1.0000** | No: ventaja0 al inicio |
| Ambas neuronas pre-WTA | random_tie | 0.4925 | 0.510625 | 0.4925 | No |
| Ambas neuronas pre-WTA | first_index | 1.0000 | 0.0000 | **1.0000** | No |

La elegibilidad exclusiva de un ganador importa enormemente, pero esta fase usa winner de **ese mismo ensayo**, que es una convención experimental más directa que el flujo real.

## 4. Resultados E09g.3 — reloj continuo basado en OUTPUT anterior

**Evidencia:** [CI #44933734902](https://github.com/mxlzz/Nilo_public/actions/runs/44933734902), **246 tests** junto con regresiones E01–E09, con 2 fallos experimentales históricos **expectedFailure**. [JSON E09g.3 por semilla](resultados/run-44933734902/e09g3.json).

- Decision emplea Concept previo; OUTPUT previo después de WTA condiciona susceptibilidad; STATE neuronal perdura y se relaja en vez de reiniciarse.
- Pulso químico sintético Reward/Punishment generado por la acción se entrega el **siguiente tick**. El modelo no simula la velocidad de la reacción bioquímica real.
- `random_tie`: precisión media inicial **1.0000**, reversión **1.0000**, control congelado **0.4925**; 20/20 semillas superan ambos criterios (≥0.90) y ventaja media0.5075. **Puerta aprobada para este modelo**.
- `first_index`: precisión inicial1.0000, reversión1.0000, control congelado inicial1.0000; no supera el criterio de ventaja inicial, porque la regla fija D0 ofrece un sesgo previo coincidente con el objetivo de entrenamiento. **No atribuir ese 100% inicial a aprendizaje**.
- Con el reloj continuo, **el resultado positivo no desaparece**. Sigue limitado a una contingencia única, un concepto fijo y un evaluador de laboratorio.

## 5. Qué queda demostrado y qué no

**Demostrado para el modelo experimental:** una red con cinco unidades y las tasas sinápticas extraídas del genoma puede aprender/revertir una relación de dos acciones en una tarea sintética, y la temporización de output/WTA puede determinar si existe aprendizaje selectivo.

**NO demostrado:** inteligencia general, mente autónoma, capacidad de autogenerar metas, creación de nuevos conceptos, generalización a estímulos diferentes, crecimiento libre, comportamiento C1 idéntico byte por byte, ni conexión con Nilo 0.7. No se ha superado el problema de crédito causal de E05 en casos con distractores correlacionados.

## 6. Próximas pruebas de valor

1. **E09g.4:** contrabalancear objetivo inicial D0/D1, introducir 10% de feedback erróneo y demoras de 3 ticks. Confrontar métricas antes de crecer la red; informe de fallos separado.
2. **Después:** estudiar una segunda situación/Concept para probar discriminación contextual: con un solo Concept fijo puede bastar un sesgo, no «comprensión de contextos».
3. **Solo si gana utilidad verificable:** incorporar drive químico interno y atención, sin cuerpo ni mundo. Comparar contra baseline tabular simple.
4. **No integrar a Nilo** antes de demostrar mayor valor que un mecanismo mucho más sencillo y sin decidir expresamente la evolución del proyecto.

**Estado de PR:** todos los cambios en la rama `docs/neurolab-protocolo-20261120`, PR#103 en borrador, `main` sin cambios.
