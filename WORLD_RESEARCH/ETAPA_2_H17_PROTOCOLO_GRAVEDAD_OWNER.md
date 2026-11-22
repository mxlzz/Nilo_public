# Etapa2 — H17. Protocolo previo: gravedad y obstáculo actualizan owner cinemático

**Fecha:** 2026-11-22. **Estado:** PRERREGISTRADO antes de código, sin CI aún. La etapa1 acaba de cerrar **solo su gate de laboratorio mínimo** ([ADR-0009](DECISIONES/ADR-0009_GATE_ETAPA_1_MINIMO.md)); la etapa2 se abre aquí. No hay autorización para un motor físico universal, fusión a main ni trabajo sobre NeuroLab.

## Objetivo y brecha causal

Etapa2, [hoja de ruta §6](BASES_Y_HOJA_DE_RUTA.md): «descenso de material móvil cuando hay hueco y no cuando está bloqueado», con cambios de un estado común y controles de gradiente. H7/H8/H10 confirmaron gravedad/contacto **en Bullet** pero el owner `xarray` material conservó solo inventario de masa, sin adoptar **posición y velocidad post-solver** como siguiente estado reproducible. H17 no repite un ensayo de cuerpos para verlos caer: pregunta si se puede **publicar y recuperar la cinemática material** íntegramente, sin crear dos dueños de posición.

**Hipótesis:** con misma materia A móvil de2kg y obstáculo B fijo8kg, retirar B del camino produce mayor descenso de A; colocar B debajo produce apoyo antes de tocar el suelo; sin gravedad no hay desplazamiento. En todos los casos se propaga el resultado Bullet por un **commit validado** a un único `xarray.Dataset`. Si el obstáculo se solapa, el solver genera penetración no admisible o la restauración no es exacta, el ensayo fracasa.

## Reutilización sin motor propio

- PyBullet3.2.7 (Bullet, zlib): [ADR-0006](DECISIONES/ADR-0006_PROVEEDOR_CONTACTO_BULLET.md), H7/H8/H10 y CI existentes justifican proveedor de **contacto rígido local**. No usar DEM, MPM ni reglas de colisión caseras.
- `xarray` y NumPy para propietario único y `NetCDF` para estado publicado. Datos mínimos `material_mass_kg(body)`, `position_m(body,xyz)`, `velocity_mps(body,xyz)`, `half_extent_m(body,xyz)`, `is_fixed(body)`. A y B son etiquetas de materia, NO tipos de objetos prefabricados; aquí las geometrías cubo son condiciones geométricas experimentales prescritas.
- **No se simula energía térmica ni se afirma conservar la energía mecánica**; Bullet con colisiones inelásticas puede disipar energía, no convertir ese faltante artificialmente en calor. Conservar **masa y cantidad de cuerpos** únicamente; la etapa2 tiene una prueba independiente de conducción térmica H14/H16, pero aún no acopla energía mecánica.

## Condiciones idénticas salvo factor explícito

- Cuerpo A cubo1×1×1m, masa2kg, centro inicial(0,0,2,0)m, velocidad(0,0,0). B cubo1×1×1m, masa real8kg en owner, **fijo a la superficie del mundo** (colisión Bullet baseMass=0 porque está sujeto); centro z0,5m, bottom z0. El suelo inmóvil global es una frontera idealizada en z0, no un inventario material adicional.
- **Libre:** B permanece en (2,5,0,0,5)m, fuera de la vertical de A; gravedad(0,0,−9,81)m/s².
- **Bloqueado:** B está bajo A, en (0,0,0,5)m; misma gravedad. A puede caer inicialmente0,5m y debe apoyarse sobre B (centro A≈1,5m). No colocar B suspendido en el vacío.
- **Ablación g0:** geometría «libre» pero g=(0,0,0). A debe permanecer en z2m sin fuerzas/contactos de apoyo.
- **Replay:** repetir el escenario libre en un segundo Bullet DIRECT con mismos parámetros. Integrar720 pasos fijos `dt=1/240s` (3s físicos). Sin gráficos ni colas de UI.
- Registrar posición/velocidad cada 60 pasos, contactos con fuerza positiva suelo vs obstáculo, z final, deltas, masa. Al final elaborar **candidato** de posiciones/velocidades sobre el owner; validar unidades, identidad, masa, exclusión volumétrica y límites; publicar con `np.copyto` sobre buffer existente.

## Gates originales, a verificar

1. **Respuesta causal:** libre A desciende `>1,2m` desde z2m, final centro z entre0,45 y0,60m, y presenta contactos de apoyo con suelo de fuerza positiva. Bloqueado A desciende entre0,3 y0,7m, final centro entre1,45 y1,60m, contactos positivos A–B, sin atravesar B ni piso. Descenso libre mayor que bloqueado por `>0,8m`.
2. **Control de gravedad:** g0 A cambia de posición `<1e-8m` y velocidad final `<1e-8m/s`, con cero fuerzas de apoyo positivas. La posición B queda constante en todos los escenarios.
3. **Propiedad y validación:** owner único contiene A2kg+B8kg y cubos volumen1m³ cada uno, etiquetas A/B, velocidades y posiciones en metros; las posiciones finales no provocan interpenetración volumétrica superior a0,02m o subsuelo superior a0,02m. Ningún mass source, unidad alterada o cuerpo perdido se autoriza. `np.copyto` actualiza ambos campos cinemáticos del owner **solo después de validar** un candidato completo. No contabilizar masa dos veces por cache de Bullet.
4. **Integridad adversarial:** al menos seis corrupciones rechazadas sin alterar owner: masa aumentada, masa negativa, unidad cm, ID adulterado, B desplazado sin permiso, cubos solapados, campo de velocidad duplicado con otra unidad o flag fijo cambiado. Reportar al menos seis válidas.
5. **Reproducibilidad y restauración:** replay libre bit-a-bit idéntico en observaciones periódicas y último estado del owner. NetCDF conserva posiciones y velocidades finales, masa, flags, extents, ids/metadata y hash exactos; recuperación seguida por un segundo episodio físico **no se exige aún** (sería gate de etapa6).
6. **No ficción experimental:** registrar `WORLD_EVAL_JSON` con versiones, parámetros y CI; no declarar que existe generación espontánea de obstáculos, deformación del bloque, conservación de energía mecánica/termal o mundo persistente autónomo. **No cerrar etapa2** a partir de H17 solo: aún debe auditarse transporte por gradiente físico y coherencia de esquemas de campo.

## Resultado admisible

**H17 APROBADA** únicamente con todos los gates1–5, y CI reproducible. Si algún criterio físico falla, conservar fallo, diagnosticar y modificar parámetros o criterios **solo en protocolo nuevo**, nunca para convertir fail en pass a posteriori. El objetivo es poner a prueba la publicación del estado cinemático real de Bullet, no ampliar el solver.
