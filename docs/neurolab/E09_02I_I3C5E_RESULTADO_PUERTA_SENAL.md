# E09.02i–I3c.5e — resultado del testigo de propagación del microrefuerzo

**21-11-2026 · POST HOC.** [Preregistro anterior al auditor](E09_02I_I3C5E_PUERTA_SENAL_PRE_REGISTRO.md) · [código](../../experiments/neurolab/e09_i3c5e_signal_gate.py) · [evidencia JSON](resultados/e09i3c5e_oracles.json) · [CI #44965764264](https://github.com/mxlzz/Nilo_public/actions/runs/44965764264) **SUCCESS, 6/6 tests**, artefacto14731856013. Huella SHA256 del JSON completo **ea7304982758c8680e9322b163814aab0aba65bb01bcd1ab009d7479fd0cd9ce**. Reutiliza las 20 huellas I3c.5d del [fixture congelado](resultados/e09i3c5d_resumen_y_hashes.json); no se han corrido nuevos episodios ni cambiado reglas.

## Comparaciones numéricas comprobadas

1. **Cuantización de clase:** bajo el Concept one-hot ya existente `(255*128)>>8` con atenuación255, la salida del concepto es **126**. El barrido exhaustivo STW0..255 con el operador real `dendrite_signal` dio **mínimo STW=5** para enviar una señal positiva a Decision (atenuación128). STW1 genera **0**. Una microred fixture en `learn=False` comprobó scores (D0,D1) **(80,80)** con STW0 y STW1, frente **(81,80)** con STW5. Es umbral de contribución, NO umbral de decisión correcta.
2. **Relajación:** con un `reinforcement_effect=1`, STW0→1 antes de relax, el helper genético tasa80 en **tick7** produce **STW final0 dentro del mismo tick**. En el control matemático equivalente de **tick6**, STW1 permanece. Esto es compatible con D0: 16/80 ramas con efecto unitario sólo en tick7 y STW0 en los snapshots posteriores.
3. **Pérdida de fortaleza:** en condición artificial strength1, STW1, `lose_rate=5` y `lose_rule_output>0`, tick9 mantiene fuerza1/STW1 y tick10 produce `lost_connection=true`, fuerza0 y STW0. Compatible con D3: efecto positivo sólo tick10 y STW0 después.
4. **Conducta original I3c.5d:** 0/80 cambios de elección frente N en ticks9/16/128 tanto en D0 como D3; máximo efecto unitario, STW0 en todos los snapshots. Este diagnóstico no cambia ni reemplaza ese resultado.

**Distinción importante:** H-Q/H-R/H-L se validaron para **oráculos matemáticos del modelo N**, y encajan con el calendario y los valores de I3c.5d; NO son reproducción con el mismo estado biológico original en cada paso, ni demuestran que uno de esos cuellos de botella sea causa única en un Norn C1 completo. La cuantización de tipo0/type1 establece que **un efecto STW1 aislado jamás habría cambiado scores en este circuito** mientras la señal Concept fuese126.

## Errata preservada

La **primera CI #44965690554 falló 6/6 tests** porque un SHA del archivo de evidencia fue transcripto incorrectamente al crear manualmente el fixture: seed1309 tenía una cadena de59 caracteres en lugar de64. No era fallo neuronal ni del cálculo de umbral. Se recuperó el valor exacto del **ZIP original I3c.5d, sin recalcular una referencia nueva**, y se actualizó **únicamente el fixture** en [commit bbdd3c17](https://github.com/mxlzz/Nilo_public/commit/bbdd3c17cecef555d6f4e9148a2f6edc701b4e02). La CI posterior #44965764264 cerró satisfactoriamente todos los tests; se preservan ambas evidencias. Este incidente evidencia la conveniencia de derivar hashes automáticamente al cargar artefactos, no transcribirlos a mano.

## Conclusión y siguiente decisión

**G-I3c5e-NUMERIC validada; G05/G09/G00-H siguen ABIERTAS.** El refuerzo ambiental sintético único y débil no cruza siquiera el umbral matemático de propagación; adelantar la recompensa no soluciona esta condición. No tiene utilidad repetir una prueba idéntica con más semillas ni aumentar gain/dosis a ciegas.

**Siguiente unidad recomendada: auditoría de equivalencia de estado basal** del C1 real vs microcerebro N: (a) pesos y rangos iniciales GEN, (b) locus CHEM2/3 nominal/atrofia, (c) 128 contactos por clase Decision original vs solo4 por neurona reducida, (d) reconstrucción incompleta de emisiones/reacciones y calendario. Reutilizar archivos GEN/EXE ya disponibles y las piezas históricas; **sin programar nueva arquitectura ni modificar Nilo 0.7**. Diseñar el próximo ensayo de aprendizaje únicamente después de identificar qué diferencia de mecanismo, no de mera escala, merece contrastarse.
