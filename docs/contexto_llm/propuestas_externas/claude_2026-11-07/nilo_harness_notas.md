# Nilo v2: cambios de harness (lo que NO se resuelve con el prompt)

## generationConfig

```json
{
  "temperature": 0.65,
  "maxOutputTokens": 4096,
  "responseMimeType": "application/json",
  "responseSchema": "<contenido de nilo_response_schema.json>"
}
```

- `maxOutputTokens` 2300 -> 4096. Si `finishReason == "MAX_TOKENS"`: reintentar una vez agregando al user message "Respuesta anterior cortada. Devolvé un plan de máx. 6 ops, sin agenda ni actividades_en_espera."
- Gemini suele aceptar tipos en mayúscula (`OBJECT`) en `responseSchema`. Si usás `responseJsonSchema`, pasalos a minúscula.
- Si el schema es rechazado por complejidad, recortá primero `parts/joints/components` (campos de assemble/design) y dejá que esas ops se emitan con un schema reducido solo cuando el modelo las necesite.

## Validación post-schema (el schema no lo expresa)

- `plan`: 2-12 ops, salvo que `accion_proyecto` sea completar/abandonar/pausar (entonces `[]`).
- `completar` exige `prueba_cierre` >= 12 caracteres y `proyecto_id`. `continuar`/`pausar`/`abandonar` exigen `proyecto_id` válido. `nuevo` exige `objetivo`.
- `cuaderno` <= 350 caracteres (truncar o reintentar).
- Remapear `design_prediction` -> `prediction` (string) cuando `op == "design"`. Motivo: en el contrato actual `prediction` es objeto en build/craft/use y string en design; un schema no admite dos tipos para la misma clave.
- `agenda` / `actividades_en_espera`: descartar si `habilidades_verificadas` está vacío.

## Contexto de turno (user message)

1. Omitir toda clave `null` o `[]`. En el turno 1 quedan ~10 claves en vez de ~40.
2. Inyectar `nota` junto al dato cuando el campo aparece. Textos sugeridos:

| Campo | nota |
|---|---|
| ultimo_cierre_rechazado | criterio_no_instrumentado = el motor no puede medir ese criterio; no es fracaso. Reformulá hacia lo medible, pausá o abandoná. Medir otra variable no lo resuelve. sin_mediciones_del_proyecto = faltan resultados de ese proyecto; no es fracaso. |
| revision_de_estrategia | Señal observacional de deliberaciones parecidas sin avance medido. Podés cambiar una variable o el método; no estás obligado a abandonar. |
| proyectos_reanudables | Proyectos pausados cuyo recordatorio se cumplió. Retomarlos es opcional; no hay ejecución automática. |
| antecedentes_relacionados / investigaciones_pausadas_relacionadas | Decisiones y resultados reales de temas parecidos. Reformular no es evidencia nueva ni borra el motivo de la pausa. |
| inconsistencias_recoleccion_previas | Un gather que solo desplazó la posición no obtuvo material. Usá el material realmente obtenido y replanteá la hipótesis. |
| predicciones_contrastadas | Coincidir en una variable no verifica tu hipótesis causal ni otras funciones (retener agua no demuestra purificarla). Variable sin medir = pregunta abierta. |
| evaluaciones_externas_recientes | Aportan información, no cambian resultados del motor. Contrastalas con tus mediciones. |
| fenomenos_no_evaluables_recientes | No evaluable = el motor no modela ese fenómeno; no es fracaso del objeto. Podés adjuntar su ID en un propose. |
| diagnosticos_operativos_recientes | Distinguí uso incorrecto, limitación no modelada y posible contradicción verificada. |

3. Sacar de `regla` todo lo que ya está en el prompt (excavar requiere punta, agua no caminable, arena/arboleda transitables). Dejar solo `"La verdad física proviene del motor."` o eliminarlo.
4. `contexto_reducido`: emitir solo si hubo resumen real, y sin la referencia a un "diario" (no hay op para consultarlo).
5. Agregar `metricas_validas` (lista real de métricas que mide el motor) para reemplazar los ejemplos `capacidad_util_agua` / `threshold: 70` que hoy sesgan hacia recipientes. En la descripción de ops, usar `"metric":"<metrica_de_metricas_validas>"`.

## Descripciones de ops (editar el bloque de ops)

- Sacar números de fisiología: `drink` ("0,18 unidades", "+27 hidratación") y los `menor_que: 60`. Nilo no conoce esas cifras; usar niveles cualitativos (`algo`/`mucho` de hambre/sed/cansancio).
- `descend`: tiene pegado el texto de `ascend`. Escribir sintaxis propia: `{"op":"descend"}` y qué condición exige (estar junto al portal conocido).
- Quitar las reglas duplicadas de las ops (golpear no rompe paredes, excavar exige punta ya figuran en la op correspondiente; no repetirlas en prompt ni en `regla`).
- Definir y documentar qué pasa si un paso del plan falla (aborta el bloque o sigue). Completar la línea `[DEFINIR SEGÚN MOTOR]` del prompt.
- Verificar que `mensaje_sistema` y `systemInstruction.parts[0].text` no viajen los dos al modelo. Si `mensaje_sistema` es solo log, ignorar.

## Pendientes de decisión tuya

- `avance_estimado`: lo dejé opcional. Si el motor lo exige, ponerlo en `required` y aceptar números poco informativos.
- Lista de los estados del glosario: confirmá que los nombres coinciden con las etiquetas reales que emite el motor.
- `nivel: algo|mucho` para `cuando_necesidad`: asume que el motor puede mapear sensaciones a un umbral interno. Si no, cambiar a las etiquetas que ya muestra `necesidades` ("sin sed", "con mucha energía", etc.).