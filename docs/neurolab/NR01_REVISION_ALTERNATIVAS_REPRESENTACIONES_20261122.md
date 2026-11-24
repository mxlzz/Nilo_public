# NeuroLab NR01 — revisión comparativa de soluciones existentes para aprender representaciones

**22/11/2026 · INVESTIGACIÓN DOCUMENTAL; NO implementación ni benchmark.** Esta línea **se inaugura después del cierre limitado E09**, no modifica G00–G09 ni reemplaza lo observado. Pregunta: **¿puede un sistema pequeño adquirir, reutilizar y preservar representaciones útiles a partir de experiencia, sin que el diseñador le precodifique todas las categorías, y con ventaja práctica frente a soluciones simples que reciben la misma información?**

**Método de búsqueda:** papers primarios, documentación oficial y repositorios/páginas de paquetes visitables al 22/11/2026. Es revisión **selectiva orientada a decisión**, no revisión sistemática completa con protocolo PRISMA. Se recopilaron familias representativas (no se promete haber examinado todas las implementaciones); distinguir capacidades declaradas en documentación de resultados que debamos medir nosotros. No se ha validado instalación, rendimiento ni compatibilidad práctica en el entorno del laboratorio.

## 1. Por qué esta pregunta y no otra

[E09.05 TAB2](E09_05_TAB2_E03_RESULTADO.md): E03 episodios reset son algebraicamente una tabla 2×2 de pesos. [E09.05 TAB1](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md): E06 depende de detectores de parejas **ya elegidas** y es exactamente una tabla 4×2 con esa representación; [E07](E09_EVIDENCE_INDEX.md) empata a LRU. Por tanto no es valioso reimplementar asociación trivial o añadir STW/LTW antes de descubrir una necesidad.

**Advertencia conceptual:** en cualquier dominio finito una tabla suficientemente grande puede representar una función. La hipótesis NR01 **no** es «ser matemáticamente imposible usar tablas». Es que un mecanismo que **aprende su representación** podría obtener mejor **generalización por dato, economía de estado o adaptación** que una tabla/vecindario de capacidad comparable sin representación precodificada. La hipótesis debe sobrevivir a controles justos, no depender de un problema elegido para favorecer redes.

La creación de categorías por clustering **no demuestra por sí misma utilidad cognitiva**: hace falta prueba downstream de transferencia/reuso, sensibilidad al ruido y retención ante nuevas experiencias.

## 2. Familias y soluciones contrastadas

### A. Controles simples — necesarios, no candidatos a eliminar

**A1. Tabla literal, frecuencias, prototipos de entradas completas y 1-NN con presupuesto de ejemplos.** Coste conceptual mínimo; excelente control para detectar fugas. Limitaciones previsibles: memoriza combinaciones individuales, no garantiza invariancias con apariencias inéditas. **No dar acceso a etiquetas latentes ni reglas correctas**. Un baseline que sepa qué factores descartar es *oráculo informado*, no comparación justa.

