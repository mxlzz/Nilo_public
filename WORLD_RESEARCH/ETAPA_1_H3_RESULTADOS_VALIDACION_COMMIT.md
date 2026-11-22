# Etapa 1 — H3: integridad de capas y publicación validada

**Fecha:** 2026-11-22. **Estado:** H3 APROBADA en un único escritor, sin leyes físicas. **Etapa 1 general ABIERTA** hasta resolver alcance de representación espacial/material; esto no adopta una arquitectura universal.
**Protocolo previo:** `ETAPA_1_H3_PROTOCOLO_VALIDACION_COMMIT.md`.
**Código:** `experiments/probe_e1_all_level_validation.py` y regresiones H1/H2 sin modificar.
**CI verificado:** https://github.com/mxlzz/Nilo_public/actions/runs/44986576611 — **SUCCESS**.

## Herramienta existente evaluada
`pandera.xarray.DatasetSchema` de Pandera **0.36.0** (repo upstream MIT https://github.com/unionai-oss/pandera y documentación oficial https://pandera.readthedocs.io/en/stable/xarray_guide/dataset_schema.html), xarray 2026.9.0, Landlab 2.11.0, NumPy, Python 3.13. Se comprobó que Pandera puede validar variables, atributos de unidades, dimensiones, datos finitos/no negativos y reglas multivariable de capacidad; el **oráculo MatterGrid existente** revisó por separado cada nivel. El balance global se verificó explícitamente, porque Pandera no sabe qué fuentes/sumideros son legítimos.

## Ejecución
- Escenario H1 reutilizado: 2 materiales A/B, 2 niveles, 2×3 celdas por nivel. Campos Landlab (nivel0) comparten memoria con el tensor xarray mediante H2. Inventario global original A=1.1 kg, B≈0.6 kg.
- Siete **controles negativos**, todos rechazados ANTES de modificar owner y vistas:
  1. `negative_upper_layer` -> Pandera SchemaError
  2. `capacity_exceeded_upper_layer` -> Pandera SchemaError
  3. `nan_upper_layer` -> Pandera SchemaError
  4. `unaccounted_source_upper_layer` (añadir 0.05 kg sin retirarla) -> ValueError del balance global
  5. `unit_mismatch` (g en vez de kg) -> Pandera SchemaError
  6. `permuted_material_mass_dimensions` -> Pandera SchemaError
  7. `unexpected_material_identifier` -> ValueError del contrato de etiquetas.
- Se creó un candidato independiente `xarray.Dataset.copy(deep=True)`; transferencia **manual 0.1 kg A** en la celda (x2,y1) desde nivel0 a nivel1, sin cambio de número de partículas ni ley de gravedad, únicamente para demostrar persistencia y topología de información.
- Ambas rutas de validación aprobaron el candidato y el balance completo. Se publicó con `numpy.copyto` en **un solo escritor**. Landlab mantuvo alias de memoria y observó el valor actualizado en nivel0. Total A=1.1 kg y B≈0.6 kg. Los cambios inválidos previos no habían tocado el owner.

## Costos medidos SOLO en este microensayo
- Validación Pandera+MatterGrid de base: **7.8676 ms**. Commit `numpy.copyto` a tensor diminuto: **2.757 µs**. Son tiempos descriptivos, no benchmark estable ni predicción a territorios grandes. Validar cada tick de una simulación rápida puede costar demasiado; evaluar frecuencia y transacciones antes de diseño final.
- Se mantuvieron exitosas las 8 pruebas previas `matter_v0.py` y las pruebas H1/H2 durante la misma CI.

## Dictamen crítico
**Aprobado:** estrategia de datos etiquetados, validación de todos los niveles y publicación controlada de una copia candidata, preservando vistas de integración. Se demostró que un estado de materia **puede** tener owner único en condiciones restringidas.

**NO demostrado:** seguridad multiproceso/multihilo, transacciones concurrentes, aislamiento de lectores durante `copyto`, validez universal de compartir vistas para componentes Landlab que reemplacen sus propios campos, contacto/solidificación, 3D físico, ley de movimiento, energía, reacciones o evolución abierta. La API de acceso directo NumPy puede modificar cantidades inválidas sin pasar por el validador.

**Alternativa considerada:** reutilizar el oráculo MatterGrid para cada nivel sin instalar Pandera; cubre positividad, capacidad y densidad, pero no reemplaza verificación estructural ni de unidades. Pandera es una opción madura reutilizable de **validación de frontera**; no se elige para cada tick de motor físico a partir de un único tiempo de 8ms.

**Gate siguiente:** elaborar decisión reversible de propietario de estado y contratos antes de añadir leyes; mantener Landlab como proveedor de procesos ambientales, no como sustrato volumétrico universal. No fusionar branch ni alterar NeuroLab.
