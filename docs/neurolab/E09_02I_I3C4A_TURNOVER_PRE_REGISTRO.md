# E09.02i-I3c.4a — preregistro POST HOC de turnover y memoria bajo migración

**2026-11-21.** Auditoría EXPLORATORIA derivada del [experimento I3c.4 preregistrado](E09_02I_I3C4_QUIMICA_APAREADA_PRE_REGISTRO.md), tras observar que los contactos sí migran pero la exactitud Y≈B≈F. NO es una prueba confirmatoria, no reutilizar 900..919 para ajustar parámetros.

## Punto de integridad: distinguir ticks y conexiones

La primera versión del runner I3c.4 llamó incorrectamente «migraciones aceptadas» al contador de **ticks con al menos una** aceptación. [CI inicial #44960312460](https://github.com/mxlzz/Nilo_public/actions/runs/44960312460) registró 2.787 ticks migratorios en Y y 2.787 en P, mientras que el desglose de eventos Type1 muestra 3.377 aceptaciones Y y 3.379 P. El origen es sólo una agregación numérica: el simulador no cambió. Corrección exclusiva en contador y test adversarial de dos migraciones en el mismo tick, con nuevo workflow. Conservar errata y jamás esconder la CI inicial.

## Pregunta observacional

¿Por qué la red con migración no supera al control químicamente apareado? ¿Hay churn de origen excesivo, borrado de STW/LTW, pérdida de fortaleza, o ausencia de crédito causal? Ninguna causa se afirma antes de medir.

## Método antes del nuevo auditor

- Repetir EXACTAMENTE las mismas 20 semillas900..919, las mismas cuatro ramas B/Y/P/F, mismos 60 entrenamientos+36 holdout por fase, mismo RNG raw precargado, misma dosis80/rate40. No ajustar cerebro ni feedback.
- Instrumentar sin cambiar la lógica mediante SUBCLASE OBSERVADORA de DynamicContextBrain.step que llama al paso real y SOLO lee su DynamicBrainTick. Registrar en cada tick por modo: ganador, clase/source, punteros antes/después, strength, STW/LTW, eventos Type1 y cursor. No crear nuevos estímulos ni intervenir en química.
- Igualdad estricta: la respuesta completa de run_seed con instrumentación debe ser byte-identical a la respuesta original para cada semilla, contrastada con un SHA-256 canónico por semilla derivado del artefacto del workflow I3c.4 corregido. El inspector NO debe mutar el estado.
- Conteos por fase y brazo: acceptances por **contacto** y ticks con≥1 aceptación por separado; tasa por 100 ticks y por slot, intervalos entre migraciones del mismo slot, máxima racha sin migrar, distribución de dirección C0→C1/C1→C0, cambios de source vs no-acción. Reportar si todo está explicado por los eventos.
- Memoría/atrofia: cuando la dendrita migra, observar LTW/STW y fuerza de la conexión **ANTES del tick** y DESPUÉS. Registrar cantidad con LTW positiva antes de la limpieza del mismo tick; cuantificar pérdida justo cuando strength llega0, cambios LTW de gate128 y LTW que permanece al final. **No confundir borrado por atrofia con efecto directo del algoritmo de migración**.
- Sin cambios de genoma, tasas, reglas C1 o migrador. Ninguna métrica altera el test original. No clasificar sinapsis como causal sin un contraste que las suprima.

## Puertas

- **I3c4a-REPLAY:** hash por semilla y respuesta numérica de I3c.4 corregido idénticos bajo instrumentación.
- **I3c4a-ACCOUNTING:** cantidad de eventos migratorios en trace=reason accepted del estudio original, y ticks con actividad migratoria≤eventos.
- **I3c4a-EVIDENCE:** informe negativo o positivo más JSON completo, CI.
- G05/G09/G00-H se mantienen ABIERTAS. El resultado puede recomendar una nueva prueba independiente, pero no validar una arquitectura de más neuronas ni justificar tuning retroactivo.
