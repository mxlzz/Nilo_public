# NeuroLab — guía operativa de etapas E00–E09

**Versión 0.1.0 · Plan (no ejecución).** Cada subtarea requiere su identificador, fecha real cuando se complete, responsable, evidencia y resultado. Las casillas iniciales están **pendientes**, no «en progreso».

## Convención para ejecutar cualquier subtarea

1. Leer [ESTADO_Y_CONTINUIDAD.md](ESTADO_Y_CONTINUIDAD.md); confirmar rama, etapa, subtarea, bloqueo y último commit verificado.
2. Leer reglas históricas pertinentes en [FUENTES_Y_RECONSTRUCCION.md](FUENTES_Y_RECONSTRUCCION.md) y diferenciar lo no confirmado.
3. Escribir previamente *qué va a cambiar*, hipótesis falsable, controles, entradas, resultados esperados y umbrales o criterio cualitativo observable.
4. Realizar **una** unidad verificable. Guardar artefactos y resultados **reales**, no ejemplos ficticios.
5. Correr controles, regresiones y pruebas reproducibles. Registrar resultados positivos, negativos, nulos y desviaciones.
6. Solo marcar completado si hay evidencia accesible y criterios satisfechos. De lo contrario registrar `falló / bloqueado / revisión`, y no avanzar fingiendo éxito.
7. Actualizar estado, número de experimento, decisión y *siguiente subtarea exacta*. No reescribir el pasado: corregir con adenda.

**Semáforo de fase:** pendiente → en curso → verificación → validada / bloqueada / descartada. `Validada` significa cumplir el criterio de esa fase, no demostrar autonomía general o una reconstrucción histórica completa.

---

## E00 — Arqueología y especificación del cerebro C1

**Hipótesis metodológica:** es posible aislar un subconjunto suficientemente documentado de C1 para implementarlo sin atribuirle datos inventados.

- [ ] **E00.01 Inventariar fuentes.** Abrir SRC-01…SRC-05; constatar accesibilidad, fecha/versión, contenido y citas pertinentes. Buscar documentación primaria adicional para lagunas concretas. Entrega: tabla versionada de fuentes y fragmentos localizables.
- [ ] **E00.02 Fijar edición.** Determinar versión y genoma de C1 de referencia; si no se obtiene un genoma legalmente accesible, documentar que se trabajará solo sobre descripción técnica, sin equivalencia de genoma.
- [ ] **E00.03 Mapear lóbulos.** Tabla con ID/nombre, tamaño, clase de input/output, topología, conectividad, si hay unidades sin uso y cómo se computa «952» en la edición elegida. Las cifras preliminares deben verificarse.
- [ ] **E00.04 Neurona.** Registrar variables, tipos/rangos, transferencia, umbral, reposo, relajación, combinaciones, SVRule, saturación y actualización. Para cada regla, ejemplo calculado manualmente.
- [ ] **E00.05 Sinapsis.** Precisar STW/LTW, susceptibilidad, fortaleza, fuente/destino, refuerzo, decaimiento, atrofia, migración y parámetros de construcción. Distinguir estados de implementación original y propuestas experimentales.
- [ ] **E00.06 Reloj y conducta.** Reconstruir orden de tick, si cada fase usa valores anteriores/actuales, propagación, competición de neuronas de decisión y relación con acciones externas/objetos.
- [ ] **E00.07 Instintos y recompensa.** Identificar en qué forma y momento se introducen drives, químicos, refuerzos y sueño; especificar qué se excluye al estudiar una mente sin cuerpo.
- [ ] **E00.08 Matriz de certeza.** Por variable y operación, marcar `confirmada / reconstruida / abierta`, fuente y experimento que permitiría resolverla; registrar variantes incompatibles si existen.
- [ ] **E00.09 Especificación histórica v0.1.** Pseudocódigo del tick neuronal/sináptico; casos con resultado calculado a mano; tabla de transformaciones, rangos y excepciones.
- [ ] **E00.10 Revisión crítica.** Comprobar que no se mezclan C1, C2 y C3; revisar afirmaciones de fidelidad; anotar lagunas sin taparlas.

**Puerta G00:** especificación matemática *suficiente para la primera implementación* y separación exacta entre mecanismos históricos y convenciones propias. Si no hay evidencia para detalles esenciales, permitir solo prototipo N explícitamente no fiel y mantener G00 histórico parcialmente abierto. No exigir descifrar todo el genoma para simular una neurona básica.

**Si falla:** buscar otra fuente primaria, declarar la laguna o reducir alcance. Prohibido reemplazar un dato ausente por un valor plausible sin marcarlo como hipótesis.

---

## E01 — Motor elemental, sin aprendizaje

**Pregunta:** ¿la implementación de una unidad neuronal y una sinapsis reproduce las reglas especificadas sin efectos del orden de ejecución no deseados?

