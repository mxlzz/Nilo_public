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
