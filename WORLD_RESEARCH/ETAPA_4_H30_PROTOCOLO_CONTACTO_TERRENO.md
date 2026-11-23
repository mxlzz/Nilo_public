# Etapa4 — H30. Preregistro de compatibilidad del relieve generado con contacto rígido local

**2026-11-22. PROTOCOLO ANTES DE CÓDIGO/CI.** La [H29](ETAPA_4_H29_RESULTADOS_SEMILLAS_TERRITORIO.md) validó WorldEngine→Landlab/SPACE con dos seeds, owner de masa y balances; E4 también exige compatibilidad de **condiciones iniciales con las leyes E2** de gravedad y soporte rígido. H30 comprueba **una superficie LOCAL derivada exactamente de uno de esos terrenos**, no fusiona WorldEngine, Landlab y Bullet en un motor ni pretende simular terreno volumétrico completo.

## Hipótesis física

Un patch triangular estático construido a partir de **cuatro elevaciones generadas WorldEngine** puede servir como frontera de contacto válida en PyBullet, sustentando una esfera que cae por gravedad y evitando penetración; con g0 la esfera no cae, sin superficie no hay apoyo. Hipótesis contraria: las coordenadas/unidades se proyectan incorrectamente, el mesh no se reconoce, hay túnel o cuerpos pasan de largo; NO se aprueba E4 aunque H29 sea correcto.

## Alternativa y decisión geométrica

PyBullet3.2.7 ya utilizado con `GEOM_PLANE` en H17/H26; su `GEOM_MESH` y `GEOM_FORCE_CONCAVE_TRIMESH` admiten superficies estáticas con triángulos. No implementar solver de contacto ni triangulador arbitrario: dos triángulos de cuatro muestras existentes son la discretización geométrica mínima de una superficie definida por alturas, no modelar cuevas. Un `GEOM_HEIGHTFIELD` de la totalidad de16×32 sería más complejo de alinear y no necesario para verificar soporte LOCAL; el actor real debe poder referenciar el mismo origen y fuente de elevación que Landlab.

## Input compartido y muestras

- Reutilizar **sin modificaciones** el generador H29 pinneado `Mindwerks/worldengine SHA 3b9113ecfad884cab4b32081d138a15e6262ada8`, mismo NPZ raw de seeds **7321 y8128**, mismo reset global1234, shape16×32, mismos SHA fuente. La CI puede usar el mismo artefacto generado por el job H29.
- Convertir a elevación **nominal 0..50m** con `z_m=50*(raw-min)/(max-min)`; **no** calibración de relieve natural. De todos los subcuadrados de2×2 muestras de cada mapa, seleccionar uno **de manera determinista** con mínimo rango `max(z_4)-min(z_4)`, desempate por orden de filas/columnas; no escoger a mano la ubicación según resultado Bullet.
- Construir la superficie local a partir de cuatro muestras con separación horizontal100m y alturas calculadas: vértices `v0=(0,0,z00)`, `v1=(100,0,z01)`, `v2=(100,100,z11)`, `v3=(0,100,z10)`, triángulos orientados `[v0,v1,v2]` y `[v0,v2,v3]`. Los nodos corresponden a posiciones originales de **centros de celda WorldEngine** (regla de traslado del origen físico −50m H29); no se interpola entre escenas de origen distinto. La pendiente/rango y origen (índice row/col) se registran; la prueba NO modela toda la superficie global.
- Punto de ensayo en **interior del triángulo1** `(x=40m,y=30m)`, barycentría `z_expected=0.6*z00+0.1*z01+0.3*z11`. El ray cast vertical desde `z_expected+10m` hasta `z_expected−10m` debe golpear el mismo mesh y reflejar altura esperada a tol absoluta **0,001m**. No trasladar ni deformar datos para forzar el rayo.

## Banco de caída sin contacto ad hoc

- Esfera rígida `radius=0.50m`, `mass=2.0kg`, centro inicial `(40,30,z_expected+3.0)m`, velocidad inicial0. Bullet DIRECT, gravedad−9.81m/s², `dt=1/240s`,720 pasos (3s), solver60, fricción lateral .8, restitución0, sin otro suelo, paredes o fuerzas.
- **A por cada seed:** mesh físico estático derivado del patch y esfera móvil: al menos1 contacto de fuerza positiva durante3s, descenso neto vertical≥1m, ausencia de penetración de superficie (distancia firmada de contactos≥−0,05m), esfera finita, posición final dentro del patch y altura final por encima de `min(z4)-1m`. La dinámica puede deslizarse si la pendiente no es cero, por eso **no** exigir z final exactamente barycentría inicial o reposo de larga duración.
- **Control g0:** mismo mesh y cuerpo, g=(0,0,0); posiciones/velocidades finales sin cambio (tol1e−8m/m/s), sin contacto de fuerza positiva.
- **Control sin mesh:** misma gravedad/esfera pero sin terreno: caída libre por≥5m, ningún contacto positivo, posición final por debajo de inicial−5m. No interpretar ese paso bajo la superficie nominal como estado físico válido de un mundo con terreno.
- **Replay:** caso con mesh y gravedad para seed7321 reproduce bit a bit pos/vel/cuantificación de contactos y ray z en el mismo runner. Scene seed8128 usa el otro raw map, cumple controles y distingue mapa fuente por hash.

## Owner, invariantes y controles

- Un `xarray.Dataset` por caso físico con `material_mass_kg(body)=2kg`, `position_m(body,xyz)`, `velocity_mps(body,xyz)`, `terrain_height_m_nominal(y=2,x=2)` como geometría inerte derivada del raw source, más metadatos de seed, raw sourceSHA, patch index, unidades y reloj. Bullet es vista computacional transitoria; datos de masa/pose se publican solo tras validar candidato completo.
- **Rechazo de al menos seis corrupciones**: masa+1kg, masa negativa, unidad errónea, cota geométrica alterada sin fuente, hash fuente alterado, id corpo alterado, campo duplicado de masa. Estado sano/geométrico no mutado, NetCDF restaura altura 2×2, masa, pos/vel, metadatos, SHA exactamente.
- El contexto Landlab H29 conserva por separado un owner de suelo; **no se puede afirmar que ambos estén ya sobre un owner simultáneo o compartan el mismo reloj**. La geometría se deriva exactamente del raw y se comprueba por source SHA, pero los procesos no están acoplados; esa es Etapa5.
- Emitir `WORLD_EVAL_JSON` con SHA upstream/ejecuciones, versions, semillas, patch selection, rango, ray error, caída/control, contactos, replay/checkpoint y gates; salida CI no-cero si falla. Mantener H29, H17, H26 intactos. **No corregir** superficie, datos ni tolerancias según resultado.

## Interpretación

**H30 APROBADA** solo si todos los gates funcionan en ambas semillas y controles; junto con H29 habilita auditoría de cierre mínimo E4: dos terrenos iniciales reproducibles, materia/relieve sin saldos inválidos y compatibilidad con ambas interacciones elegidas en E2, **por separado**. No demostraría cuevas, estabilidad geológica, realismo métrico ni acoplamiento ambiental. La etapa5 tiene su propia hipótesis y no se declara hecha.
