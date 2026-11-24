# NeuroLab E09.02i–I3c.7d — preregistro de auditoría de comparabilidad del régimen de atrofia

**21-11-2026 · NL-AUDIT-I3c7d-v1 · antes del nuevo código, después del resultado I3c.7c.** Auditoría del **contrato ya implementado**, no nuevo ensayo de aprendizaje, sin cohortes adicionales ni tuning.

## Problema identificado al releer controles ya existentes

La línea de refuerzo directo [E09g.5](E09_02G_05_RESULTADO_DOS_CONCEPTOS.md) usa `ZERO=(0,0,0,0)`, `REWARD=(255,0,0,0)`, `PUNISHMENT=(0,255,0,0)` (en `e09_context_protocol.py`), y su readout `evaluate_brain` usa `learn=False`, congelando todas las dendritas. En contraste el puente de química I3/ I3c.7b inicializa Decision desde los genes receptores originales127/128: `CHEM2/CHEM3 nominal=16` y, sin emisores53/70, puede mantenerlas positivas. Las SVRules Decision de **pérdida de fuerza** son `CHEM2`/`CHEM3`, y el código de `update_strength` pierde fuerza con regla de salida no cero en ticks múltiplos5.

Por lo tanto **las líneas E09g.5 y I3 no difieren solamente en vía/intensidad de refuerzo**. Una puede tener pérdida desactivada por sus químicos2/3 siempre cero, y la otra pérdida activa por línea basal nominal16. Este es un **confusor de régimen** que aún no se había documentado claramente en el contraste; no confundir éxito previo de E09g.5 con éxito bajo atrofia activa.

## Experimento de control técnico, SIN nuevas decisiones ni parámetro calibrable

Usar `C1ContextBrain` original, una sola semilla de fixture predefinida **0** (ya consumida en E09g.5), contexto sensorial constante0, 20 ticks y tres trayectorias desde el mismo estado tipado:
- **Z:** `learn=True`, químicos `ZERO=(0,0,0,0)` del E09g.5 (representa su régimen de pérdida química, **no** su entrenamiento con recompensa).
- **L:** `learn=True`, químicos `(0,0,16,16)` con nominales auténticos del GEN original y `locus` de emisores ausente (representa el piso de pérdida de I3, **no** una criatura completa).
- **F:** `learn=False`, mismos químicos `(0,0,16,16)`, testigo congelado del contrato de readout.

Sin pulsos CHEM0/1, sin genes nuevos, sin mundo, ni emisores ficticios. Guardar snapshots del número de sinapsis positivas y los 8 valores de fuerza en `tick=0,4,5,9,10,16,20`; registrar `lost_connection` por tick mediante `update_c1_synapse` original o comparar transiciones verificadas. Confirmar que `C1ContextBrain.step` coincide por dendrita con testigo independiente donde `learn=True`; para congelada verificar estado inmutable.

**Falsable:** bajo estos exactos controles, Z debe retener fuerza2, L perder fuerza a1 en tick5 y fuerza0 en tick10, F fuerza2. Si otra observación aparece, reportar falla y no cambiar la regla para forzarla. Comprobar que los genes Decision de E09g.5 comparten el núcleo con I3, y los bits CHEM2/3 difieren. No atribuir a esa diferencia por sí sola todo el rendimiento E09g.5; otros factores incluyen dosis, frecuencia, retardo, tareas y readout congelado.

## Salida y límites

- **G-I3c7d-COMPAT:** tres trayectorias, mismos inputs/semilla/core, invariantes de fuerza y testigo, nominal auténtico del GEN, firmas de código constantes, tests adversariales, reporte y CI independientes.
- **G05/G09/G00-H abiertas**. No concluir que el Norn natural tiene CHEM16 constantes ni que un simple bloqueo de pérdida sea correcto. Una futura comparación química/directa **justa** debe igualar exposición de CHEM2/3 o reportarla como factor de intervención explícito, con control de readout que no congele una función distinta del resto.
- Si se valida el confusor: preparar propuesta de ensayo multiepisodio con control de fuerza/retención y evidencia de crédito, **no codificar otra variante solo por observar un benchmark alto**.

PR#103 sigue draft, `main` y Nilo0.7 intactos.
