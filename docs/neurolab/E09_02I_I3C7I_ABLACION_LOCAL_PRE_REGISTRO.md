# NeuroLab E09.02i–I3c.7i — preregistro de ablaciones sinápticas locales sobre el ensayo I3c.7h

**22/11/2026 · NL-AUDIT-I3c7i-v1 · SE FIJAN INTERVENCIONES ANTES DE EJECUTARLAS, PERO DESPUÉS DE HABER VISTO I3c.7h.** Estudio mecanístico *post hoc* sobre cohortes ya consumidas, **no una confirmación independiente G05**. La fuente [I3c.7h](E09_02I_I3C7H_RESULTADO_CONTINGENCIA.md) demostró que desalinear el feedback cambia la política (~+38,6pp B−P activo invertido), pero no demuestra qué conexiones causan elecciones.

## Opciones existentes evaluadas (no desarrollar cerebro nuevo)

Se puede intervenir la microred existente `C1ContextBrain`: `ContextBrainState` y `C1SynapseState` son dataclasses congeladas; el núcleo `step(...,learn=False)` lee las **8 STW**, calcula `dendrite_signal`, SVRule Decision y WTA sin actualizar sinapsis. Ya existen `checkpoint/restore`, `_run_external_tape` y `run_phase` en I3c.7h/I3c.7e, más hashes SHA originales de cada semilla. No es necesario crear otro motor ni introducir genes, emisores o una función de aprendizaje. La ablación es sólo intervención DIAGNÓSTICA en un clone, **no mecanismo del agente**.

## Pregunta y estimando

¿Cuáles de las **8 entradas sinápticas** son **necesarias localmente** para las acciones que genera el circuito ya entrenado, bajo la misma situación inicial? Comparar el circuito de recompensa **B contingente** y **P permutado** de I3c.7h. El *estimando* para slot j y contexto c en cada checkpoint es la diferencia de acción/precisión en los seis últimos ticks de un bloque de ocho estímulos constantes, entre estado original/sham y **el mismo estado con STW del slot j sustituida por0** (único cambio; fuerza, LTW, químicos, neuronas restantes y estado inicial intactos). Clones del MISMO checkpoint permiten afirmar un efecto causal **de la señal sináptica local sobre esa decisión**, no del origen de su aprendizaje ni de la importancia universal de la conexión.

**Caveats importantes:** la excitación/inhibición se combina y hay umbrales, saturación y redundancias; un efecto nulo tras quitar una entrada **no demuestra** que no contribuya. `C1ContextBrain.step` lee STW incluso cuando la fuerza del contacto es0 (como se observó en I3c5b): por eso no enmascarar/omitir contactos `strength0`, sino registrar fuerza separada. Concept-output126 y WTA pueden hacer que impacto en score no cambie la acción. Una lesión local no prueba que el refuerzo haya atribuido crédito correctamente a la conexión.

## Cohorte, fuentes originales y replay

- **NO consumir nuevas semillas**: exactamente las20 de desarrollo **1800..1819** de I3c7h y fases `first`/ `reversed`. Las1400..1419 siguen reservadas para posible confirmación de una hipótesis posterior.
- Reejecutar `e09_i3c7h_contingency_permutation.run_seed(seed)` y comprobar su SHA256 canónica contra [manifest original](resultados/e09i3c7h_resumen_y_hashes.json) para **cada** semilla; fail closed en divergencia. Archivo completo original `i3c7h.json` 39.394.817bytes SHA256 `d723c4a590c0428e13b175c39cd9028c69ed5b714d000f46ada61717eebe925e`, CI44986258314, artifact14739997041.
- Reconstruir sólo estados B/P al final de **256 y512 ticks** usando `initial_coupled`, `run_phase(M0)`, `event_tape_from_original`, `context_stratified_permutation`, `_run_external_tape`. Exigir igualdad exacta con `end_state_sha256` de los datos originales por seed/phase/mode; no modificar runner de origen ni generar nuevo aprendizaje. La reconstrucción B y P se mantiene on-policy/remoto como experimento original; la prueba posterior no añade feedback.
- **Dos contextos** por seed/phase/mode (`0` y `1`) y **9 micropruebas por contexto:** sham/original + **8 ablaciones de slot único**. Control adicional `ALL_ZERO` con STW=0 en los ocho slots para medir dependencia colectiva/no redundancia. Cada microprueba dura exactamente **8 ticks del mismo contexto**; `learn=False` y químicos cerebrales `ZERO=(0,0,0,0)` en TODOS, sin metabolismo, sin nuevos premios y sin actualizar el checkpoint. Sólo contar como resultado `steady` las acciones de **ticks3–8 del microbloque**; ticks1–2 son acomodación del Concept con latencia y se conservan como secundaria, no se eliminan del archivo.
- Atribución funcional estructural **predefinida**, puramente descriptiva: `slot index=(owner*2+source)*2+class`, class exc0/inh1. Para un contexto `c`, `aligned` si fuente=c Y (exc hacia owner=mapping[c] o inhib hacia owner distinto), `unaligned` en otro caso. Examinar ambos, sin atribuir causalidad con sólo esa etiqueta.

## Invariantes adversariales y controles

