# Laboratorio como centro de ajustes del motor — propuesta del 4/11/2026

> **Estado:** diseño exploratorio documentado, **pendiente de aprobación**. No hay versión asignada, implementación iniciada ni modificación de la física, el prompt o la configuración de una partida por registrar esta propuesta. Guía principal: [issue #70](https://github.com/mxlzz/Nilo_public/issues/70); seguimiento: [#71](https://github.com/mxlzz/Nilo_public/issues/71), [#72](https://github.com/mxlzz/Nilo_public/issues/72), [#73](https://github.com/mxlzz/Nilo_public/issues/73).

## Objetivo

Convertir el laboratorio existente en el punto central para **entender el motor, experimentar con reglas y prompts, observar el contexto que recibe el LLM, comparar variantes y aplicar/restaurar configuraciones de forma verificable**. La herramienta debe conservar Escenarios (68 casos), Sandbox y Partidas históricas; la interfaz técnica se organiza por tareas, sin estética obligatoria compartida con el juego.

La premisa de arquitectura es **separar variantes experimentales del motor instalado**, y no modificar archivos Python al pulsar un control. Los ensayos deben recorrer el **mismo motor** que utiliza Nilo, sobre estado o SQLite aislados. Para aplicar un cambio a la instalación real se necesita una operación explícita y respaldada.

## Secciones previstas

| Sección | Alcance | Salida verificable |
| --- | --- | --- |
| **Parámetros** | Controles por subsistema (física, necesidades, tiempos y planificación), tipados con rangos, unidades, origen, dependencias, documentación y valor vigente. | Diff entre variante y baseline; efecto sobre escenarios; valores inválidos rechazados. |
| **LLM y contexto** | Editor/versiones de instrucciones Gemini/Groq, núcleo compartido y contratos de respuesta; filtros por campos o grupos con checkboxes. | Mensaje final por proveedor, con roles, instrucciones, acciones, valores, omisiones, tamaño y comparación antes/después. |
| **Simulaciones** | Catálogo de escenarios, sandbox de planes y replay desde checkpoints de partidas. | Resultados físicos, invariantes y trazas reales, con semilla, perfil y versión. |
| **Comparador** | Baseline frente a una o más variantes desde las mismas condiciones iniciales. | Diferencias de contexto, planes, resultados, inventario, tiempo, proyectos, memoria y métricas. |
| **Versiones** | Configuraciones y checkpoints nombrados, backups automáticos, aplicar y restaurar. | Historial de cambios, hashes, versión y posibilidad demostrada de recuperación. |

Los **checkboxes de contexto** afectan qué se comunica al LLM; **no** eliminan hechos, memoria archivada, necesidades ni leyes del mundo. La vista de observador puede mostrar valores internos que jamás recibe el LLM. La salida para Gemini y Groq debe construirse mediante los mismos contratos reales y señalar cuando un campo no es editable porque es requisito del protocolo o de consistencia cognitiva.

El **editor de prompts** debe permitir cambios en una variante y mostrar su efecto literal sobre la solicitud preparada. No se debe ejecutar una consulta de pago para generar una vista previa. El proveedor efectivo puede cambiar por fallback, por lo que las variantes deben identificar proveedor/modelo y diferenciar **solicitud preparada** de **solicitud efectivamente enviada**.

## Tres etapas independientes, priorizadas por utilidad

### A. Entorno experimental, sin tocar motor instalado — [#71](https://github.com/mxlzz/Nilo_public/issues/71)

Introducir perfiles de ajustes en un formato estructurado y validado. Editar las instrucciones, activar o desactivar información del contexto, guardar/cargar variantes y comparar dos escenarios desde el mismo estado y semilla. Extraer gradualmente constantes actualmente integradas en Python para poder configurarlas **sin duplicar física**. Mostrar origen, transformación y destino de cada campo del contexto. Registrar la configuración exacta usada en cada ensayo.

**Aceptación:** cambiar un campo cambia el payload de prueba como se espera, pero no el estado ni la configuración global de Nilo; pruebas de igualdad con baseline y de aislamiento.

### B. Aplicación segura, backups y restore — [#72](https://github.com/mxlzz/Nilo_public/issues/72)

Guardar y cargar **checkpoints de configuración** con nombre; al pulsar **Aplicar al motor**, realizar validación y copia automática previa de configuraciones/archivos afectados con manifest y hashes. Preparar aplicación atómica y rollback ante error; exigir detener/reiniciar el motor si los cambios no pueden cargarse en caliente. **Restaurar** selecciona un backup verificable y revierte el motor/configuración. La partida se conserva por defecto.

El checkpoint **completo de una partida** es otra operación: si se solicita, copiar SQLite de forma coherente (incluido WAL) con la API de backup de SQLite. Nunca mezclar «restaurar ajustes» con «volver al día N de la partida» sin una decisión explícita.

**Aceptación:** aplicación/restauración deja un historial legible; ante falla de escritura se conserva la configuración original; la base de la partida no retrocede al restaurar reglas.

### C. Experimentos avanzados — [#73](https://github.com/mxlzz/Nilo_public/issues/73)

Ampliar parámetros físicos configurables con invariantes, comparar resultados de múltiples perfiles/versions, y ejecutar **deliberaciones reales con Gemini/Groq** solo cuando el observador lo solicite y pueda revisar proveedor, modelo y costo. Comparar resultados físicos por semilla y decisiones cognitivas mediante corridas repetidas, sin prometer reproducibilidad de las respuestas del LLM.

**Aceptación:** informe reproducible/exportable con perfiles, checkpoints, versiones, salidas, medidas y límites de inferencia. Los cambios de conducta requieren evaluación con LLM real, no solo pasar tests deterministas.

## Recuperación y seguridad: requisitos transversales

- **Reglas/configuración vs. estado del mundo**: registros y backups distintos. No alterar ni borrar mundos por aplicar/restaurar un perfil. Conservar backups **fuera** de la carpeta que se sobrescribe.
- **Modificaciones acotadas:** nada de ejecución arbitraria de Python ni edición irrestricta de rutas desde el servidor local; endpoints de escritura explícitos, validación de tipos, rangos, dependencias y versiones.
- **Aplicación en uso:** proteger o pausar la instancia activa antes de modificar archivos que un proceso ya tiene cargados; verificar restauración sin corrupción.
- **Auditoría:** almacenar cambios, hashes, perfil, semilla, motor, prompt, proveedor y si la acción se ejecutó en el sandbox o se aplicó.
- **Reproducción:** respetar los límites documentados en [LABORATORIO_HISTORICO.md](LABORATORIO_HISTORICO.md): UUID, RNG, reloj real y evidencias archivadas pueden impedir identidad bit a bit; los checkpoints de 0.6.3 son históricos de mundo, **no** checkpoints de configuración.
- **Pruebas:** además de verificar que una operación termine, controlar invariantes físicas y diferencias concretas, especialmente [#67](https://github.com/mxlzz/Nilo_public/issues/67), [#68](https://github.com/mxlzz/Nilo_public/issues/68) y [#69](https://github.com/mxlzz/Nilo_public/issues/69).

## Decisiones pendientes antes de programar

- Primer conjunto pequeño y útil de parámetros; no abrir todo el motor de golpe.
- Formato/versionado de perfiles, defaults y migración; manejo de variables vinculadas y campos requeridos.
- Qué clases de ajustes son de carga inmediata y cuáles exigen detener/reiniciar Nilo.
- Alcance del backup de «motor original»: configuración solamente, archivos Python afectados o instalación completa en cambios de código.
- Método de comparación y métricas que respondan a problemas concretos, sin imponerle a Nilo proyectos, prioridades ni objetivos.
- Si la aplicación al motor real se habilita dentro de la primera entrega o después de validar las variantes; la propuesta recomienda **A → B → C**.

Esta propuesta es deliberadamente reversible y revisable: un issue abierto no representa autorización para cambiar la vida del personaje ni para publicar una versión.
