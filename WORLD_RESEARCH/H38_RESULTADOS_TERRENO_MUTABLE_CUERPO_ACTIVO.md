# H38 — Resultado negativo: el raycast actualiza el relieve, el contacto no

**2026-11-23 local. H38 NO APROBADA.** [Protocolo](H38_PROTOCOLO_TERRENO_MUTABLE_CUERPO_ACTIVO.md), [CI 45299333730 — failure físico](https://github.com/mxlzz/Nilo_public/actions/runs/45299333730). PyBullet3.2.7, NumPy2.4.6, xarray2026.9.0. Dos incidencias instrumentales previas (YAML y atributo NetCDF `mode`) se conservaron y corrigieron sin alterar dinámica.

La esfera2kg se apoyó a z1,24999m en meseta1m. `replaceHeightfieldIndex` mantuvo IDs, pose/velocidades y rango original del terreno. Los raycasts a x=.5 confirmaron ambas nuevas alturas0,899999976m y0,800000012m. El inventario cerró exactamente3752kg, exportaciones750+750=1500kg, cinco corruptelas rechazadas y checkpoint NetCDF exacto. Los controles sham y static permanecieron correctamente apoyados.

**Fallo:** tras cada descenso, el cuerpo permaneció en z1,24999m, delta vz=0, con fuerza normal registrada19,62N y distancia de contacto−1e−5m; el hueco real era0,1/0,2m. La trayectoria cinemática SHA fue exactamente igual al sham y static. Los cuatro gates físicos de descenso/gravedad y apoyo final fallaron en activo y replay. Raycast correcto y stock conservado NO garantizan contacto correcto.

La causa interna no fue aislada: posible contacto persistente obsoleto y/o estado de activación. No atribuirla exclusivamente al AABB: los extremos se mantuvieron constantes. **No adoptar actualización in situ como mecanismo de mundo.** Evaluar en un ensayo independiente activación explícita y sustitución de *solo* collider estático, manteniendo cuerpo dinámico y su estado, con controles idénticos. Si ninguna opción nativa pasa, reconsiderar proveedor. H38 permanece negativa, E7 abierta.
