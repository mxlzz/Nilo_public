# Etapa1 — H16. Protocolo previo: dos materiales, volumen excluyente, energía y fase en un owner

**2026-11-22. PRERREGISTRO antes de código y CI.** Se realiza únicamente para evaluar el [gate de Etapa1](BASES_Y_HOJA_DE_RUTA.md), cuyo requisito (materiales distintos, masa, volumen, energía, transformaciones trazables) no está cubierto *en el mismo esquema* por H1/H5/H15 separados. Referencias [H1](ETAPA_1_H1_RESULTADOS_ESTADO_MATERIA.md) (A/B + volumen), [H5](ETAPA_1_H5_RESULTADOS_ACOPLAMIENTO_ESTADO.md) (ROI/propiedad de masa), [H15](ETAPA_1_H15_RESULTADOS_FASE_ENTALPIA.md) (una sustancia + energía/estado) y [ADR-0008](DECISIONES/ADR-0008_ENTALPIA_FASE_CAMBIO.md). No elegir motor del mundo.

## Pregunta

¿Un `xarray.Dataset` con inventario simultáneo `material_mass_kg(material,cell)` e `internal_energy_J(material,cell)` y volumen derivado puede representar **dos composiciones distintas** con propiedades térmicas diferentes, admitir una conversión de fase del material A gobernada por energía, rechazar ocupación imposible y permitir una ley de conducción común **sin pérdida de cantidad**?

**Predicción:** 4 celdas A calientes y 4 celdas B frías intercambiarán energía y el A junto a la frontera cambiará su proporción líquida; al retirar conductividad o gradiente cesarán los cambios. Con todo B en todas las celdas, masa y temperaturas iniciales idénticas, la distinta capacidad térmica provoca evolución de temperatura distinta. La alteración de composición es un control causal, no resultado aleatorio.

## Fuente de física y alternativa

- Reusar FiPy4.0.3 (NIST, licencia propia NIST) del H14/H15, **no desarrollar ecuaciones de transporte**. `TransientTerm(coeff=CellVariable(rho*cp_eff)) == DiffusionTerm(coeff=k)`: capacidad calorífica aparente por zona, calor latente solo en A, `k` uniforme. Modelo de entalpía con intervalo de transición ver [ADR-0008](DECISIONES/ADR-0008_ENTALPIA_FASE_CAMBIO.md).
- No usar OpenFOAM/GeoTaichi para un gate de inventario sin movimiento. Tampoco simular materia/energía en paralelo con dos solvers ni crear orquestador propio.

## Escenario exacto, siembra y ownership

1. Ocho celdas 1D de volumen1m³ (`dx=1m`), sin flujo en límites. Dos etiquetas abstractas A y B, cada una con densidad2kg/m³: una celda llena contiene exactamente 2kg de una etiqueta; **no hay mezcla intracelda en H16**, ya que requeriría una ley de mezcla y temperatura común no modelada todavía.
2. **A**: cp500J/(kg K), L50.000J/kg, solidus290K y liquidus310K; temperatura de inicio306K. **B**: cp1000J/(kg K), L0 y sin fracción de fase definida, temperatura inicial294K. `material_mass_kg(A,0..3)=2`, `material_mass_kg(B,4..7)=2`, otros0. Volumen ocupado por celda `sum_m(m/rho_m)=1m³`. Total A8kg+B8kg=16kg.
3. Energía `E_A=m_A[cp_A*T + L_A*f_A(T)]` y `E_B=m_B cp_B T`; para A en la banda `f_A=(T-290)/(310-290)`. **Energia inicial:** A386.000J cada una ×4, B588.000J cada una ×4, total3.896.000J. `T` y `f_A` DERIVADAS del único owner. Nada de energía ni masa duplicada.
4. Conductividad k1000W/(m K), 100 pasos de0,1s; coeficiente volumétrico en A6000J/(m³ K), en B2000J/(m³ K), según cp y L; solvers sobre un único campo T derivado y resultado convertido a candidato owner antes de commit. El cálculo solo es válido si el T de A queda estrictamente290–310K en todos los pasos.
5. **Caso AB:** composición anterior, gradiente306→294K. **Ablación k0:** misma masa y E que AB, k0. **Uniforme:** misma composición AB, todas las temperaturas300K. **Control BB:** solo B en las8 celdas con 2kg/celda, temperaturas iniciales306K en primeras cuatro y294K en últimas; por composición diferente cambian capacidades caloríficas y energía inicial, **no** cantidades totales ni gradiente. **Replay AB:** idéntico.

