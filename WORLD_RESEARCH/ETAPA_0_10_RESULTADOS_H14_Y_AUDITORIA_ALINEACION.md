# E0.10 — Resultado H14 y retorno al plan rector

**Fecha:** 2026-11-21. **Estado:** H14 APROBADO; etapa 0 general ABIERTA. Este ensayo no altera las decisiones rectoras.
**Hipótesis y protocolo versionado antes de ejecución:** `ETAPA_0_10_PROTOCOLO_H14_ECO_CHECKPOINT.md`
**CI** https://github.com/mxlzz/Nilo_public/actions/runs/44957517450 — **SUCCESS**.
**Ensayo:** `experiments/probe_landlab_eco_checkpoint.py`; baseline intacto `experiments/probe_landlab_90day_loop.py`.

## Lo ejecutado
- Proceso independiente A: escenario H9 con agua de lluvia sintética cada cinco días, `SoilMoisture`→`Vegetation`→`DepthDependentDiffuser` hasta 90 días, en 3 ventanas de 30 días.
- Proceso B: mismas condiciones desde el día cero hasta el **día 45**; serializó grilla, instancias de suelo, vegetación y difusión, velocidad espacial, reloj, periodo de avance, lista de métricas y estado medio del ciclo en pickle propio protegido por SHA-256. Checkpoint **21,274 bytes**, sha256 `81919af6b3cbae5968e177e089bfd51cab2ecd1db46f311a8470a29197869b0b`; Python 3.13.18, Landlab 2.11.0.
- Proceso C: cargó exclusivamente su propio pickle en otro intérprete, verificó `component.grid is grid` para los tres componentes, completó hasta día 90 sin reiniciar el periodo ni borrar memoria del estado.

## Resultados
- Coincidencia **bit a bit** de `soil__depth` y `topographic__elevation` finales respecto a H9 original.
- Coincidencia **exacta** de todas las métricas de las 3 ventanas, incluyendo biomasa, humedad, fracción de cobertura, coeficiente de difusión, volumen y reloj.
- Al día 90 cobertura media **0.7599564988434792**, biomasa media **157.47538508886296**, reloj interno **0.24640657084188877 años**.
- Residual de conservación del suelo móvil **-3.552713678800501e-15 m³**.
- **Aprobado H14:** continuidad recuperable de 3 componentes eco-geomorfológicos Landlab dentro de mismo SO y versión.

## Alcance y restricciones
NO prueba checkpoint de `Radiation`/PET, WorldEngine, clima, caudal/agua infiltrada de H11c, sedimentos fluviales SPACE ni de NeuroLab. NO autoriza pickle de datos no confiables ni prueba compatibilidad cross-version.

## Corrección de alineación de etapa 0
La secuencia H7–H14 se extendió hacia pruebas que, en la hoja de ruta rectora `BASES_Y_HOJA_DE_RUTA.md`, corresponden **conceptualmente a etapas 5 y 6**. Son pruebas exploratorias de encaje, **no ejecución ni cierre** de las etapas 5/6 ni de arquitectura de producción. Se conserva toda su evidencia, pero **se congela su expansión** hasta evaluar pendientes preexistentes de etapa 0:
1. Segundo motor de materia **The Powder Toy** (comparar con Sandspiel), licencia GPL-3 y grado real de API headless.
2. **Ecosystem Explorer** como benchmark funcional de caja negra del mundo generado/evolutivo; no asumir código abierto ni permisos de copia.
3. Otras alternativas de la revisión de 42 proyectos con ventaja plausible sobre caso de uso, no más pruebas aisladas por inercia.
4. Concluir una **decisión provisional de representación** con argumentos y gates, sin sustituir objetivos confirmados.

Este registro constituye la corrección de rumbo exigida por el procedimiento rector; no se asume que aprobar 14 hipótesis sea equivalente a haber elegido un núcleo apropiado para la organización emergente.
