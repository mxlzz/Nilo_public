# E09.02i–I3c.5c — preregistro observacional de disponibilidad de conexiones

**21/11/2026 · NL-EXP-I3c5c-v1 · ANTES del nuevo instrumento y corrida.**

## Motivo y ubicación en el plan

La auditoría *posterior al resultado* del archivo completo [I3c.5a](E09_02I_I3C5A_RESULTADO_CREDITO_DIFERIDO.md) detectó que **todas las ramas iniciaron su primer tick de observación (125) con 8/8 slots de strength0**. Esto amenaza la validez del uso de I3c.5a para interpretar *aprendizaje funcional*: podría medir refuerzo transitorio sobre slots agotados. La evidencia del EXE original sugiere que fuerza0 no necesariamente impide transmisión/peso numérico, pero eso no acredita memoria estable. Debemos caracterizar **cómo se llega al tronco** antes de proponer ajustes a la arquitectura.

## Congelación previa

- **Estudio estrictamente descriptivo/post hoc**, no validación independiente de G05. Reusar **semillas1200..1219** y targets0/1 de I3c.5a, **40 troncos únicos** (A/B dan exactamente el mismo estado antes del feedback). No elegir nuevos objetivos, no sintonizar tasas ni pesos.
- Reejecutar *exactamente* las 120 entradas de preparación: `((i//8)%2 for i in range(120))` seguidas de cuatro pasos del objetivo, sin refuerzo, con `C1ContextBrain`, el puente químico existente y `witness_step`, gain1.
- **Muestras por tronco:** tick0, cada tick1..124 (125 muestras), el número `strength>0` (0..8), `STW>0`, `LTW>0`, fuerza/STW/LTW por slot, estado de decisión, químicos leídos, acción sin puntuación y primer tick en que todos los slots llegaron simultáneamente a strength0; registrar si se recupera alguna fuerza antes de tick124.
- **Comparador externo congelado:** los hashes `trunk_checkpoint_sha256` de cada semilla-target en el artefacto I3c.5a, que se derivan de `brain.checkpoint` del estado en tick124; el hash canónico del diccionario de 40 pares es `31559f090dc473ec5502308de2ecfee17e6e2daa07cd451fa4e61b23440225fc` (serialización JSON sort_keys=True, separators=(',',':')). Guardar además pares explícitos como oráculo para impedir reemplazos accidentales.
- Registrar que una fuerza recuperada en ramas con feedback de I3c.5a no prueba que la fuerza inicial fuera positiva; contar separadamente evidencia por fase.
- **No** ejecutar C1 real ni afirmar igualdad global de simulación. No modificar código neuronal ni escoger ahora un nuevo warmup, dosis, ventana o conexión; realizar esto **antes** de preregistrar una intervención.

## Puertas

1. **G-I3c5c-REPLAY:** exactamente 40 troncos, 125 muestras cada uno; tick124/chemical tick124, 40 hashes individuales idénticos al artefacto original; cero verdad de evaluador introducida.
2. **G-I3c5c-DIAG:** distribución completa de primer agotamiento, recuperación espontánea, fuerza al tick124, STW/LTW remanentes y activación. Toda observación negativa se preserva sin manipular resultados.
3. **G05/G09/G00-H:** permanecen abiertas. Sólo después de identificar la causa de pérdida de fuerza plantear una prueba *confirmatoria independiente*, con controles apareados y nueva cohorte, sin usar ésta para optimizar comportamiento.

**Siguiente nodo condicionado:** distinguir disfunción por protocolo preparatorio de una limitación auténtica de la fuerza genómica, comparando cronología y semántica de `strength` antes de intervenir. El código histórico ya debe figurar en [informe I3c.5b-H](E09_02I_I3C5B_H_RESULTADO_X86.md) cuando se complete su publicación.
