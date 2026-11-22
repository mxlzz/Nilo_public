# E09.02i–I3c.5a — resultado de crédito diferido (observación mecanística)

**21/11/2026 — Resultado de cohorte nueva, preregistrada antes del código.** [Preregistro](E09_02I_I3C5A_CREDITO_DIFERIDO_PRE_REGISTRO.md) · [runner](../../experiments/neurolab/e09_i3c5a_credit_forks.py) · [tests](../../experiments/neurolab/tests/test_e09_i3c5a_credit_forks.py) · [CI inicial 44963707697](https://github.com/mxlzz/Nilo_public/actions/runs/44963707697) · [CI con desglose 44963833232](https://github.com/mxlzz/Nilo_public/actions/runs/44963833232) **SUCCESS (5/5 tests)**, archivo íntegro `neurolab-i3c5a-credit-forks`, artefacto ID **14730781039** (retención temporal). Ningún cambio a genes, motor estable, dosis ni tasa.

## Experimento ejecutado

Se evaluaron **20 semillas nuevas (1200..1219)**, objetivos 0/1 y contingencias A/B: **80 troncos neuronales idénticos antes del feedback** (tick124), clonados en cinco ramas cada uno: control N sin pulso y D0/D1/D2/D3 con precursor en retrasos0/1/2/3 ticks. Total **400 ramas**. Las decisiones y el contexto objetivo se fijaron *antes* de la bifurcación; el evaluador externo determina si el precursor corresponde a acierto o error. Se observaron **40 elecciones inicialmente correctas, 40 erróneas, ninguna ausencia de acción**. Los ensayos sin acción están cubiertos por tests, pero no por eventos naturales de esta cohorte.

El observador de ocho sinapsis utiliza `update_c1_synapse` y exige transición numérica idéntica a `C1ContextBrain.step` en cada tick; registra distribución por fuente objetivo/distractor y acción, susceptibilidad, STW/LTW, fuerza, CHEM y lectura final sin aprendizaje. No introduce verdad ni origen causal al cerebro. Reloj hasta tick256, snapshots en128/256. Reporte completo por tick/semilla en artefacto Actions, no en el repositorio por volumen.

## Resultados preregistrados

**Fracción media de refuerzo atribuible al origen del contexto objetivo** (diferencia positiva de efecto sináptico frente al control N; denominadores positivos en 80/80 ramas por retraso):

- D0 **0,56731**, D1 **0,49146**, D2 **0,43940**, D3 **0,39946**.
- Contraste pareado por semilla D0−D1: **+0,07585** [IC bootstrap95% **+0,04544;+0,10542**].
- D0−D2: **+0,12791** [IC95% **+0,09691;+0,15960**].
- D0−D3: **+0,16785** [IC95% **+0,13609;+0,20074**].
- La fracción que recae específicamente en origen objetivo **y dueño de la acción previa** fue D0 **0,35356**, D1 **0,31006**, D2 **0,28086**, D3 **0,26116**. Es una clasificación experimental exógena, no una selección causal aprendida por el cerebro.

Los cinco brazos preservaron la simetría esperada de dosis y exposición integrada media: para D0..D3, AUC media CHEM0 y CHEM1 **20,5 cada una**; N0. **Igual AUC agregada no significa exposición por tick igual**, pues la inyección se desplaza temporalmente y modifica la coincidencia con susceptibilidad/activación. No se aisló el efecto de timing del patrón químico instantáneo.

**Conducta y retención negativas:** lectura sin aprendizaje al terminar: precisión **0,50 para N, D0, D1, D2 y D3**. Diferencia absoluta media de LTW contra N en conexiones de origen objetivo a tick256 **0 en todos los brazos**. Para los cinco modos, **8/8 sinapsis presentaban strength0 en tick256** en cada evaluación (promedio 8): resultado circunscrito a este ensayo de exposición única y larga espera, NO diagnóstico universal de C1. Diferencia absoluta de STW objetivo en tick128: D0=1,15; D1=2,55; D2/D3=0 (pulso aún no consolidado en la ventana medida). Ninguna evidencia de mejora sostenida.

## Interpretación / puertas

- **G-I3c5a-SOFTWARE** aprobada: cinco tests, 20 hashes SHA por semilla y artefactos completos; 80/400 unidades, 80 pulsos por D0..D3, 0 en N, igualdad de testigo sináptico y continuidad temporal.
- **G-I3c5a-CREDIT**: existe distribución temporal mensurable de efecto hacia fuente objetivo, decreciente con el retardo en este modelo sintético; la magnitud *no* acredita una causalidad aprendida.
- **G-I3c5a-LTW**: retención negativa en tick256, fuerza0; no identificar incrementos numéricos transitorios con memoria funcional.
- **G05, G09 y G00-H ABIERTAS**. La exactitud 0,50 impide interpretar este resultado como aprendizaje; no tunear ni ampliar red con esta cohorte. Ver [I3c.5b](E09_02I_I3C5B_RESULTADO_STRENGTH0.md) antes de diseñar intervención con fuerza y pruebas conductuales confirmatorias.

**Límite de alcance:** ocho contactos fijos de la línea N; puente metabólico con tasas40/dosis80 sintéticas, no emulación validada del Norn completo; sin migración deliberadamente para separar crédito temporal. La cohorte1200..1219 queda consumida y no puede servir como validación independiente de una variante elegida a posteriori.


## Anexo de auditoría retrospectiva del artefacto íntegro (posterior al resultado)

Se descargó el ZIP original del CI **44963833232**, artefacto ID **14730781039**, y se inspeccionaron **los 52.800 registros por tick** de las 400 ramas (132 ticks por rama). **En el primer frame posfeedback (tick125), las ocho dendritas tenían strength=0 en el 100% de las ramas**; por identidad del tronco, todas comenzaban el bifurcado en tick124 con los ocho slots agotados. Esto no estaba detectado en el preregistro original y se informa como **limitación metodológica post hoc**, sin cambiar los resultados numéricos.

- En el control N, los 10.560 frames mantuvieron siempre los ocho slots agotados.
- En D0/D1/D2/D3 hubo transiciones transitorias de fuerza positiva después del pulso: frames con menos de ocho agotadas, respectivamente **270 / 650 / 0 / 750** de 10.560 por modo. Al tick256, **todos** tenían fuerza0; la lectura final siguió al azar.
- Es incorrecto interpretar el contraste de fracciones D0 vs D3 como aprendizaje sobre una red inicialmente consolidada. Representa asignación numérica temporal bajo **condiciones de agotamiento inicial**; algunas ramas muestran recuperación transitoria de fuerza sin retención final. El posible mecanismo histórico de pesos sobre fuerza0 se investigó por separado en [I3c.5b-H](E09_02I_I3C5B_H_RESULTADO_X86.md).

**Consecuencia:** conservar la observación (no es un fallo de ejecución) pero no usarla como prueba ni siquiera indicio suficiente de aprendizaje conductual. Investigar por qué el warmup lleva a fuerza0 antes de un futuro experimento confirmatorio. Ya se preregistró la auditoría [I3c.5c](E09_02I_I3C5C_DISPONIBILIDAD_TRONCO_PRE_REGISTRO.md) sin alterar el cerebro. G05/G09 permanecen abiertas.
