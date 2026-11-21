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
