# Mundo autónomo — fundamentos y hoja de ruta experimental

**Estado:** investigación conceptual; sin implementación del mundo.
**Fecha de registro:** 2026-11-21.
**Ubicación provisional:** rama `research/world-foundations-2026-11` de `mxlzz/Nilo_public`.
**Alcance:** mundo físico/ambiental generativo. **Excluye** cerebro, genética neuronal, Norns, NeuroLab, LLM y control cognitivo de agentes.
**Separación:** no alterar `main`, el mundo existente de Nilo ni las investigaciones de NeuroLab. Si el proyecto progresa, migrar este material a un repositorio independiente sin reescribir su historia.

## 1. Intención

Investigar un **mundo pequeño, explorable en el futuro, autónomo y persistente**, que se construya y transforme mediante reglas compartidas. Se busca evitar diseñar manualmente cada mapa, objeto, estructura o fenómeno emergente. La novedad de las organizaciones debe **medirse**, no presumirse. Nilo podría integrarse en el futuro como un habitante, pero **no es una dependencia**.

No decidir todavía el motor gráfico, la perspectiva visual, el lenguaje de implementación ni la arquitectura definitiva. Las primeras pruebas pueden ser numéricas y sin interfaz.

## 2. Decisiones confirmadas en conversación

1. **Reglas híbridas (1C):** propiedades e interacciones generales más modelos eficientes de fenómenos conocidos; conservar espacio experimental para organizaciones no prefijadas.
2. **Generación inicial + evolución (2A+B):** crear un estado inicial coherente mediante algoritmos y dejarlo evolucionar de manera autónoma. No simular millones de años solo para llegar al punto de partida.
3. **Organización abierta (3B):** permitir que estructuras surjan de relaciones entre componentes; no limitar todo a catálogos de piezas finales prefabricadas.
4. **Territorio pequeño (4A):** priorizar detalle causal y validación antes que escala.
5. **Evolución independiente del observador (5B):** el mundo mantiene estado y procesos, esté o no siendo explorado.

**Aún NO decidido:** implementación en celdas/partículas/continuo; escala real; materiales específicos; precisión física; reglas de generación concretas; licencia; repositorio permanente; tecnologías gráficas. Las elecciones técnicas abajo son **hipótesis de experimentación**.

## 3. Criterio de diseño

Programar explícitamente **modelos aproximados para fenómenos conocidos** cuando el ahorro computacional sea grande y no bloquee las interacciones relevantes. Dejar **abiertas las configuraciones y relaciones entre componentes** allí donde se busque emergencia. Una aproximación no debe crear una realidad física contradictoria con otra parte del motor.

No llamar «emergencia» a mera aleatoriedad, ruido visual ni a resultados predeterminados por reglas especiales para cada forma final. Distinción operacional:
- **Generación procedural:** el algoritmo produce una configuración inicial.
- **Dinámica autónoma:** la configuración cambia bajo reglas sin intervención.
- **Organización emergente:** patrones funcionales distinguibles que resultan de interacciones locales y no de plantillas que construyen directamente ese patrón.
- **Evolución abierta:** producción sostenida de novedad; objetivo de investigación **no garantizado** ni requisito temprano.

## 4. Contrato de prueba por etapa

Cada etapa debe abrir con:
- **Hipótesis explícita** y alternativa simple (incluido no implementar).
- **Mecanismo mínimo** a ensayar, sin añadir subsistemas no necesarios.
- **Prueba unitaria** de leyes/invariantes.
- **Prueba integrada** de consecuencias causales.
- **Prueba diferencial o control** (sin regla, con parámetro distinto, o con otra semilla).
- **Medición y registro**: condiciones iniciales, semilla, versión de reglas, parámetros, acciones, métricas, fallos, captura del estado final.
- **Criterio de salida** acordado antes del experimento: aprobar, ajustar, descartar o volver a analizar. No avanzar solo porque no aparecieron errores.

Registrar por experimento un archivo pequeño de configuración y resultados reproducibles; no presentar videos o imágenes como única evidencia. Conservar pruebas de regresión al introducir nuevas reglas.

## 5. Hipótesis inicial: propiedades físicas compartidas

**Esquema mínimo a ensayar**, no física fundamental exacta:
- **Espacio y cantidad:** posición/región, cantidad de materia, masa, volumen; densidad es derivada, no una propiedad arbitraria adicional.
- **Composición y estado:** componentes materiales y estado (por ejemplo sólido, granular o fluido), sin imponer catálogos completos de objetos finales.
- **Energía térmica:** cantidad de energía y capacidad para intercambiarla; temperatura se calcula bajo un modelo explícito.
- **Interacción mecánica:** movimiento, apoyo, resistencia/cohesión y contacto según materiales y geometría.
- **Transporte e intercambio:** movimiento de material y de energía entre zonas; reglas de fuentes/sumideros explícitas.

**Advertencia:** no todas estas propiedades son intrínsecas al material: permeabilidad depende de la estructura porosa y la escala; peso depende de la gravedad; presión depende de estado y condiciones. Evitar duplicar estados y asignar propiedades independientes contradictorias.

Modelo candidato para el primer laboratorio: región cerrada muy pequeña, representación discreta y pocas clases de materia abstracta. Esto es una **elección experimental reversible**, no una decisión definitiva sobre cómo se renderizará el mundo.

## 6. Hoja de ruta por hitos verificables

### Etapa 0 — Baseline y alternativas
**Entregable:** especificación de 2–3 fenómenos iniciales, invariantes, formato de resultados y evaluación de soluciones existentes (por ejemplo simuladores celulares, erosión y materiales). Evitar desarrollar una capacidad que ya existe con licencia e integración adecuadas.
**Prueba:** cada propiedad y mecanismo debe asociarse con un fenómeno observable y un test; descartar variables sin utilidad demostrable.

