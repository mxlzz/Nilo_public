# NR01.03-B — preregistro de comprobación técnica de bibliotecas existentes (sin ensayo científico)

**22/11/2026 · PRE-IMPLEMENTACIÓN.** Antes de adoptar un paquete como encoder: instalar versiones fijadas, comprobar interfaz de entrenamiento incremental, transformación de datos, lectura sin aprendizaje y número de categorías medibles. **No usar ninguna semilla científica**, ni datos de las familias A/B, ni respuestas correctas del evaluador.

**Candidatos y origen oficial:** `artlib==0.1.12` ([documentación v0.1.12](https://adaptiveresonancelib.readthedocs.io/en/latest/); [proyecto PyPI](https://pypi.org/project/artlib/)), `scikit-learn==1.9.1` ([MiniBatchKMeans.partial_fit](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MiniBatchKMeans.html)); `numpy` dependencia de ambos. Python 3.11 en runner GitHub Actions Ubuntu, biblioteca de origen público. Se probarán con **cuatro vectores fijos ficticios**, no prototipos/semillas de `nr01_worlds`.

**Prueba ART:** construir `FuzzyART(rho=.8,alpha=.001,beta=1.0)`, fijar límites de datos `np.zeros(16),np.ones(16)`, aplicar `prepare_data`, verificar complemento 32D, crear categorías mediante `partial_fit` o `fit`; después obtener `predict` en ese mismo espacio y demostrar igualdad exacta de pesos de categoría, número de categorías y contadores antes/después de predecir (sin feedback). El smoke verifica APIS, **no** valor de los clusters. Los datos del test no deben mezclar clases latentes reales.

**Prueba KMeans:** `MiniBatchKMeans(n_clusters=2,batch_size=4,random_state=42)`, `partial_fit` cuatro filas16D, `predict` y verificar centros/contador inalterados después de predecir. Comprobar número y dimensión de categorías/centroides.

**Criterio:** ambas bibliotecas importan con versiones fijadas, entrenan sin recibir etiquetas, producen IDs y mantienen estado idéntico en `predict`; si falla, **no modificar el benchmark NR01** ni afirmar capacidad, inspeccionar API y registrar adenda antes de cambiar código. No hay ajuste de hiperparámetros científicos ni consumo de confirmación.

**Resultado permitido:** `NR01.03-B SOFTWARE PASS`, o problema de compatibilidad delimitado. Ninguna de las dos situaciones valida G09/NR01 capacidad científica.
