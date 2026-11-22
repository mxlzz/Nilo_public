# Etapa 1 — H12. Reposo y morfología 3D sin ayuda de paredes

**Fecha:** 2026-11-22. **Estado:** PROTOCOLO ANTES DE CÓDIGO. Requisito anterior: H11 (CI 45055263832, SUCCESS); ver ETAPA_1_H11_RESULTADOS_MPM_3D.md. Etapa 1 ABIERTA; no se alteran main ni NeuroLab.

## Hipótesis y alternativa

H11 demostró deformación a t=0.25s, pero la masa seguía en movimiento y el dominio lateral (0.60×0.24m) podía influir en la expansión. ¿El GeoMPM upstream, con material Sand de fricción interna30°, puede formar un depósito que deje de moverse apreciablemente sin que las paredes laterales lo detengan?

Si la velocidad queda alta, el modelo choca con los límites o la materia se aplasta hasta una lámina por clamping de frontera, el resultado NO autoriza hablar de estructura estable.

## Solver reutilizado y escenario fijo

PINNeAPPle Apache-2.0, geo_mpm.py del commit c8a6e3dce5daedd10903cc68f7f3a062c42b8bc4, sin cambiar ecuaciones. CPU PyTorch y xarray. Dominio 3D (0.80,0.80,0.36)m, dx=0.025m; bloque inicial desde (0.30,0.30,0.075) hasta (0.45,0.45,0.225)m; ppc=1, Sand(E=20000Pa,nu=0.3,rho=1600kg/m³). Suelo con fricción externa0.5, paredes slip, tiempos de observación t=0,0.4,0.8,1.2s.

Casos: A con g=-9.81 y fricción interna30°, B sin gravedad y fricción30°, C con gravedad y fricción interna0°, A' idéntico a A como replay.

## Criterios previos

1. Inventario y masas por punto son finitos, positivos y constantes, y el dueño único xarray conserva identidad/masa. 10–1000 puntos con mismos hashes de masa inicial en A/B/C.
2. A: descenso de centro de masa >0.05m. B: sin desplazamiento ni velocidad detectable (>1e-8) bajo g0.
3. A: **cero partículas** a <=2.5dx de cualquiera de las cuatro paredes laterales x/y al terminar. Medir para B y C.
4. Estabilidad longitudinal: en A a t=1.2s velocidad máxima <0.05m/s; entre t=0.8 y1.2s cambios individuales de q01 y q99 de x/y <0.005m, y de q99 de z <0.005m.
5. Volumen geométrico vertical de envolvente cuantilar en z mayor que una celda dx=0.025m. Fracción de puntos exactamente clamped en z=1.5dx <=50%. Si no se cumple, no declarar masa 3D físicamente apoyada.
6. Comparar A y C midiendo extensiones laterales, cambios de posición y velocidades sin asumir que fricción0 causa un patrón final particular.
7. A/A' idénticos en posiciones, velocidades y masa en snapshots de t=0,0.4,0.8,1.2. Registrar métricas en WORLD_EVAL_JSON aun cuando falle un gate, y fallar el job.
8. Los modelos siguen sin calibración geotécnica, sin acoplamiento a ROI, sin fuente material, sin energía y sin persistencia de estado interno del solver.

**Resultado:** H12 aprobada solo si 1–5,7 se satisfacen; en caso contrario informe de no-aprobación y causa observable sin cambiar parámetros a posteriori. No cerrar la etapa1 ni elevar H12 a emergencia o morfología natural.
