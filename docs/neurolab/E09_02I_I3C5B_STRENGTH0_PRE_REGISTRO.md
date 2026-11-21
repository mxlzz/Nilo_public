# E09.02i–I3c.5b — preregistro de auditoría strength=0

**21-11-2026 · NL-EXP-I3c5b-v1 · auditoría de discrepancia, NO reparación ni confirmación histórica.**

## Motivo

I3c.4b encontró aumentos numéricos de LTW en slots con `strength=0`. El modelo reducido `DynamicContextBrain.class_signal` calcula señales a partir de `STW` pero no consulta `strength`. El intérprete C1 y `update_strength` fueron reconstruidos estáticamente del EXE original SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`, pero este chat no dispone de los bytes originales para volver a verificar condiciones de bucle. **No dar por demostrada la semántica histórica.**

## Preguntas separadas

1. **N actual — transporte de señal:** dado un `DynamicConnection` cuya fortaleza es0 pero STW positiva, ¿`class_signal` genera entrada para Decision? Comparar mismo enlace con STW0, sin mutaciones, y demostrar su aporte con test estático.
2. **N actual — plasticidad:** en una dendrita strength0, ¿el helper numérico puede modificar STW/LTW antes de recuperar fortaleza? Usar exactamente `update_c1_synapse`, con un caso artificial con CHEM0, sin modificar genes ni código; registrar el estado anterior y resultado, incluida la fuerza.
3. **N actual — selección:** al pasar por `DynamicContextBrain.step(...,learn=False)`, ¿la señal observada alcanza la etapa WTA incluso con fuerza0? Verificar mediante `trace.class_signals` comparando un estado clonado con STW0.
4. **C1 histórico — condición decisiva:** localizar en la rutina que calcula dendritas (VA0x403F2F–0x403F8F) y en el bucle neuronal superior la condición exacta que excluye o incluye una dendrita agotada. Cruzar con VA0x40451E–0x4047E2, clase de migración1 y momento de limpieza. **No validar C1 a partir del modelo Python.**

## Criterios y límites

- Tests de observación específicos: no cambiar `class_signal`, `C1ContextBrain`, `DynamicContextBrain`, `update_c1_synapse` ni `c1_strength.py`.
- Si se observa señal positiva con fortaleza0 en N, marcar explícitamente **posible contaminación de resultados B/Y/P** e impedir interpretarlos como una desconexión funcional sin evidencia histórica.
- Si se observa actualización STW en strength0, separar **peso numérico**, **transmisión a WTA** y **reconexión efectiva**.
- Sin EXE original o dump verificado del bucle, el paso **G-I3c5b-HISTORICAL permanece BLOQUEADO/ABIERTO**. Un test Python exitoso solo valida el diagnóstico N, no acredita la condición histórica.
- No corregir código ni retrovalidar G05, G09, G00-H. Preservar resultados anteriores y efectuar un contrafactual con y sin puerta de fortaleza solo después de preregistro aparte, controles y fuente histórica suficiente.

**Fuentes de contraste:** [forense x86](E09_02F_INFORME_EJECUTABLE.md), [migración](E09_02F_05_MIGRACION_ANALISIS.md), [invocadores](E09_02I_I3C2_RESULTADO_INVOCADOR_MIGRACION.md), [I3c.4b](E09_02I_I3C4B_RESULTADO_GATE128.md).
