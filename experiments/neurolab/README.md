# NeuroLab — motor experimental aislado E01

**ATENCIÓN:** laboratorio aislado: E01 núcleo, E02 circuito de seis unidades, E03 aprendizaje por refuerzo, E04 doble peso STW/LTW aislado, E05 elegibilidad temporal aislada, E06 conceptos conjuntivos, E07 recableado limitado y E08 recurrencia matemática. No modifica Nilo 0.7 ni representa el algoritmo byte a byte de Creatures 1.

- Documentación de arqueología: [E00](../../docs/neurolab/E00_INFORME_HISTORICO_01.md).
- Plan por subetapas: [E01–E09](../../docs/neurolab/ETAPAS_00_09.md).
- Código: `kernel.py` (transición pura), `circuit.py` (elección), `plasticity.py` (aprendizaje E03), `twin_weight.py` (memoria E04), `eligibility.py` (crédito temporal E05), `concepts.py` (E06), `rewiring.py` (E07) y `recurrent.py` (E08).
- Tests: `python -m unittest discover -s experiments/neurolab/tests -v` desde la raíz del repositorio.
- Sin PyTorch, sin internet, sin dependencias externas. Solo biblioteca estándar Python (3.10+ por operadores de tipos y diccionarios).
- E03 incluye recompensas y pesos modificables; E04–E08 son pruebas controladas de capacidades separadas, **todavía no integradas** en un cerebro único. [Métricas por semilla y auditoría E09](../../docs/neurolab/E09_EVIDENCE_INDEX.md).
- E03 tiene evidencia de aprendizaje asociativo elemental. E04 demuestra propiedades temporales de una sinapsis aislada; E05 documenta una limitación de atribución causal, E06 invariancia contextual, E07 no supera a LRU y E08 actividad recurrente. Nada de esto demuestra mente general o conducta autónoma.

## Semántica exacta E01

Entrada: `stimulus=0..255` por neurona marcada `input`; ausencia equivale a 0.
Una neurona de cómputo recibe salidas del **tick previo** ponderadas por `floor(output*weight/255)`; agrega excitación e inhibición.
`pre=clamp(state_old + sum(excit) - sum(inhib),0,255)`.
`output = max(0, pre-threshold)` (modo `above_threshold`) o `pre` si `pre>threshold` (modo `full_state`).
El estado posterior se aproxima a `rest`: `rest+sign(pre-rest)*floor(abs(pre-rest)*(256-decay)/256)`.

Estos últimos cálculos son convenciones **propias** del experimento NeuroLab, no atribuidos al ejecutable C1. Las pruebas incluyen ambas versiones de umbral porque las fuentes históricas discrepan.

Un checkpoint JSON contiene `tick`, estados y SHA256 de configuración: restaurar bajo otra topología se rechaza.
