# E09.02g.9 — replicación fuera de muestra con 80 semillas nuevas

**Fecha:** 2026-11-21. **Pre-registro antes de implementar:** [E09_02G_09_REPLICACION_NUEVAS_SEMILLAS_PRE_REGISTRO.md](E09_02G_09_REPLICACION_NUEVAS_SEMILLAS_PRE_REGISTRO.md). **Evidencia CI:** [GitHub Actions #44939075550](https://github.com/mxlzz/Nilo_public/actions/runs/44939075550), job `136952069314`, commit verificado `fb31ad91079f0454a4b8ac730455832bbdea44c3`, conclusión `success`. Se invocó `python -m experiments.neurolab.e09_oos_replicate`; se archivó la salida JSON **íntegra** en [e09g9.json](resultados/run-44939075550/e09g9.json) para no depender de la retención limitada de los artefactos.

## Diseño congelado

**80 semillas nuevas 20..99**; ninguna se utilizó en las fases de diseño E09g.5–g.8 (semillas 0..19). Sin cambiar código ni hiperparámetros de los brazos C/G/S de g.8, se volvieron a entrenar las dos fases de 32×8 ticks y a evaluar con holdouts balanceados de 16×8 ticks por fase. `C`: química original; `G`: suprime el pulso en el segundo tick posterior al cambio de contexto; `S`: suprime el pulso siguiente, en el mismo bloque. **G y S son oráculos externos de frontera** y no representan capacidad de C1.

## Resultados exactos

| Modelo | Steady A | Steady B | Early A | Early B | ≥0.90 steady en ambas |
|---|---:|---:|---:|---:|---:|
| C original | 0.926171875 | 0.949479167 | 0.613671875 | 0.639453125 | **46/80** |
| G dirigido | **0.954166667** | **0.972395833** | 0.552734375 | 0.594921875 | **60/80** |
| S control adyacente | 0.923046875 | 0.940494792 | **0.615625000** | 0.628906250 | **44/80** |

- Diferencia pareada de `steady` G−S, **fase B +0.0319010417**; **fase A +0.0311197917**. El criterio práctico preregistrado (B≥+0.03 y A≥−0.02) **se cumple en esta replicación**, pero no cambia el fracaso anterior de g.8 en semillas 0..19.
- Bootstrap pareado 4.000 remuestras, semilla `20261121`, intervalo percentil al 95 % **[+0.0161458333, +0.0500000000]** para la diferencia media de steady B. El intervalo está completamente encima de 0: **apoyo direccional fuera de muestra** según el protocolo.
- Heterogeneidad B: **35** semillas con G>S, **13** con G<S, **32** con empate; **mediana G−S = 0**. El beneficio medio no es universal y se concentra en ciertos casos. A: 42 mejores, 11 peores, 27 empatadas; mediana +0.0104167.
- Pulsos efectivamente omitidos: **1.264** en fase A y **1.307** en fase B **por cada brazo G/S**, con igual distribución de oportunidades. No se recurrió a premios inexistentes para equiparar métricas.
- Coste: `early` de G es sustancialmente peor que C/S en ambas fases (A 0.5527 frente a 0.6137/0.6156; B 0.5949 frente a 0.6395/0.6289). La intervención mejora la fase tardía pero no el comportamiento de transición.
- El 75 % (60/80) de G supera ambas métricas individuales, todavía lejos de la fiabilidad objetivo del laboratorio de 90 % en cada fase y semilla. No extrapolar 80 semillas sintéticas a un organismo o entorno real.

## Conclusión científica

**Sí se reproduce** fuera de las semillas originales una ventaja media de filtrar pulsos en la frontera temporal precisa, superior a la de omitir tantos pulsos un tick después. Eso hace plausible que el desfase de crédito localizado por g.7 contribuya a la degradación en este circuito; la hipótesis merece investigación adicional. No equivale a demostrar un mecanismo causal interno, porque el banco de pruebas identifica el cambio de contexto para el circuito, ni a verificar fidelidad de todo el motor C1.

**No aprobar retroactivamente g.8**: su puerta de +0.03 en B falló con 0.0291667. El resultado g.9 favorable es una **nueva evidencia** y no una corrección de la historia experimental. G00-H, G05 y G09 global permanecen abiertas.

## Próximo paso de mayor rendimiento y menor complejidad

**E09g.10 — evaluación de viabilidad de crédito interno, sin implementación inmediata de oráculos.** Contrastar tres opciones antes de desarrollar:

1. Una memoria mínima de procedencia de decisión (Concept/acción/sinapsis previos, sin información futura), bajo el mismo presupuesto y coste de estado.
2. Una compuerta de plasticidad deducible exclusivamente del estado cerebral disponible en tiempo real, sin reloj de bloques externo ni conocimiento del objetivo.
3. Mantener la tabla 2×2 o memoria asociativa simple como alternativa eficiente si no hay una ventaja comprobable del circuito neuronal.

Cualquier nuevo experimento requiere su propio preregistro, acciones y controles, preservando los resultados negativos. No añadir neuronas por defecto ni tocar Nilo 0.7.
