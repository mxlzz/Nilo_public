# Migración pública — Issues y validación

Actualización del 5 de noviembre de 2026.

## Seguimiento migrado

Se reconstruyeron 76 issues, con 58 abiertos y 18 cerrados, y sus 94 comentarios.
Se conservaron títulos, contenido, estados, etiquetas, asignaciones y orden de
los comentarios. GitHub asigna nuevas fechas y autoría nativas a la importación;
la autoría y fecha originales se documentan en cada cuerpo importado.
No existían hitos en el origen.

La correspondencia completa está en [MAPEO_ISSUES_PUBLICOS.json](MAPEO_ISSUES_PUBLICOS.json).
El antiguo issue privado 151 corresponde al [issue público 74](https://github.com/mxlzz/Nilo_public/issues/74).
Las referencias entre issues se adaptaron a los nuevos números en sus cuerpos,
comentarios y documentación. Las evidencias históricas de PRs, commits, releases
y CI privados se conservan como identificadores textuales: no se trasladó ese
historial ni se presentan enlaces públicos que apunten a objetos inexistentes.

Se revisaron cuerpos y comentarios antes de publicar. La verificación posterior
compara contenido, títulos, estados, etiquetas, asignaciones, comentarios y
marcadores de procedencia para detectar ausencias o duplicados.
El repositorio privado permanece como archivo histórico sin modificaciones.

## Validación pública

- [Referencia estable 0.6.4: CI aprobada](https://github.com/mxlzz/Nilo_public/actions/runs/41957705421).
- [Runtime 0.7 hasta etapa 08: CI completa aprobada](https://github.com/mxlzz/Nilo_public/actions/runs/41960204088): auditorías, suite, escenarios, identidad/RNG entre procesos, ZIP y replays deterministas.
- [Compatibilidad histórica pública aprobada](https://github.com/mxlzz/Nilo_public/actions/runs/41960983505): seis partidas sintéticas importadas tanto en 0.6.4 como en 0.7, conservando intactos los originales.

El workflow de compatibilidad en `refactor/0.7` usa [fixtures sintéticas versionadas](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/docs/BASELINE_PUBLICA_07.md)
y el snapshot público inmutable de 0.6.4. No depende de secretos, commits o
releases privados. Se habilitó la ejecución manual de la validación general.
No se alteraron las leyes físicas, los prompts ni la versión del producto.

## Punto de continuación histórico (5/11/2026)

Al cerrar la migración de issues se habían completado las etapas 00–08; la etapa 09 seguía pendiente. Ese corte no publicaba 0.7 ni probaba mejoras conductuales. Posteriormente se completaron los pasos 09–23 y la validación técnica de 24. Véase [tablero actualizado](ESTADO_REESTRUCTURACION_07.md); no usar esta instantánea histórica para determinar el release.
