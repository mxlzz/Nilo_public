# Etapa 1 — H13A. Viabilidad técnica de GeoTaichi CPU no demostrada en entorno acotado

**2026-11-22. Dictamen: H13A NO APROBADA; bloqueada en imports antes de ejecutar física.** No se concluye que GeoTaichi sea incorrecto o incapaz de simular MPM 3D en CPU. La razón comprobada es el costo creciente del árbol de dependencias de importación en la instalación deliberadamente limitada.

**Protocolo previo:** [ETAPA_1_H13A_PROTOCOLO_GEOTAICHI_CPU.md](ETAPA_1_H13A_PROTOCOLO_GEOTAICHI_CPU.md).
**Workflow:** [.github/workflows/world-e1-geotaichi-cpu.yml](../.github/workflows/world-e1-geotaichi-cpu.yml).
**Proveedor original inalterado:** https://github.com/Yihao-Shi/GeoTaichi en commit `6cae5a6998c4f0be9f59b5615bf2e26857df824f`, GPL-3.0, Python 3.11, `taichi==1.7.0`, CPU, Ubuntu 24.04; checkout temporal en CI, sin copiar código del proveedor a Nilo.

## Primer intento: import Open3D faltante

[CI 45055983838](https://github.com/mxlzz/Nilo_public/actions/runs/45055983838) **FAIL**. Entorno inicial instaló Taichi/NumPy/Scipy/Trimesh/Pillow/Pytest/Matplotlib/Sympy/Meshio, checkout de revisión exacta; el primer test abortó al importar `geotaichi/__init__.py → src.sdf.arbitrarily → src.sdf.MeshBased → src.sdf.BasicShape` por `ModuleNotFoundError: No module named 'open3d'`. No se ejecutó física. Open3D figura entre las dependencias declaradas en pyproject del upstream.

Enmienda **preregistrada** en protocolo tras fallo: instalar solamente `open3d==0.19.0` (wheel binaria, `--no-deps`), sin alterar pruebas oficiales ni física, y **detener la persecución de dependencias en caso de nuevas importaciones ajenas a MPM**.

## Segundo intento: nueva importación Plotly

[CI 45056130916](https://github.com/mxlzz/Nilo_public/actions/runs/45056130916) **FAIL** tras instalar Open3D y recuperar upstream exacto. El primer test volvió a abortar por `ModuleNotFoundError: No module named 'plotly'`. Nuevamente el solver 3D no se ejecutó y el control adversarial secundario tampoco, dado `--maxfail=1`. Este segundo fallo no prueba nada sobre estabilidad de partículas, conservación de masa o errores de MPM.

**Causa observada a nivel de integración:** paquete `geotaichi` importa de forma ávida módulos ajenos a la ruta estrictamente necesaria de ensayo MPM, haciendo que una instalación parcial no sea suficiente. El primer intento mostró `open3d`, y el segundo `plotly`. No se infiere que la instalación completa oficial falle: no se ha probado.

## Decisión y gate

**Se detiene H13A según la regla definida antes del segundo intento**, sin añadir Plotly y sin cambiar el upstream. No declarar GeoTaichi descartado para futuras investigaciones, ni convertir un problema de importación en un problema científico del constitutivo. Se rechaza **por ahora** la ruta de integración CPU acotada para el próximo experimento porque la carga de dependencias y mantenimiento aumenta antes de obtener evidencia física nueva.

**Resultado útil de decisión:** H11 de PINNeAPPle sigue siendo demostración básica de deformación; H12 sigue NO aprobada por fracción de clamping inferior. No hay validación independiente MPM 3D. El siguiente paso debe ser una alternativa **realmente independiente y más aislable** o una validación cuantitativa contra benchmark publicado, con suelo/apoyo mecánico explícito; si no existe solución apropiada, registrar el bloqueo en vez de programar un solver propio. Conservar separación Stage1 y no modificar `main` ni NeuroLab.

**No hubo pruebas MPM superadas en H13A**; los dos CI rojos permanecen como evidencia para auditoría.
