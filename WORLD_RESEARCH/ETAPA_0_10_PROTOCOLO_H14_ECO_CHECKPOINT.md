# E0.10 — H14: checkpoint de ecología + geomorfología durante 90 días

**Estado:** protocolo registrado ANTES de implementar. Fecha 2026-11-21, etapa 0 ABIERTA.
**Motivación:** H13a demostró checkpoint de agua superficial e infiltración entre procesos; H9 demostró continuidad de 90 días con `SoilMoisture+Vegetation+DepthDependentDiffuser`, pero nunca persistencia de sus tres estados. Para un mundo autónomo y recuperable necesitamos ambas líneas. H14 no integra todavía los dos sistemas ni sustituye un modelador existente.

## Referencias verificadas
- H9, ejecución CI https://github.com/mxlzz/Nilo_public/actions/runs/44951992403 , código `experiments/probe_landlab_90day_loop.py`, escenario húmedo con 12mm lluvia cada cinco días, 1h tormenta +23h intertormenta cada día, PET 8mm/día, 3 periodos de difusión conservativa `dt=1/3` estación, `Kd=2.5e-4 exp(-0.3V)` m²/estación (Sharma/Ehlers 2023), grilla 8×8 dx1m y suelo móvil inicial 0.6m.
- H13a, Python pickle del conjunto de instancias del solver, **solo cargar desde checkpoint propio**, comparación exacta en procesos separados.
- Objetivo H14: demostrar que los campos, el tiempo, los parámetros y las instancias de estado de H9 se restauran y reproducen exactamente a partir de un checkpoint en **día 45** (entre ventanas geomorfológicas) hasta completar día 90.

## Especificación y tests
1. **Baseline**: importar H9 estable sin modificar y ejecutar `scenario(True,0.3)` durante 90 días, guardar perfil completo de suelo/topografía nodal y salidas de ventanas (día30, 60,90) en archivos NPZ/JSON de referencia, con hash/versión de Landlab.
2. **Prepare**: ejecutar el MISMO contrato H9 con el motor Landlab, 45 días (solo difundir después de día30), empaquetar grilla, SoilMoisture, Vegetation, DepthDependentDiffuser, array de velocidades por link, reloj y progreso, historia mensual e inventario inicial; serializar juntos a pickle de archivo **generado por nosotros** y metadata de versión+checksum SHA-256.
3. **Resume en otro intérprete**: cargar pickle propio, comprobar `component.grid is grid` para 3 componentes; continuar desde día46 al día90 con 2 ventanas geomorfológicas restantes, sin repetir día45 ni resetear biomasa/lluvia/tiempo.
4. **Comparar**: suelo y topografía por nodo idénticos bit a bit con H9, y 3 ventanas con mismas cifras de humedad, biomasa, cobertura, volumen y fracción de año. Registrar estado final, checksum, bytes, material sólido conservado <0.01% y variables finitas, profundidad de suelo no negativa.
5. **Control**: sin mutaciones a H9 baseline, condiciones iniciales, fórmulas ni tolerancias para 'hacer pasar' la prueba. Si falla pickle o replay, conservar fallo y diagnosticar qué estado faltó; no falsificar ni reiniciar desde semilla alegando persistencia.
6. **Alcance**: la prueba no guarda `Radiation`/PET de H10b ni un solver de agua infiltrada; comprueba el par eco-geomorfológico, no el estado mundial completo. Persistencia entre SO/versiones y costo a grandes escalas siguen bloqueantes.

**Próximo gate:** H14 exitosa permite planificar un checkpoint común de todos los subsistemas, pero unir los presupuestos hídrico y sólido exige modelo de suelo no saturado válido. DRYP2 como alternativa no se descarta por falta de ejecución.