- [ ] **E01.01 Contratos de datos.** Diseñar estructuras `NeuronState`, `SynapseState`, `BrainState` con identificadores estables y tipos/rangos; memoria separada de configuración.
- [ ] **E01.02 Orden de actualización.** Establecer explícitamente lectura/escritura de estado anterior, fases de tick y política numérica. Anotar divergencias de C1.
- [ ] **E01.03 Neurona elemental.** Implementar solo activación/relajación. Test con entradas 0, máximo, mínimo, valores simultáneos y vacío.
- [ ] **E01.04 Sinapsis sin plasticidad.** Implementar signo/peso/propagación con parámetros fijos; test de excitación e inhibición.
- [ ] **E01.05 Ciclo temporal.** Ejecutar una red arbitraria pequeña con tiempos discretos; verificar ausencia de estado implícito entre experimentos.
- [ ] **E01.06 Determinismo.** Con mismo estado inicial y misma secuencia de entradas comprobar identidad de la trayectoria; con aleatoriedad guardar semilla, PRNG y estado.
- [ ] **E01.07 Checkpoint exacto.** Serializar/restaurar en mitad de la ejecución; comparar la continuación con la corrida sin interrupción.
- [ ] **E01.08 Tests de referencia.** Construir fixtures de resultado calculado manualmente **independientes** del código principal; incluir 1 neurona, 2 conectadas, inhibición y relajación.
- [ ] **E01.09 Auditoría de rendimiento.** Registrar memoria, tiempo/ciclo y complejidad en red pequeña; no optimizar prematuramente.

**Puerta G01:** fixtures matemáticos correctos, determinismo y restauración sin divergencia, tests de rangos/NaN/overflow definidos. **No** se afirma aprendizaje.

**Si falla:** corregir secuencia o representación, registrar bug y nueva prueba; no aumentar tamaño.

---

## E02 — Circuito mínimo de seis neuronas

**Pregunta:** ¿dos entradas abstractas y dos conceptos bastan para modular la competencia entre dos acciones sin aprendizaje todavía?

- [ ] **E02.01 Topología versionada:** E1,E2 (entrada), C1,C2 (concepto), D1,D2 (decisión). Es un circuito propio, no una subred certificada de C1.
- [ ] **E02.02 Definir estímulos:** A, B, ninguno, simultáneos, valores parciales; no incluir etiquetas semánticas «comida», «miedo», etc.
- [ ] **E02.03 Conexiones iniciales:** tabla explícita de todas las sinapsis, signos, pesos y límites; generador parametrizable y semilla.
- [ ] **E02.04 Política de elección:** máximo de activación y tratamiento determinista/documentado de empates, inactividad y umbral mínimo.
- [ ] **E02.05 Correr ejemplos manuales:** al menos tres estados con resultados paso por paso.
- [ ] **E02.06 Barrido de entradas:** analizar respuesta a A/B/ambas/ninguna; comprobar elección y trace.
- [ ] **E02.07 Revisar estabilidad:** estudiar oscilaciones, dominancia sistemática y efectos del orden de actualización.

**Puerta G02:** elección explicable por activación, reproducible y sin reglas ad hoc «si A, entonces X». Un sesgo de elección por conexiones iniciales es aceptable si se documenta; no es aprendizaje.

**Si falla:** resolver implementación o revisar topología con una comparación controlada, sin sumar neuronas automáticamente.

---

## E03 — Plasticidad asociativa (primera capacidad de aprendizaje)

**Pregunta:** ¿el circuito puede aprender A→X y B→Y exclusivamente por refuerzo, sin recibir las correspondencias como reglas internas?

- [ ] **E03.01 Regla plástica candidata:** implementar variante respaldada por G00, o anotar regla propia con ecuación y dominio. No agregar STW/LTW aún.
- [ ] **E03.02 Banco de refuerzo:** construir contingencias A→X y B→Y fuera del cerebro, accesibles al evaluador pero no al controlador.
- [ ] **E03.03 Protocolo previo:** fijar semillas, número de ensayos, secuencias, criterio de éxito, entrenamiento y ventana de prueba independiente.
- [ ] **E03.04 Control sin aprendizaje:** misma red, entradas y aleatoriedad; plasticidad deshabilitada.
- [ ] **E03.05 Entrenamiento balanceado:** presentar A y B con frecuencias iguales y orden aleatorizado registrable.
- [ ] **E03.06 Evaluación sin refuerzo:** medir precisión y matriz de confusión en secuencias no vistas.
- [ ] **E03.07 Invertir contingencia:** cambiar a A→Y y B→X; medir ciclos hasta adaptación y olvido.
- [ ] **E03.08 Ablación:** retirar componente plástico y observar pérdida del efecto.
- [ ] **E03.09 Repetir semillas:** reportar distribución de resultados, no elegir solo el mejor.
- [ ] **E03.10 Informe causal:** mostrar cambios de pesos antes/después vinculados a decisiones concretas.

