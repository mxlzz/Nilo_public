# E09.02i-I3b.2 — resultado de ventana LTW en tick lógico128

**21/11/2026.** [Preregistro previo](E09_02I_I3B2_VENTANA_LTW_PRE_REGISTRO.md) · [código](../../experiments/neurolab/e09_i3b2_ltw_window.py) · [workflow CI #44957320048](https://github.com/mxlzz/Nilo_public/actions/runs/44957320048) **SUCCESS**, 5 pruebas específicas aprobadas · artefacto **neurolab-i3b2-ltw128-gate**, ID **14728127074**, 80 episodios completos, trazas por tick, retención hasta 2027-02-19.

**Estado:** G-I3b2-WIRING y G-I3b2-OBSERVACIÓN cerradas **en alcance de simulación N de un evento**. G05/G09 y reconstrucción histórica íntegra ABIERTAS.

## Prueba concreta

- 20 semillas nuevas **400..419**, 2 objetivos0/1, 2 mappings A/B, demora d3, **80 episodios**. Química inicial sin precursor, tronco igual hasta tick124.
- E1/E4 reciben el mismo precursor de dosis80 justo antes de tick125; L1/L4 justo antes de tick128, control N sin precursor. Misma cantidad total de ticks, mismos genes57/71/111/112 y receptores88/89/126..129, tasa40 sintética; ganancia1 natural de laboratorio y ganancia4 artificial.
- El helper de LTW reutilizado exige tick %128 ==0 y el gen de Decision registra ltw_rate128; la primera ventana luego del evento es exactamente **tick128**. Química upstream idéntica para pares gain1/gain4 a igual timing; se validó cada testigo de ocho sinapsis contra actualización real de C1ContextBrain.

## Resultado principal

| Condición | LTW delta abs media tick128 vs N | STW delta abs media tick128 vs N | LTW delta abs media tick136 vs N |
|---|---:|---:|---:|
| N: sin precursor | 0 | 0 | 0 |
| E1: temprano, CHEM×1 | **1,475** | 1,775 | **0,050** |
| L1: tardío, CHEM×1 | **0** | 0 | 0 |
| E4: temprano, CHEM×4 | **3,925** | 21,950 | **3,375** |
| L4: tardío, CHEM×4 | **0** | 0 | 0 |

- Contraste temprano−tardío, ganancia4 **+3,925 unidades LTW** por episodio en tick128, IC bootstrap95% por **20 clusters de semilla** [3,800;4,000]. Con ganancia1: +1,475 [1,275;1,676].
- En tick127, **0 cambio LTW** en todas las condiciones: coherente con compuerta de actualización exacta. En tick128 hubo cambio LTW **en todos los 80 episodios tempranos**, aunque amplitud distinta; cero tardíos.
- Lectura final de cuarta decisión sin plasticidad (tick140): acierto N0.5000; E1=0.5000; L1=0.5000; E4=0.6125; L4=0.6125; E4−N=+0.1125 IC cluster [0.0125;0.2000]. Solo efecto conductual de corto horizonte, **no aprendizaje acumulativo**.

## Hallazgo de retención que exige diagnóstico

El efecto LTW temprano de ganancia1 **cae de 1,475 en tick128 a 0,050 en tick136**. Ganancia4 cae 3,925→3,375. Esto es una observación directa del estado, **no debe llamarse decaimiento ordinario LTW**: el motor de sinapsis incluye [atrofia y borrado por fortaleza](../../experiments/neurolab/c1_strength.py), y la regla LTW rate128 no tiene actualización ordinaria fuera de la compuerta. **Todavía no se instrumentó qué conexiones fueron borradas**: requiere [I3b.2a diagnóstico de fortaleza](E09_02I_I3B2A_FORTALEZA_PRE_REGISTRO.md).

## Interpretación permitida

Una misma señal química puede alcanzar o perder la ventana discreta de LTW por cambio de tres ticks, bajo este tick lógico N. Esto demuestra un fenómeno mecanístico de **dependencia de fase** del modelo implementado; no que C1 real ejecute tick128 en cierta cantidad de segundos, no que LTW dure a largo plazo ni atribución causal correcta. En especial, una lectura de corta duración no sustituye ensayo de entrenamiento y holdout independiente.

No se cambiaron ganancias/rates/dosis del preregistro, ni neuroarquitectura. PR#103 draft, main y Nilo0.7 intactos.
