# Etapa2 — H18. Pendiente geomorfológica como causa del transporte sedimentario

**2026-11-22. Dictamen:** **H18 APROBADA** conforme al protocolo antes del código. [Protocolo](ETAPA_2_H18_PROTOCOLO_GRADIENTE_SEDIMENTO.md), [código](experiments/probe_e2_h18_slope_ablation.py), [CI 45060100229 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45060100229). Se reutilizó **sin cambiarlo** el solver/material owner H9 y las bibliotecas Landlab2.11.0, xarray2026.9.0, Python3.13.18, NumPy2.5.5.

## Ablación causal

Dos escenas 16×16, mismo sedimento A inicial **10.080.000kg**, mismo K_sed0,1, K_br=0, mismo outlet0, mismos 12 pasos `dt=.2`, misma topología del nodo/máscara, mismo espesor inicial de suelo, misma configuración física. **Única intervención:** multiplicar por0,5 la elevación de bedrock en owner y campo temporal Landlab antes del primer paso.

- Pendiente media del sustrato: **0,046806662 → 0,023403331**, cociente exacto0,5. Pendiente media de superficie completa **0,049949721 → 0,028161274** (no es mitad exacta porque el escalón del espesor de suelo se conservó).
- **Escenario original (G1):** salida sedimento **472.551,1385719963kg**, masa almacenada final **9.607.448,861428004kg**; error balance **0kg**, tolerancia0,1008kg. Hay erosión y deposición en los12 pasos, 50 nodos con ganancia neta.
- **Pendiente mitad (G0,5):** salida **288.317,58610280097kg**, masa almacenada **9.791.682,413897198kg**, residuo **−1,862645149230957×10⁻⁹kg**, misma tolerancia. Diferencia respecto original **−38,987008480379765%** (más del5% predefinido). Hubo erosión/deposición en12 pasos y50 nodos con ganancia neta.
- **Control K_sed=0:** sin movimiento de suelo ni exportación, idéntico estado a inicial. El ajuste de pendiente modificó la distribución espacial real de suelo; no se dedujo salida de diferencia de stocks: se usaron directamente los valores de salida nativos del solver.
- **Replay de G0,5:** arrays y saldos exactamente idénticos. Cinco corrupciones de owner de H9 rechazadas sin mutar estado válido; NetCDF **5.308bytes** restauró datos de sedimentos, bedrock alterado, geometría derivada, salida y hash SHA `7258e903dc697c1c1a899214c5423d9c7a3915d027f9e4bcebf032332455350e`.

## Interpretación y gobierno

**Aporta evidencia al gate E2(d):** cambiar únicamente el gradiente de relieve condiciona la dinámica nativa del transporte de materia, con magnitud diferente de exportación y presupuesto conservativo. El cambio físico observado no proviene de alterar el coeficiente de erosión ni de imponer un depósito.

**No demuestra:** dinámica de granos volumétricos 3D, transporte en cavidades H5, deformación/estabilidad de pendientes reales, condiciones de lluvia calibradas, generación abierta de paisaje ni acoplamiento al balance de energía H16. La discontinuidad inicial del suelo se prescribió en H9 y se mantuvo; solo el gradiente de bedrock se escaló. Los resultados no son una tasa real de erosión natural.

**Próximo paso:** auditar el gate de etapa2 sobre sus requisitos escritos antes de pruebas, incluyendo H17 (gravedad y bloqueo) y H18 (gradiente) más conservación de calor comprobada en H15/H16, **sin** confundir ensayos aislados con etapa5 de acoplamiento ambiental. No modificar main ni NeuroLab.