**Puerta G03:** mejora reproducible respecto a controles y reaprendizaje tras inversión, con evidencia de que la tabla de correspondencias no aparece en código cerebral. El 85 % propuesto anteriormente es orientativo; no convertirlo en éxito automático sin protocolo registrado y resultados de control.

**Si falla:** discriminar regla de aprendizaje, topología, recompensa y exploración; modificar una variable por comparación.

---

## E04 — Memoria a dos velocidades (STW/LTW)

**Pregunta:** ¿una asociación rápida y otra lenta permiten adaptarse a perturbaciones breves sin perder toda la experiencia consolidada?

- [ ] **E04.01 Especificar regla STW/LTW** desde fuente C1 o marcar adaptación propia.
- [ ] **E04.02 Incluir límites y relajación** y tests con pesos extremos.
- [ ] **E04.03 Calibrar escala temporal** sin usar como criterio curvas inventadas; documentar rangos de barrido.
- [ ] **E04.04 Entrenar repetidamente** hasta estabilización definida.
- [ ] **E04.05 Inyectar refuerzo contrario breve** y medir salida y pesos temporales.
- [ ] **E04.06 Inyectar refuerzo contrario prolongado** y medir cambio duradero.
- [ ] **E04.07 Comparar controles** un solo peso y STW/LTW, con números de parámetros y ciclos comparables.
- [ ] **E04.08 Pausas sin refuerzo** para verificar decaimiento y retención.
- [ ] **E04.09 Registrar sensibilidad** a tasas de aprendizaje y relajación.

**Puerta G04:** distinguir cuantitativamente memoria temporal y duradera; demostrar ventaja o declarar resultado nulo. Un doble peso sin efecto funcional no cuenta como logro.

---

## E05 — Crédito y refuerzo retrasado

**Pregunta:** ¿el circuito refuerza preferentemente las conexiones implicadas cuando la consecuencia llega varios ciclos después?

- [ ] **E05.01 Definir elegibilidad/susceptibilidad:** activación, caducidad, signo, saturación, relación con STW/LTW.
- [ ] **E05.02 Instrumentar trazabilidad:** ID de decisión, ID de conexiones activas, tick de acción, tick de refuerzo.
- [ ] **E05.03 Definir retrasos antes del experimento** (ej., 0,1,3,5,10 ticks), sin ajustar post hoc buscando una curva conveniente.
- [ ] **E05.04 Control de refuerzo inmediato** vs retrasado y control sin elegibilidad.
- [ ] **E05.05 Distractores intercalados** para probar atribución errónea a acciones posteriores.
- [ ] **E05.06 Experimentos temporales pareados** con mismas señales/semillas.
- [ ] **E05.07 Análisis:** rendimiento, pesos modificados por decisión, error de crédito y ventana efectiva.
- [ ] **E05.08 Ablación de trazas** y contraste.

**Puerta G05:** ventaja reproducible en al menos retrasos predefinidos frente a control, sin reforzar sistemáticamente decisiones ajenas.

---

## E06 — Conceptos y transferencia

**Pregunta:** ¿conceptos formados por combinaciones de señales permiten responder mejor a situaciones no entrenadas?

- [ ] **E06.01 Crear generador de patrones** de 1–4 entradas activas, con semillas y etiquetas internas irrelevantes.
- [ ] **E06.02 Definir regularidades latentes** y holdouts de combinaciones (sin fuga al entrenamiento).
- [ ] **E06.03 Construir detector de conceptos** siguiendo regla histórica documentada o adaptación explícita.
- [ ] **E06.04 Entrenar conjuntos parciales** con distribución controlada.
- [ ] **E06.05 Evaluar combinaciones nuevas** bajo una regla observable del evaluador, sin refuerzo durante test.
- [ ] **E06.06 Comparar memoria de patrón exacto** y red sin conceptos; equilibrar capacidad/variables en lo posible.
- [ ] **E06.07 Ensayar señales ruidosas/ambiguas** sin alterar el criterio después.
- [ ] **E06.08 Inspeccionar activaciones** y qué concepto produjo cada respuesta.
- [ ] **E06.09 Medir generalización positiva y negativa:** interferencia, sobreajuste y confusiones.

**Puerta G06:** mejora en holdouts que no pueda explicarse solo por memorizar ejemplos completos; detallar casos en que falló.

---

## E07 — Atrofia y plasticidad estructural

**Pregunta:** ¿migrar conexiones aumenta capacidad de adaptación cuando hay recursos sinápticos limitados, y a qué coste de olvido?

