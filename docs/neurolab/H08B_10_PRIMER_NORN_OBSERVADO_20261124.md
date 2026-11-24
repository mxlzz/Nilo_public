# H-08b.10 — primera observación de un Norn ejecutado por el original

**Fecha:** 2026-11-24. **Gate de factibilidad PASS.** [CI #45449497913](https://github.com/mxlzz/Nilo_public/actions/runs/45449497913), job 138642342350, commit `f051526728c461f0f6e1eb036f90c23567f97e95`; [arranque y protocolo](H08B_09_MODO_ARRANQUE_DOCUMENTADO_20261124.md). Se verificaron ZIP del CD, EXE y GEN, CD montado CDFS y DDE constante123. Mundo inicial Norns0/Grendels0. Una única llamada documentada NEW: CREA creó un individuo masculino a partir de una copia byte a byte de dad1.gen SHA256 e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4, moniker NL01. Conteo1. DDE moniker observado `31306c6e` (bytes de token invertidos respecto a texto; no imponer convención). La creación directa no es incubación natural ni representa una cohorte experimental.

## Datos observados

Tres rondas del mismo Norn; identidad verificada antes/después, 18/18 consultas de los seis campos esperados válidas. En las tres:

- Pool 49 (Reward) 0; 50 (Punishment) 0; 51 (reinforcement) 2; 54 (RewardEcho) 4; 55 (PunishEcho) 0.
- Decision lobe6, cell0, dendtype0: `[0,27,128,0,0,0,126]`. Según [CDR BrainCellMonitor](https://double.nz/creatures/brainutilities.htm) los siete campos son output, state, número de dendritas, suma susceptibilidad, suma STW, suma LTW, suma strength. No son pesos individuales.
- Latencias de consulta registradas entre 0 y 16000 us, cuantizadas por reloj coarse de Windows; cero no significa respuesta instantánea. Se corrige a perf_counter_ns en la siguiente prueba. Valores idénticos en las rondas, no demuestran ticks activos, maduración normal o causalidad.

No se inyectaron estímulos de refuerzo. No se confunde el eco con recompensa instantánea ni los datos secuenciales con una instantánea atómica. El binario en disco no se modificó. Recursos de ejecución retirados, incluido CD; no se distribuyó original.

## Continuidad

La búsqueda de bytes en Creatures.exe exacto encuentra token `cell`, `chem` y `monk`, pero no `lcus`/LCUS/sucl/SUCL. La documentación CDN cubre varias versiones; no asumir que LCUS esté implementado en este Build. Para la pregunta original se prioriza el enlace x86 ya verificado [H4](E09_H_04_RESULTADO_ENLACE_LOCI.md), en lugar de probar al azar una macro potencialmente no implementada.

[Commit b9074fe19277cd5815742dfc20e5ea0c44e45158](https://github.com/mxlzz/Nilo_public/commit/b9074fe19277cd5815742dfc20e5ea0c44e45158) prepara traza CDB adjunta tras birth/lecturas, con puntos world tick, regular prebrain/prechem/postchem, llamada alternativa y llamadas internas química/cerebro, 120 eventos como máximo, pseudonimiza punteros, no publica raw logs. [CI #45449814988](https://github.com/mxlzz/Nilo_public/actions/runs/45449814988) en curso al registrar. La traza comprobará orden, no frecuencia sin instrumentación; medir fase receptor/reacción y loci solo si se comprueba la identidad del objeto y los puntos alcanzados. N STOP, G05/G09 abiertas, main intacto.

## Repetición independiente del gate y primer intento de traza

[CI #45449814988](https://github.com/mxlzz/Nilo_public/actions/runs/45449814988), job 138643470266: nueva sesión desde la misma imagen, nuevo individuo con el mismo moniker de ensayo y genoma hasheado (NO el mismo individuo persistido entre sesiones). 18/18 lecturas válidas, identidad comprobada por ronda. Concentraciones secuenciales de 49/50/51/54/55: (1,0,7,7,3), (0,0,4,6,0), (0,0,3,5,0). Decision cell0 tipo0: (0,27,128,0,0,0,115) en las tres rondas. Medición de consulta corregida con perf_counter_ns: 2937–3960 us para los 18 campos. Esto demuestra cambios en la química del original durante la observación, no orden intratick ni aprendizaje inducido. Primer CDB attach: marcador inicial presente, salida tras 10101 ms, **0 eventos interpretables**, no error reconocido por el filtro inicial. No se puede distinguir aún pérdida de captura, formato o ausencia de eventos. No computar frecuencia ni declarar PASS del trazador. [Commit fc5504c2e37ca617fe24c2df08cb6b4d127eb897](https://github.com/mxlzz/Nilo_public/commit/fc5504c2e37ca617fe24c2df08cb6b4d127eb897) añade marcadores independientes y categorías diagnósticas; [CI #45450061479](https://github.com/mxlzz/Nilo_public/actions/runs/45450061479) en curso al escribir. No se cambió motor ni se aplicaron estímulos.
