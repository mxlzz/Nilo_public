# NeuroLab G05-NX01 — preregistro del primer ensayo discriminante de recompensa anónima

**Fecha 22/11/2026; PRE-REGISTRO ANTES DE RUNNER Y ANTES DE SEMILLAS CIENTÍFICAS.** Antecedente: [G05-INFO.03 PASS técnico](G05_INFO_03_RESULTADO_FACTIBILIDAD_20261122.md), [control maestro](ETAPAS_00_09.md), [g.10b negativo](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md). **Esta es una nueva pregunta acotada, no una repetición retroactiva de g.10b ni modificación de C1.** No implica integración Nilo0.7, nueva arquitectura ni cierre de G09.

## 1. Pregunta y criterios de falsación

¿La susceptibilidad sináptica existente de `C1ContextBrain`, bajo consecuencias demoradas **anónimas**, aprende contingencias contextuales de forma selectiva y reversible con más rendimiento que controles de información idéntica y menor complejidad?

H0: no tiene mejora práctica suficiente sobre controles comparables, o la aparente mejora es consecuencia de reward contingente no selectivo, de latencia sensorial, o del atajo estadístico de contexto. En H0/indistinción se conserva el resultado negativo y NO se rediseñan tasas C1.

**No se espera atribuir perfectamente cada pulso:** [testigo de ambigüedad](G05_INFO_03_RESULTADO_FACTIBILIDAD_20261122.md) demuestra que una recompensa individual admite al menos dos orígenes observacionalmente iguales. La señal de contingencia solo es identificable estadísticamente.

## 2. Entorno y API estrictos

**Un tick = decisión con input x_t y posible químico reward antiguo.** Contexto x0 sorteo Bern(1/2), luego transición con probabilidad .10 por tick. En todo tick: premio que vence del pasado, contexto, acción del agente, actualización interna y agenda de una futura consecuencia por esa acción (señal exógena no observada). La acción se decide **antes de que el químico recibido en ese mismo tick pueda modificar la política elegida**, con caso especial: si el circuito C1 suprime decisiones por fortaleza/cambio en el mismo tick, registrar incidencia y tratar el caso como diferencia de reloj, no esconderla. Todos los brazos reciben el mismo contexto y oportunidades exógenas; se ocultan `mapping`, `B_t`, `L_t`, lista de eventos pendientes, prioridades, `source_tick` y banderas de fase/target en API.

- Oportunidad `B_t~Bernoulli(.20)` independiente por tick; demora `L∈{2,4,7}` uniforme; prioridad `U(0,1)` independiente de signo/contexto/agente. Si la acción es `None`, no se genera evento; se registra tasa de abstención.
- Al vencimiento, seleccionar evento de **menor prioridad**, entregar solo su signo ± como `REWARD=(255,0,0,0)` o `PUNISHMENT=(0,255,0,0)`, descartar los demás; `ZERO=(0,0,0,0)` cuando no hay evento. Ninguna colisión se desplaza a otro tick ni revela cuantos eventos se perdieron.
- Cada evento registra en el evaluador el contexto/acción **del momento en que fue originado** y calcula signo contra mapping externo. Brazo C1 **no** recibe esos metadatos; aplicarlos solo a métricas/permutaciones.
- Dos fases A mapping (0→D0,1→D1) y B (0→D1,1→D0) con **2.400 ticks de adquisición cada una**. No reset de pesos entre fases. Después de cada fase, **7 ticks extra de drenaje**: exógenos y con decisión, sin agendar nuevos eventos, se entregan los ya programados, plasticidad activa. Así al invertir mapping no quedan consecuencias pendientes de A.
- Después de drenar, **600 ticks de holdout por fase** en copia independiente desde checkpoint, con contextos nuevos generados con el mismo mecanismo, **sin feedback ni actualización de políticas tabulares**; la lectura primaria de C1 es `ACTIVE-NOREWARD` (su dinámica puede relajarse, pero no recibe químicos). `FROZEN` auxiliar para determinar efectos de relajación. Los holdouts no afectan el estado de entrenamiento. Evaluación de `None` = decisión incorrecta.
- No se incorpora mundo físico, genoma nuevo, cuerpo, LLM ni necesidades.
- Generación: PRNGs independientes por mundo para contextos, oportunidad, demora, prioridad y exploración; **misma secuencia de contextos/oportunidades/demoras/prioridades** en cada brazo, pre-generada antes de elegir acciones. Los signos de reward difieren naturalmente según las acciones de cada brazo. Cualquier excepción/colisión y número total de premios se registra.

## 3. Brazos y procedimientos inmovilizados

**C: C1 original sin modificar** (`C1ContextBrain`), mismo inicializador y genes. No agregar STDP, elegibilidad extra ni parámetros.

**F: C1 congelado:** mismos inputs y estados, pero `learn=False` durante entrenamiento; controla efecto de aprendizaje, NO es ablación selectiva de elegibilidad.

**P: C1 con signos de reward independientes:** mismo schedule exógeno, pero cada premio de cualquier acción presente recibe ± con Bern(1/2) independiente del mapping. Identifica aprendizaje por contingencia frente a premio casual. No es un control con signo marginal exactamente pareado con C y se declara esa limitación.

**T0: tabla reactiva**, Q[2 contextos ×2 acciones], valores iniciales0, en cada pulso posterior a decisión aplica `q[x_t,a_t] += 0.10 * r_t` con clamp [-1,1], sin ID causal. Políticas tabulares epsilon-greedy de `epsilon=.10` al entrenar, con desempates pseudoaleatorios; holdout greedy.

