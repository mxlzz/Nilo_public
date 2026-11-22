# Etapa1 — H15. Protocolo preregistrado: transformación de fase y balance térmico en el mismo owner

**Fecha:** 2026-11-22. **Estado:** PRERREGISTRADO ANTES DE CÓDIGO/CI. **Precedente:** H14 [SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45056513417); [gate post-H14](AUDITORIA_GATE_ETAPA_1_POST_H14_2026-11-22.md); [ADR-0008](DECISIONES/ADR-0008_ENTALPIA_FASE_CAMBIO.md). No se adopta motor físico ni se cierra etapa1.

## Hipótesis

¿Un mismo inventario material y energético de 8 celdas cerradas puede determinar qué porción de cada celda está «sólida» o «líquida», y cambiar esas porciones **por conducción de calor con latente** sin producir materia ni energía ficticias? **Contraria:** la aproximación puede conservar energía pero no provocar conversión detectable, puede salir del dominio del constitutivo lineal o puede romper conservación por redondeo/parametrización.

La física será **capacidad calorífica aparente/entalpía estándar** en banda de transformación; FiPy4.0.3 ejecuta el volumen finito `TransientTerm == DiffusionTerm`. No se programará un solver propio.

## Escenario reproducible

- Ocho celdas contiguas, `Grid1D(nx=8,dx=1m)`, volumen1m³ por celda, masa A=2kg/celda, densidad2kg/m³ (abstracta).
- `cp=500J/(kg K)`, `L=50000J/kg`, `T_s=290K`, `T_l=310K`, `k=1000W/(m K)`, banda20K. `cp_eff=3000J/(kg K)`, `rho*cp_eff=6000J/(m³ K)`. Parámetros nominales ficticios, **no calibración de agua o roca**.
- Estado inicial: cuatro celdas a **306K** y cuatro a **294K**; fracciones líquidas respectivamente0,8 y0,2. Materia total16kg; energía interna `E=m*[cp*T+L*f(T)]`: 386000J/celda caliente y314000J/celda fría; total **2.800.000J**. Fracción inicial líquida equivalente **8kg**, sólida8kg, solo derivadas.
- 100 pasos `dt=0.1s`, duración total10s físicos, fronteras no-flux. En cada paso, el owner xarray publica solo `material_mass_kg(cell)` e `internal_energy_J(cell)` tras validar la solución. `T`, `f`, `m_s` y `m_l` se DERIVAN, no son variables materiales independientes.
- Todas las temperaturas deben permanecer estrictamente **290<T<310K** cada paso: solo así puede utilizarse `cp_eff` constante sin agregar no-linealidad o clipping de fase.
- **A:** conducción y L>0. **B:** k=0 con misma materia, energía y fracción inicial. **C:** T uniforme300K y k positivo. **D:** L=0, misma geometría, cp, conductividad y temperatura inicial que A, como ablación de calor latente. **A_replay:** segunda ejecución idéntica A.

## Gates físico-causales, datos e integridad

1. **Conservación por paso:** masa16kg exacta; energía total2.800.000J con tolerancia absoluta0,02J por paso en A/B/C/A_replay, sin fuentes/sumideros; en D energía inicial2.400.000J y mismo umbral0,02J (diferente energía inicial por ausencia de latente, comparación válida de **temperatura** con misma temperatura inicial). Ninguna celda con energía/materia no finita o negativa. No corregir sumas a posteriori.
2. **Conversión observable y causal:** en A, fracción líquida en el borde caliente (índice3) desciende **>0,01** y en el frío (índice4) aumenta **>0,01**; ambas fases presentes, fracción entre0 y1 en cada celda y cantidades de material sólido+líquido DERIVADAS suman exactamente16kg dentro de1e-12kg. Cada región conserva su masa total individual. Temperatura caliente disminuye y fría aumenta.
3. **Ausencia de efecto falso:** en B (k=0) energía/fase/temperatura en cada celda inalteradas dentro de1e-7J,1e-12 fracción,1e-12K; en C (gradiente0) también. La diferencia térmica no se debe a asignar formas especiales por celda.
4. **Efecto del latente:** en D (L=0) la diferencia térmica final en interfaz entre celdas3 y4 debe ser al menos **20% menor** que en A (difusión sensible más rápida) bajo k, cp y temperaturas iguales. D no es fase transitoria (f=0 por definición material sin latente); comparar exclusivamente evolución térmica, no masas líquidas.
5. **Reproducibilidad:** A y A_replay producen arrays de energía material idénticos bit a bit en el mismo entorno CPU; `xarray→NetCDF→xarray` conserva masa, energía, cp, L, `T_s/T_l`, unidades, ids y SHA final. Material derivado de snapshot debe coincidir exactamente en temperatura y fase.
6. **Rechazo previo a commit:** detectar al menos seis corruptelas: añadir+1J, masa negativa, energía negativa, unidad kJ, modificar L, alterar `T_s`, intentar insertar `phase_fraction` como variable stock. El owner sano mantiene hash inalterado.
7. **Coherencia de estado:** para A no se permite ni una celda fuera de 290–310K ni exponer un segundo inventario de masa o energía; auditoría registra energía, masa, fase, amplitud térmica, versiones y fuente de parámetros, sin hacer corrección artificial de saldos.

## Revisión estricta del éxito

**Aceptar H15 solo** si gates1–7 pasan en CI de forma verificable. **No aceptar** si se cumple la conservación pero no cambia la fracción, si falla la ablación L=0, si se invierte mediante clipping para forzar rango o si solo hay cambios cosméticos.

**Interpretación permitida:** demostración de **fracción de estado material derivada de energía conservada** con transición reversible *mushy* y sin cambio volumétrico. **Prohibido concluir:** hielo real, microestructura, fusión abrupta, calor del movimiento, mecánica de un líquido, interacción con cavidad3D, formación emergente o mundo operativo. Etapa1 ABIERTA y etapas2–8 sin gate formal.

## Incidencia H15.0 — fallo de hash de checkpoint antes del informe físico

**Primera CI:** https://github.com/mxlzz/Nilo_public/actions/runs/45058864901 **FAIL** (exit1) dentro de `state_sha(restored)` después de ejecutar casos y controles, al verificar NetCDF. Error `TypeError: Object of type int32 is not JSON serializable`: `xarray.open_dataset` reconstituyó `schema_version` como `numpy.int32` mientras el hasher usa `json.dumps(dict(ds.attrs))`. **No hubo resumen WORLD_EVAL_JSON**; la ausencia de ese registro impide afirmar que ya pasaron todos los gates físicos, aunque el traceback alcanzó el checkpoint. No es un fallo identificado en el solver FiPy.

**Enmienda de ingeniería antes del reintento:** normalizar escalar NumPy de metadatos a escalar Python mediante `v.item()` solo al calcular el hash; mantener exactamente el modelo, la ecuación, parámetros, escenarios, semillas, tolerancias, cinco corridas y criterios previos. No alterar el checkpoint ni reducir controles. **Segundo CI deberá ejecutar física y todos los gates**. Conservar el primer CI rojo en el historial.
