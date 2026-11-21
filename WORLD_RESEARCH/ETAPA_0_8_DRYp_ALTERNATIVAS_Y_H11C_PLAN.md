# E0.8 — Revisión de DRYP y gate H11c ANTES de integrar nueva hidrología

Fecha: 2026-11-21. Estado: investigación de alternativas y protocolo experimental; **etapa 0 abierta**. Documenta decisiones reversibles sin incorporar código ajeno.

## Objetivo de línea
El proyecto busca un entorno físico autónomo, inicialmente generado, con procesos causales acoplables y verificables. NeuroLab es independiente. La unidad H11b mostró balance de agua superficial + infiltrada, **no** humedad de raíces ni aguas subterráneas. Antes de diseñar un adaptador, contrastar modelos ya completos y un benchmark justo de los módulos disponibles.

## Alternativas nuevas y verificación de procedencia
### DRYP 1.0
- Artículo revisado en Geoscientific Model Development, Quichimbo et al. (2021), https://doi.org/10.5194/gmd-14-6893-2021: modelo de Landlab con zona superficial, no saturada y saturada; almacenamiento, evapotranspiración, recarga, ríos efímeros; pasos temporales distintos.
- Repo upstream https://github.com/AndresQuichimbo/DRYP y documentación; fecha del último push en API GitHub: **2021-12-08**. Repo no archivado, pero sin licencia identificada en metadatos GitHub (`license: null`); no hay un archivo LICENSE en la raíz inspeccionada. No equivale a concesión pública de derechos de adaptación/republicación; no copiar al repositorio de nuestro mundo.
- Guía de usuario 2021 https://gmd.copernicus.org/articles/14/6893/2021/gmd-14-6893-2021-supplement.pdf: Python 3.7.4, Landlab 2.0, NumPy 1.16.4 y pandas 0.25.1. En su driver reciente `run_DRYP.py` se importan extensiones y bibliotecas como netCDF4 y el repositorio incluye Cython, lo que añade complejidad de mantenimiento. No se ejecutó con la versión Landlab 2.11 todavía.

### DRYP 2.0 — HALLAZGO POSTERIOR, MÁS RELEVANTE
- Zenodo, **26-oct-2025**, DOI https://doi.org/10.5281/zenodo.17451148: nueva versión de DRYP para cuencas y escala regional, clima seco y otros gradientes, con superficie, zona vadosa y acuífero, lagos/charcas/intercepción de vegetación, distribución espacio-temporal.
- Preprint Quichimbo et al. 2025 https://doi.org/10.5194/egusphere-2025-5316 (estado editorial: preprint, no afirmar aceptación). El archivo `dryp.zip` 5.7MB se publica en Zenodo.
- Archivo independiente `LICENSE` en Zenodo declara MIT, pero copyright `(c) 2024 CornishLeo`, sin correspondencia clara en los autores. **Licencia/procedencia del código real NO CLARIFICADA.** No afirmar permiso seguro de redistribuir el archivo ZIP ni incorporarlo; inspeccionar los avisos interiores de la distribución o solicitar aclaración a autores antes de seleccionar como núcleo.
- Intento de descargar ZIP al contenedor de análisis: descarga no disponible; **NO se examinó código 2.0 ni se ejecutó.** No inferir su compatibilidad con Landlab 2.11 ni conservación real solo por descripciones.
- Datos de 1.0 no se extrapolan a 2.0 sin pruebas. La actualización puede cambiar prioridades: **no diseñar nuevo framework hídrico multisectorial propio antes de comparar DRYP 2.0 en condiciones concretas**.

### Otras opciones que siguen disponibles
- Landlab 2.11.0, MIT, en Python 3.13, verificadas H7-H11b. `OverlandFlow` y `KinwaveImplicitOverlandFlow` usan fórmulas y fuentes diferentes. `SoilInfiltrationGreenAmpt` se conecta directamente por campos con estos solvers, pero la equivalencia física aún requiere tests.
- HEC-HMS Layered Green–Ampt demuestra que ya existen enfoques de suelo estratificado y balance de zona radicular; su software/contratos no se presuponen incorporables al framework Landlab. https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/canopy-surface-infiltration-and-runoff-volume/infiltration/layered-green-and-ampt-model
- ParFlow, simulador integral de agua superficial/subsuperficial y evapotranspiración, LGPL: https://www.parflow.org/ . Potente pero de otra escala y dependencias complejas; no sustituir Landlab sin test de integración.

