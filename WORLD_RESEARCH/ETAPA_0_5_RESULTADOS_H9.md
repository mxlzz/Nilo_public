# E0.5 — Resultados H9: continuidad eco-geomorfológica de 90 días

**Fecha:** 2026-11-21. **Tipo:** ensayo reproducible de componentes abiertos; no motor definitivo.  
**Protocolo preexistente:** [ETAPA_0_5_CONTRATO_TIEMPO_Y_CONTINUIDAD.md](ETAPA_0_5_CONTRATO_TIEMPO_Y_CONTINUIDAD.md)  
**Evidencia:** https://github.com/mxlzz/Nilo_public/actions/runs/44951992403  
**Script:** `experiments/probe_landlab_90day_loop.py`  
**CI:** `.github/workflows/world-landlab-mobile-soil.yml` (**SUCCESS**, con control independiente H8b).

## Hipótesis
Usando solo componentes Landlab `SoilMoisture`, `Vegetation`, `DepthDependentDiffuser`, se puede mantener un mismo inventario de suelo durante 90 días sintéticos con eventos diarios y pasos de geomorfología cada 30 días, permitiendo que cobertura vegetal calculada modifique un coeficiente de transporte publicado.

## Condiciones
- Malla cerrada 8×8; capa de suelo inicial 0.6 m y volumen interior 21.6 m³; producción de suelo cero; roca madre fija.
- Forzante sintético: húmedo 12 mm cada 5 días, seco 0 mm; `Tr=1 h` y `Tb=23 h` diarios; PET constante 8 mm/día. **No calibrado con clima real**.
- Cada 30 días: 1 paso de `DepthDependentDiffuser` de 1/3 de estación; `Kd=Kb exp(-alpha V)`; Kb=2.5e-4 m²/estación, alpha=0.3 (Sharma y Ehlers 2023). d*=1m (valor por defecto del componente, supuesto del ensayo).
- Controles: húmedo/seco con alpha=0; repetición exacta del húmedo.

## Resultados observados
- El reloj hidrológico alcanzó 90/365.25 = 0.24640657 años, sin desviación fuera de tolerancia.
- Ventana 1 (30 días): fracción de cobertura húmeda 0.68422, seca 0.38680; biomasa húmeda 221.924, seca 78.658.
- Ventana 2 (60 días): fracción de cobertura húmeda 0.75299, seca 0.32006; biomasa húmeda 196.775, seca 35.314.
- Ventana 3 (90 días): fracción de cobertura húmeda **0.7599565**, seca **0.2579612**; biomasa húmeda **157.475**, seca **16.2275**.
- Diferencia máxima de relieve húmedo-seco, alpha=0.3: **1.9573432165742588×10^-5 m** (~0.01957 mm).
- Diferencia de relieve entre escenarios al anular alpha: **0 m**.
- Inventario sólido de 21.6 m³ conservado en las tres ventanas, residual absoluto máximo ~1.07×10^-14 m³. Roca madre sin variación.
- Segundo ensayo húmedo reprodujo exactamente el estado de elevaciones nodales.
- **Dictamen de H9: APROBADO para continuidad unidireccional temporal de Landlab y conservación del suelo**. No equivale a validar estabilidad de largo plazo, fenología realista ni ciclo de retroalimentación completo.

## Interpretación y puntos abiertos
1. La secuencia física probada es **forzante de lluvia → saturación/estrés → biomasa/cobertura → movilidad de suelo/relieve**. La topografía nueva **no** altera todavía radiación, escorrentía o humedad posterior; no es un circuito bidireccional.
2. El suelo es material conservado mediante `DepthDependentDiffuser`; no se han unido aún `SpaceLargeScaleEroder` ni caudal fluvial, cuya interacción podría duplicar balances si se integra sin contrato.
3. PET constante 8 mm/día y lluvia sintética obligan a separar funcionamiento numérico de plausibilidad ecológica.
4. La diferencia morfológica es microscópica en el horizonte estudiado; no es una prueba de formación observable de biomas o hábitats nuevos.
5. Persistencia del estado completo de los distintos solvers, condiciones de borde abiertas y rendimiento a escala objetivo todavía no auditados.

## Gate siguiente
Antes de simular un circuito nuevo: comprobar la viabilidad nativa de `Radiation` (relieve→flujo de energía) y `PotentialEvapotranspiration` (radiación→demanda hídrica), documentar API, interpolaciones nodo/celda, unidades y tiempo. Plantear H10 con controles positivos y negativos antes de escribir código. Priorizar modelo existente y no inventar fórmulas de topografía→lluvia.