- [ ] **E07.01 Identificar reglas históricas efectivamente activas**; separar “propuesto” de “implementado”.
- [ ] **E07.02 Definir fortaleza, atrofia y disparador** con límites deterministas y política de selección de nuevo origen.
- [ ] **E07.03 Implementar desconexión/reconexión** con trazas de topología y condiciones de no duplicación.
- [ ] **E07.04 Entrenar tarea inicial** bajo presupuesto fijo de sinapsis.
- [ ] **E07.05 Introducir nuevas asociaciones** y medir saturación.
- [ ] **E07.06 Tres controles:** conexiones fijas sin plasticidad, pesos plásticos con conexiones fijas, pesos y topología plásticos.
- [ ] **E07.07 Medir retención antigua y aprendizaje nuevo** (trade-off), con varias semillas.
- [ ] **E07.08 Ensayar reentrenamiento** tras conexiones perdidas y estabilidad de red.
- [ ] **E07.09 Evaluar coste** computacional por unidad de beneficio.

**Puerta G07:** ventaja atribuible a reorganización bajo restricción predefinida, no solo a más parámetros; si no se demuestra, registrar descarte provisional.

---

## E08 — Dinámica interna sin estímulos continuos

**Pregunta:** ¿puede la red mantener estados internos interesantes y responder de forma dependiente de la historia cuando se suspenden las entradas?

- [ ] **E08.01 Definir estado basal** y fijar qué cuenta como actividad, oscilación, estabilidad y divergencia.
- [ ] **E08.02 Diseñar conexiones recurrentes** explícitas; no inferir equivalencia histórica sin fuente.
- [ ] **E08.03 Fijar parámetros y rangos de estabilidad** antes del ensayo.
- [ ] **E08.04 Estimular y suspender entradas**, registrando trayectoria por tick.
- [ ] **E08.05 Contrastar red sin recurrencia** y red con recurrencia bajo mismo estado inicial posible.
- [ ] **E08.06 Inyectar perturbaciones controladas** después de intervalos sin entrada.
- [ ] **E08.07 Clasificar estados** (apagado, punto fijo, ciclo, transitorio, inestabilidad numérica).
- [ ] **E08.08 Evaluar dependencia de historia** y robustez a ruido/semillas.
- [ ] **E08.09 Redactar límites:** ninguna trayectoria, por sí sola, demuestra pensamiento, curiosidad, intenciones o conciencia.

**Puerta G08:** dinámica cuantificada y estable o resultado nulo documentado; no añadir sistemas de emociones solo por necesitar actividad aparente.

---

## E09 — Síntesis, ablación y arquitectura mínima resultante

**Pregunta:** ¿qué mecanismos son necesarios, suficientes o redundantes para las capacidades efectivamente demostradas?

- [ ] **E09.01 Congelar versiones** de cada variante candidata, códigos, entradas y pesos.
- [ ] **E09.02 Reejecutar evaluación completa** con datos/semillas de prueba bloqueados.
- [ ] **E09.03 Ablaciones por mecanismo**: conceptos, STW/LTW, elegibilidad, migración, recurrentes.
- [ ] **E09.04 Barrido de tamaño mínimo:** bajar neuronas/conexiones hasta pérdida de cada capacidad, sin alterar la prueba.
- [ ] **E09.05 Comparar baseline simple** (tabla asociativa / aprendizaje tabular) para evitar construir una red compleja sin ventaja.
- [ ] **E09.06 Analizar sensibilidad** a ruido, parámetros, inicialización y contingencias invertidas.
- [ ] **E09.07 Reportar incertidumbre** e intervalos/distribuciones, junto con resultados negativos.
- [ ] **E09.08 Seleccionar arquitectura mínima** respaldada por evidencia; separar selección de uso en Nilo.
- [ ] **E09.09 Declarar límites**: mente asociativa ≠ agente general; sin cuerpo/mundo no hay comportamiento ecológico.
- [ ] **E09.10 Proponer próximos experimentos** (modulación de motivación, consulta LLM, entorno) como opciones futuras, **no** ejecutarlas ni declararlas aprobadas.

**Puerta G09:** informe técnico reproducible con resultados por capacidad, mecanismos esenciales/no esenciales, arquitectura mínima y decisión: crecer, revisar o detener.

---

## Regla de cambio de alcance

No se avanza a una fase superior si la anterior no explica qué se ha observado. Se permite trabajar **en paralelo solo en investigación documental o pruebas independientes** que no supongan una capacidad no validada. Toda alteración del orden requiere una decisión documentada (qué puerta se omite, por qué, riesgo y cómo se recuperará).

**No se obliga a implementar todas las fases:** una fase puede terminar en resultado negativo o justificar suspender la investigación. Cumplir el plan no significa fabricar obligatoriamente una mente de 952 neuronas.
