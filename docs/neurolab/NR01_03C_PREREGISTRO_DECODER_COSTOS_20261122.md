> **RECTIFICACIÓN DE TRAZABILIDAD · 22/11/2026:** este archivo se creó en `fb98fe8c` **después** del preregistro canónico [NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md](NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md) (commit `7d5b1344`) y **después** de comenzar el código `nr01_decoder.py` (commit `0340c779`). Por tanto **NO es un preregistro previo al código y NO debe usarse como especificación experimental**. Conservamos el contenido únicamente como propuesta alternativa histórica no aprobada. Sus reglas incompatibles (eta 0.5 frente a 0.25, inversión del signo D0/D1, KMeans lotes K/seed19537 frente a lotes32/seed42, kNN32/tie reciente frente a kNN16/tie antiguo) fueron detectadas antes de ejecutar cohortes; **rige exclusivamente el contrato anterior**. No borrar para preservar auditoría.

# NR01.03-C — contrato congelado de interfaz, decodificación y costo (pre-run)

**22/11/2026 · protocolo anterior a la implementación y a cualquier cohorte NR01.** Depende de [NR01.02](NR01_02_PREREGISTRO_DESAFIO_20261122.md), [contrato del generador](NR01_02A_CONTRATO_GENERADOR_PRECODIGO.md) y [smoke de APIs](NR01_03B_RESULTADO_APIS_20261122.md). Objetivo: comparar **representaciones adquiridas sin supervisión** contra soluciones simples, sin privilegios de información ni ajustes oportunistas. Este documento **no es un resultado** y no autoriza consumir semillas 24000..24019.

## 1. Auditoría previa de alineación

- **Pregunta científica:** ¿la representación no supervisada aporta transferencia tras 32 recompensas, en combinaciones retenidas, con costo defendible?
- **Alternativas existentes primero:** ARTlib `0.1.12` (candidato), MiniBatchKMeans de scikit-learn `1.9.1` (control aprendido); controles de entrada cruda lineal y kNN, **sin motor neuronal nuevo**.
- **Control refutador:** si el clasificador crudo, kNN o KMeans iguala o supera ART con menos costo, no hay mérito demostrado para ART.
- **Alcance:** solo `experiments/neurolab/nr01_*`, documentación y tests. No modificar `main`, Nilo 0.7, Creatures, mundo, cuerpo ni LLM.
- **Orden:** congelar reglas aquí → tests técnicos con semillas ficticias 0/1/42 → CI → cohorte de desarrollo 23000..23019 → si hay señal, congelar selección y ejecutar una sola confirmación 24000..24019.

## 2. Superficies públicas y exclusión de información

`observe_unlabelled(x: tuple[float,...])` recibe exactamente 16 reales dentro de [0,1], sin labels, IDs ni premios. El entrenamiento no supervisado ve las mismas 1.200 observaciones **en el mismo orden** por mundo para ART y KMeans; los baselines raw también pueden observar esa cinta, pero no reciben información derivada de latentes. El evaluador privado crea `EvaluatorCase(observation, latent)`, entrega **solo** `case.observation` y calcula `reward` después de `choose`. Ningún adaptador importa `target_for_evaluator` ni recibe `EvaluatorCase`, etapa, familia, mundo, semilla generativa o solución.

`freeze_encoder()` impide todo `partial_fit`, `fit`, creación de categoría y mutación posterior. `encode_read_only(x)` devuelve un **ID entero** de categoría (ART y KMeans) o el vector raw (control), usando `predict` solo en modelos ya entrenados. Nunca actualizar durante downstream o test. Si `predict` o normalización cambia estado, **bloquear brazo antes de cohorte**; las pruebas de API sintética no garantizan eso para datos reales.

La representación categórica es **one-hot sobre K categorías en el mismo orden de índice de la librería**. No hay acceso a centroides, distancias, grados de membresía, prototipos ni otros valores para el decoder. Para ART, complemento de entrada 16→32 mediante `prepare_data` con límites [0,1] fijos y mismos `rho=.60,.80,.90`, `alpha=.001`, `beta=1` del preregistro. Para KMeans, `K=4,8,16`, `partial_fit` en orden con lote de arranque de K observaciones y posteriormente lotes consecutivos de K (no reordenar), `random_state=19537` fijo, `n_init=1`, inicialización `k-means++`; verificar esas firmas en un smoke sin cohortes antes de ejecución.

**Capacidad:** KMeans tiene K fijo ≤16; ART no puede exceder 16 categorías. Si crea una decimoséptima durante adquisición: registrar **fuera de presupuesto**, conservar conteo y costo, excluir de candidatos elegibles para selección, sin truncar ni cambiar `rho` a posteriori. La adquisición sigue **sin recompensas**. La cantidad de categorías al congelar determina dimensión del decoder (no se filtra etiqueta).

## 3. Decoder común y regla de acción/actualización

Decoder `D-v1` para **raw 16D**, **ART one-hot** y **KMeans one-hot**. Estado: vector de coeficientes `w` de longitud `d+1`, inicializado exactamente en cero; la última entrada de `phi` es sesgo fijo 1. La fuente `phi` para raw son los **16 valores x originales** sin selección de canales, escalado adicional ni preprocesamiento aprendido. Para clusters, `phi` es un one-hot de largo K. Se agrega sesgo 1 a ambos. Mismo código y paso `eta=0.5` para todos, sin regularización ni decaimiento.