## Umbrales previos de aceptación

1. **Invariantes conjuntos:** por paso en AB/k0/uniforme/BB/replay, masa16kg y masa por especie/celda exactas; volumen ocupado no supera1m³; en esta prueba exactamente1m³, sin doble ocupación. `E` no negativa/finita, energía global residual absoluto `<0,02J` respecto de la energía inicial de **cada caso**, sin compensaciones externas ni reescritura para cerrar balance.
2. **Causalidad transformación:** en AB, A caliente en celda3 disminuye su fracción líquida **>0,02** desde0,8, y B celda4 aumenta T **>0,5K** respecto294K; sin alterar materia local. Cualquier masa líquida derivada de A es `0<=m_liquid_A<=m_A` y `m_solid_A+m_liquid_A=m_A` (tolerancia1e-12kg). B no recibe un estado de fase ficticio.
3. **Controles:** k0 deja todo E/T/fracción exactamente igual dentro1e-7J y1e-12 de temperatura/fracción; uniforme deja todo E/T/fracción igual dentro los mismos umbrales. Replay del estado final AB exacto bit a bit.
4. **Diferencia de composición con base física:** el escenario BB tendrá un cambio de temperatura en celda3 **al menos0,25K mayor** en magnitud que AB (`T_start3−T_end3`), manteniendo exactamente los mismos16kg, gradiente y conductividad. No comparar saldos absolutos AB vs BB porque sus energías iniciales físicas son diferentes.
5. **Integridad y persistencia:** rechazar al menos 8 corrupciones antes del commit: energía+1J sin fuente, masa negativa, sobreocupación, masa de B en celda ya ocupada por A, unidades de energía, alterar cp o densidad, duplicar temperatura como stock y alterar identidad; owner válido inalterado. NetCDF roundtrip conserva exactamente inventarios, metadatos, ids, hashes y campos derivados de fase/T. Registrar CI/env y fuente.
6. **Falsabilidad:** ningún gate relajado tras observar resultados; si FiPy no admite coeficiente transitorio espacial, registrar fallo de adaptador y no inventar solver alternativo. Si un caso excede la banda de la fase A, declarar **no aprobado** antes de aplicar clip de temperatura. Guardar salida `WORLD_EVAL_JSON` en CI; éxito CI necesario pero no suficiente para dictamen de etapa.

## Limitaciones y gate posterior

**H16 SOLO demuestra** coexistencia espacial de dos materiales bajo la misma PDE térmica con propiedades diferentes y una fase derivada, en **1D sin mezcla intracelda ni movimiento**. No demuestra acoplamiento mecánico, cavidades, patrones 3D ni autoorganización abierta. Si todos los gates pasan, ejecutar **auditoría específica contra los cuatro criterios formales de etapa1**, incluyendo H1–H6 y H15; no declarar cierre automáticamente. Etapas2–8 permanecen sin aprobación por este protocolo.

## Incidencia H16.0: el workflow fue inválido antes de ejecutar jobs

[Primera Actions run 45059294431](https://github.com/mxlzz/Nilo_public/actions/runs/45059294431) se marcó **FAIL** instantáneo, con **cero jobs**. Un parser YAML independiente reprodujo `mapping values are not allowed here` en la línea `run: python -m pip install --only-binary=:all: ...`; la secuencia `=:all:` con dos puntos dentro de un escalar YAML no citado invalida ese bloque. **No se ejecutó ninguna simulación** y no existe resultado físico H16 todavía.

**Enmienda preregistrada antes de reintentar:** cambiar exclusivamente el comando de instalación a bloque literal `run: |` como en H15, sin modificar dependencias, código, hipótesis, parámetros, tests ni umbrales. Conservar la CI roja y realizar una segunda ejecución válida.
