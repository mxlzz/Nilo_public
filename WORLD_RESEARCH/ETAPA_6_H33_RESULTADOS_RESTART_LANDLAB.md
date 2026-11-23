# Etapa6 — H33. Reanudar Landlab en otro proceso reproduce EXACTAMENTE los seis pasos continuos

**2026-11-22 — H33 APROBADA según todos los gates preregistrados.** [Protocolo previo](ETAPA_6_H33_PROTOCOLO_RESTART_LANDLAB.md), [script](experiments/probe_e6_h33_resume_landlab.py), [CI final 45092764108: SUCCESS en los tres jobs](https://github.com/mxlzz/Nilo_public/actions/runs/45092764108). Fuente raw WorldEngine upstream revision `3b9113ecfad884cab4b32081d138a15e6262ada8` y datos H29/H31 invariables. Landlab2.11, Python3.13.18, NumPy2.5.5, xarray2026.9.0.

## Evidencia de reanudación real

El productor ejecutó para cada uno de los tres escenarios:
1. **baseline** Landlab continuo de pasos1–6, con `SpaceLargeScaleEroder` original, `PriorityFloodFlowRouter`, dt0,2;
2. **prefijo independiente** pasos1–3, guardando NetCDF del owner conjunto `soil_mass_kg+bedrock+body_mass_kg` en status`reservoir`, `landlab_step=3`, `landlab_t_bench=0.6`, `bullet_t_s=0`, saldo de material exportado y fuente SHA;
3. **consumidor de GitHub Actions en runner/proceso nuevo** cargó exactamente raw WorldEngine y el checkpoint del paso3, reconstruyó componentes Landlab *solo desde el owner*, y ejecutó **los pasos4,5,6** sin repetir1–3 ni recurrir a memoria del proceso productor.

| Escenario | Exportación 6 pasos (kg) | SHA continuo = reanudado | Masa por celda bit a bit |
|---|---:|---|---|
| seed7321 K=.1 | 13.637.273,698001327 | `33f352be6a90...` | Sí |
| seed8128 K=.1 | 13.657.955,999957621 | `b97a8af673b5...` | Sí |
| seed7321 K=0 | 0 | `28d3aacfa5a3...` | Sí |

En **los tres casos** salida exportada exacta, hash del owner idéntico, topología/datos del terreno y cuerpo reservoir intactos, origen/outlet0 sin cambios. El control K=0 permaneció inerte; las dos escenas de K=.1 cambiaron material efectivamente. Repetición del baseline de la primera seed idéntica bit a bit. En cada paso `soil + exported + body =921.600.002kg`, máximo error observado al reanudar **1,1920928955078125×10⁻⁷kg**, contra tolerancia0,09216kg. Nueve candidatos corruptos fueron rechazados, sin alterar owner verdadero. Checkpoints originales t3 y t6 recuperados con SHA intactos.

**Evidencia específica:** `resume_executed_first_step=4`, `resume_executed_last_step=6` en los3 escenarios, sin retroceder tiempo. `failed_preregistered_gates=[]`, jobs source, producer y consumer SUCCESS.

## Incidencias de informe, no fallos físicos

- [CI 45092212509](https://github.com/mxlzz/Nilo_public/actions/runs/45092212509) llegó al informe del consumidor pero `json.dumps` rechazó `numpy.bool_`. [Incidencia H33.0](ETAPA_6_H33_INCIDENCIA_0_JSON_NUMPY_BOOL.md) registrada antes de corrección puntual.
- [CI 45092434351](https://github.com/mxlzz/Nilo_public/actions/runs/45092434351) repitió el fallo en otro booleano de informe; [incidencia H33.1](ETAPA_6_H33_INCIDENCIA_1_JSON_NUMPY_BOOL.md) registrada antes de normalizar `np.generic.item()` **solo al emitir JSON**, sin alterar la física, tipos de estado/masas ni gates.
- Tercer CI citado aprobó después de serialización general robusta. No se inventaron resultados de dos ejecuciones cuyo JSON no pudo emitirse.

## Interpretación

**Demostrado:** un subsistema que erosiona material con un cuerpo conservado en reservorio reanuda tras cambio de proceso exclusivamente desde su owner xarray+fuente raw, con trayectoria bit a bit igual en esa versión de Landlab. Se pudo detener, guardar, reabrir y continuar causalmente sin observador.

**No demostrado:** continuación temporal de Bullet dentro del mismo flujo soil→contacto, retroacción/contactos de cuerpo móvil durante Landlab, estados ocultos de un proceso más complejo, cambio de versión de solver, reanudación del feed granular H26, física energética o un reloj unificado. [H34](ETAPA_6_H34_RESULTADOS_CHECKPOINT_BULLET.md) prueba por separado `saveBullet/restoreState` en una escena de dos cubos y contacto; no inferir automáticamente que su combinación ya se reanuda. **E6 debe auditarse contra su alcance o extenderse si se exige continuidad de fuente granular.**
