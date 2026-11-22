# Etapa 1 — H8. Prueba mecánica decisiva de cavidad frente a mapa de alturas

**Fecha:** 2026-11-22. **Estado:** PROTOCOLO ANTES DE CÓDIGO. Depende de [H5](ETAPA_1_H5_RESULTADOS_ACOPLAMIENTO_ESTADO.md), [H7](ETAPA_1_H7_RESULTADOS_RIGID_CONTACT_BULLET.md) y `DECISIONES/ADR-0005_REPRESENTACION_ESPACIAL_HIBRIDA.md`. **No se implementa física propia** ni se considera etapa 2 completada. Objetivo: establecer si el dato 3D, y no solo su almacenamiento, cambia una predicción física con solver existente.

## Hipótesis y falsabilidad
Dos terrenos con exactamente el mismo campo superficial z(x,y) —un bloque macizo y el mismo bloque con cavidad interior cerrada de **16 vóxeles**— representan distintas posibilidades de contacto. En el mundo con cavidad, una caja rígida de 1m de lado colocada **dentro del espacio vacío** puede caer sobre su piso interno usando Bullet DIRECT. En el mundo macizo, el volumen que ocuparía esa caja **ya está ocupado**, por lo que el validador debe rechazar colocarla allí (no forzar a Bullet a resolver una interpenetración inicial inválida).

**Predicción preregistrada:** ROI estática H5 con cavidad interior z=2,3 y (x,y) global x=4..7,y=3..4; cubo móvil 1m³ en x=5.5, y=3.5 y centro z inicial3.4, velocidad0, gravedad−9.81m/s². Tras **360 pasos de 1/240s**, centro final z en **[2.45,2.60]m**, velocidad vertical absoluta <0.1m/s, contacto físico con por lo menos un collider del piso de cavidad (voxel z1). **Con gravedad0**, z permanece en3.4 ±1e-9m, sin contacto.

## Propietarios materiales y conservación, antes de iniciar solver
- Estado original H5: **A=762kg, B=3kg** en `outside_column_mass` y `roi_voxel_mass`; no hay cuerpos móviles.
- Hacer una **intervención explícita** que retira 16 voxeles de material A (=32kg) de una región completamente encerrada, no una excavación física simulada. De esos 32kg retirados, **2kg A pasan a un nuevo objeto rígido móvil** registrado como `rigid_body_mass(material,rigid_body)` en el MISMO `xarray.Dataset`; **30kg A salen del sistema material** como `external_sinks_A_kg` declarada en metadata/ledger. El inventario tras preparar el escenario es estático A730kg+B3kg, cuerpo A2kg, sumidero A30kg; se comprueba **730+2+30=762kg A**.
- Bullet recibe los **2kg del body desde el owner**. Los 272 voxeles sólidos ROI se convierten en proxies de colisión estáticos `GEOM_BOX`, `baseMass=0` para no representar otra reserva material en el motor; las propiedades materiales y la cuenta de B permanecen exclusivamente en xarray. Bullet es autoridad de la cinemática de la caja hasta terminar; no se simula movimiento/deformación del terreno.
- No contar el parámetro mass cache de Bullet como segundo inventario. No sumar `getDynamicsInfo` a los kilos de `xarray`.

