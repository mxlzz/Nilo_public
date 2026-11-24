# E09h.3 — preregistro de transferencia de receptores al cerebro C1

**Fecha:** 2026-11-21. Registrado después de inspección exploratoria de x86 `0x421F8D..0x422011` y del genoma C1 CD, **antes de implementar** un evaluador aislado de receptor. No es preregistro ciego de la fórmula.

## Objetivo y pertinencia

Cerrar un eslabón del camino de aprendizaje histórico: cómo una concentración de Reward49/Punishment50 se convierte en el valor que ve el lóbulo Decision, antes de seguir investigando el crédito temporal. No agregar neuronas, compuertas IG ni reglas LLM.

**Fuentes primarias:** el mismo EXE SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7` y `dad1.gen` SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. Se examinarán los receptores cerebrales 88,89,126–129, con bytes original verificados y `E00_MAPA_NEUROQUIMICO_C1.md`.

## Operaciones a verificar

Dentro de la fase receptora de `0x421E70`, para receptor con químico id distinto de cero:
1. Obtener `available=max(0,pool[chemical]-threshold)`; leer el valor de `gain`.
2. Si `flags&2`, usar `effect=gain` cuando hay `available>0`. En otro caso `effect=(available*gain)>>8`; con available=0 el efecto es0.
3. Si `flags&1`, calcular `max(0,nominal-effect)`, de lo contrario `min(255,nominal+effect)`.
4. Escribir resultado en la localización ligada a receptor. **No deducir aquí que un locus genético corresponde a CHEM0 si la rutina de enlace de punteros no fue verificada**. No implementar emisores, reacciones o el ciclo completo, solo función local.
5. La etapa de receptores ocurre **antes** de las reacciones del mismo tick químico, E09h.1. Por lo tanto una sustancia sintetizada posteriormente se transferirá en otra llamada, no la misma.

## Fixtures antes del código

- Receptor 88: químico49, nominal0, umbral0, gain255, flags0. Con concentración49=12, valor `(12*255)>>8=11`; concentración0 entrega0.
- Receptor 89: químico50 con parámetros idénticos; si concentración50=12, salida11.
- Receptor 127: químico53, nominal16, umbral0, gain255, flags1. Con concentración53=12, salida `max(0,16-11)=5`; concentración mayor (p. ej. 40) satura en0.
- Receptor 126: químico52, nominal4, gain255, flags1; concentración5 → `max(0,4-(5*255>>8))=1`.
- Control `flags&2`: si concentración supera umbral, efecto=gain independiente de magnitud, según branch del ejecutable; con concentración bajo/igual umbral, efecto0. No atribuir este caso a genes cerebrales si no lo usan.
- Confirmar vía parser que hay 43 receptores tipo1/subtipo0 y que los seis campos relevantes coinciden exactamente. No emitir químicos ni mutar un pool de concentraciones de 256 entradas.

## Puerta y límites

Si los fixtures y 318+ pruebas del laboratorio pasan, reportar **transferencia de receptor aislada** validada para esos bytes y la semántica indicada por el assembly. **No** equivale a receptor intracelular completo ni validación de enlace a `CHEM0..` o cronología global; G00-H/G05/G09 siguen abiertas. Documentar qué falta y el costo de seguir antes de otra implementación.
