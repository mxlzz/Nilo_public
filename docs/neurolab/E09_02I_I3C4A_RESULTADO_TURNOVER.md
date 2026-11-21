# E09.02i-I3c.4a — auditoría de recambio y LTW, resultado POST HOC

**Fecha: 2026-11-21.** Tipo: auditoría observacional retrospectiva, NO repetición confirmatoria ni éxito de G05/G09. [Preregistro I3c.4a](E09_02I_I3C4A_TURNOVER_PRE_REGISTRO.md) anterior al observador; [código read-only](../../experiments/neurolab/e09_i3c4a_turnover_observer.py); [tests](../../experiments/neurolab/tests/test_e09_i3c4a_turnover_observer.py); [workflow #44960961073](https://github.com/mxlzz/Nilo_public/actions/runs/44960961073) **SUCCESS: 4 tests específicos y las 20 semillas auditadas**. Artefacto completo **neurolab-i3c4a-turnover-exact-replay**, ID **14728999464**, JSON de eventos por conexión, retención hasta 2027-02-19.

## Controles de integridad

- El observador no modifica ni una instrucción del simulador I3c.4. Intercepta solo la respuesta inmutable del método step, contando cambios y salidas de Type1.
- Para cada semilla 900..919 se reprodujo exactamente la salida numérica original de [I3c.4 corregido](E09_02I_I3C4_RESULTADO_QUIMICA_APAREADA.md) según el archivo de [20 fingerprints SHA256](resultados/e09i3c4_golden_seed_hashes.json). Toda discrepancia detiene el análisis.
- Se verificó que cada cambio de source_pointer tiene evento accepted y que el número de contactos recableados no se confunde con el número de ticks con ≥1 migración. La química B/Y/F continúa apareada.
- Historial de correcciones del **auditor** preservado: [primera CI fallida #44960853419](https://github.com/mxlzz/Nilo_public/actions/runs/44960853419) por leer campo run_id en fixture cuyo campo real es workflow_id; [segunda CI fallida #44960904099](https://github.com/mxlzz/Nilo_public/actions/runs/44960904099) por buscar snapshots de aprendizaje en F, que es congelado y nunca aprende. Se corrigieron solo lecturas/observación. [CI definitiva #44960961073](https://github.com/mxlzz/Nilo_public/actions/runs/44960961073) satisfactoria.

## Resultados acumulados de 20 semillas por fase

| Métrica | Y primera | Y invertida | P primera | P invertida |
|---|---:|---:|---:|---:|
| Conexiones Type1 migradas | **1698** | **1679** | **1700** | **1679** |
| Ticks con alguna migración | 1401 | 1386 | 1402 | 1385 |
| Con LTW positiva **antes** del recableado | **0** | **0** | **0** | **0** |
| Con STW positiva antes del recableado | 1 | 4 | 1 | 3 |
| Unidades totales LTW al terminar entrenamiento | **0** | **0** | **0** | **0** |
| Contactos agotados al terminar (suma20) | 49 | 48 | 49 | 47 |

Controles: B no migró y terminó la primera fase con **1 unidad LTW en toda la cohorte**, segunda con **0**, y 76/77 contactos agotados; F no migró ni modificó sus pesos, LTW0 y fortaleza positiva. En Y/P las migraciones restauran experimentalmente fortaleza2/LTW0; **eso NO es una regla genética original confirmada**.

## Duración entre migraciones de un mismo slot

Calculado sobre eventos exactos por identidad de slot (owner, clase) para cada semilla, SIN sumar contactos como si fueran neuronas diferentes:

- **Y primera:** 1618 intervalos observados; media **19,565 ticks**, mediana **20**, rango **8–42**.
- **Y invertida:** 1599 intervalos; media **20,028**, mediana **20**, rango **11–45**.
- **P primera:** 1620 intervalos; media **19,537**, mediana **20**, rango **8–42**.
- **P invertida:** 1599 intervalos; media **20,028**, mediana **20**, rango **11–45**.
- **Todos los intervalos entre migraciones consecutivas registrados son menores que los 128 ticks de la puerta de LTW.** Esto describe las sustituciones observadas, pero NO demuestra automáticamente que ningún contacto haya estado vivo en tick128: hay conexiones iniciales y últimas cuya duración no queda cubierta por intervalos cerrados.

## Interpretación y límites científicos

**Comprobado en esta reducción:** el recableado del Norn simplificado ocurre con abundancia, pero casi siempre encuentra conexiones con STW0 y siempre LTW0; en los estados de entrenamiento finales no persiste LTW en Y/P. Esto ofrece un mecanismo plausible para el fracaso conductual I3c.4 (Y≈B≈F), distinto de «la migración no funciona».

**NO probado:** que el recambio por sí solo cause la ausencia de aprendizaje, que ningún contacto haya alcanzado t128, que el original C1 tenga estas duraciones o parámetros de fortaleza, o que alguna sinapsis migrada debiera preservar su memoria previa. La función Type1 es derivada del EXE, pero la arquitectura y su activación post-WTA, selección de fuentes y valores iniciales son convenios N. Los datos de I3c.4a son post hoc sobre semillas observadas.

**Próximo paso:** [I3c.4b preregistro observacional](E09_02I_I3C4B_GATE128_PRE_REGISTRO.md): medir EN los ticks de actualización LTW cuántas dendritas tienen realmente STW, susceptibilidad y refuerzo disponibles antes/después del paso numérico y borrado/migración, conservando hashes originales. Sin agregar neuronas ni ajustar dosis, tasa, RNG o genes. G05/G09/G00-H siguen ABIERTAS; PR #103 draft, main/Nilo0.7 intactos.
