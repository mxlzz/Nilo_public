# E03 — pre-registro del primer aprendizaje sináptico

**Estado inicial:** diseño congelado **antes** de implementar o ejecutar E03.  
**Clasificación:** hipótesis NeuroLab propia, inspirada en asociación/refuerzo de C1; **no** reproducción de su STW/LTW, SVRule de refuerzo ni bioquímica.  
**Predecesores:** [G01 y G02 verificados por CI](ESTADO_Y_CONTINUIDAD.md).  
**Fecha:** 2026-11-20.

## 1. Pregunta e hipótesis

¿Puede una red de seis neuronas modificar localmente sus pesos sin recibir las etiquetas correctas, para aprender una contingencia A→D0 y B→D1, y adaptarse al invertirla?

H1: aprendizaje local por refuerzo mejora precisión en estímulos balanceados frente a la misma topología con pesos congelados. H2: puede invertir preferencias al invertir el refuerzo.

H0: sin ventaja reproducible respecto al control o sin capacidad de reaprender.

El problema de «correcto» reside EXCLUSIVAMENTE en el evaluador y no en el módulo neuronal.

## 2. Regla plástica experimental congelada

- Topología E02 (2 entradas, 2 conceptos, 2 decisiones), sin modificaciones de neuronas.
- Cuatro sinapsis C0→D0, C0→D1, C1→D0, C1→D1; pesos enteros en 0..255, iniciales derivados del PRNG de la semilla.
- `choice`: WTA por máximo de salida neuronal (empates: primera acción declarada). No se trata de una instrucción del evaluador.
- `reward`: +1 si la acción elegida coincide con la contingencia oculta, −1 si no coincide. Se presenta **después** de la elección y nunca se entrega la etiqueta correcta al aprendizaje.
- Solo cambia la sinapsis desde concepto **efectivamente activo** hacia decisión **efectivamente elegida**: `w_new = clip(w_old + 16*reward, 0, 255)`. Todas las restantes quedan iguales.
- Si hubiera varias neuronas de concepto activas, se aplica a las que participaron. Durante E03 solo se utilizan estímulos uno-a-la-vez y no se pretende crédito diferido.
- Si el aprendizaje está congelado, el estado sináptico no cambia aunque el evaluador entregue refuerzo.

**Limitaciones reconocidas:** no hay susceptibilidad/eligibilidad, STW/LTW ni inhibición plástica; cada episodio de 3 ticks empieza sin actividad residual. No extrapolar resultados a memoria persistente neuronal ni experiencia ecológica.

## 3. Diseño preregistrado

- Semillas de evaluación: `0..19`, veinte variantes con pesos iniciales distintos; no se elige la mejor.
- Aprendizaje original: 100 episodios por semilla, estímulos A/B equilibrados en cada conjunto, orden aleatorio reproducible; tabla de contingencia oculta solo para el evaluador.
- Holdout: 80 episodios por semilla en orden aleatorio distinto, **sin refuerzo y sin cambiar pesos**, usando valores de entrada C1 no entrenados temporalmente (orden nuevo, mismos símbolos). **Esto NO mide generalización semántica**, reservada a E06.
- Controles: a) pesos plásticos vs b) mismos pesos congelados. Mismo orden y semillas. Se informa precisión total, por A/B y por semilla.
- Inversión: 160 episodios por semilla después de entrenar, con contingencias A→D1, B→D0; después nuevo holdout 80 sin refuerzo.
- Métrica primaria: precisión en holdout original; secundaria: precisión después de invertir y pérdida de pesos originales.
- Umbral exploratorio definido antes de observar resultados: al menos 18/20 semillas con precisión ≥0.90 original y después de inversión; promedio de precisión original ≥0.30 sobre control congelado. Si fallara, informe de resultado nulo y diagnóstico, **no modificar pruebas para hacerlas pasar**.
- Test de integridad: constatar que las variables que codifican correspondencias de evaluación no son atributos ni parámetros de las clases Brain/Learner; el aprendizaje solo recibe `reward`, estímulo realmente activado y decisión elegida.
- Repeatability: secuencias y resultados reproducibles, serialización y reanudación de pesos sin diferencia de trayectoria en ejecución determinista.

## 4. Condiciones de fallo y análisis

- Mayor exactitud por azar en una sola semilla no alcanza.
- Pérdida de una clase por sesgo hacia una acción no alcanza.
- Bloqueo al tocar pesos 0/255 requiere diagnóstico del mecanismo de exploración, no aprobación automática.
- Modificar pesos utilizando directamente `target_action` viola la separación entre evaluador y mente.
- Un cambio en el código posterior a observar el holdout implica congelar nueva versión y nuevas semillas de evaluación.

## 5. Artefactos esperados

- `experiments/neurolab/plasticity.py`: regla plástica local y modelo de estado.
- `experiments/neurolab/e03_protocol.py`: generador/evaluador balanceado, referencias de semilla, reporte legible.
- `experiments/neurolab/tests/test_plasticity.py`: pruebas de aprendizaje, inversión, congelación, reproducibilidad y aislamiento.
- Enlace de CI con SHA de código, informe real con resultados por semilla, estado de G03.

**Decisión de diseño:** este ensayo es para verificar una capacidad mínima. No confundirlo con una reconstrucción histórica detallada de la sinapsis C1.
