# Etapa 0 — Evaluación experimental de reutilización (informe parcial)

**Fecha:** 2026-11-21  
**Estado:** etapa 0 ABIERTA, dos candidatos inspeccionados y pruebas iniciales realizadas; **NO hay motor adoptado**.
**Alcance:** únicamente mundo/ambiente físico; NeuroLab y cognición excluidos.

## Alineación y gates
- Objetivo confirmado: mundo pequeño, autónomo, persistente, con generación inicial y evolución por reglas compartidas, abierto a formas de organización no diseñadas.
- Etapa: 0 — establecer baseline, investigar soluciones, ejecutar pruebas de encaje antes de desarrollar leyes propias.
- Hipótesis H0: algún componente existente puede reutilizarse para generación inicial y/o procesos materiales sin escribir desde cero todo un motor.
- Alternativa: adaptar componentes independientes; escribir solo el mínimo no cubierto tras demostrar brecha.
- Estado gate: **abierto**. Falta comparación ejecutada del segundo motor material (The Powder Toy u otra alternativa de requisitos equivalentes); no se ha comprobado integración de generación + dinámica ni persistencia prolongada.

## Fuentes principales inspeccionadas
- https://github.com/MaxBittker/sandspiel : `crate/src/lib.rs`, `crate/src/species.rs`, Cargo.toml, tests/web.rs.
- https://github.com/MaxBittker/sandspiel-studio : src/simulation/SandApi.js, updateSchemes.js, package.json.
- https://github.com/The-Powder-Toy/The-Powder-Toy : src/simulation/Simulation.h, meson.build, meson_options.txt, README.md.
- https://github.com/Mindwerks/worldengine : `worldengine/plates.py`, `worldengine/generation.py`, pyproject.toml, world model, tests.
- Referencias alternativas: https://github.com/weigert/SoilMachine y https://github.com/Yihao-Shi/GeoTaichi .
- Detalles de licencias y riesgos en ADR-0001. Las características en el código no son evidencia de ejecución.

## Resultados medidos: WorldEngine

Ejecución real en GitHub Actions: https://github.com/mxlzz/Nilo_public/actions/runs/44943949457
Job `worldengine`: **SUCCESS**.

Prueba con mundo 32x16, semilla del generador 7321 y estado inicial global NumPy 1234:
- Terreno producido, elevación finita con forma 16x32.
- Dos generaciones con la misma semilla del generador **y** reseteando el RNG global NumPy produjeron el mismo hash de elevación.
- Sin resetear ese RNG global, la tercera generación **NO** produjo el mismo hash de elevación.
- Protobuf serializó y restauró la elevación sin diferencia binaria en el ensayo.
- Hash SHA-256 de elevación del primer mundo: `495e97c24477e68e0cffcab8f485481630d4425d31a01442c7ad1cbb0daa170d`.
- Instantánea serializada: 54726 bytes.

**Interpretación:** el generador es reutilizable como punto de partida, pero el uso del RNG global en `plates.py` exige encapsulación/normalización para reproducibilidad independiente. Esto no prueba que provea una historia geológica real ni transformación posterior.

## Resultados medidos: Sandspiel

Primera prueba real: https://github.com/mxlzz/Nilo_public/actions/runs/44943949457
Job `sandspiel`: código Rust compiló; 2/3 pruebas iniciales pasaron.
- Repetición determinista de dos mundos con el mismo estado durante 20 ticks: **PASS**.
- Barrera que no deja pasar arena hacia abajo: **PASS**.
- Arena cayendo: **FAIL**. No atribuir aún a un defecto físico general.

Prueba diagnóstica: https://github.com/mxlzz/Nilo_public/actions/runs/44944059013
- Con el campo de viento inicial del constructor original, la arena pasó de (12,4) a (11,3), (10,2), (9,1) y avanzó hacia x=0, sin descender.
- La inspección del código explica la condición: `Universe::new` inicializa campos de viento en cero, pero `blow_wind` interpreta desplazamientos como `dx-126` y `dy-126`, por lo que cero no significa ausencia de viento.
- Esto indica una **dependencia externa de inicialización** al ejecutar el núcleo aislado. No demostraría por sí solo que el juego completo tiene ese defecto.
- Se añadió test con viento neutral (126,126) y control de inicialización sin corregir, en un checkout temporal de upstream. **Resultado pendiente de registrar hasta que termine el workflow**.

Limitaciones de arquitectura verificadas por lectura:
- Los tipos de materia son variantes enumeradas `Species` y su comportamiento depende de funciones `update_*` concretas.
- El RNG del constructor usa una semilla fija.
- La API expuesta no proporciona directamente un sistema general de materiales por propiedades ni guardado arbitrario versionado.
- El ensayo usa instrumentación dentro de una copia temporal del módulo privado, no una API pública sin modificación.

## Powder Toy — inspección, NO prueba ejecutada
- Código: C++ con `Simulation`, estado y partículas; posee `Save`, `Load`, `CreateSnapshot`, `Restore`, `UpdateParticles` y API Lua.
- La estructura sugiere una vía de integración, pero no establece automáticamente compatibilidad con ejecución headless ni mutación de materiales por propiedades.
- GPL-3.0: requisito de revisión de compatibilidad/licencia antes de copiar o enlazar código.
- **Pendiente:** preparar un ensayo pequeño de estado/materiales y progresión sin GUI; registrar dependencias reales y esfuerzo antes de elegir.

## Sandspiel Studio — inspección, NO prueba ejecutada
- Reglas programables por bloques, pero el núcleo actual importa estado global y utilidades, con dependencias de cliente.
- Usa `Math.random()` y ruido inicializado con aleatoriedad global; determinismo por semilla no demostrado.
- Advertencia en actualización: varios esquemas no funcionan correctamente con tamaños variables; requiere tests.
- No asumir que un editor de reglas es un motor headless.

## Riesgos y coste de oportunidad
- No construir desde cero una simulación de caída o erosión antes de demostrar por qué las existentes son inadecuadas.
- No forzar a que un solo motor represente tectónica, clima, arena, edificios y organismos: desajuste de escala y acoplamiento.
- Evitar adopción de simuladores donde los tipos son un catálogo cerrado si la finalidad es evolución abierta de las **reglas**. Un prototipo puede usar catálogo para ensayos sin convertirlo en decisión de diseño.
- Diferenciar inventario de materia con conservación exacta de autómatas con transformaciones y fuentes/sumideros (fire, gas, cloner); test de masa por especie no siempre tiene sentido en el segundo.
- El avance de CI no constituye una auditoría de aptitud arquitectónica.

## Próxima puerta
1. Confirmar resultado de Sandspiel con viento neutral y registrar si se necesita modificar internals.
2. Probar The Powder Toy u otra solución de comportamiento material como segundo candidato, en un caso de alcance equivalente.
3. Evaluar módulo WorldEngine como generador bajo encapsulamiento completo del RNG.
4. Elaborar ADR-0002 con recomendación explícita de usar / adaptar / combinar / desarrollar, apoyada en pruebas y costo de integración. **No avanzar a etapa 1 antes del dictamen.**
