# E09h.6 — preregistro de reloj y rutas de actualización de C1

**Fecha:** 2026-11-21. **Estado:** preregistrado antes de nueva implementación. Esta tarea sigue la reconstrucción histórica E09h.1–h.5, no altera ni integra Nilo.

## Necesidad

Ya se conocen las rutas locales de receptor, reacciones y emisores, pero **no** si comparten una escala de tiempo global, frecuencia fija y secuencia universal de tick. E09h.1 verificó una ruta regular cerebro→química y una ruta alternativa con orden inverso; no demostró sus disparadores, tasa de llamada ni si la criatura puede actualizarse más de una vez por iteración del mundo. Es indispensable cerrar estos huecos antes de atribuir causalidad temporal a una sinapsis.

## Preguntas fijadas antes de inspección adicional

1. ¿Qué condición lleva a la ruta regular de 0x407540, y cuándo se omite? Reconstruir ramas de entrada/salida con direcciones y semántica **solo si los datos la acreditan**.
2. ¿Qué contexto invoca la ruta alternativa 0x405D20 (química→cerebro) y cómo afecta el contador? No asumir que es parte del tick normal ni que es una duplicación por frame.
3. ¿Qué valor concreto de Norn+0x2C20 recibe el cerebro (0x403BB0), la bioquímica (0x421E70) y cualquier actualización neuronal/química secundaria? ¿En qué punto se incrementa?
4. ¿Qué bucle externo llama a 0x407540 y bajo qué temporización, pausa, desactivación y excepciones? Distinguir **cantidad de llamadas verificadas en assembly** de frecuencia real en Hz/ms; si no puede medirse, informar la limitación.
5. ¿Existen otras rutas de actualización de brain/chem que puedan escribir en los mismos estados sin pasar por el loop principal? Buscar referencias de llamadas y rutas virtuales, sin declarar exhaustividad por hallar algunos E8.
6. ¿El orden reconstruido permite o impide que un emisor, un receptor y una reacción participen en un mismo instante químico? Derivar solo de llamadas efectivamente verificadas.

## Procedimiento y controles

- Analizar EXE SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7. No ejecutar ni instalar, ni publicar binario.
- Registrar dirección exacta, opcode, flujo de control, contador y condiciones. Separar hechos de x86 de inferencias de fuente de tiempo.
- Enfrentar la hipótesis de “siempre cerebro→química” con la ruta química→cerebro ya encontrada en h.1; no eliminar esa contradicción en documentación por comodidad.
- Auditar invariantes con script independiente y tests sintéticos, como en h.1/h.4/h.5.
- Cualquier run de NeuroLab deberá etiquetarse como **simulación aislada** hasta contar con evidencia del scheduler íntegro; no calibrar STW/LTW o nuevos módulos con tiempos arbitrarios presentados como históricos.
- No convertir pruebas de instrucciones correctas en una afirmación de tiempo real: una frecuencia solo se valida si se rastrea por completo la fuente o se mide en la versión original bajo condiciones identificadas.

## Puertas de aceptación

- **G-H6-FLOW:** al menos rutas regular y alternativa documentadas con condiciones, sites de llamada, contador y pruebas de branch.
- **G-H6-CLOCK:** fuente y cadencia de la actualización cerebral/química demostradas de forma suficiente para tiempos comparables; **no cerrar** por localizar un timer sin probar su vínculo.
- **G00-H/G05/G09:** permanecerán abiertas por construcción.

Siguiente unidad acotada: **E09h.6a**, seguir x86 en 0x405D20, 0x407540 y 0x424884, contrastar las ramas y el contador. No añadir neuronas ni reabrir g.10 hasta verificar estas dependencias.
