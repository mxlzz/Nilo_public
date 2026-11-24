# E09.02i-I3b.3 — viabilidad de migración C1 tipo 1 en seis unidades

**Fecha: 2026-11-21.** Estado: puerta estructural **VALIDADA en el modelo reducido**; **NO valida aprendizaje**. El código de migración existente no se modificó.

## Evidencia

- [Preregistro previo](E09_02I_I3B3_MIGRACION_VIABILIDAD_PRE_REGISTRO.md) · [auditor](../../experiments/neurolab/e09_i3b3_migration_feasibility.py) · [tests](../../experiments/neurolab/tests/test_e09_i3b3_migration_feasibility.py) · [GitHub Actions #44957812410](https://github.com/mxlzz/Nilo_public/actions/runs/44957812410): **success**, cuatro pruebas específicas.
- Artefacto **neurolab-i3b3-migration-feasibility**, ID **14728317633**, incluye resultado completo, retención hasta 2027-02-19.
- Algoritmo reutilizado sin cambios: [c1_migration.py](../../experiments/neurolab/c1_migration.py), específicamente **decision_migrate** con migration_type=1 de genes Decision.

## Hallazgo

C1ContextBrain ofrece dos fuentes Concept C0/C1. Para cada Decision D0/D1 y clase excitatoria/inhibitoria, existen exactamente dos dendritas, una asignada a cada fuente. El algoritmo tipo1 rechaza una fuente si su puntero ya aparece en otra dendrita de esa clase, incluso si la fortaleza de ésta llegó a cero.

- **8/8** casos (cuatro combinaciones Decision×clase, dos elecciones de candidato) dieron **duplicate_source**, sin migración. El estado y cursor son reproducibles.
- **4/4** controles con una tercera fuente **solamente sintética y libre** migraron correctamente con la misma implementación, lo que demuestra que la prueba no bloquea toda migración.
- El control receptor inactivo devolvió **inactive_recipient**, distinguido de saturación de fuentes.
- Además, C1SynapseState solo contiene estado dendrítico y fortaleza, sin campo de identidad dinámica de origen, mientras C1ContextBrain define la procedencia por índice. Una llamada suelta a decision_migrate **no** reconecta la microred actual.

## Interpretación y decisión

**Verificado:** el motor migratorio existente no tiene un origen alternativo disponible en esta topología de 6 unidades/8 contactos. No se agregaron neuronas ni se modificaron conexiones para producir un éxito artificial.

**No verificado:** que migrar sea imposible o ineficaz en el Norn original; éste dispone de un conjunto de posibles fuentes mucho mayor. Tampoco se ha probado que una adaptación migratoria mejore aprendizaje o retención.

Antes de implementar cambios, comparar alternativas de menor costo en [I3c — alternativas mínimas](E09_02I_I3C_ALTERNATIVAS_MINIMAS.md). **G05/G09/G00-H siguen abiertas**, I3 metabólico continúa como resultado negativo, PR #103 permanece draft y Nilo0.7/main intactos.
