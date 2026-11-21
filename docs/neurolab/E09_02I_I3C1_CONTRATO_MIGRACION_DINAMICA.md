# E09.02i-I3c.1 — contrato de migración dinámica mínima (SOLO DISEÑO)

**Fecha: 2026-11-21. Estado: especificación de contrato, no implementación ni aprobación de topología.** Depende de [alternativas I3c](E09_02I_I3C_ALTERNATIVAS_MINIMAS.md), [I3b.3](E09_02I_I3B3_RESULTADO_MIGRACION.md), [migración C1 existente](../../experiments/neurolab/c1_migration.py) y [C1ContextBrain baseline](../../experiments/neurolab/c1_context_brain.py). Se conserva la pregunta rectoral de G09, si existe un cerebro mínimo que aprenda y retenga sin confundir efectos de tamaño o reglas externas.

## 1. Evaluación temprana de lo existente

- **Reutilizar** las transiciones de C1 del repositorio: C1SynapseState (plasticidad/fortaleza), Decision SVRule, c1_migration.decision_migrate con RandStream controlado, y los generadores de estímulos/chemistry ya auditados.
- La nueva necesidad no es un migrador desde cero, sino un **adaptador runtime de fuente dinámica**: el selector actual calcula source=(índice%4)//2, no lee identidad persistida. Un objeto de fuente debe viajar con cada dendrita. Ninguna solución existente en este repo satisface exactamente ese contrato de integración, sin afirmar que sea imposible fuera del repo.
- **No** cambiar el baseline ni corregir post hoc I3b.2 mediante reinicio artificial.

## 2. Contrato de estado propuesto (B: 6 unidades, 4 contactos)

Entidades mínimas:
- SourceRegistry: fuentes Concept C0/C1, IDs persistentes 0 y 1 con punteros sintéticos no nulos diferenciables (por ejemplo 0x1000 y 0x2000 **solo como etiquetas**, no VA reales). El mapa de IDs no se reconstruye a partir de posición de contacto.
- DynamicDecisionDendrite: state C1SynapseState + source_pointer; 1 contacto exc y 1 inh por Decision, total 4. El estado dendrítico siempre conserva tipo gen (exc/inh) y la identidad de origen aunque su fortaleza sea cero, hasta migración.
- DynamicBrainState: 2 estados y outputs de Decision, 2 outputs de Concept, cuatro dendritas tipadas, logical_tick y RandStream o un generador serializable con semántica de consumo definida. No se permite azar global ni PRNG oculto.
- Separation: no añadir acceso a evaluador, sign de recompensa, target, mapping ni próxima acción correcta en API del cerebro; observador externo computa métricas sin alterar inputs.

## 3. Transición por tick y evento de reconexión

- Preservar orden Decision (lee Concept previo) → WTA y estados → Concept actualizado, y química con retardo, como I2; reutilizar update_c1_synapse, sin modificar genes/umbrales ni divisores LTW.
- Los cambios C1SynapseState conservan su evolución aun si la fuente indicada es otra: la lectura de output se hace por source_pointer, no por índice de slot.
- Cuando una actualización de fortaleza informa lost_connection, el contacto conserva identidad de slot pero strength=0 y LTW/STW/susceptibility=0. El **instante de migración** posterior se debe fijar con evidencia del invocador real en el EXE C1 o declarar una convención N; no dispararla en un tick arbitrario sin identificar el régimen.
- Llamar c1_migration.decision_migrate solo desde una capa adaptadora que construye MigrationState con todas las fuentes y el grupo de su clase, recipient_output tipado y RandStream. En tipo1 hay rechazo de fuente duplicada y chequeo de receptor activo. Validar el origen devuelto, luego transportar todo el estado de dendrita migrado de vuelta al slot. **No** adaptar fórmulas de plasticidad para obtener éxito.
- La conexión nueva debe recibir LTW/strength iniciales conforme a parámetros genéticos de migración verificados; si todavía faltan en GEN, establecer fixture sintético etiquetado y mantener puerta histórica abierta.

## 4. Oráculos y gates antes de ensayar conducta

Gate C1 (estructura): 4 contactos, ID fuente estable, ningún duplicado por clase, reconstrucción completa al restaurar checkpoint, misma trayectoria bajo replay determinista.
Gate C2 (migración): test rechazo duplicate_source sin cambiar estado, test inactive_recipient sin consumir random, aceptación de fuente libre con rand explícito, mismo cursor/orden antes/después, no creación ni pérdida invisible de contacto, y reset según configuración.
Gate C3 (comparabilidad): A=red actual 6/8 sin migración, B=6/4 sin migración, B+=6/4 con migración, D=6/8 con reinicio misma fuente **explícitamente no histórica**. El coste en contactos y expresividad difiere: aislar **efecto de migración** primariamente como B+−B; A−B mide capacidad, A−D evalúa restauración, nunca presentar B+−A como efecto puro.
Gate C4 (científico): preregistrar semillas nuevas (distintas de 200..419), episodios y sinopsis de parámetros, controles con el mismo presupuesto de recompensa y visibilidad del evaluador, retención/velocidad/reversión/atribución distractores, blind holdout y resultados por semilla. G05/G09 solo con evidencia comportamental independiente.

## 5. Riesgos aún no resueltos

- Scheduler exacto de selección de destinatario migratorio y origen de random() históricos siguen incompletos; no reconstruirlos de forma arbitraria.
- Con solo 1 dendrita/clase por Decision, no se pueden representar simultáneamente ambas señales del Concept dentro de esa clase, lo que puede empeorar fuertemente clasificación/reversión; por eso B sin migración es indispensable.
- Cambiar arquitectura puede transformar mecanismo de decisión y sensibilidad a distractor; la comparación no aísla automáticamente todo, incluso bajo mismos seeds.
- Un migrador que sustituye la fuente cuando pierde fortaleza puede **borrar información útil**; migración no equivale a consolidación.
- La dinámica C1 neuronal no resuelve la procedencia causal de recompensa demorada; G05 sigue abierta aunque B+ migre.

**Estado final:** diseño delimitado, NO código experimental nuevo, NO autorización para afirmar que B es superior, NO aumento de neuronas, NO cambios a Nilo0.7/main. Siguiente decisión técnica: verificar cómo y cuándo el EXE invoca migración Type1, o marcar la convención N para poder construir un prototipo experimental aislado; después preregistrar primero gates de datos/persistencia, luego prueba conductual con nuevas semillas.
