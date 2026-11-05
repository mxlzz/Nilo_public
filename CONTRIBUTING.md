# Contribuir a Nilo

Este repositorio es público, pero solamente las personas con permiso de escritura pueden modificar sus ramas directamente. Las propuestas externas se revisan mediante *pull requests*.

## Estado y ramas

- `main`: última versión estable, actualmente Nilo **0.6.4**. Mantener estable.
- `refactor/0.7`: desarrollo de la reconstrucción 0.7.0. Las etapas 00–08 están completas; la siguiente es 09 (navegación y exploración).
- Para cambios concretos, preferir ramas `work/**` o `fix/**` y abrir un PR hacia la rama correspondiente.
- [Issue central de 0.7](https://github.com/mxlzz/Nilo_public/issues/74) · [PR de seguimiento](https://github.com/mxlzz/Nilo_public/pull/77).

## Proponer cambios

1. Abrir un issue si el cambio necesita discusión o diagnóstico.
2. Crear una rama de trabajo (o un fork, para contribuciones externas).
3. Explicar en el PR el problema, los cambios, las pruebas realizadas y los efectos sobre partidas guardadas.
4. Mantener el CI verde y evitar modificaciones accidentales de reglas físicas o decisiones del personaje.
5. No fusionar `refactor/0.7` con `main` antes de cerrar el plan de 25 etapas y la validación final.

## Datos y seguridad

No incluir claves API, archivos `config.env` / `.env`, bases SQLite personales, logs, respaldos, archivos ZIP de partidas ni información privada. Usar fixtures sintéticas para las pruebas. Evitar copiar referencias internas del repositorio histórico privado.

## Licencia

La publicación del código **no implica automáticamente una licencia de reutilización**. No se ha decidido ni añadido una licencia al proyecto. La posibilidad de ver y crear forks dentro de GitHub sigue las condiciones de la plataforma; cualquier permiso de uso adicional queda pendiente de una decisión expresa del titular.