### Etapa 1 — Materia compartida, sin paisaje
**Hipótesis:** un esquema pequeño representa materiales distintos sin definir objetos finales.
**Implementación mínima futura:** espacio cerrado simple, material/cantidad/masa/volumen/energía, transformaciones trazables.
**Pruebas:** (a) conservación exacta o dentro de tolerancia numérica documentada de masa en sistema cerrado; (b) ningún estado imposible como masa negativa o dos cuerpos ocupando espacio excluyente; (c) misma semilla y entradas producen el mismo estado; (d) parámetros de composición distintos provocan efectos distintos solo cuando una regla lo justifica.
**Salida:** invariantes superados; esquema comprensible; sin propiedades redundantes.

### Etapa 2 — Reglas locales de intercambio
**Hipótesis:** transporte y fuerzas simples producen consecuencias verificables y consistentes.
**Implementación:** una o dos interacciones primero, como caída/apilamiento y flujo simplificado, sin aún «ríos» codificados.
**Pruebas:** (a) descenso de material móvil cuando hay hueco y no cuando está bloqueado; (b) flujo acorde con el gradiente elegido; (c) balances de materia y, si se simula energía, balance térmico; (d) alterar solo el gradiente cambia el resultado sin cambios ocultos.
**Salida:** comportamiento estable bajo casos límite y reproducible.

### Etapa 3 — Formación de estructuras
**Hipótesis:** reglas de depósito, cohesión, transporte o agregación producen configuraciones estables sin plantar la forma final.
**Prueba:** condiciones iniciales distintas producen patrones medibles; registrar conectividad, tamaño y estabilidad de agregados, y comparar con distribución aleatoria de materiales. Probar ablación de reglas: retirar una interacción debe cambiar la formación conforme a una predicción previa.
**Salida:** al menos un patrón con causa demostrable, sin proclamar novedad indefinida.

### Etapa 4 — Generación de estado inicial
**Hipótesis:** un generador produce territorios plausibles y variados, utilizables por la dinámica posterior.
**Pruebas:** semillas reproducibles; estados iniciales válidos; condiciones compatibles con las leyes de la etapa 2; variación mensurable entre semillas; ausencia de lugares imposibles o saldos negativos.
**Salida:** no simular millones de años para obtener un terreno inicial; distinguir claramente condiciones generadas de historia efectivamente simulada.

### Etapa 5 — Fenómenos ambientales acoplados
**Hipótesis:** interacciones entre relieve, agua, sedimentos y temperatura (solo las que hayan demostrado utilidad) generan cambios coherentes.
**Pruebas:** el transporte altera realmente la topología/material del terreno; retirar erosión evita la erosión predicha; una intervención local tiene consecuencias registradas aguas abajo; chequear balances y comportamiento bajo parámetros extremos.
**Salida:** subsistemas sobre un mismo estado; ninguna capa visual falsifica una transformación física.

### Etapa 6 — Persistencia y tiempo autónomo
**Hipótesis:** el mundo puede avanzar sin observador ni agente, detenerse y reanudarse sin perder causalidad.
**Pruebas:** guardar/cargar no altera resultados de una continuación determinista; avance por lotes versus paso continuo produce resultados equivalentes si el algoritmo lo permite; comparar escalas temporales y documentar aproximaciones; estados corruptos se detectan, no se arreglan silenciosamente.
**Salida:** historia causal auditable y reproducción de fallos.

### Etapa 7 — Organizaciones no prediseñadas
**Hipótesis:** las reglas compartidas permiten nuevas configuraciones funcionales sin una clase especial por cada resultado.
**Pruebas:** barrido de semillas y parámetros; medir variedad, estabilidad, persistencia y funciones observables; comparar con catálogo/plantillas y con ruido aleatorio; ensayo de ablación y casos en los que no emerge nada. No declarar «evolución abierta» sin evidencia longitudinal.
**Salida:** demostrar al menos una capacidad generativa que las plantillas no expliquen trivialmente, o documentar por qué no surgió.

### Etapa 8 — Escalabilidad e interfaz futura
**Hipótesis:** el núcleo puede ampliarse y eventualmente recibir un explorador o habitantes sin reescribir sus reglas.
**Pruebas:** consumo de CPU/memoria versus resolución, reproducción bajo distintas versiones, consultas de estado parcial sin modificarlo, intervención material igual desde distintos clientes.
**Salida:** contrato de observación/acción estable **sin implementar mentes, LLM ni NeuroLab**.

## 7. Prioridad inmediata

No comenzar por biomas, gráficos, árboles, personajes ni ecosistemas completos.

**Primer experimento propuesto:** «caja cerrada de materia»: demostrar conservación, acumulación/transporte local, comportamiento diferente de dos componentes simples y reproducibilidad. Debe poder ejecutarse sin interfaz visual y fallar de manera explicable. Los umbrales numéricos se definirán junto con el método de cálculo antes de correr la prueba.

## 8. Estado y próximas decisiones

- **Confirmado:** las cinco orientaciones del apartado 2 y la separación del trabajo cognitivo.
- **Propuesto, no aprobado todavía:** representación discreta inicial, variables del apartado 5, primer experimento y secuencia detallada del apartado 6.
- **No hecho:** implementación, ejecución de ensayos, benchmarking y validación de emergencia.
- **Próxima conversación:** revisar el conjunto mínimo de propiedades compartidas, reducirlo si es posible y aprobar el primer experimento.
