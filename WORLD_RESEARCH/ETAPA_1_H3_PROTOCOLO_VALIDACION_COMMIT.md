# Etapa 1 — H3: validación completa de inventario y publicación por commit

**Fecha:** 2026-11-22 · **Estado:** PROTOCOLO previo a cualquier código H3. H1 y H2/H2b aprobados en CI; el resultado H2 demostró que xarray/Landlab comparten datos mediante `copy=False` y que una reasignación de xarray rompe aliases. Este ensayo sigue **dentro de etapa 1**, sin física, objetos ni movimiento automático.

## Necesidad concreta
`validate_and_restore(ds, level=0)` en H1 solo revisa una capa. Una masa negativa o excesiva en `level=1` podría pasar desapercibida si solo se valida la superficie. Además, toda mutación directa a un array compartido afecta inmediatamente a los dos lectores, incluso si la operación resulta inválida. Es necesario evaluar un contrato de integridad **antes de integrar solvers**.

## Reutilización de soluciones, evaluada antes de nuevo código
- **Pandera** tiene soporte documentado para `xarray.Dataset` mediante `pandera.xarray.DatasetSchema`: comprobar nombres, dimensiones, tipos, atributos, esquemas y checks. Documentación oficial https://pandera.readthedocs.io/en/stable/xarray_guide/dataset_schema.html; usar versión instalable en CI y registrar versión; licencia MIT/BSD por verificar del paquete exacto. No dar por probado su funcionamiento con nuestro esquema hasta ejecutar el ensayo.
- **MatterGrid** (`matter_v0.py`) ya comprueba por celda positividad, densidad y capacidad, y H1 proporciona `validate_and_restore`. Reutilizarlo como **oráculo de propiedades físicas mínimas** en lugar de reimplementarlas.
- **NumPy `copyto`**: posible publicación in-place de un candidato preparado fuera del owner; es una operación de datos, NO una transacción concurrente ni un motor nuevo.

## Diseño preregistrado
1. Base fija: `dataset_projection(oracle())` de H1, dos materiales A/B y niveles 0/1, Landlab fields vinculados por H2. Guardar suma de masa de **todos los niveles**, snapshot del tensor y de campos Landlab, metadatos.
2. Validar el tensor **completo**, no solo nivel0: esquema `Pandera.DatasetSchema` sobre `material_mass(material, level, y, x)`, `material_density(material)`, dimensiones 2×2×2×3, atributos y unidades. Exigir nombres de materiales exactos, cantidades finitas no negativas, densidades finitas positivas, y ocupación `sum(mass/density)<=1m³` por celda y nivel. Contrastar cada nivel con `validate_and_restore` sin cambiarlo.
3. Preparar cambios **en copia**, validar antes de publicar. Una transferencia *manual* de **0.1 kg A** desde celda (x2,y1,nivel0) a la **misma celda nivel1** debe mantener masa total A/B. Luego publicar **una vez** con `np.copyto(original,validated_candidate)`, y comprobar que las vistas Landlab siguen enlazadas y muestran el cambio de la capa 0. No implicar física vertical.
4. Controles NEGATIVOS, cada uno sobre copia independiente: (a) masa negativa solo nivel1, (b) sobrecapacidad solo nivel1, (c) NaN nivel1, (d) creación no autorizada de 0.05kg en nivel1 sin quitar en origen, (e) unidad de masa incorrecta `g` en metadata, (f) variable de masa con dimensiones permutadas, (g) nombres de materiales inesperados. Todos deben rechazarse; baseline en memoria y campos Landlab deben quedar intactos.
5. Registro de versiones Pandera/xarray/Landlab/NumPy, duración descriptiva de validación/commit, estado inicial/final por hash, tests de negativos. Si alguna prueba falla no disminuir tolerancia. Mantener original (sin extensión de física ni mundo gráfico).
6. **No asegurar** que `np.copyto` represente transacción atómica multihilo; el objetivo es **commit de una candidata validada en un solo escritor serial**, solo dentro de este ensayo.

## Criterio de aceptación
H3 aprueba si ambas rutas de validación (Pandera + oráculo MatterGrid) aceptan base y transferencia válida, rechazan todas las corrupciones indicadas, ninguna corrupción toca el owner, el commit conserva masa global y `np.shares_memory` Landlab↔xarray persiste. Si Pandera no soporta cierta propiedad, registrar brecha explícita; no sustituir una negativa por un `assert True`.

## Puerta de salida E1
Con H1/H2/H3, elaborar **ADR de representación experimental**: cuál es el owner provisional, quién valida, cómo se actualiza, qué no representa, costo de dependencia y qué falta antes de asignar volúmenes y materiales generales. No elegir un motor físico nuevo ni marcar terminadas las etapas 2–8.
