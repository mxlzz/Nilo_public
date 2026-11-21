# ADR-0002 — Priorizar Landlab como candidato experimental de núcleo ambiental

**Fecha:** 2026-11-21  
**Estado:** DECISIÓN DE EXPERIMENTO, REVERSIBLE. NO constituye selección definitiva ni aprobación de producción.
**Alcance:** mundo físico autónomo separado de NeuroLab; generación inicial, escorrentía, erosión, suelo, vegetación y observación.

## Pregunta

¿Conviene intentar integrar Landlab con un segundo motor ecológico, extender un simulador de arena, o comprobar primero si los componentes nativos de Landlab son suficientes para un mundo ambiental autoconsistente?

## Evidencias nuevas

- Revisión estructurada previa de 42 antecedentes: `REVISION_COMPARATIVA_42_ALTERNATIVAS_2026-11-21.md`.
- Landlab, `FlowAccumulator` + `StreamPowerEroder`: escorrentía al activar fuente, erosión mensurable, control nulo, checkpoint/replay reproducible. CI https://github.com/mxlzz/Nilo_public/actions/runs/44947975784
- Landlab, `Space`: sedimento en movimiento, variación de espesor de suelo y control de erosión nula; Landlab `SoilMoisture` + `Vegetation`: lluvia modifica saturación, estrés hídrico y biomasa en estación de crecimiento. CI https://github.com/mxlzz/Nilo_public/actions/runs/44948299834
- Shanhai, suite upstream y controles causales: agua modifica humedad/vegetación y resultados son reproducibles; topografía categórica 0–4 **no cambia** por proceso geológico; `getSnapshot` expone referencias a arrays internos, no un registro inmutable. CI https://github.com/mxlzz/Nilo_public/actions/runs/44947975784
- WorldEngine->Landlab, transferencia de archivo entre intérpretes aislados: generación con semilla, importación y erosión reproducibles. CI https://github.com/mxlzz/Nilo_public/actions/runs/44948883527
- En el escenario experimental, reducir el relieve continuo evolucionado a las cinco alturas de Shanhai ocultó **99.5% de los nodos que sí perdieron altura**, y produjo ~1.725 unidades de error RMS de reconstrucción.

## Alternativas contrastadas

**A. Landlab como núcleo experimental, WorldEngine como inicializador, Shanhai como benchmark externo** — preferida para la siguiente prueba; reutiliza componentes científicos ya interoperables en un mismo framework de grillas. Mantiene módulos opcionales. Las condiciones iniciales importadas precisan conversión de unidades/celdas y comprobaciones. No se presume que todos los procesos de ecosistema ya estén acoplados.

**B. Landlab + Shanhai como dos motores simultáneos** — no descartada para siempre, pero sin ventaja demostrada: diferentes lenguajes, grillas, pasos temporales y clases de alturas; acoplamiento exigiría rediseñar partes de Shanhai y conservar variables adicionales. Hay evidencia de pérdida de topografía.

**C. Sandspiel/The Powder Toy como sustrato universal** — motores de material local con grandes capacidades, pero no la misma representación geomorfológica con variables físicas continuas, suelos y campos ecohidrológicos. No adecuado como decisión principal con pruebas disponibles; puede recuperarse para efectos locales si se demuestra un caso de uso.

**D. Motor propio desde cero** — no justificado: ya existen Landlab y otros modelos para los procesos centrales y requeriría recrear y validar física. Prototipo `matter_v0.py` se conserva solo como spike histórico.

**E. Mundo procedimental estático desde WorldEngine/Infinigen** — incumple requisito de evolución causal y autónoma.

## Decisión

**Autorizar la siguiente fase de la ETAPA 0 como laboratorio Landlab-first, NO como motor de producción ni selección de arquitectura final.** Reutilizar procesos de fuentes verificadas. Mantener WorldEngine separado por datos y Shanhai como control funcional, **sin** integración mutua de motores hasta que se pruebe necesidad y contrato de estado.

Ninguna parte autoriza implementar NeuroLab, cerebros/LLM, ni decidir GUI/perspectiva. No cambia objetivos confirmados por el usuario.

## Experimentos bloqueantes antes de cerrar etapa 0

1. **Acoplamiento funcional dentro de Landlab**: buscar y probar ejemplos existentes que unan hidrología, humedad/vegetación y sedimentación con unidades, tiempo y transferencias explícitas. No inventar coeficientes de erosividad por cobertura vegetal sin fuente y pruebas.
2. **Balance físico**: comprobar sedimento erosionado/depositado/salidas e ingreso de agua en un dominio/bordes definidos. Conocer efecto de fronteras; no exigir conservación global en un sistema abierto sin medir flujos.
3. **Condiciones iniciales**: definir conversión de WorldEngine a grilla Landlab, unidades y fronteras con significado, no solo normalización visual arbitraria. El resultado actual es un smoke técnico, no planeta calibrado.
4. **Persistencia completa**: guardar y reanudar TODOS los estados de los solvers, no solo el relieve; medir dependencia de RNG y parámetros.
5. **Rendimiento y escalas**: ejecutar mallas y horizontes crecientes para demostrar viabilidad con recursos reales. Comparar enfoque monomotor con alternativa de integración usando esfuerzo documentado.
6. **Emergencia**: mantener el objetivo como línea experimental futura con métricas de patrones, no asumir que la vegetación actual genera estructuras evolutivas abiertas.

## Cómo revisar esta decisión

Si fallan componentes Landlab, el performance es inaceptable, los modelos resultan incompatibles o aparece solución abierta mejor, registrar evidencia y reevaluar A/B/C sin defender la decisión por inercia. Mantener en control de versiones experimentos fallidos, límites y datos.

**Aprobación de cierre:** parcial/reversible por evidencia experimental. **Etapa 0:** ABIERTA. **Etapa 1:** NO INICIADA. No confundir la preferencia técnica con aprobación de la arquitectura definitiva.
