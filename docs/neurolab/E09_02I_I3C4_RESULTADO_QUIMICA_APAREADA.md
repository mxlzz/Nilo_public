# E09.02i-I3c.4 — resultado NEGATIVO de aprendizaje con química apareada y migración activa

**2026-11-21.** [Preregistro previo](E09_02I_I3C4_QUIMICA_APAREADA_PRE_REGISTRO.md) · [runner](../../experiments/neurolab/e09_i3c4_yoked_metabolic.py) · [tests](../../experiments/neurolab/tests/test_e09_i3c4_yoked_metabolic.py). [GitHub Actions corregida #44960526007](https://github.com/mxlzz/Nilo_public/actions/runs/44960526007) **success: 8/8 pruebas específicas y 20 semillas completas**. Artefacto íntegro **neurolab-i3c4-chemical-yoked-four-arm**, ID **14729775966**, con datos por semilla, retención hasta 2027-02-19. [Fingerprints SHA de 20 semillas](resultados/e09i3c4_golden_seed_hashes.json) guardados ANTES de instrumentar diagnóstico I3c.4a.

## Condiciones

20 semillas **900..919**, fases A e inversión B, 60 ensayos de entrenamiento y36 holdout sin plasticidad por fase. Cuatro ramas de seis neuronas/cuatro conexiones:
- **B:** sin migración, plasticidad y recompensa propia.
- **Y:** CON migración, plasticidad y calendario de precursores del brazo B: su química se verificó **IDÉNTICA a B después de cada tick**.
- **P:** CON migración y recompensa de sus propias decisiones; su química puede divergir de B (comparación on-policy).
- **F:** congelada sin migración, calendario de precursores B; química idéntica a B e Y.

Se reutilizaron genes C1 de reacciones57/71/111/112 y receptores cerebrales, con dosis80 y tasa40 **sintéticas**; no hay emisores cerebrales automáticos ni cuerpo; la migración inicializa strength2/LTW0 como convención N, RNG local Python, no CRT original. Se preservó identidad de cuatro conexiones y ausencia de fuga del evaluador.

## Exactitud de elección en holdout: media de 20 semillas

| Brazo | Primera asociación | Inversión |
|---|---:|---:|
| B, sin migración | **0,48472** | **0,50417** |
| Y, migración, química igual a B | **0,48472** | **0,50694** |
| P, migración on-policy | **0,48611** | **0,50694** |
| F, congelada | **0,49028** | **0,50417** |

Contraste primario exploratorio **Y−B**: primera fase **0,00000** (IC bootstrap cluster95% **[-0,00972;+0,00972]**), inversión **+0,00278** (IC **[-0,00556;+0,01250]**). **No hay una mejora apreciable frente al control químicamente equiparado**. B−F fue −0,00556 y≈0 respectivamente, sin señal de aprendizaje robusto con cuatro contactos. P−B +0,00139/+0,00278, NO causalmente aislable por feedback divergente.

## Migración: distinguiendo CONEXIONES de TICKS

- En Y hubo **3.377 eventos de reconexión Type1 aceptados**: **1.698** primera fase y **1.679** inversión, que ocurrieron en **2.787 ticks** con al menos una aceptación (1.401+1.386).
- En P hubo **3.379 eventos aceptados**: **1.700** primera fase, **1.679** inversión, en **2.787 ticks** con al menos una (1.402+1.385).
- B/F: **0** migraciones. **20/20 semillas Y** tuvieron alguna migración aceptada.
- Un resumen inicial [run #44960312460](https://github.com/mxlzz/Nilo_public/actions/runs/44960312460) etiquetó incorrectamente como número de conexiones el conteo de ticks con ≥1 migración (2.787). **Errata preservada**, no problema del motor: [commit correctivo](https://github.com/mxlzz/Nilo_public/commit/b991dad4ee77bba0b8024acd3912d15a77f75c31) modificó únicamente el agregado, y se añadió prueba que fuerza dos migraciones en un mismo tick. [CI corregida #44960526007](https://github.com/mxlzz/Nilo_public/actions/runs/44960526007) valida 3.377/3.379. No alterar métricas conductuales ni ocultar fallo de contabilidad.

Al final de cada fase (suma de número de contactos agotados, no número de contactos únicos): B **76/77**, Y **49/48**, P **49/47**, F **0/0**. La migración reduce algunos contactos agotados en ese instante, **pero no genera aprendizaje observable**.

## Límites y siguiente diagnóstico

**Comprobado:** la química activa pérdida/reconexión de contactos; la conexión dinámica funciona en un experimento con precursores; el calendario de química en B/Y/F es idéntico; la red B/Y/P no supera aproximadamente el azar en las dos fases. **No comprobado:** que migrar mejore retención, que cada conexión migrada estuviera causalmente vinculada a la decisión, ni que los 3.377 eventos sean duraderos o útiles.

Una gran cantidad de cambios de origen con casi ninguna ventaja conductual hace plausible una hipótesis de **turnover repetitivo / falta de retención**, pero no la demuestra. El próximo paso [I3c.4a](E09_02I_I3C4A_TURNOVER_PRE_REGISTRO.md) es un **observador post hoc sin intervención** que mida vida útil de fuentes, LTW/STW antes y después de desconexión y churn por slot, exigiendo hashes idénticos para las 20 semillas. G05/G09/G00-H abiertas; PR experimental draft, main/Nilo 0.7 intactos.
