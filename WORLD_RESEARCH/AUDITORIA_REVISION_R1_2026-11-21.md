# Auditoría de calidad de revisión R1.0 — 2026-11-21

## Alcance de la auditoría
Se audita \`REVISION_COMPARATIVA_42_ALTERNATIVAS_2026-11-21.md\`, exclusivamente como **revisión documental**, no como validación empírica de motores o demostración de física/emergencia.

## Checklist
- [x] Problema y alcance explícitos; el desarrollo de cerebro/NeuroLab queda fuera.
- [x] Criterios separados para generación, dinámica, acoplamiento, autoorganización, persistencia, licencia/madurez.
- [x] **42 entradas únicas numeradas**: 8 sistemas ambientales, 11 generadores, 11 módulos de procesos, 8 autoorganización/materiales, 4 interfaces; no declarar a todos motores de mundo.
- [x] Fuentes primarias identificadas mediante enlaces a sitios/repositorios/documentación. Literatura científica separada de claims de README.
- [x] Repositorios principales con licencia y fecha de último push consultadas al 21-11-2026; «licencia no verificada» se conserva explícitamente.
- [x] Ecosystem Explorer incluido y separado de motores con código reutilizable.
- [x] Shanhai: lectura de diseño original descubre H (relieve) **estático**. Su inclusión no es prueba de erosión; análisis corregido.
- [x] WorldEngine y Sandspiel: resultados experimentales históricos citados con CI; no extrapolar a idoneidad integral.
- [x] CSDMS/BMI, PyMT y eWaterCycle incluidos como soluciones previas al problema de interoperabilidad.
- [x] Limitaciones metodológicas y plan de falsación de hipótesis explícitos.
- [x] No se cambió \`main\` ni NeuroLab, no se introdujo código de motor nuevo.

## Limitaciones que permanecen
- No constituye revisión **sistemática PRISMA**: no existe conteo completo de artículos recuperados, duplicados cribados y descartes documentados en bases bibliográficas. Describirla como **revisión exploratoria estructurada**, no paper revisado por pares.
- Licencia y actividad se obtuvieron mayormente de repositorio/metadata, no se verificaron todas las cadenas de licencias transitivas ni restricciones de terceros.
- Solo se inspeccionaron internamente algunos candidatos prioritarios. Los README pueden prometer funciones que no pasen nuestras pruebas.
- La evidencia experimental de Sandspiel/WorldEngine antecede esta revisión y fue acotada: no hay aún pruebas de acoplamiento entre ellos, Landlab o Shanhai.
- La comparación no dispone todavía de tiempos de CPU/memoria ni de estimaciones confiables de costo de integración.
- Los estándares BMI no garantizan que dos solvers sean físicamente compatibles.
- No se puede declarar que «ningún proyecto del mundo logra esto», solo que ninguno del corpus fue **verificado** como solución integral.

## Hallazgo principal de la auditoría
El procedimiento anterior seleccionó primero una representación de materia sin haber definido los dominios ni examinado herramientas de simulación ambiental; también pasó por alto Ecosystem Explorer y sistemas de acoplamiento. La propuesta actual cambia el orden del problema:
1. Requisitos observables de mundo ambiental;
2. Cobertura de soluciones existentes;
3. Benchmarks por función;
4. Elección modular o solución preexistente;
5. Solo entonces implementación mínima de brechas demostradas.

## Dictamen
**Revisión R1.0: APROBADA como base documental para organizar los ensayos de selección, NO apta todavía para aprobar una arquitectura o cerrar etapa 0.** Próximo gate: ejecución de alternativas prioritarias por categorías bajo los escenarios S1–S8.

**Advertencia de auditoría:** un «aprobado documental» no autoriza dar por probadas las capacidades de la lista.
