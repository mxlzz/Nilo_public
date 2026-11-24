# E09h.1 — resultado de orden estático de cerebro, química y lóbulos

**Fecha:** 2026-11-21. **Fuentes:** ejecutable y genoma originales nuevamente aportados por el usuario. Se comprobaron localmente las huellas exactas ya registradas: EXE `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7` (387.072 bytes), GEN `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4` (10.001 bytes). Ningún archivo propietario se subió al repositorio. Ver [preregistro](E09_H_01_ORDEN_CEREBRO_QUIMICA_PRE_REGISTRO.md), [verificador reejecutable](../../experiments/neurolab/e09_historical_timing_audit.py) y [salida breve de la inspección real](resultados/e09h1_inspeccion_estatica_original.json).

**Estado de pruebas:** ejecución local del verificador con ambos originales comprobó **12 firmas de instrucciones y 10 llamadas E8 con destino correcto**. [CI #44944783092](https://github.com/mxlzz/Nilo_public/actions/runs/44944783092) **success: 318 tests y 2 expectedFailure históricos**. CI utiliza fixtures sintéticos de parser PE32; **NO dispuso de los originales**, por tanto ese CI verifica el código del auditor y no revalida el archivo original. El respaldo de datos originales es el JSON anterior, generado después de la comprobación local.

## Hallazgos vinculados a direcciones

**Ruta normal condicionada del Norn, en `0x407540`:** `0x407583` llama al brain tick `0x403BB0`, luego `0x407595` llama a la bioquímica `0x421E70`, después `0x4075A6` inicia selección conductual `0x40A4B0`, y la misma rutina incrementa el contador `[norn+0x2C20]`. Esa ruta se toma bajo comprobaciones de estado de `[norn+0x2CBC]` y `[norn+0x2CCC]`; no es una afirmación universal sobre todos los caminos. Desde el loop externo de juego hay llamada a `0x407540` en `0x424884`.

**Orden de lóbulos del brain tick `0x403BB0`:** la rutina recorre cinco estructuras comenzando en `brain+0xD0` con stride `0xC8`: **lóbulos 1..5**. Después incorpora actividad de lóbulos previos en una estructura correspondiente a **lóbulo 0**, procesado mediante `0x403C87` → `0x403CD0` en `brain+8`. Finalmente empieza por `brain+0x4B8`, correspondiente a **lóbulo 6**, y procesa lóbulos posteriores mediante `0x403E00` hasta `n_lobes-1`. Esto concuerda con el índice de los lóbulos en el genoma CD (6 Decision, 8 Concept); **Decision se procesa antes que Concept dentro de la llamada**. No se simuló el scheduler de cada neurona y no se ha verificado aún toda la sincronización interna de salidas.

**Etapas de `0x421E70`:** la rutina ejecuta en orden bucles que usan `+0x128C` para **emisores** (`0x421E83`), `+0x1288` para **receptores** (`0x421F77`), `+0x1290` para **reacciones** (`0x422023`) y finalmente un bucle de **256 químicos** con decaimiento (`0x4221D0` y `call 0x419E40` en `0x4221ED`). Se constataron instrucciones que escriben en el pool químico en la primera fase (`0x421F4B`), lo leen y actualizan loci en la segunda (`0x421F9A/0x42200F`).

**Implicación temporal, razonamiento a partir de la ruta verificada:** una sustancia generada por la fase de reacciones **no puede ser leída por los receptores en esa misma invocación**, porque su lectura ya ocurrió. Aunque una emisión anterior puede ser muestreada en el mismo tick químico, las sustancias nacidas en reacciones se muestrearían recién en otra invocación de `0x421E70`; y en la ruta regular el brain tick precede a esa invocación. No convertir esta secuencia en un valor exacto de milisegundos, ni atribuir resultados de g.10b automáticamente a este desfase.

**Excepción importante:** existe otra ruta `0x405D20` que primero llama a química (`0x405D32`) y después al cerebro (`0x405DAF`). También hay una ruta alternativa de procesamiento de criatura `0x4075C0`. No afirmar “siempre cerebro→química” sin analizar disparadores y estado.

## Límites y decisión

Quedó identificada estáticamente una parte sustantiva del orden temporal del motor C1. **No** quedó establecida la frecuencia real del scheduler general, temporización de eventos de comportamiento, concentraciones dinámicas, integración completa de receptores ni fidelidad bit a bit del Norn. **E09h.1: evidencia estática validada, fidelidad integral todavía abierta.**

El siguiente paso concreto y justificado es **E09h.2: cinética de reacciones** con cálculo de consumo/producción y carga de la tasa, usando el genoma y el EXE reales. No añadir neuronas ni alterar el ensayo de crédito causal C1-reducido hasta verificar el mecanismo histórico. G00-H/G05/G09 siguen abiertas; Nilo 0.7 y main intactos.
