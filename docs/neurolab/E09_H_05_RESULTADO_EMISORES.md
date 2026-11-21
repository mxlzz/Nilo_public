# E09h.5 — emisores cerebrales C1: inspección estática y aritmética aislada

**Fecha:** 2026-11-21. **Alcance:** el enlace del emisor y su actualización local del pool fueron reconstruidos desde el EXE original verificado. No se ejecutó Creatures ni se produjo una simulación completa de sus Norns. G00-H/G05/G09 global siguen abiertas.

## Evidencia y reproducción

- EXE original idéntico a E09h.4 por SHA-256: 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7, 387.072 bytes. Verificación local estática de **32 firmas de instrucciones, vtable y dos destinos de tabla** (loci emisores 1/2), sin instalar ni ejecutar.
- [Preregistro anterior al módulo](E09_H_05_EMISORES_PRE_REGISTRO.md), [verificador de EXE](../../experiments/neurolab/e09_historical_emitter_audit.py), [fixture derivado de bytes auténticos](resultados/e09h5_inspeccion_estatica_original.json), [motor emisor aislado](../../experiments/neurolab/e09_historical_emitter.py), [tests de aritmética](../../experiments/neurolab/tests/test_e09_historical_emitter.py) y [tests sintéticos del auditor](../../experiments/neurolab/tests/test_e09_historical_emitter_audit.py).
- Los **tres emisores cerebrales** se basan en la extracción documentada de E00 del GEN real, **no en una nueva inspección del GEN en este chat**: gen123 Concept8/locus1→ConASH52; gen124 Decision6/locus1→DecASH1=53; gen125 Decision6/locus2→DecASH2=70. En E00 todos tienen threshold0, sample_rate1, gain255 y flags1.

## Camino x86 reconstruido

1. **Enlace del origen:** en 0x421B7A..0x421B89 el loader obtiene el puntero CBrain de Norn+0x2C18, usa su vtable en brain+4 y llama al resolver **0x4030E0 con kind=1**. La tabla de este tipo está en 0x403284/0x403270; los loci1 y 2 resuelven a **lobe+0xC1** y **lobe+0xC2**, no a CHEM0/1 (que usaban kind=0 y loci13..16). 0x421C17 guarda el puntero del origen en el registro de emisor.
2. **Muestreo:** el bucle en 0x421E83 se ejecuta **antes** del receptor 0x421F77. En 0x421E9A lee el byte vinculado; flag4 invierte como 255−x. Si x=0 no hay emisión. Si tick módulo sample_rate no es cero, no emite; el umbral se resta después y requiere resultado >0.
3. **Cantidad:** flag2 selecciona el valor de ganancia directamente; sin flag2, la cantidad es truncamiento entero de (x−threshold) × gain / 256, por desplazamiento de 8 bits. Chemical ID distinto de 0 se suma al pool con saturación a255 (0x421F4B), indexado con stride de dos bytes.
4. **Consumo:** con flag1 activo, 0x421F4F..0x421F58 escribe **cero en el locus origen** luego de la condición de emisión. El valor no se reinicia si falló la compuerta de x, tick o umbral.
5. **Orden:** los químicos generados por emisores pueden leerse en la fase receptora del **mismo tick químico**. Reacciones siguen ocurriendo después de receptores y su producción no entra a ese muestreo de ese mismo tick.

## Errata explícita del preregistro

La hipótesis H5.4 anticipó que, si chemical ID=0, el emisor no consumiría el byte de origen. **Es falsa para la ruta estática examinada**: en 0x421EEF y 0x421F24 ambas ramas saltan al reset 0x421F4F. Por lo tanto, si el evento pasa filtros y flag1 está activo, el origen pasa a cero **incluso sin modificar el pool**. Se preservó el preregistro y el test verificó el comportamiento real; no se cambió el criterio para fabricar éxito.

El ejecutable divide por sample_rate sin proteger cero; el módulo NeuroLab **rechaza sample_rate=0** como entrada inválida, divergencia segura que no debe presentarse como identidad bit a bit.

## Oráculos y límites

Para cualquiera de los tres emisores de E00, con fuente=80 y pool inicial cero, tick0 y los campos previos: cantidad (80×255)>>8 = **79**, concentración de su químico=79 y origen posterior=0. Con fuente=255 la cantidad es254, no255. Los controles cubren saturación, flags2/4, umbral, frecuencia, entrada ausente y chemical=0.

**Importante:** el valor fuente=80 es un caso artificial; no implica que los loci C1 +0xC1/+0xC2 tomen ese valor durante una partida. No se reconstruyó aquí cómo se activan esos bytes a través de toda la conducta. El pool también puede ser alterado por múltiples emisores/reacciones y por decaimiento. No afirmar causalidad conductual.

**Puertas:** G-H5-X86 verificada estáticamente contra el EXE; **G-H5-MATH verificada en [CI #44948424321](https://github.com/mxlzz/Nilo_public/actions/runs/44948424321), success integral: 362 tests, 2 expectedFailure históricos**. CI no utiliza los binarios originales y prueba el auditor con memoria sintética. G-H5-GEN conserva procedencia documental E00 sin nueva lectura del GEN. G00-H/G05/G09 siguen abiertas.

**Próxima dependencia propuesta dentro del plan:** reconstruir frecuencia y variaciones del scheduler C1 antes de integrar química con cerebro; no rediseñar sinapsis ni crear neuronas. Mantener PR #103 draft; main/Nilo 0.7 intactos.
