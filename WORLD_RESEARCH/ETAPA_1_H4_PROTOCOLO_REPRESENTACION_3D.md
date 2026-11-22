# Etapa 1 — H4: ¿es suficiente una superficie de alturas para conservar estructuras tridimensionales?

**Fecha:** 2026-11-22. **Estado:** PROTOCOLO ANTES DE IMPLEMENTAR. Depende de ADR-0003 (reutilizar antes de crear física) y ADR-0004 (owner único experimental y validación). Etapa 1 continúa abierta.

## Pregunta que responde al plan, no a una preferencia gráfica
El mundo podría necesitar cavidades, puentes/voladizos, canales subterráneos y varios materiales por columna vertical. H1–H3 solo demostraron inventario y niveles de datos; una dimensión `level` no prueba qué topologías distingue ni que una superficie con altura z(x,y) conserve toda la geometría. **H4 es una prueba de representabilidad**, no un motor de gravedad, cohesión ni movimiento.

## Alternativas existentes revisadas primero
- **Landlab**: malla 2/2.5D y campos por celda/nodo, científicamente útil para dinámica ambiental; una superficie de cotas por (x,y) no almacena vacíos interiores de un sólido. Mantenerlo para procesos macro de terreno, no como geometría volumétrica arbitraria.
- **xarray/NumPy (Apache-2.0/BSD)**: dimensiones etiquetadas y almacenamiento validado ya probado en H1–H3. Permiten `(material,z,y,x)`, pero no proporcionan por sí mismas leyes de contacto/estabilidad.
- **Trimesh MIT**: `trimesh.voxel.VoxelGrid`, `DenseEncoding` y `SparseEncoding` sobre vóxeles, de repositorio activo `https://github.com/mikedh/trimesh`; APIs oficiales `https://trimesh.org/trimesh.voxel.html`. Se probará una geometría tridimensional sin ejecutar nueva física, usando su representación de ocupación. Su VoxelGrid codifica ocupado/vacío; **no** conserva por sí solo identidad, masa y material de cada vóxel. Estos atributos siguen separados en un estado de datos.
- **OpenVDB Apache-2.0** (https://www.openvdb.org/documentation/doxygen/faq.html) contiene árboles de volumen disperso y herramientas, pero implica C++ y dependencia adicional; no asumir que se instala sencillamente en Python 3.13. Su ventaja potencial aparece en territorio volumétrico grande y poco ocupado.
- **Open3D** ofrece VoxelGrid/voxelización de mallas (https://www.open3d.org/docs/latest/tutorial/geometry/voxelization.html), pero usarlo como almacén autoritativo aún requiere una correspondencia de materiales y estado.
- **Bullet zlib** (https://github.com/bulletphysics/bullet3) es solver de cuerpos y colisiones: prueba futura de *estabilidad física*, NO fundamento para escoger una matriz de ocupación. **Taichi Apache-2.0** aporta arrays/compute de simulación; no define mecanismos físicos por sí mismo.
- No integrar de momento motores físicos 3D ni desarrollar solver propio: el test decisivo de H4 es matemático/geométrico y puede ejecutarse con NumPy + Trimesh + xarray.

## Hipótesis falsable y controles

**H4a: colisión de información en altura.** Construir dos estados sólidos sobre exactamente la misma grilla 3D (12,8,7), paso 1m, material único de densidad constante. Uno será un bloque lleno; el otro tendrá **una cámara de aire completamente encerrada** de dimensiones 4×2×2 vóxeles dentro de ese bloque. Proyectar ambos a un campo único `z_max(x,y)` de máxima cota de material. **Predicción preregistrada:** alturas son idénticas en todas las columnas, aunque la cantidad de material, los hashes volumétricos y la topología de espacios vacíos difieren. Calcular masa como cuenta de celdas materiales × densidad × volumen; el vacío resta exactamente 16m³ al sólido. Si las alturas difieren el ensayo está mal construido; si el conteo de celdas vacías no da 16, no se aprueba.

**H4b: conectividad volumétrica y geometría de puente.** Con otras condiciones iniciales, construir dos pilares y una viga sólida que los une por arriba, dejando una zona de paso libre bajo la viga (geometría estática). Comprobar por índices `(x,y,z)` que exista cubierta ocupada en `z>=4` sobre un vacío en `z=2`; proyectar a alturas y demostrar que cualquier reconstrucción ingenua de columna maciza agrega materia inexistente. Contar falsos positivos y comparar inventario. **No probar estabilidad ni deformación mecánica del puente**: la figura se dibuja como condición inicial, NO ha emergido ni ha soportado cargas bajo un solver.

**H4c: conservación de materiales en codificadores 3D.** Representar dos materiales abstractos A/B en un Dataset `(material,z,y,x)` con masa por celda y densidad del contrato H1; verificar ocupación total calculada, capacidad por vóxel (densidades ficticias del laboratorio), integridad de identidad por material y restauración de xarray/NetCDF. Proyectar ocupación a `trimesh.voxel.VoxelGrid` con codificación densa y dispersa; ambas deben recuperar **exactamente la ocupación booleana 3D**, pero la identidad material debe sobrevivir únicamente porque permanece en el owner del estado, **no** porque Trimesh tenga un campo intrínseco de composición.
- Control negativo: construir dos escenas con **idéntica ocupación booleana** pero intercambiando A/B en ciertos vóxeles; Trimesh debe considerarlas indistinguibles mientras el inventario por especie difiere. No elegir Trimesh como owner químico/material.

**H4d: almacenamiento disperso pequeño/mediano, no benchmark de ejecución física.** Calcular tamaño de un booleano denso `Nx×Ny×Nz` y representación SparseEncoding sobre escenario muy poco ocupado (96×96×64, ocupación dispersa determinista con semilla 7321). Confirmar lecturas/indices exactos, sin sobrecontar memoria Python de objeto; reportar `nbytes` del array denso y arrays internos sparse, y proporción de ocupación. No afirmar que el ratio se extrapola a memoria de toda la aplicación o da velocidad superior.

## Criterios de salida
1. Dos mundos 3D **diferentes** y con vacío cerrado de 16m³ mapean a **la misma** superficie de altura.
2. Volumen/masa calculados coherentes, sin números negativos; puente conserva por lo menos una coordenada con techo ocupado sobre espacio libre (reconstrucción por columna pierde información).
3. Codificadores Trimesh dense/sparse se recuperan sin pérdida de geometría en los casos H4; la proyección de composición a ocupación se declara no invertible y lo comprueba un control de materiales intercambiados.
4. xarray 3D multi-material NetCDF roundtrip conserva etiquetas, masa y unidades. No se reutilizan los índices de Landlab como si fueran volumen.
5. Semilla y versiones archivadas; no relajar límites por fallo del arnés. Cumplir solo indica **capacidad de almacenamiento geométrico**, no física, formación espontánea ni elección de motor universal.

## Puerta
Si H4 pasa: recomendación **representación híbrida candidata** (superficie ambiental Landlab + estructuras volumétricas locales, dueño de masa aún por determinar por escala), pendiente de medir topología y actualizaciones reales y de justificar si la profundidad del mundo exige 3D. Si H4 falla: corregir hipótesis o codificadores y no adoptar. No continuar con etapa 2 sin ADR auditable y relación con necesidad concreta.
