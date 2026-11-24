# NeuroLab — G05-INFO.02 propuesta conceptual de desafío sin atajo temporal

**22/11/2026. Estado: DISEÑO CONCEPTUAL COMPLETADO, NO PREREGISTRO COMPUTACIONAL NI EJECUCIÓN.** Basado en el [resultado C de identificabilidad G05-INFO.01](G05_INFO_01_RESULTADO_IDENTIFICABILIDAD_20261122.md). La pregunta original G05 es crédito temporal selectivo frente a distractores, no reconstruir una etiqueta que el evaluador filtra por patrón de contexto.

## 1. Hipótesis discriminante

**H:** con observaciones y recompensas idénticas en naturaleza a las del microcerebro C1, pero **sin un cambio sensorial que delate el origen del pulso**, ¿un mecanismo de elegibilidad atribuye mejor el refuerzo demorado a decisiones precedentes que un control sin memoria temporal, sin reforzar sistemáticamente acciones ajenas?

**Nula:** el efecto no supera mecanismos más simples con la misma información y presupuesto, o la distribución del banco no permite separar el origen del refuerzo de ruido/trivialidades. Un resultado nulo es conclusión válida.

No se presupone superioridad neuronal, ni aprendizaje de causas particulares a partir de un único pulso: el objetivo es identificar **contingencias estadísticas suficientes para una política adaptativa**. La línea H (fidelidad histórica C1) permanece separada.

## 2. Generador candidato de eventos continuos, no episodios con cuarta acción privilegiada

En cada tick:
- Llega un contexto abstracto `S0`/`S1` mediante proceso exógeno, **sin** relación fija con origen de futuros premios; la política emite `D0`/`D1` (o `None`) **en todos los ticks**.
- El evaluador puede seleccionar de manera **exógena e independiente de la acción y contexto** si esa acción origina una consecuencia futura. Si la selecciona, programa una demora aleatoria acotada y positiva, de un conjunto de varias distancias. La política no observa ese sorteo, el ID de evento ni la demora concreta.
- Al llegar, el refuerzo es positivo/negativo según la relación oculta `S→D` vigente **en el tick que lo originó**, no según el contexto contemporáneo. Los controles solo reciben el químico al tiempo de llegada, sin procedencia ni marca de ensayo.
- Se permiten, al menos en la pregunta experimental, **acciones candidatas solapadas** entre origen y entrega. No habrá `TARGET_TICKS=4` ni regla «premio luego del primer cambio de contexto».
- Una fase invierte la contingencia de salida; el criterio exige que el agente aprenda y se readapte sin reset oculto de memoria. Se separan adquisición, prueba sin premio y posibles pruebas de continuidad activa.

**Ambigüedad indispensable a resolver antes de programar:** varias consecuencias pueden llegar en el mismo tick; el `C1ContextBrain` actual espera cuatro bytes químicos y `REWARD=(255,0,0,0)`, `PUNISHMENT=(0,255,0,0)`. Hay que elegir **antes del preregistro** entre (a) una cola que serializa entregas con orden independiente de las acciones, contabilizando demora efectiva; (b) pulsos simultáneos normalizados bajo definición física común; (c) una tasa de generación tan acotada que sea posible especificar colisiones sin sesgo. **No** enviar al controlador el número de mensajes ni su ID si eso equivale a un rótulo causal ausente en C1. No declarar que una química nueva preserva fidelidad histórica.

**Desafío explícito de este diseño:** si todos los ticks producen acciones potencialmente causales, el evaluador puede generar simultaneidad de outcomes y un único reward puede tener atribución individual incierta; eso NO impide aprendizaje de valor esperado bajo exploración.

## 3. Criterio analítico de factibilidad (previo al código)

Modelo de referencia conceptual, **no decisión de parámetros**:

- `z_t∈{-1,+1}`: calidad latente de la acción/estado en tick `t` (mapping oculto, solo lo conoce evaluador).
- `B_t∈{0,1}`: oportunidad de feedback exógena independiente de `z_t`, con probabilidad `p>0`.
- `L_t`: demora positiva aleatoria independiente de la acción/contexto, con al menos dos valores posibles.
- Si se agregaran linealmente entregas: `R_u = Σ_{t<u} B_t · 1[t+L_t=u] · z_t`. Este `R_u` es variable analítica del evaluador, **no químico implementado**.

