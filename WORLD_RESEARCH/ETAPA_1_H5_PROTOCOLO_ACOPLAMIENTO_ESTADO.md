# Etapa 1 — H5: interfaz superficie + volumen local sin doble propiedad de masa

**Fecha:** 2026-11-22. **Estado:** preregistro antes de código. Bajo `BASES_Y_HOJA_DE_RUTA.md` etapa 1, procedimiento de auditoría y `ADR-0004`. H4 demostró que un heightfield pierde cavidades y huecos bajo estructuras. **H5 prueba un contrato de geometría e inventario, NO un acople de solvers ni una ley de cambio**.

## Decisión técnica a discriminar
A. Guardar todo en campo de alturas y reconstruir columnas llenas: **no invertible** con cavidades (H4).
B. Duplicar inventario de una región en raster y volumen: riesgo de doble conteo.
C. **Representación híbrida particionada**, toda cantidad de masa tiene un único owner según región, y el raster de Landlab expone solo una **vista derivada** de elevación, NO una copia autoritativa de masa. C se prueba sin construir un mundo completo.

## Biblioteca y test mínimo
Usar solamente `xarray`, `numpy`, `scipy` (NetCDF) y `Landlab` existentes. Reutilizar concepto de matriz volumétrica y altura de H4, pero no desarrollar leyes de erosión/collision. No añadir Pandera a este ensayo porque el esquema específico es verificable con el validador de prueba y el objetivo es propiedad exclusiva; Pandera sigue aprobado como validador de frontera H3.

**Escenario** 12×8 columnas, altura potencial 7m en vóxeles 1m³. Región volumétrica local x∈[2,10), y∈[1,7), 8×6 columnas, 7 capas; exterior tiene columnas continuas de A (densidad 2kg/m³, altura 2m). ROI es bloque de A de altura6m, inicialmente macizo, con 3 vóxeles superiores B (densidad 1kg/m³) en lugar de A. En el exterior el owner es `outside_column_mass(material,y,x)`; dentro de ROI, el owner es `roi_voxel_mass(material,z,roi_y,roi_x)`. Fuera de ROI el primero puede contener materia; dentro de ROI **debe ser cero**. El segundo cubre únicamente ROI. Estado guardado como UN Dataset xarray con partición y coordenadas de ROI explícitas, fuente de materia por región sin solapamiento. Un campo de cota `topographic__elevation` en nodos interiores Landlab se calcula como **techo de columna** a partir de ese estado; es caché de lectura, no stock ni fuente de verdad.

## Pruebas preregistradas
1. **Integridad:** inventario global por A/B = masa exterior + masa interior, sin superposición. Densidades finitas positivas, cantidades finitas no negativas, ocupación por voxel <=1m³, masas exteriores coherentes con altura y densidad. Landlab expone cotas de 2m fuera y 6m dentro.
2. **Excavación interna explícita (no ley):** retirar manualmente una cavidad interior de dimensiones 4×2×2 voxeles (16m³, A=32kg) y registrar la materia retirada como **salida externa**. Cota visible Landlab debe permanecer **bit a bit igual**, mientras inventario A disminuye exactamente 32kg; presupuesto `final + removed=initial`. Control negativo: sin declarar salida, exigir que el validador del balance rechace el cambio.
3. **Remoción de superficie:** retirar manualmente A=2kg de un vóxel superior z5 en (x5,y3), con salida documentada; su cubierta restante z4 debe hacer caer solo esa cota de 6→5m, sin modificar otras columnas. La caché Landlab se regenera. Control negativo: alterar a mano el campo Landlab sin tocar owner debe ser detectable como **caché obsoleta**, y no afectar masa.
4. **Doble conteo intencional:** escribir 1kg ficticio en `outside_column_mass` dentro de ROI, sin modificar voxeles; validar que se **rechaza** por propiedad exclusiva y el candidato no se publica.
5. **Persistencia:** serializar sólo estado canónico xarray a NetCDF (no almacenar la caché Landlab), abrir en proceso lógico nuevo, regenerar raster y verificar igualdad de cantidades, unidades, máscara, cotas y balance final. No usar `pickle` ajeno ni asumir punteros compartidos cross process.
6. **Control de reconstrucción ingenua:** si se interpreta la altura ROI como columna maciza después de cavidad, se generan precisamente 16 vóxeles equivalentes y 32kg A falsos (con las densidades del escenario). Documentar de forma separada que no se debe usar esa reconstrucción para contabilidad.
7. **Gate de corrección:** ejecutar los controles adversariales y no alterar las hipótesis/valores durante el ensayo. Registrar versiones, estado inicial/final, semilla N/A, hashes, datos de recursos. El ensayo debe ser determinista.

## Salida
H5 aprueba **solo** si la partición sin doble propiedad conserva el inventario bajo salidas explicitadas, las variaciones interiores no se confunden con cota, la caché puede actualizarse y restaurarse, las corrupciones son rechazadas y NetCDF redondea exactamente las masas. Si falla, **no adoptar representación híbrida**: investigar API de intercambio y consistencia. Si pasa, la interfaz híbrida queda como opción para regiones con geometría volumétrica, no como requisito de hacer todo el mundo 3D.

**No demostrado:** estabilidad de puentes, origen emergente de cavidades, movimiento, erosión/flujo de agua, extensión dinámica del ROI, escalabilidad, solvers acoplados, simultaneidad ni leyes físicas de materiales. Evaluarlos requiere nuevos gates de etapas 2–5. NeuroLab fuera de alcance, `main` intacta.
