# E09.02i-I3c — alternativas mínimas para migración y persistencia

**Fecha: 2026-11-21. Estado: PLAN / sin implementación ni aprobación de nueva arquitectura.**

## Dependencias verificadas

[I3b.2a](E09_02I_I3B2A_RESULTADO_FORTALEZA.md) observó que la pérdida de fortaleza borra LTW: con pulso temprano de ganancia normal, 114 de118 unidades LTW se borraron entre t128 y136; la versión amplificada perdió44 de314. [I3b.3](E09_02I_I3B3_RESULTADO_MIGRACION.md) probó que la topología actual no puede aprovechar migración tipo1 de la biblioteca existente: las dos fuentes C0/C1 ya están ocupadas por dos contactos/clase/Decision y el cerebro no almacena source_pointer. [c1_migration.py](../../experiments/neurolab/c1_migration.py) **ya resuelve el núcleo migratorio**, por lo que no se debe reimplementar.

## Opciones a contrastar, no resultados

| Variante | Arquitectura | Disponibilidad de fuente libre | Beneficio potencial | Limitación |
|---|---|---|---|---|
| A: baseline | 6 neuronas, 8 dendritas Decision | Ninguna | Comparación histórica exacta de la reducción actual | Desconexión sin recableado |
| B: reducción mínima | 6 neuronas, 4 dendritas (1/clase/Decision) | Una de dos Concept por clase | Puede usar decision_migrate existente sin añadir neuronas | Reduce capacidad simultánea y requiere fuente dinámica y scheduler |
| C: ampliar Concept | Al menos 7 neuronas, 8 dendritas | Un Concept adicional | Mantiene cupo de dendritas con alternativa | Aumenta complejidad sin efecto demostrado, concepto extra debe tener función |
| D: ablación de reinicialización | 6 neuronas, 8 dendritas, misma fuente | No aplica | Separa efecto de reset de efecto de recableado | **No es migración histórica C1** |

## Recomendación fundada

Priorizar **el diseño experimental de B frente a A y D**, no agregar todavía una séptima neurona. La prueba debe separar el beneficio de tener una alternativa de origen de la pérdida de capacidad por usar la mitad de sinapsis. Tampoco debe inferirse que el reinicio sintético D es una reparación histórica.

**Siguiente unidad exacta I3c.1 (DISEÑO):** redactar contrato de estado con source_pointer dinámico y cuatro contactos, punteros estables de Concept0/Concept1, cursor del RNG, condiciones de intento migratorio, recipient_output, checkpoint y determinismo; definir controles B sin migración/B con migración y D, cronograma de pruebas comparable y sin respuestas correctas dentro del cerebro. Identificar con evidencia las condiciones originales de activación migratoria o marcar adaptación N. Preregistrar cohortes nuevas, métricas y condiciones de aceptación **antes del código experimental**.

No decidir ampliar Concept ni modificar C1ContextBrain baseline, sus pesos o sus genes todavía. **G05, G09 y G00-H permanecen abiertas**. Código y PR experimental separados del motor Nilo 0.7.
