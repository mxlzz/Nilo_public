# E0.8 — H12b: importaciones y ABI de DRYP 2.0 (auditoría estática)

Fecha: 2026-11-21. Estado: H12b completada, runtime NO VERIFICADO.
Plan: `ETAPA_0_8_DRYp_ALTERNATIVAS_Y_H11C_PLAN.md`. Código de inspección `experiments/probe_dryp2_dependencies_static.py`. CI aislada https://github.com/mxlzz/Nilo_public/actions/runs/44957301049 (**SUCCESS**, contiene H12a+H12b).

## Procedencia
Se descargó nuevamente el ZIP del DOI https://doi.org/10.5281/zenodo.17451148 y se verificó que el MD5 publicado coincide. Se leyeron archivos fuente con `ast.parse` **sin ejecutar imports**, sin instalar paquetes externos ni incorporar archivos de terceros al repo. SHA-256 del ZIP: `38032acd29b592e8fcf4aa9edf180bbaa6a933ec19af85c9921150bcc3bfe36a`.

## Hallazgos
- **46 módulos Python**, sin errores de sintaxis en Python 3.13 (H12a). No implica que sus dependencias funcionen.
- Importaciones externas más frecuentes: `cuwalid` (65), `numpy` (33), `pandas` (12), `landlab` (12), `netCDF4` (6), `rasterio` (4), `matplotlib` (3), `xarray` (3), `scipy` (2), `Cython`, `rioxarray`, `tqdm`, además de `distutils` (retirado del core Python actual, salvo compatibilidad externa por setuptools).
- El ZIP contiene ruta base `dryp/`, scripts `dryp/main_DRYP.py`, `dryp/main_DRYP23.py`, `dryp/main_DRYPv2_SS.py`, `dryp/main_DRYP_SS.py`. No se detectó un runner de prueba estándar `test_*.py`; solo `dryp/example/plot_test_summary.py` lleva 'test' en la ruta.
- **Extensiones compiladas disponibles:** `faccumf90`, `gaussf90`, `lakesf90` para CPython **3.10 y 3.11 en Linux** y versiones 3.9/3.10/3.11 en Windows (pyd), más `TransLoss` Win CPython3.7 y bibliotecas Fortran. **No se verificaron extensiones CPython 3.13 para Linux/Windows.**
- Importaciones `cuwalid` sugieren que el paquete DRYP2 no es independiente del sistema CUWALID. La documentación https://cuwalid.github.io/tutorials/pip-installation/ aún dirige a TestPyPI para CUWALID y requiere bibliotecas geoespaciales. En el ZIP inspeccionado no se detectó un árbol `cuwalid/` completo, por lo que debe aclararse si se distribuye separado. **Importar el ZIP como paquete autónomo en Python 3.13 sin dependencias externas probablemente fallaría; no se ejecutó para confirmarlo.**
- ZIP no contiene LICENSE interno; Zenodo publica uno externo MIT con copyright `CornishLeo`; Coincide con el desarrollador citado en docs CUWALID pero no constituye prueba de titularidad sobre todos los módulos.

## Dictamen y recomendación
**NO adoptar DRYP2 en el entorno actual hasta poder demostrar runtime y condiciones legales de adaptación.** Su diseño de suelo-agua-acuífero y manejo de distintos pasos temporales constituye un referente importante. Si se justifica un modelo completo, preparar una ejecución de caja negra en Python 3.11 en runner aislado, solo luego de revisar dependencias y sin importar/redistribuir código en el repositorio; no reimplementar todo de memoria.

Para la próxima prueba de mundo, mantener componentes Landlab 2.11 MIT que pasaron H7-H13. DRYP2 no se considera inexistente ni descartado de forma definitiva.
