# Laboratorio Nilo 0.7.1 · Etapa 05 — Inspector literal del contexto LLM

**Fecha:** 2026-11-07. Rama work/0.7.1-lab-stage05-contexto sobre etapa 04, PR #88.  
**Alcance:** presentación y lectura. Sin cambios a física, prompts, proyección cognitiva, deliberación, memoria ni cuotas.

## Problema y solución

El observador necesita encontrar información dentro de la **solicitud realmente enviada**, sin convertirla en una paráfrasis, inferir qué hizo el personaje con ella o perder los datos originales.

**Solicitudes reales (/visor-llm):** el modo Simplificada ahora organiza los fragmentos por rol y familia dentro de cada rol, con títulos y subtítulos breves. Las familias actuales son situación/entorno, proyectos/actividad, acciones/resultados/mediciones, memorias/conocimiento y campos restantes. El cuerpo exacto se sigue viendo en modo Profesional. La clasificación es únicamente editorial y los campos desconocidos se conservan íntegros.

**Orden de lectura:** los campos originales no se reordenan. Si un campo de una familia aparece de nuevo después de otra familia, se crea una segunda sección de esa familia. Las opciones del índice llevan al bloque exacto y despliegan sus ancestros. La puntuación y espacios del JSON, que no son valores de campo, siguen en los segmentos originales y en el cuerpo HTTP completo.

**Episodio:** el detalle de cada intento de deliberación muestra sus relaciones archivadas, cuando hay identificadores exactos: decisión normalizada, checkpoints y acciones vinculadas al cuaderno. Una solicitud aceptada no demuestra ejecución física. La ausencia de vínculos se muestra sin inventarlos.

**Escenarios (/):** las vistas previas muestran mensajes literales por rol y campo, usando el mismo indexador del visor HTTP sobre el cuerpo serializado que construiría el motor. Se distinguen expresamente de consultas reales: el modelo no fue llamado.

**Ajustes (/ajustes):** «Ver solicitud exacta» y «Comparar con baseline» incorporan bloques literales agrupados, con la misma procedencia de solicitud **calculada y no enviada**. El JSON técnico anterior permanece accesible. Los checks de omisión preexistentes permanecen tal como estaban: el flujo nuevo de selección y exportación corresponde a la etapa 06.

## Fidelidad y procedencia

- El texto de cada bloque es una subcadena del texto **ya capturado o ya construido**; no se crea una versión corregida ni se reserializan campos al mostrarlos.
- Cada bloque y cada mensaje tiene SHA-256 del texto UTF-8. La segmentación conserva offsets consecutivos y la concatenación de todos los segmentos equivale exactamente al mensaje.
- El cuerpo HTTP real sigue verificado por SHA-256 antes de mostrarse. La procedencia por etapa puede estar completa, parcial o ausente; no se inventa.
- Los previews se identifican como previsualizacion_calculada_sin_red y no se confunden con una respuesta real.
- Los campos eliminados antes de componer la solicitud no reaparecen por el hecho de ser indexados.
- Las etiquetas editoriales no se agregan al prompt ni se exponen a Nilo.
- El tokenizador de proveedor puede ser distinto; no se inventan tokens exactos por bloque.

## Pruebas de aceptación

1. Segmentación sin pérdida y offsets/huellas SHA correctos en Gemini, Groq y compatible OpenAI.
2. Campos desconocidos, comillas escapadas, Unicode y familias intercaladas sin pérdida ni reordenación.
3. El texto libre de chat permanece literal, sin falsificar campos de deliberación.
4. Los previews de escenarios y perfiles coinciden byte a byte con el serializador del transporte, sin enviar solicitudes.
5. Un campo interno excluido sigue excluido de los bloques.
6. Los vínculos de episodios solo aparecen cuando están archivados y verificables.
7. La interfaz conserva el modo Profesional y los visores existentes. Sintaxis JavaScript correcta.
8. Suite de regresión y Windows portátil sin regresiones.

**Etapa 06:** checks junto a los bloques, notas humanas y exportación autocontenida para adjuntar a una IA y revisar qué cambiar. No aplicar esos cambios automáticamente al motor.

**Etapa 08:** análisis de presencia entre turnos, matrices y experimentos de ablación, separados de la lectura literal.
