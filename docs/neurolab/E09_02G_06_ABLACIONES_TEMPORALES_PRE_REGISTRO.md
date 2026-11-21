# E09.02g.6 — pre-registro interventional: estado persistente vs latencia perceptual

**Fecha de registro:** 2026-11-21, después del diagnóstico exploratorio g.5a y **antes de codificar las intervenciones g.6**. Experimento interventional derivado de un resultado previo; no es replicación independiente ni se recicla como éxito de G09.

## Pregunta y predicciones

E09g.5 fracasó en su puerta (12/20) y g.5a localizó errores muy marcados tras cambios de contexto, además de errores sostenidos en determinadas semillas (p. ej., semilla 16, S1 invertida). Se distinguirán tres hipótesis no excluyentes:

- **H-L: latencia perceptual.** Si el desfase Concept→Decision explica principalmente el error transitorio, precargar el Concept correcto al comenzar cada bloque aumentará la exactitud *early* y de la posición 0, con efecto pequeño o nulo en *steady*.
- **H-S: persistencia de Decision.** Si el estado recurrente de Decision arrastra preferencias entre bloques, reiniciarlo al estado basal en los bordes aumentará *steady* en las semillas débiles, sin tocar los pesos.
- **H-W: asociación insuficiente.** Si pesan más las asociaciones aprendidas que el contexto interno arrastrado, los errores sostenidos persistirán incluso al combinar ambas intervenciones; habrá que estudiar luego el aprendizaje y crédito causal, no sumar neuronas prematuramente.

Las hipótesis no suponen que un mecanismo gane. El origen genético del modelo y las tasas **no** se recalibran.

## Diseño congelado (factorial 2×2; pruebas pareadas)

Se reconstruye de cero la red g.5 para semillas **0..19**, exactamente los mismos bloques balanceados y 256 ticks por fase, con inversión simultánea de correspondencias y continuidad de químicos/estado entre fases. Los dos estados al cierre de entrenamiento A/B son puntos de partida inmutables de cuatro evaluaciones de holdout *learn=False*, con secuencias de prueba g.5 no alteradas, 16 bloques×8 ticks:

1. `C` **continuous** — control original g.5, sin intervención.
2. `N` **neutral-decision** — al comienzo de **cada** bloque, reemplazar solo `neuron_states=(80,80)` y `neuron_outputs=(0,0)`, conservando `concept_outputs`, tick y las 8 sinapsis.
3. `W` **warm-concept** — al comienzo de cada bloque, precargar artificialmente `concept_outputs=(126,0)` para S0 o `(0,126)` para S1; conservar Decision, tick y sinapsis. **Oracle experimental:** acorta latencia y NO es una capacidad autónoma/histórica.
4. `NW` **ambas** intervenciones como combinación de N y W, mismo borde de bloque.

Cada brazo continúa normalmente dentro del bloque. Ninguna intervención cambia el entrenamiento, la conectividad, parámetros de plasticidad, químicos, mapping correcto ni selección WTA. No se modifica `C1ContextBrain` ni el runner g.5; el diagnóstico vive en archivo aparte. Los estados de entrada se copian por referencia inmutable y cada condición ejecuta su propia trayectoria.

## Métricas e interpretación fijadas de antemano

- Métrica primaria descriptiva: exactitud `steady` en posiciones 2..7, A y B por separado y pareada frente a `C`, media de 20 semillas y delta para cada semilla.
- Secundarias: `early` posiciones 0..1, precisión por posición 0..7, exactitud por contexto, conteo de semillas que alcanzan ambos steady≥0.90 **solo como diagnóstico**. No llamar «g.5 superada» a una intervención.
- El caso específico de semillas fallidas 0,2,3,4,8,16,17,19 se reportará *sin seleccionarlas como muestras de confirmación*. Se indica también el efecto sobre todas las 20 semillas.
- **Regla orientativa preregistrada para priorizar investigación**, no gate científica: cambio `steady` ≥+0.10 en al menos 4/8 semillas originalmente fallidas sugeriría una contribución funcional sustantiva de esa manipulación; cambio menor que +0.02 en promedio sugeriría impacto limitado. Reportar resultados intermedios y efectos adversos sin acomodar umbrales.
- El control `C` debe reproducir `evaluate_brain` original por semilla/fase exactamente (tolerancia 1e-12), y su total de semillas aprobadas debe seguir siendo **12/20**; si no, la intervención es inválida.
- **Invariantes:** todas las sinapsis y sus STW/LTW/strength idénticas al comenzar cada brazo; estado original de entrenamiento intacto. Pruebas de determinismo y checkpoints de estados no deben cambiar.

## Interpretaciones excluidas

Un mejor puntaje de `N`, `W` o `NW` mostraría qué componente interfiere **en un holdout artificial**, no una red nueva aprendiendo mejor, ni una mejora histórica de Creatures 1. Una ausencia de mejora no descarta causas combinadas. La corrección causal de recompensa demorada de E05/G05 **NO** está incluida en este experimento. La tabla Q sigue siendo el competidor práctico de menor complejidad.

**Después:** documentar resultados reales y decidir si se necesita un experimento separado que pruebe alineación de refuerzo/acción/contexto. No pasar a mundo, cuerpo ni Nilo.
