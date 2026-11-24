# E09.02e — preregistro: integrar STW/LTW al microcircuito de 5 neuronas

**21/11/2026, antes de implementar.**
Motivo: [E09.02c](E09_02C_RESULTADO_NEGATIVO.md) y [E09.02d](E09_02D_RESULTADO_NEGATIVO.md) no superaron inversión de contingencias. El propio genoma de C1 distingue conexiones de refuerzo excitatorio e inhibitorio, además de STW y LTW. Este experimento contrasta **una hipótesis específica**: si la recuperación/relajación de pesos de corto plazo mejora la reversibilidad sin aumentar nodos ni forzar exploración.

## Línea de evidencia

- Las SVRules neuronales se toman del `dad1.gen`: `ANDTYPE0` para Concept y `STATE + TYPE0 - TYPE1` para Decision; ya verificadas en [E09.02a](E09_02A_PRE_REGISTRO_SVRULE_C1.md) y circuito [E09.02b](E09_02B_MICROCIRCUITO_PRE_REGISTRO.md).
- Las **dos clases** de sinapsis de decisión representan las dos rutas químicas reales: Reward49/CHEM0 para excitación y Punishment50/CHEM1 para inhibición, documentadas en [química C1](E00_QUIMICA_REFUERZO_C1.md).
- La dinámica numérica se reutiliza **sin modificar** de [E04](../../experiments/neurolab/twin_weight.py): `stw += 32*reward`, `ltw` se aproxima 1 unidad al `stw` tras el refuerzo, `stw` se aproxima 6 unidades a `ltw`. **Son coeficientes NeuroLab propios**. No afirmar que el ejecutable C1 aplique estos pasos exactamente.

## Diseño previo

- **Cinco neuronas constantes:** P0,P1,C,D0,D1. Entradas del banco (255,255); concepto C activado a255, sin semántica de objetos.
- **Cuatro sinapsis plásticas:** D0Exc, D0Inh, D1Exc, D1Inh, cada una almacena STW/LTW en rango0..255; estado inicial (0,0), consistente con LTW inicial0 del genoma C1 Decision (aunque aquí no se simula conectividad real 128+128).
- **Selección:** mismos scores `80 + concepto*STWexc/255 - concepto*STWinh/255` saturados al rango0..255, ganador D0/D1; ante empates, misma política aleatoria con semilla y contador que E09.02c. **Sin epsilon nuevo**.
- **Refuerzo:** si D0 es elegida y `Reward=1`, solo D0Exc recibe `TwinSynapse.step(+1)`; si `Punishment=1`, solo D0Inh lo recibe; análogo D1. Otras tres sinapsis reciben `step(0)` cada ensayo para permitir relajación/consolidación. Esto no incorpora química cuantitativa original, sino *dos canales de eventos* separados como en C1. No hay disminución directa de una sinapsis por `-1`; el otro canal inhibitorio compite con ella.
- **Evaluador externo:** oculto al cerebro. D0 recompensada 60 ensayos; holdout80 sin actualizar pesos; luego D1 recompensada 120 ensayos; segundo holdout80.
- **Semillas 0–19**, mismos ensayos y presupuesto de E09.02c/d, baseline sin plasticidad en idénticas condiciones. Este experimento **no cambia** el control de estímulos ni introduce una entrada correcta.
- **Criterio primario** heredado (NO ajustar tras ejecutar): 18/20 semillas con precisión >=0.90 tras entrenamiento original y reversión, ventaja media >=0.30 vs pesos congelados. Informar medias, per-seed, evolución de STW/LTW de las cuatro sinapsis.
- **Condición secundaria:** invertir en más semillas que E09.02c (6/20) sin epsilon. No se considera superado solo por esta mejora parcial.
- **Pruebas de oráculo previo:** una sinapsis (0,0) bajo evento positivo pasa a (26,1) con coeficientes E04, y tras un tick en reposo pasa a (20,2). Sin concepto activo, no reforzar ninguna conexión. Eventos de recompensa/castigo modifican solo la clase elegida, las demás solo se relajan.
- Rechazar feedback repetido/obsoleto, asegurar determinismo checkpoint y que una versión sin plasticidad permanezca constante.

## Interpretación y restricciones

Si el ensayo mejora la reversibilidad, puede afirmar que la memoria a dos velocidades, bajo nuestra regla E04, evitó ciertas preferencias absorbentes. No puede afirmar que **el cerebro original C1** funcione con estos coeficientes, que el circuito de 5 nodos replique las 952 neuronas, ni que exista voluntad o pensamiento espontáneo.

Si falla, conservar configuración, semillas y resultados; no hacer *tuning* post hoc. Siguiente acción se decidirá a partir de dónde falló (consolidación lenta, plasticidad insuficiente, saturación, exploración o conectividad).

Se comparará con ambas ramas previas sin modificar sus archivos ni sus resultados.
