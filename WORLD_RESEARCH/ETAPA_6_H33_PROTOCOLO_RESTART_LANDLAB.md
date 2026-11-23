# Etapa6 — H33. Prerregistro: detener y reanudar Landlab desde estado material autoritativo

**Fecha 2026-11-22. Protocolo registrado antes del código y de CI.** Se deriva del [plan rector E6](BASES_Y_HOJA_DE_RUTA.md) (continuación causal y checkpoint a mitad, reproducción batch vs continuo, avance sin observador, no reparación silenciosa) y del [cierre E5 acotado](AUDITORIA_CIERRE_ETAPA_5_2026-11-22.md). No se reclama E6 completa por un primer ensayo.

## Evaluación de soluciones existentes

El proveedor **Landlab2.11** ya permite recrear `RasterModelGrid`, `PriorityFloodFlowRouter` y `SpaceLargeScaleEroder` a partir de campos del **owner xarray**; H31 usa `xarray.Dataset.to_netcdf` para transferir suelo y reservorio al proceso de Bullet, pero **nunca probó reanudar a mitad de una secuencia de erosión**. Reusar esos contratos y NetCDF (licencias y dependencias ya auditadas), sin nueva física ni motor ni sistema externo de colas. La alternativa `pybullet.saveState` tiene semántica de motor local y no sustituye, por sí sola, un checkpoint material portable a otra sesión; su examen quedará para experimento de dinámica rígida separado, si H33 justifica avanzar.

## Hipótesis y alternativa

**H33:** para la cuenca WorldEngine H29/H31, el estado canónico de materia, relieve, cuerpos en reservorio, sumidero y progreso `landlab_step/t` **contiene toda la información causal suficiente** para interrumpir Landlab después de3 de los6 pasos, guardar NetCDF y reconstruir los componentes nativos en **un proceso nuevo** para ejecutar otros3, obteniendo el **mismo estado final** que6 pasos sin interrupción. **Hipótesis alternativa:** un estado oculto del router/erosionador o una inicialización de superficie/bordes impide continuar idénticamente aunque presupuesto global cierre. En ese caso H33 NO APROBADA; no recalibrar ni compensar el estado sin demostrar la causa.

## Diseño fijo

- Source exacta WorldEngine MIT revision `3b9113ecfad884cab4b32081d138a15e6262ada8`, seeds7321 y8128, archivos NPZ con hashes [H29/H31](ETAPA_5_H31_RESULTADOS_SUELO_CONTACTO.md). Python3.13, Landlab2.11, xarray y scipy; igual grilla18×34 dx100m nominal, suelo inicial921.600.000kg, cuerpo inerte2kg en reservorio y salida de sedimentos.
- Escenarios preregistrados: `seed7321 K_sed=.1`; `seed8128 K_sed=.1`; control `seed7321 K_sed=0`. En todos: **6 pasos `dt=.2`**, split después de3 pasos, sin modificar una sola ley física ni input. `TIMESTEPS=6` y reloj de Landlab separados del reloj Bullet, que permanece0.
- **Tres jobs/entornos separados:** (1) generador raw WorldEngine original 3.11 (igual H29); (2) productor Landlab Python3.13 construye los tres estados iniciales, ejecuta baseline6 **sin cortar** y ensayos split3, guarda **los tres owners de t3 y los tres baseline t6** por NetCDF y manifiesto con SHA; (3) consumidor Landlab Python3.13 corre en un nuevo proceso/runner, lee checkpoint t3 y la misma fuente raw con hashes, **reconstruye** router/Space del estado t3, ejecuta **solo pasos4,5,6** y compara estado final t6 con baseline sin reinicializar materia ni volver a ejecutar pasos1–3. Ningún canal oculto de estado entre job productor y consumidor excepto artefactos declarados.
- **Algoritmo de step idéntico a H31:** copiar material actual al campo `soil__depth`, topografía derivada al grid transitorio, enrutador nativo y `solver.run_one_step(dt)`; usar `suspended+bedload` nativos para actualizar `exported_soil_kg` y el saldo único `soil+export+body` mediante candidato validado. No escribir ecuaciones de erosión.

## Gates previos

1. **Checkpoint íntegro a t3:** mismo owner de H31 para cada seed/control, `landlab_step=3`, `landlab_t_bench=.6`, cuerpo `status=reservoir` con masa2kg, `bullet_t_s=0`, `soil_mass` no negativa/solo core, export≥0, mismas fuentes SHA/unidades; corrupción de 8 estados ilegales se rechaza sin mutar el verdadero owner. Hash NetCDF t3 idéntico al owner t3 antes de guardar.
2. **Balance en cada paso** de continuo y reanudado: `soil almacenado + exported soil + 2kg =921.600.002kg` con residual máximo0,09216kg, sin reconciliar diferencias de masa a posteriori.
3. **Equivalencia estricta:** para los tres escenarios, final t6 del proceso consumidor reanudado coincide **bit a bit** con el baseline continuo en arreglos `soil_mass_kg`, atributos/contador/t y `hash_owner` y exportación exacta (el protocolo **no** acepta solo tolerancia numérica para esa equivalencia). Si no pasa, H33 NO APROBADA.
4. **Dinámica/control:** K=.1 altera al menos100 nodos core en cada seed y exporta suelo; K=0 se mantiene idéntico al suelo inicial y exportación0 en ambos procesos. La comparación no se aprueba por conservar una escena inmóvil únicamente.
5. **Reproducibilidad:** segundo baseline sin corte para seed7321 produce mismo SHA y exportación exactos; cambio de seed altera la distribución final de suelo; todos los outputs y etapas en CI auditable.
6. **Antifraude:** ningún job usa estados internos ocultos del proceso anterior, no reejecuta pasos previos al reinicio, no deja pasos extra, no realiza clipping/rebalanceo, no reduce tolerancias, no introduce información temporal/energía omitida por resultados de conveniencia. `WORLD_EVAL_JSON` informa métricas antes del exit1.

**Salida:** H33 aprobada solo si se cumplen los6 gates. Aun si pasa, no hay prueba de reanudar Bullet, fuente granular H26 en medio de descarga, reloj conjunto, continuidad al cambiar plataforma/versión ni vida ambiental autónoma de largo plazo; **E6 permanecerá abierta** hasta verificar otras instancias de dinámica y estado temporal. Main y NeuroLab intactos.
