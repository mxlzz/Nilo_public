# Etapa2 — H17. Gravedad libre/bloqueada con publicación de cinemática

**2026-11-22. H17 APROBADA** bajo criterios originales, sin cierre de etapa2 ni elección de motor universal. [Protocolo H17](ETAPA_2_H17_PROTOCOLO_GRAVEDAD_OWNER.md), [código](experiments/probe_e2_h17_rigid_owner.py), [GitHub Actions 45059850320 — SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45059850320). Ejecutada en Python3.11.18, PyBullet3.2.7, xarray2026.9.0, NumPy2.4.6.

## Configuración y observaciones

Dos cubos rígidos 1m³ cada uno. **A móvil2kg** con centro inicial z2m. **B fijo8kg** con centro z0,5m, apoyado en suelo idealizado, colocado debajo o fuera de la trayectoria de A. Bullet3D integró720 pasos `dt=1/240s`, gravedad−9,81 o0. B se modeló estático (`baseMass=0` como restricción del solver, **no** ausencia de su inventario material8kg); el owner canónico conserva A2+B8=10kg y volumen total2m³.

- **Con espacio libre:** A descendió **1,5000111652875174m**, terminó en centro z**0,49998883471248257m** sobre suelo; contacto normal con suelo fuerza positiva, máxima instantánea1394,25N.
- **Con B debajo:** A descendió **0,5000113934325197m**, terminó en centro z**1,4999886065674803m** apoyado en B; fuerza de contacto máxima486,05N, sin atravesarlo.
- **Sin gravedad:** A permaneció exactamente en centro z2m, sin movimiento/contactos de fuerza positiva.
- **Reproducibilidad:** Bullet DIRECT y sampling cada60 pasos de tres segundos físicos repitieron exactamente posiciones/velocidades, escenario y propiedades. Las posiciones/velocidades finales del solver pasaron por **candidato validado**, luego se publicaron por `np.copyto` en el mismo `xarray.Dataset`; no se conservó un segundo propietario Bullet. Regresión verificó 10kg/2m³ de materiales y obstáculos sin solapamiento imposible. 
- **18 controles inválidos** (9 por caso libre y bloqueado) rechazados sin mutar owner: material creado/negativo, geometría superpuesta, cuerpo fijo movido, etiqueta, unidades y atributos de masa/cinemática. **NetCDF1308bytes** restauró estado material, pos/vel, atributos, tiempo3s, hashes. Owner libre final SHA `bbba7f081380efb422e5ef6fb1c58878d27dc2bbc6040097e53a865c1ed1b785`.

## Brecha cubierta y límites

H7/H8 solo usaban Bullet como cálculo y no publicaban posición+velocidad en un owner material; H17 sí comprueba **una transición de estado cinemático físico auditable** desde proveedor hacia inventario único, diferenciando obstáculo y g0, sin desarrollar nuevas leyes.

**NO:** creación autónoma de la escena (obstáculo precolocado), energía potencial/kinética ni disipación termal contabilizadas, colapso de estructura o roca deformable, movimiento de fluidos, enlace con ROI espacial H5, reposición de orientación/impulsos Bullet, checkpoint reanudable del solver, ni dinámica ambiental persistente. Dos cubos de formas predefinidas son banco de pruebas, no criterio de emergencia. Contactos de gran fuerza instantánea en motor rígido no son cargas geotécnicas calibradas.

## Próximo gate etapa2

El plan exige además **respuesta diferencial a un gradiente de transporte**, no solo a gravedad/obstáculo. H9 Landlab transportó suelo por pendiente, pero su control previo era K=0, no alteración de pendiente con K fijo. Próximo ensayo selectivo: variar exclusivamente inclinación geomorfológica con mismos K/suelo/salida, usar funciones H9 sin nuevo solver, medir descarga y balance. Luego auditar gate etapa2; no crear orquestador ni combinar fenómenos arbitrariamente para aumentar la cantidad de experimentos.
