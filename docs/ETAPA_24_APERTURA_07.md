# Nilo 0.7 — Etapa 24 · Apertura y criterios de publicación

**Estado:** validación técnica completada (2026-11-06); publicación a verificar. Ver [acta de cierre técnico](ETAPA_24_CIERRE_07.md). La etapa 23 se cerró con [acta explícita](ETAPA_23_CIERRE_ARQUITECTURA_07.md), sin afirmar Groq probado ni autonomía mejorada.

## Punto de partida verificado

- Rama de trabajo `refactor/0.7`; `main` sigue apuntando a 0.6.4; PR [#77](https://github.com/mxlzz/Nilo_public/pull/77) continúa borrador.
- Última suite integral acreditada: [#42159680935](https://github.com/mxlzz/Nilo_public/actions/runs/42159680935) `success`; paquete portable reconstruido/importado desde ZIP por la prueba de CI, sin publicar release.
- Archivo `VERSION` sigue en `0.6.4` incluso en la rama refactor y los textos `LEEME_PRIMERO.txt`/`LEEME_PORTABLE.txt` todavía describen una edición portátil `05.7`. Esto **debe actualizarse** al empaquetar 0.7.0; no confundir el éxito de tests con versión publicable.
- El árbol contiene **351 archivos** de código, assets y documentación. Hay múltiples fachadas en raíz (`brain.py`, `goal_evidence.py`, `world.py`, `project_lifecycle.py`, etc.) que permiten imports históricos. Identificar dependencia real antes de eliminarlas; los tests y el bundle siguen utilizando varias. Los ciclos legacy autorizados por `tools/auditar_arquitectura.py` no equivalen a módulos libres de deuda.
- La sesión de validación no conserva `code_commit`; la próxima evaluación de un bundle debe tener procedencia verificable de su artefacto/commit.

## Trabajo pendiente de etapa 24

1. **Inventario del árbol y dependencias:** imports, código huérfano, duplicaciones y fachadas temporales. Eliminar solo con pruebas de consumidores y rutas de compatibilidad; evitar segundo motor permanente.
2. **Coherencia del release:** actualizar `VERSION` a `0.7.0`, textos de primer inicio y nombres del paquete; regenerar `MANIFIESTO_SHA256.json` y verificar sus huellas con archivos del ZIP.
3. **Integración y seguridad:** comprobar packaging `empaquetar_version.py`, primer inicio, importación de configuración/partida en copia, separación de claves, endpoints locales y que no se incluya SQLite ni `config.env` en el paquete.
4. **Migración y rollback:** abrir copia de save antiguo, conservar el original intacto y restaurar backup; repetir sobre Windows real en la verificación final de instalación.
5. **Regresión completa:** CI, auditorías de capas, fixtures, replay y package smoke; documentar fallos y correcciones.
6. **Publicación controlada:** solo después de criterios 1–5, preparar notas de versión, mover PR de borrador al circuito de revisión, fusionar e identificar tag/release `0.7.0`.

## Riesgos abiertos pero no bloqueantes de la reestructuración

Bucle de cierre de proyectos, recreación de objetivos y exploración sin frontera (deuda funcional). Groq no verificado empíricamente en etapa 23: no anunciarlo como integración probada a partir de esta etapa; la prueba de red puede integrarse a una smoke opcional cuando haya credenciales, sin detener la auditoría de empaquetado.

**Criterio:** no declarar finalizada la etapa 24 ni publicar el release mientras las verificaciones de instalación, importación, restauración e identidad de versión no estén acreditadas.

## Implementación de salida a release (6/11/2026)

Preparado en rama de trabajo, pendiente de verificación CI en commit de implementación:

- Etiqueta de producto `0.7.0`, textos de inicio y notas de versión actualizados; formato de guardado SQLite v5 sin cambio.
- Manifiesto fuente normalizado como lista de archivos permitidos. El ZIP incluye un manifiesto nuevo con SHA256 calculados sobre bytes reales y `BUILD_INFO.json` de versión/commit. Los archivos de desarrollo `.github`, `tests` y `tools` no se distribuyen.
- `run_history.engine_identity` recupera el SHA del bundle portable si no hay `.git`, sin asumir un commit inexistente.
- Auditor de paquetes y pruebas de regresión del ZIP; **nuevo smoke Windows** usando el Python 3.12.10 embebido, partida nueva, migración por API pública y restauración con backup. Su resultado final se debe verificar en Actions, no deducirlo de la configuración del job.
- `.github/workflows/paquete.yml` bloquea la publicación hasta superar CI Linux y Windows, no pisa tags existentes y publica solo desde `main`; el PR continúa borrador.

Pendiente para cerrar: resultados de CI en esta revisión, limpieza/compatibilidad de fachadas por consumidores, verificación final del ZIP y publicación controlada. No registrar release hasta tener evidencia.

## Resolución tras validaciones del 6/11/2026

El candidato 0.7.0 pasó [CI completa Linux y Windows #42214267816](https://github.com/mxlzz/Nilo_public/actions/runs/42214267816), después de corregir el diagnóstico de bytecode, instalar Python mediante hash .NET y cerrar correctamente las conexiones SQLite/WAL durante el rollback. Los tests antiguos se alinearon con la nueva etiqueta de producto sin quitar su comparación histórica de UI. Se conservaron adaptadores de API utilizados y solo se distribuyen 168 archivos allowlisted más `BUILD_INFO.json` y el manifiesto generado. La fusión, tag y publicación se acreditarán por separado.
