# Mundo autónomo — fundamentos y hoja de ruta experimental

**Estado vigente al 2026-11-22 (prevalece sobre addenda históricos):** etapa 0 **cerrada provisionalmente** ([ADR-0003](DECISIONES/ADR-0003_CIERRE_ETAPA_0_BASES_MODULARES.md)); etapa 1 **cerrada provisionalmente solo en laboratorio mínimo** tras H15/H16 ([ADR-0009](DECISIONES/ADR-0009_GATE_ETAPA_1_MINIMO.md)); etapa 2 **cerrada provisionalmente solo para dos leyes locales ensayadas por separado** tras H17/H18 ([auditoría](AUDITORIA_CIERRE_ETAPA_2_2026-11-22.md)); etapa 3 **cerrada provisionalmente solo para agregado granular rígido de laboratorio** tras H26+H28 ([ADR-0014](DECISIONES/ADR-0014_CIERRE_GATE_ETAPA_3.md)); etapa 4 **cerrada provisionalmente para condiciones iniciales 2.5D y contacto local** tras H29+H30 ([ADR-0016](DECISIONES/ADR-0016_CIERRE_GATE_ETAPA_4.md)); etapa 5 **cerrada provisionalmente SOLO para acoplamiento unidireccional mínimo** tras H31 + propagación material parcial H32 ([auditoría](AUDITORIA_CIERRE_ETAPA_5_2026-11-22.md)); etapa 6 **cerrada provisionalmente SOLO para restart de subsistemas físicos aislados** tras H33–H35 ([auditoría](AUDITORIA_CIERRE_ETAPA_6_2026-11-22.md)); etapa 7 **ABIERTA como investigación funcional**, etapa 8 sin gate completado. No hay un mundo operativo ni acoplamiento físico conjunto. Ningún motor propio autorizado, representación y proveedores experimentales reversibles. Ver [procedimiento](PROCEDIMIENTO_Y_AUDITORIA.md).
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

## 11. Addendum 2026-11-22 — H10 contacto colectivo de granos, NO suelo deformable

