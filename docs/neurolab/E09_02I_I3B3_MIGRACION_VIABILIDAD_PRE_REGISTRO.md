# E09.02i-I3b.3 — preregistro de viabilidad estructural de migración ya implementada

**21/11/2026. Antes de escribir tests nuevos**. Depende del hallazgo de [I3b.2a](E09_02I_I3B2A_RESULTADO_FORTALEZA.md) y del algoritmo existente [c1_migration.py](../../experiments/neurolab/c1_migration.py). **Objetivo:** evitar implementar un mecanismo que ya existe o modificar el cerebro innecesariamente.

## Pregunta falsable

En la microred actual C1ContextBrain hay **dos fuentes Concept C0/C1** y **dos dendritas por clase excitatoria/inhibitoria por cada Decision**; cada clase ocupa ya ambas fuentes. El gen Decision original especifica **migration_type=1**. El algoritmo histórico derivado [decision_migrate](../../experiments/neurolab/c1_migration.py) rechaza fuentes que ya figuran en la misma clase, aunque la dendrita tenga strength=0. Por tanto **hipótesis H3-A:** con ambos punteros ocupados, una conexión desconectada **no puede** migrar dentro de esta topología usando el algoritmo tipo1, sin importar qué fuente de las dos seleccione rand().

**Control H3-B:** añadir **solo en fixture aislado** una tercera SourceNeuron no ocupada debe permitir al mismo algoritmo conectar si el rand()%3 selecciona esa fuente y el receptor está activo. Esto prueba que el test no invalida artificialmente toda migración. **NO añadir la fuente al cerebro real del laboratorio**.

## Oráculos y controles

- Reutilizar SIN MODIFICAR las clases SourceNeuron, Dendrite, MigrationState, MigrationConfig, RandStream y decision_migrate. El test usa punteros ficticios 0x1000/0x2000/0x3000 y flujo de rand explícito para reproducibilidad. Rangos de inicialización del control (LTW0..0, strength1..1) son **sintéticos**, sin atribuirse al GEN original; no afectan la puerta de duplicado.
- Fijar una clase con dos dendritas, una de fortaleza0 aún enlazada al puntero original y otra de fortaleza2; fuentes activas exactamente dos. Probar rand candidato0 y candidato1: **ambos deben devolver reason=duplicate_source, migrated=False, topología y contadores invariantes**.
- Probar recipient_output0: se bloquea antes del azar con reason=inactive_recipient; no confundir con imposibilidad por falta de fuentes.
- Control positivo: tres fuentes, candidato tercero no enlazado y recipient_output>0, rand elige índice2 y provee los dos draws de inicialización: migrated=True, nueva fuente 0x3000, contador loose decrementado. **Solo fixture, no cambiar arquitectura real.**
- Verificar desde C1ContextBrain que la identidad de fuente en cada Decision/clase se calcula por la posición i y que el estado C1SynapseState NO contiene source_pointer ni mapeo dinámico. Contrastar genes Decision migration_type1. El adaptador necesario para integrar migración real no existe; no fingir que basta llamar la función.
- **G-I3b3-STRUCT:** tests en CI con ambos controles y evidencia formal de incompatibilidad en la microtopología actual. Un éxito científico de una configuración sintética con 3 fuentes **no** demuestra mejora de aprendizaje o necesidad de agrandar la red.
- **Hipótesis nula y falsación:** si la función migra efectivamente con dos fuentes ocupadas o la fuente puede editarse dinámicamente en C1ContextBrain sin adaptación, registrar contradicción y suspender propuesta de rediseño.

## Decisión condicionada (NO aprobada ni implementada)

Si H3-A y control H3-B se verifican, evaluar **alternativas de mínimo costo** antes de ampliar red: (a) reducir a una dendrita/clase dejando un origen libre; (b) ampliar el conjunto de conceptos candidatos; (c) mantener la topología pero no afirmar migración C1. Comparar bajo tareas y presupuesto de sinapsis, y considerar que reducir conexiones cambia capacidad. No realizar ninguno de esos cambios de arquitectura sin una prueba diseñada y aprobada por puertas. G05/G09 abiertas, PR#103 sigue draft, Nilo intacto.
