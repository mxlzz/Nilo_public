# Etapa 1 — H7: Bullet como proveedor existente de gravedad y contacto 3D

**Fecha:** 2026-11-22. **Dictamen:** H7 APROBADA para 1 cuerpo rígido sobre frontera estática. **Etapa 1 ABIERTA; etapa 2 NO autorizada como desarrollo propio.**
**Protocolo preregistrado:** `ETAPA_1_H7_PROTOCOLO_RIGID_CONTACT_BULLET.md`.
**Arnés:** `experiments/probe_e1_bullet_rigid_contact.py`.
**CI reproducible:** https://github.com/mxlzz/Nilo_public/actions/runs/45036231904 (**SUCCESS**). Python 3.11.18, distribución PyBullet 3.2.7, xarray 2026.9.0. PyBullet es wrapper oficial del motor Bullet, licencia upstream zlib https://github.com/bulletphysics/bullet3/blob/master/LICENSE.txt. No se modificó código de Bullet.

## Pregunta y contrato
¿Puede un solver 3D existente **leer masa y geometría declaradas**, resolver caída/contacto de una caja rígida y devolver cinemática sin que un segundo inventario empiece a crear materia?

Se usó un `xarray.Dataset` con material A=2kg y B=0kg, volumen geométrico1m³, densidades específicas de referencia A2kg/m³ y B1kg/m³, densidad efectiva de cuerpo 2kg/m³. El arnés valida unidades, signos, capacidad y etiquetas; Bullet recibe **2kg como parámetro cacheado del cuerpo**, xarray sigue como única autoridad de composición. Bullet es owner temporal de posiciones/velocidades; observaciones guardadas fuera de él NO son otro integrador. Piso sin masa material es condición de borde geométrica.

## Resultados 480 pasos a dt=1/240s, box 1m, centro inicial z=3m
- **Gravedad -9.81m/s², piso en z=0:** centro final **0.4999888412177902m**, velocidad vertical final **3.28×10⁻¹²m/s**, **2 contactos** al último paso; cumple z∈[.45,.60], descenso>2m, v<.1m/s.
- **Gravedad 0 con piso:** centro exacto **3m**, velocidad0, ningún contacto. Control de causalidad: sin fuerza no se simula caída.
- **Gravedad -9.81 sin piso:** centro final **−16.660875m**, velocidad final−19.62m/s, sin contacto. La diferencia es consecuencia de la presencia de un cuerpo estático en el solver, no del arnés.
- **Repetición:** trazas muestreadas de tiempo/posición/velocidad coinciden exactamente en dos instancias DIRECT separadas, contactos finales iguales.
- **Inventario:** `getDynamicsInfo` informó masa 2kg, mismo valor de owner; hash de matriz de masas/densidades idéntico antes/después de 3 escenarios y replay. Guardado/lectura NetCDF **876bytes** reprodujo etiquetas, unidades y masa.
- **Controles negativos:** el validador externo rechazó masa negativa, densidad nula, exceso de capacidad y unidades de masa incompatibles.
- Tiempo de `stepSimulation` 480 ticks por caso: ~2.24ms con piso; ~1.10ms con g=0; ~0.90ms en caída libre, un cubo en runner. No extrapolar.

## Evaluación crítica
**Aprobado:** una ley de contacto/soporte tridimensional ya implementada puede operar con condiciones obtenidas de un inventario validado. No se desarrolló gravedad, integrador ni colisiones. Permite considerar Bullet para cuerpos discretos rígidos, sin asumir que sea necesario simular toda la materia como cuerpos separados.

**No demostrado:** transferencia de geometría volumétrica real H5 al solver; contacto de estructuras con cavidades; erosión granular/deformable; integración a Landlab; evolución de topología; transferencia conservativa de materia entre regiones; conservación de energía/termodinámica (el contacto disipativo no deposita energía explícita como calor); rendimiento a escala; Python3.13, licencia de cada activo externo.

**Siguiente ensayo recomendado solo si agrega valor:** conectar la geometría ROI de H5 a los colliders estáticos de Bullet y hacer que un cuerpo de material contabilizado en el mismo Dataset se apoye dentro de una cavidad que el heightfield rellena falsamente. Contrastar contra superficie identica sin cavidad y registrar qué entidad es owner de cada masa; reutilizar `GEOM_BOX`/Bullet y xarray, sin implementar solver. Así H8 comprobaría que la elección híbrida tiene efecto sobre una **interacción real**, no solo almacenamiento. Etapa1 sigue abierta.
