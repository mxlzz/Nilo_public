# Nilo 0.5.8.3 — Primer contrato de resultados físicos

## Frontera de evidencia

```text
brain (propone JSON)
    ↓
Simulation (coordina tiempo, plan y archivos)
    ↓
Environment.perform_result (interfaz física)
    ↓
world.execute_action (reglas deterministas existentes)
    ↓
ActionResult (evaluación + hechos + mediciones verificadas)
    ├── experiment_log.measure  → mediciones
    ├── inventions/action_outcomes → historial y diagnósticos
    └── brain.context_for      → JSON compacto para el LLM
```

Una respuesta del LLM no puede suministrar `ActionResult`. Lo fabrica el motor
tras ejecutar cada acción. Las fuentes de evidencia son la nueva clave de
conocimiento verificado para experimentos y las nuevas pruebas de objetos,
identificadas por su contador previo. Para física ausente se exige el registro
de una tentativa `unmodeled_attempts` creada durante la ejecución.

Ejemplo (simplificado):

```json
{
  "op": "experiment",
  "status": "verified_success",
  "success": true,
  "notable": true,
  "duration_minutes": 18,
  "facts": ["Al golpear piedra..."],
  "physical": {
    "kind": "material",
    "subject": "piedra",
    "method": "golpear",
    "metrics": {"dureza": 7},
    "conditions": {"material": "piedra", "metodo": "golpear"},
    "precision": "escala estimada del motor, 0–10"
  }
}
```

La duración incluida en `ActionResult` es la duración nominal informada por la acción física. El tiempo transcurrido efectivamente en la simulación se registra aparte en `measurement.duration_minutes`; ambas cantidades no son necesariamente iguales.

La narrativa se conserva como explicacion para lectura humana. Cambiar la
redacción no debe alterar `status` ni `physical`.

## Compatibilidad

- `ActionResult.as_legacy()` preserva el protocolo de cuatro valores donde
  quedan módulos por migrar.
- Los registros anteriores sin `action_result` siguen siendo válidos.
- `measure` admite `action_result`; solo su ruta antigua sin el contrato
  mantiene heurísticas de texto para usuarios legados.
- `world.execute_action` conserva su implementación y reglas físicas;
  `IslandEnvironment` aporta el adaptador.
- No se presenta un segundo mundo jugable ni se cambia la información
  disponible antes de que Nilo observe o experimente.

## Próximo objetivo

Hacer que cada ley física devuelva el propio `ActionResult`, eliminando
adaptadores y texto como origen de métricas. Tipar también navegación,
investigación y hábitos; migrar progresivamente todos los consumidores
internos de cadenas narrativas hacia campos verificables.
