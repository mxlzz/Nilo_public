# E09.02i-I3c.3a — preregistro de prueba de esfuerzo sin recompensa

**Fecha 2026-11-21. ANTES de código y resultados.** Depende de [adaptador I3c.3](E09_02I_I3C3_ADAPTADOR_DINAMICO_PRE_REGISTRO.md). Es diagnóstico de operación y frecuencia de oportunidades migratorias, NO prueba de aprendizaje ni de fidelidad C1 real.

## Pregunta

Los oráculos I3c.3 demuestran que migrar es posible **desde un estado controlado** (fuerza cero, output no cero y origen alternativo). ¿En trayectorias autónomas de una red de 4 contactos, aparecen conexiones agotadas y destinatarios activos que generen intentos y aceptaciones, o el scheduler N bloquea el mecanismo? Un resultado cero se conservará; no se cambiará el generador hasta encontrar migraciones.

## Parámetros congelados y controles

- 20 semillas NUEVAS **800..819**. **256 ticks lógicos** por semilla y dos condiciones apareadas: **B** migración apagada vs **B+** migración encendida. Mismo número de unidades6 y contactos4, mismos genes C1, misma conexión inicial, mismos contextos y señales químicas. No hay etiqueta correcta, target ni feedback ni acción supervisada.
- Contexto sintético fijo: c(t) = (t//8)%2, t=0..255. Señal neuronal química exógena C1 Decision CHEM0/CHEM1 fija en dos fases: para t mod16 <8, CHEM=(24,0,0,0); de lo contrario CHEM=(0,24,0,0). El 24 toma como referencia magnitud medida en I3b; **NO se afirma que estas señales sean metabolitos de un Norn**. Sin cuerpo, reacciones ni pool de química: estímulo controlado de ingeniería, no aprendizaje.
- Identidad de wiring explícita y contrabalanceada, independiente de aciertos o mappings: semillas pares (C0,C1,C1,C0), impares (C1,C0,C0,C1), slots D0exc,D0inh,D1exc,D1inh.
- Migración N luego de WTA para neuronas con output no-cero, pool de ambas fuentes registradas, inicialización LTW0/strength2; nada se ajusta de I3c.3. RNG migratorio no usa random global; tape precargada con **4096 draws raw** obtenidos por generador local Python random.Random(810000+seed). Es una CONVENCIÓN N y NO la CRT original. Los draws se guardan dentro del estado y checkpoint; se registra SHA del tape/cursor. Si se agota, abortar, conservar error, no rellenar. El desempate WTA es el mismo de C1ContextBrain reducido.
- B y B+ **no tienen recompensa** y deben compartir trayectoria idéntica al principio hasta que ocurra una migración aceptada. Después sus acciones/outputs pueden diferir, y no se deben presentar como contrafactuales de aprendizaje causal.

## Métricas y tests

- Para cada semilla y rama: conteo de eventos Type1 por reason (accepted, duplicate_source, inactive_recipient, no_disconnected_dendrite), cambios de identidad, conexiones con strength0 al final, cursor RNG y draws consumidos, elecciones D0/D1/None, primer tick aceptado y primera divergencia de estado neuronal B/B+.
- Registrar eventos por tick, especialmente evidencia de fortaleza0 y destinatario inactivo. Si no hay migración: reportar 0 y diagnosticar gating, SIN incrementar químico ni cambiar wiring.
- **Checkpoint determinista**: congelar en tick128, restaurar y continuar, comparando la tupla completa de cuatro conexiones, outputs y tape cursor con corrida ininterrumpida hasta tick256 (cada rama). En B no deben consumirse draws ni alterarse punteros. En B+ todo cambio de puntero debe corresponder a witness migrated=True.
- Idempotencia por semilla: dos ejecuciones de las mismas entradas generan JSON idéntico. Los resultados descriptivos por semilla no se interpretarán como muestras independientes de aprendizaje; no hay criterio primario de exactitud.

## Gates

- **G-I3c3a-TRACE**: JSON reproducible de las 20 semillas, eventos y contadores consistentes; el test detecta un cambio de puntero sin witness.
- **G-I3c3a-CHECKPOINT**: continuación exacta desde tick128 para B y B+.
- **G-I3c3a-MECHANISM**: reportar si hay o no migraciones espontáneas en este régimen fijo; no exige tasa mínima ni inventa una puerta científica de éxito.
- G05/G09/G00-H ABIERTAS. No cambia el modelo I3c.3, no toca main ni Nilo0.7, PR #103 sigue draft.