[H10](ETAPA_1_H10_RESULTADOS_GRANOS_RIGIDOS.md) **aprobada por [CI 45049166835](https://github.com/mxlzz/Nilo_public/actions/runs/45049166835)**, con protocolo previo, 27 esferas de material abstracto A (6,75kg total), gravedad/contactos de Bullet 3.2.7, 720 pasos, control sin gravedad, control sin suelo, replay exacto, rechazo de cinco estados inválidos y un único propietario xarray del inventario. Hubo 297 pasos con fuerzas de contacto entre granos y dispersión lateral significativa; **los granos terminaron extendidos sobre el plano, NO formaron una pila estable**. El primer CI H10 falló por mutación prohibida de una coordenada xarray y se documentó/reparó sin alterar criterios físicos.

H10 complementa H9 (transporte fluvial 2.5D) con una observación de dinámica discreta 3D, pero **ninguno** acredita deformación plástica, fractura, erosión de cavidades, tiempo acoplado Landlab–Bullet, energía térmica o aparición sostenida de estructuras. Etapa1 ABIERTA, etapas2–8 no se dan por iniciadas formalmente. **Próximo gate físico**: justificar y evaluar, antes de integrar, un solver de material granular/continuo adecuado para producir morfología estable local bajo presupuesto material, conservando controles de ablación; no montar un motor universal ni programar física propia por inercia.

## 12. Addendum 2026-11-22 — H11 deformación MPM verificada; H12 reposo no demostrado

**H11** [CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45055263832) usa **GeoMPM upstream** de PINNeAPPle Apache-2.0 sin nueva física: material volumétrico 3D de 108 puntos / 2,7kg se deforma bajo gravedad y responde diferencialmente a fricción interna30° frente0°, queda inmóvil sin gravedad, replay y owner exactos. Ver [resultado](ETAPA_1_H11_RESULTADOS_MPM_3D.md), [decisión comparativa](DECISIONES/ADR-0007_GATE_MPM_3D.md). Sin calibración geotécnica ni prueba de reposo a 0,25s.

**H12** [CI FAILURE por criterio físico](https://github.com/mxlzz/Nilo_public/actions/runs/45055570920) comprobó periodo hasta1,2s de la misma física con dominio lateral amplio. Con fricción30° la velocidad bajó a0,0259m/s, cambió poco la envolvente de0,8→1,2s y cero partículas tocaron paredes laterales, PERO **61,11%** quedaron en el límite inferior z=1,5dx impuesto por el solver. El protocolo había limitado ese clamping a50% para declarar soporte no dominado por la frontera, por lo que **H12 NO APROBADA** como prueba de estructura estable. Con fricción0°, hubo dispersión a límites, alta velocidad residual y piso mayormente clamped. Ver [resultado y limitaciones](ETAPA_1_H12_RESULTADOS_REPOSO_MPM.md).

**Juicio de continuidad:** no adoptar aún PINNeAPPle ni acoplarlo a ROI H5; falta validación independiente de constitutivo y condiciones de contacto/soporte. Priorizar prueba comparativa mínima de un solver geomecánico independiente y preexistente (GeoTaichi candidato con MIT/BSD incompatibilidad: atención, **es GPL-3.0**), sin copiar código protegido ni asumir estabilidad física. Stage1 ABIERTA, etapas2–8 no completadas. No confundir un dato inmóvil por clamp con organización emergente.

## 13. Addendum 2026-11-22 — H13A no ejecutó física; H14 energía verificada, etapa1 abierta

- **H13A GeoTaichi:** [CI 45055983838](https://github.com/mxlzz/Nilo_public/actions/runs/45055983838) falló por importación Open3D, y el [único reintento 45056130916](https://github.com/mxlzz/Nilo_public/actions/runs/45056130916) por importación Plotly aun tras instalar Open3D. Los dos fallaron antes de ejecutar MPM; no constituyen rechazo del solver físico. Se detuvo la persecución de dependencias conforme al protocolo. [Informe](ETAPA_1_H13A_RESULTADOS_GEOTAICHI_CPU.md).
- **H14 FiPy:** [CI 45056513417 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45056513417). 8 regiones 1D con masa16kg y energía inicial2.400.000J intercambiaron calor; error energético máximo medido4,66×10⁻⁹J, controles sin conducción/sin gradiente inmóviles, replay, corruptelas rechazadas y NetCDF exacto. FiPy4.0.3 resolvió la física, xarray conservó inventario. **No se creó nueva ley térmica.** [Informe](ETAPA_1_H14_RESULTADOS_ENERGIA_FIPY.md).
- **Revisión independiente del gate:** [AUDITORIA_GATE_ETAPA_1_POST_H14_2026-11-22.md](AUDITORIA_GATE_ETAPA_1_POST_H14_2026-11-22.md). Etapa1 **ABIERTA**: falta una transformación común verificable y estado coherente cuando coinciden materia+energía+posición. No hay demo operativa de mundo, ni evolución abierta; etapas2–8 no formalmente completadas. No proseguir con más motores geomecánicos por inercia; priorizar fenómeno causal nuevo con hipótesis/presupuesto antes de intentar integración, sin alterar el objetivo.


## 14. Addendum 2026-11-22 — Etapas 1 y 2 cerradas provisionalmente, comienza Etapa 3

**Etapa 1, gate mínimo de «materia compartida»:** H15 con [CI 45058971601](https://github.com/mxlzz/Nilo_public/actions/runs/45058971601) probó fracción de fase derivada de masa/energía común con calor latente; H16 [CI 45059387895](https://github.com/mxlzz/Nilo_public/actions/runs/45059387895) probó dos materiales A/B con inventarios únicos de masa y energía, volumen derivado, fases, controles y replay. [Auditoría de cuatro pruebas E1](AUDITORIA_CIERRE_ETAPA_1_2026-11-22.md), [ADR-0009](DECISIONES/ADR-0009_GATE_ETAPA_1_MINIMO.md) **cerraron provisionalmente solo E1 en laboratorio pequeño**. No se aprobó motor 3D, mezclado continuo ni energía termomecánica conjunta.

**Etapa 2, gate local de dos procesos:** H17 [CI 45059850320](https://github.com/mxlzz/Nilo_public/actions/runs/45059850320) probó gravedad libre/bloqueada y publicó cinemática en owner xarray. H18 [CI 45060100229](https://github.com/mxlzz/Nilo_public/actions/runs/45060100229) probó que reducir a la mitad la pendiente de bedrock redujo un38,987% la exportación de sedimento, con balance de masa explícito. [Auditoría de cuatro pruebas E2](AUDITORIA_CIERRE_ETAPA_2_2026-11-22.md) **cerró provisionalmente solo dos mecanismos locales aislados**. Los mecanismos no están acoplados al mismo espacio/tiempo; E5 y E6 mantienen esos requisitos.

**Fallos no borrados:** H12 no demostró estabilidad de suelo sin artefactos de frontera; H13A GeoTaichi se bloqueó en importaciones antes de ejecutar física; H15.0 falló hash NumPy en checkpoint, luego corregido; H16.0 fue YAML inválido antes de jobs, luego corregido. [CI fallidas](https://github.com/mxlzz/Nilo_public/actions/runs/45059294431) se conservaron, sin alterar tolerancias físicas.

**Próximo gate Etapa 3:** formación de depósitos/patrones **que no provengan trivialmente de la condición inicial** y persistan bajo dinámica local, con controles diferenciales/aleatorios condicionados. Aprovechar Landlab H9/H18 para una prueba de conectividad/persistencia antes de instalar otro solver. Si no hay patrón con causa y contraste, mantener E3 abierta y reconsiderar alternativas existentes (pyDeltaRCM u otro). No confundir erosión y depósitos ordinarios con emergencia funcional u open-ended evolution.

## 15. Addendum 2026-11-22 — H19 negativo bajo nulo condicionado; H20A screening de proveedor

**H19** [CI 45060568065](https://github.com/mxlzz/Nilo_public/actions/runs/45060568065) obtuvo 50 nodos de depósito neto en un único componente conectado persistente entre t12 y t24 (Jaccard1), **pero** el nulo de512 permutaciones que conservó los conteos de depósitos por fila ya produjo componente mayor P95=50; la hipótesis exigía tamaño observado≥P95+3. **H19 NO APROBADA** como organización espacial distinguible de la plantilla inicial. No cambiar umbrales; [informe de fallo científico](ETAPA_3_H19_RESULTADOS_DEPOSITO_CONEXO.md). La conservación de masa Landlab y su transporte físico permanecen válidos.

**Screening H20A** [ADR-0011](DECISIONES/ADR-0011_H20_SCREENING_PYDELTARCM.md), [protocolo](ETAPA_3_H20A_PROTOCOLO_PYDELTARCM.md): pyDeltaRCM MIT es un modelo reconocido para dinámica deltaica, **pero su propio manual declara falta de conservación estricta del volumen de agua y sedimento**. Se estudia solo como **referencia morfológica externa**, con diagnóstico de entradas/pérdidas/exportación, sin autorizarlo como propietario de materia ni añadirlo al mundo. No considerar aprobado H20A hasta CI con métricas y dictamen.

**Gate E3 continúa ABIERTA**; la conectividad superficial no equivale a estabilidad mecánica, patrón funcional o autoorganización general. El próximo cambio debe superar controles condicionados, no solo producir imágenes llamativas. Main/NeuroLab intactos.

## 16. Addendum 2026-11-22 — H20A solo morfología externa; H21 no segregó con el régimen probado

**H20A pyDeltaRCM:** [CI 45060886245 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45060886245) ejecutó proveedor MIT v2.3.0 con 12 pasos en malla30×40; cambió 423 celdas, 408 fuera del inlet, resultados diferentes entre semillas y reproducción exacta. **No se adoptó:** upstream reconoce **ausencia de conservación estricta de sedimento y agua**; entrada375.000m³, cambio neto de lecho361.840m³ y exportación14.865m³ medidos por separado, **sin balance material global cerrado**. Es un punto de comparación morfológico, no stock físico del mundo. [Informe](ETAPA_3_H20A_RESULTADOS_PYDELTARCM.md).

**H21 FiPy Cahn–Hilliard:** [CI 45061348648 FAIL por gates físicos](https://github.com/mxlzz/Nilo_public/actions/runs/45061348648) ensayó segregación de mezcla binaria A/B 2D con masa conservada, pero la varianza de fracción disminuyó 0,001599→0,0000554 en vez de crecer; q05/q95 finales0,491/0,513, no fase segregada. Un rótulo binario produjo vecinos similares pero quedó apenas0,0197 por encima del p95 del nulo condicionado, menor que el margen0,08 exigido. **No aprobada** como estructura. El check complementario `sum(total)==400.0` dio falso negativo por redondeo de5,7e-14kg, muy por debajo del gate físico1e-4kg; se documentó sin alterar umbrales. [Informe](ETAPA_3_H21_RESULTADOS_CAHN_HILLIARD.md).

**Etapa3 SIGUE ABIERTA.** Diagnóstico plausible: longitud de dominio y penalización de gradiente `epsilon` en la ley Cahn–Hilliard suprimen modos finos de inestabilidad durante el tiempo de H21. Requiere nuevo preregistro comparativo de escala (H22) y controles causales, no ajustar H21 a posteriori. H19/H21 impiden declarar emergencia por patrones visuales/dicotomizados. Los cierres limitados E1/E2 y sus evidencias permanecen vigentes; no hay mundo autónomo operable.

## 17. Addendum 2026-11-22 — E3 H22–H28: separar causalidad, estabilidad y nulos

**Estado vigente, sin redefinir el plan:** etapas0–2 cerradas solo dentro de gates mínimos experimentales; **Etapa3 ABIERTA**, E4–E8 sin gate. El éxito de un ensayo local NO crea motor físico universal.

- **H22:** [CI FAIL](https://github.com/mxlzz/Nilo_public/actions/runs/45084072284), pero test del mecanismo Cahn–Hilliard mostró segregación causal al bajar epsilon1→0,5 con varianza final0,0000554→0,07053 y masa A/B conservada. Falló nulo espacial condicionado (+0,072 frente+0,08 exigido) y Jaccard0,578 frente0,60. [Resultado](ETAPA_3_H22_RESULTADOS_ESCALA_INTERFAZ.md).
- **H23:** [CI FAIL](https://github.com/mxlzz/Nilo_public/actions/runs/45084330437) en prolongación 600pasos al recibir `phi=1,00101` en seed20261124 paso579. Rechazó estado imposible **sin clipping**. No es evidencia de agregados físicos; la línea de composición ideal se pausó en favor de mecánica granular. [Resultado](ETAPA_3_H23_RESULTADOS_PERSISTENCIA_SEMILLAS.md), [ADR-0013](DECISIONES/ADR-0013_E3_MECANICA_GRANULAR_BULLET.md).
- **H24:** [CI FAIL](https://github.com/mxlzz/Nilo_public/actions/runs/45084751801), 125 esferas de3,125kg formaron montículos de~0,75m por fricción sobre suelo abierto vs monocapa~0,15m y dispersión sin fricción. **No** cumplieron reposo ni componente de fuerza≥45. [Resultado](ETAPA_3_H24_RESULTADOS_PILA_GRANULAR.md).
- **H25:** [CI FAIL](https://github.com/mxlzz/Nilo_public/actions/runs/45084934469), continuación bitwise idéntica de H24 hasta3600pasos: velocidades finales bajas, pero montículos perdieron altura y conectividad a17/27 granos; más duración no solucionó el problema. [Resultado](ETAPA_3_H25_RESULTADOS_ASENTAMIENTO_TARDIO.md).
- **H26:** [CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45085243163), condición inicial distinta físicamente justificada: introducir125 esferas gradual y SIN solapamientos desde fuente, cero velocidad horizontal, misma fricción y suelo sin paredes. Dos seeds produjeron montículos de0,724/0,894m, componentes de fuerza73/92 y reposo tardío bajo umbrales. Sin fricción: monocapa y cero contactos grano-grano. Massa3,125kg controlada fuente+Bullet, replay y owner xarray final exacto. **H26 APRUEBA agregación granulada estable en ventana corta**, no constitución de roca/caverna ni evolución abierta. [Resultado](ETAPA_3_H26_RESULTADOS_DEPOSITO_GRADUAL.md).
- **H27:** [CI FAIL no concluyente](https://github.com/mxlzz/Nilo_public/actions/runs/45085565080): las mismas pilas H26 mostraron redes **geométricas** de proximidad107/101 (distintas de redes de contacto de fuerza), pero generar nulos aleatorios no solapados preservando z/radial mediante inserción secuencial fue inviable (1/256 y0/256 nulos); **no hay p-valor estimable**. [Resultado](ETAPA_3_H27_RESULTADOS_NULO_GRANULAR.md).
- **H28:** [prerregistro](ETAPA_3_H28_PROTOCOLO_NULO_MCMC.md) sustituye únicamente el algoritmo de muestreo del nulo por una cadena Markov de esferas casi excluyentes que sale de estados H26 válidos; conserva el MISMO umbral espacial y exige pruebas independientes de mezcla. **No dictaminarla antes del CI y auditoría**. Si falla también, dejar E3 abierta con hueco claramente registrado, no perseguir estadística a cualquier costo.

**Lectura de alcance:** H26 por primera vez aporta evidencia de agregado volumétrico **bajo fricción con reposo**. H24/H25 demuestran que la **forma de alimentación** importa, no solo la fuerza/fricción/tiempo. La sección6 de Etapa3 también exige contraste con distribución aleatoria: ese criterio sigue abierto hasta un nulo comparable y muestreable. No confundir condición física μ0 con un nulo geométrico alazar. Los estados internos y reservorio de H26 no son todavía reanudables, y no hay acople con H5/Landlab/FiPy.

## 18. Addendum 2026-11-22 — Cierre limitado de Etapa3 y entrada a Etapa4

**Etapa3 cerrada provisionalmente SOLO para formación de montículo granular rígido, no mundo integrado:** [H26 CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45085243163) aportó dos seeds con fricción causante de un agregado soportado/quieto (componentes de fuerza73/92, altura0,724/0,894m), sin paredes; [H28 CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45085820365) comparó redes de proximidad107/101 con256 nulos de esferas casi excluyentes por seed, P95 de31/33, controles de mezcla MCMC aprobados, sin manipular H26. Se mantiene [H27 CI FAIL](https://github.com/mxlzz/Nilo_public/actions/runs/45085565080) por generador de nulos secuencial bloqueado. [Auditoría completa](AUDITORIA_CIERRE_ETAPA_3_2026-11-22.md) y [ADR-0014](DECISIONES/ADR-0014_CIERRE_GATE_ETAPA_3.md) cierran solo los criterios originales mínimos de E3. No se declara evolución abierta, diversidad funcional ni equilibrio geológico.

**Etapa4 iniciada como investigación, SIN gate aprobado:** reusar generación de estado inicial, no simular tiempos geológicos ni crear motor nuevo. Artefactos existentes [WorldEngine productor](experiments/export_worldengine_height.py), [WorldEngine→Landlab](experiments/probe_worldengine_to_landlab.py) y [ADR-0003](DECISIONES/ADR-0003_CIERRE_ETAPA_0_BASES_MODULARES.md) muestran un generador de alturas sin unidades físicas originarias, un puente Python3.11→3.13 y erosión. Su prueba anterior convertía muestras de **centro de celda a nodos sin geométría congruente** y fijaba arbitrariamente alturas a0–50m. E4 exige explicitar escala y ubicaciones (núcleo interior/hala), dos seeds y replay, owner material con balance y validación, flujo de Landlab nativo, sin inferir geología real. [ADR de selección E4](DECISIONES/ADR-0015_SELECCION_GENERADOR_E4.md) se documentará antes de la nueva prueba.


## 19. Addendum 2026-11-22 — E4 cerrada provisionalmente; E5 inicia sin acoplamiento ficticio

**Etapa4, gate inicial mínimo aprobado:** [H29](ETAPA_4_H29_RESULTADOS_SEMILLAS_TERRITORIO.md) [CI 45086430133 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45086430133) verificó WorldEngine dos seeds distintas y replay exacto, alturas raw arbitrarias y transformación0–50m NOMINALES, centro de muestra→Landlab core con halo sin materia, erosión nativa en dos terrenos con masa inicial921.600.000kg y desvío max1,19×10⁻⁷kg, K_sed=0 inmóvil. [H30](ETAPA_4_H30_RESULTADOS_CONTACTO_TERRENO.md) [CI 45086818016 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45086818016) tomó el MISMO artefacto WorldEngine para probar superficies locales trianguladas sobre suelo generado: raycast coincide con triángulos fuente, Bullet gravedad apoya cuerpo2kg, controles sin g/sin mesh, replay y NetCDF. Los **tres jobs H29/H30** de esa CI están en success. [Auditoría E4](AUDITORIA_CIERRE_ETAPA_4_2026-11-22.md) + [ADR-0016](DECISIONES/ADR-0016_CIERRE_GATE_ETAPA_4.md) **cierran provisionalmente SOLO E4 de laboratorio**, no geología ni malla completa.

**Etapa5 ABIERTA:** E4 validó **por separado** Landlab y Bullet tomando fuente común, pero NO hay un mismo owner de materia durante sus dos dinámicas, ni consecuencia de erosionar un material sobre el contacto posterior en otra física. El primer experimento de E5 debe probar **flujo causal unidireccional** entre suelo erosionado desde owner por Landlab y contacto rígido Bullet sobre ese mismo relieve cambiado; K0 como intervención de control; presupuesto soil+export+body y fuente raw trazable. No confundir enlace secuencial unilateral con retroacción del cuerpo sobre el suelo o historia ambiental completa. Etapa6 requiere checkpoint a mitad y reproducibilidad por continuación.


## 20. Addendum 2026-11-22 — H31 positivo, H32 negativo fuerte y gate E5 mínimo

**H31 (SUCCESS):** [CI 45088160893](https://github.com/mxlzz/Nilo_public/actions/runs/45088160893) verifica en el mismo owner material el tránsito WorldEngine→Landlab suelo erosionado→Bullet contacto, con body2kg en reservorio y luego activo, budget `soil + export + body` cerrado, geometría derivada y propagación de una alteración global de `K_sed` al contacto. Secuencial, runtimes y relojes diferentes, sin feedback.

**H32 (NO APROBADA):** [CI 45091763734](https://github.com/mxlzz/Nilo_public/actions/runs/45091763734) confirma que poner `K_sed=0` solo en9 nodos propaga diferencias de materia aguas abajo de hasta3.812/12.256kg en dos semillas con ledger cerrado, pero el máximo cambio de superficie downstream fue solo−0,000113/−0,000317m nominales, frente a umbral estrictamente fijado de `|delta_z|>0,003m`. **No se ejecutó la fase Bullet downstream de H32**. El [primer fallo instrumental](ETAPA_5_H32_INCIDENCIA_0_HASH_NETCDF.md) por `numpy.int32` en JSON de NetCDF se corrigió sin cambiar física, y [resultado científico](ETAPA_5_H32_RESULTADOS_K_LOCAL_AGUAS_ABAJO.md) quedó rechazado sin relajar umbrales.

**E5 cerrada provisionalmente SOLO en alcance original mínimo:** [auditoría contra cuatro criterios originales](AUDITORIA_CIERRE_ETAPA_5_2026-11-22.md). H31 cubre cambio material→relieve→contacto, ablación K0 y owner común; H32 cubre requisito literal de **consecuencia material local aguas abajo** pero **NO** su criterio reforzado de contacto downstream. No hay física ambiental acoplada bidireccional, presupuesto energético total, calibración geológica ni reloj común. El cierre delimitado **no aprueba H32**.

**Próximo gate E6:** demostrar restart a mitad de una trayectoria física con checkpoint desde owner, sin rerun de pasos anteriores, comparado con ejecución continua; registrar estados ocultos del proveedor cuando importen, corrigiendo ninguna trayectoria sin evidencia. Etapas7–8 no habilitadas. Antes de cada avance leer HEAD y auditorías GitHub para no duplicar trabajo: se eliminó un H26 redundante conservando el original [CI 45085243163](https://github.com/mxlzz/Nilo_public/actions/runs/45085243163).

## 21. Addendum 2026-11-22 — Restart reproducible (E6 mínimo), entrada condicionada a Etapa7

**H33** [CI 45092764108 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45092764108): Landlab2.11 desde WorldEngine+owner xarray de suelo y cuerpo reservorio ejecuta6 pasos en una sola corrida o3+reinicio en otro runner+3. El final de los3 escenarios (seed7321/8128 K0,1 y seed7321 K0) coincide **bit a bit** en masa, salida, tiempo y SHA final, con saldo hasta1,192e−7kg de error frente0,09216kg admisible. [Informe](ETAPA_6_H33_RESULTADOS_RESTART_LANDLAB.md). Primeras dos CI fallaron solo al emitir NumPy bool en JSON; incidentes conservados y JSON corregido sin tocar física.

**H34** [CI 45092703790 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45092703790): PyBullet3.2.7 guarda contacto rígido a paso360 como cache nativa `.bullet`+owner material NetCDF, restaura en otro runner y completa361–720 idéntico bit a bit a la trayectoria720. [Informe](ETAPA_6_H34_RESULTADOS_CHECKPOINT_BULLET.md).

**H35** [CI 45093344413 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45093344413): en la pila original H26 guarda al paso1200 **104 granos físicos liberados y21 en cola**, masa total3,125kg con únicos IDs fuente y caché Bullet; reconstruye ambos en runner nuevo y ejecuta solo1201–3688, reproduciendo exactamente el owner H26 histórico `ac1dd51b214ede...`, secuencia de liberaciones, contactos y velocidades. [Informe](ETAPA_6_H35_RESULTADOS_RESTART_FUENTE_GRANULAR.md).

**[Auditoría formal E6](AUDITORIA_CIERRE_ETAPA_6_2026-11-22.md):** **cerrada provisionalmente para tres subsistemas de laboratorio, no para un mundo unificado reiniciable**. La deuda explícita de reloj común, checkpoints end-to-end Landlab→Bullet, energía térmica conjunta y fuentes materiales múltiples permanece, pero no justifica desarrollar un scheduler por sí sola. Reinicio de proceso del solver está demostrado dentro de la misma versión, sin observador ni reejecutar prefijos, y los stocks inválidos fueron rechazados.

**E7 ABIERTA:** siguiente pregunta exige **función observable** de una estructura formada sin plantilla, no una simple figura conectada o apariencia. La pila H26 puede probarse como potencial obstáculo/soporte para otro cuerpo mediante Bullet, con controles de la misma materia dispersa por abolición de fricción y condiciones idénticas de prueba. **No asumir que este efecto existe** ni llamar emergencia abierta por una sola barrera. Investigar/reutilizar proveedore(s) externos antes de programar reglas; preregistrar hipótesis/nulos/fallos, no imponer un objeto especial «pila».

## 22. Addendum 2026-11-22 — E7 H36 negativo e integración causal H37 demostrada

**E7 H36 NO aprobada** [CI 45094013248](https://github.com/mxlzz/Nilo_public/actions/runs/45094013248), [informe](ETAPA_7_H36_RESULTADOS_FUNCION_PILA_IMPACTO.md): la misma pila granular H26 sin plantilla interceptó la esfera externa a centros0,686m/0,945m en dos semillas, mientras con fricción cero y materia dispersa tocó el piso a0,147m. Tras impacto se conservaron los agregados, pero la segunda esfera continuaba con velocidad0,341m/s contra umbral preregistrado<0,12m/s. **Contacto funcional diferencial sí, función de soporte duradera en ambas semillas no demostrada**. No prolongar arbitrariamente el ensayo ni rebajar gates para «salvarlo». [Auditoría de retorno](AUDITORIA_VALOR_ETAPA_7_POST_H36.md).

**Dimensiones/relojes de la integración** [auditados](AUDITORIA_UNIDADES_Y_RELOJES_PRE_CICLO_INTEGRADO.md): WorldEngine produce alturas arbitrarias escaladas a `m_nominal`; Landlab usa `landlab_t_bench` de modelo y no segundos calibrados, Bullet usa `bullet_t_s` con `dt=1/240s`. NO se pueden acoplar números de tiempo por igualdad o fijar una razón arbitraria sin evidencia. Solo una secuencia causal con dos relojes etiquetados es científicamente admisible por ahora.

**H37 APROBADA** [CI 45094662094, cuatro jobs SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45094662094), [informe](H37_RESULTADOS_RESTART_CADENA_SUELO_CONTACTO.md): mismos dos terrenos WorldEngine, K_sed=.1 y K=0, sedimentación Landlab6 pasos continuos vs checkpoint3+continuación4–6 en otro proceso, después Bullet720 pasos bajo contacto con malla derivada del **mismo owner material**. Para los cuatro casos, masa/export, geometría, primer contacto, velocidad/posición del cuerpo y SHA final **idénticos bit a bit** entre ambas historias. La erosión hizo bajar el primer contacto −0,08123 y −0,07098m **nominales** para las dos seeds, frente a sus controles. **Es una cadena de dos solvers causal y reanudable**, no un único mundo persistente/simultáneo ni SI geológico validado.

**Estado sin modificación del gate:** etapas0–6 cerradas **solo provisionalmente en alcance mínimo experimental**; **E7 ABIERTA** por falta de variedad/robustez de funciones en un mundo compartido, E8 sin gate. Siguiente inversión selectiva: comprobar si las piezas existentes pueden constituir **un ciclo longitudinal observable de avance material** con eventos y dos relojes sin inventar scheduler, GUI, agentes, nuevas leyes de contacto o física fluvial. Exigir una capacidad funcional y su comparación con referencia, no métricas burocráticas. Si no hay nueva capacidad física, detener proliferación de ensayos y reevaluar alcance del proyecto.

## 23. Addendum 2026-11-23 — Continuidad de cuerpo bajo terreno cambiante (H38–H40)

**H38 NO APROBADA** [CI](https://github.com/mxlzz/Nilo_public/actions/runs/45299333730), [informe](H38_RESULTADOS_TERRENO_MUTABLE_CUERPO_ACTIVO.md). Actualizar heightfield in situ modifica raycast, pero mantiene apoyo fantasma19,62N y esfera inmóvil con hueco de0,2m. No adoptar `replaceHeightfieldIndex` para terreno en contacto. Fallos instrumentales YAML y atributo NetCDF registrados y corregidos por separado.

**H39 APROBADA variante B** [CI](https://github.com/mxlzz/Nilo_public/actions/runs/45299570089), [informe](H39_RESULTADOS_INVALIDACION_CONTACTO.md). Despertar cuerpo tras actualización in situ NO resuelve H38. Sustituir exclusivamente collider estático derivado, sin reiniciar cuerpo dinámico, sí permite caída por gravedad y recuperación de apoyo tras ambos descensos prescritos. Masa y replay exactos; control sham no produce descenso.

**H40 APROBADA** [CI](https://github.com/mxlzz/Nilo_public/actions/runs/45299940537), [informe](H40_RESULTADOS_EPOCAS_SUELO_CUERPO.md). Dos seeds WorldEngine H37 × activo/control K0, tres épocas Bullet de3s, suelo Landlab t0/3/6 en benchmark. El mismo cuerpo conserva identidad y cinemática instantánea durante dos sustituciones de malla derivada de suelo que disminuye realmente según Landlab, pierde apoyo y vuelve a contactar sin teletransporte. Gates completos, balance, replay y NetCDF aprobados. Los controles K0 reproducen prefijo y no producen huecos. No confundir con proceso sincronizado o bidireccional; Landlab se calculó previamente por independencia del cuerpo, tiempo geomorfológico no calibrado. No se ha comprobado aumento de terreno bajo cuerpo ni restart de esta cadena a mitad de contacto.

**Decisión de enfoque:** E7 continúa ABIERTA según §6; H40 resuelve una dependencia de integración, no la emergencia funcional. Evitar nuevos bancos de mera serialización u orquestación sin capacidad necesaria. La siguiente inversión debe someter a prueba una organización con función observable en territorio cambiante y controles de estructura/azar, aprovechando H26/H28/H36/H40; evaluar utilidad de un prototipo mínimo ejecutable, sin prometer un mundo completo ni evolucionar el plan por inercia. Main y NeuroLab intactos.


## 24. Addendum 2026-11-24 — H41 funcionalidad de tránsito (en ejecución, sin dictamen)

Alineación con E7 y auditoría H36/H40: [prerregistro H41](H41_PROTOCOLO_TRANSITO_AGREGADO_SUELO_CAMBIANTE.md), commit `657703bd6c751a41e5991a0fc331c3edfed1e9b3`, anterior al [arnés](experiments/probe_h41_aggregate_transit.py) `a0ff8dd1c449917bea924fd63bb129a233da0d14` y workflow `e59ac265f71a369e819ac57785d2415f3edbcd31`. Pregunta nueva: modificación causal del tránsito horizontal por granos autoformados después de dos épocas de erosión real Landlab; dos pares de semillas, K activo/inactivo, granos activos/sin fricción y suelo solo con granos en reservorio. Se mantienen relojes separados y geometría nominal; ningún motor nuevo. H36 sigue no aprobada. Se verificó que [CI H41 run 45389348480](https://github.com/mxlzz/Nilo_public/actions/runs/45389348480) inició; **no hay resultado físico todavía**. Próximo paso obligatorio: consultar los tres jobs de este run, recuperar métricas y artefactos, contrastar los gates originales, documentar incidencias y resultado sin cambiar criterios. No iniciar H42 por inercia. E0–E6 conservan sus cierres provisionales, E7 ABIERTA, E8 no iniciada. Main/NeuroLab intactos.


## 25. Addendum 2026-11-24 — H41 negativa; H42 observación independiente

[H41 informe auditado](H41_RESULTADOS_TRANSITO_AGREGADO_SUELO_CAMBIANTE.md) (`abd737a6222e867071db21aa3e3e8972e84344b2`): CI 45389348480 concluyó FAILURE por gates físicos/instrumentales preregistrados, no por error de ejecución. Los cuatro activos conservan 125 granos e integridad al atravesar las dos épocas de suelo, y hay contacto con sonda, pero **ninguno de los cuatro controles de terreno logra el cruce**; además la ablación pierde integridad y una seed activa no alcanza el tamaño de componente. No modificar parámetros de H41 ni afirmar función de barrera. Artefacto 14917573997 conserva los estados, vence 24-12-2026.

Se abre [H42 prerregistrada](H42_PROTOCOLO_PROTECCION_DIRECCIONAL.md) (`912b024973a6ab7a6fa204961a9a71784f1895e8`) sobre esos estados, no nuevas simulaciones: raycast nativo de exposición direccional y comparación con MCMC condicionado. [Código](experiments/probe_h42_directional_cover.py) `5116d4dd49cdee126cf517ad8d9d9af3d7646dec`, [workflow](../.github/workflows/world-h42-directional-cover.yml) `2af4278bc37ee5951a40f22406b7df338f06c43e`. Sin dictamen todavía; la protección geométrica no implica transferencia térmica. Después de H42 corresponde **auditoría global de valor y viabilidad del prototipo mínimo**, no H43 de granular por inercia. E7 ABIERTA, E8 no iniciada; E0–6 cierres provisionales intactos. No modificar main ni NeuroLab.
