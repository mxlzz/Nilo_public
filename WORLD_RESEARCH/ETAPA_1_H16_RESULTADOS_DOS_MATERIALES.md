# Etapa1 — H16. Dos materiales con inventario conjunto masa-volumen-energía y fase derivada

**2026-11-22. Dictamen:** H16 **APROBADA** bajo controles previos; no implica finalización automática de etapa1 ni motor definitivo. [Protocolo](ETAPA_1_H16_PROTOCOLO_DOS_MATERIALES_CALOR.md) y [código](experiments/probe_e1_h16_dual_material_heat.py). [CI H16 definitiva](https://github.com/mxlzz/Nilo_public/actions/runs/45059387895) **SUCCESS**, commit `44def8e98e94b0d1fcbd5e8e3fcb5f7d481d0454`.

## Incidencia anterior a las pruebas físicas

[Primera CI H16](https://github.com/mxlzz/Nilo_public/actions/runs/45059294431) y la CI disparada por actualización del protocolo abortaron en análisis del YAML, **sin jobs ni física**, por `run: python -m pip install --only-binary=:all: ...` sin bloque literal. Parser YAML externo reprodujo `mapping values are not allowed here`. Protocolo registró incidencia antes del cambio; se corrigió solo `run: |`, commit `44def8e9`, sin variar ecuaciones, tests o tolerancias. No se ocultan las CI rojas.

## Escenario e invariantes verificados

FiPy4.0.3 resuelve conducción con `TransientTerm` espacial según la capacidad térmica específica y `DiffusionTerm` común. El `xarray.Dataset` posee **solo** `material_mass_kg(material,cell)` y `internal_energy_J(material,cell)`. 8 celdas 1m³ llenas, especie A en primeras cuatro y B en las otras cuatro; densidades ficticias ambas2kg/m³, total16kg (A8kg+B8kg), volumen ocupado8m³. A: cp500J/(kg·K), L50.000J/kg, fracción líquida derivada en banda290–310K; B: cp1000J/(kg·K), sin transición. A inicia306K, B294K; 100 pasos de0,1s, k1000W/(m K), sin intercambio exterior.

- **A celda3:** temperatura 306→**302,62506495797373K** y fracción líquida **0,8→0,6312532478986868**. Masa A total/local no cambia; solo su fase derivada de la energía conservada.
- **B celda4:** temperatura 294→**300,74408811645975K**, sin adjudicarle una fase ficticia.
- **Cantidad conjunta:** A8kg+B8kg=16kg, volumen8m³ exactos; el material no se traslada de celda ni se duplica. Fase A líquida total derivada 6,4→**5,779378195701639kg**; no es fuente/sumidero, la diferencia se refleja en sólido A y calor latente.
- **Energía conjunta:** inicio3.896.000J, final3.895.999,9999999544J; máximo error por paso **4,563480615615845×10⁻⁸J**, inferior al gate0,02J. No se añade energía para corregir el balance.
- **Sin conducción**: E/T/fracción permanecen exactamente constantes; **sin gradiente**: también. **Replay** exacto de masa y energía.
- **Control todo B** con misma masa16kg, misma temperatura inicial y k: celda3 se enfrió **5,2935637K**, frente a **3,3749350K** en escenario A/B; diferencia **1,9186287K**, mayor al umbral previo0,25K. El efecto corresponde a diferentes capacidades caloríficas y calor latente, no a fuentes ocultas; energías iniciales diferentes por composición física.
- **Integridad:** 9 corrupciones rechazadas (energía +1J, masa negativa, sobrecapacidad, doble material en celda llena, unidad incorrecta, cp y densidad alterados, campo redundante y material adulterado). La propiedad de volumen es derivada de masa/densidad. Snapshot NetCDF1180 bytes restauró inventarios, parámetros, ids, T/fase derivados y hash final SHA `af8c321d0c7f2a933df1a9b4e429bd1092275bc258ec4c3606f5494b66229db9`.

## Lo que NO significa

H16 prueba un **esquema pequeño multi-material con estado térmico/energético coherente** y una transformación de fase sin recetas de objetos. No demuestra mezcla **dentro de una celda**, advección de material, intercambio con ROI H5, geometría 3D física, densidades reales, movimientos de líquido, gravedad ni evolución del mundo. El experimento se limita deliberadamente a un material activo por celda, igual densidad y equilibrio local dentro del rango de calor latente.

**Siguiente acción obligatoria:** auditoría del gate de etapa1 contra sus cuatro pruebas del plan y dictamen separado: considerar H1–H6/H15/H16 como evidencia parcial o total del contrato mínimo, sin trasladar requisitos de etapas2–7 (estructura estable, movimiento autónomo, entorno) a etapa1 artificialmente. No fusionar nada con `main`.
