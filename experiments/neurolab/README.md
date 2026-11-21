# NeuroLab — motor experimental aislado E01

**ATENCIÓN:** aquí solo hay neuronas/sinapsis sin aprendizaje ni cuerpo. No contiene funciones de Nilo 0.7. No representa el algoritmo bit a bit de Creatures 1.

- Documentación de arqueología: [E00](../../docs/neurolab/E00_INFORME_HISTORICO_01.md).
- Plan por subetapas: [E01–E09](../../docs/neurolab/ETAPAS_00_09.md).
- Código: `kernel.py` (transición pura, sincronía por salida anterior, escala byte, salida seleccionable).
- Tests: `python -m unittest discover -s experiments/neurolab/tests -v` desde la raíz del repositorio.
- Sin PyTorch, sin internet, sin dependencias externas. Solo biblioteca estándar Python (3.10+ por operadores de tipos y diccionarios).
- No hay recompensa ni pesos modificables hasta E03. Las variables STW/LTW y la adaptación quedan para E04 y posteriores.
- Cualquier rendimiento medido aquí corresponde exclusivamente al kernel E01. No constituye aprendizaje ni mente general.

## Semántica exacta E01

Entrada: `stimulus=0..255` por neurona marcada `input`; ausencia equivale a 0.
Una neurona de cómputo recibe salidas del **tick previo** ponderadas por `floor(output*weight/255)`; agrega excitación e inhibición.
`pre=clamp(state_old + sum(excit) - sum(inhib),0,255)`.
`output = max(0, pre-threshold)` (modo `above_threshold`) o `pre` si `pre>threshold` (modo `full_state`).
El estado posterior se aproxima a `rest`: `rest+sign(pre-rest)*floor(abs(pre-rest)*(256-decay)/256)`.

Estos últimos cálculos son convenciones **propias** del experimento NeuroLab, no atribuidos al ejecutable C1. Las pruebas incluyen ambas versiones de umbral porque las fuentes históricas discrepan.

Un checkpoint JSON contiene `tick`, estados y SHA256 de configuración: restaurar bajo otra topología se rechaza.
