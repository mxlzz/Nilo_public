# E09.02i-I3b — diseño de discriminación mecanística, sin corrida confirmatoria todavía

**Fecha:** 2026-11-21. **Estado:** PLAN DE ENSAYO / NO EJECUTADO. Surge de la prueba [I3 negativa](E09_02I_I3_RESULTADO_NEGATIVO.md) y de la observación [I3a](E09_02I_I3A_RESULTADO_DIAGNOSTICO.md). Esta propuesta no equivale a parámetros aprobados ni a una prueba preregistrada lista para ejecutar.

## Pregunta exacta y amenazas a la validez

I3 demostró que en el **régimen sintético rate40/dose80**, M≈F. I3a observó 2820/2981 eventos con refuerzo positivo, efecto máximo4, con muchos más eventos CHEM positivos. Los datos **no distinguen** (H_A) insuficiente efecto químico de (H_T) atribución a contextos distractores.

**No se permite** subir dosis, cambiar tasas o modificar una SVRule hasta alcanzar el rendimiento esperado usando las mismas semillas200..219; esas semillas y resultados ya fueron observados. Tampoco sirve comparar sin equiparar la exposición a sustancias o el retardo del control.

## Diseño propuesto antes de preregistrar una ejecución nueva

1. **Control de integridad / exposición:** cuantificar por brazo y por tick el pool en Reward49/Punishment50, la lectura Decision CHEM0/CHEM1, la susceptibilidad y el valor efectivo de refuerzo en la sinapsis. Mantener fijo el mismo generador de estados/semillas de una futura cohorte y la misma cantidad de ticks. No introducir la acción correcta como señal neuronal.
2. **Eje de amplitud:** usar *las mismas secuencias de señales químicas* por experimento para el brazo neuronal con/sin plasticidad, e incluir un control que iguale distribución empírica de CHEM y efecto sináptico **sin** depender de feedback privilegiado del evaluador. El mecanismo para obtener amplitudes comparables debe fijarse con un oráculo externo o fuentes C1 verificadas **antes** de mirar las nuevas métricas. Si no puede conseguirse exposición equiparada sin manipular decisiones, declarar brazo no comparable en vez de ocultarlo.
3. **Eje de atribución temporal:** comparar entrega de idéntico contenido químico en el instante objetivo versus después de d distractores, sin alterar dosis total ni cambiar entradas genéticas. Registrar cada sinapsis que recibe refuerzo y cuánto corresponde a un contexto activo en la decisión causante versus distractor (atribución conocida **solo por el evaluador**). Esto es una intervención experimental de línea N, no un argumento de fidelidad histórica.
4. **Controls:** red F congelada con el **mismo calendario de pulsos exógenos** para evitar cambios de régimen entre M y F; refuerzo directo C referencial pero no apareado, Q tabular causal como límite superior informacionalmente privilegiado. Usar un brazo placebo de química desconectada de las sinapsis solo si responde a pregunta separada y se preregistra su costo.
5. **Métrica primaria todavía a congelar:** diferencia de exactitud M vs F en holdouts A/B **y** proporción de efecto sináptico aplicado a conexiones del contexto causante versus distractor, sin excluir no-acciones. Incluir reversión, coste, retención, por demora y trazas de cambios STW/LTW. Definir umbrales y tamaño muestral antes de ejecutar.
6. **Cohorte independiente:** una secuencia de semillas nunca usada por las pruebas g.10/I3/I3a (por ejemplo 300..339) queda **propuesta** y debe fijarse al cerrar el preregistro ejecutable. No reutilizar I3 semillas200..219 para validar mecanismos seleccionados post hoc.
7. **Rates/genoma:** antes de comparar con Creatures original, recuperar half-life/decay originales del GEN (o una fuente histórica independiente verificable); sin eso los nuevos resultados serán **N experimental** con tasa explícita, no reproducción del Norn.

## Puertas de decisión

- **B-I3b-DISEÑO:** hipótesis discriminables, intervención que altera solo una dimensión, brazos equiparados con suficiente rigor y sin fuga de ground truth; el protocolo confirmatorio se redacta con parámetros congelados ANTES del código y de las nuevas semillas.
- **G05/G09:** siguen abiertas hasta resultados confirmatorios y evidencia de atribución temporal correcta; un diseño bien escrito no las cierra.
- Si el mecanismo del brazo de amplitud no permite una comparación limpia con química real o su relación con susceptibilidad no puede verificarse, **detener el contraste en esa dimensión**, documentar la incertidumbre y estudiar primero la fisiología histórica.

**No modificar red, mundo, Nilo0.7 ni main.** PR#103 sigue draft. Este documento es un PLAN, no dato empírico ni decisión confirmada del usuario.
