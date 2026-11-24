# E09.02i-I3c.4b — resultado de auditoría LTW128 sobre I3c.4

**21-11-2026. Observación POST HOC, no confirmatoria.** [Preregistro](E09_02I_I3C4B_GATE128_PRE_REGISTRO.md), [módulo observador](../../experiments/neurolab/e09_i3c4b_ltw_gate_observer.py), [CI #44961418723](https://github.com/mxlzz/Nilo_public/actions/runs/44961418723): **SUCCESS, 4 tests específicos, 20 seeds900..919 con SHA256 de cada corrida idéntico al I3c.4 original**. Artefacto completo **neurolab-i3c4b-ltw-gate-witness**, ID **14729668186**, retención hasta 2027-02-19.

## Método

La auditoría llama a la función sináptica C1 existente sobre el estado ANTERIOR en cada tick de entrenamiento divisible por128, y coteja la transición efectivamente producida por la microred sin tocar sus reglas. 20 semillas, fases A e invertida, 60 instantes elegibles por fase (t128/256/384 primera, t512/640/768 inversión), cuatro contactos =240 evaluaciones por brazo y fase. F congelada no tiene actualización de LTW.

## Resultados

| Brazo | STW post-C1 positiva en gate, fase1 | Incremento LTW, fase1 | STW positiva, inversión | Incremento LTW, inversión |
|---|---:|---:|---:|---:|
| B, sin migración | 20 | 20 | 24 | 24 |
| Y, migración y química apareada | **1** | **1** | **1** | **1** |
| P, migración on-policy | **1** | **1** | **2** | **2** |

- Refuerzo sináptico positivo específicamente en gates: B 8/8, Y 1/1, P 1/2 por fase (primera/invertida).
- Conexiones con fortaleza0 **antes** del gate, sobre240 evaluaciones por fase: B225/218, Y140/121, P141/120. Migraciones Y/P ocurridas EN gate: 14/10 por fase.
- Ninguna unidad LTW se borró por fortaleza en el **mismo tick gate**. Pocas conexiones Y/P muestran siquiera STW positiva en los ticks elegibles. Los pequeños aumentos no permanecieron hasta el final del entrenamiento (I3c.4a), pero su pérdida es **posterior**, no simultánea con el gate.
- **Advertencia de validez del control B**: en la primera fase **12 de sus 20** aumentos numéricos LTW ocurrieron en conexiones con fortaleza previa0; inversión **12 de24**. De esos 12, **11** permanecían en fortaleza0 después del tick en cada fase. El motor reducido sigue calculando STW/LTW en algunos slots agotados: esto no equivale a memoria funcional y NO demuestra cómo se comporta el motor entero C1. Requiere auditar semántica de fuerza0 antes de modificarla.

## Interpretación y decisión

**H-G (falta de STW en ventana): observada** para la mayoría de contactos migratorios Y/P. **H-D (borrado de LTW dentro del mismo gate): no observada.** **H-P (borrado posterior): compatible** con [I3c.4a](E09_02I_I3C4A_RESULTADO_TURNOVER.md). La coincidencia temporal entre refuerzo, STW y ventanas LTW es un cuello de botella plausible del modelo reducido, **no causalidad única demostrada**.

En particular, B **sin migración** también registra ~50% de acierto en I3c.4: el fracaso de aprendizaje no se explica solamente por el recambio. La próxima unidad debe volver a **G05, atribución del refuerzo a contexto/decisión causante** antes de incrementar conexiones o modificar tasa/dosis.

**G05, G09 y G00-H permanecen ABIERTAS.** PR #103 draft, sin merge a main ni cambios al motor Nilo0.7.
