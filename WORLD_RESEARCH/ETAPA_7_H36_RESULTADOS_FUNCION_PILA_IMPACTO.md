# Etapa7 — H36. Intercepción diferencial del proyectil, pero NO función de soporte estable verificada

**Fecha:** 2026-11-22. **DICTAMEN: H36 NO APROBADA según el protocolo original**, aunque el control causal de altura de primer impacto y la red de soporte granular fueron positivos en ambas semillas. [Protocolo previo](ETAPA_7_H36_PROTOCOLO_FUNCION_PILA_IMPACTO.md), [script](experiments/probe_e7_h36_granular_impact_function.py), [CI 45094013248 FAILED por un gate físico](https://github.com/mxlzz/Nilo_public/actions/runs/45094013248). PyBullet3.2.7, Python3.11.18, xarray2026.9.0 y NumPy2.4.6. **Ningún parámetro/umbral se cambió tras conocer resultados.**

## Pregunta experimental y respuestas cuantificadas

Se reprodujeron **bit a bit** en el mismo proveedor las dos pilas originales H26, SHA seed20261122 `ac1dd51b214ede889328a672237a07a850ba7e183b0fa4ed4ffbf73b4e223697` y seed20261123 `b364de5794470a7677eed42d5e544fcfbfa0fb282db2dc6cbecf2c651391ab4d`, además de exactamente el estado de control H26 sin fricción `38676dbd23135e9eee45552611b82de05bedbdb7079053d468edc37f42eeacfc`. Se mantuvo suelo plano sin paredes, granos A125×0,025kg, mecanismo de alimentación original, sin objetos `pile` manuales. Se introdujo **un objeto de prueba externo** esférico r0,15m, masa0,10kg desde x=y0/z1,60m, inicial en reposo, con misma gravedad y contacto en todos los casos. Total inventario observado tras introducirlo **3,225kg**, owner único xarray con126 entidades, sin doble materia. Se ejecutaron720 pasos1/240s posteriores a formación H26.

**Activo seed20261122:**
- Primer contacto positivo con grano en paso**104**, centro z**0,685614149m**; no contacto con piso en720 pasos. Fuerza máxima positiva de contacto granular **57,739N**, impulso integrado de esos contactos ~2,8687N·s (diagnóstico, no presupuesto global termomecánico).
- Al terminar, centro del instrumento **z0,658283075m**, velocidad **0,0507867m/s**, ambos **cumplen** criterios de soporte persistente; la pila mantuvo36 granos en z>0,26m y mayor componente de contactos grano-grano de**82** (vs73 antes), 111 contactos grano-grano/48 suelo.

**Activo seed20261123:**
- Primer contacto con grano paso**88**, centro z**0,945361667m**; tampoco tocó piso dentro de720 pasos, contacto granular positivo con fuerza máxima **41,470N**, impulso diagnóstico~2,3790N·s.
- Al terminar, centro del instrumento **z0,536764532m** (cumple altura>0,30m), pero su velocidad **0,341479796m/s** **NO** cumple umbral de reposo final **<0,12m/s**; estaba físicamente en movimiento. La pila mantuvo36 granos altos y mayor componente de contactos**94** con108 contactos/grano y50/suelo. No se puede afirmar soporte estable del instrumento en esta seed solo por no haber tocado piso.

**Control de igual materia, fricción cero, seed20261122:**
- El primer contacto positivo del instrumento fue directamente con **suelo** en paso132, centro **z0,146948635m**; ningún contacto con granos, que estaban dispersos en monocapa. Al terminar z0,14999m, prácticamente inmóvil. La componente de grano-grano fue1.
- Diferencia de altura del **primer contacto físico** respecto a control ~**0,539m** en seed1 y **0,798m** en seed2: supera el umbral preregistrado≥0,18m; la intercepción alta depende de formación por fricción. La caída original empezó exactamente desde el mismo punto, sin buscar la cima de la pila.

**Controles:** mismo origen/gravedad, fuentes H26 reproducidas en cada rama, replay íntegro de caso A exacto (SHA de historia del instrumento `6f3172cdb23b56768a4d79965ce1c6bbe10a305ade48677578f6951cef96276e`), dos semillas con geometrías distintas, masa total3,225kg,9 corrupciones del owner rechazadas, snapshot NetCDF 18.276bytes con hash idéntico y todos los demás gates pasaron.

## Por qué el resultado NO aprueba E7

**Falló únicamente** `active_seed2_probe_supported_late`: z0,537m pasó el criterio de altura, pero **v0,341m/s** sobrepasó el umbral0,12m/s. Es una falla real de la afirmación «soporte estable», no de serialización ni de conservación. **H36 permanece NO APROBADA** como función mecánica sostenida y E7 sigue ABIERTA.

Sí se comprobó una **función física parcial y causal**: la organización sin plantilla de granos con fricción interceptó una esfera que habría impactado suelo sobre material disperso; los dos agregados conservaron conectividad tras el impacto. Esto no basta para decir que la estructura retuvo un cuerpo hasta el reposo o para prometer amortiguación de impacto cuantitativamente calibrada: su menor fuerza pico puede deberse también a menor velocidad de llegada, pues el contacto ocurrió a más altura; no se compararon velocidades de impacto equivalentes ni energías disipadas globalmente.

**Valor del siguiente paso:** si se requiere demostrar soporte permanente, un único experimento longitudinal preregistrado de **continuar el mismo caso sin modificar dinámica** puede comprobar si la esfera de seed2 finalmente se asienta en el agregado o cae por un talud, **con prefijo H36 exacto a paso720**. Sin embargo, no debe encadenarse indefinidamente cambios de tiempo o parámetros solo para «ganar» un gate. La alternativa es suspender la afirmación fuerte y llevar este resultado como evidencia parcial a una investigación más general de funciones y robustez entre ambientes. Cualquier decisión debe mantener explícito que no es evolución abierta ni mundo integrado.
