# Nilo 0.7 — Etapa 21: laboratorio unificado y centro de ajustes

**Fecha:** 5 de noviembre de 2026 · **Rama:** refactor/0.7 · **Baseline:** main / VERSION 0.6.4.  
**Alcance de esta entrega:** unificar ejecución del sandbox con el motor real, perfilar configuración cognitiva/operativa limitada y recuperar ajustes o mundos de modo no destructivo.

[Plan integral](PLAN_REESTRUCTURACION_NILO_07.md) · [Seguimiento de etapas](ESTADO_REESTRUCTURACION_07.md) · [Propuesta de centro de ajustes](LABORATORIO_CENTRO_AJUSTES_PROPUESTA.md) · [PR #77](https://github.com/mxlzz/Nilo_public/pull/77) · [Issue #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Reauditoría: problemas y decisiones

Se revisaron laboratorio_motor.py y su UI, laboratorio_casos.py, laboratorio_contexto.py, historical_lab.py, los tres HTML del laboratorio, Simulation, los contratos físicos, la construcción exacta de payloads Gemini/Groq, configuración, checkpoints RNG, backups WAL y los issues de alcance #70–#73.

**Problemas confirmados:**
- El sandbox antiguo conservaba MotorLab._execute, que realizaba navegación, operaciones físicas, documentos y evolución de necesidades por un camino paralelo a Simulation.plan_ready/Simulation.tick. Al mejorar el motor real, el sandbox podía dar resultados distintos. Ese ejecutor se eliminó.
- Los otros laboratorios ya utilizaban Simulation y SQLite temporal o replay de copia. No era necesario crear otro simulador: se adoptó el motor único y se dejaron el banco de escenarios, depurador histórico y sandbox como **tres vistas del mismo motor**, accesibles desde el mismo servidor local.
- El laboratorio no disponía de controles implementados y verificables para guardar y aplicar variantes. Los cambios de parámetros pedidos no debían traducirse en edición arbitraria de código, ni mezclar recuperar ajustes con rebobinar una partida.
- El servidor del laboratorio no comprobaba explícitamente Host/Origin antes de operaciones; comparte ahora la protección local de la etapa 19.
- El sandbox antiguo leía el snapshot de una partida directamente; la nueva copia usa la API backup() de SQLite, incluida la información del WAL, y nunca abre el mundo origen para escritura.

## 2. Unificación de ejecución

**nilo_runtime/labs/sandbox.py** reemplaza MotorLab._execute. Su interfaz compatible MotorLab en laboratorio_motor.py conserva los nombres existentes, pero cada instancia dispone de un archivo SQLite **temporal propio** y ejecuta las acciones mediante el mismo recorrido de Simulation del programa: normalización, plan_ready, validación de plan, ticks, efectos físicos, mediciones, diagnósticos y archivo. La selección de pasos es sintética y explícita: **no se llama a Gemini/Groq y no se atribuye al personaje una decisión del observador**.

El panel de sandbox conserva la selección del mapa, inventario de prueba, acciones, resultados, fuente de ejecución y previsualización de contexto. La traza corresponde al código ejecutado, no a un flujo inventado. El resultado tipado de una acción sale de history/diagnostic; cuando no hay medición física, se informa esa ausencia y no se fabrica un éxito.

El banco de escenarios sigue ofreciendo el catálogo original, fixtures y decisiones prefijadas (sin llamadas LLM). El depurador histórico sigue trabajando en copias, con diferencias de resultados y límites de replay explícitos. Los tres pueden abrirse desde el nuevo centro de ajustes.

**Nota de compatibilidad:** la duración reportada por algunos handlers es una estimación; el tiempo real del motor y de un descanso se observa en la medición y en el reloj. Los tests anteriores del sandbox se adaptaron para comprobar el tiempo medido y el registro de cuaderno adicional, sin cambiar las leyes de descanso.

## 3. Perfiles: parámetros seguros de la primera entrega

**nilo_runtime/core/lab_settings.py** es el esquema único validado; **nilo_runtime/labs/profiles.py** gestiona archivos y checkpoints. Formato JSON v1, sin credenciales y con versión. Primer conjunto de controles editables:

| Parámetro | Rango | Efecto |
| --- | --- | --- |
| MAX_LLM_CALLS_PER_DAY | Entero 1–500 | Máximo de deliberaciones, sujeto a cuotas externas |
| MAX_CHAT_CALLS_PER_DAY | Entero 1–100 | Máximo de consultas de chat |
| MIN_REAL_SECONDS_BETWEEN_CALLS | Entero 10–300 | Separación real mínima de consultas |
| omit_context | Lista cerrada de 9 campos opcionales | Omite únicamente esas secciones del payload LLM, nunca las borra de la partida |
| prompt_note | Texto de hasta 700 caracteres | Complemento explícito a la instrucción de sistema Gemini/Groq; conserva el núcleo original |

La posición, las necesidades, el proyecto activo, las reglas físicas y la procedencia fundamental de evidencias **no pueden eliminarse mediante checkboxes**. Un cambio cognitivo es un cambio de información o instrucción comunicada al LLM, **no de física ni de memoria persistida**.

**Importante:** las leyes físicas y sus constantes no son editables en este primer perfil. Incorporarlas requiere aislarlas en un contrato compartido por todo el motor y definir invariantes y tests físicos. El centro actual no simula que una casilla cambia una constante todavía codificada en Python.

## 4. Solicitud real, comparación y aplicación

**nilo_runtime/labs/hub.py** construye vistas previas mediante build_deliberation_request, el mismo constructor empleado por las solicitudes LLM reales. Expone roles, texto de sistema, JSON de usuario, campos finalmente enviados, omisiones, modelo, bytes y huella del prompt, sin red ni claves HTTP. La comparación baseline/variante toma el mismo contexto de una Simulation temporal y produce un diff de payload y perfil. Opcionalmente ejecuta el mismo escenario físico dos veces con la misma semilla y operaciones prefijadas, aclarando que una variante del prompt no debe alterar resultados de una acción ya fijada.

El perfil **guardado** no altera Nilo. **Aplicar** comprueba tipos/rangos y crea automáticamente un checkpoint de la configuración previa, después guarda atómicamente lab_profiles/active.json, añade una auditoría con hash y requiere reiniciar Nilo. El motor carga ese perfil una sola vez al iniciar el proceso, antes de los overrides de variables de entorno; por ello un guardado externo no cambia parcialmente las reglas a mitad de deliberación.

**Restaurar ajustes** verifica el checksum del checkpoint, crea un checkpoint de deshacer y sustituye solo el perfil activo. No modifica Python, config.env, la identidad, el mapa ni el reloj. Ante fallo de escritura, el perfil anterior permanece vigente. Los checkpoints y variantes quedan bajo lab_profiles/, fuera del manifiesto de release y excluidos por .gitignore.

## 5. Recuperación de partidas, separada de los ajustes

El panel de backups usa la API SQLite backup() verificada en etapa 18. **Crear copia** guarda un snapshot consistente de la partida principal, incluidos sus datos WAL, en lab_profiles/world_backups. **Recuperar** lee ese backup y crea otra partida en lab_profiles/world_restores, con nombre nuevo. Nunca sustituye el save activo, rebobina el mundo en ejecución ni cambia la configuración del motor por el hecho de recuperar un archivo. Este procedimiento es deliberadamente independiente de los checkpoints de perfil.

Ninguna ruta HTTP admite nombres de perfil o respaldo que puedan atravesar directorios ni código Python evaluable. Los endpoints del laboratorio comprueban Host/Origin y cuerpos JSON; las operaciones que cambian archivos requieren confirmación explícita.

## 6. Cómo utilizarlo

Ejecutar ABRIR_LABORATORIO.bat. La portada sigue siendo **Escenarios** en http://127.0.0.1:8766/. La nueva sección **Centro de ajustes** está en /ajustes, junto a /sandbox y /historico. Se pueden guardar variantes, reabrirlas en el editor, comparar solicitudes Gemini/Groq, aplicar/restaurar ajustes y crear/recuperar copias de partida.

El laboratorio no incorpora todavía un editor irrestricto de fuentes Python. La configuración del proveedor y las claves API personales siguen siendo responsabilidad del archivo config.env y las variables de entorno actuales; nunca se muestran ni almacenan en perfiles.

## 7. Pruebas, límites y continuidad

- **tools/auditar_laboratorio_21.py:** comprueba propietario único del sandbox físico, presencia de Simulation.plan_ready/tick, capa core de perfiles, integración en gateway real, endpoints, backups y exclusión de ejecución arbitraria de Python.
- **tests/test_laboratorio_21.py:** pruebas de validación de límites, protección de campos esenciales, guardado, aplicación, checkpoints de deshacer, corrupción de hash, rollback ante fallo de disco, contraseñas/secretos fuera de perfiles, comparación de solicitudes sin red, comparación de escenarios físicos, respaldo WAL, restauración de partida como copia y HTTP real con rechazo cross-origin.
- Las pruebas históricas de MotorLab, escenarios, contexto y replay siguen en regresión. El paquete ZIP portable se amplió para incluir los nuevos módulos y laboratorio_ajustes.html.
- La validación de comportamiento autónomo con APIs reales no se acredita con estas pruebas sintéticas; está reservada a la etapa 23. La QA transversal y la medición de partidas largas corresponde a la etapa 22.
- La propuesta #73 de experimentos avanzados, cambios **físicos configurables** y comparación de respuestas LLM efectivamente generadas permanece como trabajo posterior. La etapa 21 entrega el primer subconjunto seguro y reversible.

**Estado de validación final:** se actualizará con los resultados verdes de CI antes de marcar formalmente esta etapa como completada.
