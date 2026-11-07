# Nilo 0.7.1 — Laboratorio, etapa 06: revisión y exportación de contexto

**Fecha:** 2026-11-07. **Rama:** work/0.7.1-lab-stage06-revisiones, apilada sobre la etapa 05 (PR #89).
**Estado:** implementado en rama, pendiente del resultado final de CI y de una revisión de interfaz con una partida real.

## Necesidad

El usuario observa una deliberación o una previsualización y selecciona **qué bloques del contexto considera candidatos a exclusión**, dejando notas por bloque o una observación general. Puede exportar un único JSON autocontenido y adjuntarlo a otro asistente para examinar **si la exclusión tiene sentido y cómo debería implementarse**. El propósito no es cambiar el prompt desde la pantalla: esta etapa solo guarda una propuesta.

## Flujo de interfaz

El mismo control está disponible en tres lugares:

- **Solicitudes LLM**: sobre un intento HTTP archivado del proveedor, segmentado en bloques literales; el botón «Exportar revisión (.json)» queda arriba de la ficha. Cada bloque y cada sección desplegable tienen un checkbox «Proponer excluir». Las notas del campo son opcionales. La selección se mantiene al pasar entre vista Simplificada y Profesional; cambia al seleccionar otro intento.
- **Pruebas → Escenarios**: la previsualización del proveedor y momento elegidos admite los mismos checks; se identifica como **solicitud calculada, nunca enviada**. Las revisiones de cada proveedor/momento se mantienen separadas.
- **Ajustes**: tanto el baseline como la variante calculada tienen su propio botón de exportación y checks independientes. **Los checks son propuestas de revisión y NO se sincronizan con los checks preexistentes que realmente modificarían un perfil de prueba**.

**Los valores de los bloques son siempre literales.** Los títulos, familias, indicaciones y observaciones no se insertan en el prompt ni alteran la representación del mundo.

## Artefacto exportado: nilo.lab.context_review.v1

El archivo local contiene:

- Fuente declarada: HTTP capturado o previsualización calculada; el modelo, proveedor, propósito, intento, llamada y momento o semilla cuando corresponda.
- Versión del motor **instalado**, obtenida mediante un endpoint local de solo lectura. El commit se registra como **desconocido** cuando el paquete no lo proporciona; jamás se inventa. La versión instalada no necesariamente coincide con la versión que produjo una captura antigua.
- **Cuerpo literal de la solicitud completa**, bytes, SHA-256, mensajes por rol y ruta y catálogo de bloques con offsets en puntos de código Unicode y hashes. Se comprueban los mensajes contra sus rutas originales en el cuerpo JSON.
- Lista explícita de propuestas: ubicación exacta del fragmento, literal conservado, hash, observación humana y estado "propose_exclusion_only".
- Bandera que indica si el campo pertenece a los campos **opcionales del perfil instalado**. **Todas las propuestas requieren revisión humana**, aun las opcionales; una exclusión de sistema o de campo obligatorio no se aplica.
- Observación general y advertencias de alcance.
- **Ningún prompt modificado ni modelo reejecutado**: el artefacto es una revisión del contexto original y una lista de propuestas.

Los valores privados presentes en el prompt podrían aparecer en el archivo. El usuario debe revisar el JSON antes de adjuntarlo. El exportador no envía ese JSON a la red ni lo almacena en la base de la simulación: genera un archivo local en el navegador.

El origen “HTTP capturado” representa un **intento registrado al construir/activar el transporte**; en fallos de red no demuestra recepción efectiva del proveedor. El estado del intento permite interpretar ese límite.

## Integridad y seguridad

La construcción de la revisión comprueba: SHA-256 del cuerpo y de cada mensaje, concordancia de los textos con sus rutas JSON, continuidad de offsets y reconstrucción literal de todos los segmentos, identidad de cada bloque con su subcadena Unicode, y SHA-256 del literal seleccionado. Las notas tienen límites de tamaño.

El frontend usa controles de texto DOM, sin interpretar HTML de un proveedor. El único endpoint nuevo es GET /api/lab/audit/info, sin parámetros arbitrarios: devuelve VERSION del motor instalado y la lista existente de OPTIONAL_CONTEXT. La implementación se integra a los **únicos dos assets compartidos ya permitidos**, assets/laboratorio_ui.js y assets/laboratorio.css, manteniendo la misma lista de rutas autorizadas y sin dependencias externas. El visor espera a que el script diferido esté disponible antes de activar el auditor. No se agregan rutas POST, modificaciones de SQLite o acceso remoto.

## Límites de la etapa

- No hay exclusión aplicada al motor ni preview alternativo del prompt quitando bloques: el archivo describe la propuesta sin fingir que el JSON resultante es sintáctica o semánticamente válido.
- No se crean nuevas claves opcionales en el perfil; el motor sigue prohibiendo ocultar contexto esencial.
- No se modifica la captura HTTP original ni la procedencia archivada.
- No incluye ablación multiejecución, evaluaciones de comportamiento comparadas ni matriz de muchos turnos.
- Un hash demuestra identidad del texto pero no la exactitud de un testimonio del LLM ni la utilidad de una memoria.

## Criterios de aceptación

1. Exportación sin selección (solo observación general) y con una o varias exclusiones, incluyendo notas individuales.
2. Correspondencia del fragmento con el cuerpo original, por ruta, SHA-256 y offsets; casos con caracteres Unicode de más de una unidad UTF-16.
3. Rechazo de cuerpo manipulado, rutas falsas, bloques diferentes y notas fuera de límite.
4. Diferenciación inequívoca entre capturas reales y previsualizaciones sin red.
5. Checkboxes de familias que activan y desactivan todos sus campos y no pierden la posición original.
6. Fields del sistema/contrato etiquetados como **revisión obligatoria**; no escritura sobre el perfil.
7. Los tres visores siguen funcionando y JS compila; las pruebas históricas de tema, seguridad y navegación comprueban que se mantiene **una sola hoja de estilo y un solo script externo compartidos**.
8. Windows portátil incluye ambos assets nuevos y toda la regresión pasa.

**Siguiente etapa:** validación de experiencia real y organización de hallazgos; después se abordarán la matriz de presencia entre turnos y los experimentos comparativos según la hoja de ruta.
