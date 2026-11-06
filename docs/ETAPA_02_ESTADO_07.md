# Nilo 0.7 · Etapa 02 — Estado de dominio

**Fecha:** 4 de noviembre de 2026. **Rama:** `refactor/0.7`. **Referencia funcional:** release `v0.6.4` / save v5. **Estado de etapa: COMPLETADA**. Validación general `referencia privada #41871461715` (`referencia-historica-privada-actions-runs-41871461715`), commit `34460acc0a6055e15ba7a98870f60a60d6c60208`: success. Compatibilidad histórica `referencia privada #41871224896` (`referencia-historica-privada-actions-runs-41871224896`), commit `274c44cb2248a44a8db474c503cb80137d307050`: success. Registro general: [ESTADO_REESTRUCTURACION_07.md](ESTADO_REESTRUCTURACION_07.md); matriz de dependencias: [ETAPA_01_ARQUITECTURA_07.md](ETAPA_01_ARQUITECTURA_07.md).

## 1. Auditoría localizada y criterios

El `Simulation` de 0.6.4 mantiene el estado activo como tres diccionarios mutables anidados: `self.s` (sesión/estado de aplicación), `s["person"]` (persona y memoria) y `s["world"]` (hechos del entorno). La versión declarada en el JSON es **5** (`s["version"]=5`); no equivale a `VERSION=0.6.4` ni a la versión del esquema de acciones.

**Revisión de escrituras/defaults:** solo `nilo.py` contenía **52 usos de `setdefault`** en la revisión textual, muchos en `migrate`, y `world.py` otros **21**. Estos son indicios de ajustes sobre el diccionario en varios lugares, no una medición exacta del número de migraciones de estado. La inicialización de escenario/agente/entorno también estaba dentro de `nilo.py`, junto al loop temporal, HTTP, deliberación, archivos y vistas. La UI usa `public_state` y estado de lectura SQLite, mientras que el LLM recibe una proyección cognitiva seleccionada, con otros permisos. No deben compartir un contrato indiscriminado.

**Tres distinciones importantes:**

- **Hecho físico modelado:** casillas, depósitos, construcciones, posición y material disponible en `world` / `inventory`. El motor es autoridad sobre consecuencias, no el nombre de una obra.
- **Memoria o inferencia de Nilo:** `person.observations`, `research`, `knowledge`, `projects`, `measurements`. Registrar una hipótesis no la convierte en una ley física. Las medidas provienen de eventos, pero sus referencias no se validan causalmente en esta etapa.
- **Estado operativo/observador:** velocidad, pausa, intentos LLM, chat y cursor de lecturas. El registro histórico y sus marcas de lectura viven también en SQLite (`archive.py`, `review_store.py`), y las preferencias de interfaz se almacenan separadamente. No todo debe ir en `WorldState` ni inyectarse al LLM.

La propuesta conserva los diccionarios mutables mientras sus consumidores son migrados de forma ordenada. Introducir una segunda instancia de estado «tipado» que también se modifique sería duplicar la fuente de verdad. El modelo nuevo es por ahora **proyección inmutable y contrato de límites**, no segundo motor.

## 2. Código implementado

| Cambio | Fuente de verdad y responsabilidad | Compatibilidad |
| --- | --- | --- |
| `nilo_runtime/core/state.py` | `GameState`, `WorldState`, `ActorState`, `SAVE_SCHEMA_VERSION=5`, validadores `validate_loaded_envelope` / `validate_current_state`, `snapshot_state` | `to_legacy()` devuelve un diccionario independiente y serializable con el mismo contenido y orden de las claves; no se añaden claves al save |
| `nilo_runtime/application/bootstrap.py` | Creador único de estado inicial; composición de escenario, entorno y agente | `nilo.initial_state` sigue disponible por import público, sin doble implementación |
| `nilo.py` | Usa inicializador común, valida la versión cargada **antes** de `migrate`, valida estructura al persistir y ofrece `domain_snapshot()` bajo el lock | Mantiene `Simulation`, `self.s`, tablas SQLite, marcas y métodos públicos para no romper scripts / tests |
| `island_views.py` | Renderiza construcciones de la isla a partir de una copia profunda; el enriquecimiento visual no cambia `world["structures"]` | Misma descripción y simbología sin side effects de lectura |
| Manifiesto y CI | Nuevos `nilo_runtime/**` enumerados en `MANIFIESTO_SHA256.json`; verificador de ZIP extraído; pruebas de 6 saves históricos contra runtime | Evita desarrollar un paquete que luego no arranca fuera del checkout |

El lector `snapshot_state` congela recursivamente mappings/listas en `MappingProxyType` y tuplas; sus datos quedan desacoplados del diccionario mutable, incluso para objetos anidados. `GameState.to_legacy()` crea una copia JSON-equivalente. **No** altera estado, IDs, semilla, reloj ni memoria. Los futuros DTOs de UI/LLM (pasos 14 y 19) deberán seleccionar **subconjuntos** de esta información, nunca exponer `GameState.data` completo al personaje.

