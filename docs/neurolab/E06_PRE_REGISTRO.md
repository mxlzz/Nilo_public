# E06 — pre-registro: detección de conceptos y generalización limitada

**Fecha:** 2026-11-20. **E06 es independiente de E05:** no se usa eligibilidad temporal ni refuerzo retrasado, porque G05 conserva un fallo de crédito espurio. Implementación separada para estudiar únicamente representación por conjunciones.

## Fuente y alcance

Grand, Cliff y Malhotra describen neuronas del lóbulo Concept que reconocen conjunciones de entradas (1–4). La interpretación histórica exacta de sus pesos, inicialización y migración en un genoma C1 sigue pendiente.

**Este experimento NO forma conceptos nuevos a partir de experiencia**: los cuatro detectores de pares están predefinidos sin etiquetas de respuesta. Solo se aprenden sus asociaciones con acciones. La plasticidad estructural de los detectores será E07. Resultado positivo implica **transferencia a una variación de contexto irrelevante**, no generalización semántica ni invención de conceptos.

## Hipótesis

En un problema de conjunción no lineal (XOR), un circuito de detectores de pares y pesos plásticos debe aprender a elegir entre dos acciones y conservar el criterio cuando aparece un estímulo irrelevante adicional. Un memorizador del patrón completo no conoce la variante con contexto nuevo, y un decisor basado solo en pesos aditivos individuales no puede representar exactamente la función XOR.

## Banco de señales

Cinco canales binarios: `A0,A1,B0,B1,C`. Por ensayo, exactamente uno de `A0,A1` y uno de `B0,B1` están activos; `C` es señal irrelevante de contexto.

Las cuatro parejas posibles A×B son conocidas por el laboratorio, no por una tabla de respuestas embebida en el cerebro. Cuatro detectores responden a `A0∧B0`, `A0∧B1`, `A1∧B0`, `A1∧B1`; no incluyen C. Salida de detectores activos = 255. Dos neuronas de decisión reciben pesos `w(Ci, D0/D1)` inicializados por semilla [40,220]. Gana el puntaje mayor; empate → D0, salvo caso inactivo documentado.

**Solo en evaluador**, relación:
- A0,B0 → D0
- A0,B1 → D1
- A1,B0 → D1
- A1,B1 → D0.

En entrenamiento siempre C=0; en holdout solo C=1. Ningún modelo recibe del evaluador la etiqueta correcta: después de actuar recibe +1/-1 (regla local de E03: cambiar ±16 solo el peso del detector activo hacia decisión elegida).

## Baselines y datos congelados

- Semillas `0..19`, 20 condiciones reproducibles.
- Entrenamiento: 30 repeticiones de cada una de las cuatro combinaciones = 120 episodios, permutados por PRNG `seed+6000`.
- Evaluación: 20 repeticiones de cada una de las cuatro combinaciones C=1 = 80 episodios, orden PRNG `seed+7000`, sin plasticidad/refuerzo.
- Baseline `exact-pattern-memorizer`: memoriza patrón **de cinco bits completo** con C=0; para C=1 sin coincidencia emite D0 por convención predefinida. Precisión esperada 50 %.
- Baseline `singleton-additive`: usa las cuatro señales individuales A0,A1,B0,B1 con pesos de decisión inicializados misma escala y regla local de ±16. No detectores de pares. Debe reportarse su tasa real (se espera que XOR no sea perfectamente separable).
- Control `frozen-concepts`: misma topología de conceptos, sin alterar pesos; valida que no estén codificadas las respuestas en su construcción.
- No cambiar el conjunto de evaluación tras observar resultados.

## Métricas y criterio G06

- Precisión holdout por semilla y promedio, errores por par, uso de pesos, proporción de decisiones inactivas, exactitud del baseline memorístico y singleton aditivo.
- **Umbral preregistrado:** al menos 18/20 semillas con precisión ≥0.90; mejora media ≥0.20 sobre memorizador exacto y ≥0.15 sobre aditivo. Si no, registrar falla del protocolo sin alterar semillas ni etiquetas.
- Verificar que cambiar C en una misma combinación no altera la salida de la red de conceptos para pesos fijos, que hay cuatro pares activos bajo sus respectivas señales y que no se almacenan nombres de las respuestas en la arquitectura.
- Si el resultado es positivo, escribir como «invariancia contextual con detectores de conceptos predefinidos»; no «formación autónoma de conceptos», «XOR descubierto por la red» o «comprensión de lógica».

## Criterios secundarios / problemas abiertos

El diseño no prueba transferencia a un par A×B completamente nuevo (las cuatro parejas aparecen en train), ni aprende los detectores. Deben mantenerse como limitaciones para experimentos posteriores. La representación conjuntiva no está comparada aún a una red neuronal moderna entrenada por gradiente.

## Entrega

`experiments/neurolab/concepts.py`, `e06_protocol.py`, `tests/test_concepts.py`; un resultado nulo exige revisión de hipótesis o diseño, no afirmar éxito.
