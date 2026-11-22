# Etapa 1 — H2: dueño único del estado material, vistas compartidas y persistencia

**Fecha:** 2026-11-21. **Estado:** PROTOCOLO ANTES DE IMPLEMENTAR. E0 cerró el gate de alternativas en ADR-0003; E1/H1 representó sin pérdida un inventario material por Landlab y xarray. Este experimento **no introduce física ni motor de movimiento**.

## Antecedentes y riesgo
La implementación oficial de Landlab `GraphFields.add_field(name, array, at="cell", copy=False)` declara que puede guardar una referencia al array recibido. Internamente `FieldDataset` utiliza xarray y `DataArray.values`. No debe confundirse soporte de campos con garantía de una única instancia mutable: xarray/NumPy pueden devolver vistas o copias y una sustitución de variable rompe referencias existentes. Referencia: https://github.com/landlab/landlab/blob/master/src/landlab/field/graph_field.py .

## H2 — hipótesis y escenarios preregistrados
**Hipótesis:** una matriz numérica dueña de inventario `xarray.Dataset.material_mass(material,level,y,x)` puede exponer la **capa 0** en campos por celda de `RasterModelGrid` mediante vistas NumPy `copy=False`, sin duplicar inventario, y recuperar esa identidad de referencias luego de persistir como NetCDF.

1. Reutilizar `oracle()`, `dataset_projection()`, `validate_and_restore()` del script H1 sin modificarlos. A y B, 3×2 y 2 niveles; los centros Landlab 4×5 se mapean por sus coordenadas reales.
2. Para cada material, obtener un vector del array multidimensional subyacente de xarray, evitando índices sofisticados que devuelvan copias; reordenar solo si los índices de Landlab no coinciden con el mapeo de celdas. Registrar `np.shares_memory(field,ds.material_mass.values)` y coincidencia del orden de la proyección para **ambos** materiales; no aprobar si alguna copia accidental da valores correctos pero no comparte memoria.
3. Intervención manual: restar 0.05 kg del material A de una celda con A y sumar 0.05 kg en otra celda con capacidad. Es **transferencia de prueba**, no modelo de movimiento. Comprobar que xarray ve exactamente ambos cambios de Landlab y que el total por componente no cambia; `validate_and_restore(ds)` debe reconstruir material y capacidad correctos.
4. Mutación inversa: cambiar en xarray el inventario de una celda mediante asignación a sus `values` existentes, no sustitución de la variable completa. Comprobar que el campo Landlab se actualiza, que masas siguen conservadas y que la capacidad no se excedió. Niveles superiores sin alteraciones.
5. **Control negativo:** campo Landlab creado desde mismo vector con `copy=True` en una segunda grilla y diferente nombre. Debe tener **memoria separada** y no reflejar mutaciones posteriores. Si `copy=True` comparte memoria, registrar que el supuesto es incorrecto.
6. **Persistencia:** guardar NetCDF y reabrir mediante xarray. Comprobar roundtrip de valores/unidades y reconstruir **nuevas** vistas Landlab sobre el estado restaurado. No exigir que referencias sobrevivan al proceso de serialización: exigir que se **reestablezcan** mediante un procedimiento reproducible. Verificar `np.shares_memory` tras reatar y comparar el inventario restaurado con el previo.
7. **Control de corrupción:** inyectar cantidad negativa o sobrecapacidad en una vista compartida y verificar rechazo por el validador. La conclusión debe señalar que las bibliotecas no impiden por sí mismas una mutación inválida. Revertir el cambio sin afectar el baseline guardado.
8. Registrar SHA del estado, versión, tamaño de NetCDF, igualdad bit a bit, pruebas positivas y negativas; no permitir que `xarray` y Landlab sean simultáneamente propietarios conceptuales de cantidades duplicadas. **Estado canónico propuesto: tensor de masa; campos Landlab serían vistas de integración.** Es una hipótesis de representación, no adopción definitiva.

## Salida
**H2 aprobada si:** alias bidireccional real, control `copy=True` no alias, conservación tras cambios, capa superior aislada, corrupción detectada, NetCDF recupera datos exactos y se vuelven a enlazar nuevas vistas. Si el framework copia, falla el gate aunque roundtrip conserve datos; preferir adaptador explícito con owner único y sincronización validada.

**Bloqueos posteriores:** no extrapolar a `Space`, `SoilMoisture`, `Radiation` o `OverlandFlow`, porque esos componentes almacenan referencias, pueden reubicar arrays y usan topologías distintas; no se ha ensayado un solo inventario hídrico/sólido entre solvers. No declarar estado 3D físico porque existen dos índices de nivel. No iniciar leyes de materia nuevas hasta aprobación de arquitectura mínima compartida y sus tests.

## Auditoría tras la primera CI H2 (sin ocultar desvíos)

Primera ejecución: https://github.com/mxlzz/Nilo_public/actions/runs/44959354131, **SUCCESS** para alias, copias, balance, niveles, corrupción y NetCDF. Se registró un desajuste **del arnés frente al protocolo**: el documento fijó transferir **0.05 kg** en el primer cambio, pero el script ejecutó **0.125 kg**. Ambas caben en la celda, pero los valores de un protocolo preregistrado no se alteran implícitamente. La prueba inicial es válida para el mecanismo de memoria compartida, pero la conformidad estricta al protocolo H2 requiere repetir la transferencia con 0.05 kg y conservar ambas ejecuciones.

### H2b, control negativo adicional antes de implementarlo
**Riesgo identificado por lectura de Landlab y xarray:** sustituir toda la variable mediante asignación `ds["material_mass"]=...` puede crear un array nuevo sin actualizar los campos Landlab enlazados. Los tests H2 solo modifican `values` en sitio; aún no demuestran seguridad al reemplazar variables, una operación habitual al trabajar con xarray.

**Hipótesis:** tras reemplazar el tensor xarray por una copia independiente de valores idénticos, el campo Landlab anterior deja de compartir memoria. Mutar la nueva variable ya no debe verse desde el campo anterior. Rehacer `grid.add_field("material_mass__A", nueva_vista, at="cell", copy=False, clobber=True)` restablece el alias y una mutación posterior vuelve a propagarse. La masa total debe permanecer invariante (cambios de prueba reversibles) y no deben cambiar niveles altos. La sonda debe informar `stale_view_detected` y `explicit_rebind_restores_alias`, sin fingir que la sincronización es automática.

**Criterio:** no se aprueba seguridad de propiedad de estado si el alias se rompe sin ser detectado. Aunque H2b pase, **no** garantiza ausencia de race conditions, transacciones atómicas ni soporte para cambio de forma/topología; habrá que imponer reglas de actualización y testearlas antes de sistemas físicos simultáneos.

**Alcance:** son pruebas de infraestructura sobre datos, no leyes de transporte.
