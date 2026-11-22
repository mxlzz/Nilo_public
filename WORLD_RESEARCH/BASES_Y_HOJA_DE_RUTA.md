# Mundo autónomo — fundamentos y hoja de ruta experimental

**Estado actualizado (2026-11-22):** etapa 0, gate de reutilización, **cerrada provisionalmente** con [ADR-0003](DECISIONES/ADR-0003_CIERRE_ETAPA_0_BASES_MODULARES.md). Etapa 1 **ABIERTA**, con estado H1–H6 y contacto rígido H7–H8 verificados. [ADR-0005](DECISIONES/ADR-0005_REPRESENTACION_ESPACIAL_HIBRIDA.md) (representación) y [ADR-0006](DECISIONES/ADR-0006_PROVEEDOR_CONTACTO_BULLET.md) (física local) siguen reversibles. **Ningún motor físico propio autorizado**, etapas 2–8 no completadas. Ver [auditoría](PROCEDIMIENTO_Y_AUDITORIA.md) y [ADR-0001](DECISIONES/ADR-0001_REUTILIZACION.md).
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

**Esquema inicial propuesto, no aprobado y sujeto a revisión tras evaluación de motores existentes**; no física fundamental exacta:
- **Espacio y cantidad:** posición/región, cantidad de materia, masa, volumen; densidad es derivada, no una propiedad arbitraria adicional.
- **Composición y estado:** componentes materiales y estado (por ejemplo sólido, granular o fluido), sin imponer catálogos completos de objetos finales.
- **Energía térmica:** cantidad de energía y capacidad para intercambiarla; temperatura se calcula bajo un modelo explícito.
- **Interacción mecánica:** movimiento, apoyo, resistencia/cohesión y contacto según materiales y geometría.
- **Transporte e intercambio:** movimiento de material y de energía entre zonas; reglas de fuentes/sumideros explícitas.

**Advertencia:** no todas estas propiedades son intrínsecas al material: permeabilidad depende de la estructura porosa y la escala; peso depende de la gravedad; presión depende de estado y condiciones. Evitar duplicar estados y asignar propiedades independientes contradictorias.

Modelo candidato para el primer laboratorio: región cerrada muy pequeña, representación discreta y pocas clases de materia abstracta. Esto es una **elección experimental reversible**, no una decisión definitiva sobre cómo se renderizará el mundo.

## 6. Hoja de ruta por hitos verificables

### Etapa 0 — Baseline y alternativas
**Entregable:** especificación de 2–3 fenómenos iniciales, invariantes, formato de resultados y evaluación **ejecutada** de soluciones existentes (incluyendo Sandspiel y The Powder Toy para materiales, WorldEngine para generación). Registrar evidencia, licencias y costo de adaptación; ver ADR-0001. Evitar desarrollar una capacidad que ya existe con licencia e integración adecuadas. **Gate obligatorio: cierre documentado de alternativas antes de implementar nuevas leyes físicas.**
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