### Contrato estructural frente a diagnóstico físico

La revisión de CI recuperó **tres comportamientos legítimos** que una validación demasiado estricta habría roto:

1. `Environment` puede implementar otro escenario con `world={"seed":81,"abi":"minimal-v0"}`; el esquema general no exige `levels`, `revealed` y `deposits`, que son detalles de la isla.
2. Un save histórico puede omitir temporalmente `scenario_id`; el validador no inventa el valor al leer o escribir. La migración existente lo completa al **reabrir** la partida.
3. El diagnóstico de invariantes debe poder inspeccionar un estado con inventario negativo. La **validación estructural de carga/guardado** admite cantidades enteras negativas para conservar evidencia; el modo `strict_physics=True` empleado en la **creación de partidas nuevas** y las pruebas rechaza esa anomalía. El motor la diagnostica; no la corrige ni borra silenciosamente.

Un `StateSchemaError` por versión futura (p. ej. 7) rechaza la carga antes de que `migrate()` la reduzca a 5. **Corrección intencional de seguridad de datos:** el código 0.6.4 sustituía silenciosamente un JSON de snapshot corrupto por un mundo nuevo; la rama 0.7 ahora aborta la carga y conserva íntegro el payload original, para que el siguiente `write()` no lo destruya. Es el único cambio funcional deliberado de esta etapa frente al baseline. No se crea una supuesta migración v6; migraciones completas y rollback continúan siendo responsabilidad de la etapa 18.

## 3. Pruebas e invariantes que rigen el cierre

- [`tests/test_estado_07.py`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/tests/test_estado_07.py): constructor único; versión y formato conservados; roundtrip JSON sin omitir campos extendidos; instantánea profundamente inmutable/desacoplada; errores estructurales; advertencia ante futuro; mundo alternativo sin topología isleña; ausencia de `scenario_id` legado; inventario negativo disponible para diagnóstico; mapa y `public_state` sin mutación; saves corruptos/futuros que no se reemplazan; SQLite desde `Simulation`.
- [`tools/verificar_paquete_07.py`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/tools/verificar_paquete_07.py): empaquetado de desarrollo, extracción y arranque con imports desde ZIP, sin copiar partidas personales.
- [`.github/workflows/baseline_07.yml`](https://github.com/mxlzz/Nilo_public/blob/refactor/0.7/.github/workflows/baseline_07.yml): verifica la referencia histórica, genera seis SQLite sintéticas y comprueba reapertura en 0.6.4 **y** en la rama 0.7. Los reportes `migration_probe_064.json` y `migration_probe_runtime_07.json` se entregarán como artefacto.
- Suite histórica completa, escenarios físicos y dos replays desde semillas de hash distintas: sin alterar huella `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`.

**Pruebas ejecutadas y aprobadas:** CI `referencia privada #41871461715` (`referencia-historica-privada-actions-runs-41871461715`): **665 tests, 1 skip**; auditor de imports/ciclos; escenarios físicos; replay exacto; ZIP portable extraído con `ZIP bootstrap v5 OK`; dos fingerprints iguales a `9c4d43a5815fb042e06e32789b7dc6606023c3eb0634fe08dd7ad90616dc5c24`. CI histórico `referencia privada #41871224896` (`referencia-historica-privada-actions-runs-41871224896`): las seis partidas sintéticas se abrieron con el motor refactorizado, en copias sin alterar originales, y se publicaron sus reportes. La primera ejecución estricta de esquema presentó tres regresiones, corregidas antes del cierre; el test de ZIP también exigió corregir el `sys.path` del verificador (no del motor).

## 4. Deuda dejada explícita para pasos posteriores

- No existe todavía `GameState` como **estado operativo único mutable**: siguen mutando `self.s`, `person` y `world` hasta extraer el orquestador y handlers (07–13). El snapshot tipado no es una ruta alternativa de ejecución.
- Los valores de `project/research/measurements` conservan campos libres `Any`; faltan contratos de causalidad y eventos/resultados (03), memoria/conocimiento (16) y proyectos (17).
- Las vistas de mapa se hicieron puras; la separación de **todos** los DTOs HTTP/LLM, el acceso por identidad y la exposición de referencias mutables restantes se tratarán en 14/19.
- Las validaciones estructurales no reemplazan `diagnostics.inspect_invariants`, que conserva la responsabilidad de detectar contradicciones físicas. No se corrigen anomalías reescribiendo historia.
- Claves y migraciones posteriores a schema v5 no se agregan; la conservación del historial completo, performance SQLite y rollback de partidas largas pertenecen a 18/22.

## 5. Puerta de salida

**Puerta de salida superada.** Suites y auditor de capas verdes, ZIP extraído verificado, fingerprint idéntico a 0.6.4, seis SQLite históricas importadas sobre copias sin alterar originales y documentación registrada. `main`, `VERSION` y las partidas personales permanecen intactos. No se publica versión descargable nueva hasta el release final 0.7.0. **Siguiente: etapa 03, resultados y eventos tipados.**
