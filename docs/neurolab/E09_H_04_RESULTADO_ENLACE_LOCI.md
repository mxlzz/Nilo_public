# E09h.4 — resultado parcial: tabla de loci CHEM y adaptador condicionado

**Fecha:** 2026-11-21. **Estado científico:** **PARCIAL**. El adaptador demuestra consistencia con dos referencias C1 independientes y con los genes originales ya extraídos, **NO** demuestra el enlace de punteros del ejecutable ni su scheduler.

## Evidencia separada y trazable

1. **Genoma original (dato anterior E09h.3):** seis receptores cerebrales (88,89,126–129), ya presentes en [fixture derivado del CD](resultados/e09h3_receptores_genoma_original.json). GEN SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. En esta intervención no se releen los bytes originales.
2. **Tabla de receptores C1 independiente:** [Creatures Development Network, `LCUS`, receptor type 0, organ 0 Brain](https://lisdude.com/cdn/76.html): locus **13/14/15/16** se denomina `LOCUS_CHEM0/1/2/3` respectivamente (también enumera CHEM4 y CHEM5 en 17/18, fuera de las cuatro entradas del intérprete ensayado).
3. **Tabla de SVRule y transferencia lógica independiente:** [Home Sweet Albia, C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html): opcodes **5/6/7/8** leen `CHEM0/1/2/3`; al actualizar lóbulos de salida, la tabla de estado incluye los valores de las cuatro entradas químicas del lóbulo.
4. **Arimética C1 de receptor (E09h.3, ya verificada):** `receptor_value` calcula byte desde concentración. El [adaptador H4](../../experiments/neurolab/e09_historical_locus.py) condiciona el destino del byte a la tabla anterior; [tests H4](../../experiments/neurolab/tests/test_e09_historical_locus.py) usan el fixture original archivado, sin binarios propietarios.

## Resultado del caso reproducible

Usando el pool de ejemplo de E09h.3 `49=12,50=12,52=5,53=12` y estado químico inicial 0, el adaptador entrega:
- **Decision (lóbulo 6):** `CHEM0..3=(11,11,5,16)`, correspondientes a Reward49, Punishment50, DecASH1=53 y DecASH2=70.
- **Concept (lóbulo 8):** `CHEM0..3=(0,0,0,0)` con Reinforcement51=0 y ConASH52=5; el receptor invertido de ConASH retorna 0 (errata E09h.3 preservada).
- En un ensayo distinto con química51=12 y 52=0, Concept produce CHEM0=11, CHEM1=4. Mismos números de locus en diferentes lóbulos permanecen independientes.
- La lectura con `C1SVTable/evaluate` prueba que las variables del adaptador llegan a los operandos SVRule esperados en el **modelo condicionado**, no que C1 real tenga ese estado en un instante particular.
- Los controles rechazan receptores duplicados para el mismo lóbulo+CHEM (precedencia real no verificada), tipos inválidos y pool fuera de rango; no mutan concentraciones ni amplían la microred.

**Evidencia de ejecución:** [CI #44947076331](https://github.com/mxlzz/Nilo_public/actions/runs/44947076331) **success integral** para commit de tests `2ef85398502ff67b7a40f7106f6277394b989625`: **339 tests ejecutados, 2 expectedFailure históricos**; los experimentos de regresión posteriores también completaron sin errores. El CI no contiene binarios originales, y por tanto no cierra G-H4-X86.

## Limitaciones y siguiente subtarea

**G-H4-ADAPTER:** pruebas de compatibilidad con la documentación completadas. **G-H4-X86: ABIERTA** porque no se pudo acceder a los bytes del ejecutable PE32 desde este chat; los archivos binarios están listados en la Biblioteca pero la materialización de bytes devolvió «This Project file does not have an authorized raw-byte materialization path» para dos copias. No confundir visibilidad de metadatos con acceso a bytes. No se inspeccionaron nuevas instrucciones x86 en esta intervención.

Para cerrar **E09h.4** hace falta, sobre EXE SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`:
1. Decodificar en `0x4032E0..0x4034B9` o su subrutina correspondiente la carga del receptor y el cálculo del puntero `(organ,lobe,locus)`.
2. Verificar offsets estructurales concretos para loci 13–16, evitando asumir que equivalen al índice del opcode 5–8.
3. Rastrear desde la escritura de `0x42200F` hasta la lectura/instantánea de CHEM en `0x403BB0/0x403FC2`, indicando rutas condicionales.
4. Comparar las seis entradas y controles de duplicación/cambios de fase contra oráculos independientes; corregir cualquier divergencia preservando esta hipótesis inicial.

**No cerrar G00-H/G05/G09, no integrar el cerebro con Nilo, no fusionar PR.** No ejecutar ni instalar Creatures ni redistribuir GEN/EXE. Siguiente paso solo inspección estática h.4 pendiente.