- `SHAM`: `dataclasses.replace` con los mismos valores debe producir EXACTAMENTE el mismo `ContextTick`/acciones/scores que la rama original en los8 pasos. Lesión de slot cuya STW ya era0 debe tener acciones y scores idénticos al sham (no inventar sensibilidad). ALL_ZERO sólo altera STW, no fuerza ni LTW. Ningún brazo aprende, migra ni consume química; `C1ContextBrain.step` original es el único intérprete.
- Control de ruta: la acción desde el mismo `ContextBrainState` con `learn=False` debe ser idéntica con CHEM `ZERO` y `(255,255,255,255)` porque la SVRule Decision lee pesos previos y la química sólo afecta plasticidad omitida; si no, la microprueba no aísla STW.
- Al terminar cada microprueba original/lesionada, las dendritas deben conservar EXACTAMENTE sus STW/LTW/strength iniciales. El checkpoint original de ambas ramas B/P no debe alterarse; sus SHA antes/después iguales.
- **Datos íntegros y sin selección**: 20 seeds×2 fases×2 modos×2 contextos×10 micropruebas (sham+8+ALL_ZERO)=**800 bloques de ocho ticks**, más cada transición correspondiente; conservar todos los cambios de score, acción, elección None, necesidad/ayuda por lesión y controles negativos. Notar que existen **640 microbloques lesionados por slot único**, 80 SHAM y80 ALL_ZERO.
- Resultados por slot: cantidad de los seis ticks steady con `action` distinta del sham; número `sham correcto→lesión incorrecta` (**necesidad local**) y `sham incorrecto→lesión correcta` (**lesión útil**); exactitud baseline, y diferencias de score incluso cuando WTA no cambia. Reportar también distribución por fuente/clase/alignment y número de slots afectados por seed/contexto.
- Contrastes exploratorios B−P en proporción de lesiones que alteran acción, necesidad/ayuda condicionadas a tick sham correcto y distribución aligned vs unaligned, por seed-cluster20 usando **bootstrap pareado2000 RNG60521** (nunca pseudorreplicar cientos de ticks). Reprobar incertidumbre y no seleccionar solo seeds donde B rinde bien.
- **Puerta informativa**: para afirmar sensibilidad local se requiere que ALL_ZERO cambie al menos una acción steady respecto de SHAM en **≥12/20 semillas** en `B` fase invertida; si no, declarar microprobe poco sensible/no identificable, aun si las pocas lesions individuales dan alguna diferencia. Requisito adicional para comparar B/P: baseline B sham inverted steady≥0,65; si falla, el instrumento no representa suficientemente la capacidad observada en holdout normal. Si alguno falla **no reajustar** duración/contextos de esta cohorte.

## Interpretación y avance

**Puerta de software:** todas las SHA por seed y por checkpoint reproducidas, clones/sham idénticos, química inmóvil, STW0 lesión inerte, 800 microbloques exactos, sin pérdida de pesos ni nuevas semillas, output completo CI+hash.

**Resultado positivo posible:** encontrar conexiones cuya ausencia interfiere con acciones correctas de B y no de P, sobre igual contexto/estado intrabrazo. Esto prueba **necesidad local de señales sinápticas concretas** en el evaluador existente y apoya especificidad funcional de la red, **no** que esas conexiones fueron reforzadas causalmente por acciones previas. La última pregunta requeriría contrafactuales del evento de recompensa con el mismo estado/exposición y seguimiento del enlace.

**Resultado negativo:** ninguna lesión modifica acciones aunque el modelo discrimine (redundancia o WTA), lesiones fuera de alineación ayudan, o intervención global falla. Registrarlos sin ajustar la red.

**G05/G09/G00-H ABIERTAS**, aunque aparezca señal. No tocar `main`, Nilo0.7 ni PR103 draft; no usar `C1` original completo como si estuviera implementado.


## Fe de erratas instrumental posterior a ejecución — 22/11/2026

El conteo **800 microbloques, 640 lesiones únicas** escrito arriba fue un ERROR ARITMÉTICO de metadatos: la fórmula declarada literalmente (20 × 2 fases × 2 modos × 2 contextos × (1 sham + 8 single + 1 all-zero)) da **1.600 microbloques, de los cuales 1.280 son lesiones individuales, 160 sham y 160 all-zero; 12.800 microticks de diagnóstico**. El código siempre ejecutó la fórmula y **todos los datos de la primera corrida coinciden con 1.600**, sin modificación de algoritmo ni de semillas.

El [primer CI I3c7i #44986729926](https://github.com/mxlzz/Nilo_public/actions/runs/44986729926) falló un test que esperaba erróneamente40 para una sola semilla (real80). Corregida solamente la expectativa, la [segunda CI #44986812101](https://github.com/mxlzz/Nilo_public/actions/runs/44986812101) pasó los7 tests y generó el dataset completo, pero falló su último `assert` porque exigía800/640/6400 en lugar de1600/1280/12800. **No se alteraron dendritas, seeds, checkpoints, gates ni resultados.** El workflow de comprobación se corrigió a los totales matemáticos reales. Conservar este historial y no confundir fallas de recuento con resultados científicos negativos.
