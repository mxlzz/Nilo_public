# NeuroLab — protocolo de evaluación, controles y evidencia

**Estado:** pre-registro metodológico, todavía no hay datos. Los números propuestos son parámetros iniciales del banco de pruebas, no resultados ni características de C1.

## 1. Contrato de cada experimento

Antes de ejecutarlo crear una ficha desde [PLANTILLA_ENSAYO.md](PLANTILLA_ENSAYO.md) con:
- ID estable `NL-E##-T##-R##`, etapa y mecanismo modificado;
- hipótesis falsable y alternativa nula;
- versión exacta del código/commit, rama y dependencias;
- parámetros del cerebro, pesos iniciales, regla de actualización y topología;
- generador de entradas (versión, semillas, estado RNG), secuencias y cantidad de ciclos;
- función del evaluador, refuerzo y duración, **sin exponer la respuesta correcta al módulo cerebral**;
- condiciones de entrenamiento, evaluación, holdout, baselines y ablaciones;
- criterio de aceptación previamente elegido, riesgos de fuga/contaminación y conducta esperada del control;
- dónde se almacenarán registros crudos, métricas y errores.

**Identidad de ejecución:** registrar SHA del código, SHA de configuración y entradas; un ID de experimento no reemplaza el hash del contenido. Al reejecutar bajo otro commit, registrar nueva corrida, no sobrescribir la original.

## 2. Semillas, muestras y particiones

- **Propuesta inicial, no dogma estadístico:** semillas de desarrollo 0–19 y semillas de evaluación 100–119, bloqueadas antes de mirar el resultado. Más muestras cuando la variabilidad o la comparación lo requieran.
- Generar secuencias independientes para entrenamiento y evaluación. Mantener un conjunto `holdout` nunca visto durante ajuste de hiperparámetros.
- Para comparar algoritmos A/B, usar en lo posible **las mismas** secuencias de estímulos, estado inicial equivalente y presupuesto de ciclos/refuerzos; registrar dónde esto no es realizable.
- Al revertir contingencias, separar entrenamiento original, shock, reentrenamiento y test sin refuerzo.
- Si un cambio se realiza después de mirar resultados de evaluación, ese conjunto pasa a **desarrollo**; reservar otro holdout genuino.
- No seleccionar únicamente los mejores 3 runs ni cambiar retroactivamente la métrica.

## 3. Baselines indispensables

| ID | Control | Pregunta |
|---|---|---|
| BL-0 | Decisor uniforme aleatorio | ¿Mejora frente al azar? |
| BL-1 | Misma red con pesos congelados | ¿La diferencia depende de plasticidad? |
| BL-2 | Tabla estímulo→acción con actualización simple | ¿Una red neuronal aporta más que un método elemental? |
| BL-3 | Un único peso adaptable | ¿STW/LTW aporta algo distintivo? |
| BL-4 | Sin elegibilidad temporal | ¿Se necesita la traza para refuerzo retrasado? |
| BL-5 | Memorizador de patrones completos | ¿Existe transferencia a combinaciones no vistas? |
| BL-6 | Conexiones fijas con igual presupuesto | ¿Migración aporta mejora neta? |
| BL-7 | Red sin recurrencia | ¿Qué fenómeno interno depende de ella? |

Los controles se activan **cuando la etapa lo amerita**, no hace falta escribirlos todos en E01.

## 4. Banco de pruebas definido antes del entrenamiento

| Ensayo | Entrada | Refuerzo/evaluación | Medida primaria |
|---|---|---|---|
| T01 activación | Impulso 0→1→0 | Sin recompensa | Trayectoria de activación vs cálculo independiente |
| T02 inhibición | Dos entradas contrarias | Sin recompensa | Signo, saturación y cambio de salida |
| T03 reposo | Desconexión de entrada | Sin recompensa | Tiempo de relajación y estado estable |
| T04 elección | A/B/ambas/ninguna | Sin recompensa | Selección/empate y repetibilidad |
| T05 asociación | A y B balanceados | A→X, B→Y | Precisión final en test sin refuerzo |
| T06 reversión | A/B tras aprendizaje | A→Y, B→X | Ciclos para reaprender, retención y olvido |
| T07 perturbación breve | Entrenamiento seguido de pocos refuerzos contrarios | Recompensas en secuencia | Cambios STW/LTW y recuperación |
| T08 retraso | Señal→acción→k ciclos | Refuerzo con k predefinido | Precisión, conexiones acreditadas |
| T09 distractor | Secuencias intercaladas | Refuerzo para una elección anterior | Crédito erróneo a decisiones posteriores |
| T10 transferencia | Combinaciones de señales no vistas | Eval. según regla de generalización | Precisión holdout vs memorizador |
| T11 saturación | Nuevas tareas con cupo de sinapsis | Refuerzo controlado | Nuevo aprendizaje vs olvido de tareas previas |
| T12 aislamiento | Pausar entradas durante N ticks | Sin recompensa | Punto fijo, oscilaciones, robustez |
| T13 checkpoint | Pausar/serializar/restaurar | No aplica | Igualdad exacta de continuaciones |