## H11c — COMPARACIÓN JUSTA de dos rutas de flujo con Green-Ampt

**Hipótesis:** `OverlandFlow` (de Almeida) + `SoilInfiltrationGreenAmpt` pueden compartir explícitamente los campos de profundidad, conservando agua, aunque el modelo publicado del tutorial use `KinwaveImplicitOverlandFlow`. Con misma geometría e infiltración, ambos solvers obtendrán balances correctos; sus campos espaciales y velocidades de cómputo podrán diferir porque sus ecuaciones no son idénticas.

**Contrato de condiciones:** malla 12×12 con separación 1m, 100 nodos interiores (100m²), fronteras cerradas, paisaje pendiente suave y ondulación H11a/H11b, 60 segundos de evento 72mm/h en 120 pasos de 0.5s; misma película superficial inicial de 1e-8m y misma columna de infiltración inicial 0.01m. El modelo de Almeida recibe lluvia `72/3.6e6 m/s`; Kinwave recibe `72 mm/h`. Green-Ampt igual K=1e-6m/s, suelo sandy loam, superficie mínima 1e-8m. Manning 0.03 y exponente 5/3 en Kinwave (Almeida usa Manning en su formulación).
**Escenarios por solver:** activo lluvia+infiltración, lluvia+K=0, sin lluvia+K>0 y activo con terreno +0.2m. Repetir activo. Definir presupuesto como `(Vsuperficie final + Vinfiltración final) - (inicial + aporte lluvia)` y medir error respecto del **aporte de lluvia** (0.12m³), NO dividir por los ~1m³ preinfiltrados, que minimizaría artificialmente el residual.
**Criterio H11c:** en ambos, residual relativo sobre aporte <0.1%, sin agua negativa o NaN; K=0 no infiltra, sin lluvia no crea volumen; intervención cambia la distribución espacial, no volumen; replay exacto. Medir CPU *con misma carga de trabajo* pero repetir para microbench únicamente orientativo. Registrar diferencia entre campos, **no exigir igualdad de campo** entre distintos modelos. Si un modelo falla, no bajar tolerancias: auditar tipo de frontera/film/semántica de flux.
**Salida:** recomendación condicionada sobre capacidad de conservar agua, simplicidad, costo, topografía mutable, extensión a zona radicular. No elegir hasta evaluar DRYP 2.0/licencia y capacidad de continuidad general.

## H12: gate de zona radicular, sin inventar física
Comparar primero el suelo no saturado de DRYP 1/2 y los modelos documentados (Laio/SoilMoisture y Green–Ampt estratificado). El campo `soil_water_infiltration__depth` representa agua que atravesó superficie, no almacenamiento en una capa con espesor/porosidad determinado. No escribir `soil_moisture__saturation_fraction = infiltration_depth`.
Cualquier puente necesita espesor y porosidad root zone, estado de almacenamiento (volumen, no solo fracción), evapotranspiración/leakage, límites y no duplicar lluvia/ET. Registrar esquema y casos sintéticos antes de implementar.

**Gate de etapa**: H11c ejecutable ya en rama experimental. H12 arquitectura detenida hasta verificación técnica de modelos existentes. Toda decisión reversible, sin cambios a main ni NeuroLab.

## Addendum H11c-1 — anomalía del indicador en control de aporte nulo
Primer workflow H11c: https://github.com/mxlzz/Nilo_public/actions/runs/44956774655 (**FAIL**). `Kinwave` falló con `relative_error_vs_rain=0.0086597`; el script dividía `abs(residual)` por `max(rain_volume,1e-12)`. Si el caso fallido fue el control `rain_volume=0`, el denominador 1e-12 crea un porcentaje artificialmente enorme incluso ante residuo de pocos femtómetros cúbicos. Hay que diagnosticar el caso exacto: la prueba original imprimía resultados al final, **después de las aserciones**; no permite todavía adjudicar el fallo a conservación ni confirmar definitivamente el origen del ratio.

**Enmienda del criterio antes de reintentar (no relajar la tolerancia original):**
- Con `rain_volume>0`: `abs(residual)/rain_volume<0.001` (0.1%, igual que plan).
- Con `rain_volume=0`: exigir `abs(residual)<1e-9m³`, e informar ese residual **absoluto**. No dividir entre 1e-12 ni fabricar un cociente sin significado.
- Emitir los diagnósticos de cuatro escenarios antes de las aserciones, para poder auditar un fallo real sin editar repetidamente el ensayo.
- Si el fallo >0.1% ocurre en un escenario **con lluvia**, detener selección de solver y cuantificar masa de frontera/numérica. La enmienda no permite aprobar ese escenario.

