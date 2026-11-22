# ADR-0006 — Bullet como proveedor de contacto rígido local, no núcleo universal

**Fecha:** 2026-11-22
**Estado:** **DECISIÓN TÉCNICA REVERSIBLE, DE ALCANCE LIMITADO.** Etapa 1 ABIERTA; no se inicia implementación formal de etapa 2. Sin cambios a `main` ni NeuroLab.
**Objetivos:** mundo físico autónomo y persistente, reglas compartidas, estructuras no prefabricadas, no reinventar motores sin brecha probada. Ver `BASES_Y_HOJA_DE_RUTA.md` y `PROCEDIMIENTO_Y_AUDITORIA.md`.
**Antecedentes:** `ADR-0003` (reutilización), `ADR-0004` (owner), `ADR-0005` (superficie/ROI).
**Evidencias completas:** [H7](../ETAPA_1_H7_RESULTADOS_RIGID_CONTACT_BULLET.md) / [CI H7](https://github.com/mxlzz/Nilo_public/actions/runs/45036231904); [H8](../ETAPA_1_H8_RESULTADOS_CAVIDAD_CONTACTO.md) / [CI H8](https://github.com/mxlzz/Nilo_public/actions/runs/45037191905).

## Qué quedó comprobado
1. **Gravedad y contacto sin física escrita por nosotros.** Bullet DIRECT hizo caer un cubo de 1m³/2kg y lo dejó apoyado sobre plano z=0. Sin g no se movió; sin plano cayó libremente; replay exacto en un mismo entorno. Inventario xarray intacto, 4 corrupciones materiales rechazadas.
2. **Topología de cavidad afecta la física real.** Un bloque macizo y el mismo con hueco interno de 16m³ tienen alturas superficiales idénticas; solo el segundo permite ubicar una caja dentro sin interpenetración de materia. El cubo de 2kg se apoyó en el piso interno a z≈2.5m con contactos de fuerza positiva. Sin gravedad permaneció inmóvil con contactos laterales de fuerza 0N. Esta distinción no puede obtenerse de un único heightfield.
3. **Propiedad material y balance.** Del bloque H5 A762kg, quitar 32kg A de cavidad → A730 estático, A2 en cuerpo móvil de owner xarray y A30 en salida externa; A762 total contabilizado. Bullet guarda masa2kg como **parámetro de solver**, no inventario adicional. Geometría de frontera estática usa colliders sin masa física material. No hay ley de extracción/desprendimiento: la intervención se preparó manualmente y declaró sus fuentes/salidas.
4. **Interoperabilidad real entre dos entornos:** Landlab2.11 en Python3.13 produce NetCDF/JSON con hashes; PyBullet3.2.7 en Python3.11 valida contenido y ejecuta contacto. Se evita degradar Landlab o compilar pybullet en3.13. Es archivo de datos reproducible, **no acoplamiento en tiempo real** ni sincronización de estados de solver.
5. **Incidencias preservadas:** primer H8 falló por `requireit` Python3.11; el segundo por aserción físicamente inadecuada que exigía 0 contactos de cualquier tipo dentro de cavidad; el tercero diagnosticó contactos laterales fuerza0N y suelo con fuerza>0 antes de aprobar el cuarto. Enmienda del control se registró antes de ejecutarla. No se ocultan falsos positivos/fallos de arnés.

## Comparación y decisión
- **Bullet (zlib)**: **ADOPTAR SOLO COMO PROVEEDOR EXPERIMENTAL DE CONTACTO Y DINÁMICA DE SÓLIDOS RÍGIDOS** para ensayos donde el objeto es coherente como cuerpo indeformable. Tiene API headless, gravedad y contacto 3D; se comprobó, no solo se leyó. No elegir para representar *cada voxel* del mundo: H8 ya usó 272 colliders estáticos para una cámara pequeña, sin benchmark de escala.
- **Landlab (MIT)**: mantener proveedor ambiental de flujos/superficie; **no** sustituir por Bullet; ambos resuelven fenómenos diferentes. `topographic__elevation` sigue vista derivada y no conoce cavidades.
- **The Powder Toy (GPL3) / Sandspiel (MIT)**: mantener candidatos para **materia local granular/deformable**; caída/obstáculo 2D ya ensayados, no cumplen automáticamente contacto 3D o acoplamiento de masas. La licencia GPL de TPT condiciona reutilización distributiva.
- **GeoTaichi (DEMs/MPM) / otros módulos**: investigar/reutilizar antes de programar un modelo granulométrico propio si se decide simular estabilidad, avalanchas, suelo granular o fractura; se requiere comprobar disponibilidad de código, parámetros, modelos de entrada y costo. No adoptar por prestigio.
- **OpenVDB/Trimesh/xarray**: manejo de volumen y geometría; ninguno aporta por sí mismo ecuaciones mecánicas. H7/H8 no justifican migrar el owner de inventario a Bullet.

## Riesgos no resueltos y puertas científicas
1. **Física de deformación y transformación de materia.** Las cavidades de H4/H5/H8 fueron **prescritas**; todavía no existe una ley que haga excavar, fluir, fracturar o desmoronarse al terreno. No llamar «emergencia» a que Bullet deje caer un cubo.
2. **Representación volumétrica adaptativa.** H6 migró 6 columnas artificialmente, pero ningún solver hizo crecer ROI como respuesta a un fenómeno; mantenerlo como posible herramienta, no arquitectura.
3. **Energía y composición:** etapa 1 incluyó energía entre propiedades candidatas y transformaciones trazables. H7/H8 no contabilizan energía térmica ni transferencia a calor; un contacto que disipa energía mecánica no cierra el balance térmico. **No dar por completada etapa 1** ni agregar un campo «energía» sin fenómeno concreto. Una modificación de alcance requiere nueva ADR y cotejo de la hoja de ruta.
4. **Unidades/tiempo:** interconectar medioambiental y mecánico requiere frontera de tiempo, unidades y fuentes/sumideros. El puente NetCDF no es intercambio por tick, y montar una RPC/orquestador todavía no se justifica.
5. **Cargas y materiales reales:** el techo con 272 colisionadores estáticos no deformables no puede colapsar ni demostrar estabilidad de una cueva. La licencia zlib de Bullet y MIT de otras fuentes es favorable, pero revisar dependencias externas antes de distribución.
6. **Persistencia cinemática:** H7/H8 registran trayectoria por observación, pero el dueño de posiciones/velocidades del cuerpo es Bullet; restablecer dinámica entre procesos sigue sin ensayo. Checkpoints H13/H14 fueron de otros componentes, no de Bullet.

## Recomendación siguiente — preferir ciencia a infraestructura
**El primer objetivo físico nuevo debe ser una redistribución autónoma de materia granular/deformable por ley existente, no más formatos.** Antes de modificar estado, escoger 1 fenómeno observable entre granularidad/caída y una regla de transporte/sedimento, definir una cantidad conservada, comprobar la salida de un motor existente hacia el owner y hacer control sin gravedad o sin inclinación. Comparar Sandspiel/TPT/GeoTaichi y, si alguno aporta lo necesario, **adaptar solo contrato mínimo** en vez de implementar dinámica propia.

Si la pregunta científica sigue siendo solo cuerpos rígidos, Bullet basta para ese subconjunto. Si queremos que materia del mundo cambie de forma y produzca nuevas estructuras no prescritas, Bullet rígido **no prueba esa capacidad** y debe evaluarse un solver de material continuo/particulado.

**Gate:** no declarar el mundo operativo, la etapa 1 completa ni etapas 2–8 iniciadas. Mantener la investigación en rama aislada y auditable hasta demostrar mecanismo adicional de materia que justifique ampliar el motor.