## Plan de pruebas
1. **Control geométrico discriminante:** comparar mundo macizo vs cavidad con `derive_heights` H5 y exigir igualdad completa. Verificar **16 voxeles desocupados** solo en cavidad y que el espacio inicial de la caja cabe sin intersecar el sólido. El mismo espacio en el mundo macizo debe ser rechazado por **ocupación inicial**. No construir otro mundo plano ni un algoritmo de tallado.
2. **Dinámica positiva:** pasar todos los sólidos ROI a cuerpos estáticos de Bullet (collider de 1m por voxel) y crear 1 caja móvil de masa2kg en la cavidad. Verificar apoyo z∈[2.45,2.60] tras 360 pasos, contacto final con cuerpos de la capa z=1, velocidad |vz|<.1. El piso físico real está a z=2m; el cubo de 1m debería tener centro z≈2.5.
3. **Ablación:** misma geometría/material, gravedad0 => z=3.4 y sin contactos. **Replay:** repetir escena de gravedad original en otro contexto DIRECT y exigir trayectoria muestreada bit a bit igual.
4. **Balances y validación:** xarray conserva masa de ROI+exterior+objeto y ledger de 30kg de salida; la masa cacheada en Bullet coincide con 2kg. Rechazar doble contabilización del cuerpo en la ROI o salida externa no declarada. La materia **no cambia** durante una simulación donde el terreno es fijo y el cuerpo rígido no se transforma.
5. **Persistencia:** NetCDF del owner material con el ledger y el cuerpo preserva exactamente datos, unidades y ROI. La trayectoria cinemática es una observación del solver y **no queda registrada como evolución volumétrica**; almacenar checkpoint completo del solver requiere otro ensayo.
6. **Regresión:** no cambiar fórmulas ni modelos H5, no inventar dinámica de voxeles, no activar modelos térmicos o fricción compleja; usar solo `GEOM_BOX`, `stepSimulation` y contactos de Bullet. Registrar versiones e incertidumbre de discretización.

## Gate
H8 aprobada si el dato volumétrico causa una diferencia clara de **validez geométrica** frente al mapa de alturas y permite apoyo físico coherente en un hueco oculto, con controles de gravedad, replay y balance de masa. Esto no demuestra que las cuevas se formen de manera autónoma, sean estables bajo resistencia del terreno, ni que sea viable representar miles de bloques como colliders separados. Antes de diseñar un generador de cavidades o estabilidad de roca, estudiar motores existentes para materiales deformables si la pregunta lo requiere.

**Si falla** por colisiones entre cajas estáticas coincidentes o rendimiento, diagnosticar configuración de colliders y considerar malla estática existente; no alterar geometría/umbrales para obtener aprobación. No tocar `main` ni NeuroLab.

## Incidencia H8.0 — incompatibilidad de dependencias, antes de entrar en física (2026-11-22)

**Primera CI FALLÓ**: https://github.com/mxlzz/Nilo_public/actions/runs/45036561189 . El fallo fue importar `landlab` en Python3.11, ya que una dependencia instalada (`requireit.py`) incluye `def require_instance[T](...)`, sintaxis de parámetros genéricos PEP695 introducida en Python 3.12; en 3.11 genera `SyntaxError: expected '('`. La primera ejecución **no alcanzó el código físico ni probó H8**, así que no corresponde atribuir el fallo a Bullet, a la cavidad ni a masa conservada.

**Enmienda de implementación documentada ANTES DE SEGUNDO INTENTO:** separar dos procesos/cargas sin parchear ni copiar bibliotecas externas:
- **Preparación en Python3.13**: generar escenario exactamente desde `probe_e1_surface_volume_partition.py` y sus funciones H5 verificadas; registrar alturas originales e idénticas, ledger de 30kg salida y 2kg en un cuerpo móvil, checksums y persistir a **NetCDF** más manifiesto pequeño JSON.
- **Dinámica en Python3.11**: abrir el estado **de datos** sin importar Landlab ni ningún objeto pickle, validar esquema/masas/geometry/sha en NumPy/xarray y construir colliders con Bullet oficial 3.2.7. Aplicar **idénticos 360 pasos, gravedad/control, posiciones y umbrales** al protocolo H8. Releer el NetCDF como segunda verificación de transporte, sin alterar inventario ni codificar física.
- **Contrato nuevo comprobable:** distinta versión de Python para generación geomorfológica y dinámica rígida con un único owner serializado por NetCDF, sin inferir que ambos motores comparten memoria ni que pueden ejecutarse sincronizados sin un adaptador futuro.
- El manifiesto registra hash del owner y dimensiones; la prueba rechaza si difieren. Los campos de posición observados por Bullet siguen separados de material; no copiar código de Landlab ni asumir compatibilidad de sus clases entre intérpretes.

**No se modifican hipótesis, geometrías ni criterios numéricos de contacto**. La separación de entornos evita degradar Landlab o compilar Bullet desde fuente solo para un ensayo. Si el intercambio falla se registra como nueva brecha de arquitectura, no se baja tolerancia.
