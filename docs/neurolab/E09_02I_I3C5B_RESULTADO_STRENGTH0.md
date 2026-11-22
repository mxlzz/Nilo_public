# E09.02i–I3c.5b — auditoría de conexión agotada (strength=0)

**21/11/2026 — Auditoría N completada; contraste histórico C1 ABIERTO.** [Preregistro](E09_02I_I3C5B_STRENGTH0_PRE_REGISTRO.md) · [observador](../../experiments/neurolab/e09_i3c5b_strength0_audit.py) · [tests](../../experiments/neurolab/tests/test_e09_i3c5b_strength0_audit.py) · [CI 44963927561](https://github.com/mxlzz/Nilo_public/actions/runs/44963927561) **SUCCESS (3/3)** · artefacto `neurolab-i3c5b-strength0-readonly`, ID **14730781072**.

## Hipótesis y método

El [I3c.4b](E09_02I_I3C4B_RESULTADO_GATE128.md) mostró aumentos numéricos LTW en contactos de `strength=0`. Este paso **no modifica reglas ni red**: crea condiciones sintéticas explícitas de conexión agotada, evalúa `class_signal` y un paso real `DynamicContextBrain.step(...,learn=False)`; en caso separado llama la transición existente `update_c1_synapse` con fortaleza inicial0 y CHEM exógeno. Comparaciones siempre entre estados que difieren sólo en STW o configuración controlada. Esta evidencia es de **NeuroLab N**, no del ejecutable histórico.

## Resultados verificados

- En el modelo reducido, una conexión con **strength0 y STW255** aporta **127** unidades de señal a la clase; el mismo slot con **strength0 y STW0** aporta **0**. `DynamicContextBrain.step(...,learn=False)` recibe esa misma señal: el score Decision del fixture cambia **80→207**. Por lo tanto **la fortaleza cero no bloquea la transmisión** cuando existe STW residual.
- Una conexión sintética con **strength0, susceptibilidad255, STW0**, sometida en tick1 a CHEM0=255, registra efecto numérico de refuerzo **241**, STW final **241** y **strength final0**. Por lo tanto **un slot nominalmente agotado puede plastificarse** sin reconectarse en el modelo reducido.
- Los resultados son compatibles con la observación I3c.4b de LTW numérico en slots de fortaleza0, pero **no prueban** que el motor histórico permita el mismo proceso, ni que haya memoria conductual funcional. La regla numérica `update_c1_synapse` no debe confundirse con la condición de entrada del bucle C1 real.
- Los tests y el observador son **de solo lectura** respecto de las bibliotecas existentes; no se corrigió `class_signal`, `C1ContextBrain`, `DynamicContextBrain`, SVRules, `c1_strength` ni migración.

## Decisión y siguiente unidad

**G-I3c5b-N** VALIDADA para diagnóstico del modelo. **G-I3c5b-HISTORICAL BLOQUEADA**: se necesita reexaminar el EXE específico de SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`, en especial el cálculo de dendritas VA 0x403F2F–0x403F8F y su bucle llamante, frente al borrado por strength0 en VA 0x40451E–0x4047E2. El ejecutable original NO se distribuye en GitHub ni está disponible en esta ejecución; los informes forenses previos se conservan, pero no deben sustituir la lectura de los bytes en el punto disputado.

**No modificar a ciegas las reglas** para ignorar strength0 ni interpretar automáticamente como fallo del histórico C1. Si el EXE verifica que se excluye un slot agotado, preregistrar después un contrafactual estricto de una sola regla con muestras nuevas y control igualado. Si no lo excluye, documentar la divergencia intuitiva y verificar qué condición real restaura o migra conexiones.

**G05, G09 y G00-H siguen ABIERTAS.** Nilo0.7 y `main` intactos; PR #103 permanece experimental en borrador.


## Actualización de verificación histórica (posterior al cierre del informe N)

Se recuperó **el mismo EXE original del usuario** desde la carpeta Drive `neurolab` y se verificó el SHA256. La auditoría x86 [I3c.5b-H](E09_02I_I3C5B_H_RESULTADO_X86.md) y sus [siete huellas](resultados/e09i3c5b_h_strength0_x86_original.json) demostraron estáticamente que, en este ejecutable, el cálculo de señal no consulta strength y el bloque de fuerza cero incrementa un contador **sin saltarse la regla de susceptibilidad y la plasticidad numérica**. La rutina de pérdida sí limpia STW/LTW/susceptibilidad al descender fuerza a cero.

**La condición “bloqueada por EXE no disponible” descrita arriba queda SUPERADA en cuanto al flujo x86 local**; se conserva por trazabilidad del estado anterior, no como bloqueo vigente. **G-I3c5b-H-LOCAL VERIFIED_STATIC**. No implica equivalencia dinámica global, ni cierra G05/G09/G00-H. No modificar la semántica N de fuerza0 sin mayor evidencia.
