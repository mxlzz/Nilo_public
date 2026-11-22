# Marco de gobierno y auditoría — Mundo autónomo

Fecha de adopción: 2026-11-21
Estado: obligatorio para la investigación de mundo. Excluye NeuroLab, cerebro, Norns, genética neuronal y LLM.
Rama de trabajo provisional: `research/world-foundations-2026-11`; NO integrar en `main` de Nilo sin una decisión posterior explícita.

## Jerarquía de documentos

1. **Objetivo y restricciones confirmadas:** `BASES_Y_HOJA_DE_RUTA.md`, apartado 2; no se cambian unilateralmente.
2. **Plan de investigación versionado:** `BASES_Y_HOJA_DE_RUTA.md`, etapas 0–8; modificable solo con justificación, análisis de impacto y registro de decisión.
3. **Evaluación de alternativas / decisiones:** `DECISIONES/ADR-0001_REUTILIZACION.md` y siguientes; cada opción debe tener evidencia, incertidumbre y motivación.
4. **Experimentos:** archivos `ENSAYO_NN_*.md`, código y pruebas; nunca sustituir hipótesis por una demostración visual.
5. **Evidencia verificable:** enlace al commit, CI, resultados, semillas, configuración, versión y controles negativos.

## Auditoría retrospectiva 2026-11-21

**Incumplimiento detectado:** la etapa 0 (análisis de alternativas) no había concluido cuando se creó `experiments/matter_v0.py`. Es un **spike exploratorio** no autorizado como base definitiva.

**Segundo desvío:** el plan describía densidad como derivada, mientras que el código la almacena como parámetro y deriva el volumen ocupado. Esta diferencia no es necesariamente errónea, pero demuestra que la especificación física aún no está aprobada.

**Tercer desvío:** el documento inicial decía «sin implementación» pese a existir posteriormente un prototipo y pruebas. Este documento prevalece en estados hasta que se actualice la hoja de ruta.

**Resultado real:** se verificó ejecución correcta de 8 pruebas de invariantes en GitHub Actions: https://github.com/mxlzz/Nilo_public/actions/runs/44942005067. No hay prueba de gravedad, dinámica, emergencia, rendimiento o viabilidad del modelo físico. No dar por ejecutadas pruebas fuera de evidencias conservadas.

**Estado del ensayo 01:** válido solo como prueba de contrato mínimo de datos; **no validado** como motor del mundo. Congelar expansión de `matter_v0.py` hasta cerrar decisión de reutilización.

## Gate obligatorio antes de cada cambio

Se prepara una ficha breve que responda, por escrito, a las ocho preguntas:

1. **¿Qué objetivo confirmado justifica esta etapa?** ID de requisito y etapa del plan.
2. **¿Qué hipótesis falsable se probará?** También resultado alternativo plausible.
3. **¿Existe algo reutilizable?** Comprobar soluciones preexistentes relevantes antes de desarrollar, más importante en un componente nuevo.
4. **¿Por qué esta técnica?** Registro de decisión con alternativas descartadas y condicionantes (licencia, interfaz, costo, complejidad, madurez).
5. **¿Cuál es el mínimo alcance?** Sin agregar capacidades «por si acaso».
6. **¿Cuáles son las pruebas definidas ANTES de implementar?** Unitarias, integración, control negativo/ablación, reproducibilidad, indicadores de causalidad, rendimiento cuando corresponda.
7. **¿Qué evidencia de ejecución se conservará?** Commit, CI, semilla, parámetros, métrica, resultados y límites de interpretación.
8. **¿Cuál es la conclusión de auditoría?** Aceptar / corregir / descartar / investigar más; cotejo con objetivos y cambios de plan si hacen falta.

No se inicia una etapa siguiente si la actual carece de un dictamen de puerta de salida. Un resultado positivo de CI es **necesario pero insuficiente**.

## Regla de evolución del plan

Si aparece mejor herramienta, evidencia que invalida el enfoque o nueva restricción:
- documentar nuevo hecho, su origen y qué hipótesis afectó;
- proponer modificación acotada y el costo de oportunidad de mantener el plan;
- conservar versión anterior en Git;
- validar invariantes de etapas anteriores cuando cambian contratos;
- no presentar el desvío como si hubiese sido planificado desde el inicio.

