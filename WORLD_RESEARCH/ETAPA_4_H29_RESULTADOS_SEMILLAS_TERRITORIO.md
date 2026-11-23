# Etapa4 — H29. Generación procedimental WorldEngine y estado Landlab reproducibles

**Fecha:** 2026-11-22. **Dictamen H29 APROBADA** bajo todos los gates establecidos y enmendados **antes** de la primera ejecución; no cierre automático de Etapa4 ni calibración de geología. [Protocolo](ETAPA_4_H29_PROTOCOLO_SEMILLAS_TERRITORIO.md), [ADR-0015](DECISIONES/ADR-0015_SELECCION_GENERADOR_E4.md), [código generador](experiments/probe_e4_h29_worldengine_seeds.py), [código propietario+solver](experiments/probe_e4_h29_generated_owner_landlab.py). [CI 45086430133 — SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45086430133), commit `1ab31cd7b7cf749539fc11615369b8df6a9fe627`.

## Generador y fuente

`Mindwerks/worldengine` MIT revisión fija **`3b9113ecfad884cab4b32081d138a15e6262ada8`**, con PyPlatec1.4.3 y NumPy2.4.6 en Python3.11; `world_gen(32,16,generation_seed)` con reset explícito global `np.random.seed(1234)` antes de cada escena. Seeds **7321 y8128**; replay7321 bit a bit. Alturas nativas en unidades **arbitrarias, NO metros**.

- Seed7321: raw min0,3375582, max6,2902251, std0,97308; SHA `495e97c24477e68e0cffcab8f485481630d4425d31a01442c7ad1cbb0daa170d`.
- Seed8128: raw min0,34, max5,9050377, std0,92955; SHA `d03e423f93b3c26ac097fba54e303c6322131f0b7fec0afb21d15e4c52e40781`.
- 418 de512 celdas difirieron por >1e−8 entre seeds; mismo seed produjo matriz exactamente igual; productor exportó NPZ **6611bytes** sin redondeo de alturas.

## Conversión espacial, propietario y movilidad

Consumidor Python3.13.18, Landlab2.11.0, NumPy2.5.5, xarray2026.9.0: al mapear raw→**0–50m NOMINALES** por reescalado lineal (no geológicamente medido), colocar las 16×32 muestras originales WorldEngine **en los nodos core de Landlab(18×34)**, correspondencia de centro de celda con `offset_x/y=−50m` y espaciado horizontal100m; halo perímetral extrapolado sin masa. Esto corrige la incongruencia del importador temprano WorldEngine→Landlab sin requerir nueva interpolación ni tratar el halo como materia.

Suelo A por celda material core0,15m de espesor nominal, densidad1200kg/m³, masa inicial global **921.600.000kg**; único owner `soil_mass_kg(y,x)` y `bedrock_elevation_m(y,x)` como geometría inerte, plus core mask y ledger externo. `topographic__elevation` es derivada, no segundo stock. Un único outlet por terreno derivado de la altura mínima del borde; en ambos resultó casualmente `node0` (regla predefinida, no hardcode de id0).

**Dos escenas activas:** `PriorityFloodFlowRouter+SpaceLargeScaleEroder` originales, `K_sed=.10`, `K_br=0`, 6 pasos `dt=.2`, saldo global `suelo almacenado+exportación acumulada=masa inicial`:
- **Seed7321:** suelo final **907.962.726,302kg**, exportación nativa **13.637.273,698kg**,506 nodos core cambiaron masa,204 ganaron material; modificación máxima de topografía nominal0,10229m. Error de balance por paso máximo **1,1921×10⁻⁷kg**.
- **Seed8128:** suelo final **907.942.044,000kg**, exportación **13.657.955,99996kg**,510 nodos modificados,213 ganaron masa; modificación máxima de terreno0,09752m. Error de balance máximo **1,1921×10⁻⁷kg**.
- **Control K_sed=0 seed7321:** masa y relieve exactamente iniciales, salida0. Replay activo seed7321 con misma masa, exportación y SHA bit a bit.
- **Integridad:** ocho corrupciones rechazadas sin alterar propietario: fuente +1kg, negativo, borde con masa, unidad kg→g, seed, sourceSHA, extra stock altura, saldo salida negativo. NetCDF **11.884bytes** recuperó campos, geometría, unidades/metadata y hash final `4e20156677ea25d67cfee3e25a392b8adaee55acf7fa33ced82b01bd8dcaf094`. El umbral de balance se fijó **antes** de CI a0,09216kg en vez de tolerancia amplia9,216kg para que pudiera rechazar coherentemente +1kg. No hubo compensación inventada de saldos.

## Interpretación honesta y gate restante

**Demostrado:** productor procedural existente, dos semillas distintas, replay y conversión geométrica explícita; el estado inicial generado admite el proveedor nativo de transporte fluvial de E2 con masa trazable, un control negativo y persistencia. No se programó física propia.

**NO demostrado:** alturas/pendientes físicamente calibradas ni que WorldEngine produzca geografía terrestre real, contacto/gravedad de Bullet sobre geometría derivada de esos mismos terrenos, cavidades3D, organismo, clima, acoplamiento. Se propone H30, una verificación local de que una **superficie triangular derivada del terreno** soporta cuerpo rígido bajo gravedad Bullet con fuente y coordenadas auditadas; no crear «mundo» integral para solo probar compatibilidad del proveedor. E4 continúa ABIERTA hasta esa verificación y auditoría de todos sus requisitos.