`p = sigmoid(sum(w_j * phi_j))` con logit acotado solo para estabilidad a [-20,20]. `choose` selecciona D0 cuando `p>=0.5`, D1 en otro caso; empate determinista D0 para todos. Se registra predicción antes del refuerzo. **Después** de `reward∈{-1,+1}`, la acción binaria correcta inferible es `correct_action = chosen` si premio+1, o la contraria si premio−1. Definir `y=1` si `correct_action=D0`, 0 en otro caso; ejecutar `w_j ← w_j + eta*(y-p)*phi_j`, usando la probabilidad y features que se emplearon en esa decisión. El brazo nunca recibe la etiqueta latente: solo la acción que escogió y su recompensa, información **idéntica para todos**. Solo entrenamiento online, sin iteraciones extra con cada ejemplo.

El baseline **kNN-32** no usa D-v1 porque su mecanismo es memoria de ejemplos etiquetados por consecuencia, deliberadamente simple. Guarda como máximo las **32 últimas** parejas completas `(x,correct_action)` derivadas de su propio feedback. Antes de su primer feedback: D0. En consulta: 1 vecino por distancia euclidiana cuadrática sobre los 16 valores crudos; empate = ejemplo **más reciente**. No inserta datos de test ni ejemplos sin feedback. Se evalúa explícitamente como baseline de clase diferente, y su costo incluye la memoria completa. No afirmar igualdad de parámetros entre categorías y kNN.

## 4. Igualdad de presupuesto y cronología

Por cada mundo de desarrollo: misma cinta de 1.200 observaciones para ART y KMeans; **ningún premio** en adquisición. Todos los brazos tienen acceso a los mismos vectores raw posteriores, en el mismo orden, y al mismo régimen de feedback, siempre calculado en el evaluador luego de su decisión. El premiado de un brazo depende de su acción, pero la acción correcta inferida es la misma (dos acciones, premio binario). Nunca entrenar un clasificador con etiquetas antes de elegir.

**Familia A:** un único encoder congelado; decoder/memoria inician vacíos, reciben secuencialmente **64** eventos de feedback de la tarea original, luego **64** eventos de inversión **sin reset** del decoder/memoria. Evaluar en checkpoints 8,16,32,64 de cada fase sobre la misma cinta test sin premio, sin actualización, sin exposición de aciertos al aprendiz. El punto primario original A es checkpoint32; el de inversión es 32 **después de 64 del tramo original**.

**Familia B:** un único encoder congelado y **dos decoders/memorias nuevos independientes**, uno B1 y otro B2, con sus respectivas cintas de 64 feedback. Checkpoints 8,16,32,64 para cada tarea con test congelado sin premio. Punto primario: B1-32 y B2-32. El evaluador conserva sus propias métricas; **no** entrega correctitud/test al aprendiz.

La configuración de hiperparámetros se decide solo con mundos 23000..23019, nunca confirmación. Elige según métricas preregistradas, reporta **todo** el grid (ART rho 3, KMeans K 3) sin escoger semillas convenientes. Primario comparar con el **mejor baseline simple seleccionado en desarrollo**, incluyendo lineal raw y kNN; KMeans informar por separado.

## 5. Controles negativos y costos

- Negativo: permutar determinísticamente etiquetas de **test diagnóstico** por mundo/tarea conservando márgenes; usar RNG separado del evaluador. El target permutado **no** afecta recompensa durante entrenamiento ni retorna al modelo. Informar expectativa por mayoría: A .50; B1/B2 2/3, no interpretar >.50 en B como éxito.
- Ablación: mismo encoder de clase e inicialización sin llamar aprendizaje no supervisado, si la API no permite predecir en estado vacío registrar fallo de contrato y no simular una categoría con información extra. Opción válida: encoder con prototipos inicializados de datos sin entrenar solo si se define explícitamente **antes** de utilizar cohortes; la ablación principal es la diferencia entrenado vs sin entrenamiento de representación.
- Información: guardar SHA256 de cinta de observaciones por familia, mundo y fase; **no** hash de latentes como sustituto de prueba de identidad de entrada. Tests instrumentados verifican misma cinta a cada brazo y que solo salen `tuple[float,...]`, acción y recompensa.
- Costo: medir `time.perf_counter_ns` separadamente para adquisición/decisiones/actualizaciones/test y reportar hardware+versiones; medir `len(pickle.dumps(state, protocol=5))` del **estado íntegro reconstruible** encoder+decoder (o memoria kNN) incluyendo normalización, categorías, centroides, caches de ejecución necesarios. Es *tamaño serializado*, no RAM residente; no llamar a ese número RSS. Registrar también bytes reales de arrays y número de parámetros cuando sea posible. Incluir fallos/fuera-de-presupuesto, no premiar modelos que omitan sus pesos.
- Auditoría de read-only: serializar/hash estado antes/después de cada tanda de test; ningún cambio admitido.

## 6. Salidas y puertas

Antes de ejecutar siquiera **desarrollo**: tests toy de inferencia de etiqueta posterior, igualdad de exposición, decisión sin recompensa, `choose/encode` read-only, kNN FIFO, costeo con decoder, y excepción por categoría>16. Luego CI verde y especificación sin contradicciones. Todos los fallos permanecen visibles.

**Éxito científico NO definido aquí:** permanece vigente NR01.02 (ventaja de ≥5pp en confirmación y bootstrap pareado >0 frente a mejor baseline, control causal/ablación y costos, sin garantía de generalización entre familias). No reinterpretar CI software como aprendizaje. Ninguna modificación de Nilo, fusión del PR draft ni uso de confirmación en esta unidad.

**Unidad siguiente:** NR01.03-C1 — implementar solo D-v1, kNN-32 y pruebas de contrato *toy*; NR01.03-C2 — adaptadores ART/KMeans con read-only y budget en tests toy; NR01.03-D — auditoría de harness antes de cohortes.
