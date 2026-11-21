# Etapa 0 — H17: agregación por reglas locales en Particle Life

**Fecha:** 2026-11-21. **Estado:** H17 APROBADA para organización espacial local medible con control de ablación. No es evidencia de vida/organismo/evolución abierta.
**Protocolo antes de test:** `ETAPA_0_H17_PROTOCOLO_PARTICLE_LIFE.md`.
**Upstream MIT:** https://github.com/hunar4321/particle-life , SHA `256278714c4f6a1ce900d24faafcc101769c54c2`.
**CI ejecutada:** https://github.com/mxlzz/Nilo_public/actions/runs/44958620534 (**SUCCESS**).
**Sonda:** `experiments/probe_particle_life_ephemeral.py`, que instrumenta temporalmente el original `particle_life.py`; no copia el motor de terceros al repo. Pygame 2.6.1 con `SDL_VIDEODRIVER=dummy`; 80 frames, seed Python 7321.

## Hipótesis
Con posiciones iniciales idénticas de 100 amarillas y 100 rojas, la fuerza de autoatracción amarilla g=-0.1 del programa original generará mayor proximidad espacial que su única ablación g=0, sin dibujar una figura prefijada.

## Diseño de controles
- Original g=-0.1; control g=0; repetición original g=-0.1 en tres procesos independientes, mismo motor/semilla/otras reglas.
- Hash SHA-256 inicial idéntico en todas: `b3c45d78583bf47cfed3fd98da7f7a22955d5bca41bcd43337a35db7852a42ac`.
- Hash final original y replay **idéntico**: `fd7a895169723edeabf7e3b4f5e56c8378db28cc4ca406ad9e26ee231770676c`; control distinto.
- Siempre 200 partículas totales y 100 amarillas, estados finitos; sin generación/destrucción ni física externa.

## Resultados
- Atracción original: pares amarillos a menos de 8px **1043**; distancia media al amarillo más próximo **0.36620145166808654 px**.
- Sin autoatracción: pares a menos de 8px **11**; distancia media al amarillo más próximo **14.078798778863462 px**.
- Todos los criterios preregistrados pasaron sin relajar los umbrales ni alterar otras reglas.
- Los indicadores son *métricas sobre posiciones*, no un campo de densidad calibrado; la distancia incorpora naturaleza no periódica del espacio del script original. La escala px no corresponde a metros del mundo.

## Interpretación y límites
**Aceptado:** el código upstream produce agrupamientos por interacciones locales sin programar un patrón de grupo, bajo el contraste de fuerza con control nulo. Es un antecedente favorable para el requisito de organización 3B, distinto de generación procedural.

**No probado:** estabilidad tras perturbaciones, función/robustez de la estructura, conservación de masa como material físico con volumen, aparición de reglas nuevas, vida artificial en sentido biológico, evolución abierta ilimitada, acoplamiento de las partículas a suelo/agua/energía de Landlab o rendimiento a gran escala. No se deduce que convenga usar todo el motor Particle Life.

**Decisión experimental:** mantener Particle Life como **benchmark mínimo de patrones/ablación para futuras etapas 3 y 7**, no como núcleo del mundo ni parte de NeuroLab.
