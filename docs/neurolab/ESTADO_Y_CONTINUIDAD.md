# NeuroLab — estado verificable y protocolo de continuidad

**Estado actualizado:** 2026-11-21 (E09.02i-I3 benchmark químico-conductual preregistrado NO aprobó; el acoplamiento I1/I2/I1b sigue técnicamente válido. Diagnóstico I3a observacional en curso; G05/G09/G00-H abiertas).
**Línea base documentada:** protocolo v0.1.0 en rama `docs/neurolab-protocolo-20261120`, propuesto para revisión.  
**Ejecución experimental:** E01–E09g.10c e h.1–h.6 preservadas, I1/I2/I1b técnicos validados y **I3 ejecutado en 20 semillas 200..219**: M0.513889/0.534722, F0.5125/0.534722, C0.890278/0.845833, Q1/1, fases primera/invertida. [Run #44952276187](https://github.com/mxlzz/Nilo_public/actions/runs/44952276187) success técnico; gate científico I3 false.
**Código del cerebro:** inspección estática del ejecutable y genoma C1 alimenta módulos E09f (SVRule, sinapsis, strength, migración) y microredes E09g de cinco y seis unidades; sin motor Nilo, cuerpo, mundo ni LLM.  
**Autorización vigente documentada:** el usuario autorizó continuar ejecución secuencial hasta necesitar intervención; ninguna integración con el motor Nilo 0.7 ni merge a main.

## 1. Marcador canónico de progreso

| Campo | Valor inicial |
|---|---|
| Investigación | NeuroLab: mente neuronal aislada inspirada en Creatures 1 (1996) |
| Documento rector | [README.md](README.md) |
| Etapa actual | **E09.02i I3: NEGATIVA**. Química M no supera congelado F (+0.000694 de exactitud promediada ambas fases). [Informe](E09_02I_I3_RESULTADO_NEGATIVO.md) y [resumen](resultados/e09i3_resultado_resumen.json). I3a diagnóstico posthoc preregistrado y en revisión |
| Siguiente subtarea exacta | **E09.02i-I3a diagnóstico observacional**, sin cambiar modelo: comprobar CHEM, susceptibilidad, reinforcement_effect, cambios STW en 20 semillas I3 y equivalencia de replay; si prueba falla, documentar bloqueo. **No ajustar parámetros ni reutilizar estas semillas para validación confirmatoria** |
| Última subtarea validada | **E09.02i-I3 ejecutada como resultado NEGATIVO verificable**, no gate aprobada: [preregistro](E09_02I_I3_BENCHMARK_PRE_REGISTRO.md), [resultado](E09_02I_I3_RESULTADO_NEGATIVO.md), [CI técnico success](https://github.com/mxlzz/Nilo_public/actions/runs/44952276187), artefacto per-seed 14725468833; I1/I2/I1b técnicas siguen vigentes |
| Experimentos ejecutados | E01–E09g.10c; h.1–h.6; I1/I2/I1b y **I3 20 semillas×dos fases×60 entrenamiento/36 holdout**, químicos sintéticos rate40/dose80, 4 brazos M/F/C/Q; cero semillas M superaron≥90% en ambas fases |
| Runs con evidencia | [g.10b](https://github.com/mxlzz/Nilo_public/actions/runs/44942700990), [h.1](https://github.com/mxlzz/Nilo_public/actions/runs/44944783092), [h.4](https://github.com/mxlzz/Nilo_public/actions/runs/44947923270), [h.6](https://github.com/mxlzz/Nilo_public/actions/runs/44949141624), [I1](https://github.com/mxlzz/Nilo_public/actions/runs/44951342148), [I2](https://github.com/mxlzz/Nilo_public/actions/runs/44951467547), [I1b](https://github.com/mxlzz/Nilo_public/actions/runs/44951833784), [I3](https://github.com/mxlzz/Nilo_public/actions/runs/44952276187) |
| Última corrida del cerebro | **I3**, seis unidades/ocho dendritas continuas. Aprendizaje M (química) ≈ congelado F, mientras referencia C pulsa directamente y Q tiene procedencia causal privilegiada. No se alcanzó criterio I3; G05/G09 abiertas |
| Estado de E00 | E00 GEN y EXE originales contrastados previamente; h.4 receptor→loci CHEM y h.5 emisor→pool verificados estáticamente; h.6 establece ruta condicional y cadencia solicitada de 90 ms, pero no ejecución efectiva ni química global |
| Estado del código | E01–E09g, h.1–h.6; I1/I2/I1b; [I3 runner](../../experiments/neurolab/e09_i3_metabolic_protocol.py), [CI I3](../../.github/workflows/neurolab-i3.yml), [I3a diagnóstico read-only](../../experiments/neurolab/e09_i3a_diagnostic.py) pendiente de CI. No se modificó C1ContextBrain ni Nilo estable |
| Integración con Nilo 0.7 | Ninguna |
| Bloqueos | I3 no mejora aprendizaje bajo tasas sintéticas40/dosis80; origen preciso requiere diagnóstico. Tasas reales GEN, emisión cerebral automática a puertos y cadencia efectiva siguen sin reconstrucción completa. No es válido atribuir el fracaso a C1 real |
| Decisiones nuevas pendientes | Fidelidad dinámica integral aún no comprobada; E09e propio no es una réplica histórica. No resolver diferencias con hipótesis no testeadas ni adoptar g.10 neuronal sin puerta G05 |

**Regla:** nunca actualizar `última subtarea validada` sin prueba enlazada al commit, log/fixture y criterio de aceptación. Si se hace un paso pero no se logra evidencia suficiente, permanece en curso/bloqueado. No marcar «terminada» una etapa porque se produjo un texto sobre ella.

## 2. Estado por fase

| Fase | Estado inicial | Próxima subtarea | Requisito de cierre |
|---|---|---|---|
| E00 | Genoma original del CD comparado con parche; PE32 C1 examinado estáticamente | Reproducir scheduler/química completos si se exige fidelidad bit a bit | [Genoma original](E00_GENOMA_ORIGINAL_COMPARACION.md), [análisis PE32](E09_02F_INFORME_EJECUTABLE.md); G00-H parcial |
| E01 | Validación automatizada | — | CI E01, 19 tests; benchmark en workflow |
| E02 | Validación automatizada | — | CI E02, 8 tests; sin aprendizaje |
| E03 | Validada N | — | [G03 CI verde](https://github.com/mxlzz/Nilo_public/actions/runs/44851094727); no replica C1 |
| E04 | Validada como dinámica sináptica aislada | — | [CI E04](https://github.com/mxlzz/Nilo_public/actions/runs/44851265622); no integrado al selector aún |
| E05 | **Parcial / límite negativo confirmado** | Revisar crédito causal | G05 no superada; refuerzo espurio en distractor correlacionado |
| E06 | Validada: invariancia contextual, no creación de conceptos | — | CI 44851722169 |
| E07 | Verificada en modelo experimental | — | [CI E07](https://github.com/mxlzz/Nilo_public/actions/runs/44852027094), sin ventaja demostrada frente a LRU |
| E08 | Verificada dinámica matemática | — | [CI E08](https://github.com/mxlzz/Nilo_public/actions/runs/44852126108) |
| E09 | I1/I2/I1b acoplamiento técnico validado; **I3 falló gate preregistrada** con 20 semillas y controles; H y C1 completo siguen parciales | I3a observar refuerzo sináptico real sin parámetros nuevos y conservar resultado; decidir posterior ensayo confirmatorio con nuevas semillas | [I3 resultado](E09_02I_I3_RESULTADO_NEGATIVO.md), [evidencia run](https://github.com/mxlzz/Nilo_public/actions/runs/44952276187), [I3a prereg](E09_02I_I3A_DIAGNOSTICO_POSTHOC_PRE_REGISTRO.md) |

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

### 2026-11-20 — NL-LOG-0012 (E09.01 — evidencia congelada)
- Corrida canónica preintegración: [GitHub Actions #44852299967](https://github.com/mxlzz/Nilo_public/actions/runs/44852299967), job `136686250858`, commit ensayado `56cb2e7456103eee7a65cdadc275da01a1869720`, `success`.
- Artefacto Actions `neurolab-metrics` confirmado (ID `14686047092`, retención temporal). Sus cinco resultados JSON se recuperaron del log y están **guardados permanentemente como documentos versionados en GitHub** bajo [resultados/run-44852299967](resultados/run-44852299967/).
- Índice canónico con métricas exactas por fase: [E09_EVIDENCE_INDEX.md](E09_EVIDENCE_INDEX.md).
- E03 exactitud media=1.0, control congelado=0.425, reversión=1.0; E06 conceptos=1.0 vs singleton=0.5375 y memorizador=0.5; E07 migración=1.0 vs fixed=0.5 **y LRU=1.0**, olvido antiguo medio=0.5.
- Se ha cumplido **E09.01 (conservación reproducible de evidencia)**, no E09.02–09.10 ni G09.
- **Intervención necesaria para fidelidad histórica:** obtener `dad1.gen` auténtico de Creatures 1 (o un genoma C1 equivalente con procedencia verificable). Si el usuario prefiere continuar sin ese archivo, el siguiente trabajo debe reconocer que la mente será una variante propia basada en principios documentados, no reconstrucción fiel. Esa decisión no está asumida aquí.


### 2026-11-21 — NL-LOG-0013 (E00.02 — archivo aportado)
- **ZIP inspeccionado:** `Updated C1 V2.zip`, SHA256 `2661f07b33a4d617c723466883ac9dbfc14a4211dad674a6d3cae9a936130d4f`; archivo de usuario, no subido a repo.
- **dad1.gen localizado:** SHA256 `f32c0cac5985d9c71c9a6765b98cd321dd49574f315a1f2813cd4f0bb91babfe`; 20.001 bytes, 320 genes y 9 registros de lóbulos tipo/subtipo 0/0 identificados mediante marcadores de formato C1. La comparación interna con siete genomas del paquete revela identidad byte a byte de sus nueve registros de lóbulos.
- **Origen modificado confirmado** por `readme.txt`: cambio para evitar inmortalidad y corregir envejecimiento; no se afirma originalidad del genoma.
- **Registro exhaustivo y fuentes:** [comentario en issue #102](https://github.com/mxlzz/Nilo_public/issues/102#issuecomment-7064159473).
- E00.02 ha avanzado desde ausencia de archivos concretos a espécimen modificado identificable/hasheado. **G00-H sigue abierta** por falta de referencia original de 1996 y divergencias del ejecutable no resueltas.
- Siguiente subtarea documental: interpretar los nueve genes de lóbulos reales y sus campos SVRule; comparar contra documentación de C1 y prototipo N. No subir ni redistribuir genomas de terceros.


### 2026-11-21 — NL-LOG-0014 (dad1.gen del CD y nueve lóbulos decodificados)
- El usuario aportó `dad1.gen` extraído de `INSTALL/DATA.Z` en la imagen del CD. Archivo analizado: 10001 bytes, SHA-256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. **No se subió el binario**.
- Comparado contra `Updated C1 V2.zip/dad1.gen` (20001 bytes, SHA-256 `f32c0cac5985d9c71c9a6765b98cd321dd49574f315a1f2813cd4f0bb91babfe`).
- 320 marcadores `gene` en ambas; mismos offsets. Solo 15 posiciones byte diferentes (7834,7835,7837,7839–7850); el cambio es el último gen (reacción → receptor químico) y posición de `gend`. Los nueve genes neuronales son **idénticos byte por byte**.
- [Informe técnico E00-H02](E00_GENOMA_ORIGINAL_COMPARACION.md): nueve lóbulos 112+16+40+16+40+32+16+40+640=**952** posiciones, SVRules extraídas, conectividad Decision (128+128 dendritas por neurona), Attention (1+1), Concept (1–3).
- [Mapa E00-H03](E00_MAPA_NEUROQUIMICO_C1.md): seis receptores y tres emisores cerebrales originales, con químicos identificados por códigos numéricos. No se asignan nombres funcionales no contrastados.
- Código de inspección reproducible [c1_genome_inspector.py](../../experiments/neurolab/c1_genome_inspector.py) y [siete pruebas sintéticas](../../experiments/neurolab/tests/test_c1_genome_inspector.py): primer CI falló por tratar `gend` como parte de un gen terminal; causa documentada, corregida sin tocar datos. [CI corregida #44919429305](https://github.com/mxlzz/Nilo_public/actions/runs/44919429305): **success**, conjunto de tests de NeuroLab validado.
- La estructura **genética** C1 queda muy bien especificada para este archivo aportado; G00-H **ejecutable** permanece abierta en cálculos hardcoded, reloj y parámetros/identidad química exacta. No atribuir fidelidad total a NeuroLab E01–E08.
- Próximo paso: E09.02a definir microcircuito de prueba con las SVRules y conexiones históricas verificables, haciendo explícitas las convenciones temporales propias y controles necesarios.


### 2026-11-21 — NL-LOG-0015 (E09.02a–e, línea experimental y evidencia)

- **E09.02a**: tres SVRules originales `ANDTYPE0`, `STATE PLUS TYPE0 MINUS TYPE1`, `STATE PLUS TYPE0 PLUS TYPE1` decodificadas y probadas con oráculos; [especificación](E09_02A_PRE_REGISTRO_SVRULE_C1.md), [módulo](../../experiments/neurolab/c1_svrule_subset.py).
- **E09.02b**: circuito mínimo de cinco unidades P0,P1,C,D0,D1, sin aprendizaje, con reglas neuronales C1; [protocolo](E09_02B_MICROCIRCUITO_PRE_REGISTRO.md), [código](../../experiments/neurolab/c1_microcircuit.py), tests CI verificados.
- **E09.02c**: primer refuerzo fijo ±16, aprende primera preferencia con precisión1.0 pero **falla inversión** (precisión0.30, 6/20 semillas). [Registro negativo](E09_02C_RESULTADO_NEGATIVO.md).
- **E09.02d**: con exploración ε=0.10, sube inversión a0.80 y16/20, pero **NO supera** criterio18/20. [Registro negativo](E09_02D_RESULTADO_NEGATIVO.md).
- **E09.02e**: idénticas cinco unidades y política original, pero con 4 sinapsis STW/LTW (reglas NUMÉRICAS de E04, no ejecutable C1). Aprendizaje original1.0, reversión1.0, **20/20 semillas** superan ambas puertas. Control congelado media0.4925. [Reporte completo](E09_02E_RESULTADOS_STW_LTW.md).
- **Corrida canónica:** [CI #44920963462](https://github.com/mxlzz/Nilo_public/actions/runs/44920963462), commit probado `7066bef28ff6788cb89b4dc85063238e40f0331b`, `success`; resultados íntegrales con pesos por semilla en [E09c](resultados/run-44920963462/e09c_negative.json), [E09d](resultados/run-44920963462/e09d_negative.json), [E09e](resultados/run-44920963462/e09e_stw_ltw.json). El job preserva ambos controles negativos sin alterar su criterio preregistrado; los tests se etiquetan `expectedFailure` para los resultados negativos conocidos, nunca aprobados como G09.
- **Genética neuroquímica C1:** [químicos49/50/51/52/53/70](E00_MAPA_NEUROQUIMICO_C1.md) verificados con nombres históricos; [reacciones de drive y refuerzo](E00_QUIMICA_REFUERZO_C1.md) decodificadas de `dad1.gen`; [lector de genes de reacción](../../experiments/neurolab/c1_reaction_inspector.py) y tests agregados. No se subieron archivos del juego.
- **Estado crítico:** una red pequeña con dos velocidades funciona en la tarea sintética, pero las tasas de relajación experimental NO son las de la máquina de 1996 verificadas; no se demostró una mente C1 fiel ni unificación E01–E08 en un solo sistema; crédito causal diferido E05 sigue fallando. **Siguiente E09.02f:** reproducción/supervisión de un tick sináptico C1 y comparación contra nuestro E09e; para equivalencia exacta se necesita inspección del ejecutable original del CD.



### 2026-11-21 — NL-LOG-0016 (Creatures.exe y fases f.1–f.4)

- **Binario original de usuario examinado estáticamente**: `Creatures.exe` PE32 GUI x86, 387072 bytes, SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`. Metadata PE: timestamp 1997-08-06 y versión 1.0.0.1. **No ejecutado ni subido a GitHub**.
- [Informe forense con offsets/direcciones](E09_02F_INFORME_EJECUTABLE.md).
- **f.1** `c1_runtime_math.py`: aritmética SVRule por operación con saturación byte, multiplicación y señal de dendrita `>>8`, salida `max(0,state-threshold)`, competencia WTA verificada; [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44929478194).
- **f.2** `c1_decay_math.py`: helpers decay/relax de VA0x419E40 y0x419E90, dos tablas de32 valores por rate y máscaras temporales, LTW cambia una unidad cuando tick%rate=0; [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44929737314).
- **f.3** `c1_dendrite_tick.py`: sus +4/wrap o decay, refuerzo STW según sus×chemical >>8, relajación STW hacia LTW, LTW ±1 con tasa genética. Test inicial con error de fixture de rate0, corregido sin modificar implementación; [CI verde](https://github.com/mxlzz/Nilo_public/actions/runs/44930063295).
- **f.4** `c1_strength.py`: ganancia de fortaleza según regla y tasa, pérdida decremental y reinicio de campos cuando se agota. [CI verde](https://github.com/mxlzz/Nilo_public/actions/runs/44930221183): 188 tests, 2 fallos experimentales **expectedFailure** correspondientes a E09c/d, sin otros errores.
- **Hallazgo f.5 preliminar**: en el mismo ejecutable las rutinas VA0x404A80 y0x404B90 gestionan migración/reconexión con criterios distintos (Decision-style y Concept-style), aún sin especificación/reimplementación. No suponer algoritmo de E07 equivalente.
- **Divergencia cuantitativa** respecto de E09e preservada: con STATE80+TYPE0 240−TYPE1 200, la convención vieja devuelve120 y la del binario55. El primer refuerzo con sus0/chemical255 en tick1 da STW3/LTW0 bajo dinámica parcial C1, contra STW26/LTW1 del modelo experimental E09e. **Sus resultados previos siguen válidos solo para el modelo anterior**.
- **Próximo E09.02f.5**: caracterizar migración desde los dos bloques x86 y diseñar test falsable. Después E09.02g microcerebro C1 con reglas numéricas/temporales corregidas; no saltar a 952 unidades sin justificación.
- G00-H (fidelidad completa), G05 (crédito causal) y G09 (mente mínima integrada) permanecen ABIERTAS.



### 2026-11-21 — NL-LOG-0017 (E09.02f.5 — mapeo preliminar de migración)

- [Mapa de migración](E09_02F_05_MIGRACION_ANALISIS.md) redactado a partir de inspección de las direcciones x86 **0x404A80** (tipo1, Decision-style) y **0x404B90** (tipo2, Concept-style).
- Tipo1 reutiliza slot con strength0 y elige fuente entre neuronas candidatas; evita fuentes duplicadas, reinicia LTW/STW y strength en rangos genéticos y puede no reconectar.
- Tipo2 reordena candidatos y verifica combinaciones de fuentes, con criterios internos de firmas suma/producto y reglas para evitar ciertas duplicaciones; en casos de fallo los pesos/fortaleza permanecen sin conexión.
- **No se implementaron aún esas rutas** porque falta reconstruir sus firmas, PRNG y condiciones específicas. No confundir esto con el recableado experimental E07, que no aventajó a LRU.
- Próxima subtarea f.5a: especificación completa verificada y oráculos; f.5b: implementación por tipo. Ninguna intervención del usuario requerida para continuar inspección estática.


### 2026-11-21 — NL-LOG-0018 (migración, SVRule y microred C1 de cinco unidades)
- Ruta de migración tipo1 Decision y tipo2 Concept analizadas, [preregistradas](E09_02F_05A_MIGRACION_PRE_REGISTRO.md), [implementadas con rand inyectado](../../experiments/neurolab/c1_migration.py), verificadas contra oráculos de duplicado, checksum, exclusividad y fuentes. No reproduce estado global CRT ni scheduler de Norn; [CI 202 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44932539848).
- [Intérprete SVRule](../../experiments/neurolab/c1_svrule_runtime.py) con snapshot previo, [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44932796473). [Dendrita integrada](../../experiments/neurolab/c1_synapse_integrated.py) con parámetros exactos de genes Decision/Concept, [CI 223 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44933002373).
- [g.2/g.3 pruebas](E09_G_MICRORED_RESULTADOS.md): cinco unidades, 20 semillas, WTA y concepto del tick anterior; g.3 `random_tie` 20/20 aprende y revierte con control congelado0.4925; `first_index` no acredita ventaja inicial. [CI 246 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44933734902), [JSON](resultados/run-44933734902/e09g3.json).
- G00-H y G09 global abiertas, no hay emulación completa ni mente autónoma.

### 2026-11-21 — NL-LOG-0019 (robustez E09g.4)
- [Pre-registro](E09_02G_04_ROBUSTEZ_PRE_REGISTRO.md), [resultados exactos](E09_02G_04_RESULTADO_ROBUSTEZ.md), [JSON por semilla](resultados/run-44934175507/e09g4.json), [CI 256 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44934175507).
- Contrabalanceado D0→D1 y D1→D0: sin ruido, delay1/3, **20/20 semillas** cumplen ambas puertas. Con noise10%: **16/20** y **17/20** semillas cumplen, NO aprobadas. Delay3 sin distractores no resuelve el problema de crédito causal E05.

### 2026-11-21 — NL-LOG-0020 (discriminación contextual E09g.5)
- [Pre-registro](E09_02G_05_DOS_CONCEPTOS_PRE_REGISTRO.md), seis unidades con dos conceptos predefinidos y ocho dendritas de decisión, secuencias balanceadas de contextos mezclados. [CI 269 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44934616857), runner científico **passed=false**.
- [Informe](E09_02G_05_RESULTADO_DOS_CONCEPTOS.md) y [JSON](resultados/run-44934616857/e09g5.json). Precisión steady neuronal 0.9671875 A y0.9302083 B; frozen0.51927/0.51146, blind0.49948/0.49688, **tabular 1.0/1.0**. Solo **12/20 semillas** cumplen ambos umbrales de0.90, contra criterio≥18/20. **No ajustar retrospectivamente.**
- g.5a analiza por tick 8 semillas fallidas (0,2,3,4,8,16,17,19), especialmente errores cerca de transiciones de contexto. **Post hoc exploratorio, no hipótesis confirmatoria**.
- Siguiente después del diagnóstico: preregistrar comparación de crédito causal diferido entre contextos; criterio de utilidad debe reconocer que el modelo tabular sencillo ya vence a la red. Sin cambios en `main` ni integración en motor Nilo.

### 2026-11-21 — NL-LOG-0021 (diagnóstico E09g.5a y ablación g.6)
- [g.5a, informe post hoc](E09_02G_05A_DIAGNOSTICO_POSTHOC.md): precisión en primer tick tras cambio de contexto 0 (A) y 0.0111 (B); hay errores persistentes más allá de la latencia de 1 tick. [CI g.5a](https://github.com/mxlzz/Nilo_public/actions/runs/44934965506).
- [g.6, preregistro](E09_02G_06_ABLACIONES_TEMPORALES_PRE_REGISTRO.md), [resultado](E09_02G_06_RESULTADO_ABLACIONES_TEMPORALES.md), [CI #44938181968](https://github.com/mxlzz/Nilo_public/actions/runs/44938181968): reset neuronal N o precarga de Concept W mejoran parcialmente; ambos juntos NW logran 1.0 en A/B para 20/20 semillas. **NW es un oráculo artificial al inicio de cada bloque, NO una mente que se autorregula.** Paridad con E09g.5 preservada.
- Resultado: diagnóstico validado como descripción del banco; no se modifica gate de g.5, no se implementa mecanismo interno.

### 2026-11-21 — NL-LOG-0022 (auditoría de crédito E09g.7)
- [Preregistro](E09_02G_07_CREDITO_CAUSAL_PRE_REGISTRO.md), [informe](E09_02G_07_RESULTADO_LEDGER_CAUSAL.md), [CI #44938471293](https://github.com/mxlzz/Nilo_public/actions/runs/44938471293): 10.240 ticks de entrenamiento, 10.200 pulsos comparables; **652 discrepancias** entre Concept de decisión previa y Concept de plasticidad actual, 331 con cambio STW. Se concentran en posición1 tras cambio contextual; LTW no cambia en esas observaciones.
- Los estados finales por semilla/fase del entrenamiento instrumentado coinciden exactamente con E09g.5. Resultado: descripción temporal verificada, NO demostración de que cada peso cambiara por ese pulso ni cierre de G05.

### 2026-11-21 — NL-LOG-0023 (E09g.8, resultado desfavorable según regla)
- [Pre-registro g.8](E09_02G_08_PULSOS_PAREADOS_PRE_REGISTRO.md), [informe](E09_02G_08_RESULTADO_PULSOS_PAREADOS.md), [CI #44938791056](https://github.com/mxlzz/Nilo_public/actions/runs/44938791056): control original C, supresión dirigida G en tick1 de cambio, sham S en tick2. Omisiones emparejadas 319 (A) y333 (B) por brazo. Steady B C0.9302083, G0.9614583, S0.9322917. Puerta G−S B≥0.03 **FALLA**: diferencia +0.0291667; precisión temprana G empeora. Conteos conjuntos C12/20, G16/20, S13/20.
- Resultado: experimento ejecutado sin errores de software, **hipótesis práctica NO aprobada**. No ajustar parámetros ni retroaprobarlo.

### 2026-11-21 — NL-LOG-0024 (E09g.9, replicación fuera de muestra)
- [Pre-registro de 80 semillas 20..99](E09_02G_09_REPLICACION_NUEVAS_SEMILLAS_PRE_REGISTRO.md), código reutiliza g.8 sin cambios; [reporte y limitaciones](E09_02G_09_RESULTADO_REPLICACION.md), [JSON original por semilla versionado](resultados/run-44939075550/e09g9.json), [CI #44939075550](https://github.com/mxlzz/Nilo_public/actions/runs/44939075550), commit ensayado `fb31ad91079f0454a4b8ac730455832bbdea44c3`, **success, 292 tests y 2 expectedFailure históricos**.
- Media `steady_B(G-S)` +0.0319010, IC bootstrap pareado95% [0.0161458, 0.0500], umbral prospectivo cumplido; `steady_A(G-S)` +0.0311198. 46/80 C, 60/80 G, 44/80 S superan≥0.90 conjuntamente. B: 35 mejores, 13 peores y32 iguales; mediana0. `early` G empeora frente a C/S.
- Resultado: **replicación positiva del efecto medio de un filtro de feedback EXTERNO**, no solución autónoma, no restauración del gate g.8 ni cierre G05/G09. Prioridad siguiente: g.10 evaluar si una memoria de procedencia verdaderamente interna justifica complejidad frente a tabla Q2×2.
- Estado: PR #103 permanece **draft** y branch de NeuroLab aislada; `main` y motor Nilo 0.7 intactos. No se redistribuyeron archivos originales del juego.

### 2026-11-21 — NL-LOG-0025 (g.10a: compuerta intrínseca mínima, factibilidad)
- [Preregistro antes del código](E09_02G_10A_GATE_INTERNO_PRE_REGISTRO.md), [implementación](../../experiments/neurolab/e09_intrinsic_gate.py), [tests](../../experiments/neurolab/tests/test_e09_intrinsic_gate.py). IG recibe únicamente estado neuronal, memoria del Concept anterior, entrada sensorial y químico pendiente: **no conoce bloques ni respuestas correctas**.
- [CI #44939579597](https://github.com/mxlzz/Nilo_public/actions/runs/44939579597), commit probado `91a67678aeaf1be8b8356ac4a0441aaa0db93afd`, **success: 300 tests, dos expectedFailure históricos**. [Informe](E09_02G_10A_RESULTADO_GATE_INTERNO.md), [JSON por semilla100..119](resultados/run-44939579597/e09g10a.json) permanente.
- **20/20 paridades IG=G exactas:** estados neurales/sinápticos finales, pulsos químicos pendientes, supresiones y holdout A/B. A328 supresiones, B331. Steady B C0.9229167 vs IG/G0.965625; C12/20 e IG/G17/20 superan ≥0.90 en ambas; early de IG empeora.
- **No** es crédito causal general, ni puerta G05/G09 aprobada, ni un mecanismo observado en el genoma/ejecutable C1. El baseline Q2×2 sigue siendo más eficaz en la tarea de dos señales.
- **Siguiente estudio:** no seguir ajustando esta tarea simple; preregistrar test con distractores y feedback1–3 ticks y baseline de memoria causal. `main`, Nilo y PR draft sin merge.

### 2026-11-21 — NL-LOG-0026 (g.10b: recompensa diferida y distractores)
- [Preregistro](E09_02G_10B_DEMORA_DISTRACTORES_PRE_REGISTRO.md), [código](../../experiments/neurolab/e09_delayed_distractors_protocol.py), [resultado](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md), [JSON por semilla](resultados/run-44942700990/e09g10b.json), [CI 308 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44942700990), commit ensayado `738e002a85b4346eb44af0b83ebf889b5d6b8345`, success.
- 40 semillas120..159, dos fases con 60 entrenamiento/36 holdout, 4 ticks target, 1–3 distractores y feedback en el tick siguiente. C16/40 e IG6/40 cumplen ≥0.90 ambas fases vs Q40/40 y F0/40. **C/IG gates fallidas**, Q recibe procedencia explícita privilegiada. IG suprime exactamente 800/2400 pulsos por fase, pero su rendimiento cae. No recalibrar retrospectivamente.
- El criterio opcional de parada forzosa (ventaja media Q≥+0.15) NO se activó: +0.1316; se recomienda detener tunings por el costo de oportunidad, no falsear esa puerta.

### 2026-11-21 — NL-LOG-0027 (g.10c: susceptibilidad ya existe)
- [Preregistro post hoc explícito](E09_02G_10C_SUSCEPTIBILIDAD_PRE_REGISTRO.md), [auditoría](../../experiments/neurolab/e09_eligibility_audit.py), [informe](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md), [resumen JSON](resultados/run-44943178871/e09g10c_summary.json), [CI 313 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44943178871), commit `7ec6fc0e0a8bef52886962dddad64350da0885a6`, success.
- 4800 eventos en 40 semillas, paridad exacta g.10b. Susceptibilidad de dendrita de contexto/acción originales >0 en el 100% de las llegadas. Frente a pulso ZERO en el mismo estado, con 3 distractores el efecto del pulso en STW objetivo disminuye y en distractor aumenta, comparado con 1 distractor. No significa atribución correcta exclusiva ni demuestra causa futura.
- [Evaluación de alternativas E09g.11](E09_02G_11_ALTERNATIVAS_Y_PRIORIDAD.md): C1 ya tiene elegibilidad local; tabla Q usa información causal privilegiada; TD(lambda) existe pero no se justifica agregar otra traza aún. Próxima prioridad: reloj/bioquímica C1 históricos E09h.1. Binario original no accesible en los archivos de este proyecto/chats actuales para ampliar inspección estática; no pedir hasta que se precise.
- PR #103 permanece draft, main/Nilo no modificados.

### 2026-11-21 — NL-LOG-0028 (E09h.1, orden de actualización histórico)
- Los originales EXE 387072 bytes SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7` y GEN10001 bytes SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4` fueron recibidos nuevamente y coincidieron con E09f/E00, inspeccionados localmente **sin subirlos a GitHub**.
- [Preregistro](E09_H_01_ORDEN_CEREBRO_QUIMICA_PRE_REGISTRO.md), [verificador](../../experiments/neurolab/e09_historical_timing_audit.py), [JSON de evidencia binaria local](resultados/e09h1_inspeccion_estatica_original.json), [informe](E09_H_01_RESULTADO_ORDEN_CEREBRO_QUIMICA.md), [CI 318 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44944783092) success, 2 expectedFailure históricos.
- 12 firmas de instrucción y 10 destinos E8 comprobados en EXE. Ruta regular criatura: cerebro→bioquímica→conducta; ruta alternativa invierte cerebro/química. Lóbulos1..5,0,6+ y etapas químicas emisor→receptor→reacción→decaimiento. **Orden estático verificado; frecuencia real del scheduler no.**
- Resultado: E09h.1 completada **solo** como verificación estática delimitada; G00-H/G05/G09 sin cerrar.

### 2026-11-21 — NL-LOG-0029 (E09h.2, cinética de reacciones C1)
- [Preregistro](E09_H_02_REACCIONES_QUIMICAS_PRE_REGISTRO.md), [código](../../experiments/neurolab/e09_historical_reaction_math.py), [tests](../../experiments/neurolab/tests/test_e09_historical_reaction_math.py), [informe](E09_H_02_RESULTADO_REACCIONES_QUIMICAS.md), [evidencia original](resultados/e09h2_reacciones_genoma_original.json), [CI325 success](https://github.com/mxlzz/Nilo_public/actions/runs/44945152541), 2 expectedFailure.
- 58 reacciones originales. Se verificó que el loader x86 reubica tasa de último byte serializado a offset+4 del registro runtime. Capacidad según reactivos, extent=capacidad-decay(capacidad,tasa,tick), consumo/generación saturados. **Orden de reacciones en el mismo tick importa:** gen71→111 genera Reinforcement51 y Echo54 desde Reward49 generado ese mismo tick; orden invertido no.
- Resultado: **aritmética de reacción aislada verificada con fixtures**, no bioquímica de Norn integrada.

### 2026-11-21 — NL-LOG-0030 (E09h.3, recepción química → locus)
- [Preregistro original](E09_H_03_RECEPTORES_QUIMICOS_PRE_REGISTRO.md), [código](../../experiments/neurolab/e09_historical_receptor.py), [tests](../../experiments/neurolab/tests/test_e09_historical_receptor.py), [resultado](E09_H_03_RESULTADO_RECEPTORES.md), [JSON original](resultados/e09h3_receptores_genoma_original.json), [CI success332 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44945435224), dos expectedFailure.
- 43 receptores originales y seis cerebrales, incluido Reward49/Punishment50 de Decision. El efecto `(available*gain)>>8` produce para concentración12 y gain255 el byte11. **Errata**: prereg E09h.3 esperaba receptor126 output1 con pool52=5, pero el resultado correcto es0; [CI inicial fallida](https://github.com/mxlzz/Nilo_public/actions/runs/44945392755) detectó el error, se corrigió fixture sin alterar fórmula ni prereg.
- Resultado: etapa de transferencia de receptor verificada **sin probar aún que el locus esté correctamente vinculado a CHEM0..3**. Mantener E09h.4 como próximo paso, sin modificar Nilo ni fusionar PR#103.


### 2026-11-21 — NL-LOG-0031 (E09h.4, enlace de receptor a CHEM; PARCIAL)
- [Preregistro](E09_H_04_ENLACE_LOCI_PRE_REGISTRO.md) se guardó **antes** del código, commit `ed66c8ab482d3d55d342fd4a98671a784d82abb2`.
- Fuente [CDN/LCUS](https://lisdude.com/cdn/76.html) confirma receptor locus13–16 = CHEM0–3 por lóbulo; guía [C1 Brain](https://zenzoa.com/creatures/c1-brains.html) confirma operandos SVRule5–8 y carga de los cuatro CHEM de ese lóbulo.
- [Adaptador](../../experiments/neurolab/e09_historical_locus.py), [tests](../../experiments/neurolab/tests/test_e09_historical_locus.py), [resultado condicionado](E09_H_04_RESULTADO_ENLACE_LOCI.md), commit de tests `2ef85398502ff67b7a40f7106f6277394b989625`; [workflow](https://github.com/mxlzz/Nilo_public/actions/runs/44947076331) **success integral** (339 tests, 2 expectedFailure); únicamente pruebas de adaptador y regresión, no nuevos bytes de EXE.
- Oráculos del fixture CD h.3: Decision6 CHEM=(11,11,5,16), Concept8 CHEM=(0,0,0,0), con pool de ejemplo; controles de aislamiento, canales ausentes, duplicados y no mutación. Son verificaciones de **compatibilidad documental**, no memoria física C1.
- Acceso a binarios: Biblioteca localizó ambas copias originales por metadatos, pero falló la materialización de bytes. No se realizaron nuevas lecturas x86, y por eso la **puerta G-H4-X86 sigue abierta**. Siguiente tarea exacta: inspeccionar asignación de puntero receptor→lobe CHEM y su snapshot de SVRule cuando exista acceso real al ejecutable original.
- PR #103 sigue draft; main/Nilo 0.7/G00-H/G05/G09 intactos.


### 2026-11-21 — NL-LOG-0032 (E09h.4-X86, enlace verificado)
- Fuente directa: nueva copia del EXE enviada por usuario, 387.072 bytes, SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7; inspeccionado localmente en estático. No ejecutado ni subido.
- [Evidencia x86 original](resultados/e09h4_inspeccion_estatica_original.json), [verificador](../../experiments/neurolab/e09_historical_locus_audit.py), [informe](E09_H_04_RESULTADO_ENLACE_LOCI.md) y tests: 31 instrucciones, vtable del resolver en 0x43302C→0x4030E0; locus13..16→+0xC3..+0xC6 en lóbulo 0xC8; código de receptor escribe mediante puntero guardado y la SVRule lee esos bytes como opcodes5..8.
- Hallazgo adicional: loader inicializa destino con nominal en 0x421ACF. Se añadió función de nominales aislada y controles sobre los seis genes previamente archivados de h.3. Los genes originales no fueron reanexados en esta intervención; no afirmar relectura de GEN.
- [CI final #44947923270](https://github.com/mxlzz/Nilo_public/actions/runs/44947923270): **success, 348 tests, 2 expectedFailure históricos**. CI solo usa fixtures y código, sin exe original; las firmas reales fueron verificadas localmente.
- **G-H4-X86 validada en alcance estático, E09h.4 cerrada**; G00-H/G05/G09 pendientes; no hay cerebro integrado ni conducta real certificada. PR #103 draft, main y Nilo 0.7 sin cambios.
- Siguiente **E09h.5**: preregistro de emisores y vinculación a concentraciones, desde EXE original; luego implementación aislada si la evidencia lo permite. No ampliar redes ni extrapolar resultados g.10.


### 2026-11-21 — NL-LOG-0033 (E09h.5, emisores y errata preregistrada)
- [Preregistro H5](E09_H_05_EMISORES_PRE_REGISTRO.md) escrito antes de codificar. Inspección estática del mismo EXE original SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7: **32 firmas de instrucciones**, método virtual 0x4030E0, emisor kind1, loci1/2→lobe+0xC1/C2, escritura al pool y reset de fuente.
- [Auditor reejecutable](../../experiments/neurolab/e09_historical_emitter_audit.py), [fixture x86 derivado](resultados/e09h5_inspeccion_estatica_original.json), [función aislada](../../experiments/neurolab/e09_historical_emitter.py), [tests](../../experiments/neurolab/tests/test_e09_historical_emitter.py), [resultado](E09_H_05_RESULTADO_EMISORES.md).
- **Errata preservada:** el preregistro supuso que chemical0 no consumiría origen, pero las ramas x86 0x421EEF y 0x421F24 saltan igualmente a reset por flag1 tras superar filtros. Test demuestra consumo sin pool. No se corrigió el preregistro retroactivamente.
- [CI #44948424321](https://github.com/mxlzz/Nilo_public/actions/runs/44948424321) **success: 362 tests, 2 expectedFailure históricos**. CI sintético y análisis estático original local, sin binarios en GitHub.
- Tres genes cerebrales 123/124/125 provienen del mapa de GEN extraído E00 anterior, **no** de relectura de bytes GEN en este chat. Valor fuente80→emisión79 es un ejemplo artificial, no una lectura de Norn real.
- **G-H5-X86 + G-H5-MATH cerradas en alcance acotado; G-H5-GEN con procedencia documental E00 y sin revalidación directa nueva; G00-H/G05/G09 abiertas**. PR #103 draft, main y Nilo 0.7 sin cambios. Siguiente **E09h.6 scheduler y reloj, previo preregistro**.


### 2026-11-21 — NL-LOG-0034 (E09h.6a/b, flujo y reloj nominal)
- [Preregistro global](E09_H_06_SCHEDULER_PRE_REGISTRO.md) y [preregistro de timer](E09_H_06B_CADENCIA_PRE_REGISTRO.md) conservados; **ambos se escribieron antes de sus respectivos auditores**.
- **h.6a:** inspección del EXE original, SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7; **24 firmas x86 y 8 direct calls**. Rama Norn+0x2CBC separa ruta regular y alternativa; Norn+0x2CCC omite cerebro y conducta pero no química; contador Norn+0x2C20 compartido antes de incremento. Bucle mundial usa fases0..4 y stride4; index4,8,... aparece en más de una fase; observación estática, no diagnóstico de bug.
- [Informe h.6a](E09_H_06A_RESULTADO_FLUJO_SCHEDULER.md), [auditor](../../experiments/neurolab/e09_historical_scheduler_audit.py), [datos derivados](resultados/e09h6a_flujo_original.json).
- **h.6b:** en EXE original, **17 firmas + 7 llamadas + 6 campos MFC**; USER32.SetTimer ID1 de 90 ms en 0x411F63 y KillTimer en 0x411F7F, WM_TIMER 0x113→0x418960→world tick 0x4247B0. Otro SetTimer500ms en ventana distinta, NO confundir. [Informe h.6b](E09_H_06B_RESULTADO_CADENCIA.md), [auditor](../../experiments/neurolab/e09_historical_timer_audit.py), [fixture](resultados/e09h6b_cadencia_original.json).
- [CI #44949141624](https://github.com/mxlzz/Nilo_public/actions/runs/44949141624) **success integral: 374 tests, 2 expectedFailure históricos**. Los tests del auditor usan memoria/importaciones PE sintéticas; la verificación auténtica fue local sin publicar ni ejecutar juego.
- **Puertas:** G-H6-FLOW verificada solo en rutas directas; G-H6-CLOCK-NOMINAL verificada; **G-H6-CLOCK EFECTIVA / G00-H / G05 / G09 ABIERTAS**. No se ha medido un ritmo real de Norn. PR#103 permanece draft, main/Nilo 0.7 sin cambios.
- Próximo punto de decisión técnica: ¿es necesaria fidelidad temporal en segundos antes de montar tick de pruebas integrado, o alcanza tick lógico explícito sin afirmar equivalencia de C1? Si se exige fidelidad, ampliar trazas/medición en vez de extrapolar 90ms directamente.

### 2026-11-21 — NL-LOG-0035 (E09.02i-I1/I2/I1b; no nueva capacidad conductual)
- **Decisión metodológica N:** reloj lógico sin segundos para evaluar acoplamiento mínimo; no se altera G-H6-CLOCK efectiva. [Preregistro](E09_02I_INTEGRACION_QUIMICA_PRE_REGISTRO.md) commit b9c9c56e279f9bb442aaa09e5ac0b857f3ae4481.
- [I1](E09_02I_I1_I2_RESULTADOS.md): puente inmutable emisor→receptor→reacción; test con gen111 muestra que Reinforcement51 fabricado en reacción no llega a receptor hasta otra invocación; [CI success383 tests + 2 expectedFailure](https://github.com/mxlzz/Nilo_public/actions/runs/44951342148). No aprendizaje probado.
- [I2](E09_02I_I1_I2_RESULTADOS.md): seis unidades preexistentes acopladas unidireccionalmente a CHEM de Decision del tick previo, checkpoint conjunto reproducible, sin conexión inventada de winner-output a source loci, Concept CHEM trazado pero no consumido por plasticidad; [CI success391 + 2 expectedFailure](https://github.com/mxlzz/Nilo_public/actions/runs/44951467547).
- [I1b prereg](E09_02I_1B_POOL_DECAY_PRE_REGISTRO.md): bytes EXE originales SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7 verificaron **15 firmas x86 + call 0x4221ED→0x419E40**; bucle256 químico byte0/rate byte1, stride2. [Módulo y auditor](E09_02I_I1B_RESULTADO_POOL_DECAY.md), [CI401 success + 2 expectedFailure](https://github.com/mxlzz/Nilo_public/actions/runs/44951833784). Tasas genómicas de los 256 químicos NO recuperadas; módulo exige rates explícitos, tests sintéticos.
- **G-I1, G-I2, G-I1b-MATH/X86 cerradas solo técnicamente; G-I1b-RATES, G-H6-CLOCK efectiva, G00-H, G05, G09 ABIERTAS.** Ningún benchmark conductual I3 ejecutado, no afirmar victoria de aprendizaje. PR#103 draft, main/Nilo0.7 intactos.
- Próxima unidad preregistrada: I3 benchmark sobre tasas sintéticas explícitas con controles y no-fidelidad histórica, sin nuevas neuronas ni ajuste de pesos. Antes del experimento fijar cohortes, dosis, rates, fuentes y pruebas negativas.


### 2026-11-21 — NL-LOG-0036 (I3 no supera criterio, I3a en curso)
- [Preregistro I3](E09_02I_I3_BENCHMARK_PRE_REGISTRO.md) anterior al runner. 20 semillas nuevas200..219; 60 entrenamiento +36 holdout por fase A/B con reversión, retardo1–3, M química, F congelado químico, C pulsos directos no equivalentes, Q tabla con procedencia privilegiada.
- [Run I3 #44952276187](https://github.com/mxlzz/Nilo_public/actions/runs/44952276187) terminó success de **software**, NO la hipótesis. Media M primera0.513889 e invertida0.534722; F0.5125/0.534722; C0.890278/0.845833; Q1/1. M−F=0.00069444; 0/20 M≥.90 en ambas fases. **G-I3 científica FALLIDA**, conservar [informe negativo](E09_02I_I3_RESULTADO_NEGATIVO.md).
- [Resumen JSON](resultados/e09i3_resultado_resumen.json), artefacto I3 ID14725468833 con resultados completos por semilla y 90 días de retención, enlace al run. M tuvo 71 y75 decisiones objetivo no emitidas en entrenamiento de fases A/B respectivamente; no hubo concentraciones255 en los puntos finales de ensayo medidos (Reward/Punishment max25, Reinforcement max109). No inferir causalidad desde esto.
- La tasa40 en 256 químicos y dosis80 fueron **sintéticas y preregistradas**, no tasas GEN. No hubo ajuste posterior. Las referencias C y Q no igualan temporalidad o privilegios de información con M. No afirmar que C1 histórico fracasa.
- [I3a preregistrado posthoc](E09_02I_I3A_DIAGNOSTICO_POSTHOC_PRE_REGISTRO.md) para conteos read-only de susceptibilidad/CHEM/reinforcement_effect/STW, replay de mismos estados sin alterar neuronal; **todavía no declarar conclusión I3a** sin CI y JSON.
- Decisión: priorizar mecanismo y atribución antes de tunear hiperparámetros o sumar neuronas. G00-H/G05/G09 y tasas históricas abiertas. PR#103 draft, main/Nilo0.7 intactos.
