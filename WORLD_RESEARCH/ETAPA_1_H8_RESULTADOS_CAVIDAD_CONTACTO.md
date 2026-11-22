# Etapa 1 — H8: contacto físico en una cavidad, balance y transferencia entre runtimes

**Fecha:** 2026-11-22. **Dictamen:** H8 **APROBADA** para colisión con geometría volumétrica local. **Etapa 1 general ABIERTA**, no motor definitivo, no etapa 2 de materiales deformables.
**Plan preregistrado y enmiendas auditables:** `ETAPA_1_H8_PROTOCOLO_CAVIDAD_CONTACTO.md`.
**Fuente de datos Python3.13:** `experiments/probe_e1_bullet_cavity_prepare.py`, reutiliza H5.
**Solver externo Python3.11:** `experiments/probe_e1_bullet_cavity_owner.py`, llama Bullet DIRECT sin implementar física.
**Workflow:** `.github/workflows/world-e1-bullet-cavity.yml`.
**CI final reproducible:** https://github.com/mxlzz/Nilo_public/actions/runs/45037191905 (**SUCCESS**).

## Pregunta respondida
¿Puede una región volumétrica de nuestro estado material servir para una **interacción física real** que una superficie de alturas equivalente no pueda representar, conservando la propiedad e inventario de la materia, sin inventar un motor nuevo?

**Sí, en un caso estático de cavidad con cuerpo rígido.** Un bloque macizo y el mismo con un hueco cerrado de 16m³ comparten exactamente el heightfield, pero solo el segundo admite la posición inicial de un cubo de 1m dentro de la cámara (en el primero hay sólido allí). El bloque se construyó por prescripción, no por erosión espontánea.

## Ejecución real
- Estado inicial H5: **A762kg + B3kg**; ROI con 288 voxeles llenos. Remoción manual de 16 voxeles interiores A (=32kg) produce **272 voxeles estáticos**. Una de las 16 unidades extraídas (A2kg, volumen 1m³) se registra como `rigid_body_mass` en **el mismo xarray Dataset**; los otros 30kg A se anotan como **sumidero externo explícito**.
- Saldo: estáticos A730kg+B3kg, móvil A2kg, salida A30kg; ecuación A730+2+30=762kg. El terreno exterior de H5 permanece en inventario, aunque la prueba de contacto construye colliders solo para los voxeles ROI.
- H5 en **Python3.13.18 / Landlab2.11.0** creó y validó NetCDF **8,952 bytes**, con hash SHA256 de material `caec2423d6b9f7c7ea166f918fb972eee51a128ae7b2110a31317958770df87b` y archivo `bc18a4a8a1902389c335d8960a570106321970fbe18d11c6464fda0db75b65ed`.
- Otro proceso **Python3.11.18 / PyBullet3.2.7** verificó hashes, leyó NetCDF sin importar Landlab, validó coordenadas y cantidades, creó **272 colliders estáticos de 1m** con masa Bullet cero como **geometría de frontera** y un único cuerpo dinámico de masa2kg como caché del owner xarray.
- Cubo móvil con centro inicial `(5.5,3.5,3.4)m`, lado1m, `g=-9.81m/s²`, dt1/240s, **360 pasos**. Centro final z=**2.499988271068438m**, velocidad vertical **−3.77534e−5m/s**, **4 contactos efectivos con piso de cámara z=1** (superficie a altura2m), fuerza normal máxima del contacto de piso **5.50734N**. Hubo contactos laterales por confinamiento.
- Control de gravedad0: centro z **3.4m exacto**, vz=0, **0 contactos de piso**; 8 contactos geométricos de pared lateral **con fuerza cero**. Replay del caso con gravedad reprodujo exactamente las muestras de posición/velocidad y contactos.
- Los controles negativos rechazaron materia duplicada y salida externa no declarada. El inventario se mantuvo inalterado mientras Bullet ejecutaba sus pasos, y el dataset persistió/restauró exactamente mediante NetCDF.

## Historia de fallos — NO ocultar ni contar como físico un error de arnés
1. https://github.com/mxlzz/Nilo_public/actions/runs/45036561189 — **FAIL antes de física**: import de Landlab2.11 en Python3.11 arrastró `requireit.py` con sintaxis `def require_instance[T]` de Python>=3.12. Solución razonada antes de cambiar código: preparar estado en Python3.13 y consumir NetCDF en PyBullet3.11. No se forzó compilación de Bullet en3.13 ni se degradó Landlab.
2. https://github.com/mxlzz/Nilo_public/actions/runs/45036835382 — **FAIL en aserción de control sin gravedad**: el arnés exigía no ver ningún contacto geométrico aun cuando el cubo toca pared de la cavidad; el producer sí había verificado geometría/hash/presupuesto. Faltaba diagnóstico de superficie.
3. https://github.com/mxlzz/Nilo_public/actions/runs/45037035274 — **FAIL diagnóstico deliberado**, sin modificar valores de simulación. Registró contacto lateral normal [0,1,0], fuerza **0 N**, distancia −0.0m, z/vz sin gravedad inmutables; con g, contacto verdadero de piso con fuerza>0 y apoyo a z2.5.
4. Se documentó **antes del ensayo definitivo** sustituir el control sin fundamento «0 contactos de cualquier clase» por un criterio físicamente identificable: **0 contactos con el piso y 0 fuerzas normales significativas sin gravedad**; exigir fuerza vertical positiva con gravedad. Sin tocar cota, cuerpo, voxel, masa, paso ni umbrales. Corrida final https://github.com/mxlzz/Nilo_public/actions/runs/45037191905 **SUCCESS**.

## Juicio crítico
**Demostrado:** la topología tridimensional de una región local afecta la **validez geométrica de la colocación y el contacto dinámico** en un motor existente. Las cantidades A/B conservan owner y ledger aun cuando el solver tenga parámetros de masa cacheados; la interfaz NetCDF permite dos runtimes Python diferentes con contenido y checksum verificados.

**No demostrado:** formación espontánea de cuevas, estabilidad mecánica de techo de roca bajo carga, excavación física, conversión dinámica de voxeles a cuerpos, ruptura/fragmentación, sedimentos y fluidos, continuidad con un nuevo checkpoint, coste de cientos de miles de colliders ni un modelo de energía térmica. Los 272 colliders estáticos son solo para este pequeño ensayo; **no se recomienda** 1 collider por voxel a escala del mundo.

## Implicación de arquitectura
**Mantener ADR-0005 como candidata**: macroambiente en Landlab y geometría local cuando se necesita; ahora hay evidencia de que la segunda dimensión cambia una interacción física. **No adoptar Bullet universal**: adecuado para cuerpos rígidos en este ensayo; partículas granulares, suelo deformable, cambios de fase y emergencia necesitan evaluación distinta. La separación 3.13→3.11 es una **prueba exitosa de datos** pero no un acoplamiento en tiempo real.

**Próxima puerta científica:** antes de programar más contenedores, decidir un **fenómeno de transformación/redistribución de materia** y comparar un solver granular/deformable existente (The Powder Toy/Sandspiel, GeoTaichi/DEM/MPM) con las propiedades mínimas e invariantes de la hoja de ruta. Rechazar catálogos de formas prescritas como «evolución abierta». No continuar añadiendo colliders o adaptadores por inercia.
