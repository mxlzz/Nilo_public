# E07 — pre-registro de plasticidad estructural y reutilización de capacidad

**Fecha:** 2026-11-20. **Clasificación:** aproximación experimental NeuroLab, NO réplica byte a byte de Creatures 1. Se registra antes de implementar y ejecutar.

## Antecedente contrastado (E07.01)

Paper primario Grand/Cliff/Malhotra: dendritas individuales pueden migrar dentro del mismo lóbulo de origen al llegar `strength=0`; **solo** un mecanismo adicional de competencia por «supervivencia del más apto» fue desconectado. [Fuente](https://eem.foo/ccarchive/Sites/fp.cyberlifersrch.plus.com/articles/agents_%2797_paper.htm).

Guía detallada de C1 [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html) distingue migración Decision-style y Concept-style y criterios para evitar fuentes duplicadas. Es reconstrucción secundaria aún no contrastada con el binario/genoma del juego. [Gene Loom](https://lisdude.com/Creatures/Community/GeneLoom/) admite inspeccionar C1 cuando se disponga legalmente del genoma.

## Hipótesis

Con igual capacidad total (dos detectores conjuntivos), permitir desconectar detectores debilitados y reconectarlos a nuevos pares de señales debe posibilitar aprender patrones nuevos que una red de conexiones fijas no puede representar. El coste esperado es olvidar algunas asociaciones antiguas.

**Límite:** esto podría no ofrecer ventaja frente a un caché LRU de igual capacidad. La comparación LRU será obligatoria. No atribuir superioridad cognitiva si basta un caché.

## Modelo mínimo congelado

- Entradas 4 canales `A0,A1,B0,B1`, exactamente un A y un B activo; conjunto de pares `(0,2),(0,3),(1,2),(1,3)`.
- Presupuesto: **dos conceptos (slots)**. Cada uno tiene dos dendritas de entrada vinculadas a un par, `strength∈[0,3]` y dos pesos hacia decisiones D0 y D1; el número de slots no cambia jamás.
- Inicialmente los slots detectan `(0,2)` y `(1,3)`. Las decisiones NO están cableadas: pesos aleatorios en [40,220] por semilla.
- Activación: solo si las dos señales del par están presentes. Ganador D0/D1 por peso del slot activo; si no hay slot activo, abstención/elección predeterminada D0 y sin actualización de peso.
- Feedback después de elección: +1 si acierta según evaluador, -1 si falla; solo modifica peso de la decisión elegida del slot activo, ±16 limitado a [0,255].
- **Modelo `migratory`**: cada uso del slot restablece fuerza a 3; cada ensayo donde no se activa pierde una unidad. Si llega a 0, el slot se desconecta; si su par de fuentes es diferente del patrón actual y el patrón actual no está ya representado, se reconecta al par actualmente presente, reset de pesos según semilla reproducible y fuerza=3. Nunca se duplican pares. NO se presupone que estos sean los criterios reales de atrofia genética de C1.
- **Modelo `fixed`**: mismos dos slots y pesos plásticos, pero fuentes nunca cambian.
- **Modelo `lru`**: misma capacidad y regla de pesos, pero reemplaza inmediatamente al slot menos recientemente usado cuando aparece un patrón nuevo; se compara efectividad/coste. No se atribuye carácter neuronal a LRU.

## Datos y métricas pre-registrados

- Semillas `0..19` (20 repeticiones).
- Fase I: patrones antiguos `(0,2)→D0` y `(1,3)→D1`, 30 episodios cada uno, orden intercalado por semilla.
- Fase II: nuevos patrones `(0,3)→D1` y `(1,2)→D0`, 30 episodios cada uno, orden intercalado.
- Holdout nuevo: 40 episodios de cada patrón nuevo, sin plasticidad/atrofia para evaluación. Holdout viejo idéntico para medir olvido.
- Criterio principal: migratory ≥0.90 de precisión sobre patrones nuevos en al menos 18/20 semillas; media migratory vs fixed ≥0.30.
- Criterio de coste: retención vieja del migratory debe cuantificarse, y reportar si es peor por ≥0.15. LRU deberá informarse con las mismas semillas y episodios; no exigir que migratory lo supere.
- Criterios de invariantes: dos slots siempre, pares de fuentes de lóbulos adecuados y no duplicados, pesos/fortaleza en rangos, reinicios verificables, mismos patrones/semillas en condiciones.
- Regresión: congelar aprendizaje y comprobar que controles no adquieren capacidades por un bug.

## Interpretación

Éxito confirma que **reutilizar conexiones bajo capacidad fija facilita aprender patrones nuevos a costa de olvidar otros**, no que la mente forme conceptos generalizables. Resultado equivalente a LRU indica que el mecanismo no añade todavía utilidad sobre administración simple de memoria. No introducir más slots para superar la prueba. Registrar todos los resultados, incluso fracaso y olvido.