Bajo exploración balanceada que haga `E[z_t]=0` y secuencia de `z_t` no autocorrelacionada, `E[R_{t+ℓ} z_t] = p Pr(L_t=ℓ)` para cada demora admisible `ℓ` en el modelo ideal. Por eso existe **señal estadística prospectivamente detectable** sobre el pasado, aunque el origen de un pulso individual no sea identificable. La ecuación deja de ser exacta bajo política dependiente de historia, serialización de colisiones, química saturada o correlaciones temporales: **esas desviaciones deben analizarse, no ocultarse**.

**Puerta de validez de futuro banco:** un test manual/oráculo de correlación y un control con recompensas permutadas deben comprobar que la señal existe cuando hay contingencia y desaparece cuando no. También se debe buscar un atajo de calendario/contexto capaz de recuperar eventos sin aprender: si existe, rediseñar antes de ejecutar modelos. No gastar semillas científicas para validar esa semántica.

## 4. Comparadores prioritarios: existentes antes que nuevos

1. **Sin memoria temporal y sin aprendizaje**, para establecer azar/invariantes.
2. **Tabla reactiva de pares `(S_t,D_t)`** que atribuye refuerzo al par del tick actual o último, **mismo streaming**, no `target` del evaluador.
3. **Trazas de elegibilidad tabulares** con decaimiento para pares estado-acción, como controles de bajo costo. Opciones existentes: [SARSA(λ)/TrueOnlineSARSA(λ) de MushroomRL](https://mushroomrl.readthedocs.io/en/latest/source/mushroom_rl.algorithms.value.html); antes de usar la biblioteca, verificar si su API requiere marcador de episodio, valores de transición u otro input inaccesible para C1.
4. **Susceptibilidad de `C1ContextBrain` tal cual** (si su reloj, pulsos y modo ACTIVE son compatibles), y variante congelada.
5. **Oráculo con procedencia** exclusivamente para techo descriptivo; si se le proporciona ID/tiempo causal oculto, NO es un baseline fair.

**Prohibido:** introducir una red mayor, e-prop, Brian2, rediseñar química o usar un LLM para mejorar la métrica antes de que un control simple y la auditoría de información descarten explicaciones triviales.

## 5. Puertas de decisión antes de implementar

- **D1: auditabilidad de señales.** Definir entradas públicas privadas, orden exacto de tick y recompensa, políticas de acción `None`, si la agenda de feedback depende de la política y cómo se igualan fuentes de aleatoriedad entre brazos.
- **D2: validez del problema.** Demostrar, con fixtures ajenos a seeds de investigación, no existencia de un marcador perfecto del origen y presencia de señal agregada bajo exploración. Considerar poblaciones donde el premio causa información insuficiente y delimitar explícitamente qué nivel de aprendizaje es posible.
- **D3: costo y reutilización.** Probar solo compatibilidad de interfaces de candidato existente, sin entrenarlo; contabilidad de estado/ciclos/feedback y condiciones de detención explícitas.
- **D4: preregistro independiente.** Congelar distribuciones, demoras, tasa de eventos, régimen de colisiones, precisión por fase, atribución espuria, reversión, controles, población de desarrollo y holdout nuevo, error estadístico y regla STOP **antes** de cualquier ejecución científica.
- **D5: decisión de avance.** Si D1–D3 no resuelven identificabilidad, señal, igualdad de información y costo, **detener** sin abrir la fase experimental. Un benchmark sin señal no demuestra un algoritmo malo; uno con pista causal perfecta no demuestra atribución general.

## 6. Alcance y próxima unidad exacta

**G05-INFO.02 queda completada como diseño conceptual**, sin parámetros ni software: no sustituye el preregistro requerido por D4. **Próxima unidad `G05-INFO.03`, DOCUMENTAL**: resolver D1–D3, especialmente colisiones/demora efectiva, demostrar ausencia del atajo con ejemplos adversarios, y elegir si una biblioteca existente es compatible con las señales sin privilegios. Si se satisface, redactar preregistro numérico y oráculos toy; si falla, pausa/rediseño.

**Sin corridas científicas, sin cambios a microC1, NR01 ni mundo/Nilo; `main` no modificado.** G05/G09 siguen sin superarse, H por separado; PR#103 draft.
