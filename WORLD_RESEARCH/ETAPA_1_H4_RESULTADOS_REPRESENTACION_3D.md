# Etapa 1 — H4: resultados de representabilidad espacial 2.5D/3D

**Fecha:** 2026-11-22. **Estado:** H4 APROBADA bajo alcance geométrico, **NO** selección definitiva de sustrato. E1 abierta.
**Protocolo preregistrado:** `ETAPA_1_H4_PROTOCOLO_REPRESENTACION_3D.md`.
**Código:** `experiments/probe_e1_spatial_geometry.py`.
**CI verificada:** https://github.com/mxlzz/Nilo_public/actions/runs/45034754946 (**SUCCESS**).
**Entorno observado:** Python 3.13.18, NumPy 2.5.5, Trimesh 5.2.2 (MIT), SciPy 1.18.1, xarray 2026.9.0; volumen nominal de cada vóxel 1m³, sin propiedades mecánicas.

## Pruebas y evidencia
1. **H4a, altura no inyectiva:** bloque completo de 288m³ y bloque con cavidad interna de 16m³ (sólido 272m³), misma superficie `max(z sólido)` en todas las columnas, pero hashes 3D diferentes. La cámara es un componente de vacío 6-conectado **sin contacto con la frontera externa**, con 16 vóxeles. Reconstruir un volumen lleno desde las alturas crea 16m³ de sólido ficticio. Si el material abstracto tuviera densidad2kg/m³, eso falsearía el inventario en **32kg**. **Conclusión demostrada:** un heightfield de techo único no alcanza para distinguir esos estados.
2. **H4b, geometría estática de puente:** dos pilares y viga ocupan 96 vóxeles, forman un componente sólido conectado, con techo ocupado en z=4 y aire en z=2 bajo la viga. Reconstrucción por columnas = 160, **64 falsas ocupaciones**. Se construyó **por prescripción**: no existe prueba de carga, cohesión, equilibrio, estabilidad, deformación ni surgimiento emergente.
3. **H4c, identidad material separada de ocupación:** owner xarray `(material,z,y,x)=(2,7,8,12)` con A densidad2 y B densidad1; geometría ocupada igual a escena puente Trimesh `VoxelGrid(DenseEncoding)` y `SparseEncoding.from_dense`. Inventario inicial A=186kg, B=3kg, capacidad de un voxel por celda no superada; una escena alternativa con idéntica ocupación pero material A=192kg, B=0kg **es indistinguible como ocupación Trimesh**, no como inventario químico/material. NetCDF conserva cantidades y unidades exactamente, tamaño **11,632 bytes**. La diferencia de inventario es entre estados iniciales alternativos, NO creación de masa por transformación simulada.
4. **H4d, codificación dispersa:** escena 96×96×64 con 3,000 vóxeles ocupados (fracción ~0.00509) y semilla 7321; representación dense bool payload 589,824 bytes; índices+valores sparse payload **75,000 bytes**, aprox. 12.72% del dense. `sparse.dense` recuperó la misma geometría sin pérdida. **Métrica LIMITADA A PAYLOAD**: no incluye objetos Trimesh/SciPy, allocator, metadatos de material ni costo de física; no es benchmark de RAM real de simulador.

## Decisión
- **Rechazar la hipótesis de que la superficie z(x,y) sea el estado geométrico completo del universo**, si se espera cavidad, puente, material interior o sólido separado verticalmente.
- **Mantener Landlab como superficie ambiental posible**, no como dueño de todas las celdas volumétricas; el resultado no cuestiona sus modelos de cuencas.
- **Conservar xarray/NumPy como owner candidato de composición** y Trimesh como biblioteca de geometría/visualización/consultas. Trimesh no debe reemplazar el inventario material, porque codificar solo ocupado/vacío pierde etiquetas.
- **OpenVDB como candidata para volumen disperso a mayor escala** (requiere evaluar dependencia/integración, no se ejecutó); Open3D, Bullet y Taichi siguen como alternativas parciales, no probadas aquí.
- **No seleccionar una representación full-voxel del mapa** sin observar costo total y necesidades 3D. La lectura causal más prudente es una **hipótesis de superficie ambiental + regiones locales volumétricas** donde la pregunta científica lo exija.

## Prueba siguiente condicionada (E1/H5)
Antes de seleccionar esa representación híbrida, confirmar que un raster de superficie y un dominio volumétrico local pueden compartir información **sin que ambos sean propietarios de la misma masa ni de un campo z incompatible**, y que un cambio interior que NO altera la altura visible se detecta por balance global. No desarrollar nuevas leyes, solo un contrato de intercambio y controles de doble conteo. E1 ABIERTA, etapa 2 no iniciada.