Todos los ensayos deben incluir eventos con `no_refuerzo` y definir claramente que una señal cero no equivale necesariamente a castigo.

## 5. Métricas y significado

- **Exactitud:** número de elecciones reforzadas en evaluación / número de elecciones evaluables. Si no hay elección, informar por separado en lugar de ocultarla del denominador.
- **Matriz de confusión:** entradas o clases de situación × acción, incluidos `ninguna` y empates según política.
- **Velocidad de aprendizaje:** rendimiento por ventana y número de ciclos/episodios hasta un umbral predefinido. Si no se alcanza, registrar censura, nunca imputar logro.
- **Retención:** rendimiento tras intervalo sin refuerzo, no solamente tamaño de pesos.
- **Reversibilidad:** rendimiento tras inversión de relación estímulo→acción, coste de reentrenamiento.
- **Generalización:** rendimiento únicamente en combinaciones no utilizadas durante entrenamiento ni ajuste, con contraste contra memorizar patrón exacto.
- **Crédito temporal:** proporción de refuerzo asignada a conexiones de la decisión que realmente lo antecedió vs distractoras; la relación causal es **conocida por el evaluador**, no por la mente.
- **Estabilidad:** distribución de estados, variación, punto fijo, ciclos, divergencias y NaNs; se debe usar ventana de análisis definida.
- **Capacidad y coste:** número de neuronas/sinapsis, memoria, tiempo/tick, reproducibilidad, reconfiguración.
- **Varianza:** informar por semilla (tabla o artefacto), media/mediana y dispersión; usar intervalos de incertidumbre cuando haya tamaño muestral apto.
- **Trazabilidad causal:** poder enlazar `estímulo → activaciones → decisión → refuerzo → modificación sináptica → siguiente decisión`.

No usar «autonomía», «inteligencia» o «conciencia» como métricas numéricas derivadas arbitrariamente de estas pruebas.

## 6. Criterios de aceptación

Una fase se considera **técnicamente validada** únicamente cuando:
1. todos sus tests de cálculo y persistencia pasan, con registro del entorno;
2. el efecto previsto aparece en runs controlados reproducibles, **o** se documenta explícitamente un resultado nulo/negativo con decisión de revisión/descarte;
3. se presentan todos los ensayos planeados, incluidos fallidos y no-evaluables;
4. no hay contaminación de train/test ni uso inadvertido de etiquetas en el controlador;
5. se registra la comparación con un baseline adecuado y el coste;
6. no hay regresiones en capacidades previamente validadas fuera de un trade-off documentado;
7. se enlaza el resultado con la hipótesis y se actualiza estado.

**Objetivo de trabajo opcional E03:** alcanzar ≥85 % de exactitud en una evaluación A/B equilibrada después de entrenamiento, en una proporción elevada de semillas, con mejora frente al baseline sin plasticidad. *No* se considera evidencia suficiente por sí sola; este umbral puede resultar trivial o demasiado restrictivo según el diseño. La definición final se registra antes de ejecutar E03.

La decisión estadística no debe basarse en un único valor `p` ni en una corrida: atender tamaño del efecto, varianza, fallos, coste y sensibilidad.

## 7. Auditoría de causalidad y trazabilidad

Por tick registrar como mínimo:
```text
run_id, tick, stimulus_id, stimulus_vector,
neuron_state_before, synapse_state_before,
outputs, decision_id, decision_status,
reward_value, reward_source, reward_applied_at_tick,
neuron_state_after, synapse_changes, topology_changes,
rng_state_hash, warnings
```
Para archivos muy grandes, conservar un log sin pérdidas de eventos y snapshots periódicos **con acceso verificable a reconstruir el período completo**. No basarse solo en dashboards agregados.

Registrar en metadatos si el procesamiento fue sincrónico por snapshot o secuencial; esta diferencia puede alterar los resultados.

## 8. Análisis de errores

Ante un resultado inesperado:
1. fijar el ejemplo mínimo y guardar el estado inicial;
2. separar error de implementación, regla histórica ambigua, diseño experimental y limitación del modelo;
3. comparar cálculo manual vs salida real para al menos un tick;
4. verificar sincronía, saturación, signos, PRNG, recompensa y filtrado accidental de la respuesta;
5. agregar test de regresión independiente;
6. corregir una sola causa;
7. reejecutar controles y documentar resultados;
8. mantener trazas anteriores, no reemplazarlas.

## 9. Qué constituye evidencia aceptable

| Hallazgo | Evidencia suficiente | Qué NO permite afirmar |
|---|---|---|
| Aprendió asociación | mejora sin fuga vs control y pesos modificados | entendió el significado de A |
| Retuvo | prueba tras intervalo sin refuerzo | posee memoria episódica humana |
| Generalizó | prueba nueva que explota estructura compartida | razonamiento causal abstracto |
| Reorganizó sinapsis | cambios topológicos y mejora bajo cupo fijo | evolución biológica |
| Actividad sin entradas | trazas estables de recurrentes | pensamiento espontáneo o conciencia |

**Los resultados del protocolo siguen siendo hipótesis hasta ejecutarse.**
