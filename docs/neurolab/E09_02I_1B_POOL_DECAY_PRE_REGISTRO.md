# E09.02i-I1b — preregistro del decaimiento global de 256 químicos

**Fecha:** 2026-11-21. **Antes de implementación:** se verificó exploratoriamente el loop x86 en el EXE del usuario; todavía no se creó ningún módulo I1b.

## Dependencia del plan

I1 e I2 acoplaron cerebro y química, pero omitieron la última fase del tick C1: el decaimiento global. **No ejecutar ni interpretar una comparación de aprendizaje prolongado con concentraciones persistentes sin declarar su comportamiento.** En la ruta regular de E09h.1, la química corre **emisor → receptor → reacción → decaimiento**. El receptor no debe leer el resultado de la reacción ni del decaimiento de la misma llamada.

## Evidencia primaria a auditar

EXE PE32 original SHA-256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7.

En el segmento 0x4221CD..0x4221FD: inicializa puntero al pool+8 y contador256; cada entrada contiene un byte de **concentración** en offset0 y un byte de **tasa** en offset1; si concentración no es cero, llama a 0x419E40 con (puntero concentración, tasa, tick); escribe el resultado y avanza con stride2. La función decay C1 ya está implementada en [c1_decay_math.py](../../experiments/neurolab/c1_decay_math.py), con tests anteriores.

## Experimento mínimo y controles (I1b)

- Reutilizar decay() sin modificar ni reimplementar la fórmula.
- Implementar transformación PURA de pool[256] + rates[256] + tick lógico, con copia del resultado y sin estado implícito; validar enteros byte y dimensiones.
- Test fijo: concentración200 tasa80, tick6 →200 y tick7 →194, según decaimiento previo. Confirmar byte0, byte255 y que no cambia posición ajena.
- Test de orden: reacción que genera concentración en el mismo tick puede ser afectada por el decaimiento final; un receptor que muestreó antes permanece con el valor previo, no con el post-decaimiento.
- Verificador estático reejecutable con 15 firmas del loop + llamada E8 a0x419E40 del EXE original (no incluir binarios propietarios en GitHub).
- No inventar tasas: se pasan por argumento. **Un conjunto sintético de tasas permite probar el algoritmo, no reproduce las tasas del genoma de C1**. Registrar origen de cada tasa si más adelante se usa para tareas.
- Mantener el puente I1 original sin decaimiento como control histórico de su propio protocolo; incorporar la opción como transformación adicional separada. No cambiar retrospectivamente sus oráculos.

## Puertas

- **G-I1b-X86:** 15 firmas + llamada x86 con SHA verificado y tests adversariales.
- **G-I1b-MATH:** 256 entradas, orden y copias correctos, CI verde.
- **G-I1b-RATES:** permanece **ABIERTA** hasta comprobar de qué genes/tablas proceden las tasas originales de los 256 químicos y sus valores para el genoma elegido.
- **G05/G09/G00-H:** no se cierran por traducir una fase de química. Sin cuerpo/mundo, sin LLM ni integración Nilo 0.7. PR #103 continúa draft.
