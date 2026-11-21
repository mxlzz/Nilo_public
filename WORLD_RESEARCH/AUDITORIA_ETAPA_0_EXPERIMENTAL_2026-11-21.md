# Auditoría de cierre de la unidad experimental E0 · 2026-11-21

**Alcance:** serie de ensayos H1, H2, H4, H5 y H6 definidos antes de cada script en `ETAPA_0_PROTOCOLO_LANDLAB_SHANHAI.md`. Esta es una auditoría del avance dentro de etapa 0, **no una aprobación de arquitectura final**.

## Objetivos y evidencia

- [x] Comparar alternativas existentes por código y ejecución, sin desarrollar motor nuevo.
- [x] Testar con control negativo el aporte de escorrentía y la erosión de Landlab: ejecución https://github.com/mxlzz/Nilo_public/actions/runs/44947975784 .
- [x] Ejecutar suite original + probe Shanhai con y sin fuentes; diferencia en agua, humedad y biomasa, topografía inmóvil y alias de snapshots: misma ejecución.
- [x] Evaluar Landlab `Space`, `SoilMoisture` y `Vegetation` como vía monomotor (suelo, sedimento y respuesta de crecimiento): https://github.com/mxlzz/Nilo_public/actions/runs/44948299834 .
- [x] Probar generación inicial WorldEngine y modificación por Landlab en entornos independientes, exportando y reimportando un `NPZ`: https://github.com/mxlzz/Nilo_public/actions/runs/44949003747 .
- [x] Verificar existencia de **dos artifacts** del workflow final: `worldengine-height` (fuente) y `landlab-evolved-height` (resultado).
- [x] Cuantificar pérdida de detalle al discretizar alturas de Landlab a cinco niveles como Shanhai: ~99.5% de nodos con erosión invisible a esa escala experimental.
- [x] Documentar los errores de infraestructura: Landlab actual requiere Python compatible con sintaxis PEP695 de `requireit`; primer intento de ablación Shanhai cambió parámetro pero no anuló fuentes locales con `spring.output`; workflow de bridge con `: ` no escapado en comando de pip resultó inválido. Corregidos en commits posteriores y comprobados por CI.
- [x] Registrar ADR-0002 en `DECISIONES/ADR-0002_LANDLAB_PRIMERO.md` como **decisión experimental reversible**.

## Comprobaciones negativas y límites

1. **No está demostrada** conservación de masa sedimentaria total en el sistema abierto ni que los sedimentos se hayan depositado efectivamente en alguna celda durante el smoke SPACE. Detectamos transporte y cambios de suelo con controles.
2. **No está demostrado** un circuito completo suelo-vegetación-erosión ni qué modelo físico se usará para la influencia de cobertura vegetal sobre erosividad. Evitar inventar coeficientes.
3. **No está calibrado** el generador WorldEngine con la escala de Landlab. Se usó explícitamente una proyección experimental 0–50 metros sobre malla 100 m (centros de celdas interpretados como nodos), válida para comprobar transferencia técnica, **no** como acoplamiento geométrico/temporal físico.
4. Repetición determinista y guardado de elevación **no prueban persistencia integral** de todas las variables de los solvers.
5. No hay evidencia de evolución abierta de estructuras no diseñadas; la etapa específica de autoorganización sigue por iniciar.
6. Sandspiel/WorldEngine y Shanhai fueron evaluados, pero no todas las 42 alternativas del corpus se ejecutaron; selección de experimentos priorizó pertinencia.
7. La conexión GitHub actual permite trabajar en rama independiente, pero **no creó un repositorio nuevo**. Sigue pendiente trasladar documentación y experimentos a repositorio dedicado al mundo; no se hicieron cambios a `main` ni se desarrolló NeuroLab.

## Dictamen

**Unidad E0 actual: ACEPTADA con salvedades.** Las pruebas ejecutadas justifican priorizar un próximo experimento de acoplamiento ambiental **dentro de Landlab** y utilizar WorldEngine solo como posible generador de partida, con Shanhai como referencia ecológica.

**Etapa 0 global: ABIERTA.** Los tests positivos no cierran la selección de arquitectura. La decisión de implantar un motor definitivo queda expresamente bloqueada hasta:
- Ensayo de sedimentos con balance y deposición bajo fronteras especificadas.
- Validación de realimentación entre humedad, biomasa y procesos del terreno con fuentes/modelos justificados.
- Contratos de unidad, malla y paso temporal.
- Persistencia completa y rendimiento a resolución del territorio objetivo.

## Próxima unidad planificada

Antes de programar feedback propio: revisar ejemplos y bibliografía de acoplamiento existentes dentro del ecosistema Landlab, particularmente `Space` y componentes ecohidrológicos; formular experimento conjunto con *ablación de cobertura vegetal*, conservación y tiempo. Registrar diseño y métricas antes del próximo cambio.

**Regla de continuidad:** cualquier agente debe comenzar por ADR-0002, protocolo E0 y este dictamen. No reactivar `matter_v0.py`, no portar Shanhai por inercia y no añadir NeuroLab a este repo experimental.

## Comprobación adicional de material nativo de Landlab

Se inspeccionaron los tutoriales oficiales de ecohidrología de su repositorio:
- https://github.com/landlab/landlab/tree/master/docs/source/tutorials/ecohydrology/cellular_automaton_vegetation_DEM
- https://github.com/landlab/landlab/tree/master/docs/source/tutorials/ecohydrology/cellular_automaton_vegetation_flat_surface
- https://github.com/landlab/landlab/tree/master/docs/source/tutorials/landscape_evolution/space

