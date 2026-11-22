# NeuroLab I3c.7c — auditoría reproducida de extinción del refuerzo directo

**21/11/2026. POST HOC, MISMA COHORTE, NO NUEVO HOLDOUT.** [Preregistro retrospectivo antes del auditor](E09_02I_I3C7C_EXTINCION_PRE_REGISTRO.md) · [código](../../experiments/neurolab/e09_i3c7c_extinction_audit.py) · [CI #44968676147](https://github.com/mxlzz/Nilo_public/actions/runs/44968676147) **SUCCESS 6 tests**, artefacto `neurolab-i3c7c-exact-replay-and-extinction` ID14732582942, con nuevo JSON completo y reporte de extinción. Se volvió a ejecutar `I3c.7b` en las 20 semillas1500..1519 y **el JSON de12.128.800 bytes resultó idéntico al original byte por byte: SHA256 `2660ba63b866abfff469d754ff88cab8941b215b1078a652ddc52dfca0cce8a6`**. No se cambió el simulador, rate, fuerza, direct255, precursor80, timing ni semilla.

## Secuencia original verificada con sus denominadores

**80 coordenadas**, cada una con 4 ramas N/M/C/F, y 124 ticks por rama. En `C`:
- **Tick7**, inmediatamente después del único pulso directo: 80/80 ramas tienen STW positiva en al menos una dendrita viva y **60/80** tienen STW≥5; las 8 conexiones siguen con `strength>0`.
- **Ticks8 y9:** conservan ese peso en60/80 ramas; **36/80** presentan entrada neural `type0/type1` y scores distintos de N; el primer score distinto ocurre en tick8. La lectura `learn=False` realizada a partir de estados t7 y t9 cambia 22/80 decisiones, **20 mejoras y2 empeoramientos** (72,5% vs N50%).
- **Tick10:** **80/80** ramas de C, N y M tienen **8/8 conexiones fuerza0** después del tick; no conservan STW funcional ni LTW positiva. La señal `type` calculada **antes de actualizar** este tick todavía puede ser distinta de cero para36/80: no confundir lectura de estado viejo con persistencia post-tick.
- **Tick11:** 0/80 con entrada `type` positiva. **Ticks16 y128:** 0/80 decisiones de C o M difieren del neutro, y exactitud =50% en todos. No hay retención.
- **F:** conserva8/8 conexiones hasta tick128 por `learn=False` y no genera STW nueva; no mejora conducta. Como las sinapsis congeladas tampoco pierden fuerza, F no es comparador conductual puro.

**Crédito espurio registrado:** las 1196 unidades de efecto numérico de C incluyen **724 en fuente objetivo y 472 en fuente distractora**. En M 20 unidades de efecto sobre fuente objetivo, sin traspasar el umbral de señal; ni la distribución por fuente ni la mejora temporal prueban causalidad sináptica individual.

## Resultado epistemológico

La cadena **pulso directo→STW funcional→entrada Decision→cambio transitorio de elección→pérdida sincronizada de fuerza→extinción** es coherente con las transiciones del modelo y el archivo se reproduce exactamente. Esto **no demuestra** que un evento aislado de atrofia sea causa única de todo el olvido en un Norn original ni descarta el efecto adicional de STW relax. Tampoco constituye aprendizaje autónomo o confirmación G05.

**G-I3c7c-DATA VALIDADA, G-I3c7c-MECHANISM observación post hoc reproducida. G05/G09/G00-H ABIERTAS.** Siguiente: [I3c.7d](E09_02I_I3C7D_COMPARABILIDAD_ATROFIA_PRE_REGISTRO.md), auditar un posible confusor entre línea química con CHEM2/3 nominal16 y benchmark directo previo con CHEM2/3=0. No consumir semillas1400..1419, no tocar `main` ni Nilo0.7.
