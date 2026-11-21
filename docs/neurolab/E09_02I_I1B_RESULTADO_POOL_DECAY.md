# E09.02i-I1b — decaimiento global de los 256 químicos

**Fecha:** 2026-11-21. **Estado de evidencia:** el bucle del EXE original fue verificado estáticamente, y la aritmética quedó incorporada como una fase opcional con tasas **explícitas**, sin modificar los resultados anteriores de I1/I2.

## Evidencia original directa

- EXE PE32 del usuario, 387.072 bytes, SHA-256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7.
- Se comprobaron **15 firmas de instrucciones x86** y llamada en 0x4221ED a 0x419E40 sobre bytes originales de la sección .text.
- Desde 0x4221CD, la rutina recorre **256 pares de bytes** (concentración y tasa), lee tasa en +1, salta el cálculo si concentración0, invoca el helper y escribe el nuevo valor en +0; aumenta puntero en2 y repite.
- [Auditor reejecutable](../../experiments/neurolab/e09_pool_decay_audit.py), [preregistro](E09_02I_1B_POOL_DECAY_PRE_REGISTRO.md), [fixture derivado](resultados/e09i1b_pool_decay_inspeccion_original.json).

## Adaptación de laboratorio

- [Función pura de decaimiento](../../experiments/neurolab/e09_pool_decay.py) utiliza la implementación existente [C1 decay](../../experiments/neurolab/c1_decay_math.py), acepta pool256, rates256 y tick lógico; no cambia tasas, cerebro, receptores ni reacciones previos.
- El wrapper de química ejecuta I1 primero (emisor→receptor→reacción), **luego** decae pool; preserva en la traza el resultado pre-decaimiento y lo mantiene separado de los bytes ya escritos en loci neuronales.
- [Pruebas](../../experiments/neurolab/tests/test_e09_pool_decay.py) y [auditor sintético adversarial](../../experiments/neurolab/tests/test_e09_pool_decay_audit.py). Oráculo aislado anterior: concentración200 tasa80, tick6→200, tick7→194.
- La interfaz exige un vector completo de tasas declarado: **no es válido suponerlas a partir de la estructura del EXE**. No se inspeccionaron los bytes de half-lives del GEN original en esta intervención.

## Puertas y restricciones

- G-I1b-X86: correspondencia del bucle y helper **verificada estáticamente para ese build**.
- **G-I1b-MATH validada en su alcance técnico**: [CI #44951833784](https://github.com/mxlzz/Nilo_public/actions/runs/44951833784) **success integral: 401 tests, 2 expectedFailure históricos**. CI verifica códigos y oráculos sintéticos; los bytes EXE auténticos se inspeccionaron localmente.
- **G-I1b-RATES ABIERTA:** los valores por sustancia para el GEN original no se recuperaron todavía. Las tasas usadas en tests son sintéticas.
- **G05/G09/G00-H ABIERTAS:** el puente no es un Norn fiel; una prueba de aprendizaje sin tasas identificadas históricamente sería un experimento N con parámetros declarados, no evidencia histórica.

La implementación original de I1/I2 permanece disponible como control sin decaimiento; no modificar retrospectivamente sus métricas. PR #103 draft, main/Nilo intactos.
