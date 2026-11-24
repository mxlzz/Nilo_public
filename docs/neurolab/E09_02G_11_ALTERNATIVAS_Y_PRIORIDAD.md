# E09g.11 — evaluación de alternativas y continuidad

**Fecha:** 2026-11-21. Recomendación metodológica, no una arquitectura aprobada por el usuario. NeuroLab continúa aislado de Nilo 0.7, sin fusión a main.

## Hechos verificados

- [G10b](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md): en 40 semillas, la microred original aprende parcialmente bajo distractores y recompensa diferida, pero no pasa su puerta; la compuerta artificial IG empeora el resultado; el control Q con atribución causal explícita logra 100 % en ambas fases. Este último dispone de información de procedencia adicional.
- [G10c](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md): las sinapsis de Decision ya conservan susceptibilidad. La conexión objetivo sigue con susceptibilidad positiva cuando llega la recompensa, pero a medida que hay más distractores el efecto químico afecta crecientemente otras conexiones. Es un contrafactual de un solo tick, no una prueba conductual causal a largo plazo.
- El circuito de seis unidades es una reducción del modelo C1; todavía no equivale a la dinámica completa de los 952 puestos neuronales del genoma histórico.

## Alternativas examinadas

**1. Susceptibilidad C1 existente.** Es una traza temporal local regulada por coactividad y química; ya está implementada según reglas genéticas y fragmentos verificados del ejecutable. Su limitación no es ausencia total de memoria, sino atribución poco selectiva entre asociaciones con distractores. Conviene comprobar primero la fidelidad de reloj/química original, no añadir otra traza redundante.

**2. Cola causal simple.** La tabla Q2×2 registra origen (contexto y acción), y resolvió el banco con poca complejidad. Pero recibe una correspondencia causal provista por el evaluador que el cerebro no conoce; en un mundo abierto habría que detectar eventos causales por medios propios. Es un baseline eficaz y de menor costo, no emulación histórica.

**3. Trazas de elegibilidad de RL, como TD(lambda).** Son un mecanismo existente de atribución temporal (Sutton y Barto, segunda edición, capítulo 12: https://web.stanford.edu/class/psych209/Readings/SuttonBartoIPRLBook2ndEd.pdf ; revisión https://pmc.ncbi.nlm.nih.gov/articles/PMC3208325/). No garantizan crédito correcto con distractores y añaden hiperparámetros. Dada la susceptibilidad C1 existente, **no está justificado implementarlas todavía**.

## Recomendación priorizada

**No sumar neuronas ni ajustar IG en este clasificador S0/S1.** La siguiente unidad de investigación es **E09h.1: revisar fidelidad temporal y bioquímica del C1 original**. Estudiar orden real entre señales de Concept, output de Decision, actualización de susceptibilidad, aplicación química, STW/LTW, winner-takes-all y reloj por lóbulo. Separar siempre hechos de ensamblador, parámetros de genes e hipótesis del laboratorio.

Para verificar nuevos offsets y la secuencia exacta del scheduler es necesario disponer nuevamente del ejecutable original del CD, SHA-256 documentado en [E09f](E09_02F_INFORME_EJECUTABLE.md). El binario no figura entre los archivos accesibles de esta conversación/proyecto; GitHub conserva el análisis derivado, no el ejecutable. La documentación puede revisarse sin él, pero la **verificación adicional del código máquina queda pendiente hasta recuperarlo**. No pedir ni subir distribuciones de terceros.

G00-H, G05 y G09 global siguen abiertas. La recomendación no autoriza integración con Nilo ni cambios en main.
