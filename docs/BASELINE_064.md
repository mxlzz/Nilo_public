# Nilo 0.7 · Etapa 00 — Congelación de referencia y respaldos

**Fecha:** 4/11/2026. **Estado: COMPLETADA — ejecución verificada:** [GitHub Actions run #41867873550](https://github.com/mxlzz/Nilo/actions/runs/41867873550), job `126706730029`: success. Artefacto `nilo-07-baseline-064-synthetic` (ID `13342533195`, 75.343 bytes comprimidos), disponible desde la página del workflow, caduca el **2/2/2027** según GitHub.

## 1. Referencia publicada e inmutable

- **Release oficial:** [v0.6.4](https://github.com/mxlzz/Nilo/releases/tag/v0.6.4).
- **Commit al que apunta el tag:** `a8b72d664e9f29d8307ff5866d8ff4a7773368f0`.
- **SHA-256 del asset `Nilo-0.6.4.zip` informado por la API de releases de GitHub:** `2da332eac1933648cf5e0b7220ea0580c91650d2a9eaf833d6f272d6f7fb6517`. La descarga del ZIP y comparación contra este valor **pasaron en GitHub Actions** (salida `release_zip/Nilo-0.6.4.zip: OK` del run #41867873550).
- **Commit auditado posteriormente:** `e7229ebf9cf6a9f45a44a4ca184c12795535c843`. La comparación Git `v0.6.4...e7229eb` muestra **un único commit documental**: `docs/FUTUROS_CAMINOS.md` y `docs/LABORATORIO_CENTRO_AJUSTES_PROPUESTA.md`. El código ejecutable permanece idéntico al release.
- **Fingerprint existente del replay de referencia** `tests/fixtures/replay_basico.json`: `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24` (valor registrado en la propia fixture). Se prueba con `PYTHONHASHSEED=11` y `97`.

**Repositorios y distribuciones históricos para migración:**

| Versión | Ref Git inmutable | Fixture |
| --- | --- | --- |
| 0.5.9.4.2 | `f71ea48b344d3a4ca6c1a61b554f8df30e572a5b` | SQLite sintético inicial + con espera |
| 0.6.0 | `18559f496d5116aa542fbd96c6b9e08efd43217c` | SQLite sintético inicial + con espera |
| 0.6.4 | `a8b72d664e9f29d8307ff5866d8ff4a7773368f0` | SQLite sintético inicial + con espera, replay y backup/restore |

## 2. Qué se implementó para la prueba

- [`tools/congelar_baseline_064.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/tools/congelar_baseline_064.py): genera seis SQLite de prueba, sus hashes en un manifiesto, dos replays deterministas con huellas por campo y un ciclo de backup/restauración con la herramienta real `gestionar_partidas`, redirigida a un directorio sintético.
- [`tools/verificar_importacion_baseline_07.py`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/tools/verificar_importacion_baseline_07.py): vuelve a abrir **copias** de las seis partidas con el motor 0.6.4, comprueba integridad y conservación de semilla, escenario, reloj e historial no decreciente; verifica SHA-256 del original sin modificar.
- [`.github/workflows/baseline_07.yml`](https://github.com/mxlzz/Nilo/blob/refactor/0.7/.github/workflows/baseline_07.yml): descarga/verifica el ZIP oficial, checkout de los tres commits históricos, crea fixtures y publica un artefacto `nilo-07-baseline-064-synthetic` con los SQLite y reportes, **solo si todas las pruebas anteriores terminan satisfactoriamente**.

El artefacto del workflow es una copia de trabajo de QA con **retención de 90 días**, no un respaldo permanente de información personal. La generación mediante referencias inmutables y scripts en el repositorio permite recrearlo. El release 0.6.4 sigue disponible independientemente del artefacto.

## 3. Respaldo y rollback

**Partidas personales:** ninguna partida privada se subió ni se modificó. Las fixtures del laboratorio no son un respaldo de la partida real del usuario; para migrarla en el futuro debe guardarse una copia local de su archivo SQLite y, si corresponde, la configuración, **antes de abrirla con el nuevo motor**. En Windows se mantiene el flujo `RESPALDAR_PARTIDA.bat`; restaurar requiere cerrar Nilo y comprobar que SQLite no esté activo. El control de rollback no sustituye este paso sobre una instalación real.

**Código:** el tag v0.6.4 conserva el ZIP y commit. Toda la reestructuración se desarrolla en `refactor/0.7` y el PR draft [#155](https://github.com/mxlzz/Nilo/pull/155); `main` no recibe el nuevo motor. Hasta la integración, volver a 0.6.4 significa ejecutar el paquete oficial con una partida de esa misma versión o una copia conservada. **No abrir con 0.6.4 una partida ya migrada por 0.7** sin restaurar antes un backup compatible; la reversibilidad de migraciones posteriores no está garantizada.

## 4. Validación y puertas pendientes

- **Cumplido:** GitHub Actions #41867873550 verificó ZIP SHA, seis SQLite generadas, dos replays idénticos, backup/restore y seis importaciones (salida `{\"cases\": 6, \"all_passed\": true}`).
- **Cumplido:** GitHub Actions #41867065751 confirmó etapa 01 (auditor estructural, tests, escenarios, replay).
- **Limitación de la muestra:** las bases son sintéticas, una recién creada y otra con `wait` por versión. No representan la diversidad de una partida personal de meses con decenas de construcciones y proyectos. La etapa 18 ampliará esta batería para migración real, con fixtures y pruebas de integridad de enlaces/IDs; no dar por cubierta toda compatibilidad al pasar estas pruebas.

**Condición para comenzar implementación de etapa 02:** cumplida la puerta de CI de referencia (ambos workflows verdes y artefactos disponibles). Los resultados de los seis saves confirman una **muestra sintética acotada**, no compatibilidad absoluta con partidas personales extensas; su cobertura se ampliará en etapa 18.
