# E09.02i-I3c.2 — ubicación de los invocadores históricos de migración

**Fecha:** 2026-11-21. Estado: **rutas de llamada directas verificadas estáticamente**, no scheduler completo. [Preregistro antes del auditor](E09_02I_I3C2_INVOCADOR_MIGRACION_PRE_REGISTRO.md).

## Procedencia y método

- EXE original aportado por usuario, Windows PE32, **387.072 bytes**, SHA256 **548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7**. Lectura estática local de bytes, sin ejecutar el juego ni subir EXE al repositorio.
- 22 firmas x86 y dos llamadas relativas E8 verificadas sobre la misma imagen .text del ejecutable. [Auditor reproducible](../../experiments/neurolab/e09_i3c2_migration_callsite_audit.py) y [tests sintéticos adversariales](../../experiments/neurolab/tests/test_e09_i3c2_migration_callsite_audit.py). [Evidencia resumida](resultados/e09i3c2_invocador_migracion_original.json).

## Hallazgos delimitados

- El fragmento neuronal contiene WTA en torno a VA0x4048CC y borrado de salidas no ganadoras en 0x4048F8. Después, la fase de migración comienza hacia 0x404911.
- Tipo1: prueba del tipo de clase en 0x404922 (valor1), luego recorre registros neuronales y **salta** la llamada si el byte de salida en registro+2 es cero (lectura 0x404939 y salto 0x40493E). La llamada directa 0x40494C apunta a **0x404A80**, función de migración tipo1 ya reconstruida por separado. La fase recorre dos clases (comparación 0x404967).
- Tipo2: prueba del tipo de clase en 0x404992 (valor2); se consulta el índice de célula seleccionada en 0x404997, donde -1 evita llamada; el índice de registro se escala a **16 bytes** en 0x4049BD. La llamada directa 0x4049C2 apunta a **0x404B90**, función de migración tipo2. También hay dos iteraciones de clase.
- Esto explica que el adaptador de la reducción **no debería** disparar migración indiscriminadamente cada vez que una dendrita pierde fortaleza. El invocador histórico es posterior a la decisión/WTA y tiene puertas de tipo y salida neuronal activa; no se ha demostrado exhaustividad de la distribución de ocasiones de migración.

## Límites y siguiente trabajo

- **G-I3c2-CALLSITE** cubre firmas y rutas directas sobre un único EXE. **No** prueba secuencia real de RNG, cronología en segundos, selección completa de destinatarios o distribución empírica de reconexiones; eso mantiene abierta la reconstrucción histórica integral.
- El modelo C1ContextBrain actual todavía fija Concept por índice de posición y tiene dos fuentes saturadas por clase. **No** se integró Type1 ni se cambió la arquitectura.
- La decisión propuesta sigue siendo evaluar el contrato [I3c.1](E09_02I_I3C1_CONTRATO_MIGRACION_DINAMICA.md) mediante una prueba separada de adaptador dinámico (si se implementa, marcar las diferencias del scheduler original como N y preregistrarlas). No sustituir tasas/genoma no confirmados por supuestos. G05/G09 permanecen ABIERTAS, PR #103 draft, Nilo/main intactos.