**A2. River: aprendizaje online supervisado simple y clusterizadores.** [River documentación/repositorio](https://github.com/online-ml/river), [publicación en JMLR](https://jmlr.org/papers/v22/20-1380.html), licencia BSD-3-Clause [LICENSE](https://github.com/online-ml/river/blob/main/LICENSE), versión [0.27.0 en PyPI (13/11/2026)](https://pypi.org/project/river/0.27.0/). Admite flujo `learn_one`, modelos incrementales y [DBSTREAM](https://github.com/online-ml/river/blob/main/river/cluster/dbstream.py) para agrupamiento de densidad online. **Útil:** baselines de aprendizaje incremental y clusterización sin nuevas implementaciones de motor. **Límite:** no hay garantía de que un cluster coincida con un concepto que sirva para elección. Coste y versión Python concretos requieren test local.

**A3. scikit-learn: MiniBatchKMeans con partial_fit.** [API oficial](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MiniBatchKMeans.html), versión [1.9.1 (10/09/2026)](https://pypi.org/project/scikit-learn/1.9.1/), BSD-3-Clause. Centroides actualizados incrementalmente con capacidad fija; buen primer baseline aprendiendo prototipos **sin etiquetas**, fácil de inspeccionar. **Límite:** número de clusters escogido por diseñador, sensibilidad a escala, forma y distracciones; no descubre necesariamente factores composicionales.

### B. Categorías autoorganizadas: prioridad inicial

**B1. Adaptive Resonance Theory (ART): Fuzzy ART / Gaussian ART / TopoART.** [Fuzzy ART original, Carpenter–Grossberg–Rosen 1991](https://doi.org/10.1016/0893-6080(91)90056-B), mecanismo de estabilidad–plasticidad por resonancia y umbral de vigilancia. Implementación viva [AdaptiveResonanceLib](https://github.com/NiklasMelton/AdaptiveResonanceLib), paper de software [JOSS 2025](https://joss.theoj.org/papers/10.21105/joss.07764), versión [artlib 0.1.12 24/09/2026](https://pypi.org/project/artlib/0.1.12/), [docs](https://adaptiveresonancelib.readthedocs.io/en/latest/), licencia **MIT**. El repositorio documenta categorías incrementales, ART no supervisado y variantes supervisadas. **Ventaja potencial:** crea categorías con datos sucesivos y puede resistir interferencia. **Riesgos:** un criterio de vigilancia puede generar categorías ilimitadas y aprender irrelevancias; es representación de patrón, no creación espontánea de semántica ni garantía de invariancia. **Recomendación:** primera candidata real reutilizable, con tope de capacidad obligatorio y comparación de umbrales fijada antes del test.

**B2. SOM/Kohonen con MiniSom.** [MiniSom repo](https://github.com/JustGlowing/minisom), [release 2.3.6](https://pypi.org/project/MiniSom/2.3.6/) (febrero 2026), licencia **MIT**; pesos competitivos y preservación de vecindario/topología en grilla de tamaño fijo. **Ventaja:** prototipos adaptables, arquitectura reducida, código legible. **Riesgos:** número de neuronas y malla predefinidos, sesgos por geometría, posible mayor costo que KMeans sin ventaja en transferencia. **Recomendación:** control neuronal autoorganizativo de capacidad fija si el primer piloto demuestra que comparar topología aporta información; no sumar a la matriz inicial por acumulación.

**B3. Growing Neural Gas (GNG) / `minigng`.** [Fritzke, NeurIPS 1994](https://papers.nips.cc/paper/1994/hash/d56b9fc4b0f1be8871f5e1c40c0067e7-Abstract.html), implementación [eliovr/minigng](https://github.com/eliovr/minigng), paquete [minigng 0.1.1 (09/08/2026)](https://pypi.org/project/minigng/0.1.1/). Crece unidades y enlaces para aproximar estructura/topología. **Ventaja:** puede alterar su capacidad de representación sin una grilla preestablecida. **Riesgos:** escala de categorías sin límite, manejo de edades y múltiples hiperparámetros; licencia y mantenimiento sostenido de este paquete **no verificados suficientemente** para adoptar sin revisión adicional. **Recomendación:** segunda ronda solo si ART + centroides no resuelven una necesidad específica de reorganización.

**B4. River DBSTREAM / clusterización de densidad en streaming.** [Código oficial](https://github.com/online-ml/river/blob/main/river/cluster/dbstream.py). Detecta microclusters online; alternativa no neuronal clara para autoaparición/desaparición de grupos. **Riesgos:** umbral de distancia, desvanecimiento de clusters, impacto de orden de llegada. **Recomendación:** agregar como baseline si hay aparición/desaparición de categorías; no usar tabla exacta como único control.

### C. Representación de factores y regularidades, no solo clusters

**C1. IncrementalPCA / regla de Oja.** [IncrementalPCA oficial](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.IncrementalPCA.html), teoría de Oja (1982) revisada en [material universitario](https://bnaskrecki.faculty.wmi.amu.edu.pl/nnets/_build/html/part4_learning_rules/ch13_oja_pca.html). Aprende direcciones lineales de varianza. **Costo pequeño y control útil** de representación lineal; no puede garantizar separar factores latentes no lineales o relevantes con varianza baja. No afirmar que PCA aprende la «categoría correcta».

**C2. Aprendizaje de diccionarios dispersos (sparse coding).** [MiniBatchDictionaryLearning.partial_fit](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.MiniBatchDictionaryLearning.html), [Mairal et al. 2009](https://www.di.ens.fr/~fbach/mairal_icml09.pdf). Átomos adaptables que pueden reutilizarse en combinaciones nuevas. **Interesante para composicionalidad** con entradas de alta dimensión; control de número de átomos indispensable, costo de optimización superior a KMeans/ART. Segunda fase si surge pregunta de combinaciones no resuelta.

**C3. Slow Feature Analysis (SFA).** [Wiskott–Sejnowski, Neural Computation 2002](https://pubmed.ncbi.nlm.nih.gov/11936959/). Aprende características que varían lentamente en series temporales sin etiquetas. **Ventaja:** cuando el problema necesita invariancia en transformaciones sucesivas; **límite:** depende de una hipótesis de continuidad temporal que no vale para cualquier secuencia y puede confundir distractores lentos con categorías. Requiere una tarea temporal específica, no introducirla como ingrediente decorativo.

### D. Mecanismos de mayor complejidad: referencias, no elección inicial

**D1. HTM Spatial Pooler / Temporal Memory.** [htm-community/htm.core](https://github.com/htm-community/htm.core), comunidad con implementaciones C++/Python; variante comunitaria activa, original NuPIC archivado. Licencia **AGPLv3** según repositorio. Arquitectura extensa y compromisos de licencia/dependencias desproporcionados para un primer desafío abstracto. **Posponer** hasta hallar ventaja específica de secuencias dispersas que un control pequeño no logre.

**D2. SoftHebb (aprendizaje hebbiano local competitivo).** [SoftHebb repo](https://github.com/NeuromorphicComputing/SoftHebb); buen antecedente de aprendizaje WTA/online y reglas locales sin backprop. Su configuración publicada usa experimentos con CNN/datasets de imágenes y entrenamiento más complejo. **No hay evaluación de que reproduzca un microcircuito C1 ni ventaja con pocos bits**; el costo de adaptar la infraestructura supera un piloto con ART/KMeans. Licencia de uso del código debe verificarse antes de copiarlo.

**D3. Representación contrastiva tipo SimCLR.** [Chen et al., ICML 2020](https://proceedings.mlr.press/v119/chen20j.html). Aprende invariancias con pares de vistas/augmentaciones, pero la *política de augmentación es información externa sobre qué debe preservarse*, potencialmente tan privilegiada como el detector A×B de E06. Además requiere entrenamiento por gradientes y mayor presupuesto. No usar como «prueba» de emergencia autónoma sin controles de información.

**D4. Redes de aprendizaje predictivo/implementaciones biológicas extensas (Leabra, NGC-learn).** [Leabra](https://github.com/emer/leabra) y [NGC-learn](https://github.com/NACLab/ngc-learn) son referencias para algoritmos locales/predictivos; sus dependencias y complejidad hacen que un salto inicial esté injustificado. Revisar solo si un mecanismo específico se convierte en hipótesis de alto valor.

### E. Alternativas que abordan otro problema

**EWC, Synaptic Intelligence, multiescala Benna–Fusi, replay y reglas de tres factores:** ya examinadas en [I3c8](E09_02I_I3C8_ALTERNATIVAS_EXISTENTES_MEMORIA.md). Ayudan a estabilidad/retención/crédito, **no crean necesariamente las features útiles**. Incluir como ensayo secundario **solo** después de identificar un cuello de botella reproducible del aprendizaje de representación. No «resolverlo» con consolidación primero.

## 3. Selección basada en requisitos

- **Control cero:** tabla de observaciones completas/1-NN, con límites de capacidad; aprendizaje online supervisado de River como punto de referencia de clasificación.
- **Baselines aprendidos sin recompensas:** **MiniBatchKMeans** (centroides fijos) y **ARTlib Fuzzy ART** (categorías adaptativas). Ambos reciben exactamente los mismos vectores; aprenderá su representación **antes** de observar cualquier etiqueta o mapa de recompensa downstream.
- **Si el factor temporal es indispensable:** SFA, River con ventanas y HTM solo tras una nueva hipótesis específica; no contaminar la primera comparación.
- **Si faltan composición o capacidad estructural:** MiniBatchDictionaryLearning, GNG o variantes ART sin ampliar por defecto.
- **MiniSom** como control neuronal de topología fija cuando aporte una pregunta discriminante frente a centroides.

**Recomendación actual:** NO desarrollar un nuevo modelo neuronal. Primero diseñar una **comparación de aprendizaje de representación no supervisado + reutilización para nuevas tareas** con controles tabulares y KMeans, ART como único candidato estructural principal. Mantener la opción de que el ganador sea un algoritmo simple. Las capacidades publicadas por cada biblioteca **no son todavía resultados de NeuroLab**.

## 4. Riesgos metodológicos que debe resolver el diseño

1. **No confundir partición con representación útil:** clustering puede agrupar por ruido o por intensidad, no por regularidad que sirva a acciones.
2. **Sin señal oculta privilegiada:** generador/evaluador conoce la verdad latente pero **ningún encoder ni baseline** debe recibir las etiquetas, el mapa o parámetros de generación.
3. **Evaluación de transferencia verdaderamente inédita:** el holdout debe incorporar combinaciones no entrenadas y mundos/transformaciones generativas nuevos, no solo nueva semilla que conserva idéntica tabla codificada.
4. **Competencia justa:** igual información, presupuesto de eventos, memoria medida, tiempo/costo reportados, hiperparámetros de desarrollo separados de la confirmación. Oráculo con representación correcta es solo techo de interpretación.
5. **Técnicas que necesitan conocimiento de invariancia (aumentos, máscara, pares contrastivos):** contabilizar esa información y compararla de modo justo, no «descubierta» por el sistema.
6. **Control negativo anti-fuga:** recompensas/regularidades aleatorias o permutadas deben impedir inferir una estructura útil.
7. **Revisión de licencias y versiones antes de ejecutar:** sólo se verificaron fuentes web/repositorios; los paquetes no se instalaron ni se ejecutaron aquí.
8. **Criterio de detención:** si los baselines simples logran igual transferencia bajo igual presupuesto, el proyecto puede reutilizar solución existente o cerrar esta vía; no tunear más neuronas.

**Próximo documento de contrato:** [NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md). La etapa R01 prepara un contraste científico; no aprueba todavía la arquitectura de Nilo ni habilita correr experimentos sin protocolo cerrado.
