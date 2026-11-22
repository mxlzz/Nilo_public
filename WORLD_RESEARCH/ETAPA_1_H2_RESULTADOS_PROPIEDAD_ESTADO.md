# Etapa 1 — H2: estado único, vistas compartidas y control de reemplazo

**Fecha:** 2026-11-22. **Dictamen:** H2 **APROBADA** para un alias material de prueba y recuperación de vista, **NO** para transacciones ni acoplamiento de solvers simultáneos. Etapa 1 ABIERTA.
**Plan:** `ETAPA_1_H2_PROTOCOLO_PROPIEDAD_ESTADO.md`.
**Script:** `experiments/probe_e1_shared_state_views.py`.
**Evidencia actual CI:** https://github.com/mxlzz/Nilo_public/actions/runs/44986371590 — **SUCCESS**.
**Primera prueba CI:** https://github.com/mxlzz/Nilo_public/actions/runs/44959354131 — PASS para alias original; el primer desplazamiento fue 0.125 kg pese a que el plan establecía 0.05 kg. Se conservó el fallo de conformidad al protocolo y se corrigió el valor en segunda CI sin relajar los criterios.

## Condiciones
- Landlab 2.11.0 + xarray 2026.9.0 + NumPy, grilla ambiental 4×5 con **6 celdas interiores**; el estado material de referencia es un Dataset con **2 materiales × 2 niveles × 2 filas × 3 columnas**. Referencia = `matter_v0` preexistente con 8 pruebas originales, sin física propia añadida.
- Campo por material/celda de Landlab enlazado a **vista NumPy del tensor xarray** usando `copy=False` y asignación de índices espaciales exacta (no suposiciones de reordenamiento). Se registró `np.shares_memory` en ambos materiales.

## Observaciones
- **Alias bidireccional real:** `A=true`, `B=true`. La transferencia **manual 0.05kg** desde campo Landlab alteró exactamente el array canónico xarray. Una segunda transferencia manual sobre el array xarray fue visible desde Landlab. Inventario cerrado A **1.1 kg**, B **≈0.6 kg**, cantidades conservadas dentro de tolerancia; el nivel superior permaneció idéntico.
- **Control negativo:** al crear campos Landlab con `copy=True`, `shares_memory=false` para A y B y los valores no acompañaron una mutación posterior del owner.
- **Corruptibilidad explícita:** un escritor directo puede crear masa negativa o superar capacidad sin recibir error de Landlab/xarray; el **validador externo MatterGrid** detectó ambos casos. No atribuir reglas de conservación a los contenedores.
- **Persistencia:** NetCDF de **964 bytes**, roundtrip exacto y enlace de vistas explícitamente reconstruido luego de cargar. El alias no «sobrevive» a disco como puntero: se restablece desde el array cargado.
- **H2b, control de variable reemplazada:** al asignar nuevo tensor `ds["material_mass"] = <copia>`, el campo Landlab anterior **dejó de compartir memoria** (`stale_view_detected=true`). El nuevo tensor pudo mutarse sin modificar el campo obsoleto, una situación de divergencia **peligrosa si no se controla**. Al reatar campos Landlab mediante `add_field(...,copy=False,clobber=True)`, ambas memorias volvieron a compartirse (`A=true`, `B=true`) y los valores se propagaron nuevamente. La prueba restauró valores y preservó inventario.

## Conclusión técnica
La vía xarray/NumPy owner + Landlab vista es **factible con arrays homogéneos y topologías/índices comprobados**, pero **NO segura ante sustitución de variable, mutaciones concurrentes o escrituras sin validación**. `xarray` no debe tratarse como motor de física, `Landlab` no debe convertirse sin pruebas en universo tridimensional. Necesitamos **punto de commit validado** (o recuperación rollback) antes de conectar subsistemas; los cálculos pueden operar sobre staging buffers y publicar solo estados íntegros. Primero investigar validadores existentes, no construir framework de infraestructura.

## Próxima prueba focalizada
H3: **validación integral de todos los niveles y publicación atómica de un cambio material**, comparar `Pandera DatasetSchema` (biblioteca existente que soporta xarray) con las reglas numéricas mínimas de MatterGrid. Prueba de corrupción negativa y sobrecapacidad en **nivel 1**, valores NaN, cambios de unidades y balance total. El objetivo es seleccionar contrato de datos reutilizable de bajo costo, NO implementar caída, física nueva o gestores universales.
