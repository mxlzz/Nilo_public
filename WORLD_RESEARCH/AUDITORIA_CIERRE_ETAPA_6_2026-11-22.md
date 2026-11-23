# Auditoría del gate experimental E6 — Continuación causal verificable de subsistemas

**2026-11-22. Dictamen: gate E6 MÍNIMO cerrado PROVISIONALMENTE para tres subsistemas seleccionados; continuidad de un mundo ambiental totalmente integrado NO aprobada.** Fuentes: [hoja de ruta §6](BASES_Y_HOJA_DE_RUTA.md), [H33](ETAPA_6_H33_RESULTADOS_RESTART_LANDLAB.md), [H34](ETAPA_6_H34_RESULTADOS_CHECKPOINT_BULLET.md) y [H35](ETAPA_6_H35_RESULTADOS_RESTART_FUENTE_GRANULAR.md), todos con protocolos registrados **antes** de sus ejecutores CI. No modificar ni reinterpretar H26/H31 ni el resultado negativo H32.

## 1. Cotejo de los requisitos originales E6

**Hipótesis E6:** «el mundo puede avanzar sin observador ni agente, detenerse y reanudarse sin perder causalidad». **Interpretación verificada acotada:** tres evoluciones físicas headless que ya integraban el diseño de mundo —transporte de sedimento+reservorio material, contacto rígido y fuente que convierte stock en cuerpos vivos— **pueden detenerse y reanudarse entre procesos de CI sin perder su propia historia causal**. **No** existe todavía un solo proceso mundial que combine tres fenómenos y reinicie todos al mismo instante.

**Prueba (a), guardar/cargar sin alterar continuación determinista — CUMPLIDA en tres escenarios materiales distintos:**
- **H33** [CI SUCCESS 45092764108](https://github.com/mxlzz/Nilo_public/actions/runs/45092764108): Landlab2.11 WorldEngine raw + `xarray` owner con cuerpo en reservorio, checkpoint en paso3/6, reinicio en un runner nuevo ejecutando solo4–6; dos mapas con erosión y control K0 con salida, distribución de masa y hash de owner final **bit a bit** idénticos.
- **H34** [CI SUCCESS 45092703790](https://github.com/mxlzz/Nilo_public/actions/runs/45092703790): PyBullet3.2.7 con cuerpo móvil y bloque fijo, paso360/720, `xarray` owner + `.bullet` cache de contactos; otro runner reconstruye escena, restaura y ejecuta361–720, con poses, vel/angular/quaterniones y fuerzas de contacto idénticos.
- **H35** [CI SUCCESS 45093344413](https://github.com/mxlzz/Nilo_public/actions/runs/45093344413): original H26, guardar en paso1200 cuando hay104 granos vivos/21 en cola, misma materia3,125kg, IDs fuente, secuencia y nativo `.bullet`; runner nuevo crea104 cuerpos, restaura poses y contactos, ejecuta1201–3688, libera 21 granos y reproduce **exactamente** hash original H26 y secuencia de alimentaciones, estado de agregación y velocidad final.

**Prueba (b), avance por lotes vs continuo — CUMPLIDA en esas dinámicas y versiones.** H33 prefijo3+cola3 vs6, H34 360+360 vs720, H35 1200+2488 vs3688, todos estados final **bit a bit**, sin volver a ejecutar prefijos. No confundir esto con validar equivalencia de *integradores con distintos tamaños de paso*: solo se probó particionar la misma malla temporal, con mismo motor y versión.

**Prueba (c), escalas temporales y aproximaciones — DOCUMENTADAS, NO COORDINADAS.** Landlab `dt=.2` unidades temporales benchmark (6 pasos); Bullet `dt=1/240s` (720 y3688 pasos, respectivamente); alturas nominales WorldEngine sin calibración geológica; ninguna conversión geológica de reloj. **No existe equivalencia de tiempo entre erosión y contacto**, ni escala ambiental de generaciones. Esto es un límite explícito, no una condición falsamente cumplida.

**Prueba (d), corrupción de estado detectada — CUMPLIDA en bancos pequeños.** H33 rechazó9 cambios de estado, H34 rechazó9 y H35 rechazó10 (incluyendo IDs de fuente duplicados, poses imposibles de reservorio y stock adicional), todos sin modificar owner sano. H34/H35 verificaron SHA de cache `.bullet` y rechazaron el bit modificado en H35 **antes** de restauración.

**Salida, historia causal auditable y headless — CUMPLIDA en cada instancia, NO mundo operativo.** Todos los tests corrieron sin observador, produjeron hashes, manifiestos, logs de CI, checkpoints y protocolos. La física permaneció original (Landlab2.11, Bullet3.2.7) y el inventario material único (xarray); las caches de solver son estados transitorios del motor, no inventarios independientes. Se preservan dos fallos H33 de emisión JSON NumPy previos, distinguidos de la física, antes de [CI final SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45092764108).

## 2. Objeciones a un cierre absoluto

- Ningún experimento congeló y reanudó en una sola operación el **ciclo conjunto** procedural WorldEngine→sedimento mutable Landlab→Bullet contacto, mucho menos dos procesos con feedback. H33+H34 no prueban automáticamente reanudación de su combinación bajo un reloj mundial.
- No se verificó persistencia de temperatura/energía H16 durante un entorno material y mecánico acoplado, ni geometría volumétrica/cavidad que se erosione.
- Solo se probó mismo runtime/versión de cada proveedor en runner Linux distinto, no compatibilidad entre versiones/plataformas, reinicios dentro de un paso, caída eléctrica, base de datos transaccional real, ni scheduling continuo autónomo fuera del CI.
- H35 cubre única seed de una alimentación de125 granos, mientras H26 original probó dos seeds para formación. Reproducción de reinicio es una propiedad distinta de diversidad de configuraciones.

## 3. Decisión y próxima inversión útil

**E6 mínimo, en su alcance de prueba aislada, CERRADO PROVISIONALMENTE:** ya se demostró que capacidades materiales necesarias tienen estado reiniciable sin rehacer pasos, incluso cuando el número de cuerpos físicos crece. **No** se implementa un motor global ni se seleccionan gráficos, agente o mundo operativo. La **integración temporal end-to-end** queda como deuda explícita a reconsiderar cuando la arquitectura común realmente lo exija, no como pretexto para construir infraestructura de schedulers prematuramente.

**E7 puede abrirse como investigación funcional independiente** (no ingeniería de mundo): la [etapa7 §6](BASES_Y_HOJA_DE_RUTA.md) pregunta si reglas compartidas producen configuraciones **funcionales** no prescritas, con semillas, ablaciones, comparación frente a plantillas/azar y estabilidad. Su primer test debe ir más allá de decir «la pila tiene forma»: probar una **consecuencia física externa medible** del agregado H26 (p. ej., si actúa como barrera de soporte para un objeto que cae frente a la misma materia dispersa sin fricción) con escena, punto, masa, controles, ventana y umbrales preregistrados. No suponer que un montículo ya cumple «emergencia funcional»: puede fallar.

**Reapertura E6** obligatoria si la posterior integración descubre stock duplicado, solver cache incompatible, progreso irreconciliable, diferencia entre continuación y continuo o un reloj físico común insuficiente. No empezar por agentes, biomas, interfaz ni evolución abierta.
