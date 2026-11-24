# E09.02i–I3c.5b-H — semántica de dendrita agotada en el EXE original

**21/11/2026 · NL-EXP-I3c5b-H-v1 · evidencia de x86 REAL, verificación ESTÁTICA.**

## Procedencia

Fuente exacta: archivos de la carpeta Google Drive `neurolab` facilitada por el usuario. **Creatures.exe** de 387.072 bytes, SHA256 **548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7**, PE32 con image base 0x400000 y sección .text VMA0x401000. **dad1.gen** de 10.001 bytes SHA256 **e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4**. Las huellas se calcularon sobre bytes realmente descargados; el EXE y el genoma **NO se publican**.

Se desensamblaron ventanas locales con GNU `objdump -D -M intel` y se contrastaron **siete bloques x86 completos** contra el EXE con hashes SHA256 independientes del contenido de cada bloque. [Evidencia JSON](resultados/e09i3c5b_h_strength0_x86_original.json) (solo direcciones, longitudes y fingerprints, no binario), [auditor independiente](../../experiments/neurolab/e09_i3c5b_exe_static_audit.py) y [tests sintéticos adversariales](../../experiments/neurolab/tests/test_e09_i3c5b_exe_static_audit.py). En CI el original no está presente: los tests prueban parser/contrato; la verificación real de siete bloques se hizo localmente contra el archivo aportado.

## Descodificación de la ruta específica

1. **Cálculo de entrada (VA 0x403F2F–0x403F4D)**: en el bucle de dendritas el motor lee el output de la neurona fuente `[edi+2]` y el peso STW `[esi+7]`, los multiplica y desplaza 8 bits. **Ese bloque no verifica fuerza `[esi+9]`**. Si la neurona fuente sigue referenciada y emite, y STW es mayor que cero, la fuerza cero no la silencia por sí sola. Hay una compuerta por actividad de la fuente, no por fortaleza.
2. **Entrada a la actualización (VA 0x4041A1–0x4041BC)**: el programa sí lee `strength=[esi+9]` y, cuando es cero, **incrementa contador de conexiones agotadas** mediante la instrucción en `0x4041B8`. El salto `jne 0x4041BC` del caso no agotado y la rama `inc` del caso agotado convergen en `0x4041BC`, que entra a la regla de susceptibilidad, **sin salto de descarte de la sinapsis**. Esta coincidencia está verificada en los bytes.
3. **Plasticidad (VA0x404306, 0x404451)**: la decisión de entrar al bloque de refuerzo numérico depende de **susceptibilidad** `[ebp+0]`, no de `strength`. La rutina de STW/LTW usa `[esi+7]` y `[esi+8]`. Por tanto, un slot con fuerza0 no queda incondicionalmente excluido de plasticidad posterior, si su susceptibilidad se regenera.
4. **Pérdida de fortaleza (VA0x4047B9–0x4047E2)**: cuando la fortaleza desciende hasta0, el motor borra **susceptibilidad, STW, LTW** y dos bytes de la neurona receptora. Esto obliga a separar (a) fuerza cero desde un evento de borrado y (b) posibles pesos numéricos nuevos después del borrado en ticks sucesivos. Una lectura puntual de LTW de slot strength0 NO prueba retención o conectividad útil.
5. **Migración posterior (VA0x404939–0x40494C)**: la ruta Type1 se invoca después de WTA sólo para receptores con salida positiva. La migración depende del scheduler y del pool de fuentes, no equivale automáticamente a la adquisición de conexión aprendida.

## Comparación con NeuroLab N

La auditoría [I3c.5b N](E09_02I_I3C5B_RESULTADO_STRENGTH0.md) había encontrado `strength0/STW255` con señal127 (frente0 con STW0), y modificación de STW0→241 con strength aún0. **El mecanismo está respaldado por el flujo de código original para este EXE**: la sospecha de que toda señal con fuerza cero debía ser forzosamente bloqueada era un supuesto falso para el bloque observado. No debe introducirse artificialmente una puerta `if strength == 0: signal=0` sin otro fundamento.

**Límites:** evidencia **estática** de los bloques y del flujo local; no ejecución del juego, validación temporal del motor completo, genealogía completa de pool/PRNG, ni equivalencia global de valores a todos los ticks. La ausencia de guardia en el bloque no significa que cualquier slot agotado retenga memoria indefinidamente: la limpieza real borra pesos al perder fortaleza. Esta prueba **no** cierra G05, G09 ni G00-H completos.

## Decisión trazable

- **G-I3c5b-H-LOCAL: VERIFICADA ESTÁTICAMENTE** en este EXE de SHA bloqueado, por siete anclas y flujo de control.
- **No corregir** `class_signal` para descartar fuerza0: el cambio divergiría del mecanismo estudiado. No confundir compatibilidad local con equivalencia global.
- La evidencia del [I3c.5a](E09_02I_I3C5A_RESULTADO_CREDITO_DIFERIDO.md) requiere un control adicional de **disponibilidad antes del feedback**: en el artefacto original, al primer tick de las 400 ramas había 8/8 fuerzas en cero. Algunos brazos recuperaron fuerza brevemente tras el pulso, pero todos terminaron agotados. No usar ese resultado como demostración de aprendizaje.
- [I3c.5c](E09_02I_I3C5C_DISPONIBILIDAD_TRONCO_PRE_REGISTRO.md) investiga descriptivamente el momento de agotamiento, antes de tocar parámetros o introducir variantes.

**G05, G09, G00-H siguen ABIERTAS.** `main` y Nilo0.7 sin modificaciones, PR#103 experimental/draft.