Las hipótesis técnicas reversibles pueden cambiar por evidencia. Los objetivos confirmados por el usuario no cambian por iniciativa del implementador.

## Regla de reutilización

Por defecto preferir **usar, adaptar o combinar soluciones existentes** antes que reconstruir su funcionalidad. Desarrollo propio solo si se acredita mediante pruebas una brecha material, incompatibilidad de licencia, extensión desproporcionada o riesgo técnico mayor. Una biblioteca de referencia puede inspirar criterios sin copiar código.

El trabajo específico y pequeño (por ejemplo interfaces o adaptadores) puede requerir código propio incluso si se reutiliza un motor. Eso no justifica crear uno desde cero.

## Estado de avance al cierre de auditoría

- Etapa 0: **abierta, parcialmente investigada; decisión de motor pendiente de prueba comparativa ejecutada**.
- Etapa 1: **spike experimental en cuarentena; no aprobado como base del proyecto**.
- Etapas 2–8: **no iniciadas**.
- Bloqueo actual: prueba de encaje técnico y licencias de al menos dos candidatas sobre los mismos casos de uso.
- Próximo trabajo autorizado por el plan: documentación, inspección de alternativas, definición de benchmarks y pruebas limitadas de adaptación; **no** desarrollar nuevas leyes físicas en el prototipo existente.

## Addendum — estado verificable al 22-11-2026 (prevalece sobre el corte histórico anterior)

Las líneas anteriores "etapa 0 abierta / etapa 1 spike en cuarentena" documentan el diagnóstico del **21 de noviembre**. **NO** representan el estado vigente tras las pruebas posteriores. Mantenerlas por trazabilidad y utilizar la [hoja de ruta actualizada](BASES_Y_HOJA_DE_RUTA.md) como puerta activa.

