# ADR-0016 — Cierre provisional de Etapa4, condiciones iniciales de terreno

**Fecha:** 2026-11-22. **Estado:** APROBADO solo para laboratorio inicial2.5D y superficie rígida local; REVERSIBLE.

## Decisión

[Auditoría formal E4](../AUDITORIA_CIERRE_ETAPA_4_2026-11-22.md) confirma que [H29](../ETAPA_4_H29_RESULTADOS_SEMILLAS_TERRITORIO.md) y [H30](../ETAPA_4_H30_RESULTADOS_CONTACTO_TERRENO.md) cumplen **las cuatro verificaciones originalmente escritas en E4** en su alcance mínimo: generación de dos semillas reproducibles, variabilidad no trivial, estados materiales válidos, y aceptación de ese terreno por las **dos leyes locales E2 escogidas en separado** (erosión Landlab y gravedad/contacto Bullet). No fue necesario programar un generador nuevo ni simular miles de años. **E4 cerrada provisionalmente** en ese sentido, E5–E8 pendientes.

## Evidencias y límites que condicionan la aprobación

- WorldEngine MIT generador pinneado produce raw16×32 no plano y reproducible, con dos semillas diferentes418/512 muestras; alturas sin unidad física →nominal0..50m **no calibrada**, geología real NO probada.
- H29 mapea centros fuente a nodos Landlab de16×32 core con halo sin masa, con suelo A inicial921,6 millones kg, erosión en seis pasos conservada con salida nativa, ablate K=0 sin movimiento, replay y checkpoint.
- H30 triangula un patch **local poco inclinado pero no plano** desde mismo raw, Bullet valida ray≈altura analítica, gravedad produce caída+contacto sin penetración y controles g0/sin mesh responden. **No** prueba toda la topografía.
- H29 y H30 producen **dos dueños separados durante ejecución**, aunque parten del mismo artefacto source. No se confunde esto con E5. Aún faltan continuidad de IDs, energía mecánica, celdas ROI, acople sedimentación→contacto y persistencia del estado cinemático/mundo.

## Próximo paso

Abrir E5 como **demostración mínima de causalidad cruzada** con el menor número de componentes ya validados: suelo/relieve que Landlab cambia en owner, seguido de contacto rigid Bullet que consulta ese **mismo owner material/geométrico**, comparando K=.1 vs K=0. Registrar transformaciones y medir efecto aguas abajo antes de sumar agua dinámica, calor/latente o nuevos motores. Una segunda etapa podrá ensayar feedback opuesto; no afirmar acoplamiento bidireccional por un enlace de una sola dirección.

La elección de WorldEngine/Landlab/PyBullet sigue siendo experimental y revocable: no fusionar `main` ni NeuroLab.
