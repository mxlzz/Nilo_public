# Etapa 1 — H6: migración reversible de una frontera entre altura y volumen

**Fecha:** 2026-11-22. **Estado:** PROTOCOLO previo a código. Dependencia H4 (heightfield pierde cavidades) y H5 (masa con propietario exclusivo por región). **No hay física nueva**.

## Pregunta alineada
Un mundo autónomo no puede garantizar que todos los huecos, objetos y transformaciones futuros ocurran dentro de una ROI fija. Si elegimos superficie + volumen local, debe existir una migración de **representación** cuando una región que antes era una columna homogénea pasa a necesitar información 3D. La reversión de región 3D a altura **solo puede aceptarse si es realmente invertible**, sin ocultar una cavidad.

## Soluciones existentes y enfoque mínimo
Usar `xarray.Dataset.reindex` y selecciones para ampliar/recortar una coordenada `roi_x` y `NumPy` para migrar cantidades explícitas; Landlab proporciona solo un campo de alturas derivado. No implementar sistema de chunks, resolución adaptativa, simulador 3D, gravedad ni gestión de eventos. OpenVDB ofrece volúmenes dispersos dinámicos pero sin prueba de interoperabilidad con nuestro inventario y sin garantía de facilidad de instalación Python3.13; considerarlo si el problema escala, no antes de este contrato.

## Escenario
Desde el estado H5 de 12×8 columnas, ROI x=[2,10), y=[1,7), 7 niveles. Crear la cavidad H5 retirando 16 vóxeles A (32kg), con su salida registrada. Inventario inicial total A762kg, B3kg; luego de esa salida A730kg, B3kg. La frontera exterior inmediata x=10, y=1..6 es una columna compacta de A de altura2m, **4kg por columna**, hoy propiedad del campo 2D. Expansión prevista de ROI a x=[2,11) para incluir esas seis columnas.

## Controles y criterios fijados antes del ensayo
1. **Promoción a volumen (x=10):** ampliar el campo `roi_voxel_mass` por `reindex` y transferir exactamente A=4kg por columna (24kg en total) desde `outside_column_mass` a dos vóxeles A de 2kg cada uno en niveles z0,z1. Actualizar la máscara de ownership. Validador genérico de tamaños y etiquetas debe exigir exclusión de propietarios, capacidad y inventario global por especie A730,B3. La altura física sigue idéntica en **todas** las columnas, porque la representación cambia pero el mundo no.
2. **Cavidad precedente preservada:** ROI preexistente conserva exactamente estado de cavidad de 16m³; un voxel interior no se rellena durante la migración. NetCDF roundtrip del nuevo estado y derivación de altura tras recarga no cambian nada.
3. **Controles negativos:** (a) ampliar ROI y agregar 24kg a voxel **sin quitar** 24kg de exterior debe ser rechazado por doble propiedad; (b) quitar materia exterior y no depositarla en voxel debe ser rechazado por balance; (c) intentar degradar a altura una columna con hueco interior (por ejemplo x5,y3 de cavidad H4/H5) debe ser rechazado por criterio geométrico.
4. **Reversión segura:** solo la **franja agregada** x=10 que contiene columnas compactas sin vacíos ni cambios de material puede volver a altura, reponiendo sus 4kg originales por columna, reduciendo `roi_x` de 9 a 8 celdas y reconstruyendo la máscara. Inventario, máscara, geometría y altura deben quedar idénticos a la escena anterior a la promoción (el estado con cavidad). Comprobar hashes de matrices originales `outside_column_mass` y `roi_voxel_mass`.
5. **Rastreo:** reportar versiones, coordenadas, conteo ROI antes/ahora/después, masses y checks. No aplicar nueva ley; toda migración es intervención de esquema de datos y no es una cavidad que aparezca sola.

## Dictamen previsto
Si pasa, el enfoque híbrido no queda bloqueado por fronteras de **un** nivel de forma —pero NO se demuestra adaptación automática, solver acoplado, volumen infinito ni equilibrio mecánico. El resultado autoriza un **ADR de representación provisional para laboratorios**, no elección definitiva del motor físico ni cierre de etapas 2–8. Si falla, documentar cuál invariante deja de cumplirse y reevaluar OpenVDB/vóxeles globales antes de construir adaptadores mayores.
