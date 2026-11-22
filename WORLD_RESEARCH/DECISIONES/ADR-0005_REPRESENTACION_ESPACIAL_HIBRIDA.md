# ADR-0005 — Representación espacial híbrida como HIPÓTESIS PROVISIONAL, no motor definitivo

**Fecha:** 2026-11-22
**Estado:** DECISIÓN EXPERIMENTAL REVERSIBLE, limitada a siguientes pruebas de materia; la **etapa 1 permanece ABIERTA**. No modificar `main` ni NeuroLab.
**Rector:** `BASES_Y_HOJA_DE_RUTA.md` apartados 1–6 y `PROCEDIMIENTO_Y_AUDITORIA.md`.
**Antecedentes:** `ADR-0003_CIERRE_ETAPA_0_BASES_MODULARES.md`, `ADR-0004_PROPIEDAD_INTEGRIDAD_ESTADO.md`.
**Resultados:** [H4 geometría](https://github.com/mxlzz/Nilo_public/actions/runs/45034754946), [H5 owner particionado](https://github.com/mxlzz/Nilo_public/actions/runs/45035061531), [H6 frontera variable](https://github.com/mxlzz/Nilo_public/actions/runs/45035363232).

## Cuál es la decisión y por qué
**NO** usar un único heightfield z(x,y) como representación completa de la materia si aspiramos a cavidades, varias capas de sólidos independientes o estructuras con aire debajo. **NO** imponer un volumen denso a todo el territorio en esta fase. En pruebas futuras, **preferir datos superficiales para fenómenos ambientales de gran extensión y regiones volumétricas locales para geometría que el heightfield no puede conservar**, con único propietario por región y raster de alturas como observación/derivado, nunca inventario duplicado.

Se trata de **una propuesta de datos en laboratorio**, no de decidir que el futuro mundo sea necesariamente 3D, voxelado, ni que Landlab gobierne dinámica material de cavidades. El requisito científico es dar cabida a configuraciones no prediseñadas cuando sea necesario, no fabricar cuevas o puentes explícitos para simular «emergencia».

## Evidencia decisiva
1. **H4:** bloque completo 288m³ y otro con vacío interior16m³ → **idéntico heightfield**, distinta masa/volumen/topología. Un puente estático de 96 vóxeles se confunde con 160 si se rellena su silueta de alturas. Trimesh representa ocupación densa/dispersa; xarray conserva masa A/B, porque Trimesh binario no conoce sus identidades. Un ejemplo 96×96×64 con 0.5% de ocupación usa 75KB de payload disperso vs 590KB denso, **no cifra de RAM total ni benchmark de solver**.
2. **H5:** superficie 12×8 + dominio volumétrico 8×6×7, propietarios exclusivos en un Dataset. Excavar manualmente 16 vóxeles interiores retira 32kg sin alterar superficie; quitar otros 2kg del techo cambia exactamente una cota. Controles rechazaron balances incompletos, inventario duplicado y cache de altura obsoleta; NetCDF restauró propietarios y derivaciones.
3. **H6:** seis columnas compactas de superficie se pasaron a ROI 3D transfiriendo 24kg, sin cambio de altura ni masa global. Una franja compacta se pudo revertir sin pérdida y conservó el hash original, mientras un vacío interior impidió degradar la región a una altura. Se hicieron controles de doble owner y de pérdida de material.
4. **H1–H3:** alias y owner en xarray/NumPy compartibles con Landlab bajo topología compatible, con riesgo de puntero obsoleto si se reemplaza variable; Pandera sirve para validación estructural ocasional, no como motor ni validador a cada tick.

## Alcance técnico
- **Landlab**: proveedor candidato de ecuaciones de superficie/terreno ya probadas; la elevación derivada de ROI **no constituye sincronización física automática** con sus solvers ni implica compatibilidad sin tests de intercambio de masa/sedimento.
- **xarray/NumPy**: representaciones de datos y composición en el laboratorio. Para mezcla de regiones, **propietario único por región y magnitud**; en vez de forzar una única matriz global (`ADR-0004` H1–H3), H5–H6 usaron dos variables de masa con dominios excluyentes y una máscara que las relaciona. Esta **ampliación deliberada del ADR-0004** preserva su principio de no duplicación, pero ajusta la forma del owner para dominios de dimensión diferente. No cambiar ADR-0004 retroactivamente: mantener la trazabilidad.
- **Trimesh MIT**: geometría y consultas/serialización de ocupación; por sí solo no contiene composición ni simula estabilidad, evolución, cohesión o masa.
- **OpenVDB Apache-2.0**: alternativa real si crecen muchas regiones volumétricas dispersas y hay evidencia de costos prohibitivos; NO probada su integración o distribución Python en este entorno. **Bullet/pybullet**: dinámica de sólidos y colisiones para etapas posteriores, no reemplaza ecosistemas. **Taichi**: computación/partículas, no física por sí sola.
- **Ecosystem Explorer**: referente de experiencia de mundo autónomo en navegador, no código públicamente reutilizable verificado.
- **Etapas 2–8**: no se dan por completadas por los ensayos de representación.

## Límites/errores a evitar
- La prueba H4 **dibujó** cavidad y puente; ninguno emergió por leyes ni soportó cargas.
- H5–H6 son migraciones de estado **manuales** sobre región rectangular homogénea en el exterior; no diseñan un algoritmo adaptativo ni un esquema eficiente para millones de vóxeles.
- Un campo de alturas no mide masa en regiones volumétricas: derivarlo de ROI y luego contabilizar el sólido como columna llena crea materia fantasma.
- Un Dataset con `z` no es motor físico tridimensional, ni una representación completa de propiedades térmicas/composición/energía. Los valores de densidad (A=2kg/m³, B=1kg/m³) son solo **unidades abstractas de prueba** y no fijan un modelo material general.
- `numpy.copyto` no garantiza actualizaciones atómicas concurrentes. No implementar un orquestador paralelo sin prueba de necesidad.

## Próximo gate de valor científico (evitar ingeniería prematura)
Regresar al **núcleo de etapa 1: definición de propiedades e invariantes materiales mínimas**. La hoja de ruta habla de masa/volumen/energía/composición y transformación trazable; los ensayos H1–H6 solo verificaron masa/volumen/identidad y **no energía ni respuesta física autónoma**. Antes de añadir un campo de energía, precisar qué fenómeno desea estudiar y buscar componentes existentes para resolverlo; no imponer termodinámica como decoración.

Elegir una primera **ley local ya implementada** para etapa 2 entre contacto/soporte granular (Sandspiel/The Powder Toy/Bullet) o transporte simple, con test diferencial y conservación, y comprobar cómo lee/escribe el estado compartido sin violar el contrato. La elección no se hace aún. No añadir clima, vegetación, interfaz, habitantes ni agentes mientras la representación siga sin un caso físico demostrado.

## Gate de revisión
Reabrir si resulta innecesario conservar topologías bajo tierra, si aparecen cuerpos/materiales no voxelizables, si el acoplamiento Landlab↔ROI necesita doble conteo, si el coste es excesivo, si OpenVDB/Bullet/GeoTaichi resuelve mejor un requisito real, o si la novedad de las configuraciones no puede demostrarse más allá de formas prefijadas.

**Dictamen:** los ensayos H1–H6 dan evidencia suficiente de una **infraestructura de datos candidata**. **No justifican crear un motor físico nuevo ni afirmar que ya existe el mundo autónomo**. La etapa 1 continúa, con nuevo trabajo centrado en mecanismos y preguntas científicas, no en más cambios cosméticos de formatos.