## Addendum E0.8-DRYP2 — inspección de distribución existente sin copiar ni ejecutar código (antes del ensayo)
Se localizaron también la documentación de CUWALID (https://cuwalid.github.io/), que incluye DRYP, STORM y stoPET, y el tutorial https://cuwalid.github.io/tutorials/github-installation/ . Este último atribuye el repo a `CornishLeo/CUWALID`; esa ruta responde HTTP 301 en GitHub API a un identificador de repositorio, cuyo destino canónico no pudo recuperarse por la integración disponible. La licencia MIT publicada en Zenodo 2.0 incluye `Copyright (c) 2024 CornishLeo`, que coincide con ese identificador de CUWALID. **Esto proporciona una explicación posible de la atribución, no prueba por sí sola que todos los archivos DRYP 2.0 estén legalmente cubiertos.**
CUWALID guía de instalación https://cuwalid.github.io/tutorials/pip-installation/ recomienda rama TestPyPI, y para STORM requiere GDAL y `numpy<2.0`; no extrapolar esa dependencia a DRYP standalone sin inspeccionar.
**Riesgo metodológico:** el tutorial de GitHub de CUWALID muestra un ejemplo de test que puede lanzar `AssertionError` en comparación de salida. No presumir que todos los tests upstream pasan.

### H12a — clasificación estática de ZIP original, sin incorporación de código
- Descargar desde Zenodo DOI `10.5281/zenodo.17451148` solamente en el runner efímero; verificar **MD5 `f1c491b001755a22c90214d609c0d51b`** indicado por Zenodo para `dryp.zip` y reportar SHA-256 para reproducibilidad; no almacenar ZIP en GitHub ni artifact.
- Abrir ZIP en modo solo lectura, límite de tamaño descomprimido, inspeccionar árbol de archivos, nombre/copyright de licencias en el archivo si existen, versionado/dependencias, antigüedad aproximada de scripts; compilar AST de módulos Python para detectar problemas sintácticos **sin importar/ejecutar** código del proyecto externo.
- Salidas: reporte resumido, número de módulos, errores y ruta(s) de configuración/test dentro del ZIP; no publicar código/archivos ajenos. Comparar existencia de licencias internas con la licencia externa del registro.
- **Criterio positivo:** descargable con hash correcto, estructura inspeccionable y sintaxis compatible con Python 3.13. **No equivale** a que funcione con dependencias, que sus ecuaciones sean adecuadas al mundo, ni autoriza redistribución.
- Si falla descarga, no inventar resultado; conservar fallo como bloqueo de infraestructura y mantener fuentes bibliográficas.
- **Gate:** no instalar ni acoplar DRYP2 hasta ver estructura, licencia y requisitos; revisar luego pruebas upstream/documentación como caja negra, sin mezclarlo con NeuroLab.

## H12b — Dependencias y ABI de DRYP 2.0 (plan, sin ejecución de código de terceros)
Tras H12a, el archivo oficial verificado contiene **46 módulos Python sintácticamente válidos** y numerosas extensiones compiladas (`.pyd`, `.dll`, `.so`, fuentes Fortran/Cython). Esto permite formular una inspección más precisa antes de intentar ejecutar un programa externo en la CI.
**Hipótesis:** la distribución puede requerir módulos específicos y binarios no portables a Python 3.13/Linux, que cambian el costo y la conveniencia frente a Landlab 2.11 probado.
**Método**: mismo ZIP y MD5 de Zenodo, abrir en modo solo lectura, analizar importaciones mediante AST (sin importar), listar nombres de librerías compiladas y posibles etiquetas `cpython-XY`; identificar entry points y módulos de test, dependencias declaradas en paquetes estándar sin ejecutar setup. Validar que los archivos de test y un driver identificable existen y reportar posibles incompatibilidades. **No** ejecutar binarios ajenos, no publicar archivos ZIP ni licencia, ni asumir que sintaxis compatible equivale a ABI compatible.
**Criterio:** manifiesto completo y hashes verificados; resultado informativo (puede mostrar incompatibilidad). Si aparecen dependencias nativas no verificables, DRYP2 queda como comparación académica y candidato de caja negra, no núcleo ya adoptado.
