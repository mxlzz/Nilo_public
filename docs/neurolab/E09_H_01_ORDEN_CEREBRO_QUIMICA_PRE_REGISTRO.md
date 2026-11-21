# E09h.1 — auditoría de orden de actualización cerebral y bioquímica C1

**Fecha:** 2026-11-21. Registro tras una primera inspección exploratoria del ensamblado, **antes de programar el verificador independiente**. No es un preregistro ciego respecto de las direcciones identificadas.

## Fuentes controladas

Se volvieron a recibir los archivos originales del usuario y se calcularon localmente sus huellas:
- `Creatures(1).exe`: 387.072 bytes, SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`, **idéntica** a la documentada en E09f.
- `dad1(1).gen`: 10.001 bytes, SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`, **idéntica** a E00.
- Ambos se inspeccionan localmente y **no se suben ni redistribuyen**. PE32 i386 (ImageBase 0x400000), con sección .text RVA0x1000/offset0x400, validado con `objdump`.

## Preguntas y verificaciones congeladas

1. **Ruta de actualización normal en criatura** en `0x407540`: identificar por calls directos y orden de dirección `0x407583→0x403BB0` (brain), `0x407595→0x421E70` (biochemistry) y `0x4075A6→0x40A4B0` (selector conductual). Registrar condiciones previas; **no** asumir que se ejecuta en todas las ramas (existe modo alternativo).
2. **Orden de lóbulos** del brain tick `0x403BB0`: comprobar instrucción `mov ebp,5`, inicio en `brain+0xD0`, stride `0xC8` para cinco lóbulos iniciales, posterior llamada `0x403C87→0x403CD0` sobre `brain+8` y después `0x403CA5→0x403E00` desde `brain+0x4B8` para lóbulos restantes. No inferir sincronía global simultánea. El calendario puede tener dependencias de un ciclo entre lóbulos.
3. **Orden de etapas químicas dentro de `0x421E70`:** lectura de contadores `[edi+0x128C]` al principio (emisiones), `[edi+0x1288]` a continuación (receptores), `[edi+0x1290]` después (reacciones); último bucle de 256 concentraciones y llamada a `0x419E40` para decaimiento. Verificar que emisiones escriben en el pool químico y receptores lo leen, antes de interpretar las etiquetas.
4. **Consecuencia de orden, aún hipótesis:** recompensa generada en la fase de reacciones llega demasiado tarde para receptores del mismo `0x421E70`. Si ninguna otra ruta interviene, afecta el cerebro al menos un ciclo posterior al que generó la reacción. Distinguir latencias **por orden estático** de mediciones reales con el juego ejecutándose.
5. **Integridad de evidencias:** verificador Python sin dependencias binarias externas, obligado a comparar hashes, offsets PE, bytes de encabezado y destinos relativos E8; probar parser también contra un PE sintético mínimo con fixture no propietario. CI no dispone de los originales: allí se probará únicamente el verificador, no se afirmará que reanalizó la copia real.
6. **Puerta de alcance:** cerrar *solo* identificación estática del orden de esas rutas si concuerdan todos los oráculos locales; no cerrar todavía scheduler completo, química cuantitativa ni G00-H/G05/G09. Evitar tunear la microred o añadir neuronas.

## Acciones tras ejecución

Versionar el código del verificador, sus tests sin binarios propietarios, un JSON breve de evidencia obtenida **sobre el archivo aportado**, y un informe que distinga instrucciones observadas, inferencias y límites. Marcar E09h.1 parcial si falta probar rutas indirectas o frecuencia del planificador global. La siguiente unidad E09h.2 debe elegir una sola pregunta del orden químico con mayor impacto en la fidelidad antes de desarrollar una simulación.
