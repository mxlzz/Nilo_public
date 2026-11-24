# NeuroLab I3c.7d — resultado: los baselines directos y químicos difieren también en atrofia

**21/11/2026. Auditoría de mecanismo y código fuente, no nueva cohorte.** [Preregistro previo](E09_02I_I3C7D_COMPARABILIDAD_ATROFIA_PRE_REGISTRO.md) · [auditor C1 original sin modificación](../../experiments/neurolab/e09_i3c7d_loss_regime_audit.py) · [CI #44968836884](https://github.com/mxlzz/Nilo_public/actions/runs/44968836884) **SUCCESS 4/4 tests**, artefacto `neurolab-i3c7d-direct-metabolic-loss-confound` ID14732757592.

## Hallazgo con fuentes de código y genoma

El benchmark [E09g.5](E09_02G_05_RESULTADO_DOS_CONCEPTOS.md) de refuerzo directo presenta al núcleo `C1ContextBrain` únicamente:
- `ZERO=(0,0,0,0)` sin recompensa;
- `REWARD=(255,0,0,0)` y `PUNISHMENT=(0,255,0,0)` al corregir.
Los químicos **CHEM2/CHEM3 están siempre en cero**. Las reglas originales de pérdida de fortaleza Decision dependen precisamente de **CHEM2/CHEM3 NO CERO** (genes excitatorio/inhibitorio), así que este benchmark **no ejerce la pérdida química de fuerza**. Además, su `evaluate_brain(...learn=False)` congela el estado de todas las sinapsis, incluyendo atrofia y relajación, durante la evaluación.

Por contraste, `I3/I3c` inicializa la rama metabólica mediante receptores genéticos127 y128 del `dad1.gen` original. Su estado nominal Decision es `CHEM0/1=0, CHEM2/3=16`; sin los emisores endógenos53/70, esa señal basal de pérdida persiste en este laboratorio, salvo otras concentraciones/reglas activas. **No es una fisiología C1 completa.**

## Verificación de tres trayectorias sin feedback, mismo cerebro

Fixture con semilla histórica0 (ya utilizada en E09g.5), estímulo fijo, 20 ticks y **8 dendritas iniciales strength2**; mismo `C1ContextBrain` y 8 testigos `update_c1_synapse` en cada tick plástico:
- **Z = `CHEM=(0,0,0,0)`, `learn=True`:** 8/8 conservan fuerza2 al tick20, sin eventos de pérdida.
- **L = `CHEM=(0,0,16,16)`, `learn=True`:** las ocho pierden fuerza2→1 exactamente tick5 y fuerza1→0 en **tick10**; ninguna está activa hasta tick20.
- **F = `CHEM=(0,0,16,16)`, `learn=False`:** 8/8 conservan strength2 hasta tick20. Congelar `learn` bloquea también loss/relax.

El algoritmo original y los tests de transiciones coinciden en cada paso. Las diferencias no dependen de elegir semillas ventajosas ni de ajustar magnitud: son reglas del mismo motor con distintas entradas y modo congelado.

## Consecuencia para G05

**Es un confusor estructural de comparación:** el rendimiento previo alto del directo E09g.5 (steady 96,7% fase A y93,0% fase B, sin lograr el gate18/20) no se obtuvo bajo las mismas condiciones de desgaste que los ensayos químicos I3. No se puede decir que toda la diferencia de exactitud se explique por la ineficacia del enlace químico: también cambiaron pérdida de fuerza, amplitud, temporalidad, calendario, número de feedbacks y readout congelado.

La comparación más cercana bajo **atrofia nominal** es [I3c.7b](E09_02I_I3C7B_RESULTADO_CONTRASTE_SENAL.md): un pulso directo aún produce sensibilidad conductual breve, pero ambos N/M/C pierden8/8 enlaces en tick10. Este ensayo no prueba qué ocurriría con muchos pulsos directos bajo atrofia nominal ni que simplemente apagar CHEM2/3 sea un remedio histórico válido.

**G-I3c7d-COMPAT VALIDADA; G05/G09/G00-H ABIERTAS.** Próximo contraste razonable es un protocolo factorial o controlado de **refuerzo repetido × atrofia**, separando explícitamente fuerza nominal/no loss y midiendo continuidad de memoria sin congelar artificialmente los pesos, con protocolo/semillas nuevos. No introducir una política de atrofia «corregida» por intuición ni cambiar el motor Nilo.
