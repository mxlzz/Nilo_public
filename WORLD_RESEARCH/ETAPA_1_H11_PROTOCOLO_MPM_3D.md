# Etapa 1 — H11, protocolo antes de código: prueba mínima de MPM plástico 3D existente

**2026-11-22 · PRERREGISTRADO. Estado inicial: NO EJECUTADO.** Decisión comparativa: [ADR-0007](DECISIONES/ADR-0007_GATE_MPM_3D.md). Seguir [procedimiento rector](PROCEDIMIENTO_Y_AUDITORIA.md); sin cambios a `main`, NeuroLab ni Nilo. Ensayo exploratorio específico, etapa 1 ABIERTA.

## Objetivo e hipótesis

¿La implementación **ya existente** de MPM 3D + material `Sand` (Drucker–Prager) puede producir un cambio volumétrico y de forma causado por gravedad y por resistencia/fricción del material, manteniendo inventario por partícula y sin patrones dibujados a mano? H9 conservó masa sedimentaria superficial, H10 comprobó contactos de granos rígidos sin deformación. H11 analiza **otra física**: material deformable con constitutivo continuo, no granos rígidos ni ecosistema.

**Predicción falsable:** una columna 3D de arena, modelada como puntos materiales en un dominio fijo, caerá y cambiará su distribución espacial en el escenario activo con gravedad, mientras que bajo g=0 la geometría no cambiará; cambiar únicamente el ángulo de fricción interna de 30° a 0° debe producir un cambio medible en la distribución. El solver puede fallar por inestabilidad numérica, error del adaptador o porque los parámetros escogidos sean demasiado cortos para distinguir fricciones. No convertir esas fallas en «aprobado» relajando el protocolo.

## Reutilización, mínima implementación y dependencias

- Proveedor: [PINNeAPPle](https://github.com/PINNeAPPle-Labs/PINNeAPPle), fuente `pinneapple_simulation/particle_dynamics/geo_mpm.py`, commit externo fijado `c8a6e3dce5daedd10903cc68f7f3a062c42b8bc4`, Apache-2.0. Su código se importa desde checkout temporal en GitHub Actions, **sin copiar clases ni ecuaciones en Nilo**.
- Ejecutar en Python 3.11 CPU, PyTorch CPU wheel, NumPy, xarray. No instalar la suite PINNeAPPle completa ni componentes gráficos, UI, LLM, bibliotecas de CAD o servidores. Restringir threads PyTorch a 1 para replay.
- Un solo `xarray.Dataset` guarda inventario material por ID de punto (kg), obtenido al crear el escenario; el arreglo `m` del solver es parámetro/caché de cálculo, **no otro stock sumable**. Registro de posiciones, velocidades, deformación (`F`) como observaciones del solver. El método `step` y el constitutivo permanecen upstream.
- Escenario CPU pequeño: caja de dominio (0.60,0.24,0.36)m, `dx=0.025m`, suelo `floor="friction"`, otras fronteras `walls="slip"`, `wall_friction=0.5`, material `Sand(E=20000Pa,nu=0.3,rho=1600kg/m³)`, volumen inicial rectangular de (0.075,0.075,0.075)m a (0.225,0.15,0.225)m, `ppc=1`. Se espera un conjunto discreto pequeño; solo se evalúan puntos realmente sembrados por la API. t final `0.25s`, imágenes de salida t0 y t0.25, sin rendering.
- Casos: **A** g=(0,0,-9.81)m/s² y fricción interna 30°; **B** g=(0,0,0) y fricción interna 30°; **C** g=(0,0,-9.81) y fricción interna 0°; **A_replay** repite A exactamente. Todas las demás condiciones iguales. No imponer que A alcance reposo en 0.25 s.

## Controles preestablecidos

1. **Estado y solidez:** tres dimensiones, 10–1000 partículas, masa inicial estrictamente positiva/finita, coordenadas iniciales y finales finitas, volumen por punto finito y positivo, masas sin variación; registrar masa total, semilla (si upstream tiene RNG, también), versión upstream/torch, tiempos de ejecución, máximo de partículas en bordes (clamp). Rechazar identificadores, kg, masa negativa, campo no finito o entrada externa de material.
2. **Causalidad gravedad:** centro de masa A desciende **>0.015m** en 0.25s y alguna coordenada longitudinal difiere al menos `0.005m`; la dispersión lateral inicial/final y altura quedan reportadas. Sin g, desplazamiento máximo desde inicio **<1e-8m**, velocidades máximas `<1e-8m/s` (si el modelo posee tensiones iniciales no nulas, será un fallo científico/arnés a diagnosticar, no aprobar).
3. **Fricción interna:** comparar cuantiles extremos de x/y y altura para A y C, con exactamente la misma gravedad y parámetros salvo `Sand.friction_deg`. La diferencia L1 media de posiciones de puntos correspondientes debe ser **>0.002m**. Registrar también runout x (q99) y velocidades: la diferencia no se puede atribuir a otra condición inicial.
4. **Conservación:** tras 0.25s, masa de cada punto en solver es igual a su valor inicial y coincide con owner xarray; **tolerancia 1e-12 relativa** para masa por partícula y total. La suma material no depende de `det(F)` porque éste modifica volumen/densidad, no crea masa. No asumir conservación de energía mecánica o térmica.
5. **Control de integridad:** simular corrupción del owner con 1 kg extra, masa negativa, unit g, ID alterado; todos deben ser rechazados antes de commit y mantener hash del caso válido; no reescribir datos del solver para forzar cierre del balance.
6. **Reproducibilidad:** A y A_replay devuelven exactamente mismos arrays numéricos (posiciones, velocidades y masas) bajo mismo intérprete/threads CPU; guardar un snapshot owner+posiciones en NPZ/NetCDF de prueba y verificar lectura con checksum sin pickle. Registrar si hay diferencias entre procesos; no extrapolar determinismo multiplataforma.
7. **Límites:** medir si queda deformación/dispersion neta en 3D, pero **no** declarar una configuración estable persistente a menos que un segundo ensayo longitudinal lo demuestre. Mantener el benchmark GeoTaichi y comparación con publicaciones como gate posterior para calibrar constitutivo y plasticidad.

## Criterio de salida

**ACEPTAR** como demostración limitada de cambio de forma/materia deformable 3D si los puntos1–6 pasan. **NO ACEPTAR** si hay fallos, errores de importación o contactos sin diferencia de fricción. Si fallan requisitos de entorno (CPU/torch), detener y registrar; evitar instalar familias de dependencias innecesarias. Si el resultado cumple, proponer ensayo longitudinal de estabilidad y comparación independiente, pero no adoptar aún un motor del mundo. Ningún avance en etapas 2–8 se declara formalmente.
