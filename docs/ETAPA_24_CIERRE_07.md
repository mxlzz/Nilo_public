# Nilo 0.7.0 — Etapa 24 · Cierre técnico y publicación

**Fecha:** 2026-11-06 · **Código validado:** `82144889b0f9fb493c71db1cb4958fc526f8ba27` antes de integrar documentación de `main`. **Estado del acta inicial:** validación técnica **aprobada**, fusión y publicación por acreditar con artefactos propios.

## Alcance de la última etapa

- **Limpieza, arquitectura:** auditados los importadores/ciclos mediante `tools/auditar_arquitectura.py`; motor único `nilo_runtime.application.engine.Simulation`, fachadas raíz por compatibilidad. El auditor de release detectó 8 fachadas explícitas en raíz y verificó el contenido del paquete; no se eliminaron porque los contratos y tests existentes todavía las usan. La eliminación por estilo, sin migrar consumidores, sería una regresión.
- **Identidad del build:** `VERSION = 0.7.0`, instrucción de instalación y encabezado UI actualizados. `empaquetar_version.py` calcula hashes reales de los 168 archivos permitidos y agrega `BUILD_INFO.json` con commit SHA cuando se genera desde CI. `run_history` lee esa identidad en ejecutables portátiles sin `.git`.
- **Distribución:** ZIP `Nilo-0.7.0.zip` no contiene pruebas, GitHub Actions, claves `config.env`, bases SQLite personales ni logs. El intérprete portátil se descarga en primer inicio desde python.org y se verifica con SHA256 por implementación .NET; no requiere modificar el PATH de Windows.
- **Persistencia:** corrección de cierres de conexiones en `gestionar_partidas.py`; Windows distingue WAL residual de base todavía abierta, checkpoint seguro y backup antes de restaurar. Las validaciones E2E verifican fuente no alterada y destino íntegro.
- **Interfaz:** la etiqueta visible indica Nilo 0.7.0; las pruebas históricas preservan el hash de la interfaz anterior normalizando **únicamente** la etiqueta de versión, no cambiando sus assets ni código JS.

## Pruebas acreditadas

[**GitHub Actions #42214267816**](https://github.com/mxlzz/Nilo_public/actions/runs/42214267816) terminó **success**, con los siguientes jobs:

- **Linux:** batería completa sin credenciales, auditorías de arquitectura/identidad/operaciones/mundo/navegación/recursos/física/estado/memoria/autonomía/persistencia/API/UI/laboratorio; carga de 8 días simulados **sin LLM**, QA multi-semilla, reproducción entre procesos y pruebas de ZIP.
- **Windows:** ejecución real del portátil con Python 3.12.10 embebido, verificación del hash de descarga, creación de partida nueva, importación de otra carpeta sin escribir en ella, backup, restauración y SQLite íntegra.
- Job de **Groq/Gemini real opcional omitido**, porque no se disparó manualmente. Esto **no acredita Groq**. Una sesión Gemini real fue evaluada en la [etapa 23](ETAPA_23_CIERRE_ARQUITECTURA_07.md).
- No se evaluó equivalencia conductual contra 0.6.4 mediante corridas emparejadas. Los bucles conocidos de proyectos y exploración quedan como deuda funcional posterior a 0.7.

## Control de integración

La rama de refactor se construyó desde un snapshot previo a tres commits documentales de `main`. Antes de fusionarla, esos commits deben preservarse mediante merge de dos padres y resolución explícita en `README.md`, `docs/CAMBIOS.md`, plan, guía de contribución y acciones. La prioridad es conservar tanto los enlaces públicos migrados como las implementaciones nuevas del release. Un CI aprobado **antes** de esa integración no certifica la revisión final integrada; validar nuevamente.

## Publicación

Solo declarar 0.7.0 **publicado** cuando se observen el merge real en `main`, la ejecución aprobada del workflow `Paquete versionado Nilo`, el tag `v0.7.0` y el asset `Nilo-0.7.0.zip` en [GitHub Releases](https://github.com/mxlzz/Nilo_public/releases). La etapa 24 solo se cierra de modo definitivo tras esa comprobación.