**Tλ: tabla de elegibilidad**, Q[2×2], trace[2×2] decae `lambda=.75`; ante pulso actualiza `q[i]+=0.10*r*trace[i]/sum(trace)` para `sum(trace)>0`, clampeando [-1,1]; el par elegido en tick actual solo se incorpora **después** de la actualización de ese pulso, por lo que la acción actual no recibe crédito de reward que causalmente no pudo originar. No conoce distribución de retardos.

**TK: tabla con soporte temporal conocido**, buffer de 7 pares `(x,a)` de sus elecciones, cuando llega pulso actualiza cada uno en posiciones temporales 2/4/7 con aporte `0.10*r/3`, clamp [-1,1]. Es un **control fuerte con conocimiento del soporte de demoras** (prior del diseñador, no ID de evento). No atribuye causalidad perfecta. Misma `epsilon=.10` y regla de exploración de T0/Tλ.

**Prohibido dar a TK o Tλ `target`, `delay` verdadero, `source_tick` verdadero, recompensa de una acción que no generó feedback o acceso al mapping.** Un oráculo externo con procedencia, si se calcula, es solo techo superior descriptivo, no un control de misma información.

## 4. Latencia y medición

`C1ContextBrain.step` usa `previous_concepts` para decidir; una tabla puede usar x_t directamente. Por eso informar **dos precisiones** en los mismos 600 ticks: (i) precisión **estable** cuando x_t=x_{t-1}=x_{t-2} (primaria, fijada antes de datos); (ii) precisión en **todos** los ticks y por distancia desde un switch. No extrapolar ventaja de tablas por latencia a crédito causal. No condicionar métricas a que se emita una acción. Reportar pérdida de eventos por colisión, n de químicos, distribución de etiquetas, lectura ACTIVE vs FROZEN, CPU y bytes de estado serializable.

**Unidad estadística:** mundo completo pareado, no ticks. Puntaje primario por mundo `S=0.5*(accuracy_stable_A+accuracy_stable_B)`. Medir reversión también por curva de entrenamiento en cuatro ventanas fijas de 600 ticks cada una de B, con accuracy de decisiones en contextos estables (sin condicionar por feedback). Los resultados analíticos de origen evaluador no son datos de entrenamiento.

## 5. Cohortes y orden de ejecución

- **Piloto técnico: una sola semilla de desarrollo 25000**, para verificar clock, API, captura/lectura, estado y presencia de todos los brazos; no ajustar hiperparámetros por desempeño. El piloto es la primera fila de desarrollo y se debe reproducir bit a bit.
- **Desarrollo: 20 semillas 25000..25019**, dos fases cada una, seis brazos C/F/P/T0/Tλ/TK. Fijar generador/configuración sin cambios entre piloto y desarrollo, salvo corrección de defectos con tests y repetición integral versionada.
- **Confirmación BLOQUEADA: semillas 26000..26019**; abrir solo si se supera gate de desarrollo íntegra y candidato/configuración congelados. **Nunca usar 1400..1419 ni 24000..24019** de otras líneas.
- Estadística: diferencia por mundo pareada, bootstrap95% por mundo con 5000 réplicas y RNG fijo 918278; informar distribución por fase, no inferir independencia de ticks. La selección de mejor baseline en desarrollo impide usar su IC como confirmación.
- Ejecuciones fijadas en GitHub Actions, commit exacto, trazas JSON/JSONL por mundo/etapa/brazo, controles de replay y hashes; resultados negativos permanentes.

## 6. Puertas STOP establecidas ANTES de correr

**G05-NX01.03 técnica:** se exige clock equivalente de acciones, paridad de cintas exógenas, química posterior a elecciones pasadas, cero fugas de `source_tick`/mapping, tests de `None`, colisiones, fases/drenaje, replay exacto y costo; un error bloquea toda corrida científica.

**G05-NX01.04 desarrollo:** el brazo C solo es elegible para confirmación si simultáneamente:
1. S de C supera a **mejor T0/Tλ/TK** por **≥0.05** puntos absolutos, y a P y F por **≥0.10** puntos absolutos; mejoras positivas en ≥15/20 mundos;
2. accuracy estable ≥0.70 en **ambas fases**, sin colapso a política constante ni gran tasa de `None` (reportar ≥10% como alerta, no regla de exclusión);
3. evaluación de actualización química selectiva indica que el refuerzo modifica, en media, los contactos del par realmente originador más que los distractores, bajo contrafactual ZERO en un mismo estado previo. Si este diagnóstico no se implementó o es indeterminado, **no abrir confirmación**;
4. costo de memoria y CPU justificable frente a tabla, reportando cualquier caso >10× sin asumir automáticamente fracaso pero como bloqueo de adopción hasta explicar utilidad.

**Si falla algún requisito:** cerrar **resultado negativo/limitado** de G05-NX01; no usar confirmación, no tunear tasas, genes, umbrales ni añadir neuronas a ciegas. Si los propios controles también fallan, evaluar validez de banco antes de atribuir fracaso cerebral. Un gate científico fallido **no** es CI fallida.

**Si pasa:** solo entonces ejecutar confirmación única con definición de éxito preregistrada en adenda **antes de usar sus semillas**, incluyendo IC pareado95% >0 y mantenimiento de mejoras mínimas. Repetir candidaturas después de ver confirmación está prohibido.

**Alineación obligatoria:** cada etapa debe responder qué subpregunta G05 aporta, si un control sencillo refuta ventaja distintiva, cuánto presupuesto agrega y cómo se conserva evidencia. G05 original no se declara superada automáticamente por este desafío nuevo; G09 sigue abierta. `main` y Nilo0.7 intactos; PR103 draft.
