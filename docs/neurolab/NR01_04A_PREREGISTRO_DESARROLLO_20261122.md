# NR01.04-A — preregistro de cohorte de desarrollo completa (sin confirmación)

**2026-11-22 · congelado ANTES del runner y antes de usar semillas 23001..23019.**
Dependencias: [NR01 plan](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md), [desafío](NR01_02_PREREGISTRO_DESAFIO_20261122.md), [contrato D-v1](NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md), [piloto 23000](NR01_03D_RESULTADO_PILOTO_DESARROLLO_20261122.md).

## Propósito y puerta de alineación

Preguntar, bajo los mismos datos y premios, si alguna representación no supervisada ART o KMeans tiene **ventaja práctica sobre el mejor control simple**, en transferencias nuevas y con costo y memoria explicados. Nunca asumir que un cluster representa un concepto útil. No construir nuevos modelos ni cambiar tareas para rescatar un candidato.

La semilla 23000 **ya se exploró** y se repite aquí únicamente para reproducibilidad; 23001..23019 se ejecutan por primera vez bajo el contrato original. Este es un conjunto **de desarrollo** abierto al análisis, no una confirmación. **No tocar 24000..24019**, ni históricos 1400..1419.

## Matriz congelada

Por cada semilla 23000..23019 y familias A/B:
- Raw16 + decoder D-v1.
- 1NN16 FIFO sin decoder adicional.
- MiniBatchKMeans con K4/K8/K16 + D-v1.
- FuzzyART rho .60/.80/.90 con cap16 + D-v1; cualquier >16 queda `over_budget`, siempre registrado y no elegible. No fusionar/truncar ni cambiar vigilancia.
Total **320 condiciones (20 mundos ×2 familias ×8 brazos)**, incluyendo un replay de las 16 condiciones del piloto. La misma cinta de 1200 observaciones sin feedback; mismas 64 decisiones de entrenamiento por fase y el mismo holdout, congelado sin premio; evaluar checkpoints8/16/32/64 y la reversión A, y tareas independientes B1/B2.

El código llama a `run_world` existente sin duplicar reglas de modelos; usa solo semillas listadas, no acepta opciones CLI que cambien semillas/hiperparámetros. Toma tiempo CPU y estado serializado como en el contrato. Huellas de exposición deben coincidir por mundo y familia en los ocho brazos, y para ambas tareas cada cinta de feedback igual por todos los elegibles. Si el replay 23000 no reproduce los valores primarios registrados en NR01.03-DP (con tolerancia absoluta 1e-12), abortar y declarar el conjunto inválido.

## Regla de comparación, definida antes de datos nuevos

Para cada brazo **elegible en los 20 mundos de cada familia**, calcular el puntaje compuesto por mundo `S=0.5*A(original,32)+0.25*B1(32)+0.25*B2(32)`. Las tres observaciones comparten semilla; la unidad de inferencia es **mundo**, no tick. La reversión A al checkpoint32 se reporta aparte y **no se elimina** del juicio de estabilidad. No reemplazar `over_budget` por precisión cero ni promediar solo mundos donde triunfa ART.

Elegir el **mejor baseline simple** entre raw y 1NN mediante media de S sobre 20 mundos; empate favorece menor estado serializado promedio, si persiste empate raw. Comparar cada candidato aprendido elegible (KMeans y ART, si no excede tope) contra ese baseline mediante diferencias por mundo, media, mediana, proporción de mundos donde mejora/empeora y **bootstrap pareado de 5000 remuestreos sobre 20 mundos**, RNG `random.Random(918277)`, percentiles lineales 2.5/97.5. Informar A original, B1, B2 y A reversión por separado, junto con tamaños de estado, categorías y tiempos. Informar por separado número de mundos ART fuera de presupuesto por cada familia y vigilancia; si >0, brazo **no pasa la puerta completa** y no se le atribuye superioridad agregada.

**Criterio exploratorio de suficiencia para pedir confirmación posterior, NO ejecución automática:** el mejor candidato aprendido tiene ventaja media >=0.05 en S de desarrollo, IC bootstrap95% completamente >0, y no concentra toda ventaja en una sola familia; además precisa evidencia de que el encoder aprendido aporta causalmente a esa ventaja (ablación sin ventaja en ausencia de adquisición) y tradeoff CPU/memoria tolerable. Si no cumple, cerrar como resultado de desarrollo negativo/indeterminado, **sin consumir confirmación**. Incluso si cumple, congelar modelo, hiperparámetros y ablation antes de NR01.05.

## Datos y errores

Guardar JSON de resultados por semilla/brazo y JSONL incremental, incluso ante fallo, como artefacto Actions de 90 días con SHA256; emitir al log métricas y diagnóstico reproducibles; publicar índice permanente en GitHub con run, commit, checksum, cuentas y limitaciones. Queda explícito que el artefacto temporal no equivale a archivo permanente integral. Si cualquier excepción no prevista o discrepancia de exposición aparece: job falla, se conserva resultado parcial y NO se evalúan estadísticas selectivamente como si faltantes fueran azar.

**Siguiente paso aprobado por dirección NR01:** ejecutar sólo desarrollo bajo este protocolo, auditar y decidir STOP / reformular con nuevo preregistro / estudiar una confirmación separada. PR#103 draft; main/Nilo0.7 intactos.
