# Etapa2 — H18. Protocolo previo de ablación de pendiente con sedimento material

**Fecha:** 2026-11-22. **Estado:** PRERREGISTRADO antes del código. [Plan de etapa2](BASES_Y_HOJA_DE_RUTA.md) exige que variar solo un gradiente cambie un flujo físico y que no haya fuentes/sumideros ocultos. H9 (Landlab) transportó suelo por una cuenca con control `K_sed=0`; no controló independientemente la intensidad del **gradiente**. H17 ya cubrió caída contra bloqueo con cinemática en owner. Esta prueba tiene la única finalidad de discriminar el efecto de pendiente, **sin instalar motor nuevo**.

## Pregunta falsable

En la cuenca ya validada por [H9](ETAPA_1_H9_RESULTADOS_SEDIMENTO_OWNER.md), ¿reducir exclusivamente la inclinación del sustrato, con el mismo suelo A, misma configuración de erodibilidad, mismo outlet y mismas condiciones numéricas, reduce la exportación de sedimento por la ley de `SpaceLargeScaleEroder`? **Contraria:** la descarga no cambia o aumenta por un cambio de rutas de drenaje, efecto de espesor de suelo u otro mecanismo del solver. Registrar ese resultado y NO ajustar la pendiente retrospectivamente.

## Reutilización y parámetros

- Usar **exactamente** `make_scene`, `advance_native_step`, `validate`, `checksum` de `WORLD_RESEARCH/experiments/probe_e1_h9_sediment_owner.py`, Landlab2.11, Python3.13, xarray. `PriorityFloodFlowRouter` y `SpaceLargeScaleEroder` son proveedores físicos existentes. No añadir ley de erosión, fijar manualmente salida ni recomputar ledger con diferencia de masa.
- `16×16` nodos, `xy_spacing=10m`, `K_sed=0.10`, `K_br=0`, `F_f=phi=0`, `H_star=1.0`, `v_s=3.0`,12 pasos `dt=0.2`. Suelo inicial/hidrología/bordes y masa igual en todos los casos.
- **Escenario G1 (baseline):** bedrock `z0=0.042*y+0.021*x+0.016*sin(...)` original de H9. **G0.5:** escalar solo las elevaciones de bedrock por factor0,5 en el **owner** y en los campos transitorios `bedrock__elevation`/`topographic__elevation` antes del primer paso. La profundidad de suelo inicial0/0,6m permanece constante y no se cambia. Para ambos, ejecutar flow/SPACE sobre la nueva topografía calculada de bedrock + suelo. La salida sigue siendo el mismo nodo0. El factor modifica de forma verificable la pendiente del bedrock, aunque la discontinuidad debida al espesor de suelo no se escala.
- **G0.5-replay:** repetición exacta; **K0**: escenario pendiente original pero `K_sed=0` conservando suelo fijo, ya aceptado por H9. No se implementa campo de temperatura ni conectividad volumétrica.

## Gates fijados antes del ensayo

1. **Identidad de inputs:** misma matriz de suelo/máscara/materia inicial y `K_sed` en G1 y G0.5; solo difiere la bedrock escalada. El gradiente medio del **bedrock** del control debe ser exactamente0,5 de baseline dentro `1e-12` relativo; se informa también el gradiente de superficie total para no confundirlo con bedrock.
2. **Efecto de pendiente previsto:** exportación de sedimento G1 > G0.5 y reducción relativa **>5%** a los12 pasos. Ambos flujos no negativos. Si las rutas cambian y no se verifica, **H18 NO APROBADA como esta hipótesis**, aunque el ledger cierre.
3. **Dinámica material real:** al menos G1 tiene exportación y erosión+deposición nativas, incrementos netos en nodos receptores (H9); G0.5 debe cambiar al menos1 nodo de masa respecto al baseline. No añadir postprocesado que invente un depósito o erosión.
4. **Contabilidad:** en cada paso y escenario `masa almacenada + masa exportada` igual a masa inicial usando `validate` H9, tolerancia `max(1e-4kg,1e-8*M0)`; condición inicial misma masa10.080.000kg. K0 no cambia inventario ni exporta.
5. **Repetición y corrupción:** G0.5 y replay final idénticos bit a bit, `checksum` y ledger iguales; rechazos negativos de H9 siguen funcionando contra estado G0.5 (fuente no autorizada, negativo, kg→g, masa de borde, salida negativa).
6. **Persistencia y salida:** checkpoint NetCDF de G0.5 restaura exactamente inventario, bedrock escalado, unidades, sumidero exportado, topografía derivada y hash; `WORLD_EVAL_JSON` informa flujos, gradientes, balance, tiempo y versiones.
7. **Cierre restrictivo:** H18 solo demuestra una respuesta del **transporte fluvial 2,5D** ante pendiente en banco abstracto. No afirma que sedimentos salgan de cuevas, que haya conversión a roca, flujo de líquidos realista o acoplamiento calor/gravedad. Etapa2 sigue sujeta a auditoría específica de los cuatro criterios tras H17/H18 y otros antecedentes.

**Exit:** aprobar solo si todos los gates1–6 se cumplen, o dejar prueba no aprobada con resultados negativos. No tocar `main`, NeuroLab, motores H9 ni la agenda de E1.