- **Etapa 0 / evaluación de alternativas:** cerrada **solo en su gate de reutilización** mediante [ADR-0003](DECISIONES/ADR-0003_CIERRE_ETAPA_0_BASES_MODULARES.md); seis familias de soluciones ensayadas, errores instrumentales preservados. No existe motor universal seleccionado.
- **Etapa 1 / estado material:** sigue **ABIERTA**. H1–H3 validaron material/capas/alias/contrato; [H4](https://github.com/mxlzz/Nilo_public/actions/runs/45034754946) demostró colisión de alturas con cavidades y puentes estáticos, [H5](https://github.com/mxlzz/Nilo_public/actions/runs/45035061531) validó propietario material exclusivo entre superficie/volumen y caché derivada, y [H6](https://github.com/mxlzz/Nilo_public/actions/runs/45035363232) migró 24kg de frontera a vóxeles y volvió sin pérdida, rechazando simplificar columnas con huecos. Los documentos completos se encuentran junto a los protocolos.
- **Decisión espacial reversible:** [ADR-0005](DECISIONES/ADR-0005_REPRESENTACION_ESPACIAL_HIBRIDA.md): considerar superficie ambiental con regiones volumétricas locales **si** el fenómeno lo exige; no inventar un motor propio ni voxelizar todo el mapa. `ADR-0004` sigue como principio de propiedad de estado; `ADR-0005` ajusta su representación experimental a propietarios exclusivos por región.
- **No probado:** estabilidad física, contacto 3D, generación espontánea de cavidades, incorporación de leyes reales al estado, energía y transformaciones de material, escala y concurrencia. Pruebas antiguas H7–H14 de agua/ecología no cierran etapas 5/6.
- **Próxima puerta:** definir y validar fenómenos materiales e invariantes no cubiertos por H1–H6, elegir componentes de física **existentes** antes de desarrollar nuevos, y evitar seguir programando adaptadores sin hipótesis causal. No pasar a etapas 2–8 sin un gate propio.
- **Repositorio:** rama `research/world-foundations-2026-11` de `Nilo_public`, ubicación provisional, aislada de `main` y de NeuroLab. El agente siguiente debe tomar las ADR recientes y resultados CI como información vigente en lugar de las etiquetas históricas.

## Addendum de auditoría H7–H8 — 22-11-2026 (prevalece sobre H1–H6 para estado reciente)

- **Motivo de avanzar:** H1–H6 habían probado contenedores, exclusión, geometría y contratos. Se precisaba observar **una consecuencia física real** del espacio volumétrico. No se escribió un nuevo integrador: se seleccionó Bullet/PyBullet zlib tras comparación con TPT/Sandspiel y otras alternativas. Protocolo [H7](ETAPA_1_H7_PROTOCOLO_RIGID_CONTACT_BULLET.md) antes de código, CI [H7](https://github.com/mxlzz/Nilo_public/actions/runs/45036231904) SUCCESS.
- **H7 física local comprobada:** contacto, caída, no-gravedad, caída libre, replay e inventario canónico con transferencia por parámetros a solver, pero sin deformación ni química.
- **H8 hipótesis justificada por H4/H5:** misma superficie visible en sólido+cavidad y distinta ocupación interior. Protocolo [H8](ETAPA_1_H8_PROTOCOLO_CAVIDAD_CONTACTO.md) antes de arnés; fuente Landlab2.11 Python3.13 generó NetCDF canónico, Bullet3.2.7 Python3.11 consumió con hash, conservó la cuenta y calculó apoyo en piso de cavidad. [CI final](https://github.com/mxlzz/Nilo_public/actions/runs/45037191905) SUCCESS, informe [H8](ETAPA_1_H8_RESULTADOS_CAVIDAD_CONTACTO.md).
- **Tres fallos y tratamiento:** falló primera vez por incompatibilidad Landlab/`requireit` con Python3.11; se documentó la separación por datos en lugar de forzar dependencias. Segundo control de «0 contactos con g0» era incorrecto por paredes laterales; tercera corrida de diagnóstico documentó normales horizontales/fuerzas nulas y apoyo del piso con g, y solo después se cambiaron criterios de **no apoyo ni fuerza significativa** con g0. La cuarta corrida aprobó. Toda la secuencia se conserva en CI y protocolo, sin cambiar físicas ni posiciones. Esto NO es prueba de cobertura exhaustiva del solver.
- **Decisión reversible:** [ADR-0006](DECISIONES/ADR-0006_PROVEEDOR_CONTACTO_BULLET.md): Bullet proveedor de contacto rígido 3D **solo local**, no sistema físico del mundo. Un mapa de alturas sigue sin admitir la configuración ensayada. La contabilidad de materia permaneció en xarray y los cuerpos Bullet son caches de mecánica, no stocks nuevos. No asumir colisiones realistas de roca deformable, cavidad estable por resistencia, transporte real, temperatura o formación espontánea.
- **Cambio de estado**: la línea anterior «no probado contacto 3D» se refería al corte H1–H6 y ahora es histórica; contacto rígido 3D sí probado en H7/H8. Etapa1 continúa ABIERTA por fenómenos de transformación/energía y sustrato no rígido. Etapas2–8 no se dan por completadas, y H7/H8 no autorizan construir sistema de bloques para todos los voxeles.
- **Siguiente gate prioritario**: estudiar antes de codificar la **redistribución espontánea de materia** mediante un solver existente: conservación, respuesta a gravedad/gradiente, heterogeneidad y trazabilidad de cantidad por material; comparar TPT/Sandspiel (2D) y herramientas DEM/MPM si las dimensiones 3D lo justifican. Evitar más ensayos de formato por inercia.


## Auditoría de alineación H9 — 2026-11-22

**Objetivo:** materia del mundo gobernada por leyes compartidas, persistente y auditable, sin inventar física nueva; etapa 1 del plan y vínculo experimental con etapa 2 futura. **Antecedente reutilizado:** `SpaceLargeScaleEroder` de Landlab, validado antes en E0.4-H7b. **Nuevo hueco cubierto:** el resultado del solver debía transformarse en único inventario xarray mediante una candidatura validada y un ledger basado en salida física observada, en vez de limitarse a editar un campo numérico temporal.

- El [protocolo H9](ETAPA_1_H9_PROTOCOLO_SEDIMENTO_OWNER.md) fue escrito en commit `364d812e` ANTES del [arnés](experiments/probe_e1_h9_sediment_owner.py) `ece75904` y workflow `82aff23d`.
- [Ejecución H9](https://github.com/mxlzz/Nilo_public/actions/runs/45048479951) **SUCCESS**; balance de salida, control sin erosión, replay, cinco rechazos y NetCDF superaron criterios originales. Datos y límites en [informe H9](ETAPA_1_H9_RESULTADOS_SEDIMENTO_OWNER.md).
- **Sin desvíos:** no se tocó `main`, NeuroLab ni se programó un solver; el campo de altura sigue siendo geometría derivada. **Limitación importante:** el intercambio probado es con una columna de sedimento 2.5D, no con owner H5 de ROI3D; H9 no prueba mezcla granular, fractura ni estabilidad estructural.
- **Decisión:** aceptar el resultado H9 y mantener etapa1 abierta. **Próximo objetivo selectivo:** contrastar qué solver existente de material granular/deformable 3D puede demostrar redistribución real con controles y propiedad material en un escenario pequeño. GeoTaichi (GPL3), Project Chrono (BSD3) y Bullet (zlib, solo cuerpos rígidos) son candidatos no equivalentes; evaluar interfaz, licencia, costo real y fenómeno antes de elegir un nuevo experimento. No imponer múltiple-motor universal por decreto.

## Auditoría de alineación H10 — 2026-11-22

**Pregunta causal adicional a H9:** la redistribución de partículas en **volumen 3D** por contactos *entre ellas*, usando proveedor existente y manteniendo propiedad material única. Un solo cubo H7/H8 no lo demostraba, pero no se presupuso que 27 esferas fueran un material continuo.

- [Protocolo H10](ETAPA_1_H10_PROTOCOLO_GRANOS_RIGIDOS.md) commit `7913541b`, previo al arnés commit `0b94667d` y workflow `a85f101e`. [Primer CI H10](https://github.com/mxlzz/Nilo_public/actions/runs/45049082476) falló **antes de física**, por una coordenada xarray read-only; el protocolo recogió incidencia en commit `5cb2ce50`. Corrección de arnés `240808f3` sin alterar umbrales; [segunda CI H10](https://github.com/mxlzz/Nilo_public/actions/runs/45049166835) **SUCCESS**.
- Resultado: caída, choques múltiples con fuerzas positivas, dispersión lateral, replay y controles con/sin gravedad/suelo; estado material 6,75kg sin alteraciones y cinco corrupciones rechazadas. **Sin formación de pila estable** ni transformación de volúmenes; [informe H10](ETAPA_1_H10_RESULTADOS_GRANOS_RIGIDOS.md).
- **Decisión:** mantener Bullet como proveedor **solo de contacto rígido**. No elevar una dispersión de esferas a modelo geomorfológico, materia deformable, emergencia estructural ni motor general. H10 no cierra etapa1 ni inicia etapas 2–8; futuro solver granular/plástico requiere fenómeno, alternativas, licencia, costo e interfaz material demostrados antes de integrarlo. No se modificaron `main` ni NeuroLab.

## Auditoría H11/H12 — 2026-11-22

- **H11:** protocolo [H11](ETAPA_1_H11_PROTOCOLO_MPM_3D.md) commit `7e222c65`, previo al código `7d868418` y workflow `a8f7b3d2`; [CI](https://github.com/mxlzz/Nilo_public/actions/runs/45055263832) SUCCESS. 108 puntos y2,7kg con MPM/Sand upstream no escrito aquí. Gravedad y fricción interna producen efecto físico diferencial; sin gravedad inmóvil, replay/materia y checkpoint de inventario exactos. **No demuestra estabilidad ni exactitud constitutiva 3D**. Fuente externa pinneada PINNeAPPle `c8a6e3dce5daedd10903cc68f7f3a062c42b8bc4`.
- **H12:** protocolo [H12](ETAPA_1_H12_PROTOCOLO_REPOSO_MPM.md) commit `f7388580`, anterior al código `438938ff` y workflow `da93f4cc`; [CI](https://github.com/mxlzz/Nilo_public/actions/runs/45055570920) **FAIL por criterio físico preregistrado**. Se midió ralentización/forma casi estable en arena con fricción30° y sin paredes laterales, pero 61,11% de puntos exactamente floor clamped z=1,5dx superaron el máximo50%; con fricción0° el material siguió desplazándose intensamente. Los demás controles (masas5,4kg, g0, replay, cambios geométricos medidos) pasaron. **No modificar tolerancias ni borrar CI fallida.** Detalle [informe](ETAPA_1_H12_RESULTADOS_REPOSO_MPM.md).
- **Corrección de interpretación importante:** H11/H12 generan en el solver una malla de partículas y su array de masas y **luego** crean una copia xarray canónica de inventario para auditarla. Eso demuestra que se puede verificar inventario **contra** un proveedor externo, pero NO que xarray controle la simulación como único dueño operativo con actualizaciones recíprocas. H9 probó publicación desde Landlab; esta conexión todavía no se ha demostrado para MPM. No inflar las conclusiones.
- **Próximo gate selectivo:** contraste con solver independiente antes de acoplamiento; GeoTaichi es candidato de referencia publicado pero GPL-3.0 y más difícil de ejecutar. La investigación no se reorienta a infraestructura hasta demostrar capacidad material necesaria. H11 válido y H12 limitante, etapa1 ABIERTA, no nuevo motor propio, main y NeuroLab intactos.

## Auditoría H13A/H14 y revisión gate — 2026-11-22

**H13A:** Prerregistro [H13A](ETAPA_1_H13A_PROTOCOLO_GEOTAICHI_CPU.md) y dos intentos consecutivos contra fuente GeoTaichi GPL-3.0 SHA fijado, sin modificaciones de upstream. [Primer CI](https://github.com/mxlzz/Nilo_public/actions/runs/45055983838) abortó antes de física por `open3d`; se preregistró instalación de dependencia oficial y límite a un único reintento. [Segundo CI](https://github.com/mxlzz/Nilo_public/actions/runs/45056130916) abortó por `plotly`. **Cierre correcto:** H13A NO APROBADA como prueba de motor 3D CPU, proveedor físico no evaluado; evitar persecución de dependencias. [Informe](ETAPA_1_H13A_RESULTADOS_GEOTAICHI_CPU.md).

**H14:** protocolo [H14](ETAPA_1_H14_PROTOCOLO_ENERGIA_FIPY.md) commit `66eb9765` antes de código `2c35b637` y workflow `5fa92af3`; [CI H14](https://github.com/mxlzz/Nilo_public/actions/runs/45056513417) **SUCCESS**. FiPy NIST resolvió conducción conservativa con dos inventarios únicos por celda (masa y energía xarray); controles, reproducción y NetCDF completos; error energético máximo4,66×10⁻⁹J. **No** equivale a transformación química o térmica realista. [Informe](ETAPA_1_H14_RESULTADOS_ENERGIA_FIPY.md).

**Dictamen:** [gate consolidado](AUDITORIA_GATE_ETAPA_1_POST_H14_2026-11-22.md) **NO CIERRA etapa1**, pues fenómenos probados aún no comparten un estado físico simultáneo (masa, posición, energía, transformación). Evitar un motor universal en código propio o decenas de ensayos sin causalidad integrada. No tocar main/NeuroLab.

## Cierre auditado E1/E2 y apertura E3 — 2026-11-22 (vigente; prevalece sobre registros históricos)

**E1:** [H15](ETAPA_1_H15_RESULTADOS_FASE_ENTALPIA.md) y [H16](ETAPA_1_H16_RESULTADOS_DOS_MATERIALES.md) con [CI 45058971601](https://github.com/mxlzz/Nilo_public/actions/runs/45058971601) y [CI 45059387895](https://github.com/mxlzz/Nilo_public/actions/runs/45059387895) verificaron transformación derivada por calor latente y A/B bajo un mismo inventario masa/energía/volumen, con controles y estados inválidos. [Auditoría del gate E1](AUDITORIA_CIERRE_ETAPA_1_2026-11-22.md) **aprobó provisionalmente etapa1 mínima** ([ADR-0009](DECISIONES/ADR-0009_GATE_ETAPA_1_MINIMO.md)). H15 primer CI falló en JSON de metadato NumPy de checkpoint, y H16 primer CI careció de jobs por YAML inválido; se documentaron antes de correcciones y no se alteraron los tests físicos.

**E2:** [H17](ETAPA_2_H17_RESULTADOS_GRAVEDAD_OWNER.md) [CI 45059850320](https://github.com/mxlzz/Nilo_public/actions/runs/45059850320) demostró cuerpo rígido apoyado/caída y **publicación de posición/velocidad al owner**; [H18](ETAPA_2_H18_RESULTADOS_GRADIENTE_SEDIMENTO.md) [CI 45060100229](https://github.com/mxlzz/Nilo_public/actions/runs/45060100229) demostró respuesta causal de erosión/transporte sedimentario al gradiente con conservación y control K0. [Auditoría E2](AUDITORIA_CIERRE_ETAPA_2_2026-11-22.md) **aprobó provisionalmente gate de dos leyes locales aisladas**. No simular ni afirmar que Bullet/Landlab/FiPy funcionan simultáneamente en un mismo espacio o mantienen toda la energía mecánica/termal.

**E3:** abierta desde el cierre limitado de E2. Las pruebas H10 (granos rígidos dispersos) y H12 (deformación MPM con piso clamped) **NO** cuentan como organización estructural estable. La fase siguiente requiere patrones espaciales conectados, persistencia temporal, ablación física y comparación contra condiciones iniciales/azar; se debe preregistrar protocolo y criterios, y se acepta no obtener estructuras. Mantener main y NeuroLab intactos.

**Riesgo de desvío:** cierre de E1/E2 solo valida bancos y contratos delimitados; E5 acoplamiento y E6 persistencia total siguen pendientes, además de validez dimensional y calibración. Usar hitos para reducir la complejidad, no para suponer que ya existe el mundo.

## Auditoría de experimentos E3 H19–H21 (2026-11-22)

- **H19 [CI FAIL por gate](https://github.com/mxlzz/Nilo_public/actions/runs/45060568065):** depósito Landlab 50 nodos conectado y persistente T12→T24, pero nulo por fila P95=50 reproduce componente del mismo tamaño; no hay organización distinguible de plantilla. [Resultado](ETAPA_3_H19_RESULTADOS_DEPOSITO_CONEXO.md).
- **H20A [CI SUCCESS solo screening](https://github.com/mxlzz/Nilo_public/actions/runs/45060886245):** pyDeltaRCM v2.3.0 upstream MIT ejecutó modelo delta30×40 durante12 pasos; seeds reproducibles, 423 celdas cambiadas; **upstream reconoce falta de conservación estricta del sedimento/agua**, solo diagnóstico externo sin owner. [Resultado](ETAPA_3_H20A_RESULTADOS_PYDELTARCM.md), [ADR-0011](DECISIONES/ADR-0011_H20_SCREENING_PYDELTARCM.md).
- **H21 [CI FAIL por gates](https://github.com/mxlzz/Nilo_public/actions/runs/45061348648):** FiPy Cahn–Hilliard con masa A/B conservada (desvío por especie~1e-10kg), g sin movilidad inmóvil y repetición exacta, pero mezcla~0,5 se **homogeneizó** (varianza0,001599→0,0000554), sin diferencia estructural frente a nulo por filas >0,08. Se observó además subcheck aritmético defectuoso que pidió `sum==400` exacto y acusó redondeo~5,7e-14kg como falso FAIL; el umbral físico de masa1e-4kg sí se cumplió. No reemplazar falsos negativos instrumentales por resultado físico ni promover H21. [Resultado](ETAPA_3_H21_RESULTADOS_CAHN_HILLIARD.md), [ADR-0012](DECISIONES/ADR-0012_CAHN_HILLIARD_E3.md).
- **H22 preregistrada, aún sin ejecución aprobada:** comparar penalización de gradientes `epsilon0,5` vs1 del mismo PDE por relación dispersiva de inestabilidad, **sin alterar H21 ni ajustar sus tolerancias**. [Protocolo](ETAPA_3_H22_PROTOCOLO_ESCALA_INTERFAZ.md). No declarar H22 probada por haber escrito el protocolo.

**Gate E3 SIGUE ABIERTO.** Los cierres E1/E2 eran locales/reversibles y no se ven anulados por los fallos de patrones, pero no justifican un mundo físico integrado. Evitar crear más motores o patrones ficticios por objetivos de CI. Las decisiones se mantienen en rama experimental aislada.
