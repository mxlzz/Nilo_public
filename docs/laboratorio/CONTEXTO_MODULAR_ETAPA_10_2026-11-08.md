# Nilo 0.7.1 · Etapa 10 — selección de contexto e instrucciones modulares

**Fecha:** 2026-11-08  
**Base:** etapa 09, PR #93, rama `work/0.7.1-lab-stage09-contracts`.  
**Modo:** experimental, **solo** para previsualizaciones y comparadores; `baseline` permanece predeterminado en toda deliberación real.

## Auditoría del constructor existente

- `brain.context_for` prepara gran cantidad de campos (incluidos campos opcionales vacíos); `project_context` proyecta datos perceptibles.
- `compact_context` incorpora un `contexto_reducido` incondicional y un orden fijo de campos. `bounded_context` aplica otro recorte por bytes. El motor físico y SQLite no se modifican.
- `context_focus` elige un único tema basándose principalmente en el texto del proyecto actual; una fabricación que ocurre durante un proyecto de exploración puede quedar fuera.
- Gemini envía `SYSTEM` como `systemInstruction` y manual completo en el mensaje de usuario; Groq envía `GROQ_SYSTEM` y catálogo abreviado en sistema. Ambos usan los mismos registros de acciones.
- El perfil actual solo admite los parámetros versionados y nueve exclusiones opcionales; cambiar el esquema para aplicar automáticamente un nuevo prompt invalidaría la compatibilidad. Por eso **esta etapa no modifica el formato del perfil ni la configuración activa**.

## Implementación

1. **Variante explícita `modular` en el gateway** (`_LAB_CONTEXT_MODE`). Cualquier valor no admitido se rechaza. Las solicitudes sin ese campo mantienen exactamente el comportamiento anterior.
2. **Focos concurrentes** derivados únicamente del proyecto vigente, preguntas de investigación abiertas y operaciones efectivamente registradas. No genera nuevas metas; no acepta instrucciones arbitrarias desde los textos históricos.
3. **Fuente única de reglas**: selecciona secciones por ID desde `prompts.POLICY_RULES`. Preserva un núcleo de autonomía, honestidad física, decisión y formato. Mantiene un índice navegable de **las 26 operaciones**, construido desde el registro real; agrega detalles operativos de los focos cuando corresponde. Las reglas físicas comunes de fabricación permanecen en la guía Gemini. No se crean contratos de operaciones paralelos.
4. **Campos vacíos con semántica explícita**: solo se pueden omitir vacíos de una lista permitida. Se conservan `proyecto_actual:null`, `resultados_de_acciones:[]`, `0`, `false`, ausencia de evidencia, identidad, proyectos y resultados físicos. Se distingue el dato desconocido de la prueba negativa.
5. **Desduplicación verificable**: solo filas con mismo ID **y contenido serializado idéntico** dentro de la misma sección; los IDs distintos, filas legadas sin ID y entradas contradictorias no se descartan ni se fusionan entre fuentes.
6. **Presupuesto**: se reutilizan los compactadores y los mismos topes por proveedor. La marca `contexto_reducido` se incorpora solo si hubo selección/reducción efectiva y cabe en el límite. El cuerpo HTTP completo continúa sujeto al tope de Groq.
7. **Recuperación de memorias multifoco opt-in**: se agregan preguntas abiertas y objetivos recientes de operaciones solo cuando la variante experimental pide `multi_focus=True`. El recuperador convencional continúa idéntico. El comparador construye ambas proyecciones desde **una misma instancia congelada de `Simulation`**, sin recrear otro mundo ni alterar el RNG. La memoria archivada no se modifica.
8. **Prueba A/B desde Centro de ajustes**: selector «Actual · baseline / Experimental · modular y multifoco». La comparación construye baseline y variante desde el mismo contexto/semilla, devuelve ambos cuerpos literales y sus hashes, sin consumir cuota. La selección de modo no se guarda ni se aplica a la partida ni a los perfiles.

## Límites y decisiones

- No se aplica la variante automáticamente a Nilo. La instalación continúa con el contrato anterior: el efecto conductual de la nueva composición **no está demostrado**.
- Los tokens por sección no se inventan; las comparaciones registran bytes. Los conteos reportados por un proveedor real pertenecen a la solicitud completa.
- El cambio de `agenda` a condiciones corporales cualitativas requiere adaptador de contrato y tests de frontera; por eso el modo modular utiliza la síntesis no numérica de agenda/delegación, sin presentar la API antigua de umbrales internos. Las capacidades siguen anunciadas.
- **Esquema JSON estructurado opcional:** se mantiene pendiente; no hay evidencia de compatibilidad de todos los métodos/operaciones con el endpoint elegido ni de mejora en calidad de decisiones. Un schema único no sustituye `normalize_decision` y validación física.
- Las secciones del laboratorio muestran el texto literal, no una interpretación del modelo. El selector cambia únicamente la vista previa/experimento local. No modifica historiales, respuestas almacenadas ni solicitudes ya efectuadas.
- La recuperación literal de recuerdos por ID puede conservar redundancia semántica; deduplicar textos parecidos sin acreditar que son el mismo hecho podría eliminar evidencia distinta.

## Aceptación y verificación

Pruebas en `tests/test_lab_stage10_context_modular.py`: preservación de null, 0, false y vacíos significativos; deduplicación con contradicciones; foco simultáneo por proyecto, investigación y acción; marcadores de reducción; catálogo completo; mismos roles del transporte, cuerpos Gemini/Groq debajo de límite; memoria relevante de preguntas simultáneas; comparador sin escritura; rechazo de modo no admitido.

El paquete Windows debe incluir `nilo_runtime/agent/context_modules.py` en `MANIFIESTO_SHA256.json`. La regresión completa y CI deben pasar antes de considerar cerrada la implementación.

**Pendientes de uso:** prueba visual con partida real y sidecar, evaluación manual de los bloques, ensayos comparables con proveedores reales consentidos, y eventual decisión de hacer aplicable una variante por perfil tras validar su efecto. No se fusionará en `main` hasta consolidar la pila de PR #85–#93.

## Próxima etapa 11

Runs controlados con igual estado de referencia y proveedor/modelo; evaluar decisiones efectivas, repeticiones, proyectos, memoria, autonomía y coste. La reducción de bytes es un indicador técnico, **no una demostración de mejores decisiones**.
