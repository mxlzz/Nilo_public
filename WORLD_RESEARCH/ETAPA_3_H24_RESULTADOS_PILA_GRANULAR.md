# Etapa3 — H24. Pila granular por fricción, SIN reposo validado en tiempo fijado

**2026-11-22. H24 NO APROBADA como agregado físico estable**, pese a formarse montículos con gran diferencia causal frente a fricción nula. Se cumplieron los gates geométricos, fricción altura/extensión, masa, reproducibilidad, no-gravedad e integridad del owner, pero **dos gates preregistrados fallaron**: soporte/conectividad de≥45 granos y reposo tardío. [Protocolo previo](ETAPA_3_H24_PROTOCOLO_PILA_GRANULAR.md), [código](experiments/probe_e3_h24_granular_pile.py), [CI H24 FAIL por física](https://github.com/mxlzz/Nilo_public/actions/runs/45084751801), commit `5fe21f93b9b7b28c01f95108488ac4f328ef71ae`.

## Banco físico y resultados

PyBullet3.2.7, Python3.11.18, xarray2026.9.0, NumPy2.4.6. 125 esferas A inicialmente separadas, radio0,075m, masa0,025kg (total3,125kg), cinco capas con perturbaciones de seed, piso físico plano y **sin paredes**, gravedad−9,81m/s² y1.600 pasos de1/240s (~6,67s). `lateralFriction=1.5`, `rollingFriction=0.15`, `spinningFriction=0.10` en activo; control todas0 con mismas geometrías/semilla.

- **Activo seed20261122:** altura superior montículo**0,7486067m**, 68 granos en capas por encima de z0,26m, componente mayor de contactos de fuerza positiva **40 granos** (gate≥45 falla), 100 contactos grano-grano y33 con suelo. Radio horizontal P90 **0,79207m**. Desplazamiento mediano entre pasos1200→1600 **0,037418m** (umbral<0,025), velocidad P90 final**0,229981m/s** (umbral<0,08). Aún movimiento residual.
- **Activo seed20261123:** altura **0,7461535m**, 69 granos elevados, mayor componente de contacto **35** (falla), 106 contactos entre granos y25 con suelo; radio P90 **0,63328m**; desplazamiento tardío mediano **0,045085m**, velocidad P90**0,194010m/s** (ambos fallan umbrales).
- **Control sin fricción:** altura superior **0,14999m** (monocapa), 0 granos elevados, 0 contactos positivos grano-grano, mayor componente tamaño1, todos125 grano/suelo. Radio P90 **11,97384m** frente0,792m del activo. Control con gravedad pero sin fricción se dispersó, por lo que la formación del montículo compacto es **causalmente dependiente del rozamiento del engine existente**, no una forma de salida dibujada por nosotros. No demuestra todavía reposo.
- **Control sin gravedad:** 125 partículas inmóviles, 0 fuerza/velocidad/descenso.
- **Integridad:** masa3,125kg en owner, posición/velocidad lineal/angular y cuaternión publicados tras validación; rechazos de8 estados imposibles, replay exacto en mismo runner y NetCDF de16.712bytes restaurado con hash idéntico. Final activo seed1 SHA `9e249c09b73176f81a696c4443ccbc36a2aed274cc9e8c4a44160d922d17ca96`, seed2 SHA `ec6d269e7621dfbd8244ed57722fc0b6e71b721d870a7d3653321f151a647b67`, control sin fricción SHA `aa35551b0e761173696e0fc89916152ed98663dd549a23cc214c4b3d588ca594`.

## Qué demuestra y qué no

**Demuestra:** bajo condiciones idénticas salvo propiedades de contacto, un proveedor de gravedad/fricción físicamente reconocido puede concentrar125 granos en estructuras tridimensionales de múltiples capas, frente a una monocapa extensa sin fricción. La diferencia de altura y extensión es grande y cumple los umbrales registrados, sin paredes ni cohesión artificial, con inventario y estado de cuerpos verificables.

**NO demuestra:** patrón definitivamente estable, reposo de la pila, ángulo de reposo calibrado, cohesión/soporte estructural de techos, resistencia geotécnica, autoorganización del terreno en ROI ni emergencia funcional. Forma inicial: cinco capas de malla con perturbaciones, no una fuente granular natural. La componente de contacto y la velocidad final fallaron gates, por lo que **no se debe llamar pila estable aprobada**.

## Acción científicamente justificada

La condición final todavía muestra material activo, y el protocolo solo corrió6,67s. Antes de cambiar cualquier coeficiente, un **nuevo protocolo H25** puede prolongar **el mismo solver, masas, geometrías, fricción y semillas sin modificar nada más**, medir en tiempo tardío si convergen velocidades y red de contactos, con la misma exigencia de reposo/conectividad de H24. Debe probar que la trayectoria **hasta t1600 es idéntica** a los snapshots H24, para descartar una reconfiguración posterior disimulada, y medir reposo en ventanas específicas nuevas. Si continúa moviéndose o la pila colapsa, documentarlo y no cambiar arbitrariamente parámetros para aprobar. E3 sigue ABIERTA.
