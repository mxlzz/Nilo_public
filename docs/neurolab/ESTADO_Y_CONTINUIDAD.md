# NeuroLab — estado verificable y protocolo de continuidad

**Estado actualizado:** 2026-11-20 (registro posterior al comienzo de ejecución).  
**Línea base documentada:** protocolo v0.1.0 en rama `docs/neurolab-protocolo-20261120`, propuesto para revisión.  
**Ejecución experimental:** E01–E04 y E06–E08 verificadas en prototipos aislados; E05 falla atribución causal; G09 sigue abierta.  
**Código del cerebro:** módulos E01–E08 en experiments/neurolab/; aún no existe un cerebro que los integre todos.  
**Autorización vigente documentada:** el usuario autorizó continuar ejecución secuencial hasta necesitar intervención; ninguna integración con el motor Nilo 0.7 ni merge a main.

## 1. Marcador canónico de progreso

| Campo | Valor inicial |
|---|---|
| Investigación | NeuroLab: mente neuronal aislada inspirada en Creatures 1 (1996) |
| Documento rector | [README.md](README.md) |
| Etapa actual | E09 — evaluación integral pendiente; G00-H y G05 abiertas |
| Siguiente subtarea exacta | **E09.01 — congelar versiones y resultados reproducibles; integrar componentes luego de la auditoría** |
| Última subtarea validada | E08 — circuitos recurrentes y controles; G09 abierta |
| Experimentos ejecutados | E01–E02 unitarias, E03 experimento preregistrado (20 semillas, controles) |
| Runs con evidencia | [E01+E02 CI](https://github.com/mxlzz/Nilo_public/actions/runs/44850881701), [E03 CI](https://github.com/mxlzz/Nilo_public/actions/runs/44851094727), [E04 CI](https://github.com/mxlzz/Nilo_public/actions/runs/44851265622), [E05 CI](https://github.com/mxlzz/Nilo_public/actions/runs/44851485383) |
| Última corrida del cerebro | Experimentos sintéticos E03 con aprendizaje local por refuerzo; sin cuerpo/mundo/LLM |
| Estado de E00 | [Informe histórico inicial](E00_INFORME_HISTORICO_01.md): G00-H abierto por incertidumbres; G00-N habilita variante propia E01 |
| Estado del código | Módulos E01–E08; 85 métodos de test (E07 +10, E08 +8) |
| Integración con Nilo 0.7 | Ninguna |
| Bloqueos | E00.02 exactitud del genoma y discrepancia histórica salida=state vs state-threshold; no bloquean experimento N rotulado como propio |
| Decisiones nuevas pendientes | Fidelidad C1 vs adaptación mínima tras E00 |

**Regla:** nunca actualizar `última subtarea validada` sin prueba enlazada al commit, log/fixture y criterio de aceptación. Si se hace un paso pero no se logra evidencia suficiente, permanece en curso/bloqueado. No marcar «terminada» una etapa porque se produjo un texto sobre ella.

## 2. Estado por fase

| Fase | Estado inicial | Próxima subtarea | Requisito de cierre |
|---|---|---|---|
| E00 | Parcial para H, suficiente N | E00.02 (genoma original), arqueología paralela | G00-H sigue abierta; G00-N documentada |
| E01 | Validación automatizada | — | CI E01, 19 tests; benchmark en workflow |
| E02 | Validación automatizada | — | CI E02, 8 tests; sin aprendizaje |
| E03 | Validada N | — | [G03 CI verde](https://github.com/mxlzz/Nilo_public/actions/runs/44851094727); no replica C1 |
| E04 | Validada como dinámica sináptica aislada | — | [CI E04](https://github.com/mxlzz/Nilo_public/actions/runs/44851265622); no integrado al selector aún |
| E05 | **Parcial / límite negativo confirmado** | Revisar crédito causal | G05 no superada; refuerzo espurio en distractor correlacionado |
| E06 | Validada: invariancia contextual, no creación de conceptos | — | CI 44851722169 |
| E07 | Verificada en modelo experimental | — | [CI E07](https://github.com/mxlzz/Nilo_public/actions/runs/44852027094), sin ventaja demostrada frente a LRU |
| E08 | Verificada dinámica matemática | — | [CI E08](https://github.com/mxlzz/Nilo_public/actions/runs/44852126108) |
| E09 | Auditoría intermedia, sin integración | E09.01 | [Informe](E09_AUDITORIA_INTERMEDIA.md), G09 abierta |

No avanzar en una fase solo porque exista su definición en este archivo.

## 3. Registro de cada intervención futura

Agregar una nueva sección fechada, sin borrar las anteriores:

```markdown
### YYYY-MM-DD — NL-LOG-0001
- Objetivo/subtarea: E00.01
- Estado antes: pendiente
- Trabajo efectivamente ejecutado:
- Artefactos creados/modificados (ruta, SHA y enlace):
- Fuentes y evidencia, con grado de certeza:
- Pruebas y resultados reales (incluidos fallos):
- Limitaciones / hechos no comprobados:
- Criterio de aceptación aplicable:
- Resultado: validado | en curso | bloqueado | fallido | descartado
- Decisión y motivo:
- Siguiente subtarea exacta:
- Estado después:
```

Si se trabaja en PR o branch no fusionado, indicarlo explícitamente: un cambio en una rama experimental **no está en `main`**.

## 4. Procedimiento obligatorio para retomar desde otro chat

1. Abrir el [issue #102](https://github.com/mxlzz/Nilo_public/issues/102) y seguir su enlace a este protocolo.
2. Leer este archivo en la rama/commit donde efectivamente se trabaja, **no asumir que `main` lo contiene** si no hubo merge.
3. Verificar en GitHub el head de branch/PR y últimos commits; no inferir estado por conversaciones anteriores.
4. Leer la siguiente subtarea E##.## y sus dependencias en [ETAPAS_00_09.md](ETAPAS_00_09.md).
5. Consultar [FUENTES_Y_RECONSTRUCCION.md](FUENTES_Y_RECONSTRUCCION.md) y [PROTOCOLO_EVALUACION.md](PROTOCOLO_EVALUACION.md) pertinentes.
6. Confirmar permiso y alcance de esa intervención (documentar, programar o ejecutar pruebas). No interpretar la orden «continuá» como autorización general para modificar el motor Nilo 0.7 o fusionar ramas.
7. Ejecutar la mínima unidad verificable; registrar artefactos y fallos.
8. Actualizar exactamente un estado canónico, enlazar issue/PR/commit/ensayo y dejar la siguiente subtarea.
9. Si hay discrepancia entre archivo e issue, investigar qué fuente es más reciente y verificada; **no sumar ambos estados automáticamente**.
10. Reportar en el chat: hecho comprobado, evidencia, incertidumbre, siguiente paso.

**Prompt de continuidad sugerido (información de entrada, no autorización implícita):**
> Continuá NeuroLab según mxlzz/Nilo_public: issue #102 y docs/neurolab/ESTADO_Y_CONTINUIDAD.md. Verificá la rama/PR real, identificá la siguiente subtarea pendiente, ejecutá solo lo autorizado y dejá trazas, pruebas y siguiente paso sin saltar puertas de aceptación.

## 5. Política de decisiones

No tomar como decisiones confirmadas las propuestas del asistente. Una decisión de diseño se registra con:
- ID (NL-DEC-0001), fecha, estado `propuesta/aceptada/rechazada/reemplazada`;
- contexto, opciones y evidencia;
- criterio explícito de adopción;
- consecuencias y costes;
- quién la aprobó, si corresponde;
- reversibilidad y pruebas de regresión.

**Decisiones confirmadas por conversación hasta ahora:**
- La nueva investigación debe centrarse en comprender C1 antes de ampliar el sistema.
- El primer objeto experimental es la mente aislada, sin cuerpo/mundo y sin LLM.
- El programa debe seguir pasos y validaciones, con documentación suficiente para retomarlo.
- Dejar asentado el plan actual en GitHub, sin implementar todavía código de Nilo.

**Propuestas todavía NO aprobadas:** utilizar un controlador tabular, adoptar una ecuación propia, añadir instintos, elegir un LLM externo, construir un cuerpo/mundo, crear un agente desarrollador autónomo, integrar a la 0.8.

## 6. Control de versiones y fusiones

- Protocolo en rama docs específica, PR en borrador hacia `main` para revisión; el merge se deja para decisión posterior.
- Las ejecuciones futuras deben usar ramas separadas con commit por unidad verificable; conservar baseline.
- Nunca mezclar documentación de fidelidad histórica con código experimental sin etiquetar divergencia.
- Ante cambios del protocolo, actualizar versión, motivación, impacto sobre evaluaciones anteriores y migración de IDs.
- No borrar datos de ejecución negativos; si un archivo grande no debe entrar a Git, mantener índice de artefacto verificable con suma SHA y ubicación.

## 7. Registro de intervenciones

**NL-LOG-0000 — 2026-11-20**
- Subtarea: preparación documental del protocolo, externa a E00.
- Se registró el procedimiento integral para E00–E09, metodología y fuentes a verificar.
- No se ejecutó E00.01; no hay resultados ni capacidad neuronal demostrada.
- Siguiente acción verificable: E00.01.


### 2026-11-20 — NL-LOG-0001 (E00)
- Se leyeron y contrastaron directamente ocho fuentes C1, incluidas dos de los autores (paper Grand/Cliff/Malhotra y `I Am Ron's Brain` fechado 1995).
- Evidencia: [E00_INFORME_HISTORICO_01.md](E00_INFORME_HISTORICO_01.md).
- E00.01 validada; E00.02 solo parcial (se conoce `dad1.gen` pero no hash); E00.03 y E00.07 con base documental; el resto contiene lagunas explicitadas.
- G00-H (réplica fiel): **ABIERTA**; discrepancia de salida sobre umbral y orden exacto de tick.
- G00-N (modelo propio): admite E01 si el motor deja claras sus convenciones. No se resolvieron dudas por suposición.

### 2026-11-20 — NL-LOG-0002 (E01)
- Código experimental nuevo: [kernel.py](../../experiments/neurolab/kernel.py), [tests E01](../../experiments/neurolab/tests/test_kernel.py), [bench.py](../../experiments/neurolab/bench.py).
- En [CI #44850766887](https://github.com/mxlzz/Nilo_public/actions/runs/44850766887), SHA `2d7a8496677702e9364ea0534c1c4ea0b49cef89`, compilación y **19 tests E01 exitosos**.
- Benchmark de 100.000 ciclos incorporado a CI y ejecutado en [run #44850839844](https://github.com/mxlzz/Nilo_public/actions/runs/44850839844); en este registro se confirma paso correcto, no se inventan métricas numéricas del log.
- Cubre activación, umbral dos variantes, excitación/inhibición, saturación, reposo, propagación retardada de 1 tick, determinismo y checkpoint. Sin aprendizaje.
- G01 funcional: **VALIDADA para modelo NeuroLab**, no para reconstrucción byte a byte de Creatures 1.

### 2026-11-20 — NL-LOG-0003 (E02)
- Código de seis neuronas: [circuit.py](../../experiments/neurolab/circuit.py), [8 tests E02](../../experiments/neurolab/tests/test_circuit.py).
- [CI #44850881701](https://github.com/mxlzz/Nilo_public/actions/runs/44850881701), SHA `a267c5b73512ccd594bb2775cf948211614cffe3`, compila y ejecuta **27 métodos de test (19 E01 + 8 E02)**; conclusión `success`.
- Demuestra propagación E→C→D, WTA explícito, empates, inactividad, repeticiones por semilla, variación sin respuesta correcta cableada y pesos estables.
- G02 funcional: **VALIDADA**, siempre sin aprendizaje ni mundo. Etapa siguiente: E03.01.

**Advertencia de trazabilidad:** los SHA de CI corresponden a los commits indicados, no necesariamente al HEAD futuro cuando se agreguen E03+.


### 2026-11-20 — NL-LOG-0004 (E03)
- Pre-registro previo a implementación: [E03_PRE_REGISTRO.md](E03_PRE_REGISTRO.md), fija 20 semillas, 100 episodios iniciales, 160 de inversión, holdouts y controles congelados, tasa de ajuste ±16 por refuerzo.
- Código: [plasticity.py](../../experiments/neurolab/plasticity.py), [e03_protocol.py](../../experiments/neurolab/e03_protocol.py), [tests E03](../../experiments/neurolab/tests/test_plasticity.py).
- [Ejecución CI #44851094727](https://github.com/mxlzz/Nilo_public/actions/runs/44851094727), SHA `ea4cf2de7ba9166edfefb568536f24c2a911bdaf`: **success**, pruebas y evaluación preregistrada completadas sin errores.
- La suite contiene 37 métodos de test (19 E01, 8 E02, 10 E03); los tests de E03 comprueban aislamiento de la contingencia en evaluador, feedback posterior a decisión, ausencia de aprendizaje en baseline congelado, reversión, seeds y checkpoint.
- El runner `run_all` sale con error si no se cumplen simultáneamente ≥18/20 semillas con exactitud ≥0.90 tras aprendizaje, ≥18/20 tras inversión y mejora media ≥0.30 frente al control congelado. Al completarse el paso con `success`, **los tres umbrales preregistrados se alcanzaron**, pero aquí no se inventan valores exactos que no se recuperaron del stdout.
- Resultado: G03 **VALIDADA para el modelo experimental N**, no es aprendizaje químico de C1 ni una mente autónoma general.
- Siguiente: E04.01 (STW/LTW de dos tiempos).

### 2026-11-20 — NL-LOG-0005 (E04)
- Pre-registro previo al código: [E04_PRE_REGISTRO.md](E04_PRE_REGISTRO.md): STW/LTW de modelo propio, refuerzo breve y prolongado, reposo sin recompensa y control de un peso.
- Código: [twin_weight.py](../../experiments/neurolab/twin_weight.py), [tests E04](../../experiments/neurolab/tests/test_twin_weight.py).
- [CI #44851265622](https://github.com/mxlzz/Nilo_public/actions/runs/44851265622), SHA `9b0960667fa27bbc2ba9e0dcf7f0896dcf246151`: `success`. Tests manuales, saturación, recuperación, memoria lenta, inversión sostenida y checkpoint superados.
- **G04 validada solo para la dinámica aislada de STW/LTW de NeuroLab.** No se ha medido todavía si un cerebro que utiliza ese mecanismo generaliza mejor ni se lo presenta como reproducción histórica exacta.
- Siguiente: E05.01 — elegibilidad temporal para una asociación ya existente.

### 2026-11-20 — NL-LOG-0006 (E05)
- Pre-registro previo al código: [E05_PRE_REGISTRO.md](E05_PRE_REGISTRO.md); ecuación propia elegibilidad=floor(3e/4), peso posterior condicionado por floor(32e/255).
- Código: [eligibility.py](../../experiments/neurolab/eligibility.py), [10 tests E05](../../experiments/neurolab/tests/test_eligibility.py).
- [CI #44851485383](https://github.com/mxlzz/Nilo_public/actions/runs/44851485383) para SHA `c24a6c6a21ae4ff313b18cfb0c1dca06dbdfb31b`: `success` (57 métodos de prueba, y evaluación prereg E03 todavía verde).
- Refuerzo sin uso previo: 0; refuerzo inmediato: +32; retraso temporal discreto reduce influencia; elegibilidad y checkpoint deterministas.
- **Caso negativo confirmatorio:** A causa refuerzo, B distrae y se activa después; elegibilidad A=107, B=191; ante premio +1, A termina peso 141 y B peso 151 (ambos desde128). El algoritmo refuerza **más a B**, pese a que B no causó la consecuencia.
- Diferenciar **tests del cálculo esperable: éxito**, de **hipótesis de crédito causal correcto: NO VERIFICADA / FALLA EN ESTE CASO**. **Puerta G05 permanece abierta**, no aprobar hasta abordar limitación por diseño o delimitar el escenario de uso.
- **Trabajo permitido independiente:** E06 solo evaluará detectores de patrones y transferencia con refuerzo inmediato de E03; no integrará ni dependerá de la elegibilidad E05. Registrar antes el diseño y no afirmar que se saltó la puerta G05.
- La elección histórica vs nueva regla correctiva queda abierta para una decisión posterior basada en ensayos, sin imponer una respuesta por comodidad.


### 2026-11-20 — NL-LOG-0007 (E06)
- Pre-registro: [E06_PRE_REGISTRO.md](E06_PRE_REGISTRO.md), con 20 semillas, XOR, contexto C inédito y tres controles (memoria exacta, singleton aditivo, sin plasticidad).
- Implementación: [concepts.py](../../experiments/neurolab/concepts.py), [e06_protocol.py](../../experiments/neurolab/e06_protocol.py), [tests E06](../../experiments/neurolab/tests/test_concepts.py).
- [CI #44851722169](https://github.com/mxlzz/Nilo_public/actions/runs/44851722169), SHA `eeb0945a338b4167008e0138b2a8440b82a55610`: success, pasa tests y criterios preregistrados (≥18/20 semillas con precisión ≥0.90, ventaja media ≥0.20 sobre memorizador y ≥0.15 sobre singleton).
- **Resultado acotado:** detectores conjuntivos **predefinidos** permiten retener decisiones ante señal distractora nueva. No aprende la representación de conceptos, no transfiere a pares esenciales no entrenados.
- E06 fue ejecutada independientemente de E05; no modifica G05 que permanece abierta.

### 2026-11-20 — NL-LOG-0008 (E07.01, primera verificación)
- Paper primario Grand/Cliff/Malhotra: migración de dendritas cuando `strength=0` **sí** parte del modelo presentado; migraciones permanecen en el mismo lóbulo de origen. Un mecanismo *adicional* de competencia «supervivencia del más apto» fue dejado desconectado, **no** toda la migración.
- Guía C1 posterior (fuente secundaria): detalla dos estilos diferentes, Decision-style y Concept-style, y restricciones de duplicados, exclusividad y actividad. La exactitud byte a byte de esas rutinas respecto al ejecutable de 1996 permanece abierta.
- Fuentes directas: [paper de autores](https://eem.foo/ccarchive/Sites/fp.cyberlifersrch.plus.com/articles/agents_%2797_paper.htm) y [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html).
- Descubrimiento de [Gene Loom](https://lisdude.com/Creatures/Community/GeneLoom/) (v1.8.0, junio 2026), editor que admite genomas C1: alternativa existente para inspeccionar el `dad1.gen` auténtico **si se dispone legítimamente del archivo**, sin obligar a desarrollar un editor de genomas.
- **E07.01 parcialmente verificada** a nivel de principios y estilos; parámetros y genoma exacto todavía abiertos. El archivo original no fue adquirido ni analizado.


### 2026-11-20 — NL-LOG-0009 (E07)
- [Pre-registro E07](E07_PRE_REGISTRO.md); dos slots, patrones antiguos y nuevos, controles con conexiones fijas y LRU.
- Código: [rewiring.py](../../experiments/neurolab/rewiring.py), [e07_protocol.py](../../experiments/neurolab/e07_protocol.py), [tests E07](../../experiments/neurolab/tests/test_rewiring.py).
- [CI #44852027094](https://github.com/mxlzz/Nilo_public/actions/runs/44852027094), SHA `c6542f53f7656699f871a5757a90060b1667e4ee`, `success`: umbral preregistrado satisfecho.
- Conexiones reutilizadas bajo cupo fijo y olvido de asociaciones anteriores. No se infiere superioridad a LRU ni equivalencia histórica de reglas de atrofia. E07.01: Grand confirma migración cuando strength=0, salvo mecanismo competitivo adicional desconectado.

### 2026-11-20 — NL-LOG-0010 (E08)
- [Pre-registro E08](E08_PRE_REGISTRO.md), dos neuronas recurrentes, controles sin conexiones y con atenuación.
- Código: [recurrent.py](../../experiments/neurolab/recurrent.py) y [tests E08](../../experiments/neurolab/tests/test_recurrent.py).
- [CI #44852126108](https://github.com/mxlzz/Nilo_public/actions/runs/44852126108), SHA `060ecc3d369e18a4627b8c0a7c0bfbab3b3dc671`, `success`.
- Oscilación de dos ticks caracterizada, control sin recurrencia se apaga; no atribuir pensamientos.

### 2026-11-20 — NL-LOG-0011 (E09, auditoría preliminar)
- [E09_AUDITORIA_INTERMEDIA.md](E09_AUDITORIA_INTERMEDIA.md): capacidades parciales comprobadas, sin unificación bajo un cerebro/tick común.
- **G09 abierta**; G05 abierta por atribución equivocada; G00-H abierta por genoma original y reglas históricas contradictorias.
- Próximo trabajo técnico: E09.01 exportar resultados agregados, congelar configuraciones y luego investigar integración con controles.