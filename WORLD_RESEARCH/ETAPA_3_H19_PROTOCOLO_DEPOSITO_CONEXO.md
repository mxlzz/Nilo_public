# Etapa3 — H19. Protocolo preregistrado de patrón deposicional conectado y persistente

**2026-11-22. Estado: ANTES DE CÓDIGO Y CI.** Vinculado a [ADR-0010](DECISIONES/ADR-0010_E3_DEPOSICION_Y_CONTROLES_NULOS.md) y [auditoría de cierre E2](AUDITORIA_CIERRE_ETAPA_2_2026-11-22.md). Etapa3 ABIERTA: H19 es primer intento de medir organización, no dictamen definitivo.

## Hipótesis y resultado alternativo

**H19:** bajo la erosión/transporte/deposición de Landlab `SPACE` de H9, sin imponer un patrón final, una fracción del sedimento se concentra en una región espacial **conectada de tamaño superior al esperado bajo permutaciones condicionadas**, y ese depósito persiste al continuar la dinámica. **Alternativa:** los depósitos reflejan únicamente el escalón inicial de suelo y topografía: la conectividad es similar al nulo que preserva la distribución por filas, o la mancha se destruye al avanzar. En tal caso la hipótesis fuerte **NO pasa**, aunque H9/H18 sean correctas y el mundo siga teniendo transporte físico.

**No equivale a emergencia abierta o estructura funcional:** solo sería un patrón geomorfológico 2.5D cuya conectividad no proviene de una plantilla explícita de destino. Un hallazgo positivo necesitará más ensayos de causalidad y condiciones iniciales antes de cierre E3.

## Diseño físico fijo y comparables

- **Mismo upstream:** llamar sin modificaciones `make_scene(K_ACTIVE)`, `advance_native_step`, `validate` y `checksum` de `experiments/probe_e1_h9_sediment_owner.py` (Landlab2.11, MIT). No escribir ni modificar ecuaciones de sedimento.
- Cuenca 16×16, 14×14 core, `dx=10m`, masa inicial10.080.000kg, densidad abstracta1200kg/m³, K_sed0,1, K_br0, 1 outlet y misma estructura de límites. Estado inicial idéntico al H9 original (sin alterar topografía ni suelo). **T12:** ejecutar12 pasos0,2; **T24:** continuar otros12 pasos0,2 **sobre el mismo owner y mismos objetos solver**, no reinicializar. 24 pasos totales sin convertir el reloj a escala geológica calibrada.
- Masas almacenadas al final y salida acumulada del API deben cerrar cada paso con tolerancia `max(1e-4kg,1e-8*M0)=0.1008kg`. No forzar balance a posteriori. Definir `delta_m = mass_t - mass_t0`; nodo «depósito neto» si delta_m>1e-6kg y es core. No usar etiquetas/semillas o reglas de deposición por ubicación.
- Medir grupos de 4-vecinos con `scipy.ndimage.label` sobre máscara 2D. Los nulos conservan **la cantidad exacta de nodos que depositaron** en T12, no el valor de masa por nodo; por ello prueban solo organización **espacial binaria**.

## Controles nulos y estadística preregistrada

- RNG solo para nulos `np.random.default_rng(20261122)`; **512 permutaciones** cada tipo, de las 196 celdas core, sin reemplazo.
- **Nulo global:** elegir al azar `n_ganadores` celdas core entre 196; medir componente conectada mayor en cada muestra.
- **Nulo condicionado por filas (decisivo):** para cada una de las 14 filas core, elegir aleatoriamente y sin reemplazo exactamente `n_ganadores` igual al observado en esa fila; conserva gradiente longitudinal/plantilla inicial. Repetir512 veces y medir componente mayor.
- Estadístico `P95=` percentil95 por `numpy.quantile(...,method="higher")` (discreto). Gate estructural: **componente mayor observada a T12 ≥ P95_condicionado +3 celdas** y **número de celdas depositadas T12 ≥8**. El nulo global es diagnóstico, NO reemplaza control condicionado si este último falla.
- **Persistencia:** Jaccard de máscaras de depósitos netos T12 vsT24 `intersection/union ≥0.60`, y la componente mayor en T24 debe tener ≥50% de las celdas de la componente mayor T12 (medida como tamaño final, no el mismo conjunto; por eso Jaccard global complementa). No declarar reposo mecánico/estructura física permanente.
- **Ablación física K_sed=0:** correr a T12 con mismo estado inicial, debe tener **cero** depósitos netos y sin exportación; no crear un mundo alterando arrays manualmente.
- **Replay:** repetir desde cero T12+T24, masas y ledgers finales, máscaras y componentes **exactos** en misma runtime. Se reportan cambios T24 aunque el patrón de T12 haya desaparecido.
- **Persistencia de datos:** NetCDF del owner T24 debe restaurar masa y salida con hash idéntico; control negativo H9 de 5 corruptelas sigue rechazando estados inválidos sin modificar original.
- **Salidas obligatorias:** `WORLD_EVAL_JSON` con tamaño de componente T12/T24, más datos de conectividad, número de nodos, p95 nulos, Jaccard, balance de materia, versiones y `failed_gates`. Salida CI no-cero cuando un gate físico falla, después de imprimir mediciones. Si no hay depósitos, documentar y no dividir por cero.

## Gate interpretativo

**H19 APROBADA** solo si supera todos los gates de conectividad condicionada, persistencia, balances, ablación, replay y checkpoint. Si nulo condicionado reproduce la organización, **H19 NO APROBADA** aunque el nulo global resulte significativo. Nunca cambiar semilla, nulos, tiempo, percentiles o umbrales después de observar resultados para «salvar» la hipótesis.

**Lo que no se prueba:** soporte mecánico por cohesión/fricción, excavación autónoma en 3D, estabilidad por años, interacción con vida, generación de cuenca, funciones ecológicas ni autoorganización universal. Etapa3 no se cierra por H19 sin evidencia adicional de función/causalidad y control de plantilla.
