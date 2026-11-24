# E09h.4 — preregistro del enlace receptor → locus CHEM → SVRule

**Fecha:** 2026-11-21. **Estado:** propuesta experimental delimitada, antes de implementar el adaptador. **Línea H, sin integrar Nilo.**

## Pregunta y dependencia

El camino de C1 reconstruido en E09h.1–h.3 llega hasta un **byte que debe escribirse en un locus**. E09h.4 determina si los loci cerebrales codificados en `dad1.gen` alimentan las cuatro entradas químicas del lóbulo que usa la SVRule.

**Datos previos no modificables:** seis genes receptores originales verificados en `resultados/e09h3_receptores_genoma_original.json`, genoma SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`, EXE SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`.

## Hipótesis y niveles de evidencia

- **H4-A (documentación independiente):** tabla de loci receptor de *Creatures Development Network*, referencia de `LCUS`, declara en órgano 0 Brain: 13=`LOCUS_CHEM0`, 14=CHEM1, 15=CHEM2, 16=CHEM3: https://lisdude.com/cdn/76.html, sección «Reference - Values for LCUS» (loci de receptor, NO confundir con los de emisor).
- **H4-B (documentación de cerebro):** guía C1 de Home Sweet Albia declara SVRule opcodes 5,6,7,8=`CHEM0..3` y la copia de los cuatro quimiorreceptores del lóbulo a la State Variable Table al comenzar su procesamiento: https://zenzoa.com/creatures/c1-brains.html.
- **H4-C (evidencia binaria pendiente):** la rutina del EXE de construcción/enlace del locus debe resolver realmente el triplete `(organ=0,lobe,locus)` hacia `brain[lobe].chem[locus-13]`; el brain tick/SVTable debe leer ese mismo campo. **Las guías, el GEN y un test de adaptador no demuestran H4-C.**
- **H4-D (cronología pendiente):** relación exacta de lectura, escritura y snapshots bajo todas las rutas de scheduler C1.

## Ensayo controlado que sí puede ejecutarse sin EXE

Implementar **adaptador de prueba condicionado por H4-A/H4-B**, sin agregar arquitectura al cerebro:

1. Entrada: receptores `Receptor` de E09h.3, pool fijo de 256 bytes, lóbulo objetivo y estado CHEM inicial de cuatro bytes.
2. Procesar exclusivamente receptores `organ=0`, lóbulo objetivo y `locus=13..16`; mapear índice `locus-13`. Conservar intactas las otras ranuras y el pool; química 0 no escribe.
3. Si dos receptores quieren escribir el mismo `(lobe,locus)`, **fallar explícitamente**, ya que no se verificó la precedencia en C1. No resolver mediante orden arbitrario.
4. Caso Decision6 con concentraciones 49=12,50=12,53=12,70=0, partiendo de cuatro ceros: `(11,11,5,16)`.
5. Caso Concept8 con concentraciones 51=0,52=5: `(0,0,0,0)` partiendo de ceros (el segundo cero es 4−4). En una SVRule `CHEM0` es el opcode 5, no el locus 5.
6. Controles negativos: aislamiento de lóbulo (mismo locus numérico no interfiere entre lobos); preservar canales sin receptor desde un estado inicial no nulo; rechazar duplicados y valores incorrectos; cambio de concentración altera solo canal con gen receptor; reproducibilidad.
7. Probar la lectura mediante `C1SVTable` y `evaluate`, **sin** afirmar que la tabla representa el snapshot real del ejecutable.

## Puertas de aceptación diferenciadas

- **G-H4-ADAPTER:** test local y CI de controles y seis fixtures del CD, con artefacto reproducible. Aceptarlo significa **compatibilidad lógica con H4-A/B**, no emulación C1.
- **G-H4-X86:** demostrar con bytes e instrucciones concretas del EXE original, hash verificado, asignación de puntero receptor→locus y copia al buffer SVRule. **Sin esa inspección, E09h.4 queda PARCIAL** aunque G-H4-ADAPTER pase.
- **G00-H / G05 / G09:** siguen abiertas aun si G-H4-X86 llegara a validarse. No instalar/ejecutar el juego ni publicar los binarios.

## Orden de trabajo fijado

Preregistro → adaptador + tests de compatibilidad → resultado con errores → actualización de estado → inspección estática C1 cuando los bytes sean accesibles → decisión de fidelidad. **Prohibido usar el resultado como autorización para sumar neuronas, tunear g.10 o tocar main/Nilo 0.7.**
