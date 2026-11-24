# NeuroLab — E09.02c resultado negativo preregistrado (no se aprueba G09.02c)

**Fecha:** 2026-11-21. **Caso histórico / resultado negativo.**
Pre-registro original: [E09_02C_APRENDIZAJE_PRE_REGISTRO.md](E09_02C_APRENDIZAJE_PRE_REGISTRO.md), aprobado como diseño *antes* de escribir el código.
Código ensayado: [c1_microlearning.py](../../experiments/neurolab/c1_microlearning.py), [e09_microlearn_protocol.py](../../experiments/neurolab/e09_microlearn_protocol.py).
CI que mostró el fallo: [GitHub Actions #44919979878](https://github.com/mxlzz/Nilo_public/actions/runs/44919979878), SHA `9f4ab4fbf47f98933c10dad39051200cd6a59028`.

## Resultado exacto del runner (impreso dentro del test fallido)

| Métrica | Obtenido | Criterio preregistrado |
|---|---:|---|
| Precisión media después de entrenar D0 | 1.0000 | ≥0.90 en al menos 18/20 semillas |
| Precisión media control congelado | 0.4925 | — |
| Ventaja frente a congelado | 0.5075 | ≥0.30 |
| Semillas que aprenden D0 ≥0.90 | 20/20 | ≥18/20 |
| Precisión media después de inversión a D1 | **0.3000** | ≥0.90 en al menos 18/20 |
| Semillas que invierten ≥0.90 | **6/20** | ≥18/20 |
| **Gate `passed`** | **FALSE** | TRUE |

**No hay éxito de reversión.** El hecho de que el test original fallara es un resultado experimental relevante, no una razón para redefinir la métrica.

La suite también encontró un **error en el fixture de validación**: afirmaba que el valor 0 de un peso debía rechazarse, pese a que el contrato válido del peso es de **0 a 255**. Se corrigió únicamente ese fixture, no los resultados ni las ecuaciones. El test del criterio preregistrado permanece con las **mismas aserciones**, marcado `@unittest.expectedFailure` para que CI distinga un **resultado científico negativo esperado** de un nuevo error de software. La ejecución independiente del protocolo continuará devolviendo fallo hasta que se evalúe otra versión, sin sobrescribir este escenario.

## Mecanismo causal probable — hipótesis de diagnóstico, no hecho histórico C1

Con dos señales de entrada permanentemente activas, los cuatro pesos D0/1-excitatorio/inhibitorio inicialmente en cero y estado basal 80:

1. La primera recompensa refuerza D0 excitatorio hasta llegar a la saturación 255.
2. En la inversión, los castigos incrementan la inhibición de D0 pero no reducen la excitación ya saturada.
3. Al llegar ambos pesos D0 al máximo, su puntaje mínimo es `80 + 255 - 255 = 80`.
4. Si D1 recibió un castigo durante la fase inicial, puede partir con puntaje `80 - 16 = 64`. Como la política solo explora cuando los puntajes empatan, **D1 ya no vuelve a elegirse**, y su peso excitatorio no puede fortalecerse.
5. Se forma una preferencia absorbente que bloquea la reversibilidad en muchas semillas.

**Esto es una inferencia verificable del código experimental, no una descripción del funcionamiento original de Norns.**

## Próxima prueba independiente

Antes de modificar el mecanismo hay que comparar **una intervención a la vez**. En [E09_02D_EXPLORACION_PRE_REGISTRO.md](E09_02D_EXPLORACION_PRE_REGISTRO.md) se plantea conservar la plasticidad exactamente igual, cambiando solo la política de selección para asegurar exploración no restringida a los empates. Comparar con este baseline original, mismo número de episodios, semillas y criterios, documentando también el coste de las elecciones exploratorias.

No afirmar que una mejora por exploración valida el modelo químico C1, ni que una red de cinco neuronas constituye mente autónoma.
