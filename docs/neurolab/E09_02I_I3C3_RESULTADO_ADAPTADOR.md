# E09.02i-I3c.3 — resultado técnico del adaptador dinámico

**2026-11-21.** [Preregistro I3c.3](E09_02I_I3C3_ADAPTADOR_DINAMICO_PRE_REGISTRO.md) anterior a implementación. [Módulo](../../experiments/neurolab/e09_i3c3_dynamic_context.py), [pruebas](../../experiments/neurolab/tests/test_e09_i3c3_dynamic_context.py); [CI #44959655977](https://github.com/mxlzz/Nilo_public/actions/runs/44959655977) **success, 9/9 tests**. [Regresión general #44959661489](https://github.com/mxlzz/Nilo_public/actions/runs/44959661489) **success 444 tests, 2 expectedFailure históricos**. Artefacto **neurolab-i3c3-dynamic-source-oracles**, ID14728284133.

- Red B aislada de 6 unidades y 4 contactos Decision. Identidad Concept del contacto por source_pointer persistente; cambiar origen con mismo peso sí cambia input. No se alteró C1ContextBrain de 8 contactos.
- Type1 reutilizado sin modificación: slot strength0, recipient output255, RandStream(1,0,0): migración C0→C1, LTW0, strength2, cursor3. RandStream(0): duplicate_source sin migración, cursor1; recipient0: inactive_recipient sin gastar azar. Prueba también llamada post-WTA del adaptador.
- Checkpoint/restauración estrictos, estado/cursor, continuación bit por bit equivalente. Con aprendizaje desactivado no modifica fuentes ni pesos ni RNG.
- **Advertencia:** la traza de 12 ticks del artefacto no provocó ninguna migración espontánea; aceptación verificada en estado controlado. El scheduler post-WTA y ambos Concept como candidatos son convenciones N, NO reconstrucción completa del original.

**G-I3c3-SCHEMA/MIGRATION/STEP/REPO satisfechas en alcance de ingeniería; G05/G09/G00-H abiertas.**
