# E09.02i-I3b.2a — diagnóstico post hoc de pérdida de LTW por fortaleza

**21/11/2026.** [Preregistro](E09_02I_I3B2A_FORTALEZA_PRE_REGISTRO.md) anterior a instrumentar; [workflow #44957588818](https://github.com/mxlzz/Nilo_public/actions/runs/44957588818) **success**, 4 tests específicos; [testigo de todas las dendritas](../../experiments/neurolab/e09_i3b2a_strength_witness.py); artefacto **neurolab-i3b2a-strength-clearing-witness**, ID **14728237546**, 80 episodios con estados por contacto y tick, retención hasta 2027-02-19.

**Estado:** G-I3b2a-WITNESS **VALIDADA como auditoría observacional**, G05/G09/G00-H permanecen abiertas. No se modificaron seis neuronas, sinapsis, parámetros de química ni I3b.2.

## Repetición y equivalencia

- Se reprodujeron exactamente las **80 trayectorias** de I3b.2, semillas400..419, objetivo0/1 y reglas A/B con estado común tick124, los precursores de dosis80 y ganancia1/4 como antes. En cada tick125–136 se recalculó la sinapsis con la misma función original update_c1_synapse sobre el estado previo.
- Se comparó todo el conjunto **8 dendritas × 12 ticks × 5 ramas × 80 episodios** con el modelo C1ContextBrain y las salidas previamente publicadas: **todos los testigos y registros de efectos/STW/LTW coincidieron**, sin interrumpir ni alterar el modelo.
- El auditor rechaza cualquier cambio numeric LTW fuera de tick divisible por128 y cualquier reducción final de LTW tras la fase numérica **sin lost_connection** explícito.

## Resultado causal interno del modelo: limpieza por atrofia

| Rama | Suma LTW en tick128, 80 episodios | LTW borrada por pérdida de conexión, ticks129–136 | Suma LTW en tick136 |
|---|---:|---:|---:|
| E1, temprano ×1 | **118** | **114** | **4** |
| E4, temprano ×4 | **314** | **44** | **270** |
| L1, tardío ×1 | 0 | 0 | 0 |
| L4, tardío ×4 | 0 | 0 | 0 |
| N, sin precursor | 0 | 0 | 0 |

- **E1:** 98 reset LTW en **tick130** y 16 en **tick135**; la pérdida de fortaleza borró 114/118 unidades LTW creadas (**96,6 %**) antes de tick136.
- **E4:** 14 reset LTW en tick130 y 30 en tick135; perdió 44/314 (**14,0 %**).
- También hubo pérdida de conexión sin LTW previa: L1 **186** eventos, L4 **12**; no imputarles pérdida de memoria lenta. Control N sin eventos de desconexión registrados en esta ventana.
- En **todos los casos** en que LTW disminuyó entre tick128 y136, la magnitud desaparecida coincidió exactamente con la suma de valores borrados en actualizaciones **lost_connection** de la rutina de fortaleza. La regla normal LTW con tasa128 NO corre entre ambos puntos.
- El mecanismo existente [c1_strength.py](../../experiments/neurolab/c1_strength.py) decrementa fortaleza según regla genómica (pérdida tasa5) y cuando llega a cero reemplaza la dendrita por DendriteState(0,0,0). Esta es la **causa operacional verificada dentro del modelo reducido**; **no es una inferencia estadística sobre Norns reales**.

## Límite de fidelidad y alternativa existente

El repositorio **ya dispone** de [c1_migration.py](../../experiments/neurolab/c1_migration.py), adaptación aislada de la migración tipo1/2 de C1 mediante punteros y secuencias explícitas del generador de azar histórico. Sin embargo, C1ContextBrain codifica fuentes Concept por **posición fija** de sus ocho contactos y **no lo enlaza** a ese módulo. Tras una desconexión, el motor actual borra estado pero no reubica la dendrita mediante la lógica original. No corresponde atribuir al juego completo el porcentaje de pérdida de LTW de esta reducción.

**Siguiente comprobación:** [I3b.3 preregistro de viabilidad de migración](E09_02I_I3B3_MIGRACION_VIABILIDAD_PRE_REGISTRO.md): probar con el módulo ya existente si 2 fuentes Concept para 2 dendritas/clase por Decision dejan alguna fuente no ocupada. No crear nueva migración ni sumar neuronas hasta verificar la restricción. G05/G09 abiertas. PR#103 draft, main/Nilo0.7 intactos.
