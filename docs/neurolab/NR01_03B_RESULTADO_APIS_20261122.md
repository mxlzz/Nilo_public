# NR01.03-B — verificación de compatibilidad y lectura sin actualización

**22/11/2026 · resultado software, NO experimento científico.** [Pre-registro anterior al workflow](NR01_03B_PRE_REGISTRO_APIS.md), [GitHub Actions run #45044290040](https://github.com/mxlzz/Nilo_public/actions/runs/45044290040), SHA de código `de94d5e7e5f60e22d39e7734b9afb9352b84f56f`. Estado **SUCCESS**, job `ARTlib and MiniBatchKMeans no-label/read-only API contract`, salida `API_SMOKE_PASS`.

## Qué se comprobó realmente

- Entorno GitHub Actions: Ubuntu, Python3.11, `artlib==0.1.12`, `scikit-learn==1.9.1`. `pip install` terminó sin errores y generó wheel de ARTlib compatible.
- Solo **cuatro vectores ficticios de 16 dimensiones**, sin importar generador NR01, factores latentes ni semillas de desarrollo/confirmación.
- `FuzzyART(rho=.8,alpha=.001,beta=1)`: normalización con límites [0,1] fijados por código y complemento de 16→32 dimensiones, `partial_fit` sin etiquetas, produjo **2 categorías** en el ejemplo. `predict` devolvió etiquetas y **no modificó pesos ni número de categorías**.
- `MiniBatchKMeans(n_clusters=2,batch_size=4,random_state=42)`: `partial_fit` sin etiquetas, obtuvo 2 centros×16D; `predict` devolvió etiquetas **sin modificar centroides ni contador de pasos**.
- Suceso concreto en logs: `{"ART":{"clusters":2,"prediction_did_not_mutate_weights":true,"prepared_features":32},"KMeans":{"clusters":2,"features":16,"prediction_did_not_mutate_centroids":true},"models_trained_on_worlds":false,"protocol":"NR01.03-B-software-v1","python_libs":{"artlib":"0.1.12","scikit_learn":"1.9.1"},"science_seeds_used":false,"status":"API_SMOKE_PASS"}`.

## Interpretación correcta

**NR01.03-B SOFTWARE: APROBADA para APIs elementales.** Las bibliotecas existen, son instalables en el runner y permiten separar adquisición de categorías y lectura posterior sin modificación **en el pequeño caso ensayado**. Esto no prueba límite de categorías16, estabilidad de orden, costo en1200 ejemplos, posibilidad de serialización exacta, resistencia a ruido, transferencia, retención, ni mejora sobre controles simples.

**Siguiente dependencia:** especificar en preregistro el decoder, tratamiento de categorías nacientes/fuera de presupuesto y baseline de aprendizaje supervisado crudo con acceso comparable a información; integrar únicamente pruebas técnicas con semillas toy antes de una cohorte científica. No retroajustar `rho`, `K`, tasas ni generador en función de resultados científicos. Semillas NR01 23000..23019 / 24000..24019, históricas1400..1419 **NO usadas**. PR#103 draft; Nilo0.7 y `main` sin cambios.