Los notebooks de ecohidrología documentan combinaciones de radiación, humedad de suelo, vegetación y VegCA. **Sin embargo, importan módulos auxiliares `Ecohyd_functions_DEM` / `Ecohyd_functions_flat` que no están presentes en los directorios examinados**; no se los considera ejecutables autónomamente ni como prueba de ciclo completo. Se deberá ubicar el origen de esos auxiliares o elegir ejemplos completos antes de reutilizar.

El tutorial `SPACE_user_guide_and_examples.ipynb` describe `FlowAccumulator`+ `DepressionFinderAndRouter`+ `Space`, con parámetros de referencia documentados y registro de sedimento. Es una base reproducible más adecuada que inventar funciones de deposición. **No se ejecutó todavía** este notebook en nuestra CI; se propone como prueba siguiente.

## Addendum H7–H10 (21-11-2026)

- H7/H7b `SpaceLargeScaleEroder`: presupuesto sedimentario de cuenca con salida validado y acreción neta en 50 nodos de zona receptora. https://github.com/mxlzz/Nilo_public/actions/runs/44951204189 . No calibrado.
- H8a `SoilMoisture+Vegetation+LinearDiffuser`: respuesta causal de lluvia/cobertura sobre relieve con coeficiente publicado; primer ensayo falló por dosel saturado, luego se corrigió estado inicial sin relajar controles. https://github.com/mxlzz/Nilo_public/actions/runs/44951510991 .
- H8b `DepthDependentDiffuser`: la respuesta actúa sobre **suelo móvil**, conservando 21.6m³ con bordes cerrados. https://github.com/mxlzz/Nilo_public/actions/runs/44951675896 .
- H9 90 días `SoilMoisture+Vegetation+DepthDependentDiffuser`: secuencia multi-evento reproducible, volumen móvil conservado, pero retroalimentación **unidireccional**. https://github.com/mxlzz/Nilo_public/actions/runs/44951992403 .
- H10a inspección y ensayo: `Radiation.update()` **no recalcula pendiente/orientación**, se requiere re-instanciar o actualizar la geometría explícitamente. https://github.com/mxlzz/Nilo_public/actions/runs/44952322090 .
- H10b lazo con 90 días `topografía→radiación→PET→humedad/vegetación→suelo→topografía` pasó tras corregir setter temporal. Prueba factorial con intervención geológica **exógena** +12m (día46) y ablación del vínculo radiativo. PET máxima diferencia 2.7046mm/día cuando vínculo activo, **0** bajo control; humedad y biomasa respondieron. Masa de suelo 2160m³ conservada; diferencia endógena PET de solo 4.42e-7mm/día sin perturbación externa. https://github.com/mxlzz/Nilo_public/actions/runs/44952698259 .
- Todos los protocolos H7/H7b/H8/H9/H10 fueron versionados antes de los ensayos correspondientes; los errores de instrumental permanecen en logs y están documentados.
- La **etapa 0 sigue ABIERTA**: un bucle de radiación no equivale a hidrología de cauce, dinámica de cuenca con presupuesto acuoso y sólidos, calibración, persistencia integral, escala o emergencia abierta. Prohibido fusionar `SPACE` y `DepthDependentDiffuser` por conveniencia sin plan de doble conteo; prohibido adoptar un motor definitivo sin gate y decisión fundada.

**Próxima comparación autorizada:** caracterizar `OverlandFlow` vs `FlowAccumulator` para estado/flujo/conservación de agua y acoplamiento con suelo. Primero diseñar pruebas con unidad/tiempo/frontera y ablation; luego ejecutar sin desarrollar física propia. También realizar pruebas de escalabilidad, checkpoint/replay de todo el estado y referencia funcional de Ecosystem Explorer (solo caja negra y respetando derechos).

## Addendum H11a — modelo hídrico de almacenamiento (21-11-2026)
- Protocolo antes de prueba: `ETAPA_0_7_PROTOCOLO_H11_AGUA.md`.
- `OverlandFlow` native Landlab, 12×12, cerrado, lluvia 2e-5m/s por 60s. Volumen inicial 0.001m³, lluvia 0.12m³, volumen final 0.121m³, residual de redondeo nulo. Rutas cambiaron tras alterar relieve +0.2m; volumen global sin cambios. Control sin lluvia conserva película inicial. Replay exacto.
- CI **SUCCESS**: https://github.com/mxlzz/Nilo_public/actions/runs/44953015600
- Informe reproducible: `ETAPA_0_7_RESULTADOS_H11A.md`.
- **Dictamen:** H11a apta como evidencia de almacenamiento hídrico conservativo sin sumideros; no acoplada todavía a `SoilMoisture`, flujo subsuperficial, borde abierto ni `SPACE`. El usuario pidió un mundo físico autónomo, no un software donde una prueba aislada de agua se presente como completa. Mantener los límites.
- **Gate E0/H11b**: antes de integrar modelos, verificar si ya existen acopladores ecohidrológicos o adaptadores BMI con entradas/salidas y presupuesto compartido de agua; luego comparar costo e implementar solo un conector mínimo con pruebas. El agua de lluvia no puede entrar por duplicado.
- **Estado global:** etapa 0 ABIERTA, decisiones ADR-0001/2 reversibles, ningún motor definitivo adoptado; no se cambió `main` ni se introdujo NeuroLab.
