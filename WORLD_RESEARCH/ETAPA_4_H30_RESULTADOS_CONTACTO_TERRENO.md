# Etapa4 — H30. Superficie local del territorio WorldEngine admite contacto Bullet

**Fecha:** 2026-11-22. **Dictamen H30 APROBADA bajo todos los gates preregistrados, incluyendo el requisito de patch NO plano enmendado antes de CI.** [Prerregistro](ETAPA_4_H30_PROTOCOLO_CONTACTO_TERRENO.md), [código](experiments/probe_e4_h30_worldengine_bullet.py), [CI integrada H29+H30 45086818016 — SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45086818016), commit `7feec536fc9072652aef873b944a074f550be81b`. Los tres jobs del workflow `generate_raw_worlds`, `check_landlab_material_owner` y `check_local_bullet_support` finalizaron SUCCESS usando **el mismo artefacto raw de WorldEngine**.

## Geometría verificada

Mismas seeds7321 y8128, WorldEngine MIT upstream `3b9113ecfad884cab4b32081d138a15e6262ada8`, hashes raw esperados de H29, mismos valores de elevación `z_nominal=50*(raw−min)/(max−min)`, y nodos 100m espaciamiento nominal. En cada mapa se seleccionó determinísticamente el patch de cuatro muestras con **menor rango de alturas≥0,05m** (enmienda previa al CI para evitar que H30 testeara solo una planicie trivial). Dos triángulos en el espacio local `(0,0),(100,0),(100,100),(0,100)`, con altura fuente exacta, no `GEOM_PLANE` artificial. Bullet `GEOM_FORCE_CONCAVE_TRIMESH` usado como límite estático.

- **Seed7321:** patch índices `(12,20)`, alturas nominales `[[0,2476121769,0,2928307264],[0,2400083690,0,2414182885]]`, rango0,0528224m. En punto interior `(40m,30m)`, altura geométrica esperada0,250275865315m, raycast Bullet0,250275865315m, error abs **6,66×10⁻¹⁶m nominales**.
- **Seed8128:** patch `(14,26)`, alturas `[[0,0523114679,0,0175012448],[0,0]]`, rango0,0523115m. En mismo punto local altura0,033137005203m, raycast correspondiente error**7,01×10⁻¹⁶m nominales**.
- Los patches son relativamente planos **por selección explícita**, no autorizan declarar que la totalidad del relieve complejo produce colisiones correctas ni estimar soporte en pendientes fuertes.

## Contacto y controles

Esfera maciza 2kg, radio0,50m, suelta desde z **3m por encima de la altura interpolada** en `(40,30)`, gravedad−9,81m/s², timestep1/240,720 pasos (3s), fricción0,8/restitución0, contacto resuelto por PyBullet3.2.7 (Python3.11.18).

- **Dos seeds, con mesh+gravedad:** descenso vertical **2,5000229m** y **2,5000142m**, final del centro a~radio0,5m sobre la superficie, sin salir de los100×100m. **546 eventos temporales** de contacto positivo en cada escena; peor penetración medida por contacto−0,000010m nominal, muy inferior al umbral−0,05m; ninguna geometría/masa ficticia.
- **Control sin gravedad:** posición y velocidad permanecen exactamente iniciales; cero contactos positivos en ambas seeds.
- **Control sin mesh:** 0 contactos, esfera desciende ~29,547m a lo largo de3s simulados (menor que caída ideal por damping Bullet, pero claramente sin soporte).
- **Replay:** seed7321 con mesh y gravedad, posiciones/velocidades/contador/ray SHA del owner idénticos.
- **Estado:** `xarray.Dataset` con propietario único de masa de esfera2kg, posición/velocidad y `terrain_height_m_nominal(2,2)` como geometría inerte derivada de raw, metadatos seed/hash/cota/tiempo. Siete estados adulterados rechazados, checkpoint NetCDF de1580bytes restauró propietario y hash `834d5e932100476ac914055e82a07c54a47ea4b8bd2cdcf2ea589f28f21721be`.

## Límite y dictamen

H29 y H30 tomaron **el mismo artefacto de fuente**, pero publicaron **dos estados y dos procesos independientes**: H29 Landlab con suelo móvil y sedimento, H30 Bullet con esfera sobre patch estático. **NO existe acople en tiempo** ni un mismo inventario que transporte suelo y sostenga al cuerpo simultáneamente. La conversión vertical0–50 es nominal, no escala física validada. Ni el mesh del mundo completo ni el soporte de cavidades3D se demostraron. H30 **no adopta motor gráfico** ni mundo final.

El resultado cubre el requisito de que los territorios iniciales de WorldEngine sean utilizables por la **segunda ley local de E2 (gravedad/colisión)** bajo un alcance geométrico restringido; la primera ley (sedimento fluvial) ya se probó en H29. Se habilita [auditoría de cierre limitado E4](AUDITORIA_CIERRE_ETAPA_4_2026-11-22.md). Etapas5–8 permanecen sin aprobar.