**Primer ensayo exploratorio ya realizado:** «caja cerrada de materia» verifica únicamente balances de materia, capacidad y reproducibilidad del estado bajo transferencias manuales. 8 pruebas verificadas en [GitHub Actions](https://github.com/mxlzz/Nilo_public/actions/runs/44942005067). **No** demostró transporte espontáneo, estructuras, gravedad ni emergencia. Está en cuarentena arquitectónica hasta cierre de etapa 0. Próxima actividad: ensayos de reutilización descritos en ADR-0001, no ampliar el motor propio.

## 8. Estado y próximas decisiones

- **Confirmado:** las cinco orientaciones del apartado 2 y la separación del trabajo cognitivo.
- **Propuesto, no aprobado todavía:** representación discreta inicial, variables del apartado 5, primer experimento y secuencia detallada del apartado 6.
- **Implementado fuera de secuencia:** prototipo aislado de invariantes de materia, con 8 pruebas aprobadas por CI; no se adopta como motor.
- **No hecho:** benchmarks comparativos de motores, simulación física autónoma, generación ambiental ni validación de emergencia.
- **Estado de gates al 2026-11-21 (histórico):** etapa 0 abierta; etapa 1 spike no adoptado; etapas 2–8 sin iniciar.
- **Actualización verificada al 2026-11-22:** etapa 0 cerró exclusivamente la selección de alternativas por [ADR-0003](DECISIONES/ADR-0003_CIERRE_ETAPA_0_BASES_MODULARES.md). Etapa 1 continúa ABIERTA con H1–H6 (datos materiales, integridad, pérdida de geometría en altura, owner particionado y migración segura de ROI), ensayos CI e informes en `WORLD_RESEARCH/ETAPA_1_H{1..6}_*`. [ADR-0004](DECISIONES/ADR-0004_PROPIEDAD_INTEGRIDAD_ESTADO.md) y [ADR-0005](DECISIONES/ADR-0005_REPRESENTACION_ESPACIAL_HIBRIDA.md) son decisiones técnicas **reversibles para laboratorio**; no motor físico elegido. Ninguna etapa 2–8 se considera iniciada por estos ensayos, aunque hubo pruebas exploratorias adelantadas de procesos ambientales. Los apartados históricos de "sin benchmarks" y "alternativas pendientes" más arriba corresponden al diagnóstico anterior, no al estado vigente.
- **Próxima actividad aprobada por el plan:** regresar a los invariantes materiales faltantes de la etapa 1 y evaluar una ley local **ya existente** (etapa 2 futura), con gate previo y controles. No profundizar en infraestructura de formatos sin una necesidad física nueva demostrada. Mantener [controles auditables](PROCEDIMIENTO_Y_AUDITORIA.md).

## 9. Addendum al 22-11-2026 — Primera física comprobada, límites de etapa

**Este apartado actualiza el estado de avance; los apartados históricos de más arriba no deben usarse como fuente de estado vigente. No modifica los objetivos ni la secuencia acordada.**

- **H7:** PyBullet3.2.7 en Python3.11 simuló una caja rígida 1m/2kg que cae sobre plano (centro z≈0.500m), control sin gravedad inmóvil, sin plano caída libre, replay exacto, inventario xarray inalterado. [CI H7](https://github.com/mxlzz/Nilo_public/actions/runs/45036231904) y `ETAPA_1_H7_RESULTADOS_RIGID_CONTACT_BULLET.md`.
- **H8:** La región volumétrica real H5 se usó para **272 colliders estáticos de Bullet** formando una cavidad cerrada. Un cubo móvil cuya masa2kg provino de las 32kg retiradas manualmente quedó apoyado en z≈2.500m sobre piso oculto; control g0 sin fuerzas y replay exacto. Superficie idéntica a bloque lleno no habría permitido la posición inicial. Ledger A762kg = A730 estático + A2 cuerpo + A30 salida externa. Generador Landlab/Python3.13 → NetCDF comprobado → consumidor Bullet/Python3.11. [CI H8](https://github.com/mxlzz/Nilo_public/actions/runs/45037191905) y `ETAPA_1_H8_RESULTADOS_CAVIDAD_CONTACTO.md`.
- **Incidencias auditadas:** Landlab2.11 no pudo importarse en Python3.11 por dependencia `requireit` que usa sintaxis3.12; se separaron runtimes sin forzar actualizaciones. Un control inicial exigía falsamente 0 contactos en un cubo tocando pared lateral; la diagnóstica mostró fuerza cero en pared, y apoyo de fuerza positiva con gravedad. Enmienda documentada antes de CI final. No ocultar esos fallos.
- **Decisión**: [ADR-0006](DECISIONES/ADR-0006_PROVEEDOR_CONTACTO_BULLET.md) autoriza considerar Bullet proveedor local de cuerpos rígidos, **no** material deformable ni motor universal. La evidencia H8 refuerza utilidad de una ROI volumétrica frente a heightfield como geometría completa.
- **Etapa 1 permanece ABIERTA**: modelo de energía/temperatura/transferencia no definido, transformaciones materiales no ensayadas, tipo de materia granular/deformable pendiente; las cavidades fueron prescritas y las colisiones no deformaron el suelo. No hay emergencia abierta ni primer mundo operativo. **Etapas 2–8 siguen sin gate formal completado**; que un solver existente ejecute gravedad como prueba exploratoria no significa implementar o cerrar etapa 2.
- **Próximo paso que sí responde al objetivo**: evaluar un mecanismo existente de **redistribución autónoma de materia** con un balance y un control diferencial (sin gravedad/gradiente), contrastando el encaje real de TPT/Sandspiel/GeoTaichi/otros con la región material. No escribir motor granular propio ni añadir nuevos formatos sin necesidad. La energía se incorporará solo con fenómeno y presupuesto concretos, previa decisión de plan.


## 10. Addendum 2026-11-22 — H9, material de sedimento físicamente actualizado

**H9 APROBADA** por [CI 45048479951](https://github.com/mxlzz/Nilo_public/actions/runs/45048479951): `SpaceLargeScaleEroder` de Landlab actualiza por paso un único owner material `xarray`; el cálculo de volumen de salida proviene del solver, no de un ajuste del ledger. Inventario inicial **10.080.000kg**, final **9.607.448,861428004kg** y exportado **472.551,1385719963kg**; residual impreso **0kg**, 50 nodos con ganancia neta. Control `K_sed=0` inmóvil, replay exacto, cinco corruptelas rechazadas y snapshot NetCDF reabierto con hash idéntico. Ver [protocolo](ETAPA_1_H9_PROTOCOLO_SEDIMENTO_OWNER.md) y [resultados](ETAPA_1_H9_RESULTADOS_SEDIMENTO_OWNER.md).

**Alcance exacto:** fenómeno fluvial sedimentario **2.5D**, con roca inerte y densidad ficticia; aún sin conexión a cavidades/ROI3D ni movimiento de granos/deformación. **Etapa 1 sigue ABIERTA**, etapas 2–8 no se declaran cerradas o iniciadas formalmente. **Próximo gate:** ensayar físicamente la redistribución granular/deformable **3D**, solo si la evaluación de solvers existentes justifica el costo; no crear motor propio ni otra infraestructura de serialización sin una brecha causal. La energía y las transformaciones requieren experimentos separados y con conservación explícita, sin campos especulativos.
