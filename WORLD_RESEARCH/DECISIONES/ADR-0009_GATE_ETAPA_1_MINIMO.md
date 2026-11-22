# ADR-0009 — Cierre provisional del gate mínimo de Etapa 1

**Fecha:** 2026-11-22. **Estado:** ADOPTADO PARA LABORATORIO, REVERSIBLE; no aprobación del motor del mundo.

## Decisión

Aprobar **únicamente** el criterio de aceptación de la etapa 1 establecido antes de los ensayos en [BASES_Y_HOJA_DE_RUTA.md](../BASES_Y_HOJA_DE_RUTA.md), tras [auditoría detallada de 4 pruebas](../AUDITORIA_CIERRE_ETAPA_1_2026-11-22.md). La prueba decisiva [H16](../ETAPA_1_H16_RESULTADOS_DOS_MATERIALES.md) pasó en [CI 45059387895](https://github.com/mxlzz/Nilo_public/actions/runs/45059387895) y cubrió en **un mismo owner** dos materiales, conservación de masa/energía, volumen derivado, fase material y respuesta diferencial a composición. H1–H6/ADR-0004/0005 sustentan integridad y representación espaciales en pruebas anteriores.

**No adoptar** FiPy, xarray, Landlab ni Bullet como **sistema universal**, ni declarar validación material de mezclas 3D, fluidodinámica, estructura estable o una simulación persistente. Son componentes experimentales y decisiones técnicas reversibles. **No confundir E1 cerrada con el proyecto completo.**

## Por qué ahora, y no antes

Antes de H15 solo se tenía conducción y materia separadas; H15 vinculó energía y fase pero solo con A; H16 completó comparación A/B, ocupación/volumen y energía en una sola representación y controles previos. No se rebajaron tolerancias. **Fallos conservados:** H12 con artefacto de frontera, H13A importaciones, H15.0 hash NumPy, H16.0 YAML. Ningún fallo físico de etapas posteriores se borra al cerrar E1.

## Condiciones y revisión

Reabrir este gate si en etapa2 una actualización cinemática crea dos dueños de la materia, pierde energía/materia o rompe la recuperación o las unidades. La etapa2 debe publicar **posición/velocidad** de un cuerpo con identidad y cantidad conservadas, bajo leyes existentes, comparando región libre/bloqueada, no limitarse a leer el log de Bullet. No agregar esquemas abstractos ni cache duplicado para ese fin. Para producción futura todavía habrá que decidir representación espacial y propiedad de todas las magnitudes.

**Etapa1 formalmente cerrada para pruebas mínimas; Etapa2 inicia solo al preregistrar H17, que no está aprobada aún.**
