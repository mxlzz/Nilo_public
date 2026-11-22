# Etapa3 — H25. La pila alcanzó velocidades bajas, pero perdió agregado conectado

**2026-11-22. H25 NO APROBADA** como formación de agregado granular estable de tamaño mínimo. [Protocolo preregistrado](ETAPA_3_H25_PROTOCOLO_ASENTAMIENTO_TARDIO.md) y [CI 45084934469 FAIL por cuatro gates](https://github.com/mxlzz/Nilo_public/actions/runs/45084934469). El código H24 no se modificó; se extendió solo el número de pasos1600→3600 y ventana tardía de observación3000→3600.

## Hallazgos causalmente firmes

**Reproducción integral de prefijo:** los SHAs de los tres estados al paso1600 fueron **idénticos** a los estados de la CI H24: activo seed20261122 `9e249c09b73176f81a696c4443ccbc36a2aed274cc9e8c4a44160d922d17ca96`, activo seed20261123 `ec6d269e7621dfbd8244ed57722fc0b6e71b721d870a7d3653321f151a647b67`, control μ0 `aa35551b0e761173696e0fc89916152ed98663dd549a23cc214c4b3d588ca594`. Por lo tanto H25 continuó exactamente la física y los estados H24, no otro experimento maquillado.

- **Activo seed20261122:** altura bajó de **0,748607m** en paso1600 a **0,480471m** en3600. Granos en capas superiores `z>0,26m`: de68→**16**, menor a30 preregistrados. Mayor componente de contactos de fuerza positiva de40→**17**, menor a45. Velocidad P90 final **0,0077205m/s**, desplazamiento mediano en ventana3000→3600 **0,0018777m**, ambos **pasaron reposo**.
- **Activo seed20261123:** altura0,746154→**0,531884m**; granos superiores69→**20** (<30); componente mayor35→**27** (<45). Velocidad P90 **0,0051778m/s** y mediana de desplazamiento final **0,0022096m**, ambos **pasaron reposo**.
- **Fricción nula:** altura final0,14999m, ningún grano elevado o contacto grano-grano, componente máxima1, dispersión horizontal P90 **22,730m**; sigue moviéndose con velocidad P90~1,07m/s. Diferencias de altura/compactación y red de contactos respecto a caso de fricción permanecen muy grandes y pasan umbrales.
- **Material/state:** 125 esferas3,125kg, sin paredes ni inventario duplicado; ocho corrupciones rechazadas, replay final exacto, checkpoints NetCDF restaurados. Sin acople termomecánico ni cohesión.
- **Gates fallidos:** `active_seed1_late_heap`, `active_seed1_connected_supported`, `active_seed2_late_heap`, `active_seed2_connected_supported`. Todos los otros gates pasaron, incluyendo tres SHAs de prefijo y los nuevos umbrales de quietud.

## Conclusión independiente

Los granos finalmente **se aquietaron**, pero su red grande de soporte se desarmó durante la fase de asentamiento; no se puede afirmar que la forma transitoria de H24 se convirtió en una estructura estable. El experimento mide un sistema con fricción efectiva, no un sólido cohesivo; su resultado es una distribución granular final parcialmente elevada y dispersa en contacto con piso, sin la conectividad mínima preregistrada.

**E3 sigue ABIERTA.** No ampliar duración arbitrariamente: a t15s la quietud ya pasó y la conectividad disminuyó, por lo que «más tiempo» ya no es una estrategia pertinente. Una nueva prueba diferenciadora podría alterar **solo la condición de alimentación**: depósito gradual de granos por gravedad desde una abertura, como en el [proyecto MIT de ángulo de reposo](https://github.com/DillGrammer/angle-of-repose-digital-twin), sin paredes y con la misma ley de fricción, para establecer si el fallo deriva de la carga inicial de125 esferas simultáneamente. Esta es otra hipótesis/prerregistro, no una reparación de H24/H25. Si tampoco produce estructura estable, es momento de detener reiteraciones de rigid grains y examinar necesidad de cohesión real o DEM especializado.
