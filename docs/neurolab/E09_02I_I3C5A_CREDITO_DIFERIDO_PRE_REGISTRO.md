# E09.02i–I3c.5a — preregistro de atribución temporal del refuerzo

**21-11-2026 · NL-EXP-I3c5a-v1 · PR #103, rama experimental. ESTADO: preregistrado, NO ejecutado al escribir este documento.**

## Alineación, antecedentes y pregunta

Continúa estrictamente [I3c.5](E09_02I_I3C5_REENFOQUE_CREDITO_CAUSAL.md) y la puerta científica **G05**, todavía ABIERTA. Reutiliza el cerebro fijo de ocho dendritas `C1ContextBrain`, el puente metabólico y los observadores de I3b.1/I3b.2/E09g.10c. **No** crea neuronas, elegibilidad, mapa causal ni plasticidad nueva; no modifica `C1ContextBrain`, genes, `main` ni Nilo 0.7. Se excluye la migración para aislar primero crédito temporal, cuya insuficiencia también se observó sin migración (B en I3c.4).

**Pregunta falsable:** para la misma elección previa y un único precursor de igual dosis nominal, ¿qué proporción del efecto sináptico atribuible al pulso recae en conexiones alimentadas por el **contexto causante** frente al **distractor posterior** cuando la entrega ocurre 0, 1, 2 o 3 ticks después? ¿Sobrevive alguna diferencia de STW/LTW y se relaciona con una decisión posterior? No confundir asociación temporal con causalidad aprendida.

## Cohorte y unidad

- **Semillas nuevas y congeladas:** `1200..1219` (20), nunca usadas por I3/I3b/I3c. Ningún resultado histórico 0..419 ni 800..919 se usa para optimización. Réplicas por semilla: objetivos 0/1 y contingencias A/B (80 troncos), **cinco ramas** por tronco: N sin precursor, D0/D1/D2/D3 con entrega en el tick posdecisión indicado. No seleccionar episodios exitosos.
- Estado compartido por las cinco ramas: `C1ContextBrain(seed)`, química C1 en el puente I3, 120 ticks preparatorios alternando grupos de ocho contextos, cuatro ticks del contexto objetivo. El tronco termina en **tick 124**. La acción proviene exclusivamente del cerebro en el cuarto tick; la verdad A/B reside exclusivamente en el evaluador externo.
- Tras clonar el estado inmutable en tick124, cada rama recibe siempre el **mismo distractor `1-target`** hasta tick256 inclusive; el pulso se agrega justo antes del avance posdecisión de índice d=0,1,2,3. No introducir más precursores. Cada tick avanza cerebro con químicos ANTERIORES, luego receptores/reacciones y decaimiento sintético I3 (`RATES=40`, `dose=80`); **ganancia 1**, sin ajuste de tasas.
- Si la acción es `None`: el evaluador **no entrega precursor en ninguna rama**. Reportar cantidad; si son cero, el mecanismo de ausencia de acción solo queda cubierto por tests artificiales, no por datos naturales.
- El mismo precursor nominal puede producir **distinta exposición química por tick** debido a desplazamiento y decaimiento. Registrar dosis, tick, concentraciones leídas y AUC por rama. N no garantiza química igualada; no atribuir resultados exclusivamente al reloj si hay diferencia de exposición.
- Luego de tick256, efectuar lectura **sin aprendizaje ni recompensa**, con cuatro avances del contexto objetivo sobre clones independientes; registrar elección y exactitud por contingencia. Esta lectura es **exploratoria**, no criterio de aprendizaje robusto.

## Observación y causalidad local

En cada tick posdecisión, antes de avanzar, ejecutar observador **read-only** sobre las ocho dendritas mediante `update_c1_synapse`, con estados y químicos reales del brazo. Exigir identidad exacta del estado de cada dendrita respecto de `brain.step` ejecutado con el mismo input; fallar si difiere. Clasificar cada contacto por **fuente 0/1, dueño D0/D1, tipo excitatorio/inhibitorio** usando índices existentes; el origen relevante es el `target` del tronco, no el contexto observado al recibir el pulso.

**Resultados obligatorios por rama, seed, objetivo, contingencia y retraso:**
1. Por fuente **objetivo/distractor** y por dueño de la acción original: suma de `reinforcement_effect` no negativo, conteo de eventos positivos y susceptibilidad anterior positiva; distinguir recompensa y castigo.
2. Fracción de efecto al origen objetivo `E_target/(E_target+E_distractor)` (nulo si denominador cero), fracción al par fuente objetivo/dueño de la decisión, y diferencia frente a N (ambos sumatorios y fracciones). **Fracción no equivale a causalidad correcta**: documentar que es una clasificación experimental exógena.
3. Divergencia absoluta de STW y LTW por fuente respecto de N **en el mismo tick**, incluidas mediciones en 128 y 256; conteo de conexiones `strength=0` antes/después, y memorias en conexiones agotadas reportadas aparte.
4. Pulso ausente, acierto de la decisión original, readout posterior con `learn=False`, tiempo lógico y AUC de CHEM0/CHEM1. Ninguna meta ni respuesta correcta entra al cerebro o al observador sináptico.

**Estimadores:** comparaciones pareadas D0−D1/D2/D3 y Dk−N; resúmenes por resultado positivo/negativo, fuente y ventana 128/256. Informar medias por semilla y **IC 95% bootstrap agrupado por semilla** con semilla bootstrap fija `60515` y 2000 réplicas; no tratar los cuatro troncos de una semilla como independientes ni hacer selección a posteriori. Si la proporción no tiene denominador, reportar `null` y cantidad de casos.

## Puertas y criterios previos a ejecución

- **G-I3c5a-SOFTWARE:** 20 semillas; 80 troncos; 400 ramas; exactamente una entrega por Dk cuando hubo acción y ninguna cuando no la hubo; igual `before` por tronco; ninguna filtración de mapping al cerebro; igualdad observador vs motor; hashes por semilla reproducibles; mismo estado/decisión para el tronco de las cinco ramas.
- **G-I3c5a-CREDIT:** informar incluso si la señal es cero, se dirige al distractor o no tiene efecto en lectura. La evidencia mecanística es **exploratoria**, sin umbral de éxito de aprendizaje en esta etapa. Registrar si la distribución depende de la demora sin modificar dosis/gain.
- **G-I3c5a-LTW:** distinguir incremento numérico en slots `strength=0` de memoria funcional. Los valores de LTW en ticks128/256 NO bastan para declarar retención.
- **G05/G09/G00-H:** permanecen **ABIERTAS** cualquiera sea el resultado de I3c.5a; G05 requiere posterior prueba conductual confirmatoria contra controles y cohorte no utilizada.

## Implementación, preservación y siguiente paso

Sólo tras este preregistro: implementar `experiments/neurolab/e09_i3c5a_credit_forks.py` y tests específicos; workflow experimental que almacene JSON por semilla y sumario, CI integral, hash de código/artefactos e informe, incluidas negativas. No reescribir criterios tras observar resultados. Después, realizar **I3c.5b auditoría histórica de strength=0** por fuentes x86 originales antes de cambiar slots o descartar conexiones agotadas. No fusionar PR #103 ni modificar `main`.
