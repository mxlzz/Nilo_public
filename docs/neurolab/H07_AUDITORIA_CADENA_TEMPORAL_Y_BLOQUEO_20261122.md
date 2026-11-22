# NeuroLab — H-07: auditoría de cadena temporal histórica tras cierre de G05-NX01

**Fecha:** 2026-11-22. **Clase:** reconciliación documental de evidencia ya preservada; **no nueva lectura de bytes del EXE**, no nuevas pruebas científicas, no cambio de puertas originales. **Estado:** H-07 documental COMPLETADA, fidelidad dinámica del cerebro C1 NO DEMOSTRADA. Derivada de [STOP de G05-NX01](G05_NX01_RESULTADO_Y_STOP_20261122.md), [objetivo original #102](https://github.com/mxlzz/Nilo_public/issues/102) y [puertas reconciliadas](E09_00R_RECONCILIACION_GATES_20261122.md).

## 1. Evidencias primarias existentes — no repetir análisis

- **H1** [orden de cerebro y química](E09_H_01_RESULTADO_ORDEN_CEREBRO_QUIMICA.md): análisis previo sobre EXE auténtico con huella SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`; ruta regular `brain→chemistry→behavior`, ruta excepcional `chemistry→brain`; dentro de química `emitters→receptors→reactions→decay`.
- **H2** [reacciones](E09_H_02_RESULTADO_REACCIONES_QUIMICAS.md): examen previo de GEN y EXE: recompensa49 y castigo50 participan en reacciones que producen Reinforcement51 y Echo54/55; **dos reacciones pueden encadenarse en un mismo paso químico** en orden de genes, pero eso no adelanta la fase de receptores ya terminada.
- **H3/H4** [receptores](E09_H_03_RESULTADO_RECEPTORES.md) y [enlace de loci](E09_H_04_RESULTADO_ENLACE_LOCI.md): los receptores cerebrales transfieren muestras químicas a bytes lóbulo CHEM0..3; SVRules leen esos bytes. Para Decision6, Reward49 se enlaza al CHEM0 y Punishment50 al CHEM1; para Concept8, Reinforcement51 a CHEM0. Una concentración no equivale necesariamente al byte, que pasa por escala `>>8`, threshold y nominal.
- **H5** [emisores](E09_H_05_RESULTADO_EMISORES.md): sustancias producidas por emisiones antes de receptor **pueden** muestrearse en esa invocación química; productos de reacciones posteriores **no** pueden hacerlo. Las fuentes de emisión también dependen de loci neuronales que pueden borrarse al emitir.
- **H6A/H6B** [flujo condicional](E09_H_06A_RESULTADO_FLUJO_SCHEDULER.md), [cadencia nominal](E09_H_06B_RESULTADO_CADENCIA.md): `SetTimer` solicita **90 ms** y `WM_TIMER` llama al loop mundial; el scheduler intercala fases 0..4 y las rutas cerebral/química están condicionadas por flags de criatura y pausa. **No son 90 ms por tick cerebral ni 450 ms por Norn**. Existe segunda ruta `chem→brain` que altera cualquier regla de latencia universal. C1 no fue ejecutado dinámicamente en esta línea.

**Jerarquía de certeza:** rutas y bytes verificados en sus inspecciones anteriores son **evidencia estática P2** para la edición hasheada. La propagación temporal inferida de ese orden es una **inferencia condicional**. Frecuencia efectiva, química cerebral en una criatura real y causalidad de conducta **siguen ABIERTAS**.

## 2. Secuencia causal histórica — cronología condicional en pasos lógicos

**Ruta normal, dos invocaciones sucesivas de química y cerebro cuando los flags permiten ambos.** Denotar `B_k` la rutina cerebral de la criatura, `E_k` emisores, `R_k` receptores, `X_k` reacciones, `D_k` decaimiento. Orden local verificado:

```text
pasada k   : B_k → E_k → R_k → X_k → D_k → conducta
pasada k+1 : B_(k+1) → E_(k+1) → R_(k+1) → X_(k+1) → D_(k+1)
pasada k+2 : B_(k+2) → ...
```

- Si un emisor produce un químico antes de `R_k`, y **si** no lo consume/elimina antes su aplicación y se cumplen rate/threshold, ese químico **puede** afectar un locus en `R_k`; la siguiente rutina cerebral normal `B_(k+1)` puede usar el locus. No afecta retroactivamente a `B_k`.
- Si una reacción `X_k` crea una sustancia después de `R_k`, `R_k` **no puede verla**. Siempre que persista en el pool hasta `R_(k+1)`, recién allí puede convertirse en CHEM del lóbulo; luego `B_(k+2)` puede verla en la ruta normal. Si el químico fue creado y consumido entre reacciones del mismo paso, ni siquiera tiene por qué persistir.
- En la ruta alternativa `chem→brain`, la química emitida/receptada en esa invocación puede preceder a la rutina cerebral del **mismo paso de esa ruta**, por lo que la latencia relativa cambia. No se debe convertir la separación `k/k+1/k+2` en milisegundos ni garantizar dos ticks de cerebro: las rutas son condicionales y pueden omitir actualizaciones.
- La semántica de `nominal` escrita en carga genética también impide deducir que todo CHEM distinto de cero deba haberse originado en una recompensa anterior.

**Esto es una deducción de orden parcial, no un oráculo numérico de conducta.** El diagrama omite acciones externas, metabolización específica, decay, otros callbacks y eventos de interfaz que no fueron medidos dinámicamente.

## 3. Diferencia crítica frente a NeuroLab N reducido

El [código `C1ContextBrain.step`](../../experiments/neurolab/c1_context_brain.py) acepta directamente `chemicals=(CHEM0,CHEM1,CHEM2,CHEM3)` en **cada paso**, sin pasar por las reacciones/almacenamiento de pool ni resolver `emitter→receptor`. Además la elección lee `previous_contexts`, introduciendo una latencia perceptiva propia del modelo reducido. El [runner g.10b](../../experiments/neurolab/e09_delayed_distractors_protocol.py) inyecta `REWARD/PUNISHMENT` directamente en esa API a partir de una respuesta que el evaluador declaró correcta.

Por lo tanto, los resultados g.10b/c y NX01 **no prueban** el retraso original de recompensa de un Norn ni su circuito real de crédito temporal. Son experimentos válidos sobre una microred **explícitamente divergente**; copiar sus puntuaciones a H o atribuir el éxito/fallo a química histórica sería incorrecto.

**Punto de mayor valor científico:** el modelo cerebral experimental fue evaluado bajo una **cronología de refuerzo simplificada**. La brecha `pool→receptor→locus→sinapsis` y el orden condicional del scheduler son diferencias cualitativas, antes de discutir parámetros de aprendizaje.

## 4. Qué falta exactamente y qué NO merece rehacerse

**Ya realizado**: 90ms solicitados, WM_TIMER→loop mundial, fases y dos rutas parciales, orden del cerebro y química, cinética local, receptores, enlaces CHEM/SVRule, emisores, análisis de GEN/EXE original, pruebas sintéticas de los auditores. No repetir ni describirlos como pendientes enteros.

**Pendientes específicos para fidelidad H**:
1. **H-08a** identificar, mediante inspección de bytes originales en nueva sesión, todos los disparadores y posibles rutas que alteran el orden/persistencia de recompensa; no basta un listado de llamadas directas si hay dispatch indirecto.
2. **H-08b** estimar solo si se dispone de ejecución del programa original y permiso específico la cadencia efectiva por criatura, pérdidas/reordenamientos de WM_TIMER, pausas y rutas especiales; no afirmar que los 90ms pedidos equivalen a comportamiento observado.
3. **H-08c** un experimento histórico controlado sobre el propio C1 requiere un observador de estados químicos/loci de la criatura real, material original accesible, reproducibilidad y consentimiento antes de ejecutar. Sin esa evidencia, una simulación lógica de los módulos H existentes sirve solo para consistencia interna, **no para certificar fidelidad C1**.

**Disponibilidad comprobada en esta intervención:** el buscador de archivos de conversación/Biblioteca no localizó los EXE/GEN originales, y la búsqueda en Drive tampoco localizó archivos con sus nombres exactos. La evidencia **ya derivada y versionada en GitHub sí está disponible**. Por ahora **no se reejecutó inspección binaria**; no declarar nuevo descubrimiento x86 original. El usuario podría volver a adjuntar EXE/GEN verificados si se aprueba H-08a. No subir originales propietarios al repositorio público.

## 5. Decisión de continuidad

**H-07 documental COMPLETADA.** La reconstrucción histórica ya estableció un conjunto significativo de reglas estáticas; **la pregunta que sí cambiaría una decisión es comprobar la temporización/causalidad efectiva del refuerzo en el motor real**, no generar otro benchmark sintético favorable a redes ni una plataforma neuronal más grande.

**Sin binarios originales accesibles, la siguiente auditoría x86 H-08a necesita que el usuario proporcione de nuevo los archivos EXE+GEN exactos o una vía accesible verificada.** Para H-08b/H-08c además se necesita consentimiento específico para ejecutar el juego y método de observación; no ejecutar sin él. Hasta entonces **PAUSA H activa en ese gate y PAUSA N por criterios científicos**. No nuevas cohortes o modificaciones de Nilo. PR#103 draft, `main` y Nilo0.7 intactos. Conservar ambas líneas, resultados negativos y contratos existentes.
