# Nilo 0.7 — Etapa 18: persistencia, migración e historial

**Fecha:** 5 de noviembre de 2026. **Rama:** refactor/0.7. **Estado:** COMPLETADA. **Base estable:** main 0.6.4. **Esquema de save:** SQLite/snapshot v5, sin incremento.

[Plan general](PLAN_REESTRUCTURACION_NILO_07.md) · [Seguimiento](ESTADO_REESTRUCTURACION_07.md) · [PR #77](https://github.com/mxlzz/Nilo_public/pull/77) · [Issue #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Reauditoría y problemas confirmados

Se inspeccionaron archive.py, review_store.py, run_history.py, nilo_runtime/storage/entropy.py y timeline.py, core/state.py, application/session.py y los casos de uso, además del laboratorio histórico y los importadores sintéticos.

1. **Commits prematuros.** History, RunHistory y ReviewStore confirmaban tablas y migraciones parciales antes de validar y guardar el mundo. Se quitaron sus commits de inicialización. La apertura usa BEGIN IMMEDIATE y, al fallar la migración, revierte DDL, índices y marcadores, cierra la conexión y conserva el snapshot original.
2. **Escritura atómica y cachés.** El nuevo propietario nilo_runtime/storage/repository.py (SnapshotRepository.persist) reúne sesión, archivo, revisiones, snapshot JSON y checkpoint RNG en la misma unidad de trabajo con savepoint, commit o rollback. Ante fallos restaura también los índices Python de sincronización y la marca temporal updated; el cambio de semilla de un mundo aún vacío restaura la entropía en memoria si el guardado se interrumpe.
3. **Migración fuera del orquestador.** El código histórico se trasladó a nilo_runtime/storage/migrations.py. SessionLifecycle.migrate es ahora una fachada. migration_path valida el sobre de entrada antes de convertir versiones 0–5 y rechaza futuras; los marcadores heredados hacen idempotentes las migraciones de partidas que ya declaran esquema 5. Se vuelve a validar el estado completo antes del commit.
4. **Archivo histórico incremental.** History.sync procesaba cada lista inmutable completa en cada guardado. Ahora usa un cursor por objeto de lista para procesar solo entradas añadidas; al sustituirse o acortarse la lista recorre y deduplica por ID. Mantiene la referencia al objeto para evitar colisiones por reutilización de id(). Los registros mutables conservan sus revisiones, y al reabrir se recupera su última huella del historial.
5. **Backups sin riesgo de copiar un WAL incompleto.** nilo_runtime/storage/backups.py utiliza la API backup() de SQLite, verifica PRAGMA quick_check, JSON y correspondencia snapshot/RNG. El archivo se valida en una ruta temporal del mismo directorio y se publica solo si el destino no existe. La restauración crea otra copia; nunca sobrescribe la partida original. Cierra conexiones explícitamente y usa URI de rutas portable para Windows y caracteres acentuados.
6. **Utilidad de recuperación.** tools/backup_partida_18.py incorpora inspeccionar, respaldar y restaurar. No necesita iniciar la interfaz ni acceder a servidores.

## 2. Contratos preservados

- El snapshot sigue siendo formato v5. No se regeneran IDs de proyectos, investigaciones, cuaderno ni mediciones al importar o reabrir.
- Archivo append-only (history), revisiones mutables (history_revisions), referencias por ID explícito (record_links), estado de RNG (runtime_entropy), sesiones y timeline permanecen separados, pero sus escrituras pendientes se confirman con el snapshot.
- Los saves con esquema futuro se rechazan sin restauración automática ni generación de otro mundo; un checkpoint RNG cuya huella no coincide con el snapshot se denuncia como incompatible.
- La lectura, el backup y la restauración nunca mutan el origen. Una restauración no puede utilizar como destino un archivo existente ni el origen.
- La importación de partidas históricas se prueba sobre copias, no sobre archivos personales.

## 3. Uso de los backups en Windows o consola

Desde el directorio de Nilo:

- Inspeccionar: python tools/backup_partida_18.py inspeccionar nilo_mundo.sqlite3
- Crear backup WAL incluso con Nilo abierto: python tools/backup_partida_18.py respaldar nilo_mundo.sqlite3 respaldo-2026.sqlite3
- Restaurar como otra partida: python tools/backup_partida_18.py restaurar respaldo-2026.sqlite3 partida-recuperada.sqlite3

El destino debe ser nuevo. Las respuestas indican huella del snapshot, versión, minuto simulado, número de registros, revisiones, vínculos y existencia del checkpoint RNG. La futura interfaz del laboratorio podrá utilizar estas funciones (etapa 21); no se crean copias automáticas sin elección explícita.

## 4. Benchmark medido en GitHub Actions

Runner Linux de CI; fixture SQLite temporal con 2.500 registros sintéticos. Ejecución reproducible: python tools/benchmark_persistencia_18.py --count 2500.

| Operación | Tiempo observado |
| --- | ---: |
| Primera sincronización de 2.500 registros | 33,720 ms |
| Sin novedades, promedio de 5 sincronizaciones | 0,011 ms |
| Añadir 20 registros | 0,787 ms |
| Crear backup consistente | 3,673 ms |
| Restaurar en copia nueva | 4,799 ms |

Se verificaron 2.500 IDs iniciales y 2.520 después de incorporar 20, sin pérdida ni duplicados. El archivo principal medía 4.096 bytes mientras el respaldo íntegro medía 454.656 bytes. **El tamaño del archivo principal excluía páginas presentes todavía en el WAL**, lo cual evidencia el riesgo de copiar únicamente el archivo .sqlite3 con una herramienta de archivos. Son mediciones de este runner y fixture, no una estimación de tiempos para una partida extensa.

## 5. Verificaciones finales

- [CI integral #42068584225](https://github.com/mxlzz/Nilo_public/actions/runs/42068584225): **success**, 932 tests (1 omitido), 20 específicos de etapa 18. Auditorías, pruebas de rollback, integridad, backups/CLI, escenarios físicos, replay y ZIP portable aprobados.
- Fingerprint determinista entre procesos: 9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24.
- [Compatibilidad histórica #42068591340](https://github.com/mxlzz/Nilo_public/actions/runs/42068591340): **success**, seis partidas SQLite sintéticas anteriores abiertas sobre copias, sin alterar originales ni IDs.
- Auditor dedicado: tools/auditar_persistencia_18.py. Tests específicos: tests/test_persistencia_18.py. Benchmark: tools/benchmark_persistencia_18.py.
- [Último commit de código validado](https://github.com/mxlzz/Nilo_public/commit/3683746c1d8283431c372a7cc79aecd3707168ab).

## 6. Límites y continuidad

El historial inmutable se sincroniza incrementalmente, pero los registros mutables siguen contrastando sus huellas. No se implementó eliminación automática de checkpoints históricos; antes hay que definir políticas de exportación y conservación. La evaluación con partidas extensas queda para etapa 22 y los botones de backup del laboratorio para etapa 21.

**Etapa 18 completada. Próxima: 19 — Servidor, API y observatorio.** main sigue en 0.6.4; PR #77 permanece en borrador, sin merge ni release 0.7.0.
